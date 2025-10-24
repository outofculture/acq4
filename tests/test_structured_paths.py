# tests/test_structured_paths.py
# Verifies structured DataManager layout and record path helpers.

import uuid
from pathlib import Path

import pytest

from acq4.util import DataManager as dm
from acq4.data.structured.constants import (
    CELLFIE_FILENAME,
    CELL_COLLECTION_NAME,
    EVENT_LOG_FILENAME,
    METADATA_FILENAME,
    PATCH_ATTEMPT_COLLECTION_NAME,
    TASKS_FILENAME,
)
from acq4.data.structured.layout import (
    STRUCTURED_ROOT_NAME,
    ensure_structured_object_roots,
)
from acq4.data.structured.paths import StructuredPathHelper


def _dm_root_handle(tmp_path):
    root_dir = tmp_path / "dm-root"
    root_dir.mkdir()
    return dm.getDirHandle(str(root_dir))


def test_ensure_structured_object_roots_creates_expected_layout(tmp_path):
    root_handle = _dm_root_handle(tmp_path)
    layout = ensure_structured_object_roots(root_handle)

    assert layout.root_path == Path(root_handle.name()) / STRUCTURED_ROOT_NAME
    assert layout.cells_path == layout.root_path / CELL_COLLECTION_NAME
    assert (
        layout.patch_attempts_path == layout.root_path / PATCH_ATTEMPT_COLLECTION_NAME
    )

    for path in [layout.root_path, layout.cells_path, layout.patch_attempts_path]:
        assert path.is_dir()
        assert not (path / ".index").exists()


def test_cell_paths_reject_invalid_uuid(tmp_path):
    helper = StructuredPathHelper(_dm_root_handle(tmp_path))
    with pytest.raises(ValueError):
        helper.cell_paths("definitely-not-a-uuid")


def test_end_to_end_layout_for_cell_and_patch_attempt(tmp_path):
    helper = StructuredPathHelper(_dm_root_handle(tmp_path))

    cell_uuid = uuid.uuid4()
    cell_paths = helper.cell_paths(cell_uuid, create=True)
    assert cell_paths.directory.is_dir()
    assert cell_paths.metadata_path == cell_paths.directory / METADATA_FILENAME
    assert cell_paths.cellfie_path == cell_paths.directory / CELLFIE_FILENAME

    patch_uuid = uuid.uuid4()
    with pytest.raises(FileNotFoundError):
        helper.patch_attempt_paths(patch_uuid, create=False)

    patch_paths = helper.patch_attempt_paths(patch_uuid, create=True)
    assert patch_paths.directory.is_dir()
    assert patch_paths.metadata_path == patch_paths.directory / METADATA_FILENAME
    assert patch_paths.event_log_path == patch_paths.directory / EVENT_LOG_FILENAME
    assert patch_paths.tasks_path == patch_paths.directory / TASKS_FILENAME

    # Re-run in read-only mode to ensure idempotency
    again = helper.patch_attempt_paths(patch_uuid, create=False)
    assert again.directory == patch_paths.directory
