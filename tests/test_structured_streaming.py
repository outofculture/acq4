# tests/test_structured_streaming.py
# Validates StreamingPatchLogger behavior.

import json
from uuid import uuid4

import pytest

from acq4.data.structured.metrics import reset_counters, snapshot
from acq4.data.structured.records import (
    CellRecord,
    PatchAttemptEvent,
    PatchAttemptRecord,
)
from acq4.data.structured.store import StructuredObjectStore

from acq4.util import DataManager as dm


def _store(tmp_path):
    root = tmp_path / "dm-root"
    root.mkdir()
    reset_counters()
    return StructuredObjectStore(dm.getDirHandle(str(root)))


def test_streaming_logger_writes_incrementally(tmp_path):
    store = _store(tmp_path)
    cell = CellRecord(
        uuid=uuid4(), global_position_m=(0, 0, 0), initial_resistance_ohm=5e6
    )
    store.create_cell(cell)
    patch = PatchAttemptRecord(
        uuid=uuid4(),
        cell_uuid=cell.uuid,
        event_log_entries=(),
        tasks_run=(),
    )
    store.create_patch_attempt(patch)

    with store.stream_patch_attempt(patch.uuid) as logger:
        logger.append_event(
            PatchAttemptEvent(timestamp_s=0.0, device="A", payload={"state": "start"})
        )
        logger.append_event(
            {"timestamp_s": 0.1, "device": "B", "payload": {"state": "seal"}}
        )
        logger.record_task("seal")
        logger.record_task("break-in")

    # Ensure JSON array persisted
    loaded = store.get_patch_attempt(patch.uuid)
    event_data = json.loads(loaded.event_log.data.decode("utf-8"))
    assert len(event_data) == 2
    assert event_data[1]["device"] == "B"
    assert json.loads(loaded.tasks_run.data.decode("utf-8")) == ["seal", "break-in"]
    metrics = snapshot()
    assert metrics["streaming_sessions_started_total"] == 1
    assert metrics["streaming_sessions_completed_total"] == 1


def test_streaming_logger_errors_when_closed(tmp_path):
    store = _store(tmp_path)
    cell = CellRecord(
        uuid=uuid4(), global_position_m=(0, 0, 0), initial_resistance_ohm=5e6
    )
    store.create_cell(cell)
    patch = PatchAttemptRecord(
        uuid=uuid4(), cell_uuid=cell.uuid, event_log_entries=(), tasks_run=()
    )
    store.create_patch_attempt(patch)

    logger = store.stream_patch_attempt(patch.uuid)
    with logger:
        logger.append_event(PatchAttemptEvent(timestamp_s=0.0, device="A", payload={}))

    with pytest.raises(RuntimeError):
        logger.append_event({"timestamp_s": 1.0, "device": "B", "payload": {}})
