# acq4/data/structured/store.py
# High-level CRUD facade for structured DataManager records.

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Sequence, Union
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
from .records import CellRecord, PatchAttemptEvent, PatchAttemptRecord
from .storage import (
    BinarySource,
    write_cell_metadata,
    write_cellfie_image,
    write_event_log,
    write_patch_attempt_metadata,
    write_tasks_run,
)

logger = get_logger(__name__)


class StructuredObjectStore:
    def __init__(self, base_dir: Union[str, Path, dm.DirHandle]):
        self.paths = StructuredPathHelper(base_dir)

    def create_cell(
        self,
        record: CellRecord,
        *,
        cellfie_source: BinarySource | None = None,
    ) -> LoadedCellRecord:
        paths = self.paths.cell_paths(record.uuid, create=True)
        _reject_if_exists(paths.metadata_path, f"Cell {record.uuid}")
        write_cell_metadata(paths, record)
        if cellfie_source is not None:
            write_cellfie_image(paths, cellfie_source)
        logger.debug("Created cell record %s", record.uuid)
        return load_cell(paths)

    def get_cell(self, cell_id: Union[UUID, str]) -> LoadedCellRecord:
        paths = self.paths.cell_paths(cell_id, create=False)
        return load_cell(paths)

    def list_cells(self) -> list[UUID]:
        return _list_record_ids(self.paths.layout.cells_path)

    def create_patch_attempt(
        self,
        record: PatchAttemptRecord,
        *,
        event_log_entries: (
            Iterable[Union[PatchAttemptEvent, Mapping[str, object]]] | None
        ) = None,
        tasks_run: Sequence[object] | None = None,
    ) -> LoadedPatchAttemptRecord:
        # Ensure referenced cell exists
        try:
            self.paths.cell_paths(record.cell_uuid, create=False)
        except FileNotFoundError as exc:
            raise ValueError(f"Cell {record.cell_uuid} does not exist") from exc

        paths = self.paths.patch_attempt_paths(record.uuid, create=True)
        _reject_if_exists(paths.metadata_path, f"PatchAttempt {record.uuid}")
        write_patch_attempt_metadata(paths, record)
        if event_log_entries is None:
            event_log_entries = record.event_log_entries
        write_event_log(paths, event_log_entries)
        if tasks_run is None:
            tasks_run = record.tasks_run
        write_tasks_run(paths, tasks_run)
        logger.debug("Created patch attempt %s", record.uuid)
        return load_patch_attempt(paths)

    def get_patch_attempt(
        self, attempt_id: Union[UUID, str]
    ) -> LoadedPatchAttemptRecord:
        paths = self.paths.patch_attempt_paths(attempt_id, create=False)
        return load_patch_attempt(paths)

    def list_patch_attempts(self) -> list[UUID]:
        return _list_record_ids(self.paths.layout.patch_attempts_path)


def _list_record_ids(root_path: Path) -> list[UUID]:
    ids = []
    for child in root_path.iterdir():
        if not child.is_dir():
            continue
        try:
            ids.append(UUID(child.name))
        except ValueError:
            continue
    ids.sort(key=lambda u: str(u))
    return ids


def _reject_if_exists(metadata_path: Path, label: str) -> None:
    if metadata_path.exists():
        raise ValueError(f"{label} already exists at {metadata_path.parent}")
