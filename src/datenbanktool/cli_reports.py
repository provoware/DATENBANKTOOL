from __future__ import annotations

import argparse
from pathlib import Path

from datenbanktool.cli_common import (
    CHANGE_LABELS,
    CHANGE_TYPES,
    add_category_filter,
    colour_mode,
    human_size,
    non_negative_int,
    positive_int,
    print_hint,
)
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.changes import ChangeFilter, export_changes, query_changes
from datenbanktool.core.folders import (
    FolderFilter,
    analyse_folders,
    export_folder_html,
    export_folder_json,
)
from datenbanktool.core.presentation import (
    TrafficLight,
    change_text,
    traffic_text,
)
from datenbanktool.core.reports import ReportFilter, export_reports


def register_index_report_parsers(
    index_subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
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
    folders.add_argument("--session-id", type=positive_int)
    folders.add_argument("--contains", default="", help="Nur Ordnerpfade mit diesem Text")
    folders.add_argument("--min-files", type=positive_int, default=1)
    folders.add_argument("--min-size-mib", type=non_negative_int, default=0)
    folders.add_argument("--max-depth", type=non_negative_int)
    folders.add_argument("--page", type=positive_int, default=1)
    folders.add_argument("--page-size", type=positive_int, default=25)
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
    folders.add_argument("--top-files", type=positive_int, default=3)
    folders.add_argument(
        "--attention-file-mib",
        type=positive_int,
        default=1024,
        help="Ab dieser Einzeldateigröße wechselt die Ampel mindestens auf Gelb.",
    )
    folders.add_argument("--json", dest="json_path", type=Path)
    folders.add_argument("--html", dest="html_path", type=Path)
    folders.add_argument("--overwrite-report", action="store_true")
    folders.add_argument("--no-terminal", action="store_true")
    bind_handler(
        folders,
        run_folders,
        CommandPolicy("index.folders", writes_reports=True),
    )

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
    changes.add_argument("--session-id", type=positive_int)
    changes.add_argument(
        "--type",
        dest="change_types",
        action="append",
        default=[],
        choices=CHANGE_TYPES,
    )
    add_category_filter(changes, default=[])
    changes.add_argument("--contains", default="")
    changes.add_argument("--page", type=positive_int, default=1)
    changes.add_argument("--page-size", type=positive_int, default=25)
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
    bind_handler(
        changes,
        run_changes,
        CommandPolicy("index.changes", writes_reports=True),
    )


def register_report_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    report = subparsers.add_parser(
        "report",
        help="Gefilterte CSV-/HTML-Dateiliste erzeugen",
    )
    report.add_argument("database", type=Path)
    report.add_argument("--session-id", type=positive_int)
    report.add_argument("--csv", dest="csv_path", type=Path)
    report.add_argument("--html", dest="html_path", type=Path)
    add_category_filter(report, default=[])
    report.add_argument("--min-size-mib", type=non_negative_int)
    report.add_argument("--max-size-mib", type=non_negative_int)
    report.add_argument("--name-warning-only", action="store_true")
    report.add_argument("--duplicates-only", action="store_true")
    report.add_argument("--overwrite-report", action="store_true")
    bind_handler(
        report,
        run_report,
        CommandPolicy("report", writes_reports=True),
    )


def run_folders(arguments: argparse.Namespace) -> int:
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
                    mode=colour_mode(arguments),
                )
            )
        for row in page.rows:
            print(traffic_text(row.traffic_light, mode=colour_mode(arguments)))
            print(
                f"  {row.folder} | direkt {row.direct_files} Datei(en), "
                f"mit Unterordnern {row.total_files} | "
                f"{human_size(row.total_size_bytes)} | "
                f"Namenshinweise {row.warning_files} | "
                f"Duplikate {row.duplicate_files}"
            )
            for largest in row.largest_files:
                print(
                    f"    ↳ {human_size(largest.size_bytes)} · "
                    f"{largest.relative_path}"
                )
        if page.page < page.total_pages:
            print(f"Nächste Seite: --page {page.page + 1}")
        print_hint(
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


def run_changes(arguments: argparse.Namespace) -> int:
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
        for key in CHANGE_TYPES:
            print(
                f"{change_text(key, CHANGE_LABELS[key], mode=colour_mode(arguments))}: "
                f"{page.counts[key]}"
            )
        if not page.rows:
            print("Keine passenden Änderungen gefunden.")
        for row in page.rows:
            old_path = row.old_path or "–"
            new_path = row.new_path or "–"
            label = change_text(
                row.change_type,
                CHANGE_LABELS[row.change_type],
                mode=colour_mode(arguments),
            )
            print(
                f"[{label}] {old_path} → {new_path} | "
                f"{row.category} | {human_size(row.size_bytes)}"
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


def run_report(arguments: argparse.Namespace) -> int:
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
            mode=colour_mode(arguments),
        )
    )
    if result.csv_path:
        print(f"CSV-Bericht: {result.csv_path}")
    if result.html_path:
        print(f"HTML-Bericht: {result.html_path}")
    return 0
