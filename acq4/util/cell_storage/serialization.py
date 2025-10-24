"""
JSON serialization utilities for Cell and PatchAttempt metadata.
"""
import os
import json


def ensure_dir_exists(path):
    """
    Create a directory if it doesn't already exist.

    Parameters
    ----------
    path : str
        Path to the directory to create.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def save_metadata(obj, directory_path):
    """
    Save a Cell or PatchAttempt object as metadata.json.

    This function converts the object to a dictionary using its to_dict() method
    and saves it as a formatted JSON file in the specified directory.

    Parameters
    ----------
    obj : Cell or PatchAttempt
        The object to save. Must have a to_dict() method.
    directory_path : str
        Path to the directory where metadata.json will be saved.
        The directory will be created if it doesn't exist.

    Raises
    ------
    IOError
        If there's an error writing the file.
    """
    # Ensure directory exists
    ensure_dir_exists(directory_path)

    # Convert object to dictionary
    data = obj.to_dict()

    # Write to metadata.json with pretty formatting
    metadata_file = os.path.join(directory_path, "metadata.json")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_metadata(directory_path, model_class):
    """
    Load a Cell or PatchAttempt object from metadata.json.

    This function reads metadata.json from the specified directory and
    creates an instance of the model_class using its from_dict() classmethod.

    Parameters
    ----------
    directory_path : str
        Path to the directory containing metadata.json.
    model_class : type
        The class to instantiate (Cell or PatchAttempt).
        Must have a from_dict() classmethod.

    Returns
    -------
    Cell or PatchAttempt
        Instance created from the metadata.

    Raises
    ------
    FileNotFoundError
        If metadata.json doesn't exist in the directory.
    json.JSONDecodeError
        If the JSON file is malformed.
    """
    metadata_file = os.path.join(directory_path, "metadata.json")

    if not os.path.exists(metadata_file):
        raise FileNotFoundError(
            f"Metadata file not found: {metadata_file}"
        )

    with open(metadata_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return model_class.from_dict(data)


__all__ = ['save_metadata', 'load_metadata', 'ensure_dir_exists']
