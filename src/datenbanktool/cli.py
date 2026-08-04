from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Sequence

from datenbanktool import __version__
from datenbanktool.core.changes import ChangeFilter, export_changes, query_changes
from datenbanktool.core.incremental import IncrementalScanOptions, incremental_rescan
from datenbanktool.core.index_admin import backup_index, list_sessions, restore_index
from datenbanktool.core.index_database import (
    IndexBuildOptions,
    IndexErrorBase,
    build_index,
    inspect_index,
    repair_index,
)
from datenbanktool.core.index_lock import IndexLockedError
from datenbanktool.core.progress import ProgressEvent
from datenbanktool.core.reports import ReportFilter, export_reports
from datenbanktool.core.scanner import ScanOptions, scan_tree
from datenbanktool.core.search import SearchFilter, build_fulltext_index, search_index

_CATEGORIES = ("audio", "video", "image", "text", "archive", "code", "document", "other")
_CHANGE_TYPES = ("added", "modified", "moved", "removed", "unchanged")
_CHANGE_LABELS = {
    "added": "Neu",
    "modified": "Geändert",
    "moved": "Verschoben",
    "removed": "Entfernt",
    "unchanged": "Unverändert",
}


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("Wert muss mindestens 1 sein")
    return parsed


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("Wert darf nicht negativ sein")
    return parsed


def _non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("Wert darf nicht negativ sein")
    return parsed


def _add_scan_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", type=Path)
    parser.add_argument("--hash-duplicates", action="store_true")
    parser.add_argument("--large-file-mib", type=_non_negative_int, default=1024)
    parser.add_argument("--max-files", type=_positive_int, default=None)
    parser.add_argument("--follow-symlinks", action="store_true")


def _add_progress_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--progress",
        choices=("human", "jsonl", "quiet"),
        default="human",
        help="Fortschritt verständlich, als JSONL oder gar nicht ausgeben.",
    )
    parser.add_argument("--lock-timeout", type=_non_negative_float, default=0.0)


def _add_category_filter(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--category",
        action="append",
        default=[],
        choices=_CATEGORIES,
        help="Nur diesen Dateityp zeigen. Mehrfach nutzbar.",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="datenbanktool",
        description="Sichere Analyse und Indexierung großer Linux-Datensammlungen.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Verzeichnis rein lesend prüfen")
    _add_scan_options(scan)
    scan.add_argument("--json", dest="json_path", type=Path)
    scan.add_argument("--overwrite-report", action="store_true")

    index = subparsers.add_parser("index", help="SQLite-Index verwalten und durchsuchen")
    index_subparsers = index.add_subparsers(dest="index_command", required=True)

    build = index_subparsers.add_parser("build", help="Index neu aufbauen oder fortsetzen")
    _add_scan_options(build)
    build.add_argument("--database", type=Path, required=True)
    build.add_argument("--batch-size", type=_positive_int, default=500)
    build.add_argument("--resume", action="store_true")
    _add_progress_options(build)

    rescan = index_subparsers.add_parser(
        "rescan", help="Seit dem vorherigen Scan geänderte Dateien erkennen"
    )
    rescan.add_argument("path", type=Path)
    rescan.add_argument("--database", type=Path, required=True)
    rescan.add_argument("--baseline-session-id", type=_positive_int)
    rescan.add_argument(
        "--hash-duplicates",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Ohne Angabe wird die Einstellung des vorherigen Scans übernommen.",
    )
    rescan.add_argument("--large-file-mib", type=_non_negative_int, default=None)
    rescan.add_argument(
        "--follow-symlinks",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    rescan.add_argument(
        "--detect-moves-by-hash",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Verschobene Dateien zusätzlich anhand vorhandener Prüfsummen erkennen.",
    )
    rescan.add_argument("--batch-size", type=_positive_int, default=500)
    rescan.add_argument("--resume", action="store_true")
    rescan.add_argument("--max-files", type=_positive_int, default=None)
    _add_progress_options(rescan)

    status = index_subparsers.add_parser("status", help="Letzten Indexstatus anzeigen")
    status.add_argument("database", type=Path)

    sessions = index_subparsers.add_parser("sessions", help="Gespeicherte Scans auflisten")
    sessions.add_argument("database", type=Path)
    sessions.add_argument("--limit", type=_positive_int, default=20)
    sessions.add_argument("--status", choices=("running", "interrupted", "complete", "failed"))
    sessions.add_argument("--root", type=Path)
    sessions.add_argument("--json", action="store_true")

    search = index_subparsers.add_parser(
        "search", help="Dateien im Index suchen – ohne Originaldateien zu verändern"
    )
    search.add_argument("database", type=Path)
    search.add_argument("text", nargs="?", default="", help="Suchwort oder mehrere Wörter")
    search.add_argument("--session-id", type=_positive_int)
    _add_category_filter(search)
    search.add_argument("--min-size-mib", type=_non_negative_int)
    search.add_argument("--max-size-mib", type=_non_negative_int)
    search.add_argument("--name-warning-only", action="store_true", help="Nur problematische Namen")
    search.add_argument("--duplicates-only", action="store_true", help="Nur erkannte Duplikate")
    search.add_argument("--page", type=_positive_int, default=1)
    search.add_argument("--page-size", type=_positive_int, default=25)
    search.add_argument(
        "--sort",
        choices=("path", "size", "date", "type", "relevance"),
        default="path",
    )
    search.add_argument("--descending", action="store_true")
    search.add_argument(
        "--fulltext",
        choices=("auto", "off", "required"),
        default="auto",
        help="Schnelle Volltextsuche automatisch nutzen, ausschalten oder verlangen.",
    )
    search.add_argument(
        "--build-fulltext-index",
        action="store_true",
        help="Einmalig einen schnellen Suchindex für die gewählte Sitzung aufbauen.",
    )
    search.add_argument("--lock-timeout", type=_non_negative_float, default=0.0)
    search.add_argument("--json", action="store_true", help="Ergebnis als JSON ausgeben")

    changes = index_subparsers.add_parser(
        "changes", help="Änderungen eines Re-Scans anzeigen oder als Bericht speichern"
    )
    changes.add_argument("database", type=Path)
    changes.add_argument("--session-id", type=_positive_int)
    changes.add_argument(
        "--type",
        dest="change_types",
        action="append",
        default=[],
        choices=_CHANGE_TYPES,
        help="Nur diese Änderungsart zeigen. Mehrfach nutzbar.",
    )
    _add_category_filter(changes)
    changes.add_argument("--contains", default="", help="Nur Pfade mit diesem Text")
    changes.add_argument("--page", type=_positive_int, default=1)
    changes.add_argument("--page-size", type=_positive_int, default=25)
    changes.add_argument("--sort", choices=("path", "type", "size", "date"), default="path")
    changes.add_argument("--descending", action="store_true")
    changes.add_argument("--json", dest="json_path", type=Path)
    changes.add_argument("--csv", dest="csv_path", type=Path)
    changes.add_argument("--html", dest="html_path", type=Path)
    changes.add_argument("--overwrite-report", action="store_true")
    changes.add_argument("--no-terminal", action="store_true", help="Nur Dateien erzeugen")

    backup = index_subparsers.add_parser("backup", help="Geprüfte Sicherung erstellen")
    backup.add_argument("database", type=Path)
    backup.add_argument("--output", type=Path)
    backup.add_argument("--overwrite", action="store_true")
    backup.add_argument("--lock-timeout", type=_non_negative_float, default=0.0)

    restore = index_subparsers.add_parser("restore", help="Geprüfte Sicherung wiederherstellen")
    restore.add_argument("database", type=Path)
    restore.add_argument("--backup", type=Path, required=True)
    restore.add_argument("--without-safety-backup", action="store_true")
    restore.add_argument("--lock-timeout", type=_non_negative_float, default=0.0)

    repair = index_subparsers.add_parser("repair", help="Index prüfen und reparieren")
    repair.add_argument("database", type=Path)
    repair.add_argument("--vacuum", action="store_true")
    repair.add_argument(
        "--without-backup",
        action="store_true",
        help="Nur bewusst verwenden: Reparatur ohne automatische Sicherheitskopie.",
    )
    repair.add_argument("--lock-timeout", type=_non_negative_float, default=0.0)

    report = subparsers.add_parser("report", help="Gefilterte CSV-/HTML-Dateiliste erzeugen")
    report.add_argument("database", type=Path)
    report.add_argument("--session-id", type=_positive_int)
    report.add_argument("--csv", dest="csv_path", type=Path)
    report.add_argument("--html", dest="html_path", type=Path)
    _add_category_filter(report)
    report.add_argument("--min-size-mib", type=_non_negative_int)
    report.add_argument("--max-size-mib", type=_non_negative_int)
    report.add_argument("--name-warning-only", action="store_true")
    report.add_argument("--duplicates-only", action="store_true")
    report.add_argument("--overwrite-report", action="store_true")
    return parser


def _progress_callback(mode: str):
    if mode == "quiet":
        return None

    def emit(event: ProgressEvent) -> None:
        if mode == "jsonl":
            print(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True), file=sys.stderr)
            return
        amount = ""
        if event.current is not None:
            total = f"/{event.total}" if event.total is not None else ""
            amount = f" [{event.current}{total}]"
        print(f"[{event.phase}:{event.kind}] {event.message}{amount}", file=sys.stderr)

    return emit


def _write_json_atomic(path: Path, payload: dict[str, object], overwrite: bool) -> None:
    target = path.expanduser().resolve(strict=False)
    if target.exists() and not overwrite:
        raise FileExistsError(f"Bericht existiert bereits: {target}. Nutze --overwrite-report.")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _human_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{int(value)} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size_bytes} B"


def _run_scan(arguments: argparse.Namespace) -> int:
    report = scan_tree(
        ScanOptions(
            root=arguments.path,
            hash_duplicates=arguments.hash_duplicates,
            large_file_bytes=arguments.large_file_mib * 1024 * 1024,
            follow_symlinks=arguments.follow_symlinks,
            max_files=arguments.max_files,
        )
    )
    print(f"Wurzel: {report.root}")
    print(f"Dateien: {len(report.files)}")
    print(f"Gesamtgröße: {report.total_size_bytes} Byte")
    print(f"Große Dateien: {report.large_file_count}")
    print(f"Exakte Duplikatgruppen: {len(report.duplicate_groups)}")
    print(f"Lesefehler: {len(report.errors)}")
    print(f"Abgebrochen durch Dateigrenze: {'ja' if report.truncated else 'nein'}")
    if arguments.json_path is not None:
        _write_json_atomic(arguments.json_path, report.to_dict(), arguments.overwrite_report)
        print(f"JSON-Bericht: {arguments.json_path.expanduser()}")
    return 1 if report.errors else 0


def _print_index_result(result) -> None:
    print(f"Datenbank: {result.database}")
    print(f"Schema-Version: {result.schema_version}")
    print(f"Sitzung: {result.session_id}")
    print(f"Status: {result.status}")
    print(f"Phase: {result.phase}")
    print(f"Importierte Dateien: {result.imported_count}")
    print(f"Fehler: {result.error_count}")
    print(f"Duplikatgruppen: {result.duplicate_group_count}")
    print(f"Fortgesetzt: {'ja' if result.resumed else 'nein'}")


def _run_index_build(arguments: argparse.Namespace) -> int:
    result = build_index(
        IndexBuildOptions(
            root=arguments.path,
            database=arguments.database,
            hash_duplicates=arguments.hash_duplicates,
            large_file_bytes=arguments.large_file_mib * 1024 * 1024,
            follow_symlinks=arguments.follow_symlinks,
            batch_size=arguments.batch_size,
            resume=arguments.resume,
            max_files=arguments.max_files,
            lock_timeout_seconds=arguments.lock_timeout,
        ),
        progress_callback=_progress_callback(arguments.progress),
    )
    _print_index_result(result)
    return 0 if result.status == "complete" and result.error_count == 0 else 1


def _run_index_rescan(arguments: argparse.Namespace) -> int:
    large_file_bytes = (
        arguments.large_file_mib * 1024 * 1024
        if arguments.large_file_mib is not None
        else None
    )
    result = incremental_rescan(
        IncrementalScanOptions(
            root=arguments.path,
            database=arguments.database,
            baseline_session_id=arguments.baseline_session_id,
            hash_duplicates=arguments.hash_duplicates,
            large_file_bytes=large_file_bytes,
            follow_symlinks=arguments.follow_symlinks,
            detect_moves_by_hash=arguments.detect_moves_by_hash,
            batch_size=arguments.batch_size,
            resume=arguments.resume,
            max_files=arguments.max_files,
            lock_timeout_seconds=arguments.lock_timeout,
        ),
        progress_callback=_progress_callback(arguments.progress),
    )
    _print_index_result(result)
    print(f"Vorheriger Scan: {result.baseline_session_id}")
    print(f"Neu: {result.added_count}")
    print(f"Geändert: {result.modified_count}")
    print(f"Verschoben: {result.moved_count}")
    print(f"Entfernt: {result.removed_count}")
    print(f"Unverändert: {result.unchanged_count}")
    return 0 if result.status == "complete" and result.error_count == 0 else 1


def _run_index_status(arguments: argparse.Namespace) -> int:
    status = inspect_index(arguments.database)
    print(f"Datenbank: {status.database}")
    print(f"Schema-Version: {status.schema_version}")
    if status.session_id is None:
        print("Noch kein Scan gespeichert.")
        return 0
    print(f"Sitzung: {status.session_id}")
    print(f"Modus: {status.scan_mode}")
    print(f"Vorheriger Scan: {status.parent_session_id or '-'}")
    print(f"Ordner: {status.root}")
    print(f"Status: {status.status}")
    print(f"Phase: {status.phase}")
    print(f"Dateien: {status.imported_count}")
    print(f"Fehler: {status.error_count}")
    print(f"Duplikatgruppen: {status.duplicate_group_count}")
    print(f"Aktualisiert UTC: {status.updated_utc}")
    return 0 if status.status in {None, "complete", "interrupted"} else 1


def _run_index_sessions(arguments: argparse.Namespace) -> int:
    sessions = list_sessions(
        arguments.database,
        limit=arguments.limit,
        status=arguments.status,
        root=arguments.root,
    )
    if arguments.json:
        print(json.dumps([item.to_dict() for item in sessions], ensure_ascii=False, indent=2))
        return 0
    if not sessions:
        print("Keine passenden Scans gefunden.")
        return 0
    for item in sessions:
        changes = (
            f"neu={item.added_count}, geändert={item.modified_count}, "
            f"verschoben={item.moved_count}, entfernt={item.removed_count}, "
            f"unverändert={item.unchanged_count}"
        )
        print(
            f"#{item.session_id} | {item.scan_mode} | {item.status}/{item.phase} | "
            f"Dateien={item.imported_count} | Fehler={item.error_count} | {changes} | {item.root}"
        )
    return 0


def _run_index_search(arguments: argparse.Namespace) -> int:
    if arguments.build_fulltext_index:
        built = build_fulltext_index(
            arguments.database,
            session_id=arguments.session_id,
            lock_timeout_seconds=arguments.lock_timeout,
        )
        print(
            f"Schneller Suchindex aufgebaut: {built.indexed_files} Dateien in Sitzung "
            f"#{built.session_id}",
            file=sys.stderr if arguments.json else sys.stdout,
        )
    mib = 1024 * 1024
    page = search_index(
        arguments.database,
        session_id=arguments.session_id,
        filters=SearchFilter(
            text=arguments.text,
            categories=tuple(arguments.category),
            min_size_bytes=(
                arguments.min_size_mib * mib
                if arguments.min_size_mib is not None
                else None
            ),
            max_size_bytes=(
                arguments.max_size_mib * mib
                if arguments.max_size_mib is not None
                else None
            ),
            naming_warning_only=arguments.name_warning_only,
            duplicate_only=arguments.duplicates_only,
            page=arguments.page,
            page_size=arguments.page_size,
            sort_by=arguments.sort,
            descending=arguments.descending,
            fulltext_mode=arguments.fulltext,
        ),
    )
    if arguments.json:
        print(json.dumps(page.to_dict(), ensure_ascii=False, indent=2))
        return 0
    search_kind = "schnelle Volltextsuche" if page.engine == "fts5" else "normale Suche"
    print(f"Ordner: {page.root}")
    print(f"Gespeicherter Scan: #{page.session_id}")
    print(f"Suchart: {search_kind}")
    print(f"Treffer: {page.total_rows} | Seite {page.page} von {page.total_pages}")
    if not page.rows:
        print("Keine passenden Dateien gefunden.")
        return 0
    for row in page.rows:
        notes: list[str] = []
        if row.filename_warnings:
            notes.append("Namensproblem")
        if row.duplicate_sha256:
            notes.append("Duplikat")
        suffix = f" | {', '.join(notes)}" if notes else ""
        print(f"{row.relative_path} | {row.category} | {_human_size(row.size_bytes)}{suffix}")
    if page.page < page.total_pages:
        print(f"Nächste Seite: --page {page.page + 1}")
    return 0


def _run_index_changes(arguments: argparse.Namespace) -> int:
    filters = ChangeFilter(
        change_types=tuple(arguments.change_types),
        categories=tuple(arguments.category),
        contains=arguments.contains,
        page=arguments.page,
        page_size=arguments.page_size,
        sort_by=arguments.sort,
        descending=arguments.descending,
    )
    has_export = any((arguments.json_path, arguments.csv_path, arguments.html_path))
    if arguments.no_terminal and not has_export:
        raise ValueError("Ohne Terminalanzeige muss mindestens JSON, CSV oder HTML gewählt werden")
    page = query_changes(arguments.database, session_id=arguments.session_id, filters=filters)
    if not arguments.no_terminal:
        print(f"Re-Scan: #{page.session_id} | Vorheriger Scan: #{page.baseline_session_id}")
        print(f"Ordner: {page.root}")
        print(
            "Gesamt: "
            f"neu={page.counts['added']}, geändert={page.counts['modified']}, "
            f"verschoben={page.counts['moved']}, entfernt={page.counts['removed']}, "
            f"unverändert={page.counts['unchanged']}"
        )
        print(f"Gefilterte Treffer: {page.total_rows} | Seite {page.page} von {page.total_pages}")
        if not page.rows:
            print("Keine passenden Änderungen gefunden.")
        for row in page.rows:
            old_path = row.old_path or "–"
            new_path = row.new_path or "–"
            print(
                f"[{_CHANGE_LABELS[row.change_type]}] {old_path} → {new_path} | "
                f"{row.category} | {_human_size(row.size_bytes)}"
            )
        if page.page < page.total_pages:
            print(f"Nächste Seite: --page {page.page + 1}")
    if has_export:
        exported = export_changes(
            arguments.database,
            session_id=page.session_id,
            filters=filters,
            json_path=arguments.json_path,
            csv_path=arguments.csv_path,
            html_path=arguments.html_path,
            overwrite=arguments.overwrite_report,
        )
        print(f"Exportierte Änderungen: {exported.row_count}")
        if exported.json_path:
            print(f"JSON-Bericht: {exported.json_path}")
        if exported.csv_path:
            print(f"CSV-Bericht: {exported.csv_path}")
        if exported.html_path:
            print(f"HTML-Bericht: {exported.html_path}")
    return 0


def _run_index_backup(arguments: argparse.Namespace) -> int:
    result = backup_index(
        arguments.database,
        arguments.output,
        overwrite=arguments.overwrite,
        lock_timeout_seconds=arguments.lock_timeout,
    )
    print(f"Datenbank: {result.database}")
    print(f"Sicherung: {result.backup}")
    print(f"Schema-Version: {result.schema_version}")
    print(f"Prüfung: {', '.join(result.integrity)}")
    print(f"Größe: {result.size_bytes} Byte")
    return 0


def _run_index_restore(arguments: argparse.Namespace) -> int:
    result = restore_index(
        arguments.database,
        arguments.backup,
        create_safety_backup=not arguments.without_safety_backup,
        lock_timeout_seconds=arguments.lock_timeout,
    )
    print(f"Datenbank: {result.database}")
    print(f"Wiederhergestellt aus: {result.restored_from}")
    print(f"Sicherung vor Wiederherstellung: {result.safety_backup or 'bewusst deaktiviert'}")
    print(f"Schema-Version: {result.schema_version}")
    print(f"Prüfung: {', '.join(result.integrity)}")
    print(f"Status: {'erfolgreich' if result.successful else 'fehlgeschlagen'}")
    return 0 if result.successful else 1


def _run_index_repair(arguments: argparse.Namespace) -> int:
    result = repair_index(
        arguments.database,
        create_backup=not arguments.without_backup,
        vacuum=arguments.vacuum,
        lock_timeout_seconds=arguments.lock_timeout,
    )
    print(f"Datenbank: {result.database}")
    print(f"Sicherheitskopie: {result.backup or 'bewusst deaktiviert'}")
    print(f"Prüfung vorher: {', '.join(result.before_integrity)}")
    print(f"Prüfung nachher: {', '.join(result.after_integrity)}")
    print(f"Fremdschlüsselfehler: {result.foreign_key_errors}")
    print(f"Unterbrochene Sitzungen korrigiert: {result.interrupted_sessions}")
    for action in result.actions:
        print(f"- {action}")
    print(f"Reparaturstatus: {'erfolgreich' if result.successful else 'nicht vollständig'}")
    return 0 if result.successful else 1


def _run_report(arguments: argparse.Namespace) -> int:
    mib = 1024 * 1024
    result = export_reports(
        arguments.database,
        csv_path=arguments.csv_path,
        html_path=arguments.html_path,
        session_id=arguments.session_id,
        overwrite=arguments.overwrite_report,
        filters=ReportFilter(
            categories=tuple(arguments.category),
            min_size_bytes=(
                arguments.min_size_mib * mib
                if arguments.min_size_mib is not None
                else None
            ),
            max_size_bytes=(
                arguments.max_size_mib * mib
                if arguments.max_size_mib is not None
                else None
            ),
            naming_warning_only=arguments.name_warning_only,
            duplicate_only=arguments.duplicates_only,
        ),
    )
    print(f"Gespeicherter Scan: #{result.session_id}")
    print(f"Gefilterte Dateien: {result.row_count}")
    print(f"Gesamtgröße: {result.total_size_bytes} Byte")
    if result.csv_path:
        print(f"CSV-Bericht: {result.csv_path}")
    if result.html_path:
        print(f"HTML-Bericht: {result.html_path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "scan":
            return _run_scan(arguments)
        if arguments.command == "index":
            handlers = {
                "build": _run_index_build,
                "rescan": _run_index_rescan,
                "status": _run_index_status,
                "sessions": _run_index_sessions,
                "search": _run_index_search,
                "changes": _run_index_changes,
                "backup": _run_index_backup,
                "restore": _run_index_restore,
                "repair": _run_index_repair,
            }
            return handlers[arguments.index_command](arguments)
        if arguments.command == "report":
            return _run_report(arguments)
    except (
        FileExistsError,
        FileNotFoundError,
        IndexErrorBase,
        IndexLockedError,
        NotADirectoryError,
        OSError,
        sqlite3.Error,
        ValueError,
    ) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 2
    parser.error("Unbekannter Befehl")
    return 2
