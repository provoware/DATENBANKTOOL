from __future__ import annotations

import html
import json
import math
import os
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from datenbanktool.core.index_types import (
    SCHEMA_VERSION,
    UnsupportedSchemaError,
    normalise_database_path,
)
from datenbanktool.core.presentation import TrafficLight

_MAX_PAGE_SIZE = 200
_MAX_TOP_FILES = 10
_VALID_SORTS = frozenset({"path", "files", "size", "largest", "warnings", "duplicates"})


@dataclass(frozen=True, slots=True)
class FolderFilter:
    contains: str = ""
    min_files: int = 1
    min_size_bytes: int = 0
    max_depth: int | None = None
    page: int = 1
    page_size: int = 25
    sort_by: str = "size"
    descending: bool = True
    top_files: int = 3
    attention_file_bytes: int = 1024 * 1024 * 1024

    def validate(self) -> None:
        if self.min_files < 1:
            raise ValueError("Mindestanzahl Dateien muss mindestens 1 sein")
        if self.min_size_bytes < 0:
            raise ValueError("Mindestgröße darf nicht negativ sein")
        if self.max_depth is not None and self.max_depth < 0:
            raise ValueError("Maximale Ordnertiefe darf nicht negativ sein")
        if self.page < 1:
            raise ValueError("Seite muss mindestens 1 sein")
        if not 1 <= self.page_size <= _MAX_PAGE_SIZE:
            raise ValueError(f"Seitengröße muss zwischen 1 und {_MAX_PAGE_SIZE} liegen")
        if self.sort_by not in _VALID_SORTS:
            raise ValueError(f"Unbekannte Sortierung: {self.sort_by}")
        if not 1 <= self.top_files <= _MAX_TOP_FILES:
            raise ValueError(f"Anzahl Platzfresser muss zwischen 1 und {_MAX_TOP_FILES} liegen")
        if self.attention_file_bytes < 1:
            raise ValueError("Schwelle für große Dateien muss mindestens 1 Byte sein")


@dataclass(frozen=True, slots=True)
class LargeFile:
    relative_path: str
    size_bytes: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FolderRow:
    folder: str
    depth: int
    direct_files: int
    total_files: int
    direct_size_bytes: int
    total_size_bytes: int
    warning_files: int
    duplicate_files: int
    largest_files: tuple[LargeFile, ...]
    traffic_level: str
    traffic_label: str
    traffic_reason: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["largest_files"] = [item.to_dict() for item in self.largest_files]
        return payload

    @property
    def traffic_light(self) -> TrafficLight:
        return TrafficLight(self.traffic_level, self.traffic_label, self.traffic_reason)


@dataclass(frozen=True, slots=True)
class FolderPage:
    database: str
    session_id: int
    root: str
    page: int
    page_size: int
    total_rows: int
    total_pages: int
    rows: tuple[FolderRow, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rows"] = [item.to_dict() for item in self.rows]
        return payload


@dataclass(slots=True)
class _FolderAccumulator:
    direct_files: int = 0
    total_files: int = 0
    direct_size: int = 0
    total_size: int = 0
    warnings: int = 0
    duplicates: int = 0
    largest: list[LargeFile] = field(default_factory=list)

    def add_largest(self, item: LargeFile, limit: int) -> None:
        self.largest.append(item)
        self.largest.sort(
            key=lambda value: (
                -value.size_bytes,
                value.relative_path.casefold(),
                value.relative_path,
            )
        )
        del self.largest[limit:]


def _readonly_connection(path: Path) -> sqlite3.Connection:
    target = normalise_database_path(path)
    if not target.exists():
        raise FileNotFoundError(f"Indexdatenbank nicht gefunden: {target}")
    uri = f"file:{quote(str(target), safe='/')}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
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
            "SELECT * FROM scan_sessions WHERE id=?",
            (session_id,),
        ).fetchone()
    if row is None:
        raise ValueError("Keine passende abgeschlossene Index-Sitzung gefunden")
    if str(row["status"]) != "complete":
        raise ValueError(f"Sitzung {row['id']} ist nicht abgeschlossen")
    return row


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


def _traffic(accumulator: _FolderAccumulator, threshold: int) -> TrafficLight:
    largest_size = accumulator.largest[0].size_bytes if accumulator.largest else 0
    warning_ratio = (
        accumulator.warnings / accumulator.total_files
        if accumulator.total_files
        else 0.0
    )
    duplicate_ratio = (
        accumulator.duplicates / accumulator.total_files
        if accumulator.total_files
        else 0.0
    )
    concentrated = (
        accumulator.total_size > 0
        and largest_size >= threshold
        and largest_size / accumulator.total_size >= 0.6
    )
    if (
        accumulator.warnings >= 10
        or warning_ratio >= 0.20
        or (accumulator.duplicates >= 5 and duplicate_ratio >= 0.20)
        or largest_size >= threshold * 10
        or concentrated
    ):
        reasons: list[str] = []
        if accumulator.warnings >= 10 or warning_ratio >= 0.20:
            reasons.append("viele auffällige Dateinamen")
        if accumulator.duplicates >= 5 and duplicate_ratio >= 0.20:
            reasons.append("hoher Duplikatanteil")
        if largest_size >= threshold * 10:
            reasons.append("sehr große Einzeldatei")
        if concentrated:
            reasons.append("Speicher stark auf eine Datei konzentriert")
        return TrafficLight("red", "Dringend prüfen", ", ".join(reasons))
    if accumulator.warnings or accumulator.duplicates or largest_size >= threshold:
        reasons = []
        if accumulator.warnings:
            reasons.append(f"{accumulator.warnings} Datei(en) mit Namenshinweis")
        if accumulator.duplicates:
            reasons.append(f"{accumulator.duplicates} Datei(en) in Duplikatgruppen")
        if largest_size >= threshold:
            reasons.append("mindestens eine große Datei")
        return TrafficLight("yellow", "Prüfen", ", ".join(reasons))
    return TrafficLight("green", "Unauffällig", "keine erkannten Auffälligkeiten")


def analyse_folders(
    database_path: Path,
    *,
    filters: FolderFilter = FolderFilter(),
    session_id: int | None = None,
    all_rows: bool = False,
) -> FolderPage:
    filters.validate()
    with closing(_readonly_connection(database_path)) as connection:
        session = _select_session(connection, session_id)
        selected_session_id = int(session["id"])
        accumulators: dict[str, _FolderAccumulator] = {}
        rows = connection.execute(
            """
            SELECT f.id, f.relative_path, f.size_bytes,
                   EXISTS(
                       SELECT 1 FROM filename_warnings w WHERE w.file_id=f.id
                   ) AS has_warning,
                   EXISTS(
                       SELECT 1 FROM duplicate_members dm WHERE dm.file_id=f.id
                   ) AS is_duplicate
            FROM files f
            WHERE f.session_id=?
            ORDER BY f.relative_path COLLATE NOCASE, f.relative_path, f.id
            """,
            (selected_session_id,),
        )
        for row in rows:
            relative_path = str(row["relative_path"])
            size = int(row["size_bytes"])
            direct_folder = _folder_path(relative_path)
            large_file = LargeFile(relative_path, size)
            for folder in _ancestors(direct_folder):
                accumulator = accumulators.setdefault(folder, _FolderAccumulator())
                accumulator.total_files += 1
                accumulator.total_size += size
                accumulator.warnings += int(bool(row["has_warning"]))
                accumulator.duplicates += int(bool(row["is_duplicate"]))
                accumulator.add_largest(large_file, filters.top_files)
            direct = accumulators[direct_folder]
            direct.direct_files += 1
            direct.direct_size += size

        output: list[FolderRow] = []
        needle = filters.contains.casefold().strip()
        for folder, accumulator in accumulators.items():
            depth = _depth(folder)
            if needle and needle not in folder.casefold():
                continue
            if accumulator.total_files < filters.min_files:
                continue
            if accumulator.total_size < filters.min_size_bytes:
                continue
            if filters.max_depth is not None and depth > filters.max_depth:
                continue
            light = _traffic(accumulator, filters.attention_file_bytes)
            output.append(
                FolderRow(
                    folder=folder,
                    depth=depth,
                    direct_files=accumulator.direct_files,
                    total_files=accumulator.total_files,
                    direct_size_bytes=accumulator.direct_size,
                    total_size_bytes=accumulator.total_size,
                    warning_files=accumulator.warnings,
                    duplicate_files=accumulator.duplicates,
                    largest_files=tuple(accumulator.largest),
                    traffic_level=light.level,
                    traffic_label=light.label,
                    traffic_reason=light.reason,
                )
            )

        key = {
            "path": lambda item: (item.folder.casefold(), item.folder),
            "files": lambda item: (
                item.total_files,
                item.folder.casefold(),
                item.folder,
            ),
            "size": lambda item: (
                item.total_size_bytes,
                item.folder.casefold(),
                item.folder,
            ),
            "largest": lambda item: (
                item.largest_files[0].size_bytes if item.largest_files else 0,
                item.folder.casefold(),
                item.folder,
            ),
            "warnings": lambda item: (
                item.warning_files,
                item.folder.casefold(),
                item.folder,
            ),
            "duplicates": lambda item: (
                item.duplicate_files,
                item.folder.casefold(),
                item.folder,
            ),
        }[filters.sort_by]
        output.sort(key=key, reverse=filters.descending)
        total_rows = len(output)
        if all_rows:
            return FolderPage(
                database=str(normalise_database_path(database_path)),
                session_id=selected_session_id,
                root=str(session["root"]),
                page=1,
                page_size=max(1, total_rows),
                total_rows=total_rows,
                total_pages=1,
                rows=tuple(output),
            )
        total_pages = max(1, math.ceil(total_rows / filters.page_size))
        start = (filters.page - 1) * filters.page_size
        selected = tuple(output[start : start + filters.page_size])
        return FolderPage(
            database=str(normalise_database_path(database_path)),
            session_id=selected_session_id,
            root=str(session["root"]),
            page=filters.page,
            page_size=filters.page_size,
            total_rows=total_rows,
            total_pages=total_pages,
            rows=selected,
        )


def paginate_folder_page(
    complete_page: FolderPage,
    *,
    page: int,
    page_size: int,
) -> FolderPage:
    if page < 1:
        raise ValueError("Seite muss mindestens 1 sein")
    if not 1 <= page_size <= _MAX_PAGE_SIZE:
        raise ValueError(f"Seitengröße muss zwischen 1 und {_MAX_PAGE_SIZE} liegen")
    if len(complete_page.rows) != complete_page.total_rows:
        raise ValueError("Pagination benötigt eine vollständige Ordnerauswertung")
    total_pages = max(1, math.ceil(complete_page.total_rows / page_size))
    start = (page - 1) * page_size
    return FolderPage(
        database=complete_page.database,
        session_id=complete_page.session_id,
        root=complete_page.root,
        page=page,
        page_size=page_size,
        total_rows=complete_page.total_rows,
        total_pages=total_pages,
        rows=tuple(complete_page.rows[start : start + page_size]),
    )


def _write_atomic(path: Path, content: str, *, overwrite: bool) -> str:
    target = path.expanduser().resolve(strict=False)
    if target.exists() and not overwrite:
        raise FileExistsError(
            f"Bericht existiert bereits: {target}. Nutze --overwrite-report."
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return str(target)


def export_folder_json(
    page: FolderPage,
    path: Path,
    *,
    overwrite: bool = False,
) -> str:
    return _write_atomic(
        path,
        json.dumps(page.to_dict(), ensure_ascii=False, indent=2) + "\n",
        overwrite=overwrite,
    )


def _human_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{int(value)} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size_bytes} B"


def export_folder_html(
    page: FolderPage,
    path: Path,
    *,
    overwrite: bool = False,
) -> str:
    rows: list[str] = []
    for item in page.rows:
        tooltip = html.escape(
            "Ampel bewertet nur den Prüfbedarf, nicht die Sicherheit der Dateien. "
            + item.traffic_reason,
            quote=True,
        )
        largest = "<br>".join(
            f"<span title=\"{html.escape(file.relative_path, quote=True)}\">"
            f"{html.escape(file.relative_path)} – {_human_size(file.size_bytes)}</span>"
            for file in item.largest_files
        ) or "–"
        rows.append(
            "<tr>"
            f"<td><span class=\"light {item.traffic_level}\" title=\"{tooltip}\" "
            f"aria-label=\"Ampel {html.escape(item.traffic_label)}: "
            f"{html.escape(item.traffic_reason)}\">"
            f"● {html.escape(item.traffic_label)}</span></td>"
            f"<td>{html.escape(item.folder)}</td>"
            f"<td>{item.direct_files}</td><td>{item.total_files}</td>"
            f"<td>{_human_size(item.total_size_bytes)}</td>"
            f"<td>{item.warning_files}</td><td>{item.duplicate_files}</td>"
            f"<td>{largest}</td>"
            "</tr>"
        )
    document = f"""<!doctype html>
<html lang=\"de\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\">
<title>DATENBANKTOOL – Ordnerübersicht</title>
<style>
body{{font-family:system-ui,sans-serif;margin:1.5rem;background:#f6f7f9;color:#15171a}}
h1{{margin-bottom:.3rem}} .hint{{background:#e8f4ff;padding:.8rem;border-radius:.5rem}}
table{{width:100%;border-collapse:collapse;background:white;margin-top:1rem}}
th,td{{padding:.65rem;border:1px solid #d8dde3;text-align:left;vertical-align:top}}
th{{background:#edf1f5;position:sticky;top:0}}
.light{{font-weight:700;display:inline-block;padding:.25rem .45rem;border-radius:.35rem;cursor:help}}
.green{{background:#dff4e4;color:#145c2a}} .yellow{{background:#fff2bf;color:#6b4d00}}
.red{{background:#ffd9d9;color:#7c1515}}
@media(max-width:800px){{table{{font-size:.88rem}}th,td{{padding:.4rem}}}}
</style></head><body>
<h1>Ordnerübersicht</h1>
<p>Scan #{page.session_id} · {html.escape(page.root)} · {page.total_rows} Ordner</p>
<p class=\"hint\" title=\"Die Ampel ist eine verständliche Priorisierungshilfe. Sie verändert keine Dateien.\">ⓘ Mit der Maus über eine Ampel fahren, um die Begründung zu sehen. Farben werden immer zusätzlich mit Text erklärt.</p>
<table><thead><tr><th>Ampel</th><th>Ordner</th><th>Direkt</th><th>Mit Unterordnern</th><th>Gesamtgröße</th><th>Namenshinweise</th><th>Duplikate</th><th>Größte Platzfresser</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></body></html>"""
    return _write_atomic(path, document, overwrite=overwrite)
