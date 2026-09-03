from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from src.persistence.migrations import (
    CURRENT_SCHEMA_VERSION,
    MigrationReport,
    run_migrations,
)


@dataclass(frozen=True)
class SchemaStatus:
    path: str
    current_version: int
    target_version: int
    ready: bool
    exists: bool
    size_bytes: int
    journal_mode: str | None


@dataclass(frozen=True)
class IntegrityReport:
    ok: bool
    quick_check: tuple[str, ...]
    foreign_key_violations: int


class _GuardedConnection(sqlite3.Connection):
    _access_gate: threading.RLock | None = None
    _gate_released = False

    def close(self) -> None:
        if self._gate_released:
            return
        try:
            super().close()
        finally:
            self._gate_released = True
            if self._access_gate is not None:
                self._access_gate.release()


class Database:
    _registry_guard = threading.Lock()
    _access_gates: dict[str, threading.RLock] = {}

    def __init__(
        self,
        path: Path,
        *,
        busy_timeout_ms: int = 5000,
    ) -> None:
        self.path = Path(path)
        self.busy_timeout_ms = busy_timeout_ms
        key = str(self.path.resolve())
        with self._registry_guard:
            self._access_gate = self._access_gates.setdefault(key, threading.RLock())

    def connect_raw(self) -> sqlite3.Connection:
        """Open a configured connection whose transaction lifecycle is caller-owned."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._access_gate.acquire()
        try:
            connection = sqlite3.connect(
                self.path,
                timeout=self.busy_timeout_ms / 1000,
                isolation_level=None,
                factory=_GuardedConnection,
            )
        except Exception:
            self._access_gate.release()
            raise
        connection._access_gate = self._access_gate
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect_raw()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def exclusive_access(self) -> Iterator[None]:
        """Block all other process-local database connections for a critical file swap."""
        self._access_gate.acquire()
        try:
            yield
        finally:
            self._access_gate.release()

    def initialize(self) -> MigrationReport:
        with self.connect() as connection:
            return run_migrations(connection)

    def schema_status(self) -> SchemaStatus:
        if not self.path.exists():
            return SchemaStatus(
                path=str(self.path),
                current_version=0,
                target_version=CURRENT_SCHEMA_VERSION,
                ready=False,
                exists=False,
                size_bytes=0,
                journal_mode=None,
            )

        with self.connect() as connection:
            current = int(connection.execute("PRAGMA user_version").fetchone()[0])
            journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0])

        return SchemaStatus(
            path=str(self.path),
            current_version=current,
            target_version=CURRENT_SCHEMA_VERSION,
            ready=current == CURRENT_SCHEMA_VERSION,
            exists=True,
            size_bytes=self.path.stat().st_size,
            journal_mode=journal_mode,
        )

    def integrity_check(self) -> IntegrityReport:
        with self.connect() as connection:
            quick_rows = connection.execute("PRAGMA quick_check").fetchall()
            fk_rows = connection.execute("PRAGMA foreign_key_check").fetchall()

        quick = tuple(str(row[0]) for row in quick_rows)
        return IntegrityReport(
            ok=quick == ("ok",) and not fk_rows,
            quick_check=quick,
            foreign_key_violations=len(fk_rows),
        )
