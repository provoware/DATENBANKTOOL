"""Zentrale Projektmetadaten und Registry-Zugriff."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VERSION_PATH = ROOT / "VERSION.json"
REGISTRY_PATH = ROOT / "src" / "config" / "registry.json"


@lru_cache(maxsize=1)
def version_info() -> dict[str, Any]:
    return json.loads(VERSION_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def product() -> dict[str, Any]:
    return version_info()["product"]


def schema_version(name: str) -> int:
    return int(version_info()["schemas"][name])


def contract_version(name: str) -> int:
    return int(version_info()["contracts"][name])
