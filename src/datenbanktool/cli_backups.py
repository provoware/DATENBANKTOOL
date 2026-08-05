from __future__ import annotations

import argparse
import json
from pathlib import Path

from datenbanktool.cli_common import colour_mode, human_size, print_hint
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.backup_catalog import delete_backup, list_backups
from datenbanktool.core.config_restore import (
    ConfigRestoreComparison,
    ConfigRestoreResult,
    compare_config_backup,
    restore_config_backup,
)
from datenbanktool.core.presentation import TrafficLight, traffic_text
from datenbanktool.core.restore_audit import RestoreAuditResult, write_restore_audit_log


def register_backup_catalog_parser(
    index_subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    backups = index_subparsers.add_parser(
        "backups",
        help="Index- und Konfigurationssicherungen prüfen und einzeln verwalten",
        description=(
            "Zeigt erkannte Sicherungen mit Alter, Größe und Prüfergebnis. "
            "Nichts wird automatisch gelöscht."
        ),
    )
    actions = backups.add_subparsers(dest="backup_action", required=True)

    listing = actions.add_parser("list", help="Sicherungen nur anzeigen und prüfen")
    listing.add_argument("database", type=Path)
    listing.add_argument("--config-directory", type=Path)
    listing.add_argument("--json", action="store_true")
    bind_handler(listing, run_backup_list, CommandPolicy("index.backups.list"))

    comparison = actions.add_parser(
        "compare",
        help="Eine Konfigurationssicherung nur mit der aktiven Datei vergleichen",
        description=(
            "Vergleicht genau eine katalogisierte Such- oder Zeitreihen-Sicherung "
            "mit der zugehörigen aktiven Konfiguration. Es wird nichts verändert."
        ),
    )
    comparison.add_argument("database", type=Path)
    comparison.add_argument("backup", type=Path)
    comparison.add_argument("--config-directory", type=Path)
    comparison.add_argument("--json", action="store_true")
    bind_handler(
        comparison,
        run_backup_compare,
        CommandPolicy("index.backups.compare"),
    )

    restoration = actions.add_parser(
        "restore",
        help="Genau eine geprüfte Konfigurationssicherung wiederherstellen",
        description=(
            "Vergleicht erneut, erstellt automatisch eine geprüfte Rückfallsicherung "
            "und ersetzt erst danach genau die zugehörige aktive Vorlagendatei."
        ),
    )
    restoration.add_argument("database", type=Path)
    restoration.add_argument("backup", type=Path)
    restoration.add_argument("--config-directory", type=Path)
    restoration.add_argument("--confirm-name", required=True)
    restoration.add_argument("--yes", action="store_true")
    restoration.add_argument(
        "--restore-log",
        type=Path,
        help=(
            "Nach erfolgreicher Wiederherstellung genau ein neues JSON-Protokoll "
            "ohne Konfigurationsinhalte schreiben. Vorhandene Dateien werden nicht "
            "überschrieben."
        ),
    )
    restoration.add_argument("--json", action="store_true")
    bind_handler(
        restoration,
        run_backup_restore,
        CommandPolicy(
            "index.backups.restore",
            writes_backups=True,
            writes_configuration=True,
            writes_reports=True,
        ),
    )

    deletion = actions.add_parser(
        "delete",
        help="Genau eine zuvor geprüfte Sicherung löschen",
        description=(
            "Löscht ausschließlich eine Datei aus derselben geprüften Übersicht. "
            "Aktive Index- und Konfigurationsdateien sind ausgeschlossen."
        ),
    )
    deletion.add_argument("database", type=Path)
    deletion.add_argument("backup", type=Path)
    deletion.add_argument("--config-directory", type=Path)
    deletion.add_argument("--confirm-name", required=True)
    deletion.add_argument("--yes", action="store_true")
    bind_handler(
        deletion,
        run_backup_delete,
        CommandPolicy("index.backups.delete", writes_backups=True),
    )


def _age_text(seconds: int) -> str:
    if seconds < 60:
        return "gerade eben"
    if seconds < 3600:
        return f"vor {seconds // 60} Minuten"
    if seconds < 86400:
        return f"vor {seconds // 3600} Stunden"
    days = seconds // 86400
    return f"vor {days} Tagen" if days != 1 else "vor 1 Tag"


def run_backup_list(arguments: argparse.Namespace) -> int:
    items = list_backups(
        arguments.database,
        config_directory=arguments.config_directory,
    )
    if arguments.json:
        print(json.dumps([item.to_dict() for item in items], ensure_ascii=False, indent=2))
        return 0
    print("Sicherungsübersicht")
    print("Es wird nichts automatisch gelöscht. Jede Entfernung braucht eine Einzelauswahl.")
    if not items:
        print("Keine erkannten Index- oder Konfigurationssicherungen gefunden.")
        return 0
    for number, item in enumerate(items, 1):
        light = TrafficLight(
            item.status_level,
            item.status_label,
            item.technical_detail,
        )
        print(f"{number}. {item.kind_label}: {item.name}")
        print("   " + traffic_text(light, mode=colour_mode(arguments)))
        print(
            f"   Größe: {human_size(item.size_bytes)} | {_age_text(item.age_seconds)} | "
            f"geändert: {item.modified_utc}"
        )
        print(f"   Pfad: {item.path}")
        print(f"   Technische Einzelheit: {item.technical_detail}")
    print_hint(
        arguments,
        "Löschen nur mit exakt angezeigtem Pfad, Dateinamen und ausdrücklichem --yes.",
    )
    return 0


def _print_names(label: str, values: tuple[str, ...]) -> None:
    text = ", ".join(values) if values else "keine"
    print(f"{label}: {text}")


def _print_comparison(comparison: ConfigRestoreComparison) -> None:
    level = "yellow" if comparison.can_restore else "green"
    label = (
        "Wiederherstellung würde Änderungen ausführen"
        if comparison.can_restore
        else "Keine Änderung nötig"
    )
    print(
        traffic_text(
            TrafficLight(level, label, comparison.validation_detail),
            mode="never",
        )
    )
    print(f"Art: {comparison.kind_label}")
    print(f"Ausgewählte Sicherung: {comparison.backup}")
    print(f"Aktive Konfiguration: {comparison.active}")
    print(
        f"Vorlagen: Sicherung {comparison.backup_preset_count} | "
        f"aktiv {comparison.active_preset_count}"
    )
    _print_names("Würde hinzufügen", comparison.add_names)
    _print_names("Würde entfernen", comparison.remove_names)
    _print_names("Würde ersetzen", comparison.change_names)
    _print_names("Unverändert", comparison.unchanged_names)
    print(f"SHA-256 Sicherung: {comparison.backup_sha256}")
    print(f"SHA-256 aktiv:     {comparison.active_sha256}")


def run_backup_compare(arguments: argparse.Namespace) -> int:
    comparison = compare_config_backup(
        arguments.database,
        arguments.backup,
        config_directory=arguments.config_directory,
    )
    if arguments.json:
        print(json.dumps(comparison.to_dict(), ensure_ascii=False, indent=2))
        return 0
    print("Konfigurations-Wiederherstellung – Nur-Lese-Vergleich")
    _print_comparison(comparison)
    print("Es wurde nichts verändert, gesichert, wiederhergestellt oder gelöscht.")
    if comparison.can_restore:
        print(
            "Eine Wiederherstellung erstellt zuerst automatisch eine neue geprüfte "
            "Rückfallsicherung der aktiven Datei."
        )
    return 0


def _restore_payload(
    result: ConfigRestoreResult,
    audit: RestoreAuditResult | None,
    audit_error: str | None,
    *,
    include_audit: bool,
) -> dict[str, object]:
    payload = result.to_dict()
    if include_audit:
        payload["restore_log"] = audit.to_dict() if audit is not None else None
        payload["restore_log_error"] = audit_error
    return payload


def _print_restored(result: ConfigRestoreResult, arguments: argparse.Namespace) -> None:
    print(
        traffic_text(
            TrafficLight(
                "green",
                "Konfiguration geprüft wiederhergestellt",
                result.comparison.active,
            ),
            mode=colour_mode(arguments),
        )
    )
    print(f"Wiederhergestellt aus: {result.comparison.backup}")
    print(f"Aktive Konfiguration: {result.comparison.active}")
    print(f"Automatische Rückfallsicherung: {result.rollback_backup.backup}")
    print(f"Bestätigte SHA-256: {result.restored_sha256}")
    print(
        "Ausgewählte Sicherung und Rückfallsicherung bleiben erhalten. "
        "Es gibt keine automatische Rotation oder Löschung."
    )


def run_backup_restore(arguments: argparse.Namespace) -> int:
    result = restore_config_backup(
        arguments.database,
        arguments.backup,
        confirm_name=arguments.confirm_name,
        yes=arguments.yes,
        config_directory=arguments.config_directory,
    )
    audit: RestoreAuditResult | None = None
    audit_error: str | None = None
    if arguments.restore_log is not None:
        try:
            audit = write_restore_audit_log(result, arguments.restore_log)
        except (FileExistsError, OSError, ValueError) as error:
            audit_error = f"{type(error).__name__}: {error}"

    if arguments.json:
        print(
            json.dumps(
                _restore_payload(
                    result,
                    audit,
                    audit_error,
                    include_audit=arguments.restore_log is not None,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1 if audit_error is not None else 0

    _print_restored(result, arguments)
    if audit is not None:
        print(f"Wiederherstellungsprotokoll: {audit.path}")
        print(f"Protokoll-SHA-256: {audit.sha256}")
        print(
            "Das Protokoll enthält nur UTC-Zeit, drei Dateipfade und drei SHA-256-Werte; "
            "keine Konfigurationsinhalte oder Geheimnisse."
        )
    elif audit_error is not None:
        print(
            "Die Konfiguration wurde erfolgreich wiederhergestellt, aber das ausdrücklich "
            "gewünschte Wiederherstellungsprotokoll konnte nicht geschrieben werden."
        )
        print(f"Technische Einzelheit: {audit_error}")
        return 1
    return 0


def run_backup_delete(arguments: argparse.Namespace) -> int:
    item = delete_backup(
        arguments.database,
        arguments.backup,
        confirm_name=arguments.confirm_name,
        yes=arguments.yes,
        config_directory=arguments.config_directory,
    )
    print(
        traffic_text(
            TrafficLight(
                "green",
                "Genau eine Sicherung gelöscht",
                item.path,
            ),
            mode=colour_mode(arguments),
        )
    )
    print(f"Gelöscht: {item.path}")
    print("Aktive Index-, Konfigurations- und Originaldateien blieben unverändert.")
    return 0
