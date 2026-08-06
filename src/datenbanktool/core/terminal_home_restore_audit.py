from __future__ import annotations

import os
from pathlib import Path

from datenbanktool.core.restore_audit_identity import require_sha256
from datenbanktool.core.terminal_home import TerminalHome as BaseTerminalHome


class TerminalHome(BaseTerminalHome):
    """Add explicit restore-log paths and read-only protocol verification."""

    def _backup_action(self) -> str:
        pending = getattr(self, "_pending_backup_action", None)
        if pending is not None:
            del self._pending_backup_action
            return str(pending)

        aliases = {
            "": "list",
            "a": "list",
            "anzeigen": "list",
            "liste": "list",
            "list": "list",
            "s": "create",
            "sichern": "create",
            "erstellen": "create",
            "create": "create",
            "w": "restore",
            "wiederherstellen": "restore",
            "restore": "restore",
            "p": "verify-log",
            "prüfen": "verify-log",
            "pruefen": "verify-log",
            "protokoll prüfen": "verify-log",
            "protokoll pruefen": "verify-log",
            "verify": "verify-log",
            "verify-log": "verify-log",
            "l": "delete",
            "löschen": "delete",
            "loeschen": "delete",
            "delete": "delete",
        }
        while True:
            value = self._read(
                "Aktion [anzeigen/sichern/wiederherstellen/Protokoll prüfen/löschen, "
                "Standard anzeigen, ? Hilfe]: ",
                help_text=(
                    "Anzeigen und Protokoll prüfen lesen nur. Sichern erstellt eine neue "
                    "SQLite-Kopie. Wiederherstellen erstellt vor dem Überschreiben eine "
                    "Rückfallsicherung und kann danach optional genau einen ausdrücklich "
                    "angegebenen neuen Protokollpfad verwenden."
                ),
            ).casefold()
            if value in aliases:
                return aliases[value]
            self._write(
                "Bitte anzeigen, sichern, wiederherstellen, Protokoll prüfen, löschen "
                "oder ? eingeben.",
                error=True,
            )

    @staticmethod
    def _explicit_absolute_path(value: str, label: str) -> Path:
        if not value or "\x00" in value:
            raise ValueError(f"{label} muss einen nicht leeren vollständigen Pfad enthalten.")
        expanded = Path(value).expanduser()
        if not expanded.is_absolute():
            raise ValueError(f"{label} muss als absoluter Pfad oder mit ~ angegeben werden.")
        return Path(os.path.abspath(os.fspath(expanded)))

    def _append_optional_restore_log(self, command: list[str]) -> list[str]:
        while True:
            value = self._read(
                "Optionaler neuer Protokollpfad; leer bedeutet kein Protokoll [? Hilfe]: ",
                help_text=(
                    "Nur bei einer ausdrücklichen Eingabe wird --restore-log ergänzt. "
                    "Das Tool schlägt keinen Pfad vor und überschreibt keine vorhandene Datei."
                ),
            )
            if not value:
                self._write("Kein Wiederherstellungsprotokoll vorgemerkt.")
                return command
            try:
                target = self._explicit_absolute_path(
                    value,
                    "Der Wiederherstellungsprotokollpfad",
                )
            except ValueError as error:
                self._write(str(error), error=True)
                continue
            if target.is_symlink():
                self._write(
                    "Der Protokollpfad ist eine symbolische Verknüpfung und wurde abgelehnt.",
                    error=True,
                )
                continue
            if target.exists():
                self._write(
                    "Der Protokollpfad existiert bereits und wird nicht überschrieben.",
                    error=True,
                )
                continue
            self._write(f"Neuer Wiederherstellungsprotokollpfad: {target}")
            return [*command, "--restore-log", str(target)]

    def _build_restore_audit_verification(self) -> list[str]:
        while True:
            value = self._required(
                "Wiederherstellungsprotokoll als vollständigen Pfad angeben",
                help_text=(
                    "Es wird genau diese eine Datei geprüft. Das Tool sucht keine "
                    "Protokolle automatisch und verändert oder löscht nichts."
                ),
            )
            try:
                protocol = self._explicit_absolute_path(
                    value,
                    "Der Wiederherstellungsprotokollpfad",
                )
            except ValueError as error:
                self._write(str(error), error=True)
                continue
            break

        self._write(f"Vollständiger Protokollpfad: {protocol}")
        command = ["index", "backups", "verify-log", str(protocol)]
        while True:
            expected = self._read(
                "Optional erwartete Protokoll-SHA-256; leer überspringt den Pin [? Hilfe]: ",
                help_text=(
                    "Nur ein ausdrücklich eingegebener kleingeschriebener SHA-256-Wert "
                    "wird verwendet. Es findet keine automatische Ermittlung oder Speicherung statt."
                ),
            )
            if not expected:
                self._write("Keine erwartete Protokoll-SHA-256 vorgemerkt.")
                return command
            try:
                confirmed = require_sha256(expected)
            except ValueError as error:
                self._write(str(error), error=True)
                continue
            self._write(f"Erwartete Protokoll-SHA-256: {confirmed}")
            return [
                *command,
                "--expected-protocol-sha256",
                confirmed,
            ]

    def _build_backup(self) -> list[str]:
        action = self._backup_action()
        if action == "verify-log":
            return self._build_restore_audit_verification()

        self._pending_backup_action = action
        command = super()._build_backup()
        if command[:3] == ["index", "backups", "restore"]:
            return self._append_optional_restore_log(command)
        return command
