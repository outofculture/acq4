# acq4/data/structured/streaming.py
# Streaming helpers for patch attempt logging.

from __future__ import annotations

import json
import os
from contextlib import AbstractContextManager
from typing import Iterable, Mapping, MutableSequence, Union

from acq4.logging_config import get_logger

from .metrics import increment_streaming_completed, increment_streaming_started
from .paths import PatchAttemptRecordPaths
from .records import PatchAttemptEvent
from .storage import refresh_attachment_manifest, write_tasks_run

logger = get_logger(__name__)


class StreamingPatchLogger(AbstractContextManager["StreamingPatchLogger"]):
    """Incrementally streams patch attempt event log entries and tasks to disk."""

    def __init__(self, paths: PatchAttemptRecordPaths):
        self._paths = paths
        self._event_tmp = paths.event_log_path.with_suffix(".event.tmp")
        self._event_file = None
        self._event_count = 0
        self._tasks: MutableSequence[str] = []
        self._closed = False
        self._lock_exit = None

    def set_lock_context(self, lock_context):
        """Store the lock context (entered by StructuredObjectStore)."""
        self._lock_exit = lock_context

    def __enter__(self) -> "StreamingPatchLogger":
        self._event_file = open(self._event_tmp, "w", encoding="utf-8")
        self._event_file.write("[\n")
        increment_streaming_started()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def append_event(
        self, event: Union[PatchAttemptEvent, Mapping[str, object]]
    ) -> None:
        if self._closed or self._event_file is None:
            raise RuntimeError("StreamingPatchLogger is closed")
        payload = (
            event.to_dict() if isinstance(event, PatchAttemptEvent) else dict(event)
        )
        if "timestamp_s" not in payload or "device" not in payload:
            raise ValueError("Event must include 'timestamp_s' and 'device'")
        if self._event_count > 0:
            self._event_file.write(",\n")
        json.dump(payload, self._event_file, ensure_ascii=False, separators=(",", ":"))
        self._event_count += 1

    def record_task(self, task_name: str) -> None:
        text = str(task_name).strip()
        if not text:
            raise ValueError("task_name must be non-empty")
        self._tasks.append(text)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True

        if self._event_file is not None:
            self._event_file.write("\n]\n")
            self._event_file.flush()
            os.fsync(self._event_file.fileno())
            self._event_file.close()
            os.replace(self._event_tmp, self._paths.event_log_path)
            logger.debug(
                "Flushed %d streaming events to %s",
                self._event_count,
                self._paths.event_log_path,
            )
            refresh_attachment_manifest(
                self._paths.metadata_path, "event_log", self._paths.event_log_path
            )

        # Tasks are typically modest in size; rewrite using storage helper.
        write_tasks_run(self._paths, self._tasks)

        increment_streaming_completed()
        if self._lock_exit is not None:
            self._lock_exit.__exit__(None, None, None)
