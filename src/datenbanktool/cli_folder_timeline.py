from __future__ import annotations

import argparse
from pathlib import Path

from datenbanktool.cli_common import (
    colour_mode,
    human_size,
    non_negative_float,
    positive_int,
    print_hint,
)
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.folder_timeline import (
    FolderTimelineOptions,
    build_folder_timeline,
)
from datenbanktool.core.folder_timeline_exports import export_folder_timeline
from datenbanktool.core.presentation import traffic_text
from datenbanktool.core.timeline_presets import get_timeline_preset


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
            "Trendgrenzen markieren ausschließlich auffälliges Wachstum. "
            "Nur gewählte JSON-, CSV- oder HTML-Berichte werden geschrieben."
        ),
    )
    timeline.add_argument("database", type=Path)
    timeline.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="Relativer Ordnerpfad im Scan; Standard ist der Stammordner '.'",
    )
    timeline.add_argument(
        "--preset",
        help="Gespeicherte Zeitreihen-Vorlage statt einer Ordnerangabe verwenden",
    )
    timeline.add_argument(
        "--preset-file",
        type=Path,
        help="Abweichende lokale Zeitreihen-Vorlagendatei",
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
    timeline.add_argument(
        "--warn-size-growth-percent",
        type=non_negative_float,
        help=(
            "ROT mit Klartext, wenn die Größe gegenüber dem vorherigen Scan "
            "mindestens um diesen Prozentwert wächst"
        ),
    )
    timeline.add_argument(
        "--warn-file-growth-percent",
        type=non_negative_float,
        help=(
            "ROT mit Klartext, wenn die Dateizahl gegenüber dem vorherigen Scan "
            "mindestens um diesen Prozentwert wächst"
        ),
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


def _percent(value: float | None) -> str:
    return "–" if value is None else f"{value:+.2f} %"


def _timeline_folder(arguments: argparse.Namespace) -> str:
    if arguments.preset:
        if arguments.folder is not None:
            raise ValueError(
                "Ordner und --preset dürfen nicht gleichzeitig angegeben werden"
            )
        return get_timeline_preset(
            arguments.preset,
            arguments.preset_file,
        ).folder
    return arguments.folder or "."


def run_folder_timeline(arguments: argparse.Namespace) -> int:
    has_export = any((arguments.json_path, arguments.csv_path, arguments.html_path))
    if arguments.no_terminal and not has_export:
        raise ValueError(
            "Ohne Terminalanzeige muss mindestens JSON, CSV oder HTML gewählt werden"
        )
    timeline = build_folder_timeline(
        arguments.database,
        options=FolderTimelineOptions(
            folder=_timeline_folder(arguments),
            from_session_id=arguments.from_session_id,
            to_session_id=arguments.to_session_id,
            limit=arguments.limit,
            warn_size_growth_percent=arguments.warn_size_growth_percent,
            warn_file_growth_percent=arguments.warn_file_growth_percent,
        ),
    )
    if not arguments.no_terminal:
        print(f"Stammordner: {timeline.root}")
        if arguments.preset:
            print(f"Zeitreihen-Vorlage: {arguments.preset} → {timeline.folder}")
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
        thresholds: list[str] = []
        if timeline.warn_size_growth_percent is not None:
            thresholds.append(
                f"Größe ab +{timeline.warn_size_growth_percent:.2f} %"
            )
        if timeline.warn_file_growth_percent is not None:
            thresholds.append(
                f"Dateizahl ab +{timeline.warn_file_growth_percent:.2f} %"
            )
        if thresholds:
            print(
                "Aktive Trendgrenzen: "
                + "; ".join(thresholds)
                + f" | Treffer: {timeline.threshold_trigger_count}"
            )
            print("Hinweis: Trendgrenzen sind rein lesend und keine Schadensbewertung.")
        else:
            print("Trendgrenzen: nicht aktiviert")
        for point in timeline.points:
            file_delta = "–" if point.file_delta is None else f"{point.file_delta:+d}"
            print(traffic_text(point.traffic_light, mode=colour_mode(arguments)))
            print(
                f"  Scan #{point.session_id} | {point.recorded_utc} | "
                f"{point.scan_mode} | Dateien {point.file_count} "
                f"({file_delta}, {_percent(point.file_delta_percent)}) | "
                f"Größe {human_size(point.size_bytes)} "
                f"({_signed_size(point.size_delta_bytes)}, "
                f"{_percent(point.size_delta_percent)})"
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
