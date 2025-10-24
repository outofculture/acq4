"""
Cellfie image utilities for cell storage.
"""
import os
import numpy as np

from .serialization import ensure_dir_exists


def save_cellfie(cellfie_data, directory_path, filename="cellfie.npy"):
    """
    Save a cellfie image to file.

    Parameters
    ----------
    cellfie_data : numpy.ndarray or None
        The cellfie image data to save. Typically a 3D numpy array.
        If None, no file is created.
    directory_path : str
        Path to the directory where the cellfie will be saved.
        The directory will be created if it doesn't exist.
    filename : str, optional
        Name of the file to save. Defaults to "cellfie.npy".
    """
    # Don't create a file if cellfie_data is None
    if cellfie_data is None:
        return

    # Ensure directory exists
    ensure_dir_exists(directory_path)

    # Save using numpy
    cellfie_file = os.path.join(directory_path, filename)
    np.save(cellfie_file, cellfie_data)


def load_cellfie(directory_path, filename="cellfie.npy"):
    """
    Load a cellfie image from file.

    Parameters
    ----------
    directory_path : str
        Path to the directory containing the cellfie file.
    filename : str, optional
        Name of the file to load. Defaults to "cellfie.npy".

    Returns
    -------
    numpy.ndarray or None
        The cellfie image data, or None if the file doesn't exist.
    """
    cellfie_file = os.path.join(directory_path, filename)

    if not os.path.exists(cellfie_file):
        return None

    return np.load(cellfie_file)


__all__ = ['save_cellfie', 'load_cellfie']
