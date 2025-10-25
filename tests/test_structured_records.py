# tests/test_structured_records.py
# Covers CellRecord and PatchAttemptRecord serialization/validation.

import math
from uuid import uuid4

import pytest

from acq4.data.structured.constants import (
    CELLFIE_FILENAME,
    CELL_RECORD_SCHEMA_VERSION,
    EVENT_LOG_FILENAME,
    PATCH_ATTEMPT_RECORD_SCHEMA_VERSION,
    TASKS_FILENAME,
)
from acq4.data.structured.records import (
    CellRecord,
    PatchAttemptEvent,
    PatchAttemptRecord,
)


def test_cell_record_round_trip():
    record = CellRecord(
        uuid=uuid4(),
        global_position_m=(1.2e-5, -3.4e-5, 5.6e-5),
        initial_resistance_ohm=7.5e6,
        notes="membrane looks spicy",
    )

    payload = record.to_metadata_dict()
    assert payload["uuid"] == str(record.uuid)
    assert payload["schema_version"] == CELL_RECORD_SCHEMA_VERSION
    assert payload["global_position_m"] == [1.2e-5, -3.4e-5, 5.6e-5]
    assert payload["initial_resistance_ohm"] == pytest.approx(7.5e6)
    assert payload["cellfie_filename"] == CELLFIE_FILENAME

    round_trip = CellRecord.from_metadata_dict(payload)
    assert round_trip == record


def test_cell_record_validation_errors():
    with pytest.raises(ValueError):
        CellRecord(
            uuid=uuid4(), global_position_m=(1e-6, 2e-6), initial_resistance_ohm=5e6
        )

    with pytest.raises(ValueError):
        CellRecord(
            uuid=uuid4(),
            global_position_m=(0.0, 0.0, 0.0),
            initial_resistance_ohm=math.nan,
        )

    with pytest.raises(ValueError):
        CellRecord(
            uuid="not-a-uuid",
            global_position_m=(0.0, 0.0, 0.0),
            initial_resistance_ohm=5e6,
        )


def test_patch_attempt_record_round_trip():
    event = PatchAttemptEvent(
        timestamp_s=0.25, device="MultiPatch", payload={"resistance": 8.3e6}
    )
    record = PatchAttemptRecord(
        uuid=uuid4(),
        cell_uuid=uuid4(),
        successful_seal=True,
        tasks_run=("seal", "break_in"),
        event_log_entries=(event,),
        notes="held for 5 min",
    )

    payload = record.to_metadata_dict()
    assert payload["schema_version"] == PATCH_ATTEMPT_RECORD_SCHEMA_VERSION
    assert payload["event_log_filename"] == EVENT_LOG_FILENAME
    assert payload["tasks_filename"] == TASKS_FILENAME
    assert payload["event_log"][0]["device"] == "MultiPatch"

    hydrated = PatchAttemptRecord.from_metadata_dict(payload)
    assert hydrated == record


def test_patch_attempt_record_validation():
    with pytest.raises(ValueError):
        PatchAttemptRecord(uuid=uuid4(), cell_uuid=uuid4(), tasks_run=("",))

    with pytest.raises(ValueError):
        PatchAttemptRecord(
            uuid=uuid4(),
            cell_uuid=uuid4(),
            event_log_entries=(
                {"timestamp_s": 1.0, "device": "A"},
                {"timestamp_s": 0.5, "device": "B"},
            ),
        )


def test_schema_validation_rejects_unknown_versions():
    payload = PatchAttemptRecord(
        uuid=uuid4(),
        cell_uuid=uuid4(),
    ).to_metadata_dict()
    payload["schema_version"] = "future-version"

    with pytest.raises(ValueError):
        PatchAttemptRecord.from_metadata_dict(payload)


def test_patch_attempt_validates_event_timestamps_monotonic():
    with pytest.raises(ValueError):
        PatchAttemptRecord(
            uuid=uuid4(),
            cell_uuid=uuid4(),
            event_log_entries=(
                PatchAttemptEvent(timestamp_s=1.0, device="A", payload={}),
                PatchAttemptEvent(timestamp_s=0.5, device="B", payload={}),
            ),
        )
