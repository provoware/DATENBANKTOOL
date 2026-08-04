"""Öffentliche Paketinformationen."""

import json
from pathlib import Path
from typing import Any


def _package_version_from_display(display_version: str) -> str:
    """Wandle die dokumentierte Alpha-Schreibweise in die PEP-440-Schreibweise um."""
    return display_version.replace("-alpha.", "a")


def _read_registry() -> dict[str, Any]:
    registry = Path(__file__).resolve().parents[2] / "registry.json"
    payload = json.loads(registry.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("registry.json muss ein JSON-Objekt sein.")
    return payload


def _read_version() -> str:
    payload = _read_registry()
    version = payload.get("version")
    if isinstance(version, str) and version:
        return version
    display_version = payload.get("display_version")
    if isinstance(display_version, str) and display_version:
        return _package_version_from_display(display_version)
    raise RuntimeError("registry.json benötigt version oder display_version.")


__version__ = _read_version()
