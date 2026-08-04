from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Sequence

from datenbanktool import __version__
from datenbanktool.core.index_database import (
    IndexBuildOptions,
    IndexErrorBase,
    build_index,
    inspect_index,
    repair_index,
)
from datenbanktool.core.reports import ReportFilter, export_reports
from datenbanktool.core.scanner import ScanOptions, scan_tree


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


def _add_scan_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", type=Path)
    parser.add_argument("--hash-duplicates", action="store_true")
    parser.add_argument("--large-file-mib", type=_non_negative_int, default=1024)
    parser.add_argument("--max-files", type=_positive_int, default=None)
    parser.add_argument("--follow-symlinks", action="store_true")


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

    index = subparsers.add_parser("index", help="Persistenten SQLite-Index verwalten")
    index_subparsers = index.add_subparsers(dest="index_command", required=True)

    build = index_subparsers.add_parser("build", help="Index neu aufbauen oder fortsetzen")
    _add_scan_options(build)
    build.add_argument("--database", type=Path, required=True)
    build.add_argument("--batch-size", type=_positive_int, default=500)
    build.add_argument("--resume", action="store_true")

    status = index_subparsers.add_parser("status", help="Letzten Indexstatus anzeigen")
    status.add_argument("database", type=Path)

    repair = index_subparsers.add_parser("repair", help="Index prüfen und reparieren")
    repair.add_argument("database", type=Path)
    repair.add_argument("--vacuum", action="store_true")
    repair.add_argument(
        "--without-backup",
        action="store_true",
        help="Nur bewusst verwenden: Reparatur ohne automatische Sicherheitskopie.",
    )

    report = subparsers.add_parser("report", help="Gefilterte CSV-/HTML-Berichte erzeugen")
    report.add_argument("database", type=Path)
    report.add_argument("--session-id", type=_positive_int)
    report.add_argument("--csv", dest="csv_path", type=Path)
    report.add_argument("--html", dest="html_path", type=Path)
    report.add_argument(
        "--category",
        action="append",
        default=[],
        choices=("audio", "video", "image", "text", "archive", "code", "document", "other"),
    )
    report.add_argument("--min-size-mib", type=_non_negative_int)
    report.add_argument("--max-size-mib", type=_non_negative_int)
    report.add_argument("--name-warning-only", action="store_true")
    report.add_argument("--duplicates-only", action="store_true")
    report.add_argument("--overwrite-report", action="store_true")
    return parser


def _write_json_atomic(path: Path, payload: dict[str, object], overwrite: bool) -> None:
    target = path.expanduser().resolve(strict=False)
    if target.exists() and not overwrite:
        raise FileExistsError(
            f"Bericht existiert bereits: {target}. Nutze --overwrite-report zum Ersetzen."
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


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
        _write_json_atomic(
            arguments.json_path, report.to_dict(), overwrite=arguments.overwrite_report
        )
        print(f"JSON-Bericht: {arguments.json_path.expanduser()}")
    return 1 if report.errors else 0


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
        )
    )
    print(f"Datenbank: {result.database}")
    print(f"Schema-Version: {result.schema_version}")
    print(f"Sitzung: {result.session_id}")
    print(f"Status: {result.status}")
    print(f"Phase: {result.phase}")
    print(f"Importierte Dateien: {result.imported_count}")
    print(f"Fehler: {result.error_count}")
    print(f"Duplikatgruppen: {result.duplicate_group_count}")
    print(f"Fortgesetzt: {'ja' if result.resumed else 'nein'}")
    return 0 if result.status == "complete" and result.error_count == 0 else 1


def _run_index_status(arguments: argparse.Namespace) -> int:
    status = inspect_index(arguments.database)
    print(f"Datenbank: {status.database}")
    print(f"Schema-Version: {status.schema_version}")
    if status.session_id is None:
        print("Noch keine Index-Sitzung vorhanden.")
        return 0
    print(f"Sitzung: {status.session_id}")
    print(f"Wurzel: {status.root}")
    print(f"Status: {status.status}")
    print(f"Phase: {status.phase}")
    print(f"Importierte Dateien: {status.imported_count}")
    print(f"Fehler: {status.error_count}")
    print(f"Duplikatgruppen: {status.duplicate_group_count}")
    print(f"Aktualisiert UTC: {status.updated_utc}")
    return 0 if status.status in {None, "complete", "interrupted"} else 1


def _run_index_repair(arguments: argparse.Namespace) -> int:
    result = repair_index(
        arguments.database,
        create_backup=not arguments.without_backup,
        vacuum=arguments.vacuum,
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
    min_size = arguments.min_size_mib * mib if arguments.min_size_mib is not None else None
    max_size = arguments.max_size_mib * mib if arguments.max_size_mib is not None else None
    result = export_reports(
        arguments.database,
        csv_path=arguments.csv_path,
        html_path=arguments.html_path,
        session_id=arguments.session_id,
        overwrite=arguments.overwrite_report,
        filters=ReportFilter(
            categories=tuple(arguments.category),
            min_size_bytes=min_size,
            max_size_bytes=max_size,
            naming_warning_only=arguments.name_warning_only,
            duplicate_only=arguments.duplicates_only,
        ),
    )
    print(f"Index-Sitzung: {result.session_id}")
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
            if arguments.index_command == "build":
                return _run_index_build(arguments)
            if arguments.index_command == "status":
                return _run_index_status(arguments)
            if arguments.index_command == "repair":
                return _run_index_repair(arguments)
        if arguments.command == "report":
            return _run_report(arguments)
    except (
        FileExistsError,
        FileNotFoundError,
        IndexErrorBase,
        NotADirectoryError,
        OSError,
        sqlite3.Error,
        ValueError,
    ) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 2
    parser.error("Unbekannter Befehl")
    return 2
