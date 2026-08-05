from __future__ import annotations

import argparse
from pathlib import Path

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


def optional_config_backup(
    enabled: bool,
    source: Path,
    *,
    configuration_exists: bool,
) -> ConfigBackupResult | None:
    if not enabled or not configuration_exists:
        return None
    return create_config_backup(source)


def print_config_backup(
    backup: ConfigBackupResult | None,
    *,
    color_mode: str,
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
            mode=color_mode,
        )
    )
    print(f"Sicherung: {backup.backup}")
