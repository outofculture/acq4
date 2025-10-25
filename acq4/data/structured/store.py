# acq4/data/structured/store.py
# High-level CRUD + query facade with locking safeguards.

from __future__ import annotations

import json
import os
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator, Mapping, Sequence, Union
from uuid import UUID

from acq4.logging_config import get_logger
from acq4.util import DataManager as dm

from .loader import (
    LoadedCellRecord,
    LoadedPatchAttemptRecord,
    load_cell,
    load_patch_attempt,
)
from .paths import StructuredPathHelper
from .metrics import (
    increment_cells_created,
    increment_patch_attempts_created,
)
from .records import CellRecord, PatchAttemptEvent, PatchAttemptRecord
from .storage import (
    BinarySource,
    write_cell_metadata,
    write_cellfie_image,
    write_event_log,
    write_patch_attempt_metadata,
    write_tasks_run,
)
from .streaming import StreamingPatchLogger

logger = get_logger(__name__)


@dataclass(frozen=True)
class CellSummary:
    uuid: UUID
    notes: str
    metadata_path: Path


@dataclass(frozen=True)
class PatchAttemptSummary:
    uuid: UUID
    cell_uuid: UUID
    successful_seal: bool
    metadata_path: Path


class StructuredLockError(RuntimeError):
    """Raised when a record directory lock cannot be acquired."""


class StructuredObjectStore:
    """Thread/process-safe facade over structured DataManager helpers."""

    LOCK_TIMEOUT_DEFAULT = 5.0
    LOCK_POLL_INTERVAL = 0.05

    def __init__(
        self,
        base_dir: Union[str, Path, dm.DirHandle],
        *,
        lock_timeout: float | None = None,
    ):
        self.paths = StructuredPathHelper(base_dir)
        self._lock = threading.RLock()
        self._lock_timeout = (
            self.LOCK_TIMEOUT_DEFAULT if lock_timeout is None else lock_timeout
        )

    def create_cell(
        self,
        record: CellRecord,
        *,
        cellfie_source: BinarySource | None = None,
    ) -> LoadedCellRecord:
        with self._store_guard():
            paths = self.paths.cell_paths(record.uuid, create=True)
            with self._record_write_lock(paths.directory):
                _reject_if_exists(paths.metadata_path, f"Cell {record.uuid}")
                write_cell_metadata(paths, record)
                if cellfie_source is not None:
                    write_cellfie_image(paths, cellfie_source)
                increment_cells_created()
                logger.info(
                    "Structured store: created cell %s at %s",
                    record.uuid,
                    paths.metadata_path,
                )
                return load_cell(paths)

    def get_cell(self, cell_id: Union[UUID, str]) -> LoadedCellRecord:
        with self._store_guard():
            paths = self.paths.cell_paths(cell_id, create=False)
            return load_cell(paths)

    def list_cells(
        self,
        *,
        predicate: Callable[[CellSummary], bool] | None = None,
        sort_by: str = "uuid",
    ) -> list[CellSummary]:
        with self._store_guard():
            summaries = list(_generate_cell_summaries(self.paths.layout.cells_path))
        if predicate is not None:
            summaries = [s for s in summaries if predicate(s)]
        _sort_summaries(summaries, sort_by)
        return summaries

    def iter_cells(
        self, predicate: Callable[[CellSummary], bool] | None = None
    ) -> Iterator[CellSummary]:
        return iter(self.list_cells(predicate=predicate))

    def create_patch_attempt(
        self,
        record: PatchAttemptRecord,
        *,
        event_log_entries: (
            Iterable[Union[PatchAttemptEvent, Mapping[str, object]]] | None
        ) = None,
        tasks_run: Sequence[object] | None = None,
    ) -> LoadedPatchAttemptRecord:
        with self._store_guard():
            try:
                self.paths.cell_paths(record.cell_uuid, create=False)
            except FileNotFoundError as exc:
                raise ValueError(f"Cell {record.cell_uuid} does not exist") from exc

            paths = self.paths.patch_attempt_paths(record.uuid, create=True)
            with self._record_write_lock(paths.directory):
                _reject_if_exists(paths.metadata_path, f"PatchAttempt {record.uuid}")
                write_patch_attempt_metadata(paths, record)
                if event_log_entries is None:
                    event_log_entries = record.event_log_entries
                write_event_log(paths, event_log_entries)
                if tasks_run is None:
                    tasks_run = record.tasks_run
                write_tasks_run(paths, tasks_run)
                increment_patch_attempts_created()
                logger.info(
                    "Structured store: created patch attempt %s for cell %s",
                    record.uuid,
                    record.cell_uuid,
                )
                return load_patch_attempt(paths)

    def get_patch_attempt(
        self, attempt_id: Union[UUID, str]
    ) -> LoadedPatchAttemptRecord:
        with self._store_guard():
            paths = self.paths.patch_attempt_paths(attempt_id, create=False)
            return load_patch_attempt(paths)

    def list_patch_attempts(
        self,
        *,
        predicate: Callable[[PatchAttemptSummary], bool] | None = None,
        sort_by: str = "uuid",
    ) -> list[PatchAttemptSummary]:
        with self._store_guard():
            summaries = list(
                _generate_patch_summaries(self.paths.layout.patch_attempts_path)
            )
        if predicate is not None:
            summaries = [s for s in summaries if predicate(s)]
        _sort_summaries(summaries, sort_by)
        return summaries

    def iter_patch_attempts(
        self, predicate: Callable[[PatchAttemptSummary], bool] | None = None
    ) -> Iterator[PatchAttemptSummary]:
        return iter(self.list_patch_attempts(predicate=predicate))

    def stream_patch_attempt(
        self, attempt_id: Union[UUID, str]
    ) -> StreamingPatchLogger:
        with self._store_guard():
            paths = self.paths.patch_attempt_paths(attempt_id, create=False)
            lock_cm = self._record_write_lock(paths.directory)
            lock_cm.__enter__()
            logger_obj = StreamingPatchLogger(paths)
            logger_obj.set_lock_context(lock_cm)
            return logger_obj

    @contextmanager
    def _store_guard(self):
        with self._lock:
            yield

    @contextmanager
    def _record_write_lock(self, directory: Path, *, timeout: float | None = None):
        if timeout is None:
            timeout = self._lock_timeout
        lock_path = directory / ".lock"
        deadline = time.monotonic() + timeout
        fd = None
        try:
            while True:
                try:
                    fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                    break
                except FileExistsError:
                    if time.monotonic() >= deadline:
                        raise StructuredLockError(
                            f"Timed out acquiring lock for {directory}"
                        )
                    time.sleep(self.LOCK_POLL_INTERVAL)
            os.write(fd, str(os.getpid()).encode())
            yield
        finally:
            if fd is not None:
                os.close(fd)
                try:
                    os.unlink(lock_path)
                except FileNotFoundError:
                    pass


def _generate_cell_summaries(root_path: Path) -> Iterator[CellSummary]:
    for child in root_path.iterdir():
        meta = child / "metadata.json"
        if not meta.exists():
            continue
        try:
            data = json.loads(meta.read_text())
            yield CellSummary(
                uuid=UUID(str(data["uuid"])),
                notes=data.get("notes", ""),
                metadata_path=meta,
            )
        except Exception:
            logger.exception("Failed to summarize cell metadata at %s", meta)


def _generate_patch_summaries(root_path: Path) -> Iterator[PatchAttemptSummary]:
    for child in root_path.iterdir():
        meta = child / "metadata.json"
        if not meta.exists():
            continue
        try:
            data = json.loads(meta.read_text())
            yield PatchAttemptSummary(
                uuid=UUID(str(data["uuid"])),
                cell_uuid=UUID(str(data["cell_uuid"])),
                successful_seal=bool(data.get("successful_seal", False)),
                metadata_path=meta,
            )
        except Exception:
            logger.exception("Failed to summarize patch metadata at %s", meta)


def _sort_summaries(summaries, sort_by: str) -> None:
    if sort_by == "uuid":
        summaries.sort(key=lambda s: str(s.uuid))
    elif sort_by == "metadata_mtime":
        summaries.sort(key=lambda s: s.metadata_path.stat().st_mtime, reverse=True)
    else:
        raise ValueError(f"Unsupported sort key '{sort_by}'")


def _reject_if_exists(metadata_path: Path, label: str) -> None:
    if metadata_path.exists():
        raise ValueError(f"{label} already exists at {metadata_path.parent}")
