# acq4/data/structured/records.py
# Domain models + validation helpers for structured metadata.

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence
from uuid import UUID

from acq4.logging_config import get_logger

from . import schema
from .constants import (
    CELLFIE_FILENAME,
    CELL_RECORD_SCHEMA_VERSION,
    EVENT_LOG_FILENAME,
    PATCH_ATTEMPT_RECORD_SCHEMA_VERSION,
    TASKS_FILENAME,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class CellRecord:
    uuid: UUID
    global_position_m: tuple[float, float, float]
    initial_resistance_ohm: float
    notes: str = ""
    cellfie_filename: str = CELLFIE_FILENAME

    def __post_init__(self):
        object.__setattr__(self, "uuid", _coerce_uuid(self.uuid))
        object.__setattr__(
            self, "global_position_m", _coerce_position(self.global_position_m)
        )
        object.__setattr__(
            self,
            "initial_resistance_ohm",
            _coerce_positive_float(
                self.initial_resistance_ohm, "initial_resistance_ohm"
            ),
        )
        object.__setattr__(self, "notes", _coerce_notes(self.notes))
        object.__setattr__(
            self,
            "cellfie_filename",
            _coerce_filename(self.cellfie_filename, CELLFIE_FILENAME),
        )

    def to_metadata_dict(self) -> dict:
        payload = {
            "schema_version": CELL_RECORD_SCHEMA_VERSION,
            "uuid": str(self.uuid),
            "global_position_m": list(self.global_position_m),
            "initial_resistance_ohm": self.initial_resistance_ohm,
            "cellfie_filename": self.cellfie_filename,
        }
        if self.notes:
            payload["notes"] = self.notes
        return payload

    @classmethod
    def from_metadata_dict(cls, payload: Mapping[str, object]) -> "CellRecord":
        data = _ensure_schema("cell_record", payload)
        return cls(
            uuid=data["uuid"],
            global_position_m=data["global_position_m"],
            initial_resistance_ohm=data["initial_resistance_ohm"],
            notes=data.get("notes", ""),
            cellfie_filename=data.get("cellfie_filename", CELLFIE_FILENAME),
        )


@dataclass(frozen=True)
class PatchAttemptEvent:
    timestamp_s: float
    device: str
    payload: object

    def __post_init__(self):
        object.__setattr__(self, "timestamp_s", _coerce_timestamp(self.timestamp_s))
        object.__setattr__(self, "device", _coerce_device(self.device))

    def to_dict(self) -> dict:
        return {
            "timestamp_s": self.timestamp_s,
            "device": self.device,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "PatchAttemptEvent":
        if "timestamp_s" not in payload or "device" not in payload:
            raise ValueError("PatchAttemptEvent requires 'timestamp_s' and 'device'")
        return cls(
            timestamp_s=payload["timestamp_s"],
            device=payload["device"],
            payload=payload.get("payload"),
        )


@dataclass(frozen=True)
class PatchAttemptRecord:
    uuid: UUID
    cell_uuid: UUID
    successful_seal: bool = False
    successful_reseal: bool = False
    tasks_run: tuple[str, ...] = ()
    notes: str = ""
    event_log_entries: tuple[PatchAttemptEvent, ...] = ()
    event_log_filename: str = EVENT_LOG_FILENAME
    tasks_filename: str = TASKS_FILENAME

    def __post_init__(self):
        object.__setattr__(self, "uuid", _coerce_uuid(self.uuid))
        object.__setattr__(self, "cell_uuid", _coerce_uuid(self.cell_uuid))
        object.__setattr__(self, "successful_seal", bool(self.successful_seal))
        object.__setattr__(self, "successful_reseal", bool(self.successful_reseal))
        object.__setattr__(self, "tasks_run", _coerce_tasks(self.tasks_run))
        object.__setattr__(self, "notes", _coerce_notes(self.notes))
        object.__setattr__(
            self, "event_log_entries", _coerce_event_log(self.event_log_entries)
        )
        object.__setattr__(
            self,
            "event_log_filename",
            _coerce_filename(self.event_log_filename, EVENT_LOG_FILENAME),
        )
        object.__setattr__(
            self,
            "tasks_filename",
            _coerce_filename(self.tasks_filename, TASKS_FILENAME),
        )

    def to_metadata_dict(self) -> dict:
        return {
            "schema_version": PATCH_ATTEMPT_RECORD_SCHEMA_VERSION,
            "uuid": str(self.uuid),
            "cell_uuid": str(self.cell_uuid),
            "successful_seal": self.successful_seal,
            "successful_reseal": self.successful_reseal,
            "tasks_run": list(self.tasks_run),
            "notes": self.notes,
            "event_log_filename": self.event_log_filename,
            "tasks_filename": self.tasks_filename,
            "event_log": [entry.to_dict() for entry in self.event_log_entries],
        }

    @classmethod
    def from_metadata_dict(cls, payload: Mapping[str, object]) -> "PatchAttemptRecord":
        data = _ensure_schema("patch_attempt_record", payload)
        entries = tuple(
            PatchAttemptEvent.from_dict(entry) for entry in data.get("event_log", [])
        )
        return cls(
            uuid=data["uuid"],
            cell_uuid=data["cell_uuid"],
            successful_seal=data.get("successful_seal", False),
            successful_reseal=data.get("successful_reseal", False),
            tasks_run=tuple(data.get("tasks_run", [])),
            notes=data.get("notes", ""),
            event_log_entries=entries,
            event_log_filename=data.get("event_log_filename", EVENT_LOG_FILENAME),
            tasks_filename=data.get("tasks_filename", TASKS_FILENAME),
        )


def _ensure_schema(
    record_type: str, payload: Mapping[str, object]
) -> Mapping[str, object]:
    mutable = dict(payload)
    return schema.registry.validate_or_upgrade(record_type, mutable)


def _coerce_uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        logger.debug("Invalid UUID value: %r", value)
        raise ValueError(f"Value {value!r} is not a valid UUID") from exc


def _coerce_position(value: object) -> tuple[float, float, float]:
    if not isinstance(value, Sequence):
        raise ValueError("global_position_m must be a 3-element sequence")
    coords = tuple(float(v) for v in value)
    if len(coords) != 3:
        raise ValueError("global_position_m must contain exactly three values")
    if not all(math.isfinite(c) for c in coords):
        raise ValueError("global_position_m values must be finite")
    return coords  # type: ignore[return-value]


def _coerce_positive_float(value: object, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field} must be positive and finite")
    return number


def _coerce_notes(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _coerce_filename(value: object, default: str) -> str:
    if not value:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _coerce_tasks(value: Iterable[object]) -> tuple[str, ...]:
    tasks = tuple(str(v).strip() for v in value)
    if any(not task for task in tasks):
        raise ValueError("tasks_run entries must be non-empty strings")
    return tasks


def _coerce_event_log(value: Iterable[object]) -> tuple[PatchAttemptEvent, ...]:
    entries = []
    last_timestamp = -math.inf
    for entry in value:
        if isinstance(entry, PatchAttemptEvent):
            evt = entry
        elif isinstance(entry, Mapping):
            evt = PatchAttemptEvent.from_dict(entry)
        else:
            raise ValueError(
                "event_log entries must be dicts or PatchAttemptEvent instances"
            )
        if evt.timestamp_s < last_timestamp:
            raise ValueError("event_log timestamps must be monotonically increasing")
        last_timestamp = evt.timestamp_s
        entries.append(evt)
    return tuple(entries)


def _coerce_timestamp(value: object) -> float:
    try:
        ts = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("timestamp_s must be numeric") from exc
    if not math.isfinite(ts):
        raise ValueError("timestamp_s must be finite")
    return ts


def _coerce_device(value: object) -> str:
    if not value:
        raise ValueError("device name must be provided")
    if isinstance(value, str):
        return value
    return str(value)


# Register schema versions (upgrade hooks can be attached later).
schema.registry.register("cell_record", CELL_RECORD_SCHEMA_VERSION)
schema.registry.register("patch_attempt_record", PATCH_ATTEMPT_RECORD_SCHEMA_VERSION)
