# TODO – Structured DataManager Prototype

## Near-Term Tasks
- [x] A1: finalize DataManager subdirectory naming + creation helper
- [x] A2: path helper utilities for Cells/PatchAttempts
- [x] B1: implement CellRecord dataclass + validators/tests
- [x] B2: implement PatchAttemptRecord dataclass + validators/tests
- [x] B3: add schema version scaffolding + upgrade hooks
- [x] C1: metadata writer/reader with atomic file ops
- [x] C2: attachment writers (cellfie, event log) + checksum capture
- [x] C3: loader that rehydrates attachments + verifies integrity
- [x] D1: StructuredObjectStore CRUD facade
- [x] D2: listing/query helpers + lightweight index
- [x] D3: locking/concurrency safeguards in store
- [x] E1: acquisition helper for streaming logs/tasks
- [x] E2: prototype integration with representative acquisition path
- [x] E3: logging/metrics emission on persistence events
- [ ] F1: unit test suite for validators/serializers
- [x] F2: integration test for Cell↔PatchAttempt linking
- [x] F3: end-to-end scenario + documentation updates

## Notes
- Update this file as milestones land; keep tasks small enough to complete within a short coding session per AGENTS guidance.
