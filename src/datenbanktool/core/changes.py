from __future__ import annotations

import csv
import html
import json
import math
import os
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator, TextIO
from urllib.parse import quote

from datenbanktool.core.index_types import (
    SCHEMA_VERSION,
    UnsupportedSchemaError,
    normalise_database_path,
)

_VALID_CHANGE_TYPES = frozenset({"added", "modified", "moved", "removed", "unchanged"})
_VALID_CATEGORIES = frozenset(
    {"audio", "video", "image", "text", "archive", "code", "document", "other"}
)
_VALID_SORTS = frozenset({"path", "type", "size", "date"})
_MAX_PAGE_SIZE = 200
_CHANGE_LABELS = {
    "added": "Neu",
    "modified": "Geändert",
    "moved": "Verschoben",
    "removed": "Entfernt",
    "unchanged": "Unverändert",
}


@dataclass(frozen=True, slots=True)
class ChangeFilter:
    change_types: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    contains: str = ""
    page: int = 1
    page_size: int = 25
    sort_by: str = "path"
    descending: bool = False

    def validate(self) -> None:
        invalid_types = sorted(set(self.change_types) - _VALID_CHANGE_TYPES)
        if invalid_types:
            raise ValueError(f"Unbekannte Änderungsarten: {', '.join(invalid_types)}")
        invalid_categories = sorted(set(self.categories) - _VALID_CATEGORIES)
        if invalid_categories:
            raise ValueError(f"Unbekannte Dateitypen: {', '.join(invalid_categories)}")
        if self.page < 1:
            raise ValueError("Seite muss mindestens 1 sein")
        if not 1 <= self.page_size <= _MAX_PAGE_SIZE:
            raise ValueError(f"Seitengröße muss zwischen 1 und {_MAX_PAGE_SIZE} liegen")
        if self.sort_by not in _VALID_SORTS:
            raise ValueError(f"Unbekannte Sortierung: {self.sort_by}")


@dataclass(frozen=True, slots=True)
class ChangeRow:
    change_id: int
    change_type: str
    old_path: str | None
    new_path: str | None
    category: str
    size_bytes: int
    modified_utc: str
    sha256: str | None
    details: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ChangePage:
    database: str
    session_id: int
    baseline_session_id: int
    root: str
    page: int
    page_size: int
    total_rows: int
    total_pages: int
    counts: dict[str, int]
    rows: tuple[ChangeRow, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rows"] = [item.to_dict() for item in self.rows]
        return payload


@dataclass(frozen=True, slots=True)
class ChangeExportResult:
    session_id: int
    row_count: int
    json_path: str | None
    csv_path: str | None
    html_path: str | None


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
            "Änderungsberichte benötigen SQLite-Schema 3. "
            "Öffne den Index einmal mit einem aktuellen DATENBANKTOOL-Befehl."
        )
    return connection


def _select_session(connection: sqlite3.Connection, session_id: int | None) -> sqlite3.Row:
    if session_id is None:
        row = connection.execute(
            """
            SELECT * FROM scan_sessions
            WHERE status='complete' AND scan_mode='incremental'
            ORDER BY id DESC LIMIT 1
            """
        ).fetchone()
    else:
        row = connection.execute("SELECT * FROM scan_sessions WHERE id=?", (session_id,)).fetchone()
    if row is None:
        raise ValueError("Keine abgeschlossene Re-Scan-Sitzung gefunden")
    if str(row["status"]) != "complete" or str(row["scan_mode"]) != "incremental":
        raise ValueError(f"Sitzung {row['id']} ist kein abgeschlossener Re-Scan")
    if row["parent_session_id"] is None:
        raise ValueError(f"Sitzung {row['id']} besitzt keine Baseline")
    return row


def _where(filters: ChangeFilter, session_id: int) -> tuple[str, list[object]]:
    filters.validate()
    clauses = ["c.session_id=?"]
    parameters: list[object] = [session_id]
    if filters.change_types:
        placeholders = ",".join("?" for _ in filters.change_types)
        clauses.append(f"c.change_type IN ({placeholders})")
        parameters.extend(filters.change_types)
    if filters.categories:
        placeholders = ",".join("?" for _ in filters.categories)
        clauses.append(f"COALESCE(newf.category, oldf.category, 'other') IN ({placeholders})")
        parameters.extend(filters.categories)
    if filters.contains.strip():
        escaped = (
            filters.contains.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        pattern = f"%{escaped}%"
        clauses.append(
            "(COALESCE(c.old_path,'') LIKE ? ESCAPE '\\' COLLATE NOCASE OR "
            "COALESCE(c.new_path,'') LIKE ? ESCAPE '\\' COLLATE NOCASE)"
        )
        parameters.extend((pattern, pattern))
    return " AND ".join(clauses), parameters


def _order(filters: ChangeFilter) -> str:
    direction = "DESC" if filters.descending else "ASC"
    expression = {
        "path": "COALESCE(c.new_path,c.old_path,'') COLLATE NOCASE",
        "type": "c.change_type COLLATE NOCASE",
        "size": "COALESCE(newf.size_bytes,oldf.size_bytes,0)",
        "date": "COALESCE(newf.modified_utc,oldf.modified_utc,'')",
    }[filters.sort_by]
    return (
        f"{expression} {direction}, "
        "COALESCE(c.new_path,c.old_path,'') COLLATE NOCASE ASC, c.id ASC"
    )


def _base_select() -> str:
    return """
        SELECT c.id, c.change_type, c.old_path, c.new_path, c.details_json,
               COALESCE(newf.category, oldf.category, 'other') AS category,
               COALESCE(newf.size_bytes, oldf.size_bytes, 0) AS size_bytes,
               COALESCE(newf.modified_utc, oldf.modified_utc, '') AS modified_utc,
               COALESCE(newf.sha256, oldf.sha256) AS sha256
        FROM file_changes c
        LEFT JOIN files oldf ON oldf.id=c.old_file_id
        LEFT JOIN files newf ON newf.id=c.new_file_id
    """


def _row_from_sql(row: sqlite3.Row) -> ChangeRow:
    try:
        details = json.loads(str(row["details_json"]))
    except (json.JSONDecodeError, TypeError):
        details = {"raw": str(row["details_json"])}
    if not isinstance(details, dict):
        details = {"value": details}
    return ChangeRow(
        change_id=int(row["id"]),
        change_type=str(row["change_type"]),
        old_path=str(row["old_path"]) if row["old_path"] is not None else None,
        new_path=str(row["new_path"]) if row["new_path"] is not None else None,
        category=str(row["category"]),
        size_bytes=int(row["size_bytes"]),
        modified_utc=str(row["modified_utc"]),
        sha256=str(row["sha256"]) if row["sha256"] is not None else None,
        details=details,
    )


def _counts(connection: sqlite3.Connection, session_id: int) -> dict[str, int]:
    counts = {name: 0 for name in sorted(_VALID_CHANGE_TYPES)}
    for row in connection.execute(
        "SELECT change_type, COUNT(*) amount FROM file_changes "
        "WHERE session_id=? GROUP BY change_type",
        (session_id,),
    ):
        counts[str(row["change_type"])] = int(row["amount"])
    return counts


def query_changes(
    database_path: Path,
    *,
    filters: ChangeFilter = ChangeFilter(),
    session_id: int | None = None,
) -> ChangePage:
    filters.validate()
    with closing(_readonly_connection(database_path)) as connection:
        session = _select_session(connection, session_id)
        selected_session_id = int(session["id"])
        where, parameters = _where(filters, selected_session_id)
        total_rows = int(
            connection.execute(
                f"SELECT COUNT(*) FROM file_changes c "
                "LEFT JOIN files oldf ON oldf.id=c.old_file_id "
                "LEFT JOIN files newf ON newf.id=c.new_file_id "
                f"WHERE {where}",
                parameters,
            ).fetchone()[0]
        )
        offset = (filters.page - 1) * filters.page_size
        rows = connection.execute(
            _base_select()
            + f" WHERE {where} ORDER BY {_order(filters)} LIMIT ? OFFSET ?",
            [*parameters, filters.page_size, offset],
        ).fetchall()
        return ChangePage(
            database=str(normalise_database_path(database_path)),
            session_id=selected_session_id,
            baseline_session_id=int(session["parent_session_id"]),
            root=str(session["root"]),
            page=filters.page,
            page_size=filters.page_size,
            total_rows=total_rows,
            total_pages=max(1, math.ceil(total_rows / filters.page_size)),
            counts=_counts(connection, selected_session_id),
            rows=tuple(_row_from_sql(row) for row in rows),
        )


def _all_rows(
    connection: sqlite3.Connection,
    filters: ChangeFilter,
    session_id: int,
) -> Iterator[ChangeRow]:
    where, parameters = _where(filters, session_id)
    rows = connection.execute(
        _base_select() + f" WHERE {where} ORDER BY {_order(filters)}", parameters
    )
    for row in rows:
        yield _row_from_sql(row)


def _prepare_target(path: Path, overwrite: bool) -> tuple[Path, Path]:
    target = path.expanduser().resolve(strict=False)
    if target.exists() and not overwrite:
        raise FileExistsError(f"Bericht existiert bereits: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    temporary.unlink(missing_ok=True)
    return target, temporary


def _html_header(
    handle: TextIO,
    session: sqlite3.Row,
    counts: dict[str, int],
    row_count: int,
) -> None:
    cards = "".join(
        f'<div class="card"><strong>{counts[name]}</strong><br>{_CHANGE_LABELS[name]}</div>'
        for name in ("added", "modified", "moved", "removed", "unchanged")
    )
    handle.write(
        f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DATENBANKTOOL – Änderungen</title>
<style>
body {{
  font-family: system-ui, sans-serif;
  margin: 0;
  padding: 1rem;
  line-height: 1.45;
}}
header, .controls {{
  border: 1px solid #777;
  border-radius: .5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}}
.summary {{ display: flex; flex-wrap: wrap; gap: .6rem; }}
.card {{ border: 1px solid #777; border-radius: .4rem; padding: .5rem; min-width: 7rem; }}
.controls {{ display: flex; flex-wrap: wrap; gap: .8rem; align-items: end; }}
label {{ display: grid; gap: .2rem; }}
input, select {{ font: inherit; padding: .45rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #777; padding: .4rem; text-align: left; vertical-align: top; }}
.path {{ overflow-wrap: anywhere; }}
.hidden {{ display: none; }}
</style>
</head>
<body>
<header>
<h1>Änderungen seit dem vorherigen Scan</h1>
<p><strong>Sitzung:</strong> #{int(session['id'])} ·
<strong>Vorheriger Scan:</strong> #{int(session['parent_session_id'])}</p>
<p><strong>Ordner:</strong> {html.escape(str(session['root']))} ·
<strong>Treffer:</strong> {row_count}</p>
<div class="summary">{cards}</div>
</header>
<section class="controls">
<label>Suchen
<input id="search" type="search" placeholder="alter oder neuer Pfad">
</label>
<label>Änderung
<select id="kind">
<option value="">alle</option>
<option value="added">Neu</option>
<option value="modified">Geändert</option>
<option value="moved">Verschoben</option>
<option value="removed">Entfernt</option>
<option value="unchanged">Unverändert</option>
</select>
</label>
<label>Dateityp
<select id="category">
<option value="">alle</option>
<option>audio</option><option>video</option><option>image</option><option>text</option>
<option>archive</option><option>code</option><option>document</option><option>other</option>
</select>
</label>
<strong id="visible"></strong>
</section>
<table>
<thead><tr>
<th>Änderung</th><th>Alter Pfad</th><th>Neuer Pfad</th><th>Typ</th>
<th>Größe</th><th>Geändert UTC</th><th>Details</th>
</tr></thead>
<tbody>"""
    )


def _html_row(handle: TextIO, row: ChangeRow) -> None:
    old_path = row.old_path or ""
    new_path = row.new_path or ""
    search = html.escape(f"{old_path} {new_path}".casefold(), quote=True)
    details = html.escape(json.dumps(row.details, ensure_ascii=False, sort_keys=True))
    handle.write(
        f'<tr data-search="{search}" data-kind="{row.change_type}" data-category="{row.category}">'
        f'<td>{html.escape(_CHANGE_LABELS[row.change_type])}</td>'
        f'<td class="path">{html.escape(old_path)}</td>'
        f'<td class="path">{html.escape(new_path)}</td><td>{html.escape(row.category)}</td>'
        f'<td>{row.size_bytes}</td><td>{html.escape(row.modified_utc)}</td>'
        f'<td class="path">{details}</td></tr>\n'
    )


def _html_footer(handle: TextIO) -> None:
    handle.write(
        """</tbody></table>
<script>
const rows = [...document.querySelectorAll('tbody tr')];
const search = document.querySelector('#search');
const kind = document.querySelector('#kind');
const category = document.querySelector('#category');
const visible = document.querySelector('#visible');
function apply() {
  const query = search.value.trim().toLocaleLowerCase('de');
  let amount = 0;
  for (const row of rows) {
    const show = (!query || row.dataset.search.includes(query))
      && (!kind.value || row.dataset.kind === kind.value)
      && (!category.value || row.dataset.category === category.value);
    row.classList.toggle('hidden', !show);
    if (show) amount++;
  }
  visible.textContent = `${amount} sichtbar`;
}
for (const control of [search, kind, category]) {
  control.addEventListener('input', apply);
}
apply();
</script>
</body>
</html>"""
    )


def export_changes(
    database_path: Path,
    *,
    session_id: int | None = None,
    filters: ChangeFilter = ChangeFilter(page=1, page_size=25),
    json_path: Path | None = None,
    csv_path: Path | None = None,
    html_path: Path | None = None,
    overwrite: bool = False,
) -> ChangeExportResult:
    if json_path is None and csv_path is None and html_path is None:
        raise ValueError("Mindestens JSON, CSV oder HTML muss als Ziel angegeben werden")
    filters.validate()
    prepared: dict[str, tuple[Path, Path]] = {}
    for name, path in (("json", json_path), ("csv", csv_path), ("html", html_path)):
        if path is not None:
            prepared[name] = _prepare_target(path, overwrite)
    targets = [target for target, _ in prepared.values()]
    if len(targets) != len(set(targets)):
        raise ValueError("Jedes Ausgabeformat benötigt eine eigene Zieldatei")
    try:
        with closing(_readonly_connection(database_path)) as connection:
            session = _select_session(connection, session_id)
            selected_session_id = int(session["id"])
            rows = list(_all_rows(connection, filters, selected_session_id))
            counts = _counts(connection, selected_session_id)
            if "json" in prepared:
                _, temporary = prepared["json"]
                payload = {
                    "session_id": selected_session_id,
                    "baseline_session_id": int(session["parent_session_id"]),
                    "root": str(session["root"]),
                    "counts": counts,
                    "row_count": len(rows),
                    "changes": [row.to_dict() for row in rows],
                }
                temporary.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
            if "csv" in prepared:
                _, temporary = prepared["csv"]
                with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
                    writer = csv.writer(handle)
                    writer.writerow(
                        (
                            "change_type", "old_path", "new_path", "category",
                            "size_bytes", "modified_utc", "sha256", "details_json",
                        )
                    )
                    for row in rows:
                        writer.writerow(
                            (
                                row.change_type,
                                row.old_path or "",
                                row.new_path or "",
                                row.category,
                                row.size_bytes,
                                row.modified_utc,
                                row.sha256 or "",
                                json.dumps(
                                    row.details, ensure_ascii=False, sort_keys=True
                                ),
                            )
                        )
            if "html" in prepared:
                _, temporary = prepared["html"]
                with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                    _html_header(handle, session, counts, len(rows))
                    for row in rows:
                        _html_row(handle, row)
                    _html_footer(handle)
        for target, temporary in prepared.values():
            temporary.replace(target)
    except Exception:
        for _, temporary in prepared.values():
            temporary.unlink(missing_ok=True)
        raise
    return ChangeExportResult(
        session_id=selected_session_id,
        row_count=len(rows),
        json_path=str(prepared["json"][0]) if "json" in prepared else None,
        csv_path=str(prepared["csv"][0]) if "csv" in prepared else None,
        html_path=str(prepared["html"][0]) if "html" in prepared else None,
    )
