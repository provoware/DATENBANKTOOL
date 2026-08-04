from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass

CommandHandler = Callable[[argparse.Namespace], int]


@dataclass(frozen=True, slots=True)
class CommandPolicy:
    """Machine-readable safety and maintenance contract for one CLI command."""

    name: str
    reads_original_files: bool = False
    writes_original_files: bool = False
    writes_index: bool = False
    writes_reports: bool = False
    writes_backups: bool = False
    writes_configuration: bool = False

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("CLI-Richtlinie benötigt einen Befehlsnamen")
        if self.writes_original_files:
            raise ValueError(
                f"Befehl {self.name!r} verletzt den Sicherheitsvertrag: "
                "Originaldatei-Schreibzugriffe sind gesperrt"
            )


GLOBAL_CLI_RULES = (
    "Öffentliche Befehlsnamen und Parameter bleiben rückwärtskompatibel.",
    "Parser und Ausführung einer Funktion liegen im selben Fachmodul.",
    "cli.py enthält nur Parser-Zusammenbau, zentrale Fehlergrenze und Dispatch.",
    "Gemeinsame Validierung und Ausgabeformatierung liegen ausschließlich in cli_common.py.",
    "Fachmodule importieren niemals cli.py und rufen sich nicht gegenseitig zyklisch auf.",
    "Jeder Handler erhält argparse.Namespace und liefert einen ganzzahligen Rückgabecode.",
    "0 bedeutet Erfolg, 1 bedeutet fachlich unvollständig, 2 bedeutet kontrollierten Fehler.",
    "Originaldateien bleiben ohne separaten Sicherheitsvertrag rein lesend.",
    "Dateischreibvorgänge sind ausdrücklich, atomar und überschreiben nicht still.",
    "Shell-Auswertung, eval, exec und os.system sind in CLI-Fachmodulen verboten.",
    "Neue Befehle erhalten Parser-, Handler-, Fehler- und Rückwärtskompatibilitätstests.",
    "Maschinenlesbare Ausgaben enthalten keine ANSI-Farbcodes oder Bedienhinweise.",
)


def bind_handler(
    parser: argparse.ArgumentParser,
    handler: CommandHandler,
    policy: CommandPolicy,
) -> None:
    """Bind one validated handler and its policy to an argparse parser."""

    policy.validate()
    if not callable(handler):
        raise TypeError("CLI-Handler muss aufrufbar sein")
    parser.set_defaults(_handler=handler, _policy=policy)


def dispatch(arguments: argparse.Namespace) -> int:
    """Execute the handler selected by argparse and validate its return code."""

    handler = getattr(arguments, "_handler", None)
    policy = getattr(arguments, "_policy", None)
    if handler is None or not callable(handler):
        raise ValueError("Für diesen Befehl ist keine Ausführung registriert")
    if not isinstance(policy, CommandPolicy):
        raise ValueError("Für diesen Befehl fehlt die globale Sicherheitsrichtlinie")
    policy.validate()
    result = handler(arguments)
    if isinstance(result, bool) or not isinstance(result, int):
        raise TypeError(f"CLI-Handler {policy.name!r} muss einen int zurückgeben")
    if not 0 <= result <= 255:
        raise ValueError(f"Ungültiger Rückgabecode {result} für {policy.name!r}")
    return result
