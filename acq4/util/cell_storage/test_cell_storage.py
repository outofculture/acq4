"""
Tests for the cell storage system.
"""
import os
import pytest
import tempfile
import shutil

from acq4.util.cell_storage import CellStorageManager


class TestCellStorageManagerInit:
    """Test CellStorageManager initialization and directory setup."""

    def test_init_creates_base_directory(self, tmp_path):
        """Test that initialization creates the base directory if it doesn't exist."""
        base_dir = tmp_path / "storage"
        manager = CellStorageManager(str(base_dir))

        assert os.path.exists(base_dir)
        assert os.path.isdir(base_dir)

    def test_init_creates_cells_subdirectory(self, tmp_path):
        """Test that initialization creates the cells/ subdirectory."""
        base_dir = tmp_path / "storage"
        manager = CellStorageManager(str(base_dir))

        cells_dir = base_dir / "cells"
        assert os.path.exists(cells_dir)
        assert os.path.isdir(cells_dir)

    def test_init_creates_patch_attempts_subdirectory(self, tmp_path):
        """Test that initialization creates the patch_attempts/ subdirectory."""
        base_dir = tmp_path / "storage"
        manager = CellStorageManager(str(base_dir))

        attempts_dir = base_dir / "patch_attempts"
        assert os.path.exists(attempts_dir)
        assert os.path.isdir(attempts_dir)

    def test_init_accepts_existing_directory(self, tmp_path):
        """Test that initialization works with an existing directory."""
        base_dir = tmp_path / "storage"
        os.makedirs(base_dir)

        manager = CellStorageManager(str(base_dir))
        assert os.path.exists(base_dir)

    def test_init_stores_absolute_path(self, tmp_path):
        """Test that the manager stores an absolute path."""
        base_dir = tmp_path / "storage"
        manager = CellStorageManager(str(base_dir))

        # The stored path should be absolute
        assert os.path.isabs(manager.base_dir)


class TestCellStorageManagerHelpers:
    """Test CellStorageManager helper methods."""

    def test_get_cells_dir_returns_correct_path(self, tmp_path):
        """Test that _get_cells_dir returns the correct path."""
        base_dir = tmp_path / "storage"
        manager = CellStorageManager(str(base_dir))

        cells_dir = manager._get_cells_dir()
        expected_path = os.path.join(str(base_dir), "cells")
        assert cells_dir == expected_path

    def test_get_attempts_dir_returns_correct_path(self, tmp_path):
        """Test that _get_attempts_dir returns the correct path."""
        base_dir = tmp_path / "storage"
        manager = CellStorageManager(str(base_dir))

        attempts_dir = manager._get_attempts_dir()
        expected_path = os.path.join(str(base_dir), "patch_attempts")
        assert attempts_dir == expected_path

    def test_get_cells_dir_is_absolute(self, tmp_path):
        """Test that _get_cells_dir returns an absolute path."""
        base_dir = tmp_path / "storage"
        manager = CellStorageManager(str(base_dir))

        cells_dir = manager._get_cells_dir()
        assert os.path.isabs(cells_dir)

    def test_get_attempts_dir_is_absolute(self, tmp_path):
        """Test that _get_attempts_dir returns an absolute path."""
        base_dir = tmp_path / "storage"
        manager = CellStorageManager(str(base_dir))

        attempts_dir = manager._get_attempts_dir()
        assert os.path.isabs(attempts_dir)


# Pytest fixture for creating a temporary storage manager
@pytest.fixture
def storage_manager(tmp_path):
    """Create a CellStorageManager with a temporary directory."""
    base_dir = tmp_path / "test_storage"
    manager = CellStorageManager(str(base_dir))
    return manager
