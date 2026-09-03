import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_has_required_standards() -> None:
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["file_limits"]["python"]["max_lines"] <= 500
    assert manifest["file_limits"]["javascript"]["max_lines"] <= 500
    assert manifest["logging"]["machine_format"] == "jsonl"
    assert manifest["persistence"]["engine"] == "sqlite3"
    assert manifest["persistence"]["schema_version"] == 1
    assert manifest["persistence"]["foreign_keys"] is True
    assert manifest["persistence"]["exclusive_restore_access_gate"] is True
    assert manifest["recovery"]["contract_version"] == 1
    assert manifest["recovery"]["single_writer_gate"] is True
    assert manifest["recovery"]["startup_incomplete_operation_gate"] is True
    assert manifest["recovery"]["evidence_schema_version"] == 1
    assert manifest["backup"]["contract_version"] == 1
    assert manifest["backup"]["manifest_version"] == 1
    assert manifest["backup"]["engine"] == "sqlite_backup_api"
    assert manifest["backup"]["supports_wal_source"] is True
    assert manifest["backup"]["atomic_publish_after_verification"] is True
    assert manifest["backup"]["incomplete_backup_is_valid"] is False
    assert manifest["backup"]["restore_enabled"] is True
    assert "sha256" in manifest["backup"]["verification_checks"]
    assert manifest["restore"]["contract_version"] == 1
    assert manifest["restore"]["backup_reverified_before_restore"] is True
    assert manifest["restore"]["product_untouched_before_swap"] is True
    assert manifest["restore"]["exclusive_database_access_during_swap"] is True
    assert manifest["restore"]["postcheck_required_before_commit"] is True
    assert manifest["restore"]["rollback_on_postcheck_failure"] is True
    assert manifest["restore"]["crash_boundary_state"] == "SWAPPING"
    assert manifest["restore"]["startup_gate_blocks_incomplete_restore"] is True
    assert "tests" in manifest["quality"]["release_blocking"]
