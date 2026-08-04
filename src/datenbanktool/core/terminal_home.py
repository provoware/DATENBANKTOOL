from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Callable, Sequence, TextIO

from datenbanktool.core.presentation import TrafficLight, status_text, traffic_text

CommandRunner = Callable[[Sequence[str]], int]


class InputClosed(Exception):
    """Raised when an interactive input stream is closed."""


class UserCancelled(Exception):
    """Raised when the user cancels the current guided action."""


@dataclass(frozen=True, slots=True)
class MenuAction:
    key: str
    title: str
    description: str
    level: str
    impact_label: str
    impact_reason: str
    builder_name: str
    confirmation_required: bool = False


@dataclass(slots=True)
class HomeSession:
    last_database: str = ""
    last_root: str = ""


_ACTIONS = (
    MenuAction(
        "1",
        "Dateien suchen",
        "Dateien nach Name, Typ oder Größe finden.",
        "green",
        "Nur lesen",
        "Index und Originaldateien bleiben unverändert.",
        "search",
    ),
    MenuAction(
        "2",
        "Ordnerübersicht",
        "Ordnergrößen und größte Platzfresser anzeigen.",
        "green",
        "Nur lesen",
        "Die gespeicherten Scanwerte werden nur ausgewertet.",
        "folders",
    ),
    MenuAction(
        "3",
        "Änderungen anzeigen",
        "Neue, geänderte, verschobene und entfernte Dateien sehen.",
        "green",
        "Nur lesen",
        "Frühere Scanergebnisse werden nicht verändert.",
        "changes",
    ),
    MenuAction(
        "4",
        "Indexstatus prüfen",
        "Letzten Scan, Fehler und Duplikatgruppen anzeigen.",
        "green",
        "Nur lesen",
        "Es werden ausschließlich Statusdaten gelesen.",
        "status",
    ),
    MenuAction(
        "5",
        "Neuen Index anlegen",
        "Einen Ordnerbestand erstmals erfassen.",
        "yellow",
        "Schreibt Index",
        "Originaldateien bleiben unverändert; nur SQLite wird ergänzt.",
        "build",
        True,
    ),
    MenuAction(
        "6",
        "Ordner erneut prüfen",
        "Änderungen seit dem letzten Scan erfassen.",
        "yellow",
        "Schreibt Index",
        "Originaldateien bleiben unverändert; eine neue Scan-Sitzung entsteht.",
        "rescan",
        True,
    ),
    MenuAction(
        "7",
        "Index sichern",
        "Eine geprüfte Sicherheitskopie der SQLite-Datei erstellen.",
        "yellow",
        "Neue Sicherung",
        "Es entsteht eine neue Datei; Originaldaten bleiben unverändert.",
        "backup",
        True,
    ),
    MenuAction(
        "8",
        "Suchvorlagen anzeigen",
        "Gespeicherte häufige Suchen auflisten.",
        "green",
        "Nur lesen",
        "Die Vorlagendatei wird lediglich gelesen.",
        "presets",
    ),
    MenuAction(
        "9",
        "Funktionen erklären",
        "Zweck, Wirkung und Risiko verständlich anzeigen.",
        "green",
        "Nur Information",
        "Es werden keine Dateien verändert.",
        "explain",
    ),
)


def menu_actions() -> tuple[MenuAction, ...]:
    """Return the immutable, ordered home-screen action catalogue."""
    return _ACTIONS


class TerminalHome:
    """Guided, testable terminal home screen without shell execution."""

    def __init__(
        self,
        command_runner: CommandRunner,
        *,
        input_stream: TextIO,
        output_stream: TextIO,
        error_stream: TextIO,
        color_mode: str = "auto",
    ) -> None:
        self.command_runner = command_runner
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.error_stream = error_stream
        self.color_mode = color_mode
        self.session = HomeSession()
        keys = [action.key for action in _ACTIONS]
        if len(keys) != len(set(keys)):
            raise RuntimeError("Menü enthält doppelte Auswahlnummern")

    def _write(self, text: str = "", *, error: bool = False) -> None:
        stream = self.error_stream if error else self.output_stream
        stream.write(text + "\n")
        stream.flush()

    def _read(self, prompt: str) -> str:
        self.output_stream.write(prompt)
        self.output_stream.flush()
        line = self.input_stream.readline()
        if line == "":
            raise InputClosed
        value = line.strip()
        if value.casefold() in {"q", "quit", "abbrechen", "zurück", "zurueck"}:
            raise UserCancelled
        return value

    def _required(self, label: str, default: str = "") -> str:
        while True:
            suffix = f" [{default}]" if default else ""
            value = self._read(f"{label}{suffix}: ")
            if value:
                return value
            if default:
                return default
            self._write(
                "Bitte einen Wert eingeben oder mit q abbrechen.",
                error=True,
            )

    def _optional(self, label: str) -> str:
        return self._read(f"{label} [optional]: ")

    def _yes_no(self, question: str, *, default: bool = False) -> bool:
        marker = "J/n" if default else "j/N"
        while True:
            value = self._read(f"{question} [{marker}]: ").casefold()
            if not value:
                return default
            if value in {"j", "ja", "y", "yes"}:
                return True
            if value in {"n", "nein", "no"}:
                return False
            self._write(
                "Bitte j für Ja oder n für Nein eingeben.",
                error=True,
            )

    def _database(self) -> str:
        database = self._required(
            "Pfad zur Indexdatenbank",
            self.session.last_database,
        )
        self.session.last_database = database
        return database

    def _root(self) -> str:
        root = self._required(
            "Zu prüfender Ordner",
            self.session.last_root,
        )
        self.session.last_root = root
        return root

    def _build_search(self) -> list[str]:
        database = self._database()
        text = self._optional("Suchwort oder mehrere Wörter")
        preset = self._optional("Name einer gespeicherten Suchvorlage")
        command = ["index", "search", database]
        if text:
            command.append(text)
        if preset:
            command.extend(("--preset", preset))
        return command

    def _build_folders(self) -> list[str]:
        return ["index", "folders", self._database()]

    def _build_changes(self) -> list[str]:
        return ["index", "changes", self._database()]

    def _build_status(self) -> list[str]:
        return ["index", "status", self._database()]

    def _build_build(self) -> list[str]:
        root = self._root()
        database = self._database()
        command = ["index", "build", root, "--database", database]
        if self._yes_no("Exakte Duplikate über Prüfsummen erkennen?"):
            command.append("--hash-duplicates")
        return command

    def _build_rescan(self) -> list[str]:
        return [
            "index",
            "rescan",
            self._root(),
            "--database",
            self._database(),
        ]

    def _build_backup(self) -> list[str]:
        command = ["index", "backup", self._database()]
        output = self._optional(
            "Zielpfad der Sicherung; leer erzeugt automatisch einen Namen"
        )
        if output:
            command.extend(("--output", output))
        return command

    def _build_presets(self) -> list[str]:
        return ["index", "presets", "list"]

    def _build_explain(self) -> list[str]:
        return ["explain"]

    def _build_command(self, action: MenuAction) -> list[str]:
        builders: dict[str, Callable[[], list[str]]] = {
            "search": self._build_search,
            "folders": self._build_folders,
            "changes": self._build_changes,
            "status": self._build_status,
            "build": self._build_build,
            "rescan": self._build_rescan,
            "backup": self._build_backup,
            "presets": self._build_presets,
            "explain": self._build_explain,
        }
        try:
            return list(builders[action.builder_name]())
        except KeyError as error:
            raise RuntimeError(
                f"Menüaktion ohne Builder: {action.builder_name}"
            ) from error

    def _render(self) -> None:
        self._write("\n" + "=" * 72)
        self._write("DATENBANKTOOL – geführte Startseite")
        self._write(
            "Nummer wählen. q bricht den aktuellen Schritt ab, "
            "0 beendet das Tool."
        )
        self._write("=" * 72)
        for action in _ACTIONS:
            light = TrafficLight(
                action.level,
                action.impact_label,
                action.impact_reason,
            )
            self._write(f"{action.key}. {action.title}")
            self._write(f"   {action.description}")
            self._write(
                "   "
                + traffic_text(
                    light,
                    mode=self.color_mode,
                    stream=self.output_stream,
                )
            )
        self._write("0. Beenden")

    def run(self) -> int:
        action_by_key = {action.key: action for action in _ACTIONS}
        while True:
            self._render()
            try:
                selection = self._read("Auswahl: ")
                if selection == "0":
                    self._write("Startseite beendet.")
                    return 0
                action = action_by_key.get(selection)
                if action is None:
                    self._write(
                        "Ungültige Auswahl. Bitte eine angezeigte Nummer verwenden.",
                        error=True,
                    )
                    continue
                command = self._build_command(action)
                self._write("Geplanter Befehl:")
                self._write("  " + shlex.join(["datenbanktool", *command]))
                if action.confirmation_required and not self._yes_no(
                    "Diesen Schritt jetzt starten?"
                ):
                    self._write("Nicht ausgeführt. Zurück zur Startseite.")
                    continue
                result = int(self.command_runner(command))
                label = (
                    "erfolgreich"
                    if result == 0
                    else f"beendet mit Fehlercode {result}"
                )
                self._write(
                    "Ergebnis: "
                    + status_text(
                        label,
                        mode=self.color_mode,
                        stream=self.output_stream,
                    )
                )
            except UserCancelled:
                self._write(
                    "Aktueller Schritt abgebrochen. Zurück zur Startseite."
                )
            except InputClosed:
                self._write("Eingabe beendet. Startseite wird geschlossen.")
                return 0
            except KeyboardInterrupt:
                self._write("\nStartseite durch Tastaturabbruch beendet.")
                return 130
