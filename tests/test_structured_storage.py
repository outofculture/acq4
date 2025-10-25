# tests/test_structured_storage.py
# Verifies structured metadata/attachment writers.

import hashlib
import json
from uuid import uuid4

import pytest

from acq4.data.structured.paths import StructuredPathHelper
from acq4.data.structured.records import (
    CellRecord,
    PatchAttemptEvent,
    PatchAttemptRecord,
)
from acq4.data.structured.storage import (
    AttachmentInfo,
    read_cell_metadata,
    read_patch_attempt_metadata,
    write_cell_metadata,
    write_cellfie_image,
    write_event_log,
    write_patch_attempt_metadata,
    write_tasks_run,
)
from acq4.util import DataManager as dm


def _helper(tmp_path):
    root = tmp_path / "dm-root"
    root.mkdir()
    return StructuredPathHelper(dm.getDirHandle(str(root)))


def test_write_and_read_cell_metadata(tmp_path):
    helper = _helper(tmp_path)
    paths = helper.cell_paths(uuid4(), create=True)
    record = CellRecord(
        uuid=paths.uuid,
        global_position_m=(1e-5, 2e-5, 3e-5),
        initial_resistance_ohm=7.2e6,
        notes="first pass",
    )

    write_cell_metadata(paths, record)
    assert read_cell_metadata(paths) == record

    updated = CellRecord(
        uuid=paths.uuid,
        global_position_m=(1e-5, 2e-5, 3e-5),
        initial_resistance_ohm=8.2e6,
        notes="updated",
    )
    write_cell_metadata(paths, updated)
    assert read_cell_metadata(paths) == updated
    assert not list(paths.directory.glob("metadata.json.tmp.*"))


def test_write_and_read_patch_metadata(tmp_path):
    helper = _helper(tmp_path)
    paths = helper.patch_attempt_paths(uuid4(), create=True)

    record = PatchAttemptRecord(
        uuid=paths.uuid,
        cell_uuid=uuid4(),
        successful_seal=True,
        tasks_run=("seal",),
        event_log_entries=(
            PatchAttemptEvent(
                timestamp_s=0.0, device="MultiPatch", payload={"note": "start"}
            ),
        ),
    )

    write_patch_attempt_metadata(paths, record)
    loaded = read_patch_attempt_metadata(paths)
    assert loaded == record


def test_cellfie_writer_returns_checksum(tmp_path):
    helper = _helper(tmp_path)
    paths = helper.cell_paths(uuid4(), create=True)
    record = CellRecord(
        uuid=paths.uuid,
        global_position_m=(0.0, 0.0, 0.0),
        initial_resistance_ohm=5e6,
    )
    write_cell_metadata(paths, record)

    payload = b"\x00\x01\x02"
    info = write_cellfie_image(paths, payload)
    assert isinstance(info, AttachmentInfo)
    assert info.size_bytes == len(payload)
    with open(paths.cellfie_path, "rb") as fh:
        data = fh.read()
    assert data == payload
    assert hashlib.sha256(data).hexdigest() == info.sha256

    metadata = json.load(open(paths.metadata_path, "r", encoding="utf-8"))
    assert metadata["attachments"]["cellfie"]["sha256"] == info.sha256


def test_event_log_writer_serializes_entries(tmp_path):
    helper = _helper(tmp_path)
    paths = helper.patch_attempt_paths(uuid4(), create=True)
    record = PatchAttemptRecord(
        uuid=paths.uuid,
        cell_uuid=uuid4(),
        event_log_entries=(),
    )
    write_patch_attempt_metadata(paths, record)

    entries = [
        PatchAttemptEvent(timestamp_s=0.1, device="A", payload={"v": 1}),
        {"timestamp_s": 0.2, "device": "B", "payload": {"v": 2}},
    ]
    info = write_event_log(paths, entries)

    with open(paths.event_log_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert len(data) == 2
    assert data[0]["device"] == "A"
    assert info.size_bytes == len(
        json.dumps(data, indent=2, sort_keys=True).encode("utf-8")
    )
    metadata = json.load(open(paths.metadata_path, "r", encoding="utf-8"))
    assert metadata["attachments"]["event_log"]["sha256"] == info.sha256


def test_tasks_writer_rejects_blank_entries(tmp_path):
    helper = _helper(tmp_path)
    paths = helper.patch_attempt_paths(uuid4(), create=True)
    record = PatchAttemptRecord(
        uuid=paths.uuid,
        cell_uuid=uuid4(),
        event_log_entries=(),
    )
    write_patch_attempt_metadata(paths, record)

    write_tasks_run(paths, ["seal", "break"])
    with open(paths.tasks_path, "r", encoding="utf-8") as fh:
        assert json.load(fh) == ["seal", "break"]
    metadata = json.load(open(paths.metadata_path, "r", encoding="utf-8"))
    assert metadata["attachments"]["tasks_run"]["filename"] == paths.tasks_path.name

    with pytest.raises(ValueError):
        write_tasks_run(paths, ["ok", " "])
