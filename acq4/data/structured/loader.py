# acq4/data/structured/loader.py
# Attachment-aware loaders that verify integrity before returning payloads.

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

from acq4.logging_config import get_logger

from .paths import CellRecordPaths, PatchAttemptRecordPaths
from .records import CellRecord, PatchAttemptRecord
from .storage import (
    AttachmentInfo,
    read_cell_metadata,
    read_patch_attempt_metadata,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class AttachmentPayload:
    info: AttachmentInfo
    path: Path
    data: bytes


@dataclass(frozen=True)
class LoadedCellRecord:
    record: CellRecord
    cellfie: Optional[AttachmentPayload]


@dataclass(frozen=True)
class LoadedPatchAttemptRecord:
    record: PatchAttemptRecord
    event_log: Optional[AttachmentPayload]
    tasks_run: Optional[AttachmentPayload]


class AttachmentIntegrityError(RuntimeError):
    pass


def load_cell(paths: CellRecordPaths) -> LoadedCellRecord:
    metadata = _read_metadata_dict(paths.metadata_path)
    record = read_cell_metadata(paths)
    attachments = metadata.get("attachments", {})

    cellfie_payload = None
    if attachments.get("cellfie"):
        cellfie_payload = _validate_and_load(
            paths.cellfie_path, attachments["cellfie"], "cellfie"
        )

    return LoadedCellRecord(record=record, cellfie=cellfie_payload)


def load_patch_attempt(paths: PatchAttemptRecordPaths) -> LoadedPatchAttemptRecord:
    metadata = _read_metadata_dict(paths.metadata_path)
    record = read_patch_attempt_metadata(paths)
    attachments = metadata.get("attachments", {})

    event_payload = None
    tasks_payload = None

    if attachments.get("event_log"):
        event_payload = _validate_and_load(
            paths.event_log_path, attachments["event_log"], "event_log"
        )
    if attachments.get("tasks_run"):
        tasks_payload = _validate_and_load(
            paths.tasks_path, attachments["tasks_run"], "tasks_run"
        )

    return LoadedPatchAttemptRecord(
        record=record, event_log=event_payload, tasks_run=tasks_payload
    )


def _read_metadata_dict(path: Path) -> Mapping[str, object]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_and_load(
    path: Path, manifest: Mapping[str, object], label: str
) -> AttachmentPayload:
    if not path.exists():
        raise AttachmentIntegrityError(f"Attachment '{label}' missing at {path}")

    data = path.read_bytes()
    size = len(data)
    checksum = hashlib.sha256(data).hexdigest()

    expected_size = manifest.get("size_bytes")
    expected_checksum = manifest.get("sha256")

    if expected_size is not None and size != expected_size:
        raise AttachmentIntegrityError(
            f"Attachment '{label}' size mismatch (expected {expected_size}, got {size})"
        )
    if expected_checksum is not None and checksum != expected_checksum:
        raise AttachmentIntegrityError(
            f"Attachment '{label}' checksum mismatch (expected {expected_checksum}, got {checksum})"
        )

    logger.debug("Verified attachment '%s' (%s)", label, path)
    info = AttachmentInfo(filename=path.name, size_bytes=size, sha256=checksum)
    return AttachmentPayload(info=info, path=path, data=data)
