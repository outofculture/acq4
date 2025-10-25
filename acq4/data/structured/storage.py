# acq4/data/structured/storage.py
# Persistence helpers for structured DataManager records and attachments.

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Iterable, Mapping, Sequence, Union
from uuid import UUID

from acq4.logging_config import get_logger

from .paths import CellRecordPaths, PatchAttemptRecordPaths
from .records import (
    CellRecord,
    PatchAttemptEvent,
    PatchAttemptRecord,
)

logger = get_logger(__name__)

CHUNK_SIZE = 1024 * 1024
DEFAULT_ENCODING = "utf-8"

BinarySource = Union[bytes, bytearray, memoryview, str, os.PathLike[str], IO[bytes]]


@dataclass(frozen=True)
class AttachmentInfo:
    filename: str
    size_bytes: int
    sha256: str

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


def write_cell_metadata(paths: CellRecordPaths, record: CellRecord) -> None:
    _atomic_write_json(paths.metadata_path, record.to_metadata_dict())
    logger.debug("Wrote cell metadata to %s", paths.metadata_path)


def read_cell_metadata(paths: CellRecordPaths) -> CellRecord:
    data = _read_json(paths.metadata_path)
    return CellRecord.from_metadata_dict(data)


def write_patch_attempt_metadata(
    paths: PatchAttemptRecordPaths, record: PatchAttemptRecord
) -> None:
    _atomic_write_json(paths.metadata_path, record.to_metadata_dict())
    logger.debug("Wrote patch attempt metadata to %s", paths.metadata_path)


def read_patch_attempt_metadata(paths: PatchAttemptRecordPaths) -> PatchAttemptRecord:
    data = _read_json(paths.metadata_path)
    return PatchAttemptRecord.from_metadata_dict(data)


def write_cellfie_image(paths: CellRecordPaths, source: BinarySource) -> AttachmentInfo:
    info = _write_binary_attachment(paths.cellfie_path, source)
    _update_attachment_manifest(paths.metadata_path, "cellfie", info)
    logger.debug("Persisted cellfie attachment at %s", paths.cellfie_path)
    return info


def write_event_log(
    paths: PatchAttemptRecordPaths,
    entries: Iterable[Union[PatchAttemptEvent, Mapping[str, object]]],
) -> AttachmentInfo:
    serialized = [_normalize_event_entry(entry) for entry in entries]
    payload = json.dumps(serialized, indent=2, sort_keys=True)
    info = _write_binary_attachment(
        paths.event_log_path, payload.encode(DEFAULT_ENCODING)
    )
    _update_attachment_manifest(paths.metadata_path, "event_log", info)
    logger.debug("Persisted event log with %d entries", len(serialized))
    return info


def write_tasks_run(
    paths: PatchAttemptRecordPaths, tasks: Sequence[object]
) -> AttachmentInfo:
    normalized = [_coerce_task(t) for t in tasks]
    payload = json.dumps(normalized, indent=2)
    info = _write_binary_attachment(paths.tasks_path, payload.encode(DEFAULT_ENCODING))
    _update_attachment_manifest(paths.metadata_path, "tasks_run", info)
    logger.debug("Persisted tasks-run attachment with %d entries", len(normalized))
    return info


def compute_attachment_info(path: Path) -> AttachmentInfo:
    hash_obj = hashlib.sha256()
    size = 0
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            hash_obj.update(chunk)
            size += len(chunk)
    return AttachmentInfo(
        filename=path.name,
        size_bytes=size,
        sha256=hash_obj.hexdigest(),
    )


def refresh_attachment_manifest(
    metadata_path: Path, key: str, attachment_path: Path
) -> AttachmentInfo:
    info = compute_attachment_info(attachment_path)
    _update_attachment_manifest(metadata_path, key, info)
    return info


def _atomic_write_json(path: Path, data: Mapping[str, object]) -> None:
    text = json.dumps(data, indent=2, sort_keys=True)
    _write_bytes_atomically(path, text.encode(DEFAULT_ENCODING))


def _read_json(path: Path) -> dict:
    try:
        with open(path, "r", encoding=DEFAULT_ENCODING) as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Metadata file missing at {path}") from exc


def _write_binary_attachment(path: Path, source: BinarySource) -> AttachmentInfo:
    hash_obj = hashlib.sha256()
    size = 0

    def update(chunk: bytes) -> None:
        nonlocal size
        if not chunk:
            return
        hash_obj.update(chunk)
        size += len(chunk)

    _write_bytes_atomically(path, source, chunk_callback=update)
    return AttachmentInfo(
        filename=path.name, size_bytes=size, sha256=hash_obj.hexdigest()
    )


def _write_bytes_atomically(
    destination: Path,
    data: BinarySource,
    *,
    chunk_callback: callable | None = None,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(destination.parent), prefix=f".{destination.name}.tmp."
    )
    try:
        with os.fdopen(tmp_fd, "wb") as handle:
            for chunk in _iter_chunks(data):
                handle.write(chunk)
                if chunk_callback is not None:
                    chunk_callback(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, destination)
    except Exception:
        logger.exception(
            "Failed writing %s; removing temp file %s", destination, tmp_path
        )
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def _iter_chunks(data: BinarySource):
    if isinstance(data, (bytes, bytearray, memoryview)):
        chunk = bytes(data)
        if chunk:
            yield chunk
        return

    if isinstance(data, (str, os.PathLike)):
        with open(os.fspath(data), "rb") as handle:
            yield from _iter_chunks(handle)
        return

    if hasattr(data, "read"):
        while True:
            chunk = data.read(CHUNK_SIZE)
            if not chunk:
                break
            yield chunk
        return

    raise TypeError(f"Unsupported binary source type: {type(data)}")


def _normalize_event_entry(
    entry: Union[PatchAttemptEvent, Mapping[str, object]],
) -> Mapping[str, object]:
    if isinstance(entry, PatchAttemptEvent):
        return entry.to_dict()
    if isinstance(entry, Mapping):
        if "timestamp_s" not in entry or "device" not in entry:
            raise ValueError("Event log mappings require 'timestamp_s' and 'device'")
        return dict(entry)
    raise TypeError(f"Unsupported event log entry type: {type(entry)}")


def _coerce_task(task: object) -> str:
    text = str(task).strip()
    if not text:
        raise ValueError("tasks_run entries must be non-empty strings")
    return text


def _update_attachment_manifest(
    metadata_path: Path, key: str, info: AttachmentInfo
) -> None:
    metadata = _read_json(metadata_path)
    attachments = dict(metadata.get("attachments", {}))
    attachments[key] = info.to_dict()
    metadata["attachments"] = attachments
    _atomic_write_json(metadata_path, metadata)
