# tests/test_structured_integration.py
# End-to-end test ensuring cell ↔ patch attempt linking works.

from uuid import uuid4

from acq4.data.structured import (
    CellRecord,
    PatchAttemptEvent,
    PatchAttemptRecord,
    StructuredObjectStore,
    metrics_snapshot,
)
from acq4.util import DataManager as dm


def test_cell_patch_link_round_trip(tmp_path):
    root = tmp_path / "structured-root"
    root.mkdir()
    store = StructuredObjectStore(dm.getDirHandle(str(root)))

    cell = CellRecord(
        uuid=uuid4(),
        global_position_m=(1e-5, 2e-5, -3e-5),
        initial_resistance_ohm=6.2e6,
        notes="integration-cell",
    )
    store.create_cell(cell)

    patch = PatchAttemptRecord(
        uuid=uuid4(),
        cell_uuid=cell.uuid,
        successful_seal=True,
        tasks_run=("seal",),
        event_log_entries=(
            PatchAttemptEvent(timestamp_s=0.0, device="A", payload={"state": "start"}),
        ),
        notes="integration-patch",
    )
    store.create_patch_attempt(patch)

    with store.stream_patch_attempt(patch.uuid) as logger:
        logger.append_event(
            PatchAttemptEvent(timestamp_s=0.1, device="A", payload={"state": "break"})
        )
        logger.record_task("break_in")

    fetched_patch = store.get_patch_attempt(patch.uuid)
    assert fetched_patch.record.cell_uuid == cell.uuid
    assert fetched_patch.record.successful_seal is True
    assert len(store.list_cells()) == 1
    assert len(store.list_patch_attempts()) == 1

    metrics = metrics_snapshot()
    assert metrics["cells_created_total"] == 1
    assert metrics["patch_attempts_created_total"] == 1
