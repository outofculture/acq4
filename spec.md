we're going to prototype using acq4.util.DataManager.DataManager to be more database-like. let's start with Cell and Patch Attempt objects.

Cell
----
  - uuid
  - global position
  - cellfie (either just the 20µm³ region or the entire FoV which includes it)
  - initial resistance
  - notes

Patch Attempt
-------------
  - uuid
  - cell id
  - event log from all relevant devices (currently saved as the multipatch log)
  - successful seal
  - successful reseal (if attempted)
  - tasks run
  - notes

the DataManager should store these objects without `.index` file metadata, but we're still unsure of our final format. for now, pick something obvious and simple, like a uuid-named folder with a 
`metadata.json` file and all relevant data files named meaningfully. oh, and I guess this will be in an acq4-controlled top-level directory inside whatever directory the DataManager is initialized with.

## Structured Object Filesystem Contract

The helpers in `acq4.data.structured` establish the canonical layout for structured objects so devices/modules never have to hard-code paths.

```
<data-manager-root>/
└── structured_objects/                    # created via ensure_structured_object_roots
    ├── cells/
    │   └── <cell-uuid>/
    │       ├── metadata.json             # CellRecord payload
    │       └── cellfie.tif               # Optional image attachment
    └── patch_attempts/
        └── <patch-attempt-uuid>/
            ├── metadata.json             # PatchAttempt metadata (TBD)
            ├── event-log.json            # multipatch log payload
            └── tasks-run.json            # execution summary
```

Contract highlights:

- Directory names are UUID strings, and any required directories are created via `StructuredPathHelper` which also ensures `.index` files are never written in those locations.
- Canonical filenames live in `acq4.data.structured.constants` so the metadata writers/readers never diverge (`metadata.json`, `cellfie.tif`, `event-log.json`, `tasks-run.json`).
- `metadata.json` always includes SI units (meters for `global_position_m`, ohms for `initial_resistance_ohm`) and declares a schema version (e.g. `cell-record.v1`) so migrations remain tractable.
- Attachments such as `cellfie.tif` or `event-log.json` live alongside the metadata to keep rsync/databrowser flows straightforward; metadata references these filenames directly.

All new code should use `ensure_structured_object_roots` + `StructuredPathHelper` to resolve directories, and typed record helpers (`CellRecord`, `PatchAttemptRecord`) to produce metadata dictionaries. `PatchAttemptRecord` enforces cross-links to existing cells (`cell_uuid`), captures success booleans, tasks run, and a canonical list of multipatch events (`timestamp_s`, `device`, `payload`). The schema helper (`acq4.data.structured.schema`) validates incoming metadata and provides upgrade hooks so future migrations can be applied centrally rather than in each caller.

### Persistence helpers

- `acq4.data.structured.storage.write_{cell,patch_attempt}_metadata(...)` writes JSON atomically (temp file + `os.replace`) with deterministic ordering. The paired `read_*` helpers hydrate `CellRecord`/`PatchAttemptRecord`.
- Attachment helpers (`write_cellfie_image`, `write_event_log`, `write_tasks_run`) stream data into the canonical filenames, computing SHA-256 checksums + byte counts and returning `AttachmentInfo`. The helpers also persist an `attachments` manifest inside `metadata.json` so loaders know the expected filename/hash/size for each blob.
- Loader helpers (`load_cell`, `load_patch_attempt`) verify attachments against the manifest and rehydrate payloads (returning the typed record plus `AttachmentPayload` objects). Corrupted/missing files raise `AttachmentIntegrityError` with descriptive context, enabling call-sites to surface actionable errors to operators.
- `StructuredObjectStore` (`acq4.data.structured.store`) wraps all of the above, providing `create_*`, `get_*`, and `list_*` helpers that enforce UUID collisions, validate referenced cells before creating patch attempts, and route writes through the persistence/loader layers. The store serializes threaded callers with an internal `RLock`, uses per-record `.lock` files so concurrent processes can’t clobber directories (raising `StructuredLockError` on timeout), and exposes `stream_patch_attempt(uuid)` which returns a `StreamingPatchLogger` for acquisition modules to append multipatch events/tasks incrementally.

## Demo Integration & Metrics

Run `python -m acq4.integration.structured_patch_demo --output <path>` to see the full workflow: the script creates a demo cell, streams a synthetic patch attempt with event log entries + tasks via `StructuredObjectStore.stream_patch_attempt`, and leaves behind a fully-populated `structured_objects/` tree for inspection. The script also prints the `acq4.data.structured.metrics.snapshot()` so you can observe counters such as `cells_created_total`, `patch_attempts_created_total`, and streaming session counts.

Automated coverage lives in `tests/test_structured_integration.py`, which creates a cell + patch attempt, streams additional events via the store, and asserts the linkage and metrics counters are correct.

## End-to-End Scenario

1. Run `python -m acq4.integration.structured_patch_demo --output <path>` to generate a demo dataset.
2. Execute `pytest tests/test_structured_integration.py tests/test_structured_patch_demo.py` to validate the end-to-end flow (cell creation → patch attempt streaming → metrics snapshot).
3. Inspect `<path>/structured_objects/` to confirm the filesystem contract documented above.
