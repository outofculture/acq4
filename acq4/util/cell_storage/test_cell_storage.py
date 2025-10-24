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


class TestCellStorageOperations:
    """Test Cell CRUD operations in CellStorageManager."""

    def test_create_cell(self, tmp_path):
        """Test creating a new cell."""
        manager = CellStorageManager(str(tmp_path))

        cell = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2,
            notes="Test cell"
        )

        assert cell is not None
        assert cell.uuid is not None
        assert cell.global_position == {"x": 100.0, "y": 200.0, "z": 50.0}
        assert cell.initial_resistance == 5.2
        assert cell.notes == "Test cell"

        # Verify directory was created
        cell_dir = os.path.join(manager._get_cells_dir(), cell.uuid)
        assert os.path.exists(cell_dir)

        # Verify metadata.json was created
        metadata_file = os.path.join(cell_dir, "metadata.json")
        assert os.path.exists(metadata_file)

    def test_create_cell_saves_metadata(self, tmp_path):
        """Test that create_cell saves metadata correctly."""
        manager = CellStorageManager(str(tmp_path))

        cell = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )

        # Load the metadata directly and verify
        cell_dir = os.path.join(manager._get_cells_dir(), cell.uuid)
        loaded_cell = load_metadata(cell_dir, Cell)

        assert loaded_cell.uuid == cell.uuid
        assert loaded_cell.global_position == cell.global_position
        assert loaded_cell.initial_resistance == cell.initial_resistance

    def test_get_cell(self, tmp_path):
        """Test retrieving a cell by UUID."""
        manager = CellStorageManager(str(tmp_path))

        # Create a cell
        created_cell = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2,
            notes="Test cell"
        )

        # Retrieve it
        retrieved_cell = manager.get_cell(created_cell.uuid)

        assert retrieved_cell.uuid == created_cell.uuid
        assert retrieved_cell.global_position == created_cell.global_position
        assert retrieved_cell.initial_resistance == created_cell.initial_resistance
        assert retrieved_cell.notes == created_cell.notes

    def test_get_cell_nonexistent(self, tmp_path):
        """Test that get_cell raises ValueError for nonexistent cell."""
        manager = CellStorageManager(str(tmp_path))

        with pytest.raises(ValueError):
            manager.get_cell("nonexistent-uuid")

    def test_list_cells_empty(self, tmp_path):
        """Test listing cells when none exist."""
        manager = CellStorageManager(str(tmp_path))

        cells = manager.list_cells()

        assert cells == []

    def test_list_cells_single(self, tmp_path):
        """Test listing cells with one cell."""
        manager = CellStorageManager(str(tmp_path))

        created_cell = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )

        cells = manager.list_cells()

        assert len(cells) == 1
        assert cells[0].uuid == created_cell.uuid

    def test_list_cells_multiple(self, tmp_path):
        """Test listing multiple cells."""
        manager = CellStorageManager(str(tmp_path))

        cell1 = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )
        cell2 = manager.create_cell(
            global_position={"x": 150.0, "y": 250.0, "z": 60.0},
            initial_resistance=6.3
        )
        cell3 = manager.create_cell(
            global_position={"x": 200.0, "y": 300.0, "z": 70.0},
            initial_resistance=7.4
        )

        cells = manager.list_cells()

        assert len(cells) == 3
        uuids = {cell.uuid for cell in cells}
        assert cell1.uuid in uuids
        assert cell2.uuid in uuids
        assert cell3.uuid in uuids

    def test_update_cell(self, tmp_path):
        """Test updating a cell's metadata."""
        manager = CellStorageManager(str(tmp_path))

        # Create a cell
        cell = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2,
            notes="Original notes"
        )

        # Modify it
        cell.notes = "Updated notes"
        cell.initial_resistance = 6.0

        # Update it
        manager.update_cell(cell)

        # Retrieve it and verify changes
        updated_cell = manager.get_cell(cell.uuid)
        assert updated_cell.notes == "Updated notes"
        assert updated_cell.initial_resistance == 6.0

    def test_delete_cell(self, tmp_path):
        """Test deleting a cell."""
        manager = CellStorageManager(str(tmp_path))

        # Create a cell
        cell = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )

        cell_dir = os.path.join(manager._get_cells_dir(), cell.uuid)
        assert os.path.exists(cell_dir)

        # Delete it
        manager.delete_cell(cell.uuid)

        # Verify directory is gone
        assert not os.path.exists(cell_dir)

        # Verify it's not in the list
        cells = manager.list_cells()
        assert len(cells) == 0

    def test_delete_cell_nonexistent(self, tmp_path):
        """Test that delete_cell raises ValueError for nonexistent cell."""
        manager = CellStorageManager(str(tmp_path))

        with pytest.raises(ValueError):
            manager.delete_cell("nonexistent-uuid")


class TestPatchAttemptStorageOperations:
    """Test Patch Attempt CRUD operations in CellStorageManager."""

    def test_create_patch_attempt(self, tmp_path):
        """Test creating a new patch attempt."""
        manager = CellStorageManager(str(tmp_path))

        # First create a cell
        cell = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )

        # Create a patch attempt for that cell
        attempt = manager.create_patch_attempt(
            cell_id=cell.uuid,
            successful_seal=True,
            tasks_run=["recording1"],
            notes="Good attempt"
        )

        assert attempt is not None
        assert attempt.uuid is not None
        assert attempt.cell_id == cell.uuid
        assert attempt.successful_seal is True
        assert attempt.tasks_run == ["recording1"]
        assert attempt.notes == "Good attempt"

        # Verify directory was created
        attempt_dir = os.path.join(manager._get_attempts_dir(), attempt.uuid)
        assert os.path.exists(attempt_dir)

        # Verify metadata.json was created
        metadata_file = os.path.join(attempt_dir, "metadata.json")
        assert os.path.exists(metadata_file)

    def test_create_patch_attempt_validates_cell_id(self, tmp_path):
        """Test that create_patch_attempt validates cell_id exists."""
        manager = CellStorageManager(str(tmp_path))

        # Try to create attempt with nonexistent cell_id
        with pytest.raises(ValueError):
            manager.create_patch_attempt(
                cell_id="nonexistent-cell-uuid",
                successful_seal=True
            )

    def test_create_patch_attempt_saves_metadata(self, tmp_path):
        """Test that create_patch_attempt saves metadata correctly."""
        manager = CellStorageManager(str(tmp_path))

        # Create a cell first
        cell = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )

        # Create attempt
        attempt = manager.create_patch_attempt(
            cell_id=cell.uuid,
            successful_seal=True
        )

        # Load the metadata directly and verify
        attempt_dir = os.path.join(manager._get_attempts_dir(), attempt.uuid)
        loaded_attempt = load_metadata(attempt_dir, PatchAttempt)

        assert loaded_attempt.uuid == attempt.uuid
        assert loaded_attempt.cell_id == attempt.cell_id
        assert loaded_attempt.successful_seal == attempt.successful_seal

    def test_get_patch_attempt(self, tmp_path):
        """Test retrieving a patch attempt by UUID."""
        manager = CellStorageManager(str(tmp_path))

        # Create cell and attempt
        cell = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )
        created_attempt = manager.create_patch_attempt(
            cell_id=cell.uuid,
            successful_seal=True,
            notes="Test attempt"
        )

        # Retrieve it
        retrieved_attempt = manager.get_patch_attempt(created_attempt.uuid)

        assert retrieved_attempt.uuid == created_attempt.uuid
        assert retrieved_attempt.cell_id == created_attempt.cell_id
        assert retrieved_attempt.successful_seal == created_attempt.successful_seal
        assert retrieved_attempt.notes == created_attempt.notes

    def test_get_patch_attempt_nonexistent(self, tmp_path):
        """Test that get_patch_attempt raises ValueError for nonexistent attempt."""
        manager = CellStorageManager(str(tmp_path))

        with pytest.raises(ValueError):
            manager.get_patch_attempt("nonexistent-uuid")

    def test_list_patch_attempts_empty(self, tmp_path):
        """Test listing patch attempts when none exist."""
        manager = CellStorageManager(str(tmp_path))

        attempts = manager.list_patch_attempts()

        assert attempts == []

    def test_list_patch_attempts_single(self, tmp_path):
        """Test listing patch attempts with one attempt."""
        manager = CellStorageManager(str(tmp_path))

        # Create cell and attempt
        cell = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )
        created_attempt = manager.create_patch_attempt(cell_id=cell.uuid)

        attempts = manager.list_patch_attempts()

        assert len(attempts) == 1
        assert attempts[0].uuid == created_attempt.uuid

    def test_list_patch_attempts_multiple(self, tmp_path):
        """Test listing multiple patch attempts."""
        manager = CellStorageManager(str(tmp_path))

        # Create cells
        cell1 = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )
        cell2 = manager.create_cell(
            global_position={"x": 150.0, "y": 250.0, "z": 60.0},
            initial_resistance=6.3
        )

        # Create attempts
        attempt1 = manager.create_patch_attempt(cell_id=cell1.uuid)
        attempt2 = manager.create_patch_attempt(cell_id=cell1.uuid)
        attempt3 = manager.create_patch_attempt(cell_id=cell2.uuid)

        attempts = manager.list_patch_attempts()

        assert len(attempts) == 3
        uuids = {attempt.uuid for attempt in attempts}
        assert attempt1.uuid in uuids
        assert attempt2.uuid in uuids
        assert attempt3.uuid in uuids

    def test_list_patch_attempts_filtered_by_cell(self, tmp_path):
        """Test listing patch attempts filtered by cell_id."""
        manager = CellStorageManager(str(tmp_path))

        # Create cells
        cell1 = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )
        cell2 = manager.create_cell(
            global_position={"x": 150.0, "y": 250.0, "z": 60.0},
            initial_resistance=6.3
        )

        # Create attempts for different cells
        attempt1_1 = manager.create_patch_attempt(cell_id=cell1.uuid)
        attempt1_2 = manager.create_patch_attempt(cell_id=cell1.uuid)
        attempt2_1 = manager.create_patch_attempt(cell_id=cell2.uuid)

        # Filter by cell1
        cell1_attempts = manager.list_patch_attempts(cell_id=cell1.uuid)

        assert len(cell1_attempts) == 2
        assert all(a.cell_id == cell1.uuid for a in cell1_attempts)
        uuids = {a.uuid for a in cell1_attempts}
        assert attempt1_1.uuid in uuids
        assert attempt1_2.uuid in uuids
        assert attempt2_1.uuid not in uuids

    def test_get_cell_patch_attempts(self, tmp_path):
        """Test convenience method for getting cell's attempts."""
        manager = CellStorageManager(str(tmp_path))

        # Create cell and attempts
        cell = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )
        attempt1 = manager.create_patch_attempt(cell_id=cell.uuid)
        attempt2 = manager.create_patch_attempt(cell_id=cell.uuid)

        # Get cell's attempts
        cell_attempts = manager.get_cell_patch_attempts(cell.uuid)

        assert len(cell_attempts) == 2
        assert all(a.cell_id == cell.uuid for a in cell_attempts)

    def test_update_patch_attempt(self, tmp_path):
        """Test updating a patch attempt's metadata."""
        manager = CellStorageManager(str(tmp_path))

        # Create cell and attempt
        cell = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )
        attempt = manager.create_patch_attempt(
            cell_id=cell.uuid,
            successful_seal=False,
            notes="Original notes"
        )

        # Modify it
        attempt.successful_seal = True
        attempt.notes = "Updated notes"
        attempt.tasks_run = ["new_task"]

        # Update it
        manager.update_patch_attempt(attempt)

        # Retrieve it and verify changes
        updated_attempt = manager.get_patch_attempt(attempt.uuid)
        assert updated_attempt.successful_seal is True
        assert updated_attempt.notes == "Updated notes"
        assert updated_attempt.tasks_run == ["new_task"]

    def test_delete_patch_attempt(self, tmp_path):
        """Test deleting a patch attempt."""
        manager = CellStorageManager(str(tmp_path))

        # Create cell and attempt
        cell = manager.create_cell(
            global_position={"x": 100.0, "y": 200.0, "z": 50.0},
            initial_resistance=5.2
        )
        attempt = manager.create_patch_attempt(cell_id=cell.uuid)

        attempt_dir = os.path.join(manager._get_attempts_dir(), attempt.uuid)
        assert os.path.exists(attempt_dir)

        # Delete it
        manager.delete_patch_attempt(attempt.uuid)

        # Verify directory is gone
        assert not os.path.exists(attempt_dir)

        # Verify it's not in the list
        attempts = manager.list_patch_attempts()
        assert len(attempts) == 0

    def test_delete_patch_attempt_nonexistent(self, tmp_path):
        """Test that delete_patch_attempt raises ValueError for nonexistent attempt."""
        manager = CellStorageManager(str(tmp_path))

        with pytest.raises(ValueError):
            manager.delete_patch_attempt("nonexistent-uuid")


# Pytest fixture for creating a temporary storage manager
@pytest.fixture
def storage_manager(tmp_path):
    """Create a CellStorageManager with a temporary directory."""
    base_dir = tmp_path / "test_storage"
    manager = CellStorageManager(str(base_dir))
    return manager
