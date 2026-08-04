from __future__ import annotations

import json
import math
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import quote

from datenbanktool.core.index_lock import IndexProcessLock
from datenbanktool.core.index_types import (
    SCHEMA_VERSION,
    IndexErrorBase,
    UnsupportedSchemaError,
    normalise_database_path,
)

_VALID_CATEGORIES = frozenset(
    {"audio", "video", "image", "text", "archive", "code", "document", "other"}
)
_VALID_SORTS = frozenset({"path", "size", "date", "type", "relevance"})
_VALID_FULLTEXT_MODES = frozenset({"auto", "off", "required"})
_MAX_PAGE_SIZE = 200


class FullTextUnavailableError(IndexErrorBase):
    """Raised when FTS5 was explicitly required but is unavailable."""


@dataclass(frozen=True, slots=True)
class SearchFilter:
    text: str = ""
    categories: tuple[str, ...] = ()
    min_size_bytes: int | None = None
    max_size_bytes: int | None = None
    naming_warning_only: bool = False
    duplicate_only: bool = False
    page: int = 1
    page_size: int = 25
    sort_by: str = "path"
    descending: bool = False
    fulltext_mode: str = "auto"

    def validate(self) -> None:
        invalid = sorted(set(self.categories) - _VALID_CATEGORIES)
        if invalid:
            raise ValueError(f"Unbekannte Dateitypen: {', '.join(invalid)}")
        if self.min_size_bytes is not None and self.min_size_bytes < 0:
            raise ValueError("Mindestgröße darf nicht negativ sein")
        if self.max_size_bytes is not None and self.max_size_bytes < 0:
            raise ValueError("Maximalgröße darf nicht negativ sein")
        if (
            self.min_size_bytes is not None
            and self.max_size_bytes is not None
            and self.min_size_bytes > self.max_size_bytes
        ):
            raise ValueError("Mindestgröße darf nicht größer als Maximalgröße sein")
        if self.page < 1:
            raise ValueError("Seite muss mindestens 1 sein")
        if not 1 <= self.page_size <= _MAX_PAGE_SIZE:
            raise ValueError(f"Seitengröße muss zwischen 1 und {_MAX_PAGE_SIZE} liegen")
        if self.sort_by not in _VALID_SORTS:
            raise ValueError(f"Unbekannte Sortierung: {self.sort_by}")
        if self.fulltext_mode not in _VALID_FULLTEXT_MODES:
            raise ValueError(f"Unbekannter Volltextmodus: {self.fulltext_mode}")


@dataclass(frozen=True, slots=True)
class SearchRow:
    file_id: int
    relative_path: str
    category: str
    suffix: str
    size_bytes: int
    modified_utc: str
    is_large: bool
    filename_warnings: tuple[str, ...]
    duplicate_sha256: str | None
    sha256: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SearchPage:
    database: str
    session_id: int
    root: str
    engine: str
    query: str
    page: int
    page_size: int
    total_rows: int
    total_pages: int
    rows: tuple[SearchRow, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rows"] = [item.to_dict() for item in self.rows]
        return payload


@dataclass(frozen=True, slots=True)
class FullTextBuildResult:
    database: str
    session_id: int
    indexed_files: int
    fts5_available: bool


def _readonly_connection(path: Path) -> sqlite3.Connection:
    target = normalise_database_path(path)
    if not target.exists():
        raise FileNotFoundError(f"Indexdatenbank nicht gefunden: {target}")
    uri = f"file:{quote(str(target), safe='/')}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA foreign_keys = ON")
    version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    if version > SCHEMA_VERSION:
        connection.close()
        raise UnsupportedSchemaError(
            f"Datenbankschema {version} ist neuer als unterstützte Version {SCHEMA_VERSION}."
        )
    return connection


def _select_session(connection: sqlite3.Connection, session_id: int | None) -> sqlite3.Row:
    if session_id is None:
        row = connection.execute(
            "SELECT * FROM scan_sessions WHERE status='complete' ORDER BY id DESC LIMIT 1"
        ).fetchone()
    else:
        row = connection.execute(
            "SELECT * FROM scan_sessions WHERE id=?", (session_id,)
        ).fetchone()
    if row is None:
        raise ValueError("Keine passende abgeschlossene Index-Sitzung gefunden")
    if str(row["status"]) != "complete":
        raise ValueError(f"Sitzung {row['id']} ist nicht abgeschlossen")
    return row


def _fts_table_exists(connection: sqlite3.Connection, session_id: int) -> bool:
    table = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='file_search_fts'"
    ).fetchone()
    if table is None:
        return False
    return connection.execute(
        "SELECT 1 FROM file_search_fts WHERE session_id=? LIMIT 1", (session_id,)
    ).fetchone() is not None


def _fts_query(text: str) -> str:
    terms = [term for term in text.split() if term]
    return " AND ".join(f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms)


def _like_pattern(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _build_where(
    filters: SearchFilter,
    session_id: int,
    *,
    use_fts: bool,
) -> tuple[str, list[object]]:
    clauses = ["f.session_id=?"]
    parameters: list[object] = [session_id]
    if filters.text.strip():
        if use_fts:
            clauses.append("file_search_fts MATCH ?")
            parameters.append(_fts_query(filters.text.strip()))
        else:
            for term in filters.text.split():
                pattern = _like_pattern(term)
                clauses.append(
                    "("
                    "f.relative_path LIKE ? ESCAPE '\\' COLLATE NOCASE OR "
                    "f.suffix LIKE ? ESCAPE '\\' COLLATE NOCASE OR "
                    "f.category LIKE ? ESCAPE '\\' COLLATE NOCASE OR "
                    "EXISTS (SELECT 1 FROM filename_warnings sw "
                    "WHERE sw.file_id=f.id AND sw.code LIKE ? ESCAPE '\\' COLLATE NOCASE)"
                    ")"
                )
                parameters.extend((pattern, pattern, pattern, pattern))
    if filters.categories:
        placeholders = ",".join("?" for _ in filters.categories)
        clauses.append(f"f.category IN ({placeholders})")
        parameters.extend(filters.categories)
    if filters.min_size_bytes is not None:
        clauses.append("f.size_bytes>=?")
        parameters.append(filters.min_size_bytes)
    if filters.max_size_bytes is not None:
        clauses.append("f.size_bytes<=?")
        parameters.append(filters.max_size_bytes)
    if filters.naming_warning_only:
        clauses.append("EXISTS (SELECT 1 FROM filename_warnings w WHERE w.file_id=f.id)")
    if filters.duplicate_only:
        clauses.append("EXISTS (SELECT 1 FROM duplicate_members dm WHERE dm.file_id=f.id)")
    return " AND ".join(clauses), parameters


def _order_clause(filters: SearchFilter, *, use_fts: bool) -> str:
    if filters.sort_by == "relevance":
        if not use_fts or not filters.text.strip():
            raise ValueError("Sortierung nach Treffergenauigkeit benötigt eine FTS5-Suche")
        return (
            "bm25(file_search_fts) ASC, "
            "f.relative_path COLLATE NOCASE ASC, f.relative_path ASC, f.id ASC"
        )
    direction = "DESC" if filters.descending else "ASC"
    expression = {
        "path": "f.relative_path COLLATE NOCASE",
        "size": "f.size_bytes",
        "date": "f.modified_utc",
        "type": "f.category COLLATE NOCASE",
    }[filters.sort_by]
    return (
        f"{expression} {direction}, "
        "f.relative_path COLLATE NOCASE ASC, f.relative_path ASC, f.id ASC"
    )


def search_index(
    database_path: Path,
    *,
    filters: SearchFilter = SearchFilter(),
    session_id: int | None = None,
) -> SearchPage:
    filters.validate()
    with closing(_readonly_connection(database_path)) as connection:
        session = _select_session(connection, session_id)
        selected_session_id = int(session["id"])
        fts_ready = _fts_table_exists(connection, selected_session_id)
        use_fts = bool(filters.text.strip()) and filters.fulltext_mode != "off" and fts_ready
        if filters.fulltext_mode == "required" and filters.text.strip() and not fts_ready:
            raise FullTextUnavailableError(
                "Für diese Sitzung wurde noch kein FTS5-Suchindex aufgebaut. "
                "Nutze --build-fulltext-index."
            )
        join = (
            "JOIN file_search_fts ON file_search_fts.file_id=f.id "
            "AND file_search_fts.session_id=f.session_id"
            if use_fts
            else ""
        )
        where, parameters = _build_where(filters, selected_session_id, use_fts=use_fts)
        total_rows = int(
            connection.execute(
                f"SELECT COUNT(*) FROM files f {join} WHERE {where}", parameters
            ).fetchone()[0]
        )
        total_pages = max(1, math.ceil(total_rows / filters.page_size))
        offset = (filters.page - 1) * filters.page_size
        rows = connection.execute(
            f"""
            SELECT f.id, f.relative_path, f.category, f.suffix, f.size_bytes,
                   f.modified_utc, f.is_large, f.sha256,
                   COALESCE((SELECT GROUP_CONCAT(w.code, '|') FROM filename_warnings w
                             WHERE w.file_id=f.id), '') AS warnings,
                   (SELECT dg.sha256 FROM duplicate_members dm
                    JOIN duplicate_groups dg ON dg.id=dm.group_id
                    WHERE dm.file_id=f.id ORDER BY dg.id LIMIT 1) AS duplicate_sha256
            FROM files f
            {join}
            WHERE {where}
            ORDER BY {_order_clause(filters, use_fts=use_fts)}
            LIMIT ? OFFSET ?
            """,
            [*parameters, filters.page_size, offset],
        ).fetchall()
        results = tuple(
            SearchRow(
                file_id=int(row["id"]),
                relative_path=str(row["relative_path"]),
                category=str(row["category"]),
                suffix=str(row["suffix"]),
                size_bytes=int(row["size_bytes"]),
                modified_utc=str(row["modified_utc"]),
                is_large=bool(row["is_large"]),
                filename_warnings=tuple(filter(None, str(row["warnings"]).split("|"))),
                duplicate_sha256=(
                    str(row["duplicate_sha256"])
                    if row["duplicate_sha256"] is not None
                    else None
                ),
                sha256=str(row["sha256"]) if row["sha256"] is not None else None,
            )
            for row in rows
        )
        return SearchPage(
            database=str(normalise_database_path(database_path)),
            session_id=selected_session_id,
            root=str(session["root"]),
            engine="fts5" if use_fts else "like",
            query=filters.text,
            page=filters.page,
            page_size=filters.page_size,
            total_rows=total_rows,
            total_pages=total_pages,
            rows=results,
        )


def build_fulltext_index(
    database_path: Path,
    *,
    session_id: int | None = None,
    lock_timeout_seconds: float = 0.0,
) -> FullTextBuildResult:
    target = normalise_database_path(database_path)
    if not target.exists():
        raise FileNotFoundError(f"Indexdatenbank nicht gefunden: {target}")
    with IndexProcessLock(target, "index search --build-fulltext-index", lock_timeout_seconds):
        connection = sqlite3.connect(target)
        connection.row_factory = sqlite3.Row
        try:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if version > SCHEMA_VERSION:
                raise UnsupportedSchemaError(
                    f"Datenbankschema {version} ist neuer als unterstützte "
                    f"Version {SCHEMA_VERSION}."
                )
            session = _select_session(connection, session_id)
            selected_session_id = int(session["id"])
            try:
                with connection:
                    connection.execute(
                        """
                        CREATE VIRTUAL TABLE IF NOT EXISTS file_search_fts USING fts5(
                            session_id UNINDEXED,
                            file_id UNINDEXED,
                            relative_path,
                            suffix,
                            category,
                            warning_text,
                            tokenize='unicode61 remove_diacritics 2'
                        )
                        """
                    )
                    connection.execute(
                        "DELETE FROM file_search_fts WHERE session_id=?",
                        (selected_session_id,),
                    )
                    connection.execute(
                        """
                        INSERT INTO file_search_fts(
                            session_id, file_id, relative_path, suffix, category, warning_text
                        )
                        SELECT f.session_id, f.id, f.relative_path, f.suffix, f.category,
                               COALESCE((SELECT GROUP_CONCAT(w.code, ' ') FROM filename_warnings w
                                         WHERE w.file_id=f.id), '')
                        FROM files f WHERE f.session_id=?
                        ORDER BY f.id
                        """,
                        (selected_session_id,),
                    )
                    connection.execute(
                        "INSERT INTO file_search_fts(file_search_fts) VALUES('optimize')"
                    )
            except sqlite3.OperationalError as error:
                if "fts5" in str(error).casefold() or "no such module" in str(error).casefold():
                    raise FullTextUnavailableError(
                        "Diese Python-/SQLite-Installation unterstützt FTS5 nicht. "
                        "Die normale Suche bleibt verfügbar."
                    ) from error
                raise
            indexed = int(
                connection.execute(
                    "SELECT COUNT(*) FROM file_search_fts WHERE session_id=?",
                    (selected_session_id,),
                ).fetchone()[0]
            )
        finally:
            connection.close()
    return FullTextBuildResult(
        database=str(target),
        session_id=selected_session_id,
        indexed_files=indexed,
        fts5_available=True,
    )
