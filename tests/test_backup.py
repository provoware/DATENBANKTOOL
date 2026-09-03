from __future__ import annotations

import json
import sqlite3

import pytest

from src.backup import BackupManager, BackupVerificationError
from src.persistence import CURRENT_SCHEMA_VERSION, Database, EntryStore


def _prepared_database(tmp_path):
    database = Database(tmp_path / "user" / "provoware.sqlite3")
    database.initialize()
    store = EntryStore(database, runtime_dir=tmp_path / "runtime")
    entry = store.create(
        kind="memo",
        title="Backup-Test",
        content="Diese Daten müssen im Snapshot vorhanden sein.",
    )
    return database, entry


def test_backup_creates_verified_manifest_and_snapshot(tmp_path):
    database, entry = _prepared_database(tmp_path)
    manager = BackupManager(database, tmp_path / "backups")

    report = manager.create_backup()

    assert report.ok is True
    assert report.backup_id.startswith("bkp-")
    assert report.backup_path.name.startswith("backup_status_verified_")
    assert report.manifest.manifest_version == 1
    assert report.manifest.status == "verified"
    assert report.manifest.sha256 == report.measured_sha256
    assert report.manifest.size_bytes == report.measured_size_bytes
    assert report.manifest.schema_version == CURRENT_SCHEMA_VERSION
    assert report.manifest.integrity_ok is True
    assert report.quick_check == ("ok",)
    assert report.foreign_key_violations == 0

    snapshot = report.backup_path / "database.sqlite3"
    connection = sqlite3.connect(snapshot)
    try:
        row = connection.execute(
            "SELECT title, content FROM entries WHERE id = ?",
            (entry.id,),
        ).fetchone()
    finally:
        connection.close()
    assert row == ("Backup-Test", "Diese Daten müssen im Snapshot vorhanden sein.")


def test_backup_uses_sqlite_snapshot_with_wal_source(tmp_path):
    database, _ = _prepared_database(tmp_path)
    with database.connect() as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        connection.execute(
            "INSERT INTO app_settings(key, value_json, updated_at) VALUES (?, ?, ?)",
            ("wal-test", '"sichtbar"', "2026-09-03T00:00:00+00:00"),
        )

    manager = BackupManager(database, tmp_path / "backups")
    report = manager.create_backup()
    snapshot = report.backup_path / "database.sqlite3"

    connection = sqlite3.connect(snapshot)
    try:
        value = connection.execute(
            "SELECT value_json FROM app_settings WHERE key = 'wal-test'"
        ).fetchone()[0]
    finally:
        connection.close()
    assert value == '"sichtbar"'


def test_verification_rejects_modified_snapshot(tmp_path):
    database, _ = _prepared_database(tmp_path)
    manager = BackupManager(database, tmp_path / "backups")
    report = manager.create_backup()
    snapshot = report.backup_path / "database.sqlite3"

    with snapshot.open("ab") as handle:
        handle.write(b"manipulation")

    with pytest.raises(BackupVerificationError, match="fehlgeschlagen"):
        manager.verify_backup(report.backup_path)
    assert manager.list_verified_backups() == ()


def test_verification_rejects_modified_manifest(tmp_path):
    database, _ = _prepared_database(tmp_path)
    manager = BackupManager(database, tmp_path / "backups")
    report = manager.create_backup()
    manifest_path = report.backup_path / "backup_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(BackupVerificationError, match="fehlgeschlagen"):
        manager.verify_backup(report.backup_path)


def test_incomplete_staging_is_never_listed_as_valid(tmp_path, monkeypatch):
    database, _ = _prepared_database(tmp_path)
    manager = BackupManager(database, tmp_path / "backups")

    def fail_verification(*args, **kwargs):
        raise BackupVerificationError("simulierter Verifikationsfehler")

    monkeypatch.setattr(manager, "verify_backup", fail_verification)
    with pytest.raises(BackupVerificationError, match="simulierter"):
        manager.create_backup()

    incomplete = tuple((tmp_path / "backups").glob(".incomplete_*"))
    assert len(incomplete) == 1
    assert (incomplete[0] / "STATUS_UNVOLLSTAENDIG.txt").is_file()
    assert not tuple((tmp_path / "backups").glob("backup_status_verified_*"))


def test_staging_backup_is_rejected_by_public_verification(tmp_path):
    database, _ = _prepared_database(tmp_path)
    manager = BackupManager(database, tmp_path / "backups")
    report = manager.create_backup()
    staging = tmp_path / "backups" / ".incomplete_manual"
    staging.mkdir()
    for name in ("database.sqlite3", "backup_manifest.json"):
        source = report.backup_path / name
        (staging / name).write_bytes(source.read_bytes())

    with pytest.raises(BackupVerificationError, match="Staging"):
        manager.verify_backup(staging)
