"""
Cell storage system for managing Cell and Patch Attempt objects in ACQ4.
"""
import os
import shutil

from .models import Cell, PatchAttempt
from .serialization import save_metadata, load_metadata


class CellStorageManager:
    """
    Manager class for storing and retrieving Cell and Patch Attempt objects.

    This class provides a simple file-based storage system using UUID-named
    directories with metadata.json files and associated data files. Storage
    is organized into two top-level directories: cells/ and patch_attempts/.

    Parameters
    ----------
    base_dir : str
        The base directory path for storage. Will be created if it doesn't exist.
        Two subdirectories will be created: cells/ and patch_attempts/.

    Attributes
    ----------
    base_dir : str
        Absolute path to the base storage directory.
    """

    def __init__(self, base_dir):
        """
        Initialize the CellStorageManager.

        Parameters
        ----------
        base_dir : str
            The base directory path for storage.
        """
        # Store as absolute path
        self.base_dir = os.path.abspath(base_dir)

        # Create base directory if it doesn't exist
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

        # Create subdirectories for cells and patch attempts
        cells_dir = self._get_cells_dir()
        if not os.path.exists(cells_dir):
            os.makedirs(cells_dir)

        attempts_dir = self._get_attempts_dir()
        if not os.path.exists(attempts_dir):
            os.makedirs(attempts_dir)

    def _get_cells_dir(self):
        """
        Get the absolute path to the cells directory.

        Returns
        -------
        str
            Absolute path to the cells/ subdirectory.
        """
        return os.path.join(self.base_dir, "cells")

    def _get_attempts_dir(self):
        """
        Get the absolute path to the patch_attempts directory.

        Returns
        -------
        str
            Absolute path to the patch_attempts/ subdirectory.
        """
        return os.path.join(self.base_dir, "patch_attempts")

    def create_cell(self, global_position, initial_resistance, cellfie_data=None, notes=""):
        """
        Create a new cell and save it to storage.

        Parameters
        ----------
        global_position : dict
            Dictionary with 'x', 'y', 'z' keys (floats) for cell position.
        initial_resistance : float
            Initial resistance measurement in MΩ.
        cellfie_data : optional
            Image data for the cellfie (not yet implemented).
        notes : str, optional
            Notes about the cell.

        Returns
        -------
        Cell
            The newly created Cell instance.
        """
        # Create the Cell instance (UUID auto-generated)
        cell = Cell(
            global_position=global_position,
            initial_resistance=initial_resistance,
            notes=notes
        )

        # Create the cell's directory
        cell_dir = os.path.join(self._get_cells_dir(), cell.uuid)

        # Save metadata
        save_metadata(cell, cell_dir)

        # TODO: Handle cellfie_data when needed (Step 7)

        return cell

    def get_cell(self, uuid):
        """
        Retrieve a cell by its UUID.

        Parameters
        ----------
        uuid : str
            The UUID of the cell to retrieve.

        Returns
        -------
        Cell
            The Cell instance.

        Raises
        ------
        ValueError
            If the cell doesn't exist.
        """
        cell_dir = os.path.join(self._get_cells_dir(), uuid)

        if not os.path.exists(cell_dir):
            raise ValueError(f"Cell with UUID {uuid} does not exist")

        return load_metadata(cell_dir, Cell)

    def list_cells(self):
        """
        List all cells in storage.

        Returns
        -------
        list of Cell
            List of all Cell instances in storage.
        """
        cells = []
        cells_dir = self._get_cells_dir()

        # Scan the cells directory for subdirectories
        if not os.path.exists(cells_dir):
            return cells

        for item in os.listdir(cells_dir):
            item_path = os.path.join(cells_dir, item)
            if os.path.isdir(item_path):
                try:
                    cell = load_metadata(item_path, Cell)
                    cells.append(cell)
                except (FileNotFoundError, Exception):
                    # Skip directories that don't have valid metadata
                    continue

        return cells

    def update_cell(self, cell):
        """
        Update a cell's metadata in storage.

        Parameters
        ----------
        cell : Cell
            The Cell instance with updated data.

        Raises
        ------
        ValueError
            If the cell doesn't exist.
        """
        cell_dir = os.path.join(self._get_cells_dir(), cell.uuid)

        if not os.path.exists(cell_dir):
            raise ValueError(f"Cell with UUID {cell.uuid} does not exist")

        # Save the updated metadata
        save_metadata(cell, cell_dir)

    def delete_cell(self, uuid):
        """
        Delete a cell from storage.

        Parameters
        ----------
        uuid : str
            The UUID of the cell to delete.

        Raises
        ------
        ValueError
            If the cell doesn't exist.
        """
        cell_dir = os.path.join(self._get_cells_dir(), uuid)

        if not os.path.exists(cell_dir):
            raise ValueError(f"Cell with UUID {uuid} does not exist")

        # Remove the entire directory
        shutil.rmtree(cell_dir)

    def create_patch_attempt(self, cell_id, successful_seal=False,
                            successful_reseal=False, tasks_run=None,
                            event_log=None, notes=""):
        """
        Create a new patch attempt and save it to storage.

        Parameters
        ----------
        cell_id : str
            UUID of the cell this attempt is for. Must reference an existing cell.
        successful_seal : bool, optional
            Whether seal formation was successful. Defaults to False.
        successful_reseal : bool, optional
            Whether reseal was successful. Defaults to False.
        tasks_run : list of str, optional
            List of task names that were executed.
        event_log : optional
            Event log data (not yet implemented).
        notes : str, optional
            Notes about the attempt.

        Returns
        -------
        PatchAttempt
            The newly created PatchAttempt instance.

        Raises
        ------
        ValueError
            If the cell_id doesn't reference an existing cell.
        """
        # Validate that the cell exists
        try:
            self.get_cell(cell_id)
        except ValueError:
            raise ValueError(f"Cannot create patch attempt: cell with UUID {cell_id} does not exist")

        # Create the PatchAttempt instance (UUID auto-generated)
        attempt = PatchAttempt(
            cell_id=cell_id,
            successful_seal=successful_seal,
            successful_reseal=successful_reseal,
            tasks_run=tasks_run,
            notes=notes
        )

        # Create the attempt's directory
        attempt_dir = os.path.join(self._get_attempts_dir(), attempt.uuid)

        # Save metadata
        save_metadata(attempt, attempt_dir)

        # TODO: Handle event_log when needed (Step 6)

        return attempt

    def get_patch_attempt(self, uuid):
        """
        Retrieve a patch attempt by its UUID.

        Parameters
        ----------
        uuid : str
            The UUID of the patch attempt to retrieve.

        Returns
        -------
        PatchAttempt
            The PatchAttempt instance.

        Raises
        ------
        ValueError
            If the patch attempt doesn't exist.
        """
        attempt_dir = os.path.join(self._get_attempts_dir(), uuid)

        if not os.path.exists(attempt_dir):
            raise ValueError(f"Patch attempt with UUID {uuid} does not exist")

        return load_metadata(attempt_dir, PatchAttempt)

    def list_patch_attempts(self, cell_id=None):
        """
        List all patch attempts in storage, optionally filtered by cell_id.

        Parameters
        ----------
        cell_id : str, optional
            If provided, only return attempts for this cell.

        Returns
        -------
        list of PatchAttempt
            List of PatchAttempt instances.
        """
        attempts = []
        attempts_dir = self._get_attempts_dir()

        # Scan the attempts directory for subdirectories
        if not os.path.exists(attempts_dir):
            return attempts

        for item in os.listdir(attempts_dir):
            item_path = os.path.join(attempts_dir, item)
            if os.path.isdir(item_path):
                try:
                    attempt = load_metadata(item_path, PatchAttempt)

                    # Filter by cell_id if specified
                    if cell_id is None or attempt.cell_id == cell_id:
                        attempts.append(attempt)
                except (FileNotFoundError, Exception):
                    # Skip directories that don't have valid metadata
                    continue

        return attempts

    def get_cell_patch_attempts(self, cell_id):
        """
        Convenience method to get all patch attempts for a specific cell.

        Parameters
        ----------
        cell_id : str
            UUID of the cell.

        Returns
        -------
        list of PatchAttempt
            List of PatchAttempt instances for this cell.
        """
        return self.list_patch_attempts(cell_id=cell_id)

    def update_patch_attempt(self, attempt):
        """
        Update a patch attempt's metadata in storage.

        Parameters
        ----------
        attempt : PatchAttempt
            The PatchAttempt instance with updated data.

        Raises
        ------
        ValueError
            If the patch attempt doesn't exist.
        """
        attempt_dir = os.path.join(self._get_attempts_dir(), attempt.uuid)

        if not os.path.exists(attempt_dir):
            raise ValueError(f"Patch attempt with UUID {attempt.uuid} does not exist")

        # Save the updated metadata
        save_metadata(attempt, attempt_dir)

    def delete_patch_attempt(self, uuid):
        """
        Delete a patch attempt from storage.

        Parameters
        ----------
        uuid : str
            The UUID of the patch attempt to delete.

        Raises
        ------
        ValueError
            If the patch attempt doesn't exist.
        """
        attempt_dir = os.path.join(self._get_attempts_dir(), uuid)

        if not os.path.exists(attempt_dir):
            raise ValueError(f"Patch attempt with UUID {uuid} does not exist")

        # Remove the entire directory
        shutil.rmtree(attempt_dir)


__all__ = ['CellStorageManager']
