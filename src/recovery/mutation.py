from __future__ import annotations

import hashlib
import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Generic, TypeVar

from src.persistence.database import Database
from src.recovery.evidence import EvidenceJournal, RecoveryEvidence
from src.recovery.gate import DatabaseOperationGate

T = TypeVar("T")
Precheck = Callable[[sqlite3.Connection], None]
Mutation = Callable[[sqlite3.Connection], T]


class MutationState(str, Enum):
    RECEIVED = "RECEIVED"
    PRECHECK = "PRECHECK"
    MUTATION = "MUTATION"
    POSTCHECK = "POSTCHECK"
    COMMITTING = "COMMITTING"
    COMMITTED = "COMMITTED"
    ROLLING_BACK = "ROLLING_BACK"
    ROLLED_BACK = "ROLLED_BACK"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class MutationContractError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        operation_id: str,
        evidence_path: Path | None = None,
    ) -> None:
        super().__init__(message)
        self.operation_id = operation_id
        self.evidence_path = evidence_path


class MutationBusyError(MutationContractError):
    """Raised when another critical mutation owns the database gate."""


class MutationDuplicateError(MutationContractError):
    """Raised when the same idempotency key was already committed."""


@dataclass(frozen=True)
class MutationResult(Generic[T]):
    operation_id: str
    state: MutationState
    value: T
    evidence_path: Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _key_hash(operation_key: str | None) -> str | None:
    if operation_key is None:
        return None
    cleaned = operation_key.strip()
    if not cleaned:
        return None
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


def _validate_label(name: str, value: str, maximum: int) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{name} darf nicht leer sein.")
    if len(cleaned) > maximum:
        raise ValueError(f"{name} ist länger als {maximum} Zeichen.")
    return cleaned


class MutationCoordinator:
    """Single mutation gate plus transactional PRE/POST contract."""

    def __init__(self, database: Database, runtime_dir: Path) -> None:
        self.database = database
        self.journal = EvidenceJournal(runtime_dir)
        self.gate = DatabaseOperationGate(database.path)

    def execute(
        self,
        *,
        operation_kind: str,
        target: str,
        mutation: Mutation[T],
        precheck: Precheck | None = None,
        postcheck: Callable[[sqlite3.Connection, T], None] | None = None,
        operation_key: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> MutationResult[T]:
        kind = _validate_label("Operationsart", operation_kind, 80)
        clean_target = _validate_label("Ziel", target, 160)
        operation_id = f"op-{uuid.uuid4().hex}"
        started_at = _utc_now()
        key_hash = _key_hash(operation_key)
        transitions: list[str] = []
        base_details = details or {}

        def transition(state: MutationState, extra: dict[str, Any] | None = None) -> None:
            transitions.append(state.value)
            merged = dict(base_details)
            if extra:
                merged.update(extra)
            self.journal.append_transition(
                operation_id=operation_id,
                operation_kind=kind,
                target=clean_target,
                state=state.value,
                key_hash=key_hash,
                details=merged,
            )

        transition(MutationState.RECEIVED)
        if key_hash is not None:
            previous = self.journal.find_completed_key(key_hash)
            if previous is not None:
                transition(MutationState.REJECTED, {"reason": "duplicate_operation_key"})
                evidence_path = self._finish(
                    operation_id=operation_id,
                    kind=kind,
                    target=clean_target,
                    state=MutationState.REJECTED,
                    started_at=started_at,
                    key_hash=key_hash,
                    transitions=transitions,
                    details={"reason": "duplicate_operation_key"},
                    error_type="MutationDuplicateError",
                )
                raise MutationDuplicateError(
                    "Diese Änderung wurde mit demselben Vorgangsschlüssel bereits gespeichert.",
                    operation_id=operation_id,
                    evidence_path=evidence_path,
                )

        if not self.gate.acquire():
            transition(MutationState.REJECTED, {"reason": "mutation_gate_busy"})
            evidence_path = self._finish(
                operation_id=operation_id,
                kind=kind,
                target=clean_target,
                state=MutationState.REJECTED,
                started_at=started_at,
                key_hash=key_hash,
                transitions=transitions,
                details={"reason": "mutation_gate_busy"},
                error_type="MutationBusyError",
            )
            raise MutationBusyError(
                "Eine andere Datenänderung läuft bereits. Bitte kurz warten.",
                operation_id=operation_id,
                evidence_path=evidence_path,
            )

        connection: sqlite3.Connection | None = None
        committed = False
        try:
            connection = self.database.connect_raw()
            connection.execute("BEGIN IMMEDIATE")
            transition(MutationState.PRECHECK)
            if precheck is not None:
                precheck(connection)

            transition(MutationState.MUTATION)
            value = mutation(connection)

            transition(MutationState.POSTCHECK)
            if postcheck is not None:
                postcheck(connection, value)

            transition(MutationState.COMMITTING)
            connection.commit()
            committed = True
            committed_transitions = transitions + [MutationState.COMMITTED.value]
            evidence_path = self._finish(
                operation_id=operation_id,
                kind=kind,
                target=clean_target,
                state=MutationState.COMMITTED,
                started_at=started_at,
                key_hash=key_hash,
                transitions=committed_transitions,
                details=base_details,
            )
            transition(MutationState.COMMITTED)
            return MutationResult(
                operation_id=operation_id,
                state=MutationState.COMMITTED,
                value=value,
                evidence_path=evidence_path,
            )
        except Exception as exc:
            if committed:
                raise MutationContractError(
                    "Die Datenänderung wurde gespeichert, aber die Recovery-Evidence "
                    "ist unvollständig oder das Abschlussjournal konnte nicht geschrieben "
                    "werden. Vorgang nicht erneut ausführen; Recovery-Prüfung verwenden.",
                    operation_id=operation_id,
                ) from exc
            if connection is not None:
                transition(MutationState.ROLLING_BACK, {"error": type(exc).__name__})
                try:
                    connection.rollback()
                except sqlite3.Error:
                    transition(MutationState.FAILED, {"reason": "rollback_failed"})
                    final_state = MutationState.FAILED
                else:
                    transition(MutationState.ROLLED_BACK)
                    final_state = MutationState.ROLLED_BACK
            else:
                transition(MutationState.FAILED, {"reason": "connection_failed"})
                final_state = MutationState.FAILED
            self._finish(
                operation_id=operation_id,
                kind=kind,
                target=clean_target,
                state=final_state,
                started_at=started_at,
                key_hash=key_hash,
                transitions=transitions,
                details=base_details,
                error_type=type(exc).__name__,
            )
            raise
        finally:
            if connection is not None:
                connection.close()
            self.gate.release()

    def _finish(
        self,
        *,
        operation_id: str,
        kind: str,
        target: str,
        state: MutationState,
        started_at: str,
        key_hash: str | None,
        transitions: list[str],
        details: dict[str, Any],
        error_type: str | None = None,
    ) -> Path:
        evidence = RecoveryEvidence(
            schema_version=1,
            operation_id=operation_id,
            operation_kind=kind,
            target=target,
            state=state.value,
            started_at=started_at,
            finished_at=_utc_now(),
            key_hash=key_hash,
            transitions=tuple(transitions),
            details=details,
            error_type=error_type,
        )
        return self.journal.write_final(evidence)
