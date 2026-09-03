from __future__ import annotations

import json
from pathlib import Path

from src.core import contract_version, product, registry, schema_version, version_info

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_version_sources_are_consistent() -> None:
    version = version_info()
    manifest = load_json("MANIFEST.json")
    ui_meta = load_json("src/web/project-meta.json")

    assert version["schema_version"] == 1
    assert product()["version"] == manifest["project"]["version"]
    assert ui_meta["product"]["version"] == product()["version"]
    assert ui_meta["product"]["status_id"] == product()["status_id"]
    assert ui_meta["product"]["progress_percent"] == product()["progress_percent"]


def test_registry_has_unique_stable_ids_and_existing_paths() -> None:
    data = registry()
    assert data["registry_version"] == schema_version("registry")

    module_ids = [item["id"] for item in data["modules"]]
    endpoint_ids = [item["id"] for item in data["api"]]
    endpoint_pairs = [(item["method"], item["path"]) for item in data["api"]]

    assert len(module_ids) == len(set(module_ids))
    assert len(endpoint_ids) == len(set(endpoint_ids))
    assert len(endpoint_pairs) == len(set(endpoint_pairs))
    for item in data["modules"]:
        assert (ROOT / item["path"]).exists()


def test_contract_versions_match_manifest() -> None:
    manifest = load_json("MANIFEST.json")
    assert contract_version("recovery") == manifest["recovery"]["contract_version"]
    assert contract_version("backup") == manifest["backup"]["contract_version"]
    assert contract_version("restore") == manifest["restore"]["contract_version"]


def test_locale_catalog_and_ui_tokens_are_versioned() -> None:
    locale = load_json("src/web/i18n/de.json")
    css = (ROOT / "src/web/styles.css").read_text(encoding="utf-8")

    assert locale["catalog_version"] == schema_version("locale_catalog")
    assert locale["locale"] == version_info()["compatibility"]["default_locale"]
    assert len(locale["messages"]) >= 20
    for token in ("--space-1", "--space-4", "--radius-md", "--shadow-card", "--color-primary"):
        assert token in css


def test_tool_schema_references_existing_critical_files() -> None:
    schema = load_json("TOOL_SCHEMA.json")
    assert schema["schema_version"] == schema_version("tool_schema")
    for path in schema["critical_files"]:
        assert (ROOT / path).is_file()
