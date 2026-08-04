from __future__ import annotations

import argparse
import sqlite3
import sys
from typing import Sequence

from datenbanktool import __version__
from datenbanktool.cli_acceptance import register_acceptance_parser
from datenbanktool.cli_common import parser
from datenbanktool.cli_contract import dispatch
from datenbanktool.cli_folder_compare import register_folder_compare_parser
from datenbanktool.cli_help import register_explain_parser
from datenbanktool.cli_index import register_admin_parsers, register_scan_index_parsers
from datenbanktool.cli_reports import (
    register_index_report_parsers,
    register_report_parser,
)
from datenbanktool.cli_scan import register_scan_parser
from datenbanktool.cli_search import register_preset_parsers, register_search_parser
from datenbanktool.core.index_database import IndexErrorBase
from datenbanktool.core.index_lock import IndexLockedError
from datenbanktool.core.presentation import paint


def build_parser() -> argparse.ArgumentParser:
    root = parser(
        prog="datenbanktool",
        description=(
            "Sicheres Linux-Werkzeug für große Datensammlungen.\n"
            "Farben und Ampeln unterstützen die Orientierung, werden aber "
            "immer durch Klartext ergänzt."
        ),
        epilog=(
            "Globale Anzeigeoptionen stehen vor dem Befehl, zum Beispiel:\n"
            "  datenbanktool --color always index folders index.sqlite3\n"
            "Detaillierte Auswirkungen: datenbanktool explain"
        ),
    )
    root.add_argument("--version", action="version", version=__version__)
    root.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help=(
            "Farben automatisch, immer oder nie verwenden. "
            "Die Umgebungsvariable NO_COLOR wird respektiert."
        ),
    )
    root.add_argument(
        "--hints",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Kurze Bedienhinweise ein- oder ausschalten.",
    )
    subparsers = root.add_subparsers(dest="command", required=True)

    register_explain_parser(subparsers)
    register_scan_parser(subparsers)
    register_acceptance_parser(subparsers)

    index = subparsers.add_parser(
        "index",
        help="SQLite-Index verwalten und durchsuchen",
        description=(
            "Alle Indexfunktionen arbeiten lokal. "
            "Originaldatei-Schreibzugriffe bleiben gesperrt."
        ),
    )
    index_subparsers = index.add_subparsers(dest="index_command", required=True)
    register_scan_index_parsers(index_subparsers)
    register_search_parser(index_subparsers)
    register_index_report_parsers(index_subparsers)
    register_folder_compare_parser(index_subparsers)
    register_preset_parsers(index_subparsers)
    register_admin_parsers(index_subparsers)

    register_report_parser(subparsers)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    root = build_parser()
    arguments = root.parse_args(argv)
    try:
        return dispatch(arguments)
    except (
        FileExistsError,
        FileNotFoundError,
        IndexErrorBase,
        IndexLockedError,
        KeyError,
        NotADirectoryError,
        OSError,
        sqlite3.Error,
        TypeError,
        ValueError,
    ) as error:
        message = paint(
            f"Fehler: {error}",
            "red",
            mode=getattr(arguments, "color", "auto"),
            stream=sys.stderr,
        )
        print(message, file=sys.stderr)
        return 2
