from __future__ import annotations

import pytest

from src.persistence import (
    CURRENT_SCHEMA_VERSION,
    Database,
    EntryStore,
    EntryValidationError,
    MigrationError,
)


def test_fresh_database_migrates_and_is_idempotent(tmp_path):
    database = Database(tmp_path / "user" / "provoware.sqlite3")

    first = database.initialize()
    second = database.initialize()
    status = database.schema_status()

    assert first.from_version == 0
    assert first.to_version == CURRENT_SCHEMA_VERSION
    assert first.applied_versions == (1,)
    assert second.applied_versions == ()
    assert status.ready is True
    assert status.current_version == CURRENT_SCHEMA_VERSION
    assert status.journal_mode == "wal"


def test_initial_schema_contains_core_tables(tmp_path):
    database = Database(tmp_path / "provoware.sqlite3")
    database.initialize()

    with database.connect() as connection:
        names = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert {"entries", "tags", "entry_tags", "app_settings", "schema_migrations"} <= names


def test_entry_store_persists_hierarchy_and_metadata(tmp_path):
    database = Database(tmp_path / "provoware.sqlite3")
    database.initialize()
    store = EntryStore(database)

    parent = store.create(kind="archive", title="Sound")
    child = store.create(
        kind="prompt",
        title="HardTechno",
        content="Kick + Bass",
        parent_id=parent.id,
        favorite=True,
        metadata={"bpm": 155},
    )

    loaded = store.get(child.id)
    listed = store.list(kind="prompt")

    assert loaded is not None
    assert loaded.parent_id == parent.id
    assert loaded.favorite is True
    assert loaded.metadata == {"bpm": 155}
    assert [entry.id for entry in listed] == [child.id]


def test_entry_validation_rejects_empty_title(tmp_path):
    database = Database(tmp_path / "provoware.sqlite3")
    database.initialize()
    store = EntryStore(database)

    with pytest.raises(EntryValidationError):
        store.create(kind="memo", title="   ")


def test_precheck_blocks_unknown_parent(tmp_path):
    database = Database(tmp_path / "provoware.sqlite3")
    database.initialize()
    store = EntryStore(database)

    with pytest.raises(EntryValidationError, match="übergeordnete Eintrag existiert nicht"):
        store.create(kind="memo", title="Kind", parent_id="missing")

    assert store.list(kind="memo") == []


def test_integrity_check_reports_healthy_database(tmp_path):
    database = Database(tmp_path / "provoware.sqlite3")
    database.initialize()

    report = database.integrity_check()

    assert report.ok is True
    assert report.quick_check == ("ok",)
    assert report.foreign_key_violations == 0


def test_migration_checksum_drift_is_rejected(tmp_path):
    database = Database(tmp_path / "provoware.sqlite3")
    database.initialize()

    with database.connect() as connection:
        connection.execute("UPDATE schema_migrations SET checksum = 'wrong' WHERE version = 1")

    with pytest.raises(MigrationError):
        database.initialize()
