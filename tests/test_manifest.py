import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_has_required_standards() -> None:
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["file_limits"]["python"]["max_lines"] <= 500
    assert manifest["file_limits"]["javascript"]["max_lines"] <= 500
    assert manifest["logging"]["machine_format"] == "jsonl"
    assert "tests" in manifest["quality"]["release_blocking"]
