from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from typing import Sequence, TextIO

from datenbanktool import __version__, cli
from datenbanktool.core.run_journal import RunJournal
from datenbanktool.core.terminal_home import TerminalHome
from datenbanktool.help_command import run_help_command


def _start_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="datenbanktool start",
        description=(
            "Öffnet die einfache Startseite. Vor jedem Schritt steht zuerst, was "
            "passiert; der Fachbegriff folgt nur als Zusatz."
        ),
    )
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="Farben automatisch, immer oder nie verwenden. Klartext bleibt sichtbar.",
    )
    return parser


def _is_interactive(stream: TextIO) -> bool:
    return bool(getattr(stream, "isatty", lambda: False)())


def _run_safely(
    arguments: Sequence[str],
    operation: Callable[[], int],
    *,
    error_stream: TextIO,
) -> int:
    journal = RunJournal.begin(arguments, version=__version__)
    try:
        result = int(operation())
    except KeyboardInterrupt:
        journal.interrupted()
        error_stream.write(
            "\nDer Vorgang wurde abgebrochen. Der letzte bestätigte Zwischenstand bleibt erhalten.\n"
            "Bei einem Scan kannst du denselben Befehl mit --resume fortsetzen. "
            "(Technisch: Wiederaufnahme am Checkpoint.)\n"
        )
        error_stream.flush()
        return 130
    except Exception as error:
        report = journal.unexpected_failure(error)
        error_stream.write(
            "Das Tool wurde unerwartet beendet. Deine Originaldateien wurden nicht "
            "automatisch verändert.\n"
            "Der letzte bestätigte Zwischenstand bleibt erhalten. Prüfe zuerst mit "
            "'datenbanktool check' und starte den Schritt danach erneut.\n"
        )
        if report is not None:
            error_stream.write(f"Absturzbericht: {report}\n")
        else:
            error_stream.write("Der Absturzbericht konnte nicht gespeichert werden.\n")
        error_stream.write(
            f"Technische Einzelheit: {type(error).__name__}: {error}\n"
        )
        error_stream.flush()
        return 70
    journal.complete(result)
    return result


def main(
    argv: Sequence[str] | None = None,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    error_stream: TextIO | None = None,
) -> int:
    """Route help/start requests and provide one crash-safe process boundary."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    stdin = input_stream or sys.stdin
    stdout = output_stream or sys.stdout
    stderr = error_stream or sys.stderr

    if arguments and arguments[0] in {"help", "hilfe"}:
        return _run_safely(
            arguments,
            lambda: run_help_command(
                arguments[1:],
                output_stream=stdout,
                error_stream=stderr,
            ),
            error_stream=stderr,
        )

    if arguments and arguments[0] == "start":
        start_arguments = _start_parser().parse_args(arguments[1:])
        home = TerminalHome(
            cli.main,
            input_stream=stdin,
            output_stream=stdout,
            error_stream=stderr,
            color_mode=start_arguments.color,
        )
        return _run_safely(arguments, home.run, error_stream=stderr)

    if not arguments:
        if _is_interactive(stdin) and _is_interactive(stdout):
            home = TerminalHome(
                cli.main,
                input_stream=stdin,
                output_stream=stdout,
                error_stream=stderr,
            )
            return _run_safely(["start"], home.run, error_stream=stderr)
        stdout.write(
            "Es fehlt noch die Auswahl, was das Tool tun soll.\n"
            "Einfach starten: datenbanktool start\n"
            "Hilfe in einfachen Schritten: datenbanktool help\n"
            "Prüfen, ob alles startklar ist: datenbanktool check\n"
            "Alle Befehle: datenbanktool --help\n"
        )
        stdout.flush()
        return 0

    return _run_safely(
        arguments,
        lambda: cli.main(arguments),
        error_stream=stderr,
    )
