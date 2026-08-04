"""Schreibgeschützte SQLite-Analyse ohne Ausgabeabhängigkeiten."""

from pathlib import Path
import sqlite3
from typing import Any


class DatabaseError(ValueError):
    """Ein in einfacher Sprache darstellbarer Eingabefehler."""


def validate_database(path_text: str) -> Path:
    """Prüft einen Datenbankpfad und gibt dessen absolute Form zurück."""
    if not path_text.strip():
        raise DatabaseError("Der Datenbankpfad darf nicht leer sein.")
    path = Path(path_text).expanduser()
    if not path.exists():
        raise DatabaseError(f"Die Datei wurde nicht gefunden: {path}")
    if not path.is_file():
        raise DatabaseError(f"Der Pfad ist keine Datei: {path}")
    try:
        with path.open("rb") as database_file:
            header = database_file.read(16)
    except OSError as error:
        raise DatabaseError(f"Die Datei kann nicht gelesen werden: {path}") from error
    if header != b"SQLite format 3\x00":
        raise DatabaseError(f"Die Datei ist keine gültige SQLite-Datenbank: {path}")
    return path.resolve()


def _connect(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def list_tables(path_text: str) -> list[dict[str, Any]]:
    """Liefert Tabellen und Spalten in stabiler Reihenfolge."""
    path = validate_database(path_text)
    try:
        with _connect(path) as connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_schema "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
            result = []
            for (name,) in rows:
                columns = connection.execute(
                    "SELECT name, type, [notnull], pk FROM pragma_table_info(?) ORDER BY cid",
                    (name,),
                ).fetchall()
                result.append({
                    "name": name,
                    "columns": [
                        {"name": item[0], "type": item[1], "required": bool(item[2]), "primary_key": bool(item[3])}
                        for item in columns
                    ],
                })
            return result
    except sqlite3.Error as error:
        raise DatabaseError(f"Die Datenbank konnte nicht analysiert werden: {error}") from error


def summarize(path_text: str) -> dict[str, Any]:
    """Erstellt eine kompakte Übersicht der Datenbankstruktur."""
    path = validate_database(path_text)
    tables = list_tables(str(path))
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "table_count": len(tables),
        "column_count": sum(len(table["columns"]) for table in tables),
    }
