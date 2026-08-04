from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence, TextIO

from datenbanktool.core.guided_home_catalog import FIELD_HELP, ACTIONS, MenuAction
from datenbanktool.core.guided_home_input import (
    InputParseError,
    parse_optional_integer,
    parse_optional_percent,
    parse_report_format,
)
from datenbanktool.core.folder_timeline_help import (
    timeline_error_help,
    timeline_preset_error_help,
    timeline_topic,
)
from datenbanktool.core.layered_help import (
    error_help as base_error_help,
    get_topic as get_base_topic,
    render_topic,
)
from datenbanktool.core.presentation import TrafficLight, status_text, traffic_text
from datenbanktool.core.timeline_presets import (
    TimelinePreset,
    get_timeline_preset,
    list_timeline_presets,
)

CommandRunner = Callable[[Sequence[str]], int]


class InputClosed(Exception):
    """Raised when an interactive input stream is closed."""


class UserCancelled(Exception):
    """Raised when the user cancels the current guided action."""


@dataclass(slots=True)
class HomeSession:
    last_database: str = ""
    last_root: str = ""
    last_timeline_folder: str = "."


def _get_topic(name: str):
    extension = timeline_topic(name)
    return extension if extension is not None else get_base_topic(name)


def _error_help(topic_name: str, exit_code: int) -> tuple[str, ...]:
    if topic_name == "folder-timeline":
        return timeline_error_help(exit_code)
    if topic_name == "timeline-presets":
        return timeline_preset_error_help(exit_code)
    return base_error_help(topic_name, exit_code)


def menu_actions() -> tuple[MenuAction, ...]:
    """Return the immutable, ordered home-screen action catalogue."""
    return ACTIONS


class TerminalHome:
    """Guided terminal home with layered help and no shell execution."""

    def __init__(
        self,
        command_runner: CommandRunner,
        *,
        input_stream: TextIO,
        output_stream: TextIO,
        error_stream: TextIO,
        color_mode: str = "auto",
        timeline_preset_path: Path | None = None,
    ) -> None:
        self.command_runner = command_runner
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.error_stream = error_stream
        self.color_mode = color_mode
        self.timeline_preset_path = timeline_preset_path
        self.session = HomeSession()
        keys = [action.key for action in ACTIONS]
        if len(keys) != len(set(keys)):
            raise RuntimeError("Menü enthält doppelte Auswahlnummern")
        for action in ACTIONS:
            _get_topic(action.help_topic)

    def _write(self, text: str = "", *, error: bool = False) -> None:
        stream = self.error_stream if error else self.output_stream
        stream.write(text + "\n")
        stream.flush()

    def _write_lines(self, lines: Sequence[str], *, error: bool = False) -> None:
        for line in lines:
            self._write(line, error=error)

    def _read(self, prompt: str, *, help_text: str = "") -> str:
        while True:
            self.output_stream.write(prompt)
            self.output_stream.flush()
            line = self.input_stream.readline()
            if line == "":
                raise InputClosed
            value = line.strip()
            if value.casefold() in {
                "q",
                "quit",
                "abbrechen",
                "zurück",
                "zurueck",
            }:
                raise UserCancelled
            if help_text and value.casefold() in {"?", "hilfe", "help"}:
                self._write("Hilfe zu dieser Eingabe:")
                self._write("  " + help_text)
                continue
            return value

    def _required(self, label: str, default: str = "", *, help_text: str) -> str:
        while True:
            suffix = f" [{default}]" if default else ""
            value = self._read(
                f"{label}{suffix} [? Hilfe]: ",
                help_text=help_text,
            )
            if value:
                return value
            if default:
                return default
            self._write(
                "Bitte Wert eingeben, ? für Hilfe oder q zum Abbrechen.",
                error=True,
            )

    def _optional(self, label: str, *, help_text: str) -> str:
        return self._read(
            f"{label} [optional, ? Hilfe]: ",
            help_text=help_text,
        )

    def _optional_integer(
        self,
        label: str,
        *,
        help_text: str,
        minimum: int,
        maximum: int | None = None,
        default: int | None = None,
    ) -> int | None:
        while True:
            suffix = f" [{default}]" if default is not None else " [optional]"
            value = self._read(
                f"{label}{suffix} [? Hilfe]: ",
                help_text=help_text,
            )
            if not value:
                return default
            try:
                return parse_optional_integer(
                    value,
                    minimum=minimum,
                    maximum=maximum,
                    default=default,
                )
            except InputParseError as error:
                self._write(str(error), error=True)
                continue

    def _optional_float(
        self,
        label: str,
        *,
        help_text: str,
        minimum: float,
        maximum: float,
    ) -> float | None:
        while True:
            value = self._read(
                f"{label} [optional, ? Hilfe]: ",
                help_text=help_text,
            )
            if not value:
                return None
            try:
                return parse_optional_percent(value, minimum=minimum, maximum=maximum)
            except InputParseError as error:
                self._write(str(error), error=True)
                continue

    def _report_format(self) -> str:
        while True:
            value = self._read(
                "Optionaler Bericht [kein/json/csv/html, Standard kein, ? Hilfe]: ",
                help_text=FIELD_HELP["timeline_report"],
            )
            try:
                return parse_report_format(value)
            except InputParseError as error:
                self._write(str(error), error=True)

    def _yes_no(
        self,
        question: str,
        *,
        default: bool = False,
        help_text: str,
    ) -> bool:
        marker = "J/n" if default else "j/N"
        while True:
            value = self._read(
                f"{question} [{marker}, ? Hilfe]: ",
                help_text=help_text,
            ).casefold()
            if not value:
                return default
            if value in {"j", "ja", "y", "yes"}:
                return True
            if value in {"n", "nein", "no"}:
                return False
            self._write("Bitte j, n oder ? für Hilfe eingeben.", error=True)

    def _database(self) -> str:
        value = self._required(
            "Pfad zur Indexdatenbank",
            self.session.last_database,
            help_text=FIELD_HELP["database"],
        )
        self.session.last_database = value
        return value

    def _root(self) -> str:
        value = self._required(
            "Zu prüfender Ordner",
            self.session.last_root,
            help_text=FIELD_HELP["root"],
        )
        self.session.last_root = value
        return value

    def _build_search(self) -> list[str]:
        command = ["index", "search", self._database()]
        text = self._optional(
            "Suchwort oder mehrere Wörter",
            help_text=FIELD_HELP["search_text"],
        )
        preset = self._optional(
            "Name einer gespeicherten Suchvorlage",
            help_text=FIELD_HELP["preset"],
        )
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
        command = [
            "index",
            "build",
            self._root(),
            "--database",
            self._database(),
        ]
        if self._yes_no(
            "Exakte Duplikate über Prüfsummen erkennen?",
            help_text=FIELD_HELP["hash_duplicates"],
        ):
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
            "Zielpfad der Sicherung; leer erzeugt automatisch einen Namen",
            help_text=FIELD_HELP["backup_output"],
        )
        if output:
            command.extend(("--output", output))
        return command

    def _build_presets(self) -> list[str]:
        return ["index", "presets", "list"]

    def _build_explain(self) -> list[str]:
        return ["help"]

    def _build_folder_compare(self) -> list[str]:
        return ["index", "folder-compare", self._database()]

    def _choose_timeline_preset(self) -> TimelinePreset | None:
        try:
            presets = list_timeline_presets(self.timeline_preset_path)
        except (OSError, ValueError) as error:
            self._write(f"Zeitreihen-Vorlagen konnten nicht gelesen werden: {error}", error=True)
            self._write("Der Ordner kann weiterhin manuell eingegeben werden.")
            return None
        if not presets:
            self._write("Zeitreihen-Vorlagen: noch keine gespeichert.")
            return None
        self._write("Gespeicherte Zeitreihen-Vorlagen:")
        for number, preset in enumerate(presets, 1):
            description = f" – {preset.description}" if preset.description else ""
            self._write(f"  {number}. {preset.name}: {preset.folder}{description}")
        while True:
            value = self._optional(
                "Vorlage als Nummer oder Name; leer für manuell",
                help_text=FIELD_HELP["timeline_preset_choice"],
            )
            if not value:
                return None
            if value.isdigit():
                index = int(value) - 1
                if 0 <= index < len(presets):
                    selected = presets[index]
                else:
                    self._write("Vorlagennummer wurde nicht gefunden.", error=True)
                    continue
            else:
                try:
                    selected = get_timeline_preset(value, self.timeline_preset_path)
                except KeyError:
                    self._write("Vorlagenname wurde nicht gefunden.", error=True)
                    continue
            self._write(f"Gewählt: {selected.name} → {selected.folder}")
            return selected

    def _build_folder_timeline(self) -> list[str]:
        database = self._database()
        selected = self._choose_timeline_preset()
        default_folder = (
            selected.folder if selected is not None else self.session.last_timeline_folder
        )
        folder = self._required(
            "Relativer Ordner im Scan",
            default_folder,
            help_text=FIELD_HELP["timeline_folder"],
        )
        self.session.last_timeline_folder = folder
        command = ["index", "folder-timeline", database]
        if selected is not None and folder == selected.folder:
            command.extend(("--preset", selected.name))
            if self.timeline_preset_path is not None:
                command.extend(("--preset-file", str(self.timeline_preset_path)))
        else:
            command.append(folder)
        from_session = self._optional_integer(
            "Älteste Scan-ID",
            help_text=FIELD_HELP["timeline_from_session"],
            minimum=1,
        )
        to_session = self._optional_integer(
            "Neueste Scan-ID",
            help_text=FIELD_HELP["timeline_to_session"],
            minimum=1,
        )
        limit = self._optional_integer(
            "Höchste Zahl der Zeitpunkte",
            help_text=FIELD_HELP["timeline_limit"],
            minimum=2,
            maximum=500,
            default=100,
        )
        size_threshold = self._optional_float(
            "Warnschwelle Größenwachstum in Prozent",
            help_text=FIELD_HELP["timeline_size_threshold"],
            minimum=0,
            maximum=1_000_000,
        )
        file_threshold = self._optional_float(
            "Warnschwelle Dateizahlwachstum in Prozent",
            help_text=FIELD_HELP["timeline_file_threshold"],
            minimum=0,
            maximum=1_000_000,
        )
        if from_session is not None:
            command.extend(("--from-session-id", str(from_session)))
        if to_session is not None:
            command.extend(("--to-session-id", str(to_session)))
        if limit is not None:
            command.extend(("--limit", str(limit)))
        if size_threshold is not None:
            command.extend(("--warn-size-growth-percent", str(size_threshold)))
        if file_threshold is not None:
            command.extend(("--warn-file-growth-percent", str(file_threshold)))
        report_format = self._report_format()
        if report_format != "none":
            report_path = self._required(
                f"Zielpfad für {report_format.upper()}",
                help_text=FIELD_HELP["timeline_report_path"],
            )
            command.extend((f"--{report_format}", report_path))
        return command

    def _build_timeline_preset_save(self) -> list[str]:
        name = self._required(
            "Name der neuen Zeitreihen-Vorlage",
            help_text=FIELD_HELP["timeline_preset_name"],
        )
        folder = self._required(
            "Relativer Ordner für die Vorlage",
            self.session.last_timeline_folder,
            help_text=FIELD_HELP["timeline_folder"],
        )
        description = self._optional(
            "Kurze Beschreibung",
            help_text=FIELD_HELP["timeline_preset_description"],
        )
        command = ["index", "timeline-presets", "save", name, folder]
        if description:
            command.extend(("--description", description))
        if self.timeline_preset_path is not None:
            command.extend(("--preset-file", str(self.timeline_preset_path)))
        return command

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
            "folder_compare": self._build_folder_compare,
            "folder_timeline": self._build_folder_timeline,
            "timeline_preset_save": self._build_timeline_preset_save,
        }
        try:
            return list(builders[action.builder_name]())
        except KeyError as error:
            raise RuntimeError(
                f"Menüaktion ohne Builder: {action.builder_name}"
            ) from error

    def _render_topic(self, topic_name: str, level: str) -> None:
        self._write("\n" + "-" * 72)
        self._write_lines(render_topic(_get_topic(topic_name), level))
        self._write("-" * 72)

    def _render_help_overview(self) -> None:
        self._write("\nMehrschichtige Hilfe")
        self._write("h          zeigt diese Übersicht")
        self._write("?NUMMER    zeigt Details, zum Beispiel ?11")
        self._write("gNUMMER    zeigt Schritt für Schritt, zum Beispiel g12")
        self._write("?          erklärt das aktuelle Eingabefeld")
        self._write("q          bricht den aktuellen Schritt ab")
        self._write("0          beendet die Startseite")
        self._write("Mehr: datenbanktool help THEMA --level guided")

    def _handle_help_selection(
        self,
        selection: str,
        actions: dict[str, MenuAction],
    ) -> bool:
        value = selection.replace(" ", "").casefold()
        if value in {"h", "hilfe", "help", "?"}:
            self._render_help_overview()
            return True
        if value.startswith("?") and value[1:]:
            action = actions.get(value[1:])
            if action is None:
                self._write("Keine Hilfe für diese Nummer gefunden.", error=True)
            else:
                self._render_topic(action.help_topic, "detail")
            return True
        if value.startswith("g") and value[1:]:
            action = actions.get(value[1:])
            if action is None:
                self._write("Keine Anleitung für diese Nummer gefunden.", error=True)
            else:
                self._render_topic(action.help_topic, "guided")
            return True
        return False

    def _render(self) -> None:
        self._write("\n" + "=" * 72)
        self._write("DATENBANKTOOL – geführte Startseite")
        self._write("Nummer wählen. h = Hilfe, ?NUMMER = Details, gNUMMER = Anleitung.")
        self._write("q bricht den aktuellen Schritt ab, 0 beendet das Tool.")
        self._write("=" * 72)
        for action in ACTIONS:
            topic = _get_topic(action.help_topic)
            if action.confirmation_required:
                light = TrafficLight("yellow", "Bestätigung nötig", topic.writes)
            else:
                light = TrafficLight("green", "Sicherer Direktstart", topic.writes)
            self._write(f"{action.key}. {topic.title}")
            self._write(f"   {topic.quick}")
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

    def run(self) -> int:
        actions = {action.key: action for action in ACTIONS}
        while True:
            self._render()
            try:
                selection = self._read("Auswahl: ")
                if selection == "0":
                    self._write("Startseite beendet.")
                    return 0
                if self._handle_help_selection(selection, actions):
                    continue
                action = actions.get(selection)
                if action is None:
                    self._write(
                        "Ungültige Auswahl. Nummer oder h für Hilfe verwenden.",
                        error=True,
                    )
                    continue
                self._render_topic(action.help_topic, "quick")
                command = self._build_command(action)
                self._write("Geplanter Befehl:")
                self._write("  " + shlex.join(["datenbanktool", *command]))
                if action.confirmation_required and not self._yes_no(
                    "Diesen Schritt jetzt starten?",
                    help_text=FIELD_HELP["confirmation"],
                ):
                    self._write("Nicht ausgeführt. Zurück zur Startseite.")
                    continue
                result = int(self.command_runner(command))
                label = "erfolgreich" if result == 0 else f"Fehlercode {result}"
                self._write(
                    "Ergebnis: "
                    + status_text(
                        label,
                        mode=self.color_mode,
                        stream=self.output_stream,
                    )
                )
                if result != 0:
                    self._write("Fehlerhilfe:", error=True)
                    self._write_lines(
                        _error_help(action.help_topic, result),
                        error=True,
                    )
            except UserCancelled:
                self._write("Aktueller Schritt abgebrochen. Zurück zur Startseite.")
            except InputClosed:
                self._write("Eingabe beendet. Startseite wird geschlossen.")
                return 0
            except KeyboardInterrupt:
                self._write("\nStartseite durch Tastaturabbruch beendet.")
                return 130
