from __future__ import annotations

import argparse
from pathlib import Path

from datenbanktool.cli_common import (
    add_scan_options,
    colour_mode,
    human_size,
    print_hint,
    write_json_atomic,
)
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.presentation import TrafficLight, traffic_text
from datenbanktool.core.scanner import ScanOptions, scan_tree


def register_scan_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
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
    add_scan_options(scan)
    scan.add_argument("--json", dest="json_path", type=Path)
    scan.add_argument("--overwrite-report", action="store_true")
    bind_handler(
        scan,
        run_scan,
        CommandPolicy(
            "scan",
            reads_original_files=True,
            writes_reports=True,
        ),
    )


def run_scan(arguments: argparse.Namespace) -> int:
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
    print(traffic_text(light, mode=colour_mode(arguments)))
    print(f"Wurzel: {report.root}")
    print(
        f"Dateien: {len(report.files)} | "
        f"Gesamtgröße: {human_size(report.total_size_bytes)}"
    )
    print(
        f"Große Dateien: {report.large_file_count} | "
        f"Duplikatgruppen: {len(report.duplicate_groups)}"
    )
    if arguments.json_path is not None:
        write_json_atomic(
            arguments.json_path,
            report.to_dict(),
            arguments.overwrite_report,
        )
        print(f"JSON-Bericht: {arguments.json_path.expanduser()}")
    print_hint(arguments, "Dieser Befehl liest Dateien nur. Änderungen erfolgen nicht.")
    return 1 if report.errors else 0
