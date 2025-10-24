"""
Example usage of the Cell Storage System.

This script demonstrates how to use the CellStorageManager to store and retrieve
Cell and PatchAttempt objects with associated data (cellfie images and event logs).
"""
import numpy as np
import tempfile
import os

from acq4.util.cell_storage import CellStorageManager


def main():
    """Run the cell storage example."""

    # Create a temporary directory for this example
    # In real usage, you'd use a persistent directory
    temp_dir = tempfile.mkdtemp()
    print(f"Creating storage in: {temp_dir}\n")

    # =========================================================================
    # 1. Initialize the Cell Storage Manager
    # =========================================================================
    print("=" * 70)
    print("1. INITIALIZING CELL STORAGE MANAGER")
    print("=" * 70)

    manager = CellStorageManager(temp_dir)
    print(f"✓ Initialized storage at: {manager.base_dir}")
    print(f"  - Cells directory: {manager._get_cells_dir()}")
    print(f"  - Patch attempts directory: {manager._get_attempts_dir()}\n")

    # =========================================================================
    # 2. Create Cells with Different Options
    # =========================================================================
    print("=" * 70)
    print("2. CREATING CELLS")
    print("=" * 70)

    # Create a simple cell without cellfie
    cell1 = manager.create_cell(
        global_position={"x": 100.0, "y": 200.0, "z": 50.0},
        initial_resistance=5.2,
        notes="Pyramidal neuron in layer 2/3"
    )
    print(f"✓ Created cell 1: {cell1.uuid}")
    print(f"  Position: {cell1.global_position}")
    print(f"  Resistance: {cell1.initial_resistance} MΩ")
    print(f"  Notes: {cell1.notes}\n")

    # Create a cell with a cellfie image
    cellfie_data = np.random.rand(20, 20, 10)  # Simulated 3D image
    cell2 = manager.create_cell(
        global_position={"x": 150.0, "y": 250.0, "z": 60.0},
        initial_resistance=6.8,
        cellfie_data=cellfie_data,
        notes="Interneuron with cellfie image"
    )
    print(f"✓ Created cell 2 with cellfie: {cell2.uuid}")
    print(f"  Cellfie shape: {cellfie_data.shape}")
    print(f"  Cellfie filename: {cell2.cellfie_filename}\n")

    # Create another cell for multiple patch attempts
    cell3 = manager.create_cell(
        global_position={"x": 200.0, "y": 300.0, "z": 70.0},
        initial_resistance=4.5,
        notes="Cell with multiple patch attempts"
    )
    print(f"✓ Created cell 3: {cell3.uuid}\n")

    # =========================================================================
    # 3. List All Cells
    # =========================================================================
    print("=" * 70)
    print("3. LISTING ALL CELLS")
    print("=" * 70)

    all_cells = manager.list_cells()
    print(f"Found {len(all_cells)} cells:")
    for cell in all_cells:
        print(f"  - {cell.uuid}: {cell.notes}")
    print()

    # =========================================================================
    # 4. Retrieve and Update a Cell
    # =========================================================================
    print("=" * 70)
    print("4. RETRIEVING AND UPDATING CELLS")
    print("=" * 70)

    # Get cell 1
    retrieved_cell = manager.get_cell(cell1.uuid)
    print(f"✓ Retrieved cell: {retrieved_cell.uuid}")
    print(f"  Original notes: {retrieved_cell.notes}")

    # Update the cell's notes
    retrieved_cell.notes = "Updated: Confirmed pyramidal morphology"
    manager.update_cell(retrieved_cell)
    print(f"  Updated notes: {retrieved_cell.notes}\n")

    # Verify the update
    updated_cell = manager.get_cell(cell1.uuid)
    print(f"✓ Verified update: {updated_cell.notes}\n")

    # =========================================================================
    # 5. Create Patch Attempts
    # =========================================================================
    print("=" * 70)
    print("5. CREATING PATCH ATTEMPTS")
    print("=" * 70)

    # Create a successful patch attempt with event log
    event_log_1 = [
        {"time": "10:00:00", "device": "pipette", "event": "approach_start"},
        {"time": "10:00:15", "device": "pipette", "event": "contact"},
        {"time": "10:00:20", "device": "pipette", "event": "seal_formed", "resistance": 1.2},
        {"time": "10:00:25", "device": "pipette", "event": "break_in"}
    ]

    attempt1 = manager.create_patch_attempt(
        cell_id=cell1.uuid,
        successful_seal=True,
        tasks_run=["current_injection", "voltage_clamp"],
        event_log=event_log_1,
        notes="Successful whole-cell recording"
    )
    print(f"✓ Created patch attempt 1: {attempt1.uuid}")
    print(f"  Cell: {attempt1.cell_id}")
    print(f"  Successful seal: {attempt1.successful_seal}")
    print(f"  Tasks run: {attempt1.tasks_run}")
    print(f"  Event log entries: {len(event_log_1)}\n")

    # Create a failed attempt
    attempt2 = manager.create_patch_attempt(
        cell_id=cell2.uuid,
        successful_seal=False,
        notes="Seal formation failed"
    )
    print(f"✓ Created patch attempt 2: {attempt2.uuid}")
    print(f"  Successful seal: {attempt2.successful_seal}\n")

    # Create multiple attempts for the same cell
    for i in range(3):
        attempt = manager.create_patch_attempt(
            cell_id=cell3.uuid,
            successful_seal=(i == 1),  # Only second attempt successful
            notes=f"Attempt {i+1}"
        )
        print(f"✓ Created attempt {i+1} for cell 3: {attempt.uuid}")
    print()

    # =========================================================================
    # 6. List and Filter Patch Attempts
    # =========================================================================
    print("=" * 70)
    print("6. LISTING AND FILTERING PATCH ATTEMPTS")
    print("=" * 70)

    # List all attempts
    all_attempts = manager.list_patch_attempts()
    print(f"Total patch attempts: {len(all_attempts)}")

    # List attempts for a specific cell
    cell3_attempts = manager.get_cell_patch_attempts(cell3.uuid)
    print(f"Attempts for cell 3: {len(cell3_attempts)}")
    for attempt in cell3_attempts:
        print(f"  - {attempt.uuid}: Seal={attempt.successful_seal}, {attempt.notes}")
    print()

    # =========================================================================
    # 7. Retrieve Event Logs
    # =========================================================================
    print("=" * 70)
    print("7. RETRIEVING EVENT LOGS")
    print("=" * 70)

    # Get event log for attempt 1
    event_log = manager.get_event_log(attempt1.uuid)
    print(f"Event log for attempt 1 ({len(event_log)} events):")
    for event in event_log:
        print(f"  {event['time']}: {event['event']}")
    print()

    # =========================================================================
    # 8. Update Event Log
    # =========================================================================
    print("=" * 70)
    print("8. UPDATING EVENT LOGS")
    print("=" * 70)

    # Add event log to attempt 2 (which didn't have one)
    new_event_log = [
        {"time": "11:00:00", "device": "pipette", "event": "approach_start"},
        {"time": "11:00:10", "device": "pipette", "event": "contact"},
        {"time": "11:00:15", "device": "pipette", "event": "seal_failed"}
    ]
    manager.update_event_log(attempt2.uuid, new_event_log)
    print(f"✓ Added event log to attempt 2")

    # Verify it was saved
    retrieved_log = manager.get_event_log(attempt2.uuid)
    print(f"  Events added: {len(retrieved_log)}\n")

    # =========================================================================
    # 9. Retrieve and Update Cellfie Images
    # =========================================================================
    print("=" * 70)
    print("9. WORKING WITH CELLFIE IMAGES")
    print("=" * 70)

    # Get cellfie for cell 2
    cellfie = manager.get_cellfie(cell2.uuid)
    print(f"✓ Retrieved cellfie for cell 2")
    print(f"  Shape: {cellfie.shape}")
    print(f"  Data type: {cellfie.dtype}")
    print(f"  Mean intensity: {cellfie.mean():.4f}\n")

    # Add cellfie to cell 1 (which didn't have one)
    new_cellfie = np.random.rand(15, 15, 8)
    manager.update_cellfie(cell1.uuid, new_cellfie)
    print(f"✓ Added cellfie to cell 1")
    print(f"  Shape: {new_cellfie.shape}\n")

    # =========================================================================
    # 10. Delete Operations
    # =========================================================================
    print("=" * 70)
    print("10. DELETE OPERATIONS")
    print("=" * 70)

    # Delete a patch attempt
    manager.delete_patch_attempt(attempt2.uuid)
    print(f"✓ Deleted patch attempt: {attempt2.uuid}")

    # Verify deletion
    remaining_attempts = manager.list_patch_attempts()
    print(f"  Remaining attempts: {len(remaining_attempts)}\n")

    # Note: Deleting a cell doesn't cascade delete its attempts
    # You should delete attempts first if needed

    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    final_cells = manager.list_cells()
    final_attempts = manager.list_patch_attempts()

    print(f"Final storage statistics:")
    print(f"  Total cells: {len(final_cells)}")
    print(f"  Total patch attempts: {len(final_attempts)}")
    print(f"  Cells with cellfies: {sum(1 for c in final_cells if c.cellfie_filename)}")

    # Show storage directory structure
    print(f"\nStorage directory: {manager.base_dir}")
    print(f"  Size on disk: ~{get_directory_size(manager.base_dir) / 1024:.1f} KB")

    print("\n" + "=" * 70)
    print("EXAMPLE COMPLETE!")
    print("=" * 70)
    print(f"\nYou can inspect the storage directory at:")
    print(f"  {manager.base_dir}")
    print("\nDirectory structure:")
    print_directory_tree(manager.base_dir)


def get_directory_size(path):
    """Get total size of directory in bytes."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total += os.path.getsize(filepath)
    return total


def print_directory_tree(path, prefix="", max_depth=3, current_depth=0):
    """Print directory tree structure."""
    if current_depth >= max_depth:
        return

    items = sorted(os.listdir(path))
    for i, item in enumerate(items):
        item_path = os.path.join(path, item)
        is_last = i == len(items) - 1

        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{item}")

        if os.path.isdir(item_path):
            extension = "    " if is_last else "│   "
            print_directory_tree(item_path, prefix + extension, max_depth, current_depth + 1)


if __name__ == "__main__":
    main()
