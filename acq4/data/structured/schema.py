# acq4/data/structured/schema.py
# Shared schema version validation + upgrade helpers.

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Mapping, MutableMapping, Optional

from acq4.logging_config import get_logger

logger = get_logger(__name__)


UpgradeFunc = Callable[[Mapping[str, object]], Mapping[str, object]]


@dataclass
class SchemaRegistryEntry:
    expected_version: str
    upgrader: Optional[UpgradeFunc] = None


class SchemaRegistry:
    """Lightweight registry that keeps track of per-record schema versions."""

    def __init__(self):
        self._entries: Dict[str, SchemaRegistryEntry] = {}

    def register(
        self,
        record_type: str,
        expected_version: str,
        upgrader: UpgradeFunc | None = None,
    ):
        self._entries[record_type] = SchemaRegistryEntry(expected_version, upgrader)

    def validate_or_upgrade(
        self, record_type: str, payload: MutableMapping[str, object]
    ) -> Mapping[str, object]:
        entry = self._entries.get(record_type)
        if entry is None:
            raise ValueError(
                f"No schema entry registered for record type '{record_type}'"
            )

        version = payload.get("schema_version")
        if version is None:
            raise ValueError(f"{record_type} metadata missing schema_version")

        if version == entry.expected_version:
            return payload

        if entry.upgrader is None:
            raise ValueError(
                f"{record_type} schema_version '{version}' unsupported (expected '{entry.expected_version}')"
            )

        logger.info(
            "Upgrading %s schema from %s to %s",
            record_type,
            version,
            entry.expected_version,
        )
        upgraded = entry.upgrader(payload)
        upgraded["schema_version"] = entry.expected_version
        return upgraded


registry = SchemaRegistry()
