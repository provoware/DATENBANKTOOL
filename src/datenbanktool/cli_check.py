from __future__ import annotations

import argparse
import json
from pathlib import Path

from datenbanktool.cli_common import colour_mode
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.diagnostics import run_diagnostics
from datenbanktool.core.presentation import TrafficLight, traffic_text


def register_check_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    check = subparsers.add_parser(
        "check",
        help="Prüfen, ob alles startklar ist",
        description=(
            "Prüft verständlich, ob Start, sicheres Speichern und Wiederanlauf "
            "funktionieren. Technisch: lokale Diagnose ohne Änderung der Originaldateien."
        ),
        epilog=(
            "Optional kann eine Indexdatei nur lesend auf Lesbarkeit, Version und "
            "innere Konsistenz geprüft werden."
        ),
    )
    check.add_argument(
        "--database",
        type=Path,
        help="Optional: vorhandene Indexdatei nur lesend mitprüfen",
    )
    check.add_argument("--json", action="store_true")
    bind_handler(
        check,
        run_check,
        CommandPolicy("check", writes_test_data=True),
    )


def run_check(arguments: argparse.Namespace) -> int:
    result = run_diagnostics(arguments.database)
    if arguments.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0 if result.ready else 1
    print("Startklar-Prüfung")
    print("Dabei werden keine persönlichen Dateien verändert. (Technisch: Diagnose)")
    for item in result.checks:
        light = TrafficLight(item.level, item.message, item.technical_detail)
        print(traffic_text(light, mode=colour_mode(arguments)))
        print(f"  Technische Einzelheit: {item.technical_detail}")
    if result.ready:
        print("Ergebnis: Das Tool ist startklar.")
        return 0
    print("Ergebnis: Vor dem nächsten Lauf muss mindestens ein roter Punkt behoben werden.")
    return 1
