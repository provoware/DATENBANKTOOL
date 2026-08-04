"""Öffentliche Paketinformationen."""

import json
from pathlib import Path


def _read_version() -> str:
    registry = Path(__file__).resolve().parents[2] / "registry.json"
    return str(json.loads(registry.read_text(encoding="utf-8"))["version"])


__version__ = _read_version()
