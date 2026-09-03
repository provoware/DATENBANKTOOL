from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.persistence.database import Database


class EntryValidationError(ValueError):
    """Raised when a record does not meet the persistence contract."""


@dataclass(frozen=True)
class Entry:
    id: str
    kind: str
    title: str
    content: str
    parent_id: str | None
    favorite: bool
    status: str
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _validate_text(name: str, value: str, *, maximum: int) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise EntryValidationError(f"{name} darf nicht leer sein.")
    if len(cleaned) > maximum:
        raise EntryValidationError(f"{name} ist länger als {maximum} Zeichen.")
    return cleaned


def _entry_from_row(row: sqlite3.Row) -> Entry:
    metadata = json.loads(str(row["metadata_json"]))
    if not isinstance(metadata, dict):
        metadata = {}
    return Entry(
        id=str(row["id"]),
        kind=str(row["kind"]),
        title=str(row["title"]),
        content=str(row["content"]),
        parent_id=str(row["parent_id"]) if row["parent_id"] is not None else None,
        favorite=bool(row["favorite"]),
        status=str(row["status"]),
        metadata=metadata,
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


class EntryStore:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        *,
        kind: str,
        title: str,
        content: str = "",
        parent_id: str | None = None,
        favorite: bool = False,
        status: str = "active",
        metadata: dict[str, Any] | None = None,
    ) -> Entry:
        clean_kind = _validate_text("Art", kind, maximum=64)
        clean_title = _validate_text("Titel", title, maximum=500)
        clean_status = _validate_text("Status", status, maximum=32)
        if len(content) > 2_000_000:
            raise EntryValidationError("Inhalt ist größer als 2.000.000 Zeichen.")

        try:
            metadata_json = json.dumps(
                metadata or {},
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise EntryValidationError(
                "Metadaten müssen als JSON gespeichert werden können."
            ) from exc

        entry_id = uuid.uuid4().hex
        now = _utc_now()

        with self.database.connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """
                    INSERT INTO entries(
                        id, kind, title, content, parent_id, favorite, status,
                        metadata_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry_id,
                        clean_kind,
                        clean_title,
                        content,
                        parent_id,
                        int(favorite),
                        clean_status,
                        metadata_json,
                        now,
                        now,
                    ),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

        created = self.get(entry_id)
        if created is None:
            raise RuntimeError("Gespeicherter Eintrag konnte nicht wieder gelesen werden.")
        return created

    def get(self, entry_id: str) -> Entry | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM entries WHERE id = ?",
                (entry_id,),
            ).fetchone()
        return _entry_from_row(row) if row else None

    def list(
        self,
        *,
        kind: str | None = None,
        parent_id: str | None = None,
        limit: int = 200,
    ) -> list[Entry]:
        if not 1 <= limit <= 500:
            raise EntryValidationError("Limit muss zwischen 1 und 500 liegen.")

        where: list[str] = []
        params: list[Any] = []
        if kind is not None:
            where.append("kind = ?")
            params.append(_validate_text("Art", kind, maximum=64))
        if parent_id is not None:
            where.append("parent_id = ?")
            params.append(parent_id)

        sql = "SELECT * FROM entries"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY updated_at DESC, title COLLATE NOCASE LIMIT ?"
        params.append(limit)

        with self.database.connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [_entry_from_row(row) for row in rows]
