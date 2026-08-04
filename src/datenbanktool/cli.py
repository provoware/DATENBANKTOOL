"""Kommandozeilenschnittstelle für das DATENBANKTOOL."""

import argparse
import json
import sys
from typing import Any, Sequence

from . import __version__
from .core import DatabaseError, list_tables, summarize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="datenbanktool",
        description="Analysiert eine lokale SQLite-Datenbank schreibgeschützt.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("summary", "Zeigt Größe sowie Tabellen- und Spaltenanzahl"),
        ("tables", "Zeigt Tabellen und deren Spalten"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("database", help="Pfad zu einer SQLite-Datei")
    return parser


def _as_text(command: str, data: Any) -> str:
    if command == "summary":
        return (
            f"Datenbank: {data['path']}\nGröße: {data['size_bytes']} Bytes\n"
            f"Tabellen: {data['table_count']}\nSpalten: {data['column_count']}"
        )
    if not data:
        return "Keine Tabellen gefunden."
    lines = []
    for table in data:
        lines.append(f"{table['name']} ({len(table['columns'])} Spalten)")
        lines.extend(f"  - {column['name']}: {column['type'] or 'ohne Typ'}" for column in table["columns"])
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        data = summarize(args.database) if args.command == "summary" else list_tables(args.database)
    except DatabaseError as error:
        if args.json:
            print(json.dumps({"error": str(error)}, ensure_ascii=False))
        else:
            print(f"Fehler: {error}", file=sys.stderr)
        return 2
    print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else _as_text(args.command, data))
    return 0
