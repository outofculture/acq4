# Cell Storage System

A simple, file-based storage system for managing Cell and Patch Attempt objects in ACQ4.

## Overview

The Cell Storage System provides a lightweight, database-like interface for storing and retrieving cell data and patch attempt records. It uses a simple directory structure with JSON metadata files and binary data files, making it easy to inspect and migrate data.

## Features

- **Cell Management**: Store cells with position, resistance, notes, and optional cellfie images
- **Patch Attempt Tracking**: Record patch attempts with seal success, tasks run, and event logs
- **Foreign Key Validation**: Patch attempts must reference valid cells
- **Auto-generated UUIDs**: All entities get unique identifiers automatically
- **Human-readable Storage**: JSON metadata files with pretty-printing
- **Binary Data Support**: Efficient storage for images (NumPy .npy) and event logs (JSON)
- **Complete CRUD Operations**: Create, Read, Update, Delete for both entities
- **Query and Filter**: List all items or filter by relationships

## Directory Structure

```
<base_dir>/
├── cells/
│   ├── <cell-uuid-1>/
│   │   ├── metadata.json      # Cell metadata (position, resistance, notes)
│   │   └── cellfie.npy        # Optional: 3D image data
│   └── <cell-uuid-2>/
│       └── metadata.json
└── patch_attempts/
    ├── <attempt-uuid-1>/
    │   ├── metadata.json      # Attempt metadata (cell_id, seal success, tasks)
    │   └── event_log.json     # Optional: Device event timeline
    └── <attempt-uuid-2>/
        └── metadata.json
```

## Quick Start

```python
from acq4.util.cell_storage import CellStorageManager
import numpy as np

# Initialize the storage manager
manager = CellStorageManager("/path/to/storage")

# Create a cell
cell = manager.create_cell(
    global_position={"x": 100.0, "y": 200.0, "z": 50.0},
    initial_resistance=5.2,
    notes="Pyramidal neuron in layer 2/3"
)

# Add a cellfie image
cellfie_data = np.random.rand(20, 20, 10)  # 3D image
manager.update_cellfie(cell.uuid, cellfie_data)

# Create a patch attempt
attempt = manager.create_patch_attempt(
    cell_id=cell.uuid,
    successful_seal=True,
    tasks_run=["current_injection", "voltage_clamp"],
    notes="Successful whole-cell recording"
)

# Add event log
event_log = [
    {"time": "10:00:00", "device": "pipette", "event": "approach_start"},
    {"time": "10:00:15", "device": "pipette", "event": "seal_formed"}
]
manager.update_event_log(attempt.uuid, event_log)

# Query data
all_cells = manager.list_cells()
cell_attempts = manager.get_cell_patch_attempts(cell.uuid)
```

## Data Models

### Cell

Represents a biological cell with its properties and imaging data.

**Fields:**
- `uuid` (str): Unique identifier (auto-generated)
- `global_position` (dict): Position with x, y, z coordinates (floats)
- `initial_resistance` (float): Initial resistance in MΩ
- `cellfie_filename` (str, optional): Filename of cellfie image if present
- `notes` (str): Free-form notes

**Methods:**
- `to_dict()`: Convert to dictionary for serialization
- `from_dict(data)`: Create from dictionary (classmethod)

### PatchAttempt

Represents an attempt to patch a cell with outcome and timeline.

**Fields:**
- `uuid` (str): Unique identifier (auto-generated)
- `cell_id` (str): UUID of the associated cell (required, validated)
- `successful_seal` (bool): Whether seal formation succeeded
- `successful_reseal` (bool): Whether reseal succeeded (if attempted)
- `tasks_run` (list of str): Names of experimental tasks executed
- `event_log_filename` (str, optional): Filename of event log if present
- `notes` (str): Free-form notes

**Methods:**
- `to_dict()`: Convert to dictionary for serialization
- `from_dict(data)`: Create from dictionary (classmethod)

## API Reference

### CellStorageManager

Main interface for all storage operations.

#### Initialization

```python
manager = CellStorageManager(base_dir)
```

**Parameters:**
- `base_dir` (str): Path to storage directory (created if doesn't exist)

#### Cell Operations

##### create_cell()
```python
cell = manager.create_cell(
    global_position={"x": float, "y": float, "z": float},
    initial_resistance=float,
    cellfie_data=np.ndarray,  # optional
    notes=str  # optional
)
```

Creates a new cell and saves it to storage.

**Returns:** `Cell` instance with auto-generated UUID

##### get_cell()
```python
cell = manager.get_cell(uuid)
```

Retrieve a cell by UUID.

**Raises:** `ValueError` if cell doesn't exist

##### list_cells()
```python
cells = manager.list_cells()
```

Get all cells in storage.

**Returns:** List of `Cell` instances

##### update_cell()
```python
manager.update_cell(cell)
```

Update an existing cell's metadata.

**Raises:** `ValueError` if cell doesn't exist

##### delete_cell()
```python
manager.delete_cell(uuid)
```

Delete a cell and all its files.

**Raises:** `ValueError` if cell doesn't exist

#### Patch Attempt Operations

##### create_patch_attempt()
```python
attempt = manager.create_patch_attempt(
    cell_id=str,  # required, must exist
    successful_seal=bool,  # optional, default False
    successful_reseal=bool,  # optional, default False
    tasks_run=list,  # optional
    event_log=dict or list,  # optional
    notes=str  # optional
)
```

Creates a new patch attempt and saves it to storage.

**Returns:** `PatchAttempt` instance with auto-generated UUID

**Raises:** `ValueError` if cell_id doesn't reference an existing cell

##### get_patch_attempt()
```python
attempt = manager.get_patch_attempt(uuid)
```

Retrieve a patch attempt by UUID.

**Raises:** `ValueError` if attempt doesn't exist

##### list_patch_attempts()
```python
attempts = manager.list_patch_attempts(cell_id=None)
```

Get all patch attempts, optionally filtered by cell_id.

**Parameters:**
- `cell_id` (str, optional): Filter to only this cell's attempts

**Returns:** List of `PatchAttempt` instances

##### get_cell_patch_attempts()
```python
attempts = manager.get_cell_patch_attempts(cell_id)
```

Convenience method to get all attempts for a specific cell.

**Returns:** List of `PatchAttempt` instances

##### update_patch_attempt()
```python
manager.update_patch_attempt(attempt)
```

Update an existing patch attempt's metadata.

**Raises:** `ValueError` if attempt doesn't exist

##### delete_patch_attempt()
```python
manager.delete_patch_attempt(uuid)
```

Delete a patch attempt and all its files.

**Raises:** `ValueError` if attempt doesn't exist

#### Event Log Operations

##### get_event_log()
```python
event_log = manager.get_event_log(attempt_uuid)
```

Get the event log for a patch attempt.

**Returns:** dict/list or None if no event log exists

##### update_event_log()
```python
manager.update_event_log(attempt_uuid, event_log)
```

Update or create the event log for a patch attempt.

**Parameters:**
- `event_log` (dict or list): Event log data to save

#### Cellfie Operations

##### get_cellfie()
```python
cellfie_data = manager.get_cellfie(cell_uuid)
```

Get the cellfie image for a cell.

**Returns:** numpy.ndarray or None if no cellfie exists

##### update_cellfie()
```python
manager.update_cellfie(cell_uuid, cellfie_data)
```

Update or create the cellfie image for a cell.

**Parameters:**
- `cellfie_data` (numpy.ndarray): Image data to save

## Usage Patterns

### Basic Workflow

```python
# 1. Initialize storage
manager = CellStorageManager("/data/cells")

# 2. Create cell
cell = manager.create_cell(
    global_position={"x": 100.0, "y": 200.0, "z": 50.0},
    initial_resistance=5.2
)

# 3. Attempt to patch
attempt = manager.create_patch_attempt(
    cell_id=cell.uuid,
    successful_seal=True
)

# 4. Query results
all_attempts = manager.get_cell_patch_attempts(cell.uuid)
successful_attempts = [a for a in all_attempts if a.successful_seal]
```

### Adding Images and Logs

```python
# Add cellfie after cell creation
cellfie_data = acquire_cellfie_image()  # Your acquisition code
manager.update_cellfie(cell.uuid, cellfie_data)

# Update cell metadata to reflect the addition
cell = manager.get_cell(cell.uuid)
# cellfie_filename is automatically set when image is added

# Add event log after patch attempt
event_log = collect_device_events()  # Your event collection
manager.update_event_log(attempt.uuid, event_log)
```

### Filtering and Analysis

```python
# Get all cells
all_cells = manager.list_cells()

# Find cells with low resistance
low_resistance_cells = [c for c in all_cells if c.initial_resistance < 5.0]

# Get successful attempts for analysis
all_attempts = manager.list_patch_attempts()
successful = [a for a in all_attempts if a.successful_seal]
success_rate = len(successful) / len(all_attempts)

# Analyze by cell
for cell in all_cells:
    attempts = manager.get_cell_patch_attempts(cell.uuid)
    print(f"Cell {cell.uuid}: {len(attempts)} attempts")
```

## File Formats

### Metadata Files (metadata.json)

Pretty-printed JSON with 2-space indentation:

```json
{
  "uuid": "a1b2c3d4e5f6...",
  "global_position": {
    "x": 100.0,
    "y": 200.0,
    "z": 50.0
  },
  "initial_resistance": 5.2,
  "cellfie_filename": "cellfie.npy",
  "notes": "Pyramidal neuron"
}
```

### Event Logs (event_log.json)

Can be a list or dict:

```json
[
  {
    "time": "10:00:00",
    "device": "pipette",
    "event": "approach_start"
  },
  {
    "time": "10:00:15",
    "device": "pipette",
    "event": "seal_formed",
    "resistance": 1.2
  }
]
```

### Cellfie Images (cellfie.npy)

NumPy binary format for efficient storage and loading of 3D arrays.

## Error Handling

All methods raise `ValueError` with descriptive messages for:
- Non-existent UUIDs
- Invalid foreign key references (e.g., patch attempt with non-existent cell_id)
- Missing required fields in data models

Example:
```python
try:
    attempt = manager.create_patch_attempt(
        cell_id="non-existent-uuid",
        successful_seal=True
    )
except ValueError as e:
    print(f"Error: {e}")
    # Error: Cannot create patch attempt: cell with UUID non-existent-uuid does not exist
```

## Testing

The module includes comprehensive test coverage (79 tests):

```bash
python -m pytest acq4/util/cell_storage/test_cell_storage.py -v
```

Test categories:
- Data model validation
- Serialization round-trip
- CRUD operations
- Foreign key validation
- Event log handling
- Cellfie image handling
- Error cases

## Example Script

See `example.py` for a complete walkthrough demonstrating all features:

```bash
python -m acq4.util.cell_storage.example
```

## Notes

- **No Cascading Deletes**: Deleting a cell does NOT automatically delete its patch attempts. Delete attempts first if needed.
- **No Transactions**: Operations are not atomic. Use external mechanisms if transaction support is needed.
- **Thread Safety**: Not explicitly thread-safe. Use external locking if accessing from multiple threads.
- **Storage Format**: Designed for easy migration. All data is in human-readable or standard formats (JSON, NumPy .npy).

## Future Enhancements

Potential areas for expansion:
- Cascade delete options
- Bulk import/export utilities
- Query language for complex filters
- Integration with ACQ4 DataManager
- Versioning of metadata changes
- Index files for faster queries on large datasets
