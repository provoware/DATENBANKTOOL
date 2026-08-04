from __future__ import annotations

import argparse
import json
from typing import Sequence, TextIO

from datenbanktool.core.layered_help import (
    find_topics,
    get_topic,
    list_topics,
    render_topic,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="datenbanktool help",
        description=(
            "Mehrschichtige Laienhilfe: kurz, ausführlich oder als "
            "Schritt-für-Schritt-Anleitung."
        ),
    )
    parser.add_argument(
        "topic",
        nargs="?",
        help="Zum Beispiel search, build oder folders",
    )
    parser.add_argument(
        "--level",
        choices=("quick", "detail", "guided"),
        default="detail",
        help="quick = kurz, detail = Auswirkungen, guided = vollständige Anleitung",
    )
    parser.add_argument(
        "--find",
        metavar="TEXT",
        help="Hilfethemen mit einem Alltagswort suchen, zum Beispiel Platzfresser",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Hilfe als JSON ausgeben",
    )
    return parser


def run_help_command(
    argv: Sequence[str],
    *,
    output_stream: TextIO,
    error_stream: TextIO,
) -> int:
    arguments = _parser().parse_args(list(argv))
    try:
        if arguments.find is not None:
            topics = find_topics(arguments.find)
            if arguments.json:
                output_stream.write(
                    json.dumps(
                        [topic.to_dict() for topic in topics],
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n"
                )
            elif not topics:
                output_stream.write("Keine passende Hilfe gefunden.\n")
                output_stream.write("Alle Themen: datenbanktool help\n")
            else:
                output_stream.write("Passende Hilfethemen:\n")
                for topic in topics:
                    output_stream.write(f"- {topic.name}: {topic.quick}\n")
            output_stream.flush()
            return 0
        if arguments.topic is None:
            topics = list_topics()
            if arguments.json:
                output_stream.write(
                    json.dumps(
                        [topic.to_dict() for topic in topics],
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n"
                )
            else:
                output_stream.write("Verfügbare Hilfethemen:\n")
                for topic in topics:
                    output_stream.write(f"- {topic.name}: {topic.quick}\n")
                output_stream.write(
                    "\nDetails: datenbanktool help THEMA --level detail\n"
                )
                output_stream.write(
                    "Anleitung: datenbanktool help THEMA --level guided\n"
                )
            output_stream.flush()
            return 0
        topic = get_topic(arguments.topic)
        if arguments.json:
            payload = topic.to_dict()
            payload["level"] = arguments.level
            payload["rendered_lines"] = list(
                render_topic(topic, arguments.level)
            )
            output_stream.write(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
            )
        else:
            for line in render_topic(topic, arguments.level):
                output_stream.write(line + "\n")
        output_stream.flush()
        return 0
    except ValueError as error:
        error_stream.write(f"Fehler: {error}\n")
        error_stream.write("Alle Themen: datenbanktool help\n")
        error_stream.flush()
        return 2
