from __future__ import annotations

import argparse
from pathlib import Path

from datenbanktool.cli_common import (
    colour_mode,
    human_size,
    non_negative_int,
    positive_int,
    print_hint,
)
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.folder_compare import (
    FolderComparisonFilter,
    compare_folders,
    paginate_folder_comparison,
)
from datenbanktool.core.folder_compare_exports import export_folder_comparison
from datenbanktool.core.presentation import traffic_text

_CHANGE_TYPES = ("grown", "shrunk", "new", "removed", "changed", "unchanged")
_CHANGE_LABELS = {
    "grown": "Gewachsen",
    "shrunk": "Kleiner geworden",
    "new": "Neu",
    "removed": "Nicht mehr vorhanden",
    "changed": "Dateizahl geändert",
    "unchanged": "Unverändert",
}


def register_folder_compare_parser(
    index_subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    compare = index_subparsers.add_parser(
        "folder-compare",
        help="Ordnerwachstum zwischen zwei abgeschlossenen Scans vergleichen",
        description=(
            "Vergleicht zwei abgeschlossene Sitzungen desselben Stammordners. "
            "Standardmäßig wird der neueste Scan mit seinem direkten Vorgänger "
            "oder dem vorherigen vollständigen Scan desselben Ordners verglichen."
        ),
        epilog=(
            "Auswirkung: Die SQLite-Datenbank und Originaldateien werden nur gelesen. "
            "Nur ausdrücklich gewählte JSON-, CSV- oder HTML-Berichte werden geschrieben."
        ),
    )
    compare.add_argument("database", type=Path)
    compare.add_argument(
        "--from-session-id",
        type=positive_int,
        help="Ältere abgeschlossene Ausgangssitzung",
    )
    compare.add_argument(
        "--to-session-id",
        type=positive_int,
        help="Neuere abgeschlossene Zielsitzung; Standard ist der neueste Scan",
    )
    compare.add_argument(
        "--type",
        dest="change_types",
        action="append",
        default=[],
        choices=_CHANGE_TYPES,
        help="Nur diese Vergleichsart zeigen. Mehrfach nutzbar.",
    )
    compare.add_argument("--contains", default="", help="Nur passende Ordnerpfade")
    compare.add_argument(
        "--min-change-mib",
        type=non_negative_int,
        default=0,
        help="Nur Ordner ab dieser absoluten Größenänderung zeigen",
    )
    compare.add_argument("--max-depth", type=non_negative_int)
    compare.add_argument("--page", type=positive_int, default=1)
    compare.add_argument("--page-size", type=positive_int, default=25)
    compare.add_argument(
        "--sort",
        choices=("path", "change", "percent", "files", "current-size"),
        default="change",
    )
    compare.add_argument(
        "--descending",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    compare.add_argument(
        "--attention-growth-mib",
        type=positive_int,
        default=1024,
        help="Ab dieser Zunahme wird starkes Wachstum rot markiert",
    )
    compare.add_argument("--json", dest="json_path", type=Path)
    compare.add_argument("--csv", dest="csv_path", type=Path)
    compare.add_argument("--html", dest="html_path", type=Path)
    compare.add_argument(
        "--all-pages",
        action="store_true",
        help="Alle gefilterten Zeilen exportieren; Terminal bleibt paginiert",
    )
    compare.add_argument("--overwrite-report", action="store_true")
    compare.add_argument("--no-terminal", action="store_true")
    bind_handler(
        compare,
        run_folder_compare,
        CommandPolicy("index.folder-compare", writes_reports=True),
    )


def _signed_size(value: int) -> str:
    if value == 0:
        return "0 B"
    prefix = "+" if value > 0 else "−"
    return prefix + human_size(abs(value))


def run_folder_compare(arguments: argparse.Namespace) -> int:
    has_export = any((arguments.json_path, arguments.csv_path, arguments.html_path))
    if arguments.no_terminal and not has_export:
        raise ValueError(
            "Ohne Terminalanzeige muss mindestens JSON, CSV oder HTML gewählt werden"
        )
    if arguments.all_pages and not has_export:
        raise ValueError("--all-pages benötigt mindestens ein Exportziel")
    mib = 1024 * 1024
    filters = FolderComparisonFilter(
        change_types=tuple(arguments.change_types),
        contains=arguments.contains,
        min_change_bytes=arguments.min_change_mib * mib,
        max_depth=arguments.max_depth,
        page=arguments.page,
        page_size=arguments.page_size,
        sort_by=arguments.sort,
        descending=arguments.descending,
        attention_growth_bytes=arguments.attention_growth_mib * mib,
    )
    result = compare_folders(
        arguments.database,
        from_session_id=arguments.from_session_id,
        to_session_id=arguments.to_session_id,
        filters=filters,
        all_rows=arguments.all_pages,
    )
    page = (
        paginate_folder_comparison(
            result,
            page=arguments.page,
            page_size=arguments.page_size,
        )
        if arguments.all_pages
        else result
    )
    if not arguments.no_terminal:
        print(f"Ordner: {page.root}")
        print(
            f"Vergleich: Scan #{page.from_session_id} → #{page.to_session_id} | "
            f"Treffer: {page.total_rows} | Seite {page.page} von {page.total_pages}"
        )
        summary = " | ".join(
            f"{_CHANGE_LABELS[key]} {page.counts[key]}" for key in _CHANGE_TYPES
        )
        print(summary)
        if not page.rows:
            print("Keine passenden Ordneränderungen gefunden.")
        for row in page.rows:
            percent = (
                "kein Ausgangswert"
                if row.size_delta_percent is None
                else f"{row.size_delta_percent:+.2f} %"
            )
            print(traffic_text(row.traffic_light, mode=colour_mode(arguments)))
            print(
                f"  {row.folder} | {row.change_label} | "
                f"Dateien {row.before_files} → {row.after_files} "
                f"({row.file_delta:+d}) | Größe {human_size(row.before_size_bytes)} → "
                f"{human_size(row.after_size_bytes)} "
                f"({_signed_size(row.size_delta_bytes)}, {percent})"
            )
        if page.page < page.total_pages:
            print(f"Nächste Seite: --page {page.page + 1}")
        print_hint(
            arguments,
            "Der Vergleich liest nur gespeicherte Scans. Er löscht, verschiebt "
            "oder verändert keine Originaldateien.",
        )
    if has_export:
        export_page = result if arguments.all_pages else page
        exported = export_folder_comparison(
            export_page,
            json_path=arguments.json_path,
            csv_path=arguments.csv_path,
            html_path=arguments.html_path,
            overwrite=arguments.overwrite_report,
        )
        print(f"Exportierte Ordnerzeilen: {exported.row_count}")
        if exported.json_path:
            print(f"JSON-Bericht: {exported.json_path}")
        if exported.csv_path:
            print(f"CSV-Bericht: {exported.csv_path}")
        if exported.html_path:
            print(f"HTML-Bericht: {exported.html_path}")
    return 0
