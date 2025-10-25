# acq4/data/structured/__init__.py
# Convenience exports for structured DataManager helpers.

from .constants import (
    CELLFIE_FILENAME,
    CELL_COLLECTION_NAME,
    CELL_RECORD_SCHEMA_VERSION,
    EVENT_LOG_FILENAME,
    METADATA_FILENAME,
    PATCH_ATTEMPT_COLLECTION_NAME,
    PATCH_ATTEMPT_RECORD_SCHEMA_VERSION,
    STRUCTURED_ROOT_NAME,
    TASKS_FILENAME,
)
from .layout import StructuredRootLayout, ensure_structured_object_roots
from .loader import (
    AttachmentIntegrityError,
    AttachmentPayload,
    LoadedCellRecord,
    LoadedPatchAttemptRecord,
    load_cell,
    load_patch_attempt,
)
from .paths import CellRecordPaths, PatchAttemptRecordPaths, StructuredPathHelper
from .records import CellRecord, PatchAttemptEvent, PatchAttemptRecord
from .schema import registry as schema_registry
from .storage import (
    AttachmentInfo,
    read_cell_metadata,
    read_patch_attempt_metadata,
    write_cell_metadata,
    write_cellfie_image,
    write_event_log,
    write_patch_attempt_metadata,
    write_tasks_run,
)

__all__ = [
    "STRUCTURED_ROOT_NAME",
    "CELL_COLLECTION_NAME",
    "PATCH_ATTEMPT_COLLECTION_NAME",
    "METADATA_FILENAME",
    "CELLFIE_FILENAME",
    "EVENT_LOG_FILENAME",
    "TASKS_FILENAME",
    "CELL_RECORD_SCHEMA_VERSION",
    "PATCH_ATTEMPT_RECORD_SCHEMA_VERSION",
    "StructuredRootLayout",
    "ensure_structured_object_roots",
    "CellRecordPaths",
    "PatchAttemptRecordPaths",
    "StructuredPathHelper",
    "CellRecord",
    "PatchAttemptRecord",
    "PatchAttemptEvent",
    "schema_registry",
    "AttachmentInfo",
    "write_cell_metadata",
    "read_cell_metadata",
    "write_patch_attempt_metadata",
    "read_patch_attempt_metadata",
    "write_cellfie_image",
    "write_event_log",
    "write_tasks_run",
    "AttachmentPayload",
    "LoadedCellRecord",
    "LoadedPatchAttemptRecord",
    "load_cell",
    "load_patch_attempt",
    "AttachmentIntegrityError",
]
