from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from datenbanktool.cli_common import (
    add_category_filter,
    add_preset_filter_options,
    colour_mode,
    human_size,
    non_negative_float,
    non_negative_int,
    positive_int,
    print_hint,
)
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.config_backups import ConfigBackupResult, create_config_backup
from datenbanktool.core.presentation import (
    TrafficLight,
    paint,
    status_text,
    traffic_text,
)
from datenbanktool.core.presets import (
    default_preset_path,
    delete_preset,
    get_preset,
    list_presets,
    save_preset,
)
from datenbanktool.core.search import SearchFilter, build_fulltext_index, search_index


def register_search_parser(
    index_subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    search = index_subparsers.add_parser(
        "search",
        help="Dateien suchen oder eine Suchvorlage starten",
        description=(
            "Durchsucht einen abgeschlossenen Snapshot. Ohne "
            "--build-fulltext-index bleibt die Datenbank rein lesend.\n"
            "Eine gespeicherte Vorlage wird mit --preset NAME geladen; "
            "ausdrücklich angegebene Werte überschreiben sie."
        ),
        epilog=(
            "Beispiel: datenbanktool index search index.sqlite3 "
            "--preset grosse-audios\n"
            "Auswirkung: Keine Änderung, außer der schnelle FTS5-Index "
            "wird ausdrücklich aufgebaut."
        ),
    )
    search.add_argument("database", type=Path)
    search.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Suchwort oder mehrere Wörter",
    )
    search.add_argument("--preset", help="Gespeicherte Suchvorlage laden")
    search.add_argument("--preset-file", type=Path, help="Abweichende Vorlagendatei")
    search.add_argument("--session-id", type=positive_int)
    add_category_filter(search, default=None)
    search.add_argument("--min-size-mib", type=non_negative_int)
    search.add_argument("--max-size-mib", type=non_negative_int)
    search.add_argument(
        "--name-warning-only",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Nur problematische Namen; mit --no-name-warning-only "
            "einen Vorlagenwert ausschalten."
        ),
    )
    search.add_argument(
        "--duplicates-only",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Nur Duplikate; mit --no-duplicates-only "
            "einen Vorlagenwert ausschalten."
        ),
    )
    search.add_argument("--page", type=positive_int, default=1)
    search.add_argument("--page-size", type=positive_int, default=None)
    search.add_argument(
        "--sort",
        choices=("path", "size", "date", "type", "relevance"),
        default=None,
    )
    search.add_argument(
        "--descending",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    search.add_argument(
        "--fulltext",
        choices=("auto", "off", "required"),
        default=None,
    )
    search.add_argument("--build-fulltext-index", action="store_true")
    search.add_argument("--lock-timeout", type=non_negative_float, default=0.0)
    search.add_argument("--json", action="store_true")
    bind_handler(
        search,
        run_search,
        CommandPolicy("index.search", writes_index=True),
    )


def _add_prechange_backup_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--backup-before-change",
        action="store_true",
        help=(
            "Vor Ersetzen oder Löschen eine neue geprüfte, zeitgestempelte "
            "JSON-Sicherung erstellen. Keine automatische Rotation oder Löschung."
        ),
    )


def register_preset_parsers(
    index_subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    presets = index_subparsers.add_parser(
        "presets",
        help="Suchvorlagen speichern, anzeigen oder löschen",
        description=(
            "Speichert Suchfilter in einer kleinen lokalen JSON-Konfigurationsdatei."
        ),
        epilog=(
            "Vorlagen verändern weder Originaldateien noch den SQLite-Index.\n"
            "Starten: datenbanktool index search index.sqlite3 --preset NAME"
        ),
    )
    preset_subparsers = presets.add_subparsers(
        dest="preset_command",
        required=True,
    )
    preset_list = preset_subparsers.add_parser(
        "list",
        help="Alle Suchvorlagen auflisten",
    )
    preset_list.add_argument("--preset-file", type=Path)
    preset_list.add_argument("--json", action="store_true")
    bind_handler(
        preset_list,
        run_presets,
        CommandPolicy("index.presets.list"),
    )

    preset_show = preset_subparsers.add_parser(
        "show",
        help="Eine Suchvorlage vollständig erklären",
    )
    preset_show.add_argument("name")
    preset_show.add_argument("--preset-file", type=Path)
    preset_show.add_argument("--json", action="store_true")
    bind_handler(
        preset_show,
        run_presets,
        CommandPolicy("index.presets.show"),
    )

    preset_save = preset_subparsers.add_parser(
        "save",
        help="Neue Suchvorlage sicher speichern",
    )
    preset_save.add_argument("name")
    preset_save.add_argument("--description", default="")
    preset_save.add_argument("--preset-file", type=Path)
    preset_save.add_argument("--replace", action="store_true")
    _add_prechange_backup_option(preset_save)
    add_preset_filter_options(preset_save)
    bind_handler(
        preset_save,
        run_presets,
        CommandPolicy(
            "index.presets.save",
            writes_configuration=True,
            writes_backups=True,
        ),
    )

    preset_delete = preset_subparsers.add_parser(
        "delete",
        help="Suchvorlage löschen",
    )
    preset_delete.add_argument("name")
    preset_delete.add_argument("--preset-file", type=Path)
    preset_delete.add_argument(
        "--yes",
        action="store_true",
        help="Löschen ausdrücklich bestätigen",
    )
    _add_prechange_backup_option(preset_delete)
    bind_handler(
        preset_delete,
        run_presets,
        CommandPolicy(
            "index.presets.delete",
            writes_configuration=True,
            writes_backups=True,
        ),
    )


def _effective_search_filter(arguments: argparse.Namespace) -> SearchFilter:
    base = (
        get_preset(arguments.preset, arguments.preset_file).filters
        if arguments.preset
        else SearchFilter()
    )
    mib = 1024 * 1024
    return SearchFilter(
        text=arguments.text if arguments.text is not None else base.text,
        categories=(
            tuple(arguments.category)
            if arguments.category is not None
            else base.categories
        ),
        min_size_bytes=(
            arguments.min_size_mib * mib
            if arguments.min_size_mib is not None
            else base.min_size_bytes
        ),
        max_size_bytes=(
            arguments.max_size_mib * mib
            if arguments.max_size_mib is not None
            else base.max_size_bytes
        ),
        naming_warning_only=(
            arguments.name_warning_only
            if arguments.name_warning_only is not None
            else base.naming_warning_only
        ),
        duplicate_only=(
            arguments.duplicates_only
            if arguments.duplicates_only is not None
            else base.duplicate_only
        ),
        page=arguments.page,
        page_size=(
            arguments.page_size
            if arguments.page_size is not None
            else base.page_size
        ),
        sort_by=arguments.sort if arguments.sort is not None else base.sort_by,
        descending=(
            arguments.descending
            if arguments.descending is not None
            else base.descending
        ),
        fulltext_mode=(
            arguments.fulltext
            if arguments.fulltext is not None
            else base.fulltext_mode
        ),
    )


def run_search(arguments: argparse.Namespace) -> int:
    if arguments.build_fulltext_index:
        built = build_fulltext_index(
            arguments.database,
            session_id=arguments.session_id,
            lock_timeout_seconds=arguments.lock_timeout,
        )
        stream = sys.stderr if arguments.json else sys.stdout
        print(
            status_text(
                f"Schneller Suchindex: {built.indexed_files} Dateien",
                mode=colour_mode(arguments),
                stream=stream,
            ),
            file=stream,
        )
    filters = _effective_search_filter(arguments)
    page = search_index(
        arguments.database,
        session_id=arguments.session_id,
        filters=filters,
    )
    if arguments.json:
        print(json.dumps(page.to_dict(), ensure_ascii=False, indent=2))
        return 0
    search_kind = (
        "schnelle Volltextsuche" if page.engine == "fts5" else "normale Suche"
    )
    print(
        f"Ordner: {page.root} | Scan: #{page.session_id} | Suchart: {search_kind}"
    )
    print(f"Treffer: {page.total_rows} | Seite {page.page} von {page.total_pages}")
    if arguments.preset:
        print(
            paint(
                f"Vorlage: {arguments.preset}",
                "blue",
                mode=colour_mode(arguments),
            )
        )
    if not page.rows:
        print(
            traffic_text(
                TrafficLight("yellow", "Keine Treffer", "Filter oder Suchwort prüfen"),
                mode=colour_mode(arguments),
            )
        )
        return 0
    for row in page.rows:
        if row.filename_warnings and row.duplicate_sha256:
            light = TrafficLight(
                "red",
                "Mehrfach prüfen",
                "Namenshinweis und Duplikat",
            )
        elif row.filename_warnings:
            light = TrafficLight("yellow", "Name prüfen", "auffälliger Dateiname")
        elif row.duplicate_sha256:
            light = TrafficLight(
                "yellow",
                "Duplikat prüfen",
                "Datei gehört zu einer Duplikatgruppe",
            )
        else:
            light = TrafficLight(
                "green",
                "Unauffällig",
                "keine erkannten Hinweise",
            )
        print(
            f"{traffic_text(light, mode=colour_mode(arguments))}\n"
            f"  {row.relative_path} | {row.category} | "
            f"{human_size(row.size_bytes)}"
        )
    if page.page < page.total_pages:
        print(f"Nächste Seite: --page {page.page + 1}")
    print_hint(
        arguments,
        "Suchvorlage speichern: datenbanktool index presets save NAME ...",
    )
    return 0


def _preset_filter(arguments: argparse.Namespace) -> SearchFilter:
    mib = 1024 * 1024
    return SearchFilter(
        text=arguments.text,
        categories=tuple(arguments.category),
        min_size_bytes=(
            arguments.min_size_mib * mib
            if arguments.min_size_mib is not None
            else None
        ),
        max_size_bytes=(
            arguments.max_size_mib * mib
            if arguments.max_size_mib is not None
            else None
        ),
        naming_warning_only=arguments.name_warning_only,
        duplicate_only=arguments.duplicates_only,
        page=1,
        page_size=arguments.page_size,
        sort_by=arguments.sort,
        descending=arguments.descending,
        fulltext_mode=arguments.fulltext,
    )


def _preset_path(arguments: argparse.Namespace) -> Path:
    return arguments.preset_file or default_preset_path()


def _optional_prechange_backup(
    arguments: argparse.Namespace,
    *,
    existing_required: bool,
) -> ConfigBackupResult | None:
    if not arguments.backup_before_change:
        return None
    try:
        get_preset(arguments.name, arguments.preset_file)
    except KeyError:
        if existing_required:
            raise
        return None
    return create_config_backup(_preset_path(arguments))


def _print_config_backup(
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


def run_presets(arguments: argparse.Namespace) -> int:
    if arguments.preset_command == "list":
        presets = list_presets(arguments.preset_file)
        if arguments.json:
            print(
                json.dumps(
                    [item.to_dict() for item in presets],
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
                        "keine Suchvorlagen gespeichert",
                    ),
                    mode=colour_mode(arguments),
                )
            )
            print_hint(
                arguments,
                "Speichern: datenbanktool index presets save NAME ...",
            )
            return 0
        for preset in presets:
            description = f" – {preset.description}" if preset.description else ""
            print(
                f"{paint('●', 'green', mode=colour_mode(arguments))} "
                f"{preset.name}{description}"
            )
        return 0
    if arguments.preset_command == "show":
        preset = get_preset(arguments.name, arguments.preset_file)
        if arguments.json:
            print(json.dumps(preset.to_dict(), ensure_ascii=False, indent=2))
            return 0
        print(paint(preset.name, "bold", mode=colour_mode(arguments)))
        print(f"Beschreibung: {preset.description or 'keine'}")
        print(f"Suchwort: {preset.filters.text or 'keines'}")
        print(f"Dateitypen: {', '.join(preset.filters.categories) or 'alle'}")
        print(
            f"Größe: {preset.filters.min_size_bytes or 0} bis "
            f"{preset.filters.max_size_bytes or 'offen'} Byte"
        )
        print(
            "Nur Namenshinweise: "
            f"{'ja' if preset.filters.naming_warning_only else 'nein'}"
        )
        print(
            f"Nur Duplikate: {'ja' if preset.filters.duplicate_only else 'nein'}"
        )
        print(
            f"Sortierung: {preset.filters.sort_by} | "
            f"Seitengröße: {preset.filters.page_size}"
        )
        print_hint(
            arguments,
            f"Starten: datenbanktool index search DATENBANK "
            f"--preset \"{preset.name}\"",
        )
        return 0
    if arguments.preset_command == "save":
        backup = (
            _optional_prechange_backup(arguments, existing_required=False)
            if arguments.replace
            else None
        )
        preset = save_preset(
            arguments.name,
            _preset_filter(arguments),
            description=arguments.description,
            path=arguments.preset_file,
            replace=arguments.replace,
        )
        _print_config_backup(backup, arguments)
        print(
            traffic_text(
                TrafficLight("green", "Vorlage gespeichert", preset.name),
                mode=colour_mode(arguments),
            )
        )
        print_hint(
            arguments,
            f"Starten: datenbanktool index search DATENBANK "
            f"--preset \"{preset.name}\"",
        )
        return 0
    if arguments.preset_command == "delete":
        if not arguments.yes:
            raise ValueError("Löschen benötigt die ausdrückliche Bestätigung --yes")
        backup = _optional_prechange_backup(arguments, existing_required=True)
        deleted = delete_preset(arguments.name, path=arguments.preset_file)
        _print_config_backup(backup, arguments)
        print(
            traffic_text(
                TrafficLight("yellow", "Vorlage gelöscht", deleted.name),
                mode=colour_mode(arguments),
            )
        )
        return 0
    raise ValueError("Unbekannter Suchvorlagen-Befehl")
