"""
Tests for the cell storage system.
"""
import os
import pytest
import tempfile
import shutil

from acq4.util.cell_storage import CellStorageManager
from acq4.util.cell_storage.models import Cell, PatchAttempt
from acq4.util.cell_storage.serialization import (
    save_metadata, load_metadata, ensure_dir_exists
)


class TestCellModel:
    """Test Cell data model."""

    def test_cell_creation_with_all_parameters(self):
        """Test creating a Cell with all parameters specified."""
        cell = Cell(
            uuid="test-uuid-123",
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2,
            cellfie_filename="cellfie.ma",
            notes="Test cell"
        )

        assert cell.uuid == "test-uuid-123"
        assert cell.global_position == {"x": 100.0, "y": 200.0, "z": 50.0}
        assert cell.initial_resistance == 5.2
        assert cell.cellfie_filename == "cellfie.ma"
        assert cell.notes == "Test cell"

    def test_cell_uuid_auto_generation(self):
        """Test that UUID is auto-generated if not provided."""
        cell = Cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )

        assert cell.uuid is not None
        assert isinstance(cell.uuid, str)
        assert len(cell.uuid) > 0

    def test_cell_notes_default_empty(self):
        """Test that notes defaults to empty string."""
        cell = Cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )

        assert cell.notes == ""

    def test_cell_cellfie_filename_optional(self):
        """Test that cellfie_filename is optional."""
        cell = Cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )

        assert cell.cellfie_filename is None

    def test_cell_to_dict(self):
        """Test converting Cell to dictionary."""
        cell = Cell(
            uuid="test-uuid-123",
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2,
            cellfie_filename="cellfie.ma",
            notes="Test cell"
        )

        data = cell.to_dict()

        assert data["uuid"] == "test-uuid-123"
        assert data["global_position"] == {"x": 100.0, "y": 200.0, "z": 50.0}
        assert data["initial_resistance"] == 5.2
        assert data["cellfie_filename"] == "cellfie.ma"
        assert data["notes"] == "Test cell"

    def test_cell_from_dict(self):
        """Test creating Cell from dictionary."""
        data = {
            "uuid": "test-uuid-123",
            "global_position": {"x": 100.0, "y": 200.0, "z": 50.0},
            "initial_resistance": 5.2,
            "cellfie_filename": "cellfie.ma",
            "notes": "Test cell"
        }

        cell = Cell.from_dict(data)

        assert cell.uuid == "test-uuid-123"
        assert cell.global_position == {"x": 100.0, "y": 200.0, "z": 50.0}
        assert cell.initial_resistance == 5.2
        assert cell.cellfie_filename == "cellfie.ma"
        assert cell.notes == "Test cell"

    def test_cell_round_trip_serialization(self):
        """Test that to_dict and from_dict are inverses."""
        original = Cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2,
            notes="Test cell"
        )

        data = original.to_dict()
        restored = Cell.from_dict(data)

        assert restored.uuid == original.uuid
        assert restored.global_position == original.global_position
        assert restored.initial_resistance == original.initial_resistance
        assert restored.notes == original.notes

    def test_cell_validation_position_must_have_xyz(self):
        """Test that global_position must have x, y, z keys."""
        with pytest.raises((ValueError, KeyError)):
            Cell(
                global_position={"x": 100.0, "y": 200.0},  # Missing z
                initial_resistance=5.2
            )

    def test_cell_repr(self):
        """Test that Cell has a useful __repr__."""
        cell = Cell(
            uuid="test-uuid-123",
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )

        repr_str = repr(cell)
        assert "Cell" in repr_str
        assert "test-uuid-123" in repr_str


class TestPatchAttemptModel:
    """Test PatchAttempt data model."""

    def test_patch_attempt_creation_with_all_parameters(self):
        """Test creating a PatchAttempt with all parameters."""
        attempt = PatchAttempt(
            uuid="attempt-uuid-123",
            cell_id="cell-uuid-456",
            successful_seal=True,
            successful_reseal=False,
            tasks_run=["recording1", "current_injection"],
            event_log_filename="event_log.json",
            notes="Good seal"
        )

        assert attempt.uuid == "attempt-uuid-123"
        assert attempt.cell_id == "cell-uuid-456"
        assert attempt.successful_seal is True
        assert attempt.successful_reseal is False
        assert attempt.tasks_run == ["recording1", "current_injection"]
        assert attempt.event_log_filename == "event_log.json"
        assert attempt.notes == "Good seal"

    def test_patch_attempt_uuid_auto_generation(self):
        """Test that UUID is auto-generated if not provided."""
        attempt = PatchAttempt(cell_id="cell-uuid-456")

        assert attempt.uuid is not None
        assert isinstance(attempt.uuid, str)
        assert len(attempt.uuid) > 0

    def test_patch_attempt_defaults(self):
        """Test default values for PatchAttempt."""
        attempt = PatchAttempt(cell_id="cell-uuid-456")

        assert attempt.successful_seal is False
        assert attempt.successful_reseal is False
        assert attempt.tasks_run == []
        assert attempt.notes == ""
        assert attempt.event_log_filename is None

    def test_patch_attempt_to_dict(self):
        """Test converting PatchAttempt to dictionary."""
        attempt = PatchAttempt(
            uuid="attempt-uuid-123",
            cell_id="cell-uuid-456",
            successful_seal=True,
            successful_reseal=False,
            tasks_run=["recording1"],
            event_log_filename="event_log.json",
            notes="Test"
        )

        data = attempt.to_dict()

        assert data["uuid"] == "attempt-uuid-123"
        assert data["cell_id"] == "cell-uuid-456"
        assert data["successful_seal"] is True
        assert data["successful_reseal"] is False
        assert data["tasks_run"] == ["recording1"]
        assert data["event_log_filename"] == "event_log.json"
        assert data["notes"] == "Test"

    def test_patch_attempt_from_dict(self):
        """Test creating PatchAttempt from dictionary."""
        data = {
            "uuid": "attempt-uuid-123",
            "cell_id": "cell-uuid-456",
            "successful_seal": True,
            "successful_reseal": False,
            "tasks_run": ["recording1"],
            "event_log_filename": "event_log.json",
            "notes": "Test"
        }

        attempt = PatchAttempt.from_dict(data)

        assert attempt.uuid == "attempt-uuid-123"
        assert attempt.cell_id == "cell-uuid-456"
        assert attempt.successful_seal is True
        assert attempt.tasks_run == ["recording1"]

    def test_patch_attempt_round_trip_serialization(self):
        """Test that to_dict and from_dict are inverses."""
        original = PatchAttempt(
            cell_id="cell-uuid-456",
            successful_seal=True,
            tasks_run=["recording1"]
        )

        data = original.to_dict()
        restored = PatchAttempt.from_dict(data)

        assert restored.uuid == original.uuid
        assert restored.cell_id == original.cell_id
        assert restored.successful_seal == original.successful_seal
        assert restored.tasks_run == original.tasks_run

    def test_patch_attempt_repr(self):
        """Test that PatchAttempt has a useful __repr__."""
        attempt = PatchAttempt(
            uuid="attempt-uuid-123",
            cell_id="cell-uuid-456"
        )

        repr_str = repr(attempt)
        assert "PatchAttempt" in repr_str
        assert "attempt-uuid-123" in repr_str


class TestSerialization:
    """Test JSON serialization utilities."""

    def test_ensure_dir_exists_creates_directory(self, tmp_path):
        """Test that ensure_dir_exists creates a directory."""
        new_dir = tmp_path / "test_dir"
        assert not os.path.exists(new_dir)

        ensure_dir_exists(str(new_dir))

        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)

    def test_ensure_dir_exists_accepts_existing_directory(self, tmp_path):
        """Test that ensure_dir_exists works with existing directory."""
        new_dir = tmp_path / "test_dir"
        os.makedirs(new_dir)

        # Should not raise an error
        ensure_dir_exists(str(new_dir))

        assert os.path.exists(new_dir)

    def test_save_metadata_cell(self, tmp_path):
        """Test saving Cell metadata to JSON."""
        cell = Cell(
            uuid="test-cell-123",
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2,
            notes="Test cell"
        )

        cell_dir = tmp_path / "cell_123"
        save_metadata(cell, str(cell_dir))

        # Check that metadata.json was created
        metadata_file = cell_dir / "metadata.json"
        assert os.path.exists(metadata_file)

        # Verify content
        import json
        with open(metadata_file, 'r') as f:
            data = json.load(f)

        assert data["uuid"] == "test-cell-123"
        assert data["global_position"] == {"x": 100.0, "y": 200.0, "z": 50.0}
        assert data["initial_resistance"] == 5.2

    def test_save_metadata_patch_attempt(self, tmp_path):
        """Test saving PatchAttempt metadata to JSON."""
        attempt = PatchAttempt(
            uuid="attempt-123",
            cell_id="cell-456",
            successful_seal=True,
            tasks_run=["recording1"]
        )

        attempt_dir = tmp_path / "attempt_123"
        save_metadata(attempt, str(attempt_dir))

        # Check that metadata.json was created
        metadata_file = attempt_dir / "metadata.json"
        assert os.path.exists(metadata_file)

        # Verify content
        import json
        with open(metadata_file, 'r') as f:
            data = json.load(f)

        assert data["uuid"] == "attempt-123"
        assert data["cell_id"] == "cell-456"
        assert data["successful_seal"] is True
        assert data["tasks_run"] == ["recording1"]

    def test_load_metadata_cell(self, tmp_path):
        """Test loading Cell metadata from JSON."""
        # First save a cell
        cell = Cell(
            uuid="test-cell-123",
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2,
            notes="Test cell"
        )

        cell_dir = tmp_path / "cell_123"
        save_metadata(cell, str(cell_dir))

        # Now load it back
        loaded_cell = load_metadata(str(cell_dir), Cell)

        assert loaded_cell.uuid == cell.uuid
        assert loaded_cell.global_position == cell.global_position
        assert loaded_cell.initial_resistance == cell.initial_resistance
        assert loaded_cell.notes == cell.notes

    def test_load_metadata_patch_attempt(self, tmp_path):
        """Test loading PatchAttempt metadata from JSON."""
        # First save an attempt
        attempt = PatchAttempt(
            uuid="attempt-123",
            cell_id="cell-456",
            successful_seal=True,
            tasks_run=["recording1"]
        )

        attempt_dir = tmp_path / "attempt_123"
        save_metadata(attempt, str(attempt_dir))

        # Now load it back
        loaded_attempt = load_metadata(str(attempt_dir), PatchAttempt)

        assert loaded_attempt.uuid == attempt.uuid
        assert loaded_attempt.cell_id == attempt.cell_id
        assert loaded_attempt.successful_seal == attempt.successful_seal
        assert loaded_attempt.tasks_run == attempt.tasks_run

    def test_load_metadata_file_not_found(self, tmp_path):
        """Test that load_metadata raises error when file doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError):
            load_metadata(str(nonexistent_dir), Cell)

    def test_load_metadata_invalid_json(self, tmp_path):
        """Test that load_metadata handles invalid JSON."""
        invalid_dir = tmp_path / "invalid"
        os.makedirs(invalid_dir)

        # Write invalid JSON
        metadata_file = invalid_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            f.write("{invalid json")

        with pytest.raises(Exception):  # JSONDecodeError or similar
            load_metadata(str(invalid_dir), Cell)

    def test_save_metadata_creates_directory(self, tmp_path):
        """Test that save_metadata creates directory if it doesn't exist."""
        cell = Cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )

        new_dir = tmp_path / "new_cell_dir"
        assert not os.path.exists(new_dir)

        save_metadata(cell, str(new_dir))

        assert os.path.exists(new_dir)
        assert os.path.exists(new_dir / "metadata.json")


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
