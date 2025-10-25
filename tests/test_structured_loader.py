# tests/test_structured_loader.py
# Ensures loader rehydrates attachments and detects corruption.

import json
from uuid import uuid4

import pytest

from acq4.data.structured.loader import (
    AttachmentIntegrityError,
    load_cell,
    load_patch_attempt,
)
from acq4.data.structured.paths import StructuredPathHelper
from acq4.data.structured.records import (
    CellRecord,
    PatchAttemptEvent,
    PatchAttemptRecord,
)
from acq4.data.structured.storage import (
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


def test_loader_verifies_cellfie(tmp_path):
    helper = _helper(tmp_path)
    paths = helper.cell_paths(uuid4(), create=True)
    record = CellRecord(
        uuid=paths.uuid,
        global_position_m=(0.0, 0.0, 0.0),
        initial_resistance_ohm=5e6,
    )
    write_cell_metadata(paths, record)
    write_cellfie_image(paths, b"hello")

    loaded = load_cell(paths)
    assert loaded.record == record
    assert loaded.cellfie is not None
    assert loaded.cellfie.info.size_bytes == 5
    assert loaded.cellfie.data == b"hello"

    # corrupt file
    paths.cellfie_path.write_bytes(b"oops")
    with pytest.raises(AttachmentIntegrityError):
        load_cell(paths)


def test_loader_verifies_patch_attachments(tmp_path):
    helper = _helper(tmp_path)
    paths = helper.patch_attempt_paths(uuid4(), create=True)
    record = PatchAttemptRecord(
        uuid=paths.uuid,
        cell_uuid=uuid4(),
        event_log_entries=(
            PatchAttemptEvent(timestamp_s=0.0, device="MultiPatch", payload={}),
        ),
    )
    write_patch_attempt_metadata(paths, record)
    write_event_log(paths, record.event_log_entries)
    write_tasks_run(paths, ["seal"])

    loaded = load_patch_attempt(paths)
    assert loaded.record == record
    assert loaded.event_log is not None
    assert (
        json.loads(loaded.event_log.data.decode("utf-8"))[0]["device"] == "MultiPatch"
    )
    assert loaded.tasks_run is not None
    assert json.loads(loaded.tasks_run.data.decode("utf-8")) == ["seal"]

    paths.event_log_path.write_text("[]")
    with pytest.raises(AttachmentIntegrityError):
        load_patch_attempt(paths)
