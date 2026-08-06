from __future__ import annotations

import shlex
from pathlib import Path

from datenbanktool.core import guided_home as guided
from datenbanktool.core.backup_catalog import BackupItem, list_backups
from datenbanktool.core.config_restore import (
    ConfigRestoreComparison,
    compare_config_backup,
)
from datenbanktool.core.guided_home import (
    InputClosed,
    MenuAction,
    UserCancelled,
    menu_actions,
)
from datenbanktool.core.presentation import TrafficLight, status_text, traffic_text
from datenbanktool.core.recovery import (
    RecoveryCandidate,
    discard_recovery_candidate,
    load_recovery_candidates,
)


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
                    "Erstellt und prüft Sicherungen; Konfigurationssicherungen können "
                    "einzeln verglichen oder kontrolliert wiederhergestellt werden."
                )
                writes = (
                    "Anzeigen und Vergleichen sind rein lesend. Erstellen, "
                    "Wiederherstellen oder einzelnes Löschen braucht eine sichtbare "
                    "Bestätigung."
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
            "Kurz: Sicherungen erstellen oder prüfen, eine Konfigurationssicherung "
            "vergleichen, kontrolliert wiederherstellen oder einzeln löschen."
        )
        if level in {"detail", "guided"}:
            self._write(
                "Wirkung: Anzeigen und Vergleichen lesen nur. Wiederherstellen ersetzt "
                "genau eine aktive Vorlagendatei erst nach automatischer Rückfallsicherung."
            )
            self._write(
                "Schutz: Nur geprüfte Such- oder Zeitreihen-Sicherungen sind zulässig. "
                "Indexsicherungen, beschädigte Dateien, unbekannte Pfade und Symlinks "
                "werden abgelehnt."
            )
            self._write(
                "Aufbewahrung: Ausgewählte Sicherung und Rückfallsicherung bleiben "
                "erhalten. Es gibt keine automatische Rotation oder Löschung."
            )
        if level == "guided":
            self._write("Schritte:")
            self._write("  1. Indexdatei angeben.")
            self._write(
                "  2. Erstellen, Anzeigen, Wiederherstellen oder Löschen wählen."
            )
            self._write(
                "  3. Bei Wiederherstellung eine geprüfte Konfigurationssicherung wählen."
            )
            self._write(
                "  4. Hinzufügen, Entfernen und Ersetzen im Nur-Lese-Vergleich prüfen."
            )
            self._write("  5. Den Sicherungsnamen exakt wiederholen.")
            self._write(
                "  6. Den vollständigen Befehl ausdrücklich bestätigen; erst dann wird "
                "die Rückfallsicherung erstellt."
            )
        self._write("-" * 72)

    def _show_recovery_items(
        self,
        candidates: tuple[RecoveryCandidate, ...],
    ) -> None:
        self._write("\n" + "!" * 72)
        self._write(f"Gespeicherte Wiederanläufe: {len(candidates)}")
        self._write(
            "Jeder Eintrag wurde getrennt und nur lesend gegen Ordner, Indexdatei "
            "und SQLite-Sitzung geprüft."
        )
        for number, candidate in enumerate(candidates, 1):
            state = (
                "fortsetzbar" if candidate.resumable else "derzeit nicht fortsetzbar"
            )
            self._write(
                f"  {number}. {candidate.operation_label} | {state} | "
                f"{candidate.validation_label}"
            )
            self._write(f"     Ordner: {candidate.root}")
            self._write(f"     Index:  {candidate.database}")
        self._write("!" * 72)

    def _choose_recovery(
        self,
        candidates: tuple[RecoveryCandidate, ...],
    ) -> RecoveryCandidate | None:
        while True:
            value = self._read(
                "Wiederanlauf als Nummer wählen; leer oder n öffnet die normale Startseite "
                "[? Hilfe]: ",
                help_text=(
                    "Eine Nummer öffnet genau diesen Eintrag. Dort kann er fortgesetzt "
                    "oder bewusst verworfen werden. Leer oder n verändert keinen Eintrag."
                ),
            ).casefold()
            if not value or value in {"n", "nein", "normal", "weiter"}:
                return None
            if value.isdigit():
                index = int(value) - 1
                if 0 <= index < len(candidates):
                    return candidates[index]
            self._write("Bitte eine angezeigte Nummer, n oder ? eingeben.", error=True)

    def _show_recovery_detail(self, candidate: RecoveryCandidate) -> None:
        self._write("\n" + "-" * 72)
        self._write("Wiederanlauf im Detail")
        self._write(f"Art: {candidate.operation_label}")
        self._write(f"Ordner: {candidate.root}")
        self._write(f"Indexdatei: {candidate.database}")
        if candidate.session_id is not None:
            self._write(
                f"Gespeicherter Stand: Prüfung #{candidate.session_id} | "
                f"{candidate.status}/{candidate.phase} | Dateien: {candidate.imported_count}"
            )
        else:
            self._write(f"Gespeicherter Zustand: {candidate.status}/{candidate.phase}")
        self._write(f"Prüfergebnis: {candidate.validation_label}")
        self._write(f"Begründung: {candidate.validation_detail}")
        self._write("Geprüfter Wiederanlaufbefehl:")
        self._write("  " + shlex.join(["datenbanktool", *candidate.command]))
        self._write("-" * 72)

    def _recovery_action(self, candidate: RecoveryCandidate) -> str:
        aliases = {
            "": "back",
            "z": "back",
            "zurück": "back",
            "zurueck": "back",
            "back": "back",
            "v": "discard",
            "verwerfen": "discard",
            "discard": "discard",
        }
        if candidate.resumable:
            aliases.update(
                {
                    "f": "resume",
                    "fortsetzen": "resume",
                    "resume": "resume",
                    "j": "resume",
                    "ja": "resume",
                }
            )
        choices = "fortsetzen/verwerfen/zurück" if candidate.resumable else "verwerfen/zurück"
        while True:
            value = self._read(
                f"Aktion [{choices}, Standard zurück, ? Hilfe]: ",
                help_text=(
                    "Fortsetzen startet exakt den sichtbaren --resume-Befehl. Verwerfen "
                    "entfernt nur diesen internen Hinweis; Index und Originaldateien "
                    "bleiben unverändert."
                ),
            ).casefold()
            if value in aliases:
                return aliases[value]
            self._write(f"Bitte {choices} oder ? eingeben.", error=True)

    def _manage_recovery(self, candidate: RecoveryCandidate) -> None:
        self._show_recovery_detail(candidate)
        action = self._recovery_action(candidate)
        if action == "back":
            return
        if action == "discard":
            if not self._yes_no(
                "Nur diesen Wiederanlaufhinweis bewusst verwerfen?",
                help_text=(
                    "Ja entfernt ausschließlich den internen Eintrag. Die Indexdatei, "
                    "der Quellordner und gespeicherte Scan-Sitzungen werden nicht verändert."
                ),
            ):
                self._write("Nicht verworfen. Der Eintrag bleibt gespeichert.")
                return
            if discard_recovery_candidate(candidate.record_id):
                self._write("Wiederanlaufhinweis verworfen. Index und Ordner blieben unverändert.")
            else:
                self._write("Der Eintrag konnte nicht verworfen werden.", error=True)
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
        if result == 0:
            discard_recovery_candidate(candidate.record_id)
        else:
            self._write(
                "Dieser Wiederanlauf bleibt gespeichert. Prüfe den Index mit "
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
            "w": "restore",
            "wiederherstellen": "restore",
            "restore": "restore",
            "l": "delete",
            "löschen": "delete",
            "loeschen": "delete",
            "delete": "delete",
        }
        while True:
            value = self._read(
                "Aktion [anzeigen/sichern/wiederherstellen/löschen, Standard anzeigen, "
                "? Hilfe]: ",
                help_text=(
                    "Anzeigen prüft nur. Sichern erstellt eine neue SQLite-Kopie. "
                    "Wiederherstellen vergleicht eine Konfigurationssicherung und erstellt "
                    "vor dem Überschreiben automatisch eine Rückfallsicherung. Löschen "
                    "entfernt genau eine erkannte Sicherung."
                ),
            ).casefold()
            if value in aliases:
                return aliases[value]
            self._write(
                "Bitte anzeigen, sichern, wiederherstellen, löschen oder ? eingeben.",
                error=True,
            )

    def _show_backup_items(
        self,
        database: str,
        *,
        configuration_only: bool = False,
    ) -> tuple[BackupItem, ...]:
        items = list_backups(Path(database))
        if configuration_only:
            items = tuple(item for item in items if item.kind == "configuration")
        if not items:
            message = (
                "Keine erkannten Konfigurationssicherungen gefunden."
                if configuration_only
                else "Keine erkannten Index- oder Konfigurationssicherungen gefunden."
            )
            self._write(message)
            return ()
        heading = (
            "Geprüfte Konfigurationssicherungen – neueste zuerst:"
            if configuration_only
            else "Geprüfte Sicherungen – neueste zuerst:"
        )
        self._write(heading)
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

    def _show_restore_comparison(
        self,
        comparison: ConfigRestoreComparison,
    ) -> None:
        self._write("\nNur-Lese-Vergleich vor der Wiederherstellung")
        self._write(f"  Art: {comparison.kind_label}")
        self._write(f"  Sicherung: {comparison.backup}")
        self._write(f"  Aktive Datei: {comparison.active}")
        self._write(f"  Ergebnis: {comparison.validation_detail}")
        groups = (
            ("Würde hinzufügen", comparison.add_names),
            ("Würde entfernen", comparison.remove_names),
            ("Würde ersetzen", comparison.change_names),
            ("Unverändert", comparison.unchanged_names),
        )
        for label, values in groups:
            self._write(f"  {label}: {', '.join(values) if values else 'keine'}")
        self._write(
            "  Vor dem Überschreiben wird automatisch eine neue geprüfte "
            "Rückfallsicherung der aktiven Datei erstellt."
        )
        self._write(
            "  Die ausgewählte Sicherung und die Rückfallsicherung werden weder "
            "automatisch rotiert noch gelöscht."
        )

    def _build_backup(self) -> list[str]:
        action = self._backup_action()
        if action == "create":
            return super()._build_backup()
        database = self._database()
        if action == "list":
            return ["index", "backups", "list", database]

        items = self._show_backup_items(
            database,
            configuration_only=action == "restore",
        )
        if not items:
            raise UserCancelled
        selected = self._choose_backup(items)

        if action == "restore":
            try:
                comparison = compare_config_backup(
                    Path(database),
                    Path(selected.path),
                )
            except (OSError, ValueError) as error:
                self._write(str(error), error=True)
                raise UserCancelled from error
            self._show_restore_comparison(comparison)
            if not comparison.can_restore:
                self._write(
                    "Sicherung und aktive Konfiguration sind bereits identisch. "
                    "Es wurde nichts vorgemerkt."
                )
                raise UserCancelled
            checked = self._required(
                f"Sicherungsnamen exakt wiederholen ({selected.name})",
                help_text=(
                    "Der angezeigte Sicherungsname muss vollständig übereinstimmen. "
                    "Danach wird der Wiederherstellungsbefehl noch einmal sichtbar "
                    "bestätigt."
                ),
            )
            if checked != selected.name:
                self._write(
                    "Sicherungsname stimmt nicht überein. Es wurde nichts "
                    "wiederhergestellt.",
                    error=True,
                )
                raise UserCancelled
            return [
                "index",
                "backups",
                "restore",
                database,
                selected.path,
                "--confirm-name",
                selected.name,
                "--yes",
            ]

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

    def _backup_before_preset_change(self, command: list[str]) -> list[str]:
        if self._yes_no(
            "Vor dieser Änderung eine geprüfte Konfigurationssicherung erstellen?",
            default=True,
            help_text=(
                "Ja erzeugt zuerst eine neue zeitgestempelte JSON-Sicherung. "
                "Es gibt keine automatische Rotation oder Löschung."
            ),
        ):
            command.append("--backup-before-change")
        return command

    def _build_timeline_preset_replace(self) -> list[str]:
        return self._backup_before_preset_change(
            super()._build_timeline_preset_replace()
        )

    def _build_timeline_preset_delete(self) -> list[str]:
        return self._backup_before_preset_change(
            super()._build_timeline_preset_delete()
        )

    def run(self) -> int:
        try:
            while True:
                candidates = load_recovery_candidates()
                if not candidates:
                    break
                self._show_recovery_items(candidates)
                try:
                    candidate = self._choose_recovery(candidates)
                except UserCancelled:
                    self._write("Wiederanlaufwahl beendet. Alle Einträge bleiben gespeichert.")
                    break
                if candidate is None:
                    self._write("Kein Eintrag verändert. Die normale Startseite wird geöffnet.")
                    break
                self._manage_recovery(candidate)
        except InputClosed:
            self._write("Eingabe beendet. Alle Wiederanläufe bleiben gespeichert.")
            return 0
        return super().run()


__all__ = [
    "InputClosed",
    "MenuAction",
    "TerminalHome",
    "UserCancelled",
    "menu_actions",
]
