from __future__ import annotations

import math
import os
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from datenbanktool.core.index_types import (
    SCHEMA_VERSION,
    UnsupportedSchemaError,
    normalise_database_path,
)
from datenbanktool.core.presentation import TrafficLight

_MAX_PAGE_SIZE = 200
_VALID_TYPES = frozenset(
    {"grown", "shrunk", "new", "removed", "changed", "unchanged"}
)
_VALID_SORTS = frozenset({"path", "change", "percent", "files", "current-size"})
_TYPE_LABELS = {
    "grown": "Gewachsen",
    "shrunk": "Kleiner geworden",
    "new": "Neu",
    "removed": "Nicht mehr vorhanden",
    "changed": "Dateizahl geändert",
    "unchanged": "Unverändert",
}


@dataclass(frozen=True, slots=True)
class FolderComparisonFilter:
    change_types: tuple[str, ...] = ()
    contains: str = ""
    min_change_bytes: int = 0
    max_depth: int | None = None
    page: int = 1
    page_size: int = 25
    sort_by: str = "change"
    descending: bool = True
    attention_growth_bytes: int = 1024 * 1024 * 1024

    def validate(self) -> None:
        invalid = sorted(set(self.change_types) - _VALID_TYPES)
        if invalid:
            raise ValueError(f"Unbekannte Vergleichsarten: {', '.join(invalid)}")
        if self.min_change_bytes < 0:
            raise ValueError("Mindeständerung darf nicht negativ sein")
        if self.max_depth is not None and self.max_depth < 0:
            raise ValueError("Maximale Ordnertiefe darf nicht negativ sein")
        if self.page < 1:
            raise ValueError("Seite muss mindestens 1 sein")
        if not 1 <= self.page_size <= _MAX_PAGE_SIZE:
            raise ValueError(f"Seitengröße muss zwischen 1 und {_MAX_PAGE_SIZE} liegen")
        if self.sort_by not in _VALID_SORTS:
            raise ValueError(f"Unbekannte Sortierung: {self.sort_by}")
        if self.attention_growth_bytes < 1:
            raise ValueError("Warnschwelle für Wachstum muss mindestens 1 Byte sein")


@dataclass(frozen=True, slots=True)
class FolderComparisonRow:
    folder: str
    depth: int
    change_type: str
    change_label: str
    before_files: int
    after_files: int
    file_delta: int
    before_size_bytes: int
    after_size_bytes: int
    size_delta_bytes: int
    size_delta_percent: float | None
    traffic_level: str
    traffic_label: str
    traffic_reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @property
    def traffic_light(self) -> TrafficLight:
        return TrafficLight(self.traffic_level, self.traffic_label, self.traffic_reason)


@dataclass(frozen=True, slots=True)
class FolderComparisonPage:
    database: str
    from_session_id: int
    to_session_id: int
    root: str
    page: int
    page_size: int
    total_rows: int
    total_pages: int
    counts: dict[str, int]
    rows: tuple[FolderComparisonRow, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rows"] = [row.to_dict() for row in self.rows]
        return payload


@dataclass(slots=True)
class _FolderTotals:
    files: int = 0
    size_bytes: int = 0


def _readonly_connection(path: Path) -> sqlite3.Connection:
    target = normalise_database_path(path)
    if not target.exists():
        raise FileNotFoundError(f"Indexdatenbank nicht gefunden: {target}")
    uri = f"file:{quote(str(target), safe='/')}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    if version > SCHEMA_VERSION:
        connection.close()
        raise UnsupportedSchemaError(
            f"Datenbankschema {version} ist neuer als unterstützte Version {SCHEMA_VERSION}."
        )
    if version < 3:
        connection.close()
        raise ValueError(
            "Ordnervergleich benötigt SQLite-Schema 3. "
            "Öffne den Index einmal mit einem aktuellen DATENBANKTOOL-Befehl."
        )
    return connection


def _complete_session(connection: sqlite3.Connection, session_id: int) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM scan_sessions WHERE id=?",
        (session_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Scan-Sitzung {session_id} wurde nicht gefunden")
    if str(row["status"]) != "complete":
        raise ValueError(f"Scan-Sitzung {session_id} ist nicht abgeschlossen")
    return row


def _target_session(
    connection: sqlite3.Connection,
    session_id: int | None,
) -> sqlite3.Row:
    if session_id is not None:
        return _complete_session(connection, session_id)
    row = connection.execute(
        """
        SELECT target.*
        FROM scan_sessions target
        WHERE target.status='complete'
          AND (
              target.parent_session_id IS NOT NULL
              OR EXISTS(
                  SELECT 1 FROM scan_sessions previous
                  WHERE previous.status='complete'
                    AND previous.root=target.root
                    AND previous.id<target.id
              )
          )
        ORDER BY target.id DESC LIMIT 1
        """
    ).fetchone()
    if row is None:
        raise ValueError("Keine abgeschlossene Ziel-Sitzung mit Vergleichsbasis gefunden")
    return row


def _baseline_session(
    connection: sqlite3.Connection,
    target: sqlite3.Row,
    session_id: int | None,
) -> sqlite3.Row:
    if session_id is not None:
        baseline = _complete_session(connection, session_id)
    elif target["parent_session_id"] is not None:
        baseline = _complete_session(connection, int(target["parent_session_id"]))
    else:
        baseline = connection.execute(
            """
            SELECT * FROM scan_sessions
            WHERE status='complete' AND root=? AND id<?
            ORDER BY id DESC LIMIT 1
            """,
            (str(target["root"]), int(target["id"])),
        ).fetchone()
        if baseline is None:
            raise ValueError(
                "Keine frühere abgeschlossene Sitzung desselben Ordners gefunden"
            )
    if int(baseline["id"]) >= int(target["id"]):
        raise ValueError("Ausgangssitzung muss älter als die Zielsitzung sein")
    if os.path.normpath(str(baseline["root"])) != os.path.normpath(str(target["root"])):
        raise ValueError("Ordnervergleich benötigt zwei Sitzungen desselben Stammordners")
    return baseline


def _folder_path(relative_path: str) -> str:
    parent = PurePosixPath(relative_path).parent.as_posix()
    return "." if parent in {"", "."} else parent


def _ancestors(folder: str) -> tuple[str, ...]:
    if folder == ".":
        return (".",)
    parts = PurePosixPath(folder).parts
    values = ["."]
    for index in range(1, len(parts) + 1):
        values.append(PurePosixPath(*parts[:index]).as_posix())
    return tuple(values)


def _depth(folder: str) -> int:
    return 0 if folder == "." else len(PurePosixPath(folder).parts)


def _aggregate(
    connection: sqlite3.Connection,
    session_id: int,
) -> dict[str, _FolderTotals]:
    totals: dict[str, _FolderTotals] = {".": _FolderTotals()}
    rows = connection.execute(
        """
        SELECT relative_path, size_bytes
        FROM files
        WHERE session_id=?
        ORDER BY relative_path COLLATE NOCASE, relative_path, id
        """,
        (session_id,),
    )
    for row in rows:
        folder = _folder_path(str(row["relative_path"]))
        size = int(row["size_bytes"])
        for ancestor in _ancestors(folder):
            item = totals.setdefault(ancestor, _FolderTotals())
            item.files += 1
            item.size_bytes += size
    return totals


def _classify(before: _FolderTotals, after: _FolderTotals) -> str:
    if before.files == 0 and after.files > 0:
        return "new"
    if before.files > 0 and after.files == 0:
        return "removed"
    size_delta = after.size_bytes - before.size_bytes
    if size_delta > 0:
        return "grown"
    if size_delta < 0:
        return "shrunk"
    if after.files != before.files:
        return "changed"
    return "unchanged"


def _traffic(
    change_type: str,
    *,
    size_delta: int,
    file_delta: int,
    threshold: int,
) -> TrafficLight:
    if change_type == "grown" and size_delta >= threshold:
        return TrafficLight(
            "red",
            "Stark gewachsen",
            "Zunahme überschreitet die gewählte Warnschwelle",
        )
    if change_type == "grown":
        return TrafficLight("yellow", "Gewachsen", "Speicherbedarf ist gestiegen")
    if change_type == "new":
        return TrafficLight("yellow", "Neu", "Ordner erscheint erstmals im Zielscan")
    if change_type == "changed":
        return TrafficLight(
            "yellow",
            "Dateizahl geändert",
            f"Größe gleich, Dateidifferenz {file_delta:+d}",
        )
    if change_type == "shrunk":
        return TrafficLight("green", "Kleiner geworden", "Speicherbedarf ist gesunken")
    if change_type == "removed":
        return TrafficLight(
            "green",
            "Nicht mehr vorhanden",
            "Ordner enthält im Zielscan keine Dateien mehr",
        )
    return TrafficLight("green", "Unverändert", "Größe und Dateizahl sind gleich")


def compare_folders(
    database_path: Path,
    *,
    filters: FolderComparisonFilter = FolderComparisonFilter(),
    from_session_id: int | None = None,
    to_session_id: int | None = None,
) -> FolderComparisonPage:
    filters.validate()
    with closing(_readonly_connection(database_path)) as connection:
        target = _target_session(connection, to_session_id)
        baseline = _baseline_session(connection, target, from_session_id)
        before = _aggregate(connection, int(baseline["id"]))
        after = _aggregate(connection, int(target["id"]))

    counts = {name: 0 for name in sorted(_VALID_TYPES)}
    output: list[FolderComparisonRow] = []
    needle = filters.contains.strip().casefold()
    for folder in sorted(set(before) | set(after), key=lambda value: (value.casefold(), value)):
        old = before.get(folder, _FolderTotals())
        new = after.get(folder, _FolderTotals())
        change_type = _classify(old, new)
        counts[change_type] += 1
        size_delta = new.size_bytes - old.size_bytes
        file_delta = new.files - old.files
        percent = (
            round(size_delta / old.size_bytes * 100.0, 2)
            if old.size_bytes > 0
            else None
        )
        depth = _depth(folder)
        if filters.change_types:
            if change_type not in filters.change_types:
                continue
        elif change_type == "unchanged":
            continue
        if needle and needle not in folder.casefold():
            continue
        if abs(size_delta) < filters.min_change_bytes:
            continue
        if filters.max_depth is not None and depth > filters.max_depth:
            continue
        light = _traffic(
            change_type,
            size_delta=size_delta,
            file_delta=file_delta,
            threshold=filters.attention_growth_bytes,
        )
        output.append(
            FolderComparisonRow(
                folder=folder,
                depth=depth,
                change_type=change_type,
                change_label=_TYPE_LABELS[change_type],
                before_files=old.files,
                after_files=new.files,
                file_delta=file_delta,
                before_size_bytes=old.size_bytes,
                after_size_bytes=new.size_bytes,
                size_delta_bytes=size_delta,
                size_delta_percent=percent,
                traffic_level=light.level,
                traffic_label=light.label,
                traffic_reason=light.reason,
            )
        )

    key = {
        "path": lambda item: (item.folder.casefold(), item.folder),
        "change": lambda item: (
            abs(item.size_delta_bytes),
            item.folder.casefold(),
            item.folder,
        ),
        "percent": lambda item: (
            abs(item.size_delta_percent or 0.0),
            item.folder.casefold(),
            item.folder,
        ),
        "files": lambda item: (
            abs(item.file_delta),
            item.folder.casefold(),
            item.folder,
        ),
        "current-size": lambda item: (
            item.after_size_bytes,
            item.folder.casefold(),
            item.folder,
        ),
    }[filters.sort_by]
    output.sort(key=key, reverse=filters.descending)
    total_rows = len(output)
    total_pages = max(1, math.ceil(total_rows / filters.page_size))
    start = (filters.page - 1) * filters.page_size
    rows = tuple(output[start : start + filters.page_size])
    return FolderComparisonPage(
        database=str(normalise_database_path(database_path)),
        from_session_id=int(baseline["id"]),
        to_session_id=int(target["id"]),
        root=str(target["root"]),
        page=filters.page,
        page_size=filters.page_size,
        total_rows=total_rows,
        total_pages=total_pages,
        counts=counts,
        rows=rows,
    )
