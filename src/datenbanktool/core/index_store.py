from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from datenbanktool.core.index_records import IndexRecordMixin
from datenbanktool.core.index_schema import migrate_connection
from datenbanktool.core.index_types import (
    IndexErrorBase,
    IndexStatus,
    VALID_PHASES,
    normalise_database_path,
    utc_now,
)
from datenbanktool.core.progress import ProgressEvent


class IndexDatabase(IndexRecordMixin):
    def __init__(self, path: Path) -> None:
        self.path = normalise_database_path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 5000")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = FULL")
        self.connection.execute("PRAGMA wal_autocheckpoint = 1000")

    def __enter__(self) -> "IndexDatabase":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _passive_checkpoint(self) -> bool:
        """Try WAL housekeeping without turning a safe commit into a command error."""
        try:
            self.connection.execute("PRAGMA wal_checkpoint(PASSIVE)")
        except sqlite3.OperationalError as error:
            detail = str(error).casefold()
            if "locked" in detail or "busy" in detail:
                return False
            raise
        return True

    def close(self) -> None:
        try:
            self.connection.commit()
            self._passive_checkpoint()
        except sqlite3.Error:
            # Closing must not hide the original command error. The committed WAL stays valid.
            pass
        finally:
            self.connection.close()

    def durable_checkpoint(self) -> bool:
        """Commit durably; return whether optional WAL housekeeping also succeeded."""
        self.connection.commit()
        return self._passive_checkpoint()

    def schema_version(self) -> int:
        return int(self.connection.execute("PRAGMA user_version").fetchone()[0])

    def migrate(self) -> int:
        return migrate_connection(self.connection)

    def create_session(
        self,
        root: Path,
        options_payload: dict[str, object],
        fingerprint: str,
        *,
        scan_mode: str = "full",
        parent_session_id: int | None = None,
    ) -> int:
        now = utc_now()
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO scan_sessions(
                    root, options_json, status, phase, started_utc, updated_utc,
                    source_fingerprint, parent_session_id, scan_mode
                ) VALUES (?, ?, 'running', 'scanning', ?, ?, ?, ?, ?)
                """,
                (
                    str(root),
                    json.dumps(options_payload, sort_keys=True),
                    now,
                    now,
                    fingerprint,
                    parent_session_id,
                    scan_mode,
                ),
            )
        return int(cursor.lastrowid)

    def resumable_session(self, fingerprint: str, scan_mode: str = "full") -> sqlite3.Row | None:
        return self.connection.execute(
            """
            SELECT * FROM scan_sessions
            WHERE source_fingerprint=? AND scan_mode=?
              AND status IN ('running','interrupted','failed')
            ORDER BY id DESC LIMIT 1
            """,
            (fingerprint, scan_mode),
        ).fetchone()

    def session(self, session_id: int) -> sqlite3.Row:
        row = self.connection.execute("SELECT * FROM scan_sessions WHERE id=?", (session_id,)).fetchone()
        if row is None:
            raise IndexErrorBase(f"Der gespeicherte Scan #{session_id} wurde nicht gefunden.")
        return row

    def latest_complete_session(
        self, root: Path, *, exclude_session_id: int | None = None
    ) -> sqlite3.Row | None:
        query = "SELECT * FROM scan_sessions WHERE root=? AND status='complete'"
        parameters: list[object] = [str(root)]
        if exclude_session_id is not None:
            query += " AND id<>?"
            parameters.append(exclude_session_id)
        query += " ORDER BY id DESC LIMIT 1"
        return self.connection.execute(query, parameters).fetchone()

    def set_running(self, session_id: int) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE scan_sessions SET status='running', updated_utc=?, truncated=0 WHERE id=?",
                (utc_now(), session_id),
            )

    def set_phase(self, session_id: int, phase: str) -> None:
        if phase not in VALID_PHASES:
            raise ValueError(f"Unbekannter Arbeitsabschnitt. (Technisch: Indexphase {phase}.)")
        with self.connection:
            self.connection.execute(
                "UPDATE scan_sessions SET phase=?, updated_utc=? WHERE id=?",
                (phase, utc_now(), session_id),
            )

    def set_incremental_stage(self, session_id: int, stage: str, *, phase: str) -> None:
        if phase not in VALID_PHASES:
            raise ValueError(f"Unbekannter Arbeitsabschnitt. (Technisch: Indexphase {phase}.)")
        with self.connection:
            self.connection.execute(
                "UPDATE scan_sessions SET incremental_stage=?, phase=?, updated_utc=? WHERE id=?",
                (stage, phase, utc_now(), session_id),
            )

    def mark_interrupted(self, session_id: int, truncated: bool = False) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE scan_sessions SET status='interrupted', truncated=?, updated_utc=? WHERE id=?",
                (int(truncated), utc_now(), session_id),
            )
        self.durable_checkpoint()

    def mark_failed(self, session_id: int, message: str) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO scan_errors(session_id, path, operation, message) VALUES (?, '', 'index', ?)",
                (session_id, message),
            )
            self.connection.execute(
                """
                UPDATE scan_sessions
                SET status='failed', error_count=(SELECT COUNT(*) FROM scan_errors WHERE session_id=?),
                    updated_utc=? WHERE id=?
                """,
                (session_id, utc_now(), session_id),
            )
        self.durable_checkpoint()

    def mark_complete(self, session_id: int) -> None:
        now = utc_now()
        with self.connection:
            self.connection.execute(
                """
                UPDATE scan_sessions
                SET status='complete', phase='complete', finished_utc=?, updated_utc=?, truncated=0
                WHERE id=?
                """,
                (now, now, session_id),
            )
        self.durable_checkpoint()

    def latest_status(self) -> IndexStatus:
        row = self.connection.execute("SELECT * FROM scan_sessions ORDER BY id DESC LIMIT 1").fetchone()
        if row is None:
            return IndexStatus(
                database=str(self.path), schema_version=self.schema_version(), session_id=None,
                root=None, status=None, phase=None, imported_count=0, error_count=0,
                duplicate_group_count=0, updated_utc=None,
            )
        duplicate_count = int(
            self.connection.execute(
                "SELECT COUNT(*) FROM duplicate_groups WHERE session_id=?", (row["id"],)
            ).fetchone()[0]
        )
        return IndexStatus(
            database=str(self.path),
            schema_version=self.schema_version(),
            session_id=int(row["id"]),
            root=str(row["root"]),
            status=str(row["status"]),
            phase=str(row["phase"]),
            imported_count=int(row["imported_count"]),
            error_count=int(row["error_count"]),
            duplicate_group_count=duplicate_count,
            updated_utc=str(row["updated_utc"]),
            scan_mode=str(row["scan_mode"]),
            parent_session_id=(
                int(row["parent_session_id"]) if row["parent_session_id"] is not None else None
            ),
        )

    def add_progress_event(self, event: ProgressEvent) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO progress_events(
                    session_id, event_utc, phase, kind, current_value, total_value, message, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.session_id,
                    utc_now(),
                    event.phase,
                    event.kind,
                    event.current,
                    event.total,
                    event.message,
                    json.dumps(event.details, ensure_ascii=False, sort_keys=True),
                ),
            )

    def change_counts(self, session_id: int) -> dict[str, int]:
        counts = {name: 0 for name in ("added", "modified", "moved", "removed", "unchanged")}
        for row in self.connection.execute(
            "SELECT change_type, COUNT(*) AS amount FROM file_changes WHERE session_id=? GROUP BY change_type",
            (session_id,),
        ):
            counts[str(row["change_type"])] = int(row["amount"])
        return counts
