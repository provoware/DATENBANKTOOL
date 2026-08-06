from __future__ import annotations

import argparse
import json
from pathlib import Path

from datenbanktool.cli_common import colour_mode
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.presentation import TrafficLight, traffic_text
from datenbanktool.core.restore_audit import RestoreAuditVerification, verify_restore_audit_log
from datenbanktool.core.restore_audit_identity import (
    RestoreAuditIdentity,
    verify_restore_audit_identity,
)


def register_restore_audit_parser(
    actions: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    verification = actions.add_parser(
        "verify-log",
        help="Ein Wiederherstellungsprotokoll und seine drei Dateien nur lesend prüfen",
        description=(
            "Prüft genau ein ausdrücklich ausgewähltes JSON-Protokoll auf festes Schema, "
            "UTC-Zeiten, drei unterschiedliche absolute Pfade und drei SHA-256-Werte. "
            "Vorhandene Dateien werden nur gelesen und gehasht."
        ),
    )
    verification.add_argument("protocol", type=Path)
    verification.add_argument(
        "--expected-protocol-sha256",
        help=(
            "Optional genau diesen ausdrücklich angegebenen SHA-256-Wert der "
            "Protokolldatei vor jeder JSON-Schemaauswertung verlangen."
        ),
    )
    verification.add_argument("--json", action="store_true")
    bind_handler(
        verification,
        run_restore_audit_verification,
        CommandPolicy("index.backups.verify-log"),
    )


def _print_verification(
    result: RestoreAuditVerification,
    arguments: argparse.Namespace,
    identity: RestoreAuditIdentity | None,
) -> None:
    print("Wiederherstellungsprotokoll – vollständig lesende Prüfung")
    print(
        traffic_text(
            TrafficLight(
                result.status_level,
                result.status_label,
                result.technical_detail,
            ),
            mode=colour_mode(arguments),
        )
    )
    print(f"Protokoll: {result.protocol}")
    if identity is not None:
        print("Protokollidentität vor Schemaauswertung: bestätigt")
        print(f"Erwartete Protokoll-SHA-256: {identity.expected_sha256}")
        print(f"Tatsächliche Protokoll-SHA-256: {identity.actual_sha256}")
    print(f"Schema: {result.schema_version} | Ereignis: {result.event}")
    print(f"Protokoll erstellt (UTC): {result.created_utc}")
    print(f"Wiederherstellung abgeschlossen (UTC): {result.restore_completed_utc}")
    print(f"Konfigurationsart: {result.configuration_kind}")
    for number, item in enumerate(result.files, 1):
        light = TrafficLight(item.status_level, item.status_label, item.technical_detail)
        print(f"\n{number}. {item.label}")
        print("   " + traffic_text(light, mode=colour_mode(arguments)))
        print(f"   Pfad: {item.path}")
        print(f"   Erwartete SHA-256: {item.expected_sha256}")
        print(f"   Tatsächliche SHA-256: {item.actual_sha256 or 'nicht verfügbar'}")
        print(f"   Technische Einzelheit: {item.technical_detail}")
    print(
        "Es wurde keine Wiederherstellung gestartet und keine Datei verändert oder gelöscht."
    )


def run_restore_audit_verification(arguments: argparse.Namespace) -> int:
    identity: RestoreAuditIdentity | None = None
    if arguments.expected_protocol_sha256 is not None:
        identity = verify_restore_audit_identity(
            arguments.protocol,
            arguments.expected_protocol_sha256,
        )

    result = verify_restore_audit_log(arguments.protocol)
    if arguments.json:
        payload = result.to_dict()
        if identity is not None:
            payload["protocol_identity"] = identity.to_dict()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_verification(result, arguments, identity)
    return 0 if result.all_files_match else 1
