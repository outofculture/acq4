"""
Data models for Cell and Patch Attempt objects.
"""
import uuid as uuid_module


class Cell:
    """
    Represents a cell in the cell storage system.

    Parameters
    ----------
    uuid : str, optional
        Unique identifier for the cell. If not provided, one will be auto-generated.
    global_position : dict
        Dictionary with 'x', 'y', 'z' keys (floats) representing the cell's position.
    initial_resistance : float
        Initial resistance measurement in MΩ.
    cellfie_filename : str, optional
        Filename of the cellfie image (e.g., 'cellfie.ma').
    notes : str, optional
        Free-form notes about the cell. Defaults to empty string.

    Attributes
    ----------
    uuid : str
        Unique identifier for the cell.
    global_position : dict
        Cell's global position with x, y, z coordinates.
    initial_resistance : float
        Initial resistance in MΩ.
    cellfie_filename : str or None
        Filename of the cellfie image if one exists.
    notes : str
        Notes about the cell.
    """

    def __init__(self, global_position, initial_resistance, uuid=None,
                 cellfie_filename=None, notes=""):
        """
        Initialize a Cell instance.

        Parameters
        ----------
        global_position : dict
            Dictionary with 'x', 'y', 'z' keys.
        initial_resistance : float
            Initial resistance in MΩ.
        uuid : str, optional
            Unique identifier. Auto-generated if not provided.
        cellfie_filename : str, optional
            Cellfie image filename.
        notes : str, optional
            Notes about the cell.

        Raises
        ------
        ValueError
            If global_position doesn't have x, y, z keys.
        """
        # Validate global_position has required keys
        if not all(key in global_position for key in ['x', 'y', 'z']):
            raise ValueError("global_position must have 'x', 'y', and 'z' keys")

        # Auto-generate UUID if not provided
        if uuid is None:
            uuid = uuid_module.uuid4().hex

        self.uuid = uuid
        self.global_position = global_position
        self.initial_resistance = initial_resistance
        self.cellfie_filename = cellfie_filename
        self.notes = notes

    def to_dict(self):
        """
        Convert Cell to a dictionary.

        Returns
        -------
        dict
            Dictionary representation of the Cell.
        """
        return {
            "uuid": self.uuid,
            "global_position": self.global_position,
            "initial_resistance": self.initial_resistance,
            "cellfie_filename": self.cellfie_filename,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a Cell from a dictionary.

        Parameters
        ----------
        data : dict
            Dictionary with Cell fields.

        Returns
        -------
        Cell
            New Cell instance.
        """
        return cls(
            uuid=data["uuid"],
            global_position=data["global_position"],
            initial_resistance=data["initial_resistance"],
            cellfie_filename=data.get("cellfie_filename"),
            notes=data.get("notes", "")
        )

    def __repr__(self):
        """Return string representation of Cell."""
        return (f"Cell(uuid={self.uuid!r}, "
                f"position={self.global_position}, "
                f"resistance={self.initial_resistance})")


class PatchAttempt:
    """
    Represents a patch attempt in the cell storage system.

    Parameters
    ----------
    cell_id : str
        UUID of the cell this attempt is for.
    uuid : str, optional
        Unique identifier for the attempt. If not provided, one will be auto-generated.
    successful_seal : bool, optional
        Whether a seal was successfully formed. Defaults to False.
    successful_reseal : bool, optional
        Whether a reseal was successful. Defaults to False.
    tasks_run : list of str, optional
        List of task names that were run. Defaults to empty list.
    event_log_filename : str, optional
        Filename of the event log (e.g., 'event_log.json').
    notes : str, optional
        Free-form notes about the attempt. Defaults to empty string.

    Attributes
    ----------
    uuid : str
        Unique identifier for the attempt.
    cell_id : str
        UUID of the associated cell.
    successful_seal : bool
        Whether seal formation was successful.
    successful_reseal : bool
        Whether reseal was successful.
    tasks_run : list
        List of task names that were executed.
    event_log_filename : str or None
        Filename of the event log if one exists.
    notes : str
        Notes about the attempt.
    """

    def __init__(self, cell_id, uuid=None, successful_seal=False,
                 successful_reseal=False, tasks_run=None,
                 event_log_filename=None, notes=""):
        """
        Initialize a PatchAttempt instance.

        Parameters
        ----------
        cell_id : str
            UUID of the cell this attempt is for.
        uuid : str, optional
            Unique identifier. Auto-generated if not provided.
        successful_seal : bool, optional
            Whether seal was successful.
        successful_reseal : bool, optional
            Whether reseal was successful.
        tasks_run : list of str, optional
            Tasks that were run.
        event_log_filename : str, optional
            Event log filename.
        notes : str, optional
            Notes about the attempt.
        """
        # Auto-generate UUID if not provided
        if uuid is None:
            uuid = uuid_module.uuid4().hex

        # Default tasks_run to empty list if None
        if tasks_run is None:
            tasks_run = []

        self.uuid = uuid
        self.cell_id = cell_id
        self.successful_seal = successful_seal
        self.successful_reseal = successful_reseal
        self.tasks_run = tasks_run
        self.event_log_filename = event_log_filename
        self.notes = notes

    def to_dict(self):
        """
        Convert PatchAttempt to a dictionary.

        Returns
        -------
        dict
            Dictionary representation of the PatchAttempt.
        """
        return {
            "uuid": self.uuid,
            "cell_id": self.cell_id,
            "successful_seal": self.successful_seal,
            "successful_reseal": self.successful_reseal,
            "tasks_run": self.tasks_run,
            "event_log_filename": self.event_log_filename,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a PatchAttempt from a dictionary.

        Parameters
        ----------
        data : dict
            Dictionary with PatchAttempt fields.

        Returns
        -------
        PatchAttempt
            New PatchAttempt instance.
        """
        return cls(
            uuid=data["uuid"],
            cell_id=data["cell_id"],
            successful_seal=data.get("successful_seal", False),
            successful_reseal=data.get("successful_reseal", False),
            tasks_run=data.get("tasks_run", []),
            event_log_filename=data.get("event_log_filename"),
            notes=data.get("notes", "")
        )

    def __repr__(self):
        """Return string representation of PatchAttempt."""
        return (f"PatchAttempt(uuid={self.uuid!r}, "
                f"cell_id={self.cell_id!r}, "
                f"seal={self.successful_seal})")


__all__ = ['Cell', 'PatchAttempt']
