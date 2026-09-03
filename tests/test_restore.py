from __future__ import annotations

import json

import pytest

from src.backup import BackupManager, BackupVerificationError, RestoreManager
from src.persistence import Database
from src.recovery import EvidenceJournal


def _write_setting(database: Database, value: str) -> None:
    with database.connect() as connection:
        connection.execute(
            "INSERT INTO app_settings(key, value_json, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json, "
            "updated_at = excluded.updated_at",
            ("restore-test", json.dumps(value), "2026-09-03T00:00:00+00:00"),
        )


def _read_setting(database: Database) -> str:
    with database.connect() as connection:
        row = connection.execute(
            "SELECT value_json FROM app_settings WHERE key = ?",
            ("restore-test",),
        ).fetchone()
    return json.loads(row[0])


def _prepared_restore(tmp_path):
    database = Database(tmp_path / "user" / "provoware.sqlite3")
    database.initialize()
    _write_setting(database, "backup-stand")
    backups = BackupManager(database, tmp_path / "backups")
    backup = backups.create_backup()
    _write_setting(database, "produktiver-stand")
    restore = RestoreManager(database, backups, tmp_path / "runtime")
    return database, backups, backup, restore


def test_restore_reverifies_stages_swaps_and_commits(tmp_path):
    database, _, backup, restore = _prepared_restore(tmp_path)

    report = restore.restore_backup(backup.backup_path)

    assert report.ok is True
    assert report.operation_id.startswith("restore-")
    assert report.backup_id == backup.backup_id
    assert _read_setting(database) == "backup-stand"
    evidence = json.loads(report.evidence_path.read_text(encoding="utf-8"))
    assert evidence["state"] == "COMMITTED"
    assert evidence["transitions"][-1] == "COMMITTED"
    assert "SWAP_PREPARED" in evidence["transitions"]
    assert "SWAPPED" in evidence["transitions"]
    assert "POSTCHECK" in evidence["transitions"]


def test_tampered_backup_is_rejected_before_productive_change(tmp_path):
    database, backups, backup, restore = _prepared_restore(tmp_path)
    snapshot = backup.backup_path / "database.sqlite3"
    snapshot.write_bytes(snapshot.read_bytes() + b"tampered")

    with pytest.raises(BackupVerificationError):
        restore.restore_backup(backup.backup_path)

    assert _read_setting(database) == "produktiver-stand"
    journal = EvidenceJournal(tmp_path / "runtime")
    assert journal.incomplete_operations() == {}


def test_failure_before_swap_keeps_productive_data_unchanged(tmp_path):
    database, _, backup, restore = _prepared_restore(tmp_path)

    def fail(stage: str) -> None:
        if stage == "SWAP_PREPARED":
            raise RuntimeError("simulierter Fehler vor Swap")

    with pytest.raises(RuntimeError, match="vor Swap"):
        restore.restore_backup(backup.backup_path, fault_hook=fail)

    assert _read_setting(database) == "produktiver-stand"
    journal = EvidenceJournal(tmp_path / "runtime")
    assert journal.incomplete_operations() == {}


def test_failure_after_postcheck_rolls_back_previous_productive_state(tmp_path):
    database, _, backup, restore = _prepared_restore(tmp_path)

    def fail(stage: str) -> None:
        if stage == "POSTCHECK":
            raise RuntimeError("simulierter Fehler nach POSTCHECK")

    with pytest.raises(RuntimeError, match="POSTCHECK"):
        restore.restore_backup(backup.backup_path, fault_hook=fail)

    assert _read_setting(database) == "produktiver-stand"
    evidence_files = tuple(
        (tmp_path / "runtime" / "recovery" / "evidence").glob(
            "recovery_evidence_status_rolled-back_restore-*.json"
        )
    )
    assert len(evidence_files) == 1
    evidence = json.loads(evidence_files[0].read_text(encoding="utf-8"))
    assert evidence["state"] == "ROLLED_BACK"
    assert "ROLLING_BACK" in evidence["transitions"]
    assert "ROLLED_BACK" in evidence["transitions"]


def test_crash_at_swap_boundary_is_reconstructable_and_blocks_start(tmp_path):
    database, _, backup, restore = _prepared_restore(tmp_path)

    def crash(stage: str) -> None:
        if stage == "AFTER_REPLACE_BEFORE_SWAPPED":
            raise SystemExit("simulierter Prozessabbruch")

    with pytest.raises(SystemExit, match="Prozessabbruch"):
        restore.restore_backup(backup.backup_path, fault_hook=crash)

    assert _read_setting(database) == "backup-stand"
    incomplete = EvidenceJournal(tmp_path / "runtime").incomplete_operations()
    assert len(incomplete) == 1
    record = next(iter(incomplete.values()))
    assert record["state"] == "SWAPPING"
    assert record["details"]["expected_restore_sha256"] == backup.measured_sha256
    rollback_path = record["details"]["rollback_path"]
    assert rollback_path.endswith(".sqlite3")


def test_restore_staging_directory_is_cleaned_after_rejection(tmp_path):
    database, _, backup, restore = _prepared_restore(tmp_path)

    def fail(stage: str) -> None:
        if stage == "STAGING_VERIFIED":
            raise RuntimeError("Staging-Stopp")

    with pytest.raises(RuntimeError, match="Staging-Stopp"):
        restore.restore_backup(backup.backup_path, fault_hook=fail)

    assert _read_setting(database) == "produktiver-stand"
    assert tuple(restore.staging_root.glob("restore_staging_*.sqlite3")) == ()
