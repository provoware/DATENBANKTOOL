from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

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


class Database:
    def __init__(
        self,
        path: Path,
        *,
        busy_timeout_ms: int = 5000,
    ) -> None:
        self.path = Path(path)
        self.busy_timeout_ms = busy_timeout_ms

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            self.path,
            timeout=self.busy_timeout_ms / 1000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")
            connection.execute("PRAGMA synchronous = NORMAL")
            connection.execute("PRAGMA journal_mode = WAL")
            yield connection
        finally:
            connection.close()

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
