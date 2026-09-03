from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import uuid
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from src.backup.engine import BACKUP_DATABASE_FILENAME, BackupManager
from src.persistence.database import Database
from src.persistence.migrations import CURRENT_SCHEMA_VERSION
from src.recovery.evidence import EvidenceJournal, RecoveryEvidence
from src.recovery.gate import DatabaseOperationGate

FaultHook = Callable[[str], None]


class RestoreError(RuntimeError):
    """Restore could not be completed safely."""


class RestoreBusyError(RestoreError):
    """Another critical database operation owns the gate."""


@dataclass(frozen=True)
class RestoreReport:
    ok: bool
    operation_id: str
    backup_id: str
    restored_sha256: str
    previous_sha256: str
    schema_version: int
    evidence_path: Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _inspect(path: Path) -> tuple[int, tuple[str, ...], int]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        quick = tuple(str(row[0]) for row in connection.execute("PRAGMA quick_check"))
        foreign_rows = connection.execute("PRAGMA foreign_key_check").fetchall()
    finally:
        connection.close()
    return version, quick, len(foreign_rows)


def _copy_fsync(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    _fsync_file(destination)
    _fsync_directory(destination.parent)


class RestoreManager:
    """Verified staging restore with crash-reconstructable atomic replacement."""

    def __init__(
        self,
        database: Database,
        backup_manager: BackupManager,
        runtime_dir: Path,
    ) -> None:
        self.database = database
        self.backup_manager = backup_manager
        self.runtime_dir = Path(runtime_dir)
        self.journal = EvidenceJournal(runtime_dir)
        self.gate = DatabaseOperationGate(database.path)
        self.staging_root = self.runtime_dir / "recovery" / "restore_staging"
        self.rollback_root = self.runtime_dir / "recovery" / "restore_rollback"
        self.staging_root.mkdir(parents=True, exist_ok=True)
        self.rollback_root.mkdir(parents=True, exist_ok=True)

    def restore_backup(
        self,
        backup_path: Path,
        *,
        fault_hook: FaultHook | None = None,
    ) -> RestoreReport:
        if not self.gate.acquire():
            raise RestoreBusyError("Eine andere kritische Datenoperation läuft bereits.")
        try:
            return self._restore_locked(Path(backup_path), fault_hook=fault_hook)
        finally:
            self.gate.release()

    def _restore_locked(
        self,
        backup_path: Path,
        *,
        fault_hook: FaultHook | None,
    ) -> RestoreReport:
        verification = self.backup_manager.verify_backup(backup_path)
        expected_hash = verification.measured_sha256
        operation_id = f"restore-{uuid.uuid4().hex}"
        staging = self.staging_root / f"restore_staging_{operation_id}.sqlite3"
        rollback = self.rollback_root / f"restore_previous_{operation_id}.sqlite3"
        started_at = _utc_now()
        transitions: list[str] = []
        details = {
            "backup_id": verification.backup_id,
            "backup_directory": backup_path.name,
            "expected_restore_sha256": expected_hash,
            "staging_path": str(staging),
            "rollback_path": str(rollback),
        }

        def transition(state: str, extra: dict | None = None) -> None:
            transitions.append(state)
            merged = dict(details)
            if extra:
                merged.update(extra)
            self.journal.append_transition(
                operation_id=operation_id,
                operation_kind="database.restore",
                target=str(self.database.path),
                state=state,
                key_hash=None,
                details=merged,
            )

        source = backup_path / BACKUP_DATABASE_FILENAME
        try:
            _copy_fsync(source, staging)
            self._assert_staging(staging, expected_hash)
            if fault_hook is not None:
                fault_hook("STAGING_VERIFIED")

            previous_hash = self._prepare_previous_snapshot(rollback)
            details["previous_sha256"] = previous_hash
            transition("RESTORE_RECEIVED")
            transition("STAGING_VERIFIED")
            transition("ROLLBACK_READY")

            self._prepare_productive_for_swap()
            self._assert_staging(staging, expected_hash)
            transition("SWAP_PREPARED")
            if fault_hook is not None:
                fault_hook("SWAP_PREPARED")

            transition("SWAPPING")
            os.replace(staging, self.database.path)
            _fsync_directory(self.database.path.parent)
            if fault_hook is not None:
                fault_hook("AFTER_REPLACE_BEFORE_SWAPPED")
            transition("SWAPPED")

            self._postcheck_productive(expected_hash)
            transition("POSTCHECK")
            if fault_hook is not None:
                fault_hook("POSTCHECK")

            committed = transitions + ["COMMITTED"]
            evidence_path = self._finish(
                operation_id=operation_id,
                started_at=started_at,
                state="COMMITTED",
                transitions=committed,
                details=details,
            )
            transition("COMMITTED")
            return RestoreReport(
                ok=True,
                operation_id=operation_id,
                backup_id=verification.backup_id,
                restored_sha256=expected_hash,
                previous_sha256=previous_hash,
                schema_version=verification.measured_schema_version,
                evidence_path=evidence_path,
            )
        except Exception as exc:
            if "SWAPPED" in transitions:
                self._rollback_after_failed_postcheck(
                    operation_id,
                    rollback,
                    details,
                    transitions,
                )
                final_state = "ROLLED_BACK"
            elif "SWAPPING" in transitions:
                final_state = "FAILED"
            else:
                final_state = "REJECTED"
            self._finish(
                operation_id=operation_id,
                started_at=started_at,
                state=final_state,
                transitions=transitions,
                details=details,
                error_type=type(exc).__name__,
            )
            raise
        finally:
            if staging.exists():
                with suppress(OSError):
                    staging.unlink()

    def _assert_staging(self, staging: Path, expected_hash: str) -> None:
        measured_hash = _sha256(staging)
        version, quick, foreign_violations = _inspect(staging)
        if measured_hash != expected_hash:
            raise RestoreError("Staging-Hash stimmt nicht mit dem verifizierten Backup überein.")
        if version != CURRENT_SCHEMA_VERSION:
            raise RestoreError("Staging-Schema entspricht nicht der Zielversion.")
        if quick != ("ok",) or foreign_violations:
            raise RestoreError("Staging-Datenbank hat die Integritätsprüfung nicht bestanden.")

    def _prepare_previous_snapshot(self, rollback: Path) -> str:
        if not self.database.path.is_file():
            raise RestoreError("Produktivdatenbank fehlt.")
        source = self.database.connect_raw()
        target = sqlite3.connect(rollback)
        try:
            source.backup(target)
            target.commit()
        finally:
            target.close()
            source.close()
        _fsync_file(rollback)
        _fsync_directory(rollback.parent)
        version, quick, foreign_violations = _inspect(rollback)
        if version != CURRENT_SCHEMA_VERSION or quick != ("ok",) or foreign_violations:
            raise RestoreError("Rollback-Snapshot der Produktivdatenbank ist nicht integer.")
        return _sha256(rollback)

    def _prepare_productive_for_swap(self) -> None:
        connection = self.database.connect_raw()
        try:
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            mode = str(connection.execute("PRAGMA journal_mode = DELETE").fetchone()[0])
            if mode.lower() != "delete":
                raise RestoreError("Produktivdatenbank konnte nicht aus WAL gelöst werden.")
        finally:
            connection.close()
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(self.database.path) + suffix)
            if sidecar.exists():
                raise RestoreError("SQLite-WAL-Seitendatei ist vor dem Swap noch aktiv.")

    def _postcheck_productive(self, expected_hash: str) -> None:
        if _sha256(self.database.path) != expected_hash:
            raise RestoreError("Produktivdatenbank hat nach Swap einen unerwarteten Hash.")
        version, quick, foreign_violations = _inspect(self.database.path)
        if version != CURRENT_SCHEMA_VERSION:
            raise RestoreError("Produktivschema ist nach Restore ungültig.")
        if quick != ("ok",) or foreign_violations:
            raise RestoreError("Produktivdatenbank ist nach Restore nicht integer.")

    def _rollback_after_failed_postcheck(
        self,
        operation_id: str,
        rollback: Path,
        details: dict,
        transitions: list[str],
    ) -> None:
        transitions.append("ROLLING_BACK")
        self.journal.append_transition(
            operation_id=operation_id,
            operation_kind="database.restore",
            target=str(self.database.path),
            state="ROLLING_BACK",
            key_hash=None,
            details=details,
        )
        if not rollback.is_file():
            raise RestoreError("Rollback-Datei fehlt nach fehlgeschlagenem POSTCHECK.")
        os.replace(rollback, self.database.path)
        _fsync_directory(self.database.path.parent)
        previous_hash = str(details.get("previous_sha256") or "")
        if not previous_hash or _sha256(self.database.path) != previous_hash:
            raise RestoreError("Rollback konnte den vorherigen Produktivstand nicht bestätigen.")
        version, quick, foreign_violations = _inspect(self.database.path)
        if version != CURRENT_SCHEMA_VERSION or quick != ("ok",) or foreign_violations:
            raise RestoreError("Rollback-Datenbank ist nach Rücktausch nicht integer.")
        transitions.append("ROLLED_BACK")
        self.journal.append_transition(
            operation_id=operation_id,
            operation_kind="database.restore",
            target=str(self.database.path),
            state="ROLLED_BACK",
            key_hash=None,
            details=details,
        )

    def _finish(
        self,
        *,
        operation_id: str,
        started_at: str,
        state: str,
        transitions: list[str],
        details: dict,
        error_type: str | None = None,
    ) -> Path:
        evidence = RecoveryEvidence(
            schema_version=1,
            operation_id=operation_id,
            operation_kind="database.restore",
            target=str(self.database.path),
            state=state,
            started_at=started_at,
            finished_at=_utc_now(),
            key_hash=None,
            transitions=tuple(transitions),
            details=details,
            error_type=error_type,
        )
        return self.journal.write_final(evidence)
