# acq4/data/structured/metrics.py
# Simple in-process counters for structured persistence events.

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class _Counters:
    cells_created: int = 0
    patch_attempts_created: int = 0
    streaming_sessions_started: int = 0
    streaming_sessions_completed: int = 0


_COUNTERS = _Counters()


def reset_counters() -> None:
    """Utility for tests to reset metrics."""
    global _COUNTERS
    _COUNTERS = _Counters()


def increment_cells_created():
    _COUNTERS.cells_created += 1


def increment_patch_attempts_created():
    _COUNTERS.patch_attempts_created += 1


def increment_streaming_started():
    _COUNTERS.streaming_sessions_started += 1


def increment_streaming_completed():
    _COUNTERS.streaming_sessions_completed += 1


def snapshot() -> Dict[str, int]:
    """Return a dict copy of the current counters."""
    return {
        "cells_created_total": _COUNTERS.cells_created,
        "patch_attempts_created_total": _COUNTERS.patch_attempts_created,
        "streaming_sessions_started_total": _COUNTERS.streaming_sessions_started,
        "streaming_sessions_completed_total": _COUNTERS.streaming_sessions_completed,
    }
