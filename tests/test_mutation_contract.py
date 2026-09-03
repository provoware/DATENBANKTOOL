from __future__ import annotations

import json
import sqlite3

import pytest

from src.persistence import Database, EntryStore
from src.recovery import (
    EvidenceJournal,
    MutationBusyError,
    MutationCoordinator,
    MutationDuplicateError,
    MutationState,
)


def _database(tmp_path):
    database = Database(tmp_path / "data" / "user" / "provoware.sqlite3")
    database.initialize()
    return database


def test_mutation_contract_commits_and_writes_evidence(tmp_path):
    database = _database(tmp_path)
    coordinator = MutationCoordinator(database, tmp_path / "runtime")

    def mutation(connection: sqlite3.Connection) -> str:
        connection.execute(
            "INSERT INTO app_settings(key, value_json, updated_at) VALUES (?, ?, ?)",
            ("theme", '"dark"', "2026-09-03T00:00:00+00:00"),
        )
        return "theme"

    def postcheck(connection: sqlite3.Connection, key: str) -> None:
        row = connection.execute(
            "SELECT key FROM app_settings WHERE key = ?",
            (key,),
        ).fetchone()
        assert row is not None

    result = coordinator.execute(
        operation_kind="settings.create",
        target="setting:theme",
        mutation=mutation,
        postcheck=postcheck,
        details={"token": "secret", "safe": "visible"},
    )

    assert result.state is MutationState.COMMITTED
    evidence = json.loads(result.evidence_path.read_text(encoding="utf-8"))
    assert evidence["state"] == "COMMITTED"
    assert evidence["details"]["token"] == "[GESCHWÄRZT]"
    assert evidence["details"]["safe"] == "visible"
    assert evidence["transitions"] == [
        "RECEIVED",
        "PRECHECK",
        "MUTATION",
        "POSTCHECK",
        "COMMITTING",
        "COMMITTED",
    ]


def test_failed_postcheck_rolls_back_business_data(tmp_path):
    database = _database(tmp_path)
    coordinator = MutationCoordinator(database, tmp_path / "runtime")

    def mutation(connection: sqlite3.Connection) -> None:
        connection.execute(
            "INSERT INTO app_settings(key, value_json, updated_at) VALUES (?, ?, ?)",
            ("unsafe", "true", "2026-09-03T00:00:00+00:00"),
        )

    def postcheck(connection: sqlite3.Connection, value: None) -> None:
        del connection, value
        raise RuntimeError("POSTCHECK absichtlich fehlgeschlagen")

    with pytest.raises(RuntimeError):
        coordinator.execute(
            operation_kind="settings.create",
            target="setting:unsafe",
            mutation=mutation,
            postcheck=postcheck,
        )

    with database.connect() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM app_settings WHERE key = 'unsafe'"
        ).fetchone()[0]
    assert count == 0

    evidence_files = list(
        (tmp_path / "runtime" / "recovery" / "evidence").glob(
            "recovery_evidence_status_rolled-back_*.json"
        )
    )
    assert len(evidence_files) == 1


def test_busy_gate_rejects_parallel_mutation(tmp_path):
    database = _database(tmp_path)
    coordinator = MutationCoordinator(database, tmp_path / "runtime")
    coordinator._lock.acquire()
    try:
        with pytest.raises(MutationBusyError) as error:
            coordinator.execute(
                operation_kind="entry.create",
                target="entry:test",
                mutation=lambda connection: None,
            )
    finally:
        coordinator._lock.release()

    assert error.value.operation_id.startswith("op-")
    assert error.value.evidence_path is not None
    assert "status_rejected" in error.value.evidence_path.name


def test_idempotency_key_blocks_double_submit(tmp_path):
    database = _database(tmp_path)
    coordinator = MutationCoordinator(database, tmp_path / "runtime")

    def mutation(connection: sqlite3.Connection) -> None:
        connection.execute(
            "INSERT INTO app_settings(key, value_json, updated_at) VALUES (?, ?, ?)",
            ("double", "1", "2026-09-03T00:00:00+00:00"),
        )

    coordinator.execute(
        operation_kind="settings.create",
        target="setting:double",
        mutation=mutation,
        operation_key="button-click-123",
    )

    with pytest.raises(MutationDuplicateError):
        coordinator.execute(
            operation_kind="settings.create",
            target="setting:double",
            mutation=mutation,
            operation_key="button-click-123",
        )

    with database.connect() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM app_settings WHERE key = 'double'"
        ).fetchone()[0]
    assert count == 1


def test_incomplete_journal_operation_is_detected(tmp_path):
    journal = EvidenceJournal(tmp_path / "runtime")
    journal.append_transition(
        operation_id="op-crash-test",
        operation_kind="entry.create",
        target="entry:test",
        state="RECEIVED",
        key_hash=None,
    )
    journal.append_transition(
        operation_id="op-crash-test",
        operation_kind="entry.create",
        target="entry:test",
        state="COMMITTING",
        key_hash=None,
    )

    incomplete = journal.incomplete_operations()
    assert incomplete["op-crash-test"]["state"] == "COMMITTING"


def test_entry_store_uses_contract_and_operation_key(tmp_path):
    database = _database(tmp_path)
    store = EntryStore(database, runtime_dir=tmp_path / "runtime")

    created = store.create(
        kind="prompt",
        title="Testprompt",
        content="Inhalt",
        operation_key="prompt-create-1",
    )
    assert created.title == "Testprompt"

    with pytest.raises(MutationDuplicateError):
        store.create(
            kind="prompt",
            title="Testprompt",
            content="Inhalt",
            operation_key="prompt-create-1",
        )

    assert len(store.list(kind="prompt")) == 1
