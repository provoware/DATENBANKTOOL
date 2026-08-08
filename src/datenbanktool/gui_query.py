from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Literal


SortKey = Literal["path", "size", "date", "category"]


@dataclass(frozen=True)
class QueryFilter:
    category: str | None = None
    suffix: str | None = None
    path_contains: str | None = None
    min_size: int | None = None
    max_size: int | None = None
    warnings_only: bool = False
    duplicates_only: bool = False


@dataclass(frozen=True)
class QueryItem:
    file_id: int
    relative_path: str
    size_bytes: int
    modified_utc: str
    suffix: str
    category: str
    warning_count: int
    duplicate_group_id: int | None


@dataclass(frozen=True)
class QueryPage:
    items: tuple[QueryItem, ...]
    total_count: int
    offset: int
    limit: int
    query_seconds: float

    @property
    def has_previous(self) -> bool:
        return self.offset > 0

    @property
    def has_next(self) -> bool:
        return self.offset + len(self.items) < self.total_count


_SORT_SQL: dict[SortKey, str] = {
    "path": "f.relative_path COLLATE NOCASE ASC, f.id ASC",
    "size": "f.size_bytes DESC, f.relative_path COLLATE NOCASE ASC, f.id ASC",
    "date": "f.modified_utc DESC, f.relative_path COLLATE NOCASE ASC, f.id ASC",
    "category": "f.category ASC, f.relative_path COLLATE NOCASE ASC, f.id ASC",
}


class ReadOnlyQueryService:
    """Paginated GUI query service with whitelisted SQL fragments only."""

    def __init__(self, database: Path) -> None:
        self.database = database.expanduser().resolve(strict=False)

    def _connect(self) -> sqlite3.Connection:
        if not self.database.is_file():
            raise FileNotFoundError(f"Index nicht gefunden: {self.database}")
        connection = sqlite3.connect(
            f"file:{self.database.as_posix()}?mode=ro", uri=True, timeout=2.0
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA busy_timeout = 2000")
        return connection

    @staticmethod
    def _session_id(connection: sqlite3.Connection) -> int | None:
        row = connection.execute(
            "SELECT id FROM scan_sessions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return int(row[0]) if row is not None else None

    @staticmethod
    def _where(filters: QueryFilter, session_id: int) -> tuple[str, list[object]]:
        clauses = ["f.session_id=?"]
        parameters: list[object] = [session_id]
        if filters.category:
            clauses.append("f.category=?")
            parameters.append(filters.category)
        if filters.suffix:
            suffix = filters.suffix if filters.suffix.startswith(".") else f".{filters.suffix}"
            clauses.append("f.suffix=?")
            parameters.append(suffix.casefold())
        if filters.path_contains:
            clauses.append("f.relative_path LIKE ? ESCAPE '\\'")
            escaped = (
                filters.path_contains.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            parameters.append(f"%{escaped}%")
        if filters.min_size is not None:
            if filters.min_size < 0:
                raise ValueError("min_size darf nicht negativ sein")
            clauses.append("f.size_bytes>=?")
            parameters.append(filters.min_size)
        if filters.max_size is not None:
            if filters.max_size < 0:
                raise ValueError("max_size darf nicht negativ sein")
            clauses.append("f.size_bytes<=?")
            parameters.append(filters.max_size)
        if filters.min_size is not None and filters.max_size is not None:
            if filters.min_size > filters.max_size:
                raise ValueError("min_size darf nicht größer als max_size sein")
        if filters.warnings_only:
            clauses.append("EXISTS (SELECT 1 FROM filename_warnings fw2 WHERE fw2.file_id=f.id)")
        if filters.duplicates_only:
            clauses.append("EXISTS (SELECT 1 FROM duplicate_members dm2 WHERE dm2.file_id=f.id)")
        return " AND ".join(clauses), parameters

    def page(
        self,
        filters: QueryFilter = QueryFilter(),
        *,
        offset: int = 0,
        limit: int = 100,
        sort: SortKey = "size",
    ) -> QueryPage:
        if offset < 0:
            raise ValueError("offset darf nicht negativ sein")
        if limit < 1 or limit > 500:
            raise ValueError("limit muss zwischen 1 und 500 liegen")
        order_sql = _SORT_SQL[sort]
        started = perf_counter()
        with self._connect() as connection:
            session_id = self._session_id(connection)
            if session_id is None:
                return QueryPage((), 0, offset, limit, perf_counter() - started)
            where_sql, parameters = self._where(filters, session_id)
            total_count = int(
                connection.execute(
                    f"SELECT COUNT(*) FROM files f WHERE {where_sql}", parameters
                ).fetchone()[0]
            )
            rows = connection.execute(
                f"""
                SELECT f.id, f.relative_path, f.size_bytes, f.modified_utc,
                       f.suffix, f.category,
                       (SELECT COUNT(*) FROM filename_warnings fw WHERE fw.file_id=f.id) AS warning_count,
                       (SELECT MIN(dm.group_id) FROM duplicate_members dm WHERE dm.file_id=f.id) AS duplicate_group_id
                FROM files f
                WHERE {where_sql}
                ORDER BY {order_sql}
                LIMIT ? OFFSET ?
                """,
                [*parameters, limit, offset],
            )
            items = tuple(
                QueryItem(
                    file_id=int(row["id"]),
                    relative_path=str(row["relative_path"]),
                    size_bytes=int(row["size_bytes"]),
                    modified_utc=str(row["modified_utc"]),
                    suffix=str(row["suffix"]),
                    category=str(row["category"]),
                    warning_count=int(row["warning_count"]),
                    duplicate_group_id=(
                        int(row["duplicate_group_id"])
                        if row["duplicate_group_id"] is not None else None
                    ),
                )
                for row in rows
            )
        return QueryPage(items, total_count, offset, limit, perf_counter() - started)
