"""
Cell storage system for managing Cell and Patch Attempt objects in ACQ4.
"""
import os


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


__all__ = ['CellStorageManager']
