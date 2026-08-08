from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from typing import Sequence, TextIO

from datenbanktool import __version__, cli
from datenbanktool.core.run_journal import RunJournal
from datenbanktool.core.terminal_home_restore_audit import TerminalHome
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


def _execute_with_journal(
    journal: RunJournal,
    operation: Callable[[], int],
    *,
    error_stream: TextIO,
) -> int:
    try:
        result = int(operation())
    except SystemExit as error:
        code = error.code if isinstance(error.code, int) else 2
        journal.complete(code)
        raise
    except KeyboardInterrupt:
        journal.interrupted()
        error_stream.write(
            "\nDer Vorgang wurde abgebrochen. Der letzte bestätigte Zwischenstand bleibt erhalten.\n"
            "Die Startseite bietet den geprüften Wiederanlauf beim nächsten Start an. "
            "(Technisch: Wiederaufnahme am Checkpoint mit --resume.)\n"
        )
        error_stream.flush()
        return 130
    except Exception as error:
        report = journal.unexpected_failure(error)
        error_stream.write(
            "Das Tool wurde unerwartet beendet. Deine Originaldateien wurden nicht "
            "automatisch verändert.\n"
            "Der letzte bestätigte Zwischenstand bleibt erhalten. Prüfe zuerst mit "
            "'datenbanktool check' und öffne danach erneut die Startseite.\n"
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


def _run_safely(
    arguments: Sequence[str],
    operation: Callable[[], int],
    *,
    error_stream: TextIO,
) -> int:
    journal = RunJournal.begin(arguments, version=__version__)
    journal.record_active_command(arguments)

    def recorded_operation() -> int:
        result = int(operation())
        journal.record_command_result(arguments, result)
        return result

    return _execute_with_journal(journal, recorded_operation, error_stream=error_stream)


def _guided_home(
    arguments: Sequence[str],
    *,
    input_stream: TextIO,
    output_stream: TextIO,
    error_stream: TextIO,
    color_mode: str = "auto",
) -> int:
    journal = RunJournal.begin(arguments, version=__version__)

    def guided_runner(command: Sequence[str]) -> int:
        journal.record_active_command(command)
        result = int(cli.main(command))
        journal.record_command_result(command, result)
        return result

    home = TerminalHome(
        guided_runner,
        input_stream=input_stream,
        output_stream=output_stream,
        error_stream=error_stream,
        color_mode=color_mode,
    )
    return _execute_with_journal(journal, home.run, error_stream=error_stream)


def _run_gui(arguments: Sequence[str]) -> int:
    # Lazy import: headless CLI operation never imports a GUI toolkit.
    from datenbanktool.gui_app import run_gui

    return int(run_gui(arguments))


def main(
    argv: Sequence[str] | None = None,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    error_stream: TextIO | None = None,
) -> int:
    """Route help/start/gui requests and provide one crash-safe process boundary."""
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

    if arguments and arguments[0] == "gui":
        return _run_safely(
            arguments,
            lambda: _run_gui(arguments[1:]),
            error_stream=stderr,
        )

    if arguments and arguments[0] == "start":
        start_arguments = _start_parser().parse_args(arguments[1:])
        return _guided_home(
            arguments,
            input_stream=stdin,
            output_stream=stdout,
            error_stream=stderr,
            color_mode=start_arguments.color,
        )

    if not arguments:
        if _is_interactive(stdin) and _is_interactive(stdout):
            return _guided_home(
                ["start"],
                input_stream=stdin,
                output_stream=stdout,
                error_stream=stderr,
            )
        stdout.write(
            "Es fehlt noch die Auswahl, was das Tool tun soll.\n"
            "Grafische Oberfläche: datenbanktool gui\n"
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
