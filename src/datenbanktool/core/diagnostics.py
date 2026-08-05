from __future__ import annotations

import os
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote

from datenbanktool.core.durable_files import atomic_write_text
from datenbanktool.core.index_types import SCHEMA_VERSION, normalise_database_path
from datenbanktool.core.run_journal import default_state_directory, previous_unfinished_run


@dataclass(frozen=True, slots=True)
class DiagnosticCheck:
    name: str
    level: str
    message: str
    technical_detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DiagnosticResult:
    ready: bool
    checks: tuple[DiagnosticCheck, ...]

    def to_dict(self) -> dict[str, object]:
        return {"ready": self.ready, "checks": [item.to_dict() for item in self.checks]}


def _directory_check(name: str, directory: Path) -> DiagnosticCheck:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="diagnose-", dir=directory) as temporary_directory:
            target = Path(temporary_directory) / "write-test.txt"
            atomic_write_text(target, "startklar\n", mode=0o600)
            if target.read_text(encoding="utf-8") != "startklar\n":
                raise OSError("Rücklesen lieferte einen anderen Inhalt")
    except OSError as error:
        return DiagnosticCheck(
            name,
            "red",
            "Hier kann das Tool seinen sicheren Zwischenstand nicht speichern.",
            f"Schreib-/fsync-/replace-Test fehlgeschlagen: {error}",
        )
    return DiagnosticCheck(
        name,
        "green",
        "Sicheres Speichern funktioniert.",
        f"Atomarer Schreibtest mit fsync und os.replace in {directory}",
    )


def _database_checks(database_path: Path) -> list[DiagnosticCheck]:
    target = normalise_database_path(database_path)
    if not target.exists():
        return [
            DiagnosticCheck(
                "indexdatei",
                "red",
                "Die gewählte Indexdatei wurde nicht gefunden.",
                f"Pfad fehlt: {target}",
            )
        ]
    uri = f"file:{quote(str(target), safe='/')}?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
        try:
            connection.execute("PRAGMA query_only=ON")
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            quick_check = tuple(str(row[0]) for row in connection.execute("PRAGMA quick_check"))
        finally:
            connection.close()
    except sqlite3.Error as error:
        return [
            DiagnosticCheck(
                "indexdatei",
                "red",
                "Die Indexdatei lässt sich nicht sicher lesen.",
                f"SQLite-Fehler im Nur-Lese-Modus: {error}",
            )
        ]
    checks = [
        DiagnosticCheck(
            "indexdatei",
            "green" if quick_check == ("ok",) else "red",
            "Die Indexdatei ist lesbar und unbeschädigt."
            if quick_check == ("ok",)
            else "Die Indexdatei meldet Unstimmigkeiten.",
            f"PRAGMA quick_check: {', '.join(quick_check)}",
        )
    ]
    if version > SCHEMA_VERSION:
        checks.append(
            DiagnosticCheck(
                "datenbankversion",
                "red",
                "Diese Indexdatei stammt aus einer neueren Tool-Version.",
                f"SQLite-Schema {version}, unterstützt bis {SCHEMA_VERSION}",
            )
        )
    else:
        checks.append(
            DiagnosticCheck(
                "datenbankversion",
                "green",
                "Die gespeicherte Datenbankversion wird unterstützt.",
                f"SQLite-Schema {version}, unterstützt bis {SCHEMA_VERSION}",
            )
        )
    return checks


def run_diagnostics(database_path: Path | None = None) -> DiagnosticResult:
    checks: list[DiagnosticCheck] = []
    supported_python = sys.version_info >= (3, 10)
    checks.append(
        DiagnosticCheck(
            "python",
            "green" if supported_python else "red",
            "Die verwendete Python-Version passt."
            if supported_python
            else "Die verwendete Python-Version ist zu alt.",
            f"Python {sys.version.split()[0]}; benötigt mindestens 3.10",
        )
    )
    checks.append(
        DiagnosticCheck(
            "sqlite",
            "green",
            "Die lokale Datenbankfunktion ist verfügbar.",
            f"SQLite {sqlite3.sqlite_version}",
        )
    )
    config_base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    checks.append(_directory_check("einstellungen", config_base / "datenbanktool"))
    checks.append(_directory_check("zwischenstand", default_state_directory()))
    previous = previous_unfinished_run()
    checks.append(
        DiagnosticCheck(
            "letzter lauf",
            "yellow" if previous else "green",
            "Ein früherer Lauf wurde nicht sauber beendet; der letzte sichere Stand bleibt nutzbar."
            if previous
            else "Der vorherige Lauf wurde sauber beendet.",
            (
                f"Laufstatus {previous.get('status')}, gestartet {previous.get('started_utc')}"
                if previous
                else "Kein offener Lauf im Laufjournal"
            ),
        )
    )
    if database_path is not None:
        checks.extend(_database_checks(database_path))
    return DiagnosticResult(
        ready=all(item.level != "red" for item in checks),
        checks=tuple(checks),
    )
