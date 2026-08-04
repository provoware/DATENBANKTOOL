from __future__ import annotations

import argparse
import sys
from typing import Sequence, TextIO

from datenbanktool import cli
from datenbanktool.core.terminal_home import TerminalHome
from datenbanktool.help_command import run_help_command


def _start_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="datenbanktool start",
        description=(
            "Öffnet eine geführte Terminal-Startseite. Die Auswahl erklärt vor dem Start, "
            "ob nur gelesen oder eine Index-/Sicherungsdatei geschrieben wird."
        ),
    )
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="Farben automatisch, immer oder nie verwenden. Klartext bleibt immer sichtbar.",
    )
    return parser


def _is_interactive(stream: TextIO) -> bool:
    return bool(getattr(stream, "isatty", lambda: False)())


def main(
    argv: Sequence[str] | None = None,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    error_stream: TextIO | None = None,
) -> int:
    """Route guided help/start requests and delegate existing CLI commands."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    stdin = input_stream or sys.stdin
    stdout = output_stream or sys.stdout
    stderr = error_stream or sys.stderr

    if arguments and arguments[0] in {"help", "hilfe"}:
        return run_help_command(
            arguments[1:],
            output_stream=stdout,
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
        return home.run()

    if not arguments:
        if _is_interactive(stdin) and _is_interactive(stdout):
            home = TerminalHome(
                cli.main,
                input_stream=stdin,
                output_stream=stdout,
                error_stream=stderr,
            )
            return home.run()
        stdout.write(
            "DATENBANKTOOL benötigt in nicht-interaktiven Umgebungen einen Befehl.\n"
            "Geführte Bedienung: datenbanktool start\n"
            "Laienhilfe: datenbanktool help\n"
            "Befehlsübersicht: datenbanktool --help\n"
        )
        stdout.flush()
        return 0

    return cli.main(arguments)
