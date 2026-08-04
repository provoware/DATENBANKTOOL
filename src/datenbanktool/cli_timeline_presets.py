from __future__ import annotations

import argparse
import json
from pathlib import Path

from datenbanktool.cli_common import colour_mode, print_hint
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.presentation import TrafficLight, paint, traffic_text
from datenbanktool.core.timeline_presets import (
    delete_timeline_preset,
    get_timeline_preset,
    list_timeline_presets,
    save_timeline_preset,
)


def register_timeline_preset_parsers(
    index_subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    presets = index_subparsers.add_parser(
        "timeline-presets",
        help="Relative Ordnerpfade für Zeitreihen lokal speichern und verwalten",
        description=(
            "Speichert ausschließlich validierte relative Ordnerpfade in einer "
            "lokalen JSON-Konfigurationsdatei. Datenbankpfade und Originaldateien "
            "werden nicht gespeichert oder verändert."
        ),
        epilog=(
            "Vorhandene Vorlagen werden nicht still ersetzt. "
            "Bewusstes Ersetzen benötigt --replace."
        ),
    )
    subparsers = presets.add_subparsers(
        dest="timeline_preset_command",
        required=True,
    )

    preset_list = subparsers.add_parser("list", help="Alle Zeitreihen-Vorlagen anzeigen")
    preset_list.add_argument("--preset-file", type=Path)
    preset_list.add_argument("--json", action="store_true")
    bind_handler(
        preset_list,
        run_timeline_presets,
        CommandPolicy("index.timeline-presets.list"),
    )

    preset_show = subparsers.add_parser("show", help="Eine Vorlage vollständig erklären")
    preset_show.add_argument("name")
    preset_show.add_argument("--preset-file", type=Path)
    preset_show.add_argument("--json", action="store_true")
    bind_handler(
        preset_show,
        run_timeline_presets,
        CommandPolicy("index.timeline-presets.show"),
    )

    preset_save = subparsers.add_parser("save", help="Neue Zeitreihen-Vorlage speichern")
    preset_save.add_argument("name")
    preset_save.add_argument("folder", help="Validierter relativer Ordner oder '.'")
    preset_save.add_argument("--description", default="")
    preset_save.add_argument("--preset-file", type=Path)
    preset_save.add_argument(
        "--replace",
        action="store_true",
        help="Vorhandene gleichnamige Vorlage bewusst ersetzen",
    )
    bind_handler(
        preset_save,
        run_timeline_presets,
        CommandPolicy("index.timeline-presets.save", writes_configuration=True),
    )

    preset_delete = subparsers.add_parser("delete", help="Zeitreihen-Vorlage löschen")
    preset_delete.add_argument("name")
    preset_delete.add_argument("--preset-file", type=Path)
    preset_delete.add_argument(
        "--yes",
        action="store_true",
        help="Löschen ausdrücklich bestätigen",
    )
    bind_handler(
        preset_delete,
        run_timeline_presets,
        CommandPolicy("index.timeline-presets.delete", writes_configuration=True),
    )


def run_timeline_presets(arguments: argparse.Namespace) -> int:
    command = arguments.timeline_preset_command
    if command == "list":
        presets = list_timeline_presets(arguments.preset_file)
        if arguments.json:
            print(
                json.dumps(
                    [preset.to_dict() for preset in presets],
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if not presets:
            print(
                traffic_text(
                    TrafficLight(
                        "yellow",
                        "Noch leer",
                        "keine Zeitreihen-Vorlagen gespeichert",
                    ),
                    mode=colour_mode(arguments),
                )
            )
            print_hint(
                arguments,
                "Speichern: datenbanktool index timeline-presets save NAME ORDNER",
            )
            return 0
        for preset in presets:
            description = f" – {preset.description}" if preset.description else ""
            print(
                f"{paint('●', 'green', mode=colour_mode(arguments))} "
                f"{preset.name}: {preset.folder}{description}"
            )
        return 0

    if command == "show":
        preset = get_timeline_preset(arguments.name, arguments.preset_file)
        if arguments.json:
            print(json.dumps(preset.to_dict(), ensure_ascii=False, indent=2))
            return 0
        print(paint(preset.name, "bold", mode=colour_mode(arguments)))
        print(f"Relativer Ordner: {preset.folder}")
        print(f"Beschreibung: {preset.description or 'keine'}")
        print(f"Erstellt UTC: {preset.created_utc}")
        print(f"Aktualisiert UTC: {preset.updated_utc}")
        print_hint(
            arguments,
            f"Starten: datenbanktool index folder-timeline DATENBANK "
            f'"{preset.folder}"',
        )
        return 0

    if command == "save":
        preset = save_timeline_preset(
            arguments.name,
            arguments.folder,
            description=arguments.description,
            path=arguments.preset_file,
            replace=arguments.replace,
        )
        print(
            traffic_text(
                TrafficLight(
                    "green",
                    "Zeitreihen-Vorlage gespeichert",
                    f"{preset.name}: {preset.folder}",
                ),
                mode=colour_mode(arguments),
            )
        )
        print_hint(
            arguments,
            "Die Vorlage ist auf der geführten Startseite unter Ordner-Zeitreihe auswählbar.",
        )
        return 0

    if command == "delete":
        if not arguments.yes:
            raise ValueError("Löschen benötigt die ausdrückliche Bestätigung --yes")
        deleted = delete_timeline_preset(
            arguments.name,
            path=arguments.preset_file,
        )
        print(
            traffic_text(
                TrafficLight("yellow", "Zeitreihen-Vorlage gelöscht", deleted.name),
                mode=colour_mode(arguments),
            )
        )
        return 0

    raise ValueError("Unbekannter Zeitreihen-Vorlagenbefehl")
