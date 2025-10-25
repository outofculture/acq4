# tests/test_structured_patch_demo.py
# Exercises the structured patch demo integration.

from pathlib import Path

from acq4.integration.structured_patch_demo import run_demo


def test_run_demo_creates_records(tmp_path):
    result = run_demo(tmp_path / "out")
    assert "cell_uuid" in result
    assert "patch_uuid" in result
    assert result["event_log_entries"] == 2
