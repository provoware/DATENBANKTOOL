from __future__ import annotations

import argparse
import json
from pathlib import Path

from datenbanktool.cli_common import (
    CHANGE_LABELS,
    add_progress_options,
    add_scan_options,
    colour_mode,
    human_size,
    non_negative_float,
    non_negative_int,
    positive_int,
    print_hint,
    progress_callback,
)
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.incremental import IncrementalScanOptions, incremental_rescan
from datenbanktool.core.index_admin import backup_index, list_sessions, restore_index
from datenbanktool.core.index_database import (
    IndexBuildOptions,
    build_index,
    inspect_index,
    repair_index,
)
from datenbanktool.core.presentation import (
    TrafficLight,
    change_text,
    status_text,
    traffic_text,
)


def _add_autosave_option(target: argparse.ArgumentParser) -> None:
    target.add_argument(
        "--autosave-seconds",
        type=non_negative_float,
        default=5.0,
        help=(
            "Spätestens nach so vielen Sekunden den sicheren Zwischenstand speichern. "
            "Standard: 5. (Technisch: WAL-Checkpoint zusätzlich zur Dateimenge.)"
        ),
    )


def register_scan_index_parsers(
    index_subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    build = index_subparsers.add_parser(
        "build",
        help="Ordnerliste neu anlegen oder sicher fortsetzen",
        description=(
            "Liest einen Ordner und merkt sich eine durchsuchbare Dateiliste. "
            "Die Dateien selbst bleiben unverändert. (Technisch: SQLite-Snapshot.)"
        ),
        epilog=(
            "Autosave speichert spätestens nach der gewählten Zeit oder nach der "
            "gewählten Dateimenge – je nachdem, was zuerst eintritt."
        ),
    )
    add_scan_options(build)
    build.add_argument("--database", type=Path, required=True)
    build.add_argument(
        "--batch-size",
        type=positive_int,
        default=500,
        help="Spätestens nach dieser Dateimenge zwischenspeichern. Standard: 500.",
    )
    _add_autosave_option(build)
    build.add_argument(
        "--resume",
        action="store_true",
        help="Am letzten bestätigten Zwischenstand weiterarbeiten.",
    )
    add_progress_options(build)
    bind_handler(
        build,
        run_build,
        CommandPolicy(
            "index.build",
            reads_original_files=True,
            writes_index=True,
        ),
    )

    rescan = index_subparsers.add_parser(
        "rescan",
        help="Nachsehen, was sich seit der letzten Prüfung geändert hat",
        description=(
            "Erstellt einen neuen sicheren Stand und vergleicht ihn mit einem früheren. "
            "(Technisch: inkrementeller Snapshot.)"
        ),
        epilog="Schreibt nur in die Indexdatei; persönliche Dateien werden gelesen, nicht verändert.",
    )
    rescan.add_argument("path", type=Path)
    rescan.add_argument("--database", type=Path, required=True)
    rescan.add_argument("--baseline-session-id", type=positive_int)
    rescan.add_argument(
        "--hash-duplicates",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Ohne Angabe wird die Einstellung der vorherigen Prüfung übernommen.",
    )
    rescan.add_argument("--large-file-mib", type=non_negative_int, default=None)
    rescan.add_argument(
        "--follow-symlinks",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Verknüpften Ordnern folgen. Aus Sicherheitsgründen normalerweise aus.",
    )
    rescan.add_argument(
        "--detect-moves-by-hash",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Verschobene Dateien zusätzlich über ihre Inhaltsprüfsumme erkennen.",
    )
    rescan.add_argument(
        "--batch-size",
        type=positive_int,
        default=500,
        help="Spätestens nach dieser Dateimenge zwischenspeichern. Standard: 500.",
    )
    _add_autosave_option(rescan)
    rescan.add_argument(
        "--resume",
        action="store_true",
        help="Am letzten bestätigten Zwischenstand weiterarbeiten.",
    )
    rescan.add_argument("--max-files", type=positive_int, default=None)
    add_progress_options(rescan)
    bind_handler(
        rescan,
        run_rescan,
        CommandPolicy(
            "index.rescan",
            reads_original_files=True,
            writes_index=True,
        ),
    )

    status = index_subparsers.add_parser(
        "status",
        help="Zeigen, ob die letzte Prüfung fertig oder unterbrochen ist",
    )
    status.add_argument("database", type=Path)
    bind_handler(status, run_status, CommandPolicy("index.status"))

    sessions = index_subparsers.add_parser(
        "sessions",
        help="Gespeicherte Prüfstände auflisten",
    )
    sessions.add_argument("database", type=Path)
    sessions.add_argument("--limit", type=positive_int, default=20)
    sessions.add_argument(
        "--status",
        choices=("running", "interrupted", "complete", "failed"),
    )
    sessions.add_argument("--root", type=Path)
    sessions.add_argument("--json", action="store_true")
    bind_handler(sessions, run_sessions, CommandPolicy("index.sessions"))


def register_admin_parsers(
    index_subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    backup = index_subparsers.add_parser(
        "backup",
        help="Geprüfte Sicherung der Indexdatei erstellen",
    )
    backup.add_argument("database", type=Path)
    backup.add_argument("--output", type=Path)
    backup.add_argument("--overwrite", action="store_true")
    backup.add_argument("--lock-timeout", type=non_negative_float, default=0.0)
    bind_handler(
        backup,
        run_backup,
        CommandPolicy("index.backup", writes_backups=True),
    )

    restore = index_subparsers.add_parser(
        "restore",
        help="Geprüfte Sicherung zurückholen",
    )
    restore.add_argument("database", type=Path)
    restore.add_argument("--backup", type=Path, required=True)
    restore.add_argument("--without-safety-backup", action="store_true")
    restore.add_argument("--lock-timeout", type=non_negative_float, default=0.0)
    bind_handler(
        restore,
        run_restore,
        CommandPolicy("index.restore", writes_index=True),
    )

    repair = index_subparsers.add_parser(
        "repair",
        help="Indexdatei prüfen und sicher reparieren",
    )
    repair.add_argument("database", type=Path)
    repair.add_argument("--vacuum", action="store_true")
    repair.add_argument("--without-backup", action="store_true")
    repair.add_argument("--lock-timeout", type=non_negative_float, default=0.0)
    bind_handler(
        repair,
        run_repair,
        CommandPolicy("index.repair", writes_index=True),
    )


def _print_index_result(result: object, arguments: argparse.Namespace) -> None:
    print(f"Gespeicherte Übersicht: {result.database}")
    print(f"Prüfung: #{result.session_id} | Datenbankversion: {result.schema_version}")
    print(
        f"Ergebnis: {status_text(result.status, mode=colour_mode(arguments))} | "
        f"Arbeitsabschnitt: {result.phase}"
    )
    print(
        f"Erfasste Dateien: {result.imported_count} | Hinweise/Fehler: {result.error_count} | "
        f"Gruppen gleicher Dateien: {result.duplicate_group_count}"
    )
    print(f"Am Zwischenstand fortgesetzt: {'ja' if result.resumed else 'nein'}")


def run_build(arguments: argparse.Namespace) -> int:
    result = build_index(
        IndexBuildOptions(
            root=arguments.path,
            database=arguments.database,
            hash_duplicates=arguments.hash_duplicates,
            large_file_bytes=arguments.large_file_mib * 1024 * 1024,
            follow_symlinks=arguments.follow_symlinks,
            batch_size=arguments.batch_size,
            autosave_seconds=arguments.autosave_seconds,
            resume=arguments.resume,
            max_files=arguments.max_files,
            lock_timeout_seconds=arguments.lock_timeout,
        ),
        progress_callback=progress_callback(
            arguments.progress,
            colour_mode(arguments),
        ),
    )
    _print_index_result(result, arguments)
    print_hint(
        arguments,
        "Die Dateiliste wurde gespeichert; persönliche Dateien wurden nur gelesen. "
        "Bei Abbruch erneut mit --resume starten.",
    )
    return 0 if result.status == "complete" and result.error_count == 0 else 1


def run_rescan(arguments: argparse.Namespace) -> int:
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
            autosave_seconds=arguments.autosave_seconds,
            resume=arguments.resume,
            max_files=arguments.max_files,
            lock_timeout_seconds=arguments.lock_timeout,
        ),
        progress_callback=progress_callback(
            arguments.progress,
            colour_mode(arguments),
        ),
    )
    _print_index_result(result, arguments)
    print(f"Verglichen mit Prüfung: #{result.baseline_session_id}")
    for key, amount in (
        ("added", result.added_count),
        ("modified", result.modified_count),
        ("moved", result.moved_count),
        ("removed", result.removed_count),
        ("unchanged", result.unchanged_count),
    ):
        print(
            f"{change_text(key, CHANGE_LABELS[key], mode=colour_mode(arguments))}: "
            f"{amount}"
        )
    print_hint(arguments, "Einzelheiten: datenbanktool index changes DATENBANK")
    return 0 if result.status == "complete" and result.error_count == 0 else 1


def run_status(arguments: argparse.Namespace) -> int:
    status = inspect_index(arguments.database)
    print(f"Gespeicherte Übersicht: {status.database}")
    if status.session_id is None:
        print(
            traffic_text(
                TrafficLight("yellow", "Noch leer", "noch keine Ordnerprüfung gespeichert"),
                mode=colour_mode(arguments),
            )
        )
        return 0
    if status.status == "complete" and status.error_count == 0:
        light = TrafficLight("green", "Fertig und nutzbar", "letzte Prüfung vollständig")
    elif status.status in {"interrupted", "running"}:
        light = TrafficLight(
            "yellow",
            "Fortsetzung möglich",
            f"gespeicherter Zustand: {status.status}; mit --resume weiterarbeiten",
        )
    else:
        light = TrafficLight(
            "red",
            "Prüfung nötig",
            f"Zustand {status.status}, Hinweise/Fehler {status.error_count}",
        )
    print(traffic_text(light, mode=colour_mode(arguments)))
    print(
        f"Prüfung: #{status.session_id} | Art: {status.scan_mode} | "
        f"Früherer Stand: {status.parent_session_id or '-'}"
    )
    print(f"Ordner: {status.root}")
    print(
        f"Dateien: {status.imported_count} | Hinweise/Fehler: {status.error_count} | "
        f"Gruppen gleicher Dateien: {status.duplicate_group_count}"
    )
    return 0 if status.status in {None, "complete", "interrupted"} else 1


def run_sessions(arguments: argparse.Namespace) -> int:
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
        print("Keine passenden gespeicherten Prüfungen gefunden.")
        return 0
    for item in sessions:
        state = status_text(item.status, mode=colour_mode(arguments))
        changes = (
            f"neu={item.added_count}, geändert={item.modified_count}, "
            f"verschoben={item.moved_count}, entfernt={item.removed_count}, "
            f"gleich={item.unchanged_count}"
        )
        print(
            f"#{item.session_id} | {item.scan_mode} | {state}/{item.phase} | "
            f"Dateien={item.imported_count} | Hinweise={item.error_count} | "
            f"{changes} | {item.root}"
        )
    print_hint(
        arguments,
        "Vollständig abgeschlossene Prüfungen sind die sichere Grundlage für Suche und Berichte.",
    )
    return 0


def run_backup(arguments: argparse.Namespace) -> int:
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
                "Sicherung geprüft und nutzbar",
                ", ".join(result.integrity),
            ),
            mode=colour_mode(arguments),
        )
    )
    print(
        f"Indexdatei: {result.database}\nSicherung: {result.backup}\n"
        f"Datenbankversion: {result.schema_version} | Größe: {human_size(result.size_bytes)}"
    )
    return 0


def run_restore(arguments: argparse.Namespace) -> int:
    result = restore_index(
        arguments.database,
        arguments.backup,
        create_safety_backup=not arguments.without_safety_backup,
        lock_timeout_seconds=arguments.lock_timeout,
    )
    level = "green" if result.successful else "red"
    label = "Sicherung erfolgreich zurückgeholt" if result.successful else "Zurückholen fehlgeschlagen"
    print(
        traffic_text(
            TrafficLight(level, label, ", ".join(result.integrity)),
            mode=colour_mode(arguments),
        )
    )
    print(
        f"Indexdatei: {result.database}\nQuelle: {result.restored_from}\n"
        f"Rückfallsicherung: {result.safety_backup or 'bewusst deaktiviert'}"
    )
    if arguments.without_safety_backup:
        print_hint(
            arguments,
            "Die zusätzliche Rückfallsicherung war deaktiviert. Diese Option nur bewusst verwenden.",
        )
    return 0 if result.successful else 1


def run_repair(arguments: argparse.Namespace) -> int:
    result = repair_index(
        arguments.database,
        create_backup=not arguments.without_backup,
        vacuum=arguments.vacuum,
        lock_timeout_seconds=arguments.lock_timeout,
    )
    level = "green" if result.successful else "red"
    label = "Indexdatei erfolgreich repariert" if result.successful else "Reparatur nicht vollständig"
    print(
        traffic_text(
            TrafficLight(level, label, ", ".join(result.after_integrity)),
            mode=colour_mode(arguments),
        )
    )
    print(
        f"Sicherheitskopie: {result.backup or 'bewusst deaktiviert'} | "
        f"Verknüpfungsfehler: {result.foreign_key_errors}"
    )
    for action in result.actions:
        print(f"- {action}")
    return 0 if result.successful else 1
