# acq4/data/structured/paths.py
# Canonical record path helpers for structured DataManager objects.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union
from uuid import UUID

import acq4.util.DataManager as dm
from acq4.logging_config import get_logger

from .constants import (
    CELLFIE_FILENAME,
    METADATA_FILENAME,
    STRUCTURED_ROOT_NAME,
)
from .constants import EVENT_LOG_FILENAME, TASKS_FILENAME
from .layout import StructuredRootLayout, ensure_structured_object_roots

logger = get_logger(__name__)


@dataclass(frozen=True)
class BaseRecordPaths:
    uuid: UUID
    directory: Path
    metadata_path: Path
    handle: dm.DirHandle


@dataclass(frozen=True)
class CellRecordPaths(BaseRecordPaths):
    cellfie_path: Path


@dataclass(frozen=True)
class PatchAttemptRecordPaths(BaseRecordPaths):
    event_log_path: Path
    tasks_path: Path


class StructuredPathHelper:
    """Resolves canonical directories for structured records."""

    def __init__(
        self,
        base_dir: Union[dm.DirHandle, str, Path],
        root_name: str = STRUCTURED_ROOT_NAME,
    ):
        self._layout = ensure_structured_object_roots(base_dir, root_name=root_name)

    @property
    def layout(self) -> StructuredRootLayout:
        return self._layout

    def cell_paths(
        self, record_uuid: Union[UUID, str], create: bool = False
    ) -> CellRecordPaths:
        uuid_obj = _normalize_uuid(record_uuid)
        directory, handle = self._resolve_record_dir(
            uuid_obj, self._layout.cells_path, create=create, record_type="cell"
        )
        return CellRecordPaths(
            uuid=uuid_obj,
            directory=directory,
            metadata_path=directory / METADATA_FILENAME,
            cellfie_path=directory / CELLFIE_FILENAME,
            handle=handle,
        )

    def patch_attempt_paths(
        self, record_uuid: Union[UUID, str], create: bool = False
    ) -> PatchAttemptRecordPaths:
        uuid_obj = _normalize_uuid(record_uuid)
        directory, handle = self._resolve_record_dir(
            uuid_obj,
            self._layout.patch_attempts_path,
            create=create,
            record_type="patch_attempt",
        )
        return PatchAttemptRecordPaths(
            uuid=uuid_obj,
            directory=directory,
            metadata_path=directory / METADATA_FILENAME,
            event_log_path=directory / EVENT_LOG_FILENAME,
            tasks_path=directory / TASKS_FILENAME,
            handle=handle,
        )

    def _resolve_record_dir(
        self,
        record_uuid: UUID,
        collection_root: Path,
        *,
        create: bool,
        record_type: str,
    ) -> tuple[Path, dm.DirHandle]:
        record_directory = collection_root / str(record_uuid)
        if record_directory.exists():
            created = False
        elif create:
            record_directory.mkdir(parents=True, exist_ok=True)
            created = True
            logger.debug(
                "Created %s record directory %s", record_type, record_directory
            )
        else:
            raise FileNotFoundError(
                f"No {record_type} directory for UUID {record_uuid}"
            )

        handle = dm.getDirHandle(str(record_directory))
        if not record_directory.exists():
            raise FileNotFoundError(
                f"Expected {record_type} directory {record_directory} to exist."
            )

        if not created:
            logger.debug(
                "Resolved %s record directory %s", record_type, record_directory
            )

        return record_directory, handle


def _normalize_uuid(value: Union[UUID, str]) -> UUID:
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Value {value!r} is not a valid UUID") from exc
