# tests/test_structured_store.py
# Verifies StructuredObjectStore CRUD and listing helpers.

import queue
import threading
from uuid import uuid4

import pytest

from acq4.data.structured.records import (
    CellRecord,
    PatchAttemptEvent,
    PatchAttemptRecord,
)
from acq4.data.structured.store import StructuredLockError, StructuredObjectStore
from acq4.util import DataManager as dm


def _store(tmp_path):
    root = tmp_path / "dm-root"
    root.mkdir()
    handle = dm.getDirHandle(str(root))
    return StructuredObjectStore(handle)


def test_create_and_get_cell(tmp_path):
    store = _store(tmp_path)
    cell_id = uuid4()
    record = CellRecord(
        uuid=cell_id, global_position_m=(0, 0, 0), initial_resistance_ohm=5e6
    )
    loaded = store.create_cell(record, cellfie_source=b"cellfie")
    assert loaded.record == record
    assert loaded.cellfie is not None
    assert loaded.cellfie.data == b"cellfie"

    fetched = store.get_cell(cell_id)
    assert fetched.record == record

    with pytest.raises(ValueError):
        store.create_cell(record)


def test_create_patch_requires_cell(tmp_path):
    store = _store(tmp_path)
    cell_record = CellRecord(
        uuid=uuid4(), global_position_m=(0, 0, 0), initial_resistance_ohm=5e6
    )
    store.create_cell(cell_record)

    patch_record = PatchAttemptRecord(
        uuid=uuid4(),
        cell_uuid=cell_record.uuid,
        event_log_entries=(
            PatchAttemptEvent(timestamp_s=0.0, device="MultiPatch", payload={}),
        ),
        tasks_run=("seal",),
    )

    loaded = store.create_patch_attempt(patch_record)
    assert loaded.record == patch_record
    assert loaded.event_log is not None
    assert loaded.tasks_run is not None

    with pytest.raises(ValueError):
        store.create_patch_attempt(patch_record)

    missing_patch = PatchAttemptRecord(
        uuid=uuid4(),
        cell_uuid=uuid4(),
        event_log_entries=(),
    )
    with pytest.raises(ValueError):
        store.create_patch_attempt(missing_patch)


def test_listing_and_predicates(tmp_path):
    store = _store(tmp_path)
    cell_ids = [uuid4() for _ in range(3)]
    for idx, cid in enumerate(cell_ids):
        record = CellRecord(
            uuid=cid,
            global_position_m=(0, 0, 0),
            initial_resistance_ohm=5e6,
            notes=f"cell-{idx}",
        )
        store.create_cell(record)

    summaries = store.list_cells()
    assert {s.uuid for s in summaries} == set(cell_ids)
    filtered = list(store.iter_cells(predicate=lambda s: s.notes == "cell-1"))
    assert len(filtered) == 1

    patch_ids = []
    base_cell = cell_ids[0]
    for _ in range(2):
        patch = PatchAttemptRecord(
            uuid=uuid4(), cell_uuid=base_cell, event_log_entries=()
        )
        store.create_patch_attempt(patch)
        patch_ids.append(patch.uuid)

    summaries = store.list_patch_attempts()
    assert {s.uuid for s in summaries} == set(patch_ids)
    filtered = list(
        store.iter_patch_attempts(predicate=lambda s: s.cell_uuid == base_cell)
    )
    assert len(filtered) == 2


def test_concurrent_create_respects_lock(tmp_path):
    store = _store(tmp_path)
    cell_id = uuid4()
    record = CellRecord(
        uuid=cell_id, global_position_m=(0, 0, 0), initial_resistance_ohm=5e6
    )

    # Manually hold the lock so the worker times out.
    paths = store.paths.cell_paths(cell_id, create=True)
    paths.directory.mkdir(parents=True, exist_ok=True)

    results = queue.Queue()

    def worker():
        try:
            store.create_cell(record)
            results.put("success")
        except StructuredLockError:
            results.put("locked")

    with store._record_write_lock(paths.directory, timeout=0.2):
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()

    assert results.get() == "locked"
