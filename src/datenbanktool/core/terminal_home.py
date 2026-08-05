from __future__ import annotations

import shlex
from pathlib import Path

from datenbanktool.core import guided_home as guided
from datenbanktool.core.backup_catalog import BackupItem, list_backups
from datenbanktool.core.guided_home import (
    InputClosed,
    MenuAction,
    UserCancelled,
    menu_actions,
)
from datenbanktool.core.presentation import TrafficLight, status_text, traffic_text
from datenbanktool.core.recovery import RecoveryCandidate, load_recovery_candidate


class TerminalHome(guided.TerminalHome):
    """Guided home extended with verified recovery and backup management."""

    def _render(self) -> None:
        self._write("\n" + "=" * 72)
        self._write("DATENBANKTOOL – geführte Startseite")
        self._write("Nummer wählen. h = Hilfe, ?NUMMER = Details, gNUMMER = Anleitung.")
        self._write("q bricht den aktuellen Schritt ab, 0 beendet das Tool.")
        self._write("=" * 72)
        for action in guided.ACTIONS:
            topic = guided._get_topic(action.help_topic)
            title = topic.title
            quick = topic.quick
            writes = topic.writes
            if action.key == "7":
                title = "Sicherungen verwalten"
                quick = (
                    "Erstellt, prüft und zeigt Index- sowie Konfigurationssicherungen; "
                    "Löschen erfolgt nur einzeln."
                )
                writes = (
                    "Anzeigen ist rein lesend; Erstellen oder einzelnes Löschen braucht "
                    "eine sichtbare Bestätigung."
                )
            if action.confirmation_required:
                light = TrafficLight("yellow", "Bestätigung nötig", writes)
            else:
                light = TrafficLight("green", "Sicherer Direktstart", writes)
            self._write(f"{action.key}. {title}")
            self._write(f"   {quick}")
            self._write(
                "   "
                + traffic_text(
                    light,
                    mode=self.color_mode,
                    stream=self.output_stream,
                )
            )
        self._write("h. Hilfezentrum")
        self._write("0. Beenden")

    def _render_topic(self, topic_name: str, level: str) -> None:
        if topic_name != "backup":
            super()._render_topic(topic_name, level)
            return
        self._write("\n" + "-" * 72)
        self._write("Sicherungen verwalten")
        self._write(
            "Kurz: Sicherung erstellen, vorhandene Sicherungen prüfen oder genau eine "
            "ausgewählte Sicherung löschen."
        )
        if level in {"detail", "guided"}:
            self._write(
                "Wirkung: Die Übersicht liest nur. Eine neue Sicherung schreibt eine "
                "geprüfte Kopie. Löschen ist auf erkannte Sicherungen begrenzt."
            )
            self._write(
                "Schutz: Aktive Index-, Konfigurations- und Originaldateien sind vom "
                "Löschen ausgeschlossen. Symlinks werden abgelehnt."
            )
        if level == "guided":
            self._write("Schritte:")
            self._write("  1. Indexdatei angeben.")
            self._write("  2. Erstellen, Anzeigen oder Löschen wählen.")
            self._write("  3. Bei Löschen Status, Größe, Alter und Pfad prüfen.")
            self._write("  4. Den Dateinamen exakt wiederholen.")
            self._write("  5. Den vollständig angezeigten Befehl ausdrücklich bestätigen.")
        self._write("-" * 72)

    def _offer_recovery(self, candidate: RecoveryCandidate) -> None:
        self._write("\n" + "!" * 72)
        self._write("Unterbrochene Ordnerprüfung gefunden")
        self._write(
            "Der letzte bestätigte Zwischenstand kann fortgesetzt werden. "
            "Persönliche Dateien werden dabei nur gelesen."
        )
        self._write(f"Art: {candidate.operation_label}")
        self._write(f"Ordner: {candidate.root}")
        self._write(f"Indexdatei: {candidate.database}")
        self._write(
            f"Gespeicherter Stand: Prüfung #{candidate.session_id} | "
            f"{candidate.status}/{candidate.phase} | Dateien: {candidate.imported_count}"
        )
        self._write("Geprüfter Wiederanlaufbefehl:")
        self._write("  " + shlex.join(["datenbanktool", *candidate.command]))
        self._write("!" * 72)
        try:
            confirmed = self._yes_no(
                "Diesen Scan am bestätigten Zwischenstand fortsetzen?",
                help_text=(
                    "Ja startet exakt den angezeigten Befehl mit --resume. Nein lässt "
                    "den Wiederanlauf gespeichert und öffnet die normale Startseite."
                ),
            )
        except UserCancelled:
            confirmed = False
        if not confirmed:
            self._write("Nicht gestartet. Der Wiederanlauf bleibt für später gespeichert.")
            return
        result = int(self.command_runner(candidate.command))
        label = "erfolgreich fortgesetzt" if result == 0 else f"nicht abgeschlossen, Code {result}"
        self._write(
            "Wiederanlauf: "
            + status_text(
                label,
                mode=self.color_mode,
                stream=self.output_stream,
            )
        )
        if result != 0:
            self._write(
                "Der bestätigte Wiederanlauf bleibt gespeichert. Prüfe den Index mit "
                "datenbanktool check --database PFAD.",
                error=True,
            )

    def _backup_action(self) -> str:
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
            "l": "delete",
            "löschen": "delete",
            "loeschen": "delete",
            "delete": "delete",
        }
        while True:
            value = self._read(
                "Aktion [anzeigen/sichern/löschen, Standard anzeigen, ? Hilfe]: ",
                help_text=(
                    "Anzeigen prüft nur. Sichern erstellt eine neue SQLite-Kopie. "
                    "Löschen entfernt genau eine erkannte Sicherung nach Namensprüfung "
                    "und anschließender Befehlsbestätigung."
                ),
            ).casefold()
            if value in aliases:
                return aliases[value]
            self._write("Bitte anzeigen, sichern, löschen oder ? eingeben.", error=True)

    def _show_backup_items(self, database: str) -> tuple[BackupItem, ...]:
        items = list_backups(Path(database))
        if not items:
            self._write("Keine erkannten Index- oder Konfigurationssicherungen gefunden.")
            return ()
        self._write("Geprüfte Sicherungen – neueste zuerst:")
        for number, item in enumerate(items, 1):
            self._write(
                f"  {number}. {item.kind_label} | {item.status_label} | "
                f"{item.size_bytes} Byte"
            )
            self._write(f"     {item.name}")
            self._write(f"     {item.path}")
            self._write(f"     Technische Einzelheit: {item.technical_detail}")
        return items

    def _choose_backup(self, items: tuple[BackupItem, ...]) -> BackupItem:
        while True:
            value = self._required(
                "Sicherung als Nummer oder vollständigen Pfad wählen",
                help_text=(
                    "Die Nummer bezieht sich auf die gerade angezeigte Liste. Alternativ "
                    "den vollständigen Pfad exakt übernehmen."
                ),
            )
            if value.isdigit():
                index = int(value) - 1
                if 0 <= index < len(items):
                    return items[index]
            else:
                selected = next((item for item in items if item.path == value), None)
                if selected is not None:
                    return selected
            self._write("Diese Sicherung wurde in der geprüften Liste nicht gefunden.", error=True)

    def _build_backup(self) -> list[str]:
        action = self._backup_action()
        if action == "create":
            return super()._build_backup()
        database = self._database()
        if action == "list":
            return ["index", "backups", "list", database]
        items = self._show_backup_items(database)
        if not items:
            raise UserCancelled
        selected = self._choose_backup(items)
        self._write("Zum Löschen ausgewählt:")
        self._write(f"  Art: {selected.kind_label}")
        self._write(f"  Status: {selected.status_label}")
        self._write(f"  Größe: {selected.size_bytes} Byte")
        self._write(f"  Pfad: {selected.path}")
        checked = self._required(
            f"Dateinamen exakt wiederholen ({selected.name})",
            help_text=(
                "Nur der reine Dateiname muss exakt stimmen. Danach wird der vollständige "
                "Löschbefehl noch einmal sichtbar bestätigt."
            ),
        )
        if checked != selected.name:
            self._write("Dateiname stimmt nicht überein. Es wurde nichts gelöscht.", error=True)
            raise UserCancelled
        return [
            "index",
            "backups",
            "delete",
            database,
            selected.path,
            "--confirm-name",
            selected.name,
            "--yes",
        ]

    def run(self) -> int:
        candidate = load_recovery_candidate()
        if candidate is not None:
            try:
                self._offer_recovery(candidate)
            except InputClosed:
                self._write("Eingabe beendet. Der Wiederanlauf bleibt gespeichert.")
                return 0
        return super().run()


__all__ = [
    "InputClosed",
    "MenuAction",
    "TerminalHome",
    "UserCancelled",
    "menu_actions",
]
