from __future__ import annotations

import argparse
from pathlib import Path

from datenbanktool.cli_common import colour_mode, human_size, positive_int, print_hint
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.folder_timeline import (
    FolderTimelineOptions,
    build_folder_timeline,
)
from datenbanktool.core.folder_timeline_exports import export_folder_timeline
from datenbanktool.core.presentation import traffic_text


def register_folder_timeline_parser(
    index_subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    timeline = index_subparsers.add_parser(
        "folder-timeline",
        help="Größe und Dateizahl eines Ordners über mehrere Scans anzeigen",
        description=(
            "Zeigt eine rein lesende Zeitreihe für einen relativen Ordnerpfad. "
            "Berücksichtigt abgeschlossene Scans desselben Stammordners und zählt "
            "Dateien einschließlich Unterordnern."
        ),
        epilog=(
            "Auswirkung: SQLite und Originaldateien werden nur gelesen. "
            "Nur ausdrücklich gewählte JSON-, CSV- oder HTML-Berichte werden geschrieben."
        ),
    )
    timeline.add_argument("database", type=Path)
    timeline.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Relativer Ordnerpfad im Scan; Standard ist der Stammordner '.'",
    )
    timeline.add_argument(
        "--from-session-id",
        type=positive_int,
        help="Älteste einzubeziehende abgeschlossene Sitzung",
    )
    timeline.add_argument(
        "--to-session-id",
        type=positive_int,
        help="Neueste einzubeziehende Sitzung; Standard ist der neueste Scan",
    )
    timeline.add_argument(
        "--limit",
        type=positive_int,
        default=100,
        help="Höchstens so viele neueste Zeitpunkte anzeigen, 2 bis 500",
    )
    timeline.add_argument("--json", dest="json_path", type=Path)
    timeline.add_argument("--csv", dest="csv_path", type=Path)
    timeline.add_argument("--html", dest="html_path", type=Path)
    timeline.add_argument("--overwrite-report", action="store_true")
    timeline.add_argument("--no-terminal", action="store_true")
    bind_handler(
        timeline,
        run_folder_timeline,
        CommandPolicy("index.folder-timeline", writes_reports=True),
    )


def _signed_size(value: int | None) -> str:
    if value is None:
        return "–"
    if value == 0:
        return "0 B"
    return ("+" if value > 0 else "−") + human_size(abs(value))


def run_folder_timeline(arguments: argparse.Namespace) -> int:
    has_export = any((arguments.json_path, arguments.csv_path, arguments.html_path))
    if arguments.no_terminal and not has_export:
        raise ValueError(
            "Ohne Terminalanzeige muss mindestens JSON, CSV oder HTML gewählt werden"
        )
    timeline = build_folder_timeline(
        arguments.database,
        options=FolderTimelineOptions(
            folder=arguments.folder,
            from_session_id=arguments.from_session_id,
            to_session_id=arguments.to_session_id,
            limit=arguments.limit,
        ),
    )
    if not arguments.no_terminal:
        print(f"Stammordner: {timeline.root}")
        print(
            f"Ordner-Zeitreihe: {timeline.folder} | "
            f"Scans #{timeline.first_session_id} bis #{timeline.last_session_id} | "
            f"Zeitpunkte: {len(timeline.points)}"
        )
        if timeline.truncated:
            print(
                f"Hinweis: Neueste {len(timeline.points)} von "
                f"{timeline.total_available_sessions} passenden Scans."
            )
        print(
            f"Gesamtänderung: Dateien {timeline.net_file_delta:+d} | "
            f"Größe {_signed_size(timeline.net_size_delta_bytes)} | "
            f"Minimum {human_size(timeline.minimum_size_bytes)} | "
            f"Maximum {human_size(timeline.maximum_size_bytes)}"
        )
        for point in timeline.points:
            percent = (
                "–"
                if point.size_delta_percent is None
                else f"{point.size_delta_percent:+.2f} %"
            )
            file_delta = "–" if point.file_delta is None else f"{point.file_delta:+d}"
            print(traffic_text(point.traffic_light, mode=colour_mode(arguments)))
            print(
                f"  Scan #{point.session_id} | {point.recorded_utc} | "
                f"{point.scan_mode} | Dateien {point.file_count} ({file_delta}) | "
                f"Größe {human_size(point.size_bytes)} "
                f"({_signed_size(point.size_delta_bytes)}, {percent})"
            )
        print_hint(
            arguments,
            "Die Zeitreihe liest gespeicherte Scans. Elternordner enthalten "
            "bewusst die Werte ihrer Unterordner.",
        )
    if has_export:
        exported = export_folder_timeline(
            timeline,
            json_path=arguments.json_path,
            csv_path=arguments.csv_path,
            html_path=arguments.html_path,
            overwrite=arguments.overwrite_report,
        )
        print(f"Exportierte Zeitpunkte: {exported.row_count}")
        if exported.json_path:
            print(f"JSON-Bericht: {exported.json_path}")
        if exported.csv_path:
            print(f"CSV-Bericht: {exported.csv_path}")
        if exported.html_path:
            print(f"HTML-Bericht: {exported.html_path}")
    return 0
