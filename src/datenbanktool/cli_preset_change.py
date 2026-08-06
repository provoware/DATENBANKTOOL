from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from datenbanktool.cli_common import colour_mode
from datenbanktool.core.config_backups import ConfigBackupResult, create_config_backup
from datenbanktool.core.presentation import TrafficLight, traffic_text


def add_prechange_backup_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--backup-before-change",
        action="store_true",
        help=(
            "Vor Ersetzen oder Löschen eine neue geprüfte, zeitgestempelte "
            "JSON-Sicherung erstellen. Keine automatische Rotation oder Löschung."
        ),
    )


def optional_prechange_backup(
    arguments: argparse.Namespace,
    *,
    lookup: Callable[[str, Path | None], object],
    default_path: Callable[[], Path],
    existing_required: bool,
) -> ConfigBackupResult | None:
    if not arguments.backup_before_change:
        return None
    try:
        lookup(arguments.name, arguments.preset_file)
    except KeyError:
        if existing_required:
            raise
        return None
    return create_config_backup(arguments.preset_file or default_path())


def print_config_backup(
    backup: ConfigBackupResult | None,
    arguments: argparse.Namespace,
) -> None:
    if backup is None:
        return
    print(
        traffic_text(
            TrafficLight(
                "green",
                "Konfigurationssicherung geprüft",
                f"{backup.preset_count} Vorlagen, SHA-256 {backup.sha256}",
            ),
            mode=colour_mode(arguments),
        )
    )
    print(f"Sicherung: {backup.backup}")
