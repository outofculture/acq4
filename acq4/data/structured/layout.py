# acq4/data/structured/layout.py
# Directory layout helpers layered on top of acq4.util.DataManager.

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import acq4.util.DataManager as dm
from acq4.logging_config import get_logger

from .constants import (
    CELL_COLLECTION_NAME,
    PATCH_ATTEMPT_COLLECTION_NAME,
    STRUCTURED_ROOT_NAME,
)

logger = get_logger(__name__)

Pathish = Union[str, os.PathLike[str], Path]


@dataclass(frozen=True)
class StructuredRootLayout:
    """Bundles DirHandles and pathlib paths for the structured store roots."""

    root_handle: dm.DirHandle
    cells_handle: dm.DirHandle
    patch_attempts_handle: dm.DirHandle

    @property
    def root_path(self) -> Path:
        return Path(self.root_handle.name())

    @property
    def cells_path(self) -> Path:
        return Path(self.cells_handle.name())

    @property
    def patch_attempts_path(self) -> Path:
        return Path(self.patch_attempts_handle.name())


def ensure_structured_object_roots(
    base_dir: Pathish, root_name: str = STRUCTURED_ROOT_NAME
) -> StructuredRootLayout:
    """Ensure `<base>/structured_objects/{cells,patch_attempts}` exist."""

    base_handle = _coerce_dir_handle(base_dir)
    base_path = Path(base_handle.name())
    structured_root = base_path / root_name
    cells_root = structured_root / CELL_COLLECTION_NAME
    patch_root = structured_root / PATCH_ATTEMPT_COLLECTION_NAME

    for path in (structured_root, cells_root, patch_root):
        _ensure_directory(path)

    return StructuredRootLayout(
        root_handle=dm.getDirHandle(str(structured_root)),
        cells_handle=dm.getDirHandle(str(cells_root)),
        patch_attempts_handle=dm.getDirHandle(str(patch_root)),
    )


def _coerce_dir_handle(handle_or_path: Pathish) -> dm.DirHandle:
    if isinstance(handle_or_path, dm.DirHandle):
        return handle_or_path
    return dm.getDirHandle(os.fspath(handle_or_path))


def _ensure_directory(path: Path) -> None:
    if path.exists():
        return
    path.mkdir(parents=True, exist_ok=True)
    logger.debug("Created structured storage directory %s", path)
