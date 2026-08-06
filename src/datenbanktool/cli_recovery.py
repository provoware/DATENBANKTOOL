from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from datenbanktool.cli_common import colour_mode
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.presentation import TrafficLight, traffic_text
from datenbanktool.core.recovery import RecoveryCandidate, load_recovery_candidates
from datenbanktool.core.run_journal import default_resume_path


def register_recovery_parser(
    index_subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    recovery = index_subparsers.add_parser(
        "recovery",
        help="Alle gespeicherten Wiederanläufe ausschließlich lesend prüfen",
        description=(
            "Zeigt jeden gespeicherten Wiederanlauf mit Prüfstatus, Ordner, "
            "Indexdatei, Sitzung, Phase und Startbarkeit. Der Befehl startet, "
            "verwirft und verändert keinen Wiederanlauf."
        ),
    )
    recovery.add_argument(
        "--json",
        action="store_true",
        help="Vollständige Diagnose als JSON ohne Farben ausgeben.",
    )
    bind_handler(
        recovery,
        run_recovery_diagnostics,
        CommandPolicy("index.recovery"),
    )


def _item_payload(candidate: RecoveryCandidate) -> dict[str, object]:
    payload = candidate.to_dict()
    payload["startable"] = candidate.resumable
    return payload


def _diagnostic_payload(
    candidates: tuple[RecoveryCandidate, ...],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": str(default_resume_path()),
        "record_count": len(candidates),
        "startable_count": sum(candidate.resumable for candidate in candidates),
        "not_startable_count": sum(not candidate.resumable for candidate in candidates),
        "items": [_item_payload(candidate) for candidate in candidates],
    }


def _session_text(candidate: RecoveryCandidate) -> str:
    if candidate.session_id is None:
        return "keine bestätigte Sitzung"
    return f"#{candidate.session_id}"


def run_recovery_diagnostics(arguments: argparse.Namespace) -> int:
    candidates = load_recovery_candidates()
    if arguments.json:
        print(
            json.dumps(
                _diagnostic_payload(candidates),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print("Wiederanlauf-Diagnose – vollständig lesend")
    print(f"Statusdatei: {default_resume_path()}")
    print(
        f"Gespeicherte Einträge: {len(candidates)} | "
        f"startbar: {sum(candidate.resumable for candidate in candidates)} | "
        f"nicht startbar: {sum(not candidate.resumable for candidate in candidates)}"
    )
    print("Es wird kein Scan gestartet und kein Wiederanlauf verworfen oder verändert.")
    if not candidates:
        print("Keine gespeicherten Wiederanlaufeinträge gefunden.")
        return 0

    for number, candidate in enumerate(candidates, 1):
        level = "green" if candidate.resumable else "yellow"
        label = "startbar" if candidate.resumable else "nicht startbar"
        light = TrafficLight(level, label, candidate.validation_detail)
        print(f"\n{number}. {candidate.operation_label}")
        print("   " + traffic_text(light, mode=colour_mode(arguments)))
        print(f"   Prüfstatus: {candidate.validation_label}")
        print(f"   Ordner: {candidate.root}")
        print(f"   Indexdatei: {candidate.database}")
        print(f"   Sitzung: {_session_text(candidate)}")
        print(f"   Zustand: {candidate.status}")
        print(f"   Phase: {candidate.phase}")
        print(f"   Bestätigte Dateien: {candidate.imported_count}")
        print(f"   Aktualisiert (UTC): {candidate.updated_utc}")
        print(f"   Technische Einzelheit: {candidate.validation_detail}")
    return 0
