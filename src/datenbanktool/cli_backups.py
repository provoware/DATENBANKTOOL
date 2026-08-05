from __future__ import annotations

import argparse
import json
from pathlib import Path

from datenbanktool.cli_common import colour_mode, human_size, print_hint
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.backup_catalog import delete_backup, list_backups
from datenbanktool.core.presentation import TrafficLight, traffic_text


def register_backup_catalog_parser(
    index_subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    backups = index_subparsers.add_parser(
        "backups",
        help="Index- und Konfigurationssicherungen prüfen und einzeln verwalten",
        description=(
            "Zeigt erkannte Sicherungen mit Alter, Größe und Prüfergebnis. "
            "Nichts wird automatisch gelöscht. (Technisch: Nur-Lese-Katalog.)"
        ),
    )
    actions = backups.add_subparsers(dest="backup_action", required=True)

    listing = actions.add_parser(
        "list",
        help="Sicherungen nur anzeigen und prüfen",
    )
    listing.add_argument("database", type=Path)
    listing.add_argument("--config-directory", type=Path)
    listing.add_argument("--json", action="store_true")
    bind_handler(listing, run_backup_list, CommandPolicy("index.backups.list"))

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
