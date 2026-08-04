from __future__ import annotations

import csv
import html
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, TextIO

from datenbanktool.core.index_database import IndexDatabase
from datenbanktool.core.models import FileCategory


@dataclass(frozen=True, slots=True)
class ReportFilter:
    categories: tuple[str, ...] = ()
    min_size_bytes: int | None = None
    max_size_bytes: int | None = None
    naming_warning_only: bool = False
    duplicate_only: bool = False

    def validate(self) -> None:
        valid_categories = {category.value for category in FileCategory}
        invalid = sorted(set(self.categories) - valid_categories)
        if invalid:
            raise ValueError(f"Unbekannte Dateikategorie(n): {', '.join(invalid)}")
        if self.min_size_bytes is not None and self.min_size_bytes < 0:
            raise ValueError("min_size_bytes darf nicht negativ sein")
        if self.max_size_bytes is not None and self.max_size_bytes < 0:
            raise ValueError("max_size_bytes darf nicht negativ sein")
        if (
            self.min_size_bytes is not None
            and self.max_size_bytes is not None
            and self.min_size_bytes > self.max_size_bytes
        ):
            raise ValueError("min_size_bytes darf nicht größer als max_size_bytes sein")


@dataclass(frozen=True, slots=True)
class ReportResult:
    session_id: int
    row_count: int
    total_size_bytes: int
    csv_path: str | None
    html_path: str | None


_COLUMNS = (
    "relative_path",
    "category",
    "suffix",
    "size_bytes",
    "modified_utc",
    "is_large",
    "is_symlink",
    "filename_warnings",
    "duplicate_sha256",
)


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
        raise ValueError(
            f"Sitzung {row['id']} ist nicht abgeschlossen (Status: {row['status']})"
        )
    return row


def _where_clause(filters: ReportFilter) -> tuple[str, list[object]]:
    filters.validate()
    clauses = ["f.session_id = ?"]
    parameters: list[object] = []
    if filters.categories:
        placeholders = ", ".join("?" for _ in filters.categories)
        clauses.append(f"f.category IN ({placeholders})")
        parameters.extend(filters.categories)
    if filters.min_size_bytes is not None:
        clauses.append("f.size_bytes >= ?")
        parameters.append(filters.min_size_bytes)
    if filters.max_size_bytes is not None:
        clauses.append("f.size_bytes <= ?")
        parameters.append(filters.max_size_bytes)
    if filters.naming_warning_only:
        clauses.append("EXISTS (SELECT 1 FROM filename_warnings w WHERE w.file_id=f.id)")
    if filters.duplicate_only:
        clauses.append("EXISTS (SELECT 1 FROM duplicate_members dm WHERE dm.file_id=f.id)")
    return " AND ".join(clauses), parameters


def _iter_rows(
    connection: sqlite3.Connection, session_id: int, filters: ReportFilter
) -> Iterator[sqlite3.Row]:
    where, parameters = _where_clause(filters)
    query = f"""
        SELECT
            f.relative_path,
            f.category,
            f.suffix,
            f.size_bytes,
            f.modified_utc,
            f.is_large,
            f.is_symlink,
            COALESCE((
                SELECT GROUP_CONCAT(w.code, '|')
                FROM filename_warnings AS w
                WHERE w.file_id=f.id
            ), '') AS filename_warnings,
            COALESCE((
                SELECT dg.sha256
                FROM duplicate_members AS dm
                JOIN duplicate_groups AS dg ON dg.id=dm.group_id
                WHERE dm.file_id=f.id
                ORDER BY dg.id
                LIMIT 1
            ), '') AS duplicate_sha256
        FROM files AS f
        WHERE {where}
        ORDER BY f.relative_path COLLATE NOCASE, f.relative_path
    """
    yield from connection.execute(query, [session_id, *parameters])


def _summary(
    connection: sqlite3.Connection, session_id: int, filters: ReportFilter
) -> tuple[int, int]:
    where, parameters = _where_clause(filters)
    row = connection.execute(
        f"SELECT COUNT(*), COALESCE(SUM(f.size_bytes), 0) FROM files AS f WHERE {where}",
        [session_id, *parameters],
    ).fetchone()
    return int(row[0]), int(row[1])


def _prepare_target(path: Path, overwrite: bool) -> tuple[Path, Path]:
    target = path.expanduser().resolve(strict=False)
    if target.exists() and not overwrite:
        raise FileExistsError(
            f"Bericht existiert bereits: {target}. Nutze --overwrite-report zum Ersetzen."
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    return target, temporary


def _commit_target(target: Path, temporary: Path) -> None:
    temporary.replace(target)


def _write_csv_file(
    temporary: Path,
    connection: sqlite3.Connection,
    session_id: int,
    filters: ReportFilter,
) -> None:
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(_COLUMNS)
        for row in _iter_rows(connection, session_id, filters):
            writer.writerow([row[column] for column in _COLUMNS])


def _human_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size_bytes} B"


def _filter_description(filters: ReportFilter) -> str:
    parts: list[str] = []
    if filters.categories:
        parts.append("Typen: " + ", ".join(filters.categories))
    if filters.min_size_bytes is not None:
        parts.append("Mindestgröße: " + _human_size(filters.min_size_bytes))
    if filters.max_size_bytes is not None:
        parts.append("Maximalgröße: " + _human_size(filters.max_size_bytes))
    if filters.naming_warning_only:
        parts.append("nur Namensprobleme")
    if filters.duplicate_only:
        parts.append("nur Duplikatgruppen")
    return "; ".join(parts) if parts else "keine Vorfilter"


def _write_html_header(
    handle: TextIO,
    session: sqlite3.Row,
    row_count: int,
    total_size_bytes: int,
    filters: ReportFilter,
) -> None:
    root = html.escape(str(session["root"]))
    filter_text = html.escape(_filter_description(filters))
    handle.write(
        f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DATENBANKTOOL-Bericht</title>
<style>
:root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
body {{ margin: 0; padding: 1rem; line-height: 1.45; }}
header, .controls {{ position: sticky; top: 0; background: Canvas; padding: .8rem; border: 1px solid GrayText; z-index: 2; }}
.summary {{ display: flex; flex-wrap: wrap; gap: .7rem; margin: .7rem 0; }}
.card {{ border: 1px solid GrayText; border-radius: .5rem; padding: .6rem .8rem; min-width: 10rem; }}
.controls {{ top: auto; margin: 1rem 0; display: flex; flex-wrap: wrap; gap: .8rem; align-items: end; }}
label {{ display: grid; gap: .2rem; }}
input, select {{ font: inherit; padding: .45rem; min-height: 2.4rem; }}
table {{ width: 100%; border-collapse: collapse; font-size: .92rem; }}
th, td {{ border: 1px solid GrayText; padding: .35rem; text-align: left; vertical-align: top; }}
th {{ position: sticky; top: 0; background: Canvas; }}
.path {{ overflow-wrap: anywhere; min-width: 20rem; }}
.hidden {{ display: none; }}
.warning {{ font-weight: 700; }}
</style>
</head>
<body>
<header>
<h1>DATENBANKTOOL-Bericht</h1>
<div><strong>Wurzel:</strong> {root}</div>
<div><strong>Erzeugungsfilter:</strong> {filter_text}</div>
<div class="summary">
<div class="card"><strong>{row_count}</strong><br>Dateien</div>
<div class="card"><strong>{html.escape(_human_size(total_size_bytes))}</strong><br>Gesamtgröße</div>
<div class="card"><strong>#{int(session['id'])}</strong><br>Index-Sitzung</div>
</div>
</header>
<section class="controls" aria-label="Interaktive Tabellenfilter">
<label>Schnellsuche<input id="search" type="search" placeholder="Pfad, Endung, Warnung …"></label>
<label>Dateityp<select id="category"><option value="">alle</option>"""
    )
    for category in FileCategory:
        handle.write(f'<option value="{category.value}">{category.value}</option>')
    handle.write(
        """</select></label>
<label><span>Namensprobleme</span><input id="warnings" type="checkbox"></label>
<label><span>Duplikate</span><input id="duplicates" type="checkbox"></label>
<strong id="visible-count" aria-live="polite"></strong>
</section>
<table id="results">
<thead><tr>
<th>Pfad</th><th>Typ</th><th>Endung</th><th>Größe</th><th>Geändert UTC</th>
<th>Groß</th><th>Symlink</th><th>Namenswarnungen</th><th>Duplikat-SHA-256</th>
</tr></thead><tbody>
"""
    )


def _write_html_row(handle: TextIO, row: sqlite3.Row) -> None:
    warnings = str(row["filename_warnings"])
    duplicate = str(row["duplicate_sha256"])
    values = {column: html.escape(str(row[column])) for column in _COLUMNS}
    search_text = html.escape(
        " ".join(str(row[column]) for column in _COLUMNS).casefold(), quote=True
    )
    handle.write(
        f'<tr data-search="{search_text}" data-category="{values["category"]}" '
        f'data-warning="{int(bool(warnings))}" data-duplicate="{int(bool(duplicate))}">'
        f'<td class="path">{values["relative_path"]}</td>'
        f'<td>{values["category"]}</td><td>{values["suffix"]}</td>'
        f'<td data-bytes="{int(row["size_bytes"])}">'
        f'{html.escape(_human_size(int(row["size_bytes"])))}'</n        f'</td>'
        f'<td>{values["modified_utc"]}</td><td>{"ja" if row["is_large"] else "nein"}</td>'
        f'<td>{"ja" if row["is_symlink"] else "nein"}</td>'
        f'<td class="warning">{values["filename_warnings"]}</td>'
        f'<td class="path">{values["duplicate_sha256"]}</td></tr>\n'
    )


def _write_html_footer(handle: TextIO) -> None:
    handle.write(
        """</tbody></table>
<script>
const rows=[...document.querySelectorAll('#results tbody tr')];
const search=document.querySelector('#search');
const category=document.querySelector('#category');
const warnings=document.querySelector('#warnings');
const duplicates=document.querySelector('#duplicates');
const count=document.querySelector('#visible-count');
function applyFilters(){
  const needle=search.value.trim().toLocaleLowerCase('de');
  let visible=0;
  for(const row of rows){
    const show=(!needle||row.dataset.search.includes(needle))
      &&(!category.value||row.dataset.category===category.value)
      &&(!warnings.checked||row.dataset.warning==='1')
      &&(!duplicates.checked||row.dataset.duplicate==='1');
    row.classList.toggle('hidden',!show);
    if(show) visible++;
  }
  count.textContent=`${visible} sichtbar`;
}
for(const control of [search,category,warnings,duplicates]) control.addEventListener('input',applyFilters);
applyFilters();
</script>
</body></html>
"""
    )


def _write_html_file(
    temporary: Path,
    connection: sqlite3.Connection,
    session: sqlite3.Row,
    filters: ReportFilter,
    row_count: int,
    total_size_bytes: int,
) -> None:
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        _write_html_header(handle, session, row_count, total_size_bytes, filters)
        for row in _iter_rows(connection, int(session["id"]), filters):
            _write_html_row(handle, row)
        _write_html_footer(handle)


def export_reports(
    database_path: Path,
    *,
    csv_path: Path | None = None,
    html_path: Path | None = None,
    filters: ReportFilter = ReportFilter(),
    session_id: int | None = None,
    overwrite: bool = False,
) -> ReportResult:
    if csv_path is None and html_path is None:
        raise ValueError("Mindestens --csv oder --html muss angegeben werden")
    if not database_path.expanduser().exists():
        raise FileNotFoundError(f"Indexdatenbank nicht gefunden: {database_path.expanduser()}")

    csv_target: Path | None = None
    csv_temporary: Path | None = None
    html_target: Path | None = None
    html_temporary: Path | None = None
    if csv_path is not None:
        csv_target, csv_temporary = _prepare_target(csv_path, overwrite)
    if html_path is not None:
        html_target, html_temporary = _prepare_target(html_path, overwrite)
    if csv_target is not None and html_target is not None and csv_target == html_target:
        raise ValueError("CSV- und HTML-Bericht benötigen unterschiedliche Zieldateien")

    try:
        with IndexDatabase(database_path) as database:
            database.migrate()
            session = _select_session(database.connection, session_id)
            selected_session_id = int(session["id"])
            row_count, total_size = _summary(database.connection, selected_session_id, filters)
            if csv_temporary is not None:
                _write_csv_file(
                    csv_temporary, database.connection, selected_session_id, filters
                )
            if html_temporary is not None:
                _write_html_file(
                    html_temporary,
                    database.connection,
                    session,
                    filters,
                    row_count,
                    total_size,
                )
        if csv_target is not None and csv_temporary is not None:
            _commit_target(csv_target, csv_temporary)
        if html_target is not None and html_temporary is not None:
            _commit_target(html_target, html_temporary)
    except Exception:
        if csv_temporary is not None:
            csv_temporary.unlink(missing_ok=True)
        if html_temporary is not None:
            html_temporary.unlink(missing_ok=True)
        raise

    return ReportResult(
        session_id=selected_session_id,
        row_count=row_count,
        total_size_bytes=total_size,
        csv_path=str(csv_target) if csv_target else None,
        html_path=str(html_target) if html_target else None,
    )
