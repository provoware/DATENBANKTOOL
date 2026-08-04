from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Sequence

from datenbanktool import __version__
from datenbanktool.core.changes import ChangeFilter, export_changes, query_changes
from datenbanktool.core.folders import (
    FolderFilter,
    analyse_folders,
    export_folder_html,
    export_folder_json,
)
from datenbanktool.core.help_system import get_topic, list_topics
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
from datenbanktool.core.presentation import (
    TrafficLight,
    change_text,
    hint_text,
    paint,
    status_text,
    traffic_text,
)
from datenbanktool.core.presets import (
    delete_preset,
    get_preset,
    list_presets,
    save_preset,
)
from datenbanktool.core.progress import ProgressEvent
from datenbanktool.core.reports import ReportFilter, export_reports
from datenbanktool.core.scanner import ScanOptions, scan_tree
from datenbanktool.core.search import SearchFilter, build_fulltext_index, search_index

_CATEGORIES = (
    "audio",
    "video",
    "image",
    "text",
    "archive",
    "code",
    "document",
    "other",
)
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


def _parser(*args: object, **kwargs: object) -> argparse.ArgumentParser:
    kwargs.setdefault("formatter_class", argparse.RawDescriptionHelpFormatter)
    return argparse.ArgumentParser(*args, **kwargs)


def _add_scan_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", type=Path, help="Ordner, der geprüft werden soll")
    parser.add_argument(
        "--hash-duplicates",
        action="store_true",
        help="Dateiinhalte vergleichen. Sicher, aber bei großen Beständen langsamer.",
    )
    parser.add_argument(
        "--large-file-mib",
        type=_non_negative_int,
        default=1024,
        help="Ab dieser Größe wird eine Datei als groß markiert. Standard: 1024 MiB.",
    )
    parser.add_argument("--max-files", type=_positive_int, default=None)
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help=(
            "Symbolischen Verzeichnissen folgen. Standardmäßig aus "
            "Sicherheitsgründen aus."
        ),
    )


def _add_progress_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--progress",
        choices=("human", "jsonl", "quiet"),
        default="human",
        help="Fortschritt verständlich, als JSONL oder gar nicht ausgeben.",
    )
    parser.add_argument(
        "--lock-timeout",
        type=_non_negative_float,
        default=0.0,
        help=(
            "Wie lange auf einen anderen Indexprozess gewartet wird. "
            "Standard: sofort abbrechen."
        ),
    )


def _add_category_filter(
    parser: argparse.ArgumentParser,
    *,
    default: list[str] | None = None,
) -> None:
    parser.add_argument(
        "--category",
        action="append",
        default=default,
        choices=_CATEGORIES,
        help="Nur diesen Dateityp zeigen. Mehrfach nutzbar.",
    )


def _add_preset_filter_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--text", default="", help="Suchwort oder mehrere Wörter")
    _add_category_filter(parser, default=[])
    parser.add_argument("--min-size-mib", type=_non_negative_int)
    parser.add_argument("--max-size-mib", type=_non_negative_int)
    parser.add_argument("--name-warning-only", action="store_true")
    parser.add_argument("--duplicates-only", action="store_true")
    parser.add_argument("--page-size", type=_positive_int, default=25)
    parser.add_argument(
        "--sort",
        choices=("path", "size", "date", "type", "relevance"),
        default="path",
    )
    parser.add_argument("--descending", action="store_true")
    parser.add_argument(
        "--fulltext",
        choices=("auto", "off", "required"),
        default="auto",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = _parser(
        prog="datenbanktool",
        description=(
            "Sicheres Linux-Werkzeug für große Datensammlungen.\n"
            "Farben und Ampeln unterstützen die Orientierung, werden aber "
            "immer durch Klartext ergänzt."
        ),
        epilog=(
            "Globale Anzeigeoptionen stehen vor dem Befehl, zum Beispiel:\n"
            "  datenbanktool --color always index folders index.sqlite3\n"
            "Detaillierte Auswirkungen: datenbanktool explain"
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help=(
            "Farben automatisch, immer oder nie verwenden. "
            "Die Umgebungsvariable NO_COLOR wird respektiert."
        ),
    )
    parser.add_argument(
        "--hints",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Kurze Bedienhinweise ein- oder ausschalten.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    explain = subparsers.add_parser(
        "explain",
        help="Funktion, Auswirkung und Sicherheitsniveau verständlich erklären",
        description=(
            "Zeigt ausführlich, was eine Funktion macht, was sie schreibt "
            "und wann sie sinnvoll ist."
        ),
    )
    explain.add_argument(
        "topic",
        nargs="?",
        help="Zum Beispiel folders, search, presets oder restore",
    )
    explain.add_argument("--json", action="store_true")

    scan = subparsers.add_parser(
        "scan",
        help="Verzeichnis einmalig und rein lesend prüfen",
        description=(
            "Liest Dateiinformationen direkt aus einem Ordner. "
            "Originaldateien werden nicht verändert."
        ),
        epilog=(
            "Auswirkung: Nur ein ausdrücklich gewählter JSON-Bericht "
            "wird geschrieben."
        ),
    )
    _add_scan_options(scan)
    scan.add_argument("--json", dest="json_path", type=Path)
    scan.add_argument("--overwrite-report", action="store_true")

    index = subparsers.add_parser(
        "index",
        help="SQLite-Index verwalten und durchsuchen",
        description=(
            "Alle Indexfunktionen arbeiten lokal. "
            "Originaldatei-Schreibzugriffe bleiben gesperrt."
        ),
    )
    index_subparsers = index.add_subparsers(dest="index_command", required=True)

    build = index_subparsers.add_parser(
        "build",
        help="Index neu aufbauen oder sicher fortsetzen",
        description=(
            "Liest einen Ordner und speichert einen durchsuchbaren Snapshot in SQLite."
        ),
        epilog=(
            "Auswirkung: Schreibt nur in die gewählte Indexdatenbank; "
            "Originaldateien bleiben unverändert."
        ),
    )
    _add_scan_options(build)
    build.add_argument("--database", type=Path, required=True)
    build.add_argument("--batch-size", type=_positive_int, default=500)
    build.add_argument("--resume", action="store_true")
    _add_progress_options(build)

    rescan = index_subparsers.add_parser(
        "rescan",
        help="Änderungen seit dem vorherigen Scan erkennen",
        description=(
            "Erzeugt einen neuen Snapshot und vergleicht ihn mit einem "
            "abgeschlossenen Scan."
        ),
        epilog="Auswirkung: Schreibt eine neue Indexsitzung; Dateien werden nur gelesen.",
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

    status = index_subparsers.add_parser(
        "status",
        help="Letzten Indexstatus mit Ampel anzeigen",
    )
    status.add_argument("database", type=Path)

    sessions = index_subparsers.add_parser(
        "sessions",
        help="Gespeicherte Scans farbig auflisten",
    )
    sessions.add_argument("database", type=Path)
    sessions.add_argument("--limit", type=_positive_int, default=20)
    sessions.add_argument(
        "--status",
        choices=("running", "interrupted", "complete", "failed"),
    )
    sessions.add_argument("--root", type=Path)
    sessions.add_argument("--json", action="store_true")

    search = index_subparsers.add_parser(
        "search",
        help="Dateien suchen oder eine Suchvorlage starten",
        description=(
            "Durchsucht einen abgeschlossenen Snapshot. Ohne "
            "--build-fulltext-index bleibt die Datenbank rein lesend.\n"
            "Eine gespeicherte Vorlage wird mit --preset NAME geladen; "
            "ausdrücklich angegebene Werte überschreiben sie."
        ),
        epilog=(
            "Beispiel: datenbanktool index search index.sqlite3 "
            "--preset grosse-audios\n"
            "Auswirkung: Keine Änderung, außer der schnelle FTS5-Index "
            "wird ausdrücklich aufgebaut."
        ),
    )
    search.add_argument("database", type=Path)
    search.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Suchwort oder mehrere Wörter",
    )
    search.add_argument("--preset", help="Gespeicherte Suchvorlage laden")
    search.add_argument("--preset-file", type=Path, help="Abweichende Vorlagendatei")
    search.add_argument("--session-id", type=_positive_int)
    _add_category_filter(search, default=None)
    search.add_argument("--min-size-mib", type=_non_negative_int)
    search.add_argument("--max-size-mib", type=_non_negative_int)
    search.add_argument(
        "--name-warning-only",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Nur problematische Namen; mit --no-name-warning-only "
            "einen Vorlagenwert ausschalten."
        ),
    )
    search.add_argument(
        "--duplicates-only",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Nur Duplikate; mit --no-duplicates-only "
            "einen Vorlagenwert ausschalten."
        ),
    )
    search.add_argument("--page", type=_positive_int, default=1)
    search.add_argument("--page-size", type=_positive_int, default=None)
    search.add_argument(
        "--sort",
        choices=("path", "size", "date", "type", "relevance"),
        default=None,
    )
    search.add_argument(
        "--descending",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    search.add_argument(
        "--fulltext",
        choices=("auto", "off", "required"),
        default=None,
    )
    search.add_argument("--build-fulltext-index", action="store_true")
    search.add_argument("--lock-timeout", type=_non_negative_float, default=0.0)
    search.add_argument("--json", action="store_true")

    folders = index_subparsers.add_parser(
        "folders",
        help="Ordnergrößen, Dateizahlen und Platzfresser mit Ampel anzeigen",
        description=(
            "Fasst den gewählten Snapshot pro Ordner zusammen. Unterordner "
            "werden in den Gesamtwerten mitgerechnet.\n"
            "Die Ampel bewertet nur den Prüfbedarf und behauptet keinen Dateischaden."
        ),
        epilog=(
            "Grün = unauffällig, Gelb = prüfen, Rot = dringend prüfen. "
            "Die Begründung steht immer dabei.\n"
            "Auswirkung: Reine Auswertung; nur gewählte JSON-/HTML-Berichte "
            "werden geschrieben."
        ),
    )
    folders.add_argument("database", type=Path)
    folders.add_argument("--session-id", type=_positive_int)
    folders.add_argument("--contains", default="", help="Nur Ordnerpfade mit diesem Text")
    folders.add_argument("--min-files", type=_positive_int, default=1)
    folders.add_argument("--min-size-mib", type=_non_negative_int, default=0)
    folders.add_argument("--max-depth", type=_non_negative_int)
    folders.add_argument("--page", type=_positive_int, default=1)
    folders.add_argument("--page-size", type=_positive_int, default=25)
    folders.add_argument(
        "--sort",
        choices=("path", "files", "size", "largest", "warnings", "duplicates"),
        default="size",
    )
    folders.add_argument(
        "--descending",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    folders.add_argument("--top-files", type=_positive_int, default=3)
    folders.add_argument(
        "--attention-file-mib",
        type=_positive_int,
        default=1024,
        help="Ab dieser Einzeldateigröße wechselt die Ampel mindestens auf Gelb.",
    )
    folders.add_argument("--json", dest="json_path", type=Path)
    folders.add_argument("--html", dest="html_path", type=Path)
    folders.add_argument("--overwrite-report", action="store_true")
    folders.add_argument("--no-terminal", action="store_true")

    changes = index_subparsers.add_parser(
        "changes",
        help="Änderungen eines Re-Scans anzeigen oder speichern",
        description=(
            "Zeigt verständlich, was seit dem vorherigen Scan neu, geändert, "
            "verschoben oder entfernt wurde."
        ),
        epilog="Auswirkung: Reine Auswertung; nur gewählte Berichte werden geschrieben.",
    )
    changes.add_argument("database", type=Path)
    changes.add_argument("--session-id", type=_positive_int)
    changes.add_argument(
        "--type",
        dest="change_types",
        action="append",
        default=[],
        choices=_CHANGE_TYPES,
    )
    _add_category_filter(changes, default=[])
    changes.add_argument("--contains", default="")
    changes.add_argument("--page", type=_positive_int, default=1)
    changes.add_argument("--page-size", type=_positive_int, default=25)
    changes.add_argument(
        "--sort",
        choices=("path", "type", "size", "date"),
        default="path",
    )
    changes.add_argument("--descending", action="store_true")
    changes.add_argument("--json", dest="json_path", type=Path)
    changes.add_argument("--csv", dest="csv_path", type=Path)
    changes.add_argument("--html", dest="html_path", type=Path)
    changes.add_argument("--overwrite-report", action="store_true")
    changes.add_argument("--no-terminal", action="store_true")

    presets = index_subparsers.add_parser(
        "presets",
        help="Suchvorlagen speichern, anzeigen oder löschen",
        description=(
            "Speichert Suchfilter in einer kleinen lokalen JSON-Konfigurationsdatei."
        ),
        epilog=(
            "Vorlagen verändern weder Originaldateien noch den SQLite-Index.\n"
            "Starten: datenbanktool index search index.sqlite3 --preset NAME"
        ),
    )
    preset_subparsers = presets.add_subparsers(
        dest="preset_command",
        required=True,
    )
    preset_list = preset_subparsers.add_parser(
        "list",
        help="Alle Suchvorlagen auflisten",
    )
    preset_list.add_argument("--preset-file", type=Path)
    preset_list.add_argument("--json", action="store_true")

    preset_show = preset_subparsers.add_parser(
        "show",
        help="Eine Suchvorlage vollständig erklären",
    )
    preset_show.add_argument("name")
    preset_show.add_argument("--preset-file", type=Path)
    preset_show.add_argument("--json", action="store_true")

    preset_save = preset_subparsers.add_parser(
        "save",
        help="Neue Suchvorlage sicher speichern",
    )
    preset_save.add_argument("name")
    preset_save.add_argument("--description", default="")
    preset_save.add_argument("--preset-file", type=Path)
    preset_save.add_argument("--replace", action="store_true")
    _add_preset_filter_options(preset_save)

    preset_delete = preset_subparsers.add_parser(
        "delete",
        help="Suchvorlage löschen",
    )
    preset_delete.add_argument("name")
    preset_delete.add_argument("--preset-file", type=Path)
    preset_delete.add_argument(
        "--yes",
        action="store_true",
        help="Löschen ausdrücklich bestätigen",
    )

    backup = index_subparsers.add_parser("backup", help="Geprüfte Sicherung erstellen")
    backup.add_argument("database", type=Path)
    backup.add_argument("--output", type=Path)
    backup.add_argument("--overwrite", action="store_true")
    backup.add_argument("--lock-timeout", type=_non_negative_float, default=0.0)

    restore = index_subparsers.add_parser(
        "restore",
        help="Geprüfte Sicherung wiederherstellen",
    )
    restore.add_argument("database", type=Path)
    restore.add_argument("--backup", type=Path, required=True)
    restore.add_argument("--without-safety-backup", action="store_true")
    restore.add_argument("--lock-timeout", type=_non_negative_float, default=0.0)

    repair = index_subparsers.add_parser("repair", help="Index prüfen und reparieren")
    repair.add_argument("database", type=Path)
    repair.add_argument("--vacuum", action="store_true")
    repair.add_argument("--without-backup", action="store_true")
    repair.add_argument("--lock-timeout", type=_non_negative_float, default=0.0)

    report = subparsers.add_parser(
        "report",
        help="Gefilterte CSV-/HTML-Dateiliste erzeugen",
    )
    report.add_argument("database", type=Path)
    report.add_argument("--session-id", type=_positive_int)
    report.add_argument("--csv", dest="csv_path", type=Path)
    report.add_argument("--html", dest="html_path", type=Path)
    _add_category_filter(report, default=[])
    report.add_argument("--min-size-mib", type=_non_negative_int)
    report.add_argument("--max-size-mib", type=_non_negative_int)
    report.add_argument("--name-warning-only", action="store_true")
    report.add_argument("--duplicates-only", action="store_true")
    report.add_argument("--overwrite-report", action="store_true")
    return parser


def _mode(arguments: argparse.Namespace) -> str:
    return str(arguments.color)


def _hint(
    arguments: argparse.Namespace,
    text: str,
    *,
    stream: object = sys.stdout,
) -> None:
    if arguments.hints:
        print(
            hint_text(text, mode=_mode(arguments), stream=stream),
            file=stream,
        )


def _progress_callback(mode: str, colour_mode: str):
    if mode == "quiet":
        return None

    def emit(event: ProgressEvent) -> None:
        if mode == "jsonl":
            print(
                json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True),
                file=sys.stderr,
            )
            return
        amount = ""
        if event.current is not None:
            total = f"/{event.total}" if event.total is not None else ""
            amount = f" [{event.current}{total}]"
        prefix = paint(
            f"[{event.phase}:{event.kind}]",
            "cyan",
            mode=colour_mode,
            stream=sys.stderr,
        )
        print(f"{prefix} {event.message}{amount}", file=sys.stderr)

    return emit


def _write_json_atomic(
    path: Path,
    payload: dict[str, object],
    overwrite: bool,
) -> None:
    target = path.expanduser().resolve(strict=False)
    if target.exists() and not overwrite:
        raise FileExistsError(
            f"Bericht existiert bereits: {target}. Nutze --overwrite-report."
        )
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


def _run_explain(arguments: argparse.Namespace) -> int:
    if arguments.topic is None:
        topics = list_topics()
        if arguments.json:
            print(
                json.dumps(
                    [topic.to_dict() for topic in topics],
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        print("Verfügbare Hilfethemen:")
        for topic in topics:
            print(f"- {topic.name}: {topic.purpose}")
        _hint(arguments, "Details anzeigen: datenbanktool explain THEMA")
        return 0
    topic = get_topic(arguments.topic)
    if arguments.json:
        print(json.dumps(topic.to_dict(), ensure_ascii=False, indent=2))
        return 0
    print(paint(topic.title, "bold", mode=_mode(arguments)))
    print(f"Zweck: {topic.purpose}")
    print(f"Wirkung: {topic.effect}")
    print(f"Schreibt: {topic.writes}")
    print(f"Risiko: {topic.risk}")
    print(f"Sinnvoll wenn: {topic.use_when}")
    print(f"Beispiel: {topic.example}")
    return 0


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
    if report.errors:
        light = TrafficLight("red", "Fehler prüfen", f"{len(report.errors)} Lesefehler")
    elif report.truncated:
        light = TrafficLight("yellow", "Unvollständig", "Dateigrenze wurde erreicht")
    else:
        light = TrafficLight("green", "Scan abgeschlossen", "keine Lesefehler")
    print(traffic_text(light, mode=_mode(arguments)))
    print(f"Wurzel: {report.root}")
    print(
        f"Dateien: {len(report.files)} | "
        f"Gesamtgröße: {_human_size(report.total_size_bytes)}"
    )
    print(
        f"Große Dateien: {report.large_file_count} | "
        f"Duplikatgruppen: {len(report.duplicate_groups)}"
    )
    if arguments.json_path is not None:
        _write_json_atomic(
            arguments.json_path,
            report.to_dict(),
            arguments.overwrite_report,
        )
        print(f"JSON-Bericht: {arguments.json_path.expanduser()}")
    _hint(arguments, "Dieser Befehl liest Dateien nur. Änderungen erfolgen nicht.")
    return 1 if report.errors else 0


def _print_index_result(result: object, arguments: argparse.Namespace) -> None:
    print(f"Datenbank: {result.database}")
    print(f"Schema-Version: {result.schema_version} | Sitzung: {result.session_id}")
    print(
        f"Status: {status_text(result.status, mode=_mode(arguments))} | "
        f"Phase: {result.phase}"
    )
    print(
        f"Dateien: {result.imported_count} | Fehler: {result.error_count} | "
        f"Duplikatgruppen: {result.duplicate_group_count}"
    )
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
        progress_callback=_progress_callback(arguments.progress, _mode(arguments)),
    )
    _print_index_result(result, arguments)
    _hint(
        arguments,
        "Der Index wurde geschrieben; die gescannten Dateien wurden nur gelesen.",
    )
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
        progress_callback=_progress_callback(arguments.progress, _mode(arguments)),
    )
    _print_index_result(result, arguments)
    print(f"Vorheriger Scan: {result.baseline_session_id}")
    for key, amount in (
        ("added", result.added_count),
        ("modified", result.modified_count),
        ("moved", result.moved_count),
        ("removed", result.removed_count),
        ("unchanged", result.unchanged_count),
    ):
        print(
            f"{change_text(key, _CHANGE_LABELS[key], mode=_mode(arguments))}: "
            f"{amount}"
        )
    _hint(arguments, "Details anzeigen: datenbanktool index changes DATENBANK")
    return 0 if result.status == "complete" and result.error_count == 0 else 1


def _run_index_status(arguments: argparse.Namespace) -> int:
    status = inspect_index(arguments.database)
    print(f"Datenbank: {status.database} | Schema: {status.schema_version}")
    if status.session_id is None:
        print(
            traffic_text(
                TrafficLight("yellow", "Noch leer", "noch kein Scan gespeichert"),
                mode=_mode(arguments),
            )
        )
        return 0
    if status.status == "complete" and status.error_count == 0:
        light = TrafficLight("green", "Bereit", "letzter Scan ist vollständig")
    elif status.status in {"interrupted", "running"}:
        light = TrafficLight("yellow", "Prüfen", f"Status {status.status}")
    else:
        light = TrafficLight(
            "red",
            "Fehler prüfen",
            f"Status {status.status}, Fehler {status.error_count}",
        )
    print(traffic_text(light, mode=_mode(arguments)))
    print(
        f"Sitzung: {status.session_id} | Modus: {status.scan_mode} | "
        f"Vorheriger Scan: {status.parent_session_id or '-'}"
    )
    print(f"Ordner: {status.root}")
    print(
        f"Dateien: {status.imported_count} | Fehler: {status.error_count} | "
        f"Duplikatgruppen: {status.duplicate_group_count}"
    )
    return 0 if status.status in {None, "complete", "interrupted"} else 1


def _run_index_sessions(arguments: argparse.Namespace) -> int:
    sessions = list_sessions(
        arguments.database,
        limit=arguments.limit,
        status=arguments.status,
        root=arguments.root,
    )
    if arguments.json:
        print(
            json.dumps(
                [item.to_dict() for item in sessions],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if not sessions:
        print("Keine passenden Scans gefunden.")
        return 0
    for item in sessions:
        state = status_text(item.status, mode=_mode(arguments))
        changes = (
            f"neu={item.added_count}, geändert={item.modified_count}, "
            f"verschoben={item.moved_count}, entfernt={item.removed_count}, "
            f"unverändert={item.unchanged_count}"
        )
        print(
            f"#{item.session_id} | {item.scan_mode} | {state}/{item.phase} | "
            f"Dateien={item.imported_count} | Fehler={item.error_count} | "
            f"{changes} | {item.root}"
        )
    _hint(
        arguments,
        "Grün markierte vollständige Scans eignen sich als sichere Suchbasis.",
    )
    return 0


def _effective_search_filter(arguments: argparse.Namespace) -> SearchFilter:
    base = (
        get_preset(arguments.preset, arguments.preset_file).filters
        if arguments.preset
        else SearchFilter()
    )
    mib = 1024 * 1024
    return SearchFilter(
        text=arguments.text if arguments.text is not None else base.text,
        categories=(
            tuple(arguments.category)
            if arguments.category is not None
            else base.categories
        ),
        min_size_bytes=(
            arguments.min_size_mib * mib
            if arguments.min_size_mib is not None
            else base.min_size_bytes
        ),
        max_size_bytes=(
            arguments.max_size_mib * mib
            if arguments.max_size_mib is not None
            else base.max_size_bytes
        ),
        naming_warning_only=(
            arguments.name_warning_only
            if arguments.name_warning_only is not None
            else base.naming_warning_only
        ),
        duplicate_only=(
            arguments.duplicates_only
            if arguments.duplicates_only is not None
            else base.duplicate_only
        ),
        page=arguments.page,
        page_size=(
            arguments.page_size
            if arguments.page_size is not None
            else base.page_size
        ),
        sort_by=arguments.sort if arguments.sort is not None else base.sort_by,
        descending=(
            arguments.descending
            if arguments.descending is not None
            else base.descending
        ),
        fulltext_mode=(
            arguments.fulltext
            if arguments.fulltext is not None
            else base.fulltext_mode
        ),
    )


def _run_index_search(arguments: argparse.Namespace) -> int:
    if arguments.build_fulltext_index:
        built = build_fulltext_index(
            arguments.database,
            session_id=arguments.session_id,
            lock_timeout_seconds=arguments.lock_timeout,
        )
        stream = sys.stderr if arguments.json else sys.stdout
        print(
            status_text(
                f"Schneller Suchindex: {built.indexed_files} Dateien",
                mode=_mode(arguments),
                stream=stream,
            ),
            file=stream,
        )
    filters = _effective_search_filter(arguments)
    page = search_index(
        arguments.database,
        session_id=arguments.session_id,
        filters=filters,
    )
    if arguments.json:
        print(json.dumps(page.to_dict(), ensure_ascii=False, indent=2))
        return 0
    search_kind = (
        "schnelle Volltextsuche" if page.engine == "fts5" else "normale Suche"
    )
    print(
        f"Ordner: {page.root} | Scan: #{page.session_id} | Suchart: {search_kind}"
    )
    print(f"Treffer: {page.total_rows} | Seite {page.page} von {page.total_pages}")
    if arguments.preset:
        print(paint(f"Vorlage: {arguments.preset}", "blue", mode=_mode(arguments)))
    if not page.rows:
        print(
            traffic_text(
                TrafficLight("yellow", "Keine Treffer", "Filter oder Suchwort prüfen"),
                mode=_mode(arguments),
            )
        )
        return 0
    for row in page.rows:
        if row.filename_warnings and row.duplicate_sha256:
            light = TrafficLight(
                "red",
                "Mehrfach prüfen",
                "Namenshinweis und Duplikat",
            )
        elif row.filename_warnings:
            light = TrafficLight("yellow", "Name prüfen", "auffälliger Dateiname")
        elif row.duplicate_sha256:
            light = TrafficLight(
                "yellow",
                "Duplikat prüfen",
                "Datei gehört zu einer Duplikatgruppe",
            )
        else:
            light = TrafficLight(
                "green",
                "Unauffällig",
                "keine erkannten Hinweise",
            )
        print(
            f"{traffic_text(light, mode=_mode(arguments))}\n"
            f"  {row.relative_path} | {row.category} | "
            f"{_human_size(row.size_bytes)}"
        )
    if page.page < page.total_pages:
        print(f"Nächste Seite: --page {page.page + 1}")
    _hint(
        arguments,
        "Suchvorlage speichern: datenbanktool index presets save NAME ...",
    )
    return 0


def _run_index_folders(arguments: argparse.Namespace) -> int:
    has_export = any((arguments.json_path, arguments.html_path))
    if arguments.no_terminal and not has_export:
        raise ValueError("Ohne Terminalanzeige muss JSON oder HTML gewählt werden")
    mib = 1024 * 1024
    page = analyse_folders(
        arguments.database,
        session_id=arguments.session_id,
        filters=FolderFilter(
            contains=arguments.contains,
            min_files=arguments.min_files,
            min_size_bytes=arguments.min_size_mib * mib,
            max_depth=arguments.max_depth,
            page=arguments.page,
            page_size=arguments.page_size,
            sort_by=arguments.sort,
            descending=arguments.descending,
            top_files=arguments.top_files,
            attention_file_bytes=arguments.attention_file_mib * mib,
        ),
    )
    if not arguments.no_terminal:
        print(f"Ordner: {page.root} | Scan: #{page.session_id}")
        print(f"Treffer: {page.total_rows} | Seite {page.page} von {page.total_pages}")
        if not page.rows:
            print(
                traffic_text(
                    TrafficLight("yellow", "Keine Ordner", "Filter prüfen"),
                    mode=_mode(arguments),
                )
            )
        for row in page.rows:
            print(traffic_text(row.traffic_light, mode=_mode(arguments)))
            print(
                f"  {row.folder} | direkt {row.direct_files} Datei(en), "
                f"mit Unterordnern {row.total_files} | "
                f"{_human_size(row.total_size_bytes)} | "
                f"Namenshinweise {row.warning_files} | "
                f"Duplikate {row.duplicate_files}"
            )
            for largest in row.largest_files:
                print(
                    f"    ↳ {_human_size(largest.size_bytes)} · "
                    f"{largest.relative_path}"
                )
        if page.page < page.total_pages:
            print(f"Nächste Seite: --page {page.page + 1}")
        _hint(
            arguments,
            "Ampeln zeigen Prüfbedarf. Sie sind keine Aussage über "
            "Beschädigung oder Gefährlichkeit.",
        )
    if arguments.json_path:
        print(
            "JSON-Bericht: "
            + export_folder_json(
                page,
                arguments.json_path,
                overwrite=arguments.overwrite_report,
            )
        )
    if arguments.html_path:
        print(
            "HTML-Bericht: "
            + export_folder_html(
                page,
                arguments.html_path,
                overwrite=arguments.overwrite_report,
            )
        )
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
    has_export = any(
        (arguments.json_path, arguments.csv_path, arguments.html_path)
    )
    if arguments.no_terminal and not has_export:
        raise ValueError(
            "Ohne Terminalanzeige muss mindestens JSON, CSV oder HTML gewählt werden"
        )
    page = query_changes(
        arguments.database,
        session_id=arguments.session_id,
        filters=filters,
    )
    if not arguments.no_terminal:
        print(
            f"Re-Scan: #{page.session_id} | "
            f"Vorheriger Scan: #{page.baseline_session_id}"
        )
        print(
            f"Ordner: {page.root} | Treffer: {page.total_rows} | "
            f"Seite {page.page} von {page.total_pages}"
        )
        for key in _CHANGE_TYPES:
            print(
                f"{change_text(key, _CHANGE_LABELS[key], mode=_mode(arguments))}: "
                f"{page.counts[key]}"
            )
        if not page.rows:
            print("Keine passenden Änderungen gefunden.")
        for row in page.rows:
            old_path = row.old_path or "–"
            new_path = row.new_path or "–"
            label = change_text(
                row.change_type,
                _CHANGE_LABELS[row.change_type],
                mode=_mode(arguments),
            )
            print(
                f"[{label}] {old_path} → {new_path} | "
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


def _preset_filter(arguments: argparse.Namespace) -> SearchFilter:
    mib = 1024 * 1024
    return SearchFilter(
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
        page=1,
        page_size=arguments.page_size,
        sort_by=arguments.sort,
        descending=arguments.descending,
        fulltext_mode=arguments.fulltext,
    )


def _run_index_presets(arguments: argparse.Namespace) -> int:
    if arguments.preset_command == "list":
        presets = list_presets(arguments.preset_file)
        if arguments.json:
            print(
                json.dumps(
                    [item.to_dict() for item in presets],
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if not presets:
            print(
                traffic_text(
                    TrafficLight(
                        "yellow",
                        "Noch leer",
                        "keine Suchvorlagen gespeichert",
                    ),
                    mode=_mode(arguments),
                )
            )
            _hint(
                arguments,
                "Speichern: datenbanktool index presets save NAME ...",
            )
            return 0
        for preset in presets:
            description = f" – {preset.description}" if preset.description else ""
            print(
                f"{paint('●', 'green', mode=_mode(arguments))} "
                f"{preset.name}{description}"
            )
        return 0
    if arguments.preset_command == "show":
        preset = get_preset(arguments.name, arguments.preset_file)
        if arguments.json:
            print(json.dumps(preset.to_dict(), ensure_ascii=False, indent=2))
            return 0
        print(paint(preset.name, "bold", mode=_mode(arguments)))
        print(f"Beschreibung: {preset.description or 'keine'}")
        print(f"Suchwort: {preset.filters.text or 'keines'}")
        print(f"Dateitypen: {', '.join(preset.filters.categories) or 'alle'}")
        print(
            f"Größe: {preset.filters.min_size_bytes or 0} bis "
            f"{preset.filters.max_size_bytes or 'offen'} Byte"
        )
        print(
            "Nur Namenshinweise: "
            f"{'ja' if preset.filters.naming_warning_only else 'nein'}"
        )
        print(
            f"Nur Duplikate: {'ja' if preset.filters.duplicate_only else 'nein'}"
        )
        print(
            f"Sortierung: {preset.filters.sort_by} | "
            f"Seitengröße: {preset.filters.page_size}"
        )
        _hint(
            arguments,
            f"Starten: datenbanktool index search DATENBANK "
            f"--preset \"{preset.name}\"",
        )
        return 0
    if arguments.preset_command == "save":
        preset = save_preset(
            arguments.name,
            _preset_filter(arguments),
            description=arguments.description,
            path=arguments.preset_file,
            replace=arguments.replace,
        )
        print(
            traffic_text(
                TrafficLight("green", "Vorlage gespeichert", preset.name),
                mode=_mode(arguments),
            )
        )
        _hint(
            arguments,
            f"Starten: datenbanktool index search DATENBANK "
            f"--preset \"{preset.name}\"",
        )
        return 0
    if arguments.preset_command == "delete":
        if not arguments.yes:
            raise ValueError("Löschen benötigt die ausdrückliche Bestätigung --yes")
        deleted = delete_preset(arguments.name, path=arguments.preset_file)
        print(
            traffic_text(
                TrafficLight("yellow", "Vorlage gelöscht", deleted.name),
                mode=_mode(arguments),
            )
        )
        return 0
    raise ValueError("Unbekannter Suchvorlagen-Befehl")


def _run_index_backup(arguments: argparse.Namespace) -> int:
    result = backup_index(
        arguments.database,
        arguments.output,
        overwrite=arguments.overwrite,
        lock_timeout_seconds=arguments.lock_timeout,
    )
    print(
        traffic_text(
            TrafficLight(
                "green",
                "Sicherung geprüft",
                ", ".join(result.integrity),
            ),
            mode=_mode(arguments),
        )
    )
    print(
        f"Datenbank: {result.database}\nSicherung: {result.backup}\n"
        f"Schema: {result.schema_version} | Größe: {_human_size(result.size_bytes)}"
    )
    return 0


def _run_index_restore(arguments: argparse.Namespace) -> int:
    result = restore_index(
        arguments.database,
        arguments.backup,
        create_safety_backup=not arguments.without_safety_backup,
        lock_timeout_seconds=arguments.lock_timeout,
    )
    level = "green" if result.successful else "red"
    label = (
        "Wiederherstellung erfolgreich"
        if result.successful
        else "Wiederherstellung fehlgeschlagen"
    )
    print(
        traffic_text(
            TrafficLight(level, label, ", ".join(result.integrity)),
            mode=_mode(arguments),
        )
    )
    print(
        f"Datenbank: {result.database}\nQuelle: {result.restored_from}\n"
        f"Rückfallsicherung: {result.safety_backup or 'bewusst deaktiviert'}"
    )
    if arguments.without_safety_backup:
        _hint(
            arguments,
            "Die Rückfallsicherung war deaktiviert. "
            "Diese Option nur bewusst verwenden.",
        )
    return 0 if result.successful else 1


def _run_index_repair(arguments: argparse.Namespace) -> int:
    result = repair_index(
        arguments.database,
        create_backup=not arguments.without_backup,
        vacuum=arguments.vacuum,
        lock_timeout_seconds=arguments.lock_timeout,
    )
    level = "green" if result.successful else "red"
    label = "Reparatur erfolgreich" if result.successful else "Reparatur nicht vollständig"
    print(
        traffic_text(
            TrafficLight(level, label, ", ".join(result.after_integrity)),
            mode=_mode(arguments),
        )
    )
    print(
        f"Sicherheitskopie: {result.backup or 'bewusst deaktiviert'} | "
        f"Fremdschlüsselfehler: {result.foreign_key_errors}"
    )
    for action in result.actions:
        print(f"- {action}")
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
    print(
        traffic_text(
            TrafficLight(
                "green",
                "Bericht erstellt",
                f"{result.row_count} Dateien",
            ),
            mode=_mode(arguments),
        )
    )
    if result.csv_path:
        print(f"CSV-Bericht: {result.csv_path}")
    if result.html_path:
        print(f"HTML-Bericht: {result.html_path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "explain":
            return _run_explain(arguments)
        if arguments.command == "scan":
            return _run_scan(arguments)
        if arguments.command == "index":
            handlers = {
                "build": _run_index_build,
                "rescan": _run_index_rescan,
                "status": _run_index_status,
                "sessions": _run_index_sessions,
                "search": _run_index_search,
                "folders": _run_index_folders,
                "changes": _run_index_changes,
                "presets": _run_index_presets,
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
        KeyError,
        NotADirectoryError,
        OSError,
        sqlite3.Error,
        ValueError,
    ) as error:
        message = paint(
            f"Fehler: {error}",
            "red",
            mode=getattr(arguments, "color", "auto"),
            stream=sys.stderr,
        )
        print(message, file=sys.stderr)
        return 2
    parser.error("Unbekannter Befehl")
    return 2
