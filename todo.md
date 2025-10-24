# TODO – Structured DataManager Prototype

## Near-Term Tasks
- [x] A1: finalize DataManager subdirectory naming + creation helper
- [x] A2: path helper utilities for Cells/PatchAttempts
- [x] B1: implement CellRecord dataclass + validators/tests
- [x] B2: implement PatchAttemptRecord dataclass + validators/tests
- [x] B3: add schema version scaffolding + upgrade hooks
- [x] C1: metadata writer/reader with atomic file ops
- [x] C2: attachment writers (cellfie, event log) + checksum capture
- [ ] C3: loader that rehydrates attachments + verifies integrity
- [ ] D1: StructuredObjectStore CRUD facade
- [ ] D2: listing/query helpers + lightweight index
- [ ] D3: locking/concurrency safeguards in store
- [ ] E1: acquisition helper for streaming logs/tasks
- [ ] E2: prototype integration with representative acquisition path
- [ ] E3: logging/metrics emission on persistence events
- [ ] F1: unit test suite for validators/serializers
- [ ] F2: integration test for Cell↔PatchAttempt linking
- [ ] F3: end-to-end scenario + documentation updates

## Notes
- Update this file as milestones land; keep tasks small enough to complete within a short coding session per AGENTS guidance.
