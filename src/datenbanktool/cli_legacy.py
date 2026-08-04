from __future__ import annotations

import argparse
import json

from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core import DatabaseError, list_tables, summarize


def register_legacy_parsers(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    summary = subparsers.add_parser("summary", help="SQLite-Datenbank kurz zusammenfassen")
    summary.add_argument("database")
    bind_handler(summary, _run_summary, CommandPolicy("summary"))

    tables = subparsers.add_parser("tables", help="SQLite-Tabellen und Spalten anzeigen")
    tables.add_argument("database")
    bind_handler(tables, _run_tables, CommandPolicy("tables"))


def _print_payload(arguments: argparse.Namespace, payload: object) -> None:
    if arguments.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(payload)


def _print_error(arguments: argparse.Namespace, error: Exception) -> None:
    if arguments.json:
        print(json.dumps({"error": str(error)}, ensure_ascii=False, indent=2))
        return
    print(f"Fehler: {error}")


def _run_summary(arguments: argparse.Namespace) -> int:
    try:
        _print_payload(arguments, summarize(arguments.database))
        return 0
    except DatabaseError as error:
        _print_error(arguments, error)
        return 2


def _run_tables(arguments: argparse.Namespace) -> int:
    try:
        _print_payload(arguments, list_tables(arguments.database))
        return 0
    except DatabaseError as error:
        _print_error(arguments, error)
        return 2
