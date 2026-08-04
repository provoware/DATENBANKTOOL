from __future__ import annotations

import argparse
from pathlib import Path

from datenbanktool.cli_common import positive_int
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.acceptance import PROFILES, get_profile, run_acceptance
from datenbanktool.core.presentation import TrafficLight, traffic_text


def _positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Wert muss eine Zahl sein") from error
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Wert muss größer als 0 sein")
    return parsed


def register_acceptance_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    descriptions = "\n".join(
        f"  {name}: {profile.file_count} Dateien – {profile.description}"
        for name, profile in PROFILES.items()
    )
    acceptance = subparsers.add_parser(
        "acceptance",
        help="Reproduzierbaren Leistungs- und Laienabnahmetest durchführen",
        description=(
            "Erzeugt einen künstlichen Testbestand in einem neuen Arbeitsordner, "
            "baut einen Index, exportiert die vollständige Ordnerübersicht und "
            "prüft Laufzeit, Speicher, Vollständigkeit und Datenunverändertheit.\n\n"
            "Profile:\n" + descriptions
        ),
        epilog=(
            "Auswirkung: Schreibt ausschließlich neue Testdaten und Berichte in den "
            "angegebenen, noch nicht vorhandenen Arbeitsordner. Bestehende oder "
            "persönliche Dateien werden nicht verändert. Die erzeugte Checkliste "
            "muss anschließend von einer realen Testperson ausgefüllt werden."
        ),
    )
    acceptance.add_argument(
        "--profile",
        choices=tuple(PROFILES),
        default="quick",
        help="quick für CI, standard für lokale Prüfung, large für Großbestand",
    )
    acceptance.add_argument(
        "--workspace",
        type=Path,
        required=True,
        help="Neuer, noch nicht vorhandener Arbeitsordner für Testdaten und Berichte",
    )
    acceptance.add_argument(
        "--seed",
        type=int,
        default=20260804,
        help="Fester Startwert für exakt reproduzierbare Dateigrößen",
    )
    acceptance.add_argument(
        "--max-seconds",
        type=_positive_float,
        help="Optionale strengere oder systemgerechte Laufzeitgrenze",
    )
    acceptance.add_argument(
        "--max-memory-mib",
        type=positive_int,
        help="Optionale Grenze für den gemessenen Python-Spitzenspeicher",
    )
    bind_handler(
        acceptance,
        run_acceptance_command,
        CommandPolicy(
            "acceptance",
            writes_reports=True,
            writes_test_data=True,
        ),
    )


def run_acceptance_command(arguments: argparse.Namespace) -> int:
    profile = get_profile(arguments.profile)
    print(f"Abnahmeprofil: {profile.name} | Dateien: {profile.file_count}")
    print(f"Neuer Arbeitsordner: {arguments.workspace}")
    print("Sicherheitsgrenze: Es werden nur neue synthetische Testdaten geschrieben.")
    result = run_acceptance(
        profile,
        arguments.workspace,
        seed=arguments.seed,
        max_seconds=arguments.max_seconds,
        max_python_memory_mib=arguments.max_memory_mib,
    )
    light = (
        TrafficLight(
            "green",
            "Automatische Abnahme bestanden",
            f"{sum(check.passed for check in result.checks)}/{len(result.checks)} Prüfungen",
        )
        if result.passed
        else TrafficLight(
            "red",
            "Automatische Abnahme nicht bestanden",
            "Mindestens ein festes Kriterium wurde verfehlt",
        )
    )
    print(traffic_text(light, mode=getattr(arguments, "color", "auto")))
    print(f"Laufzeit: {result.duration_seconds:.3f} Sekunden")
    print(f"Python-Spitzenspeicher: {result.peak_python_memory_bytes} Byte")
    print(f"JSON-Bericht: {result.json_report}")
    print(f"Markdown-Bericht: {result.markdown_report}")
    print(f"Laien-Checkliste: {result.novice_checklist}")
    print("Reale Laienabnahme: noch offen; Checkliste durch Testperson ausfüllen.")
    return 0 if result.passed else 1
