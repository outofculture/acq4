"""
Event log utilities for patch attempt storage.
"""
import os
import json

from .serialization import ensure_dir_exists


def save_event_log(event_log, directory_path):
    """
    Save an event log to event_log.json.

    Parameters
    ----------
    event_log : dict, list, or None
        The event log data to save. Can be a dictionary or list of events.
        If None, no file is created.
    directory_path : str
        Path to the directory where event_log.json will be saved.
        The directory will be created if it doesn't exist.
    """
    # Don't create a file if event_log is None
    if event_log is None:
        return

    # Ensure directory exists
    ensure_dir_exists(directory_path)

    # Write to event_log.json with pretty formatting
    event_log_file = os.path.join(directory_path, "event_log.json")
    with open(event_log_file, 'w', encoding='utf-8') as f:
        json.dump(event_log, f, indent=2, ensure_ascii=False)


def load_event_log(directory_path):
    """
    Load an event log from event_log.json.

    Parameters
    ----------
    directory_path : str
        Path to the directory containing event_log.json.

    Returns
    -------
    dict, list, or None
        The event log data, or None if the file doesn't exist.
    """
    event_log_file = os.path.join(directory_path, "event_log.json")

    if not os.path.exists(event_log_file):
        return None

    with open(event_log_file, 'r', encoding='utf-8') as f:
        return json.load(f)


__all__ = ['save_event_log', 'load_event_log']
