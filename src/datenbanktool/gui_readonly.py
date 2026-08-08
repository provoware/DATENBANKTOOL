from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GuiSummary:
    database: str
    session_id: int | None
    root: str | None
    status: str | None
    phase: str | None
    file_count: int
    folder_count: int
    total_bytes: int
    duplicate_groups: int
    duplicate_files: int
    duplicate_bytes: int
    warning_count: int
    error_count: int
    unknown_count: int
    large_count: int
    updated_utc: str | None


@dataclass(frozen=True)
class GuiFileRow:
    file_id: int
    relative_path: str
    size_bytes: int
    modified_utc: str
    suffix: str
    category: str
    is_large: bool
    warning_count: int
    duplicate_group_id: int | None


@dataclass(frozen=True)
class CategoryStat:
    category: str
    file_count: int
    total_bytes: int


class ReadOnlyIndexAdapter:
    """Query-only adapter for GUI views.

    The connection uses SQLite ``mode=ro`` plus ``query_only`` and never imports
    the writable ``IndexDatabase`` class. Rendering therefore cannot migrate,
    checkpoint or mutate an index.
    """

    def __init__(self, database: Path) -> None:
        self.database = database.expanduser().resolve(strict=False)

    def _connect(self) -> sqlite3.Connection:
        if not self.database.is_file():
            raise FileNotFoundError(f"Index nicht gefunden: {self.database}")
        connection = sqlite3.connect(
            f"file:{self.database.as_posix()}?mode=ro",
            uri=True,
            timeout=2.0,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA busy_timeout = 2000")
        connection.create_function(
            "parent_path",
            1,
            lambda value: str(Path(str(value)).parent.as_posix()),
            deterministic=True,
        )
        return connection

    @staticmethod
    def _latest_session(connection: sqlite3.Connection) -> sqlite3.Row | None:
        return connection.execute(
            "SELECT * FROM scan_sessions ORDER BY id DESC LIMIT 1"
        ).fetchone()

    def summary(self) -> GuiSummary:
        with self._connect() as connection:
            session = self._latest_session(connection)
            if session is None:
                return GuiSummary(
                    database=str(self.database), session_id=None, root=None,
                    status=None, phase=None, file_count=0, folder_count=0,
                    total_bytes=0, duplicate_groups=0, duplicate_files=0,
                    duplicate_bytes=0, warning_count=0, error_count=0,
                    unknown_count=0, large_count=0, updated_utc=None,
                )
            session_id = int(session["id"])
            totals = connection.execute(
                """
                SELECT COUNT(*) AS file_count,
                       COALESCE(SUM(size_bytes), 0) AS total_bytes,
                       SUM(CASE WHEN category='unknown' THEN 1 ELSE 0 END) AS unknown_count,
                       SUM(CASE WHEN is_large=1 THEN 1 ELSE 0 END) AS large_count
                FROM files WHERE session_id=?
                """,
                (session_id,),
            ).fetchone()
            folder_count = int(
                connection.execute(
                    "SELECT COUNT(DISTINCT parent_path(relative_path)) FROM files WHERE session_id=?",
                    (session_id,),
                ).fetchone()[0]
            )
            duplicate = connection.execute(
                """
                SELECT COUNT(*) AS groups,
                       COALESCE(SUM(member_count), 0) AS members,
                       COALESCE(SUM(size_bytes * CASE WHEN member_count > 1 THEN member_count - 1 ELSE 0 END), 0)
                           AS reclaimable_bytes
                FROM (
                    SELECT dg.id, dg.size_bytes, COUNT(dm.file_id) AS member_count
                    FROM duplicate_groups dg
                    LEFT JOIN duplicate_members dm ON dm.group_id=dg.id
                    WHERE dg.session_id=?
                    GROUP BY dg.id, dg.size_bytes
                )
                """,
                (session_id,),
            ).fetchone()
            warning_count = int(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM filename_warnings fw
                    JOIN files f ON f.id=fw.file_id WHERE f.session_id=?
                    """,
                    (session_id,),
                ).fetchone()[0]
            )
            return GuiSummary(
                database=str(self.database),
                session_id=session_id,
                root=str(session["root"]),
                status=str(session["status"]),
                phase=str(session["phase"]),
                file_count=int(totals["file_count"]),
                folder_count=folder_count,
                total_bytes=int(totals["total_bytes"]),
                duplicate_groups=int(duplicate["groups"]),
                duplicate_files=int(duplicate["members"]),
                duplicate_bytes=int(duplicate["reclaimable_bytes"]),
                warning_count=warning_count,
                error_count=int(session["error_count"]),
                unknown_count=int(totals["unknown_count"] or 0),
                large_count=int(totals["large_count"] or 0),
                updated_utc=str(session["updated_utc"]),
            )

    def categories(self, limit: int = 12) -> tuple[CategoryStat, ...]:
        if limit < 1 or limit > 100:
            raise ValueError("limit muss zwischen 1 und 100 liegen")
        with self._connect() as connection:
            session = self._latest_session(connection)
            if session is None:
                return ()
            rows = connection.execute(
                """
                SELECT category, COUNT(*) AS file_count,
                       COALESCE(SUM(size_bytes), 0) AS total_bytes
                FROM files WHERE session_id=?
                GROUP BY category ORDER BY total_bytes DESC, category ASC LIMIT ?
                """,
                (int(session["id"]), limit),
            )
            return tuple(
                CategoryStat(str(row["category"]), int(row["file_count"]), int(row["total_bytes"]))
                for row in rows
            )

    def files(self, limit: int = 250) -> tuple[GuiFileRow, ...]:
        if limit < 1 or limit > 2000:
            raise ValueError("limit muss zwischen 1 und 2000 liegen")
        with self._connect() as connection:
            session = self._latest_session(connection)
            if session is None:
                return ()
            rows = connection.execute(
                """
                SELECT f.id, f.relative_path, f.size_bytes, f.modified_utc,
                       f.suffix, f.category, f.is_large,
                       COUNT(DISTINCT fw.code) AS warning_count,
                       MIN(dm.group_id) AS duplicate_group_id
                FROM files f
                LEFT JOIN filename_warnings fw ON fw.file_id=f.id
                LEFT JOIN duplicate_members dm ON dm.file_id=f.id
                WHERE f.session_id=?
                GROUP BY f.id
                ORDER BY f.size_bytes DESC, f.relative_path COLLATE NOCASE
                LIMIT ?
                """,
                (int(session["id"]), limit),
            )
            return tuple(
                GuiFileRow(
                    file_id=int(row["id"]),
                    relative_path=str(row["relative_path"]),
                    size_bytes=int(row["size_bytes"]),
                    modified_utc=str(row["modified_utc"]),
                    suffix=str(row["suffix"]),
                    category=str(row["category"]),
                    is_large=bool(row["is_large"]),
                    warning_count=int(row["warning_count"]),
                    duplicate_group_id=(
                        int(row["duplicate_group_id"])
                        if row["duplicate_group_id"] is not None else None
                    ),
                )
                for row in rows
            )
