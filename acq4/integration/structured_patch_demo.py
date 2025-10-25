# acq4/integration/structured_patch_demo.py
# CLI demo streaming a synthetic patch attempt into the structured store.

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path
from uuid import uuid4

from acq4.data.structured import (
    CellRecord,
    PatchAttemptEvent,
    PatchAttemptRecord,
    StructuredObjectStore,
    metrics_snapshot,
)


def run_demo(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    store = StructuredObjectStore(output_dir)

    cell_record = CellRecord(
        uuid=uuid4(),
        global_position_m=tuple(random.uniform(-1e-4, 1e-4) for _ in range(3)),
        initial_resistance_ohm=5e6 + random.random() * 1e6,
        notes="demo cell",
    )
    store.create_cell(cell_record)

    patch_record = PatchAttemptRecord(
        uuid=uuid4(),
        cell_uuid=cell_record.uuid,
        event_log_entries=(),
        tasks_run=(),
        notes="demo patch attempt",
    )
    store.create_patch_attempt(patch_record)

    with store.stream_patch_attempt(patch_record.uuid) as logger:
        now = time.monotonic()
        logger.append_event(
            PatchAttemptEvent(
                timestamp_s=now, device="MultiPatch", payload={"state": "seal"}
            )
        )
        logger.record_task("seal")
        time.sleep(0.01)
        logger.append_event(
            PatchAttemptEvent(
                timestamp_s=time.monotonic(),
                device="MultiPatch",
                payload={"state": "break-in"},
            )
        )
        logger.record_task("break-in")

    loaded = store.get_patch_attempt(patch_record.uuid)
    result = {
        "cell_uuid": str(cell_record.uuid),
        "patch_uuid": str(patch_record.uuid),
        "event_log_entries": len(json.loads(loaded.event_log.data.decode("utf-8"))),
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Structured DataManager patch demo")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.cwd() / "structured_demo",
        help="Directory where structured objects will be written",
    )
    args = parser.parse_args(argv)
    result = run_demo(args.output)
    print("Structured patch demo complete:", json.dumps(result, indent=2))
    print("Metrics snapshot:", json.dumps(metrics_snapshot(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
