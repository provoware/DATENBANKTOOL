from __future__ import annotations

import argparse
import json
from typing import Sequence, TextIO

from datenbanktool.core.folder_timeline_help import (
    find_timeline_topics,
    timeline_topic,
    timeline_topics,
)
from datenbanktool.core.layered_help import (
    find_topics as find_base_topics,
    get_topic as get_base_topic,
    list_topics as list_base_topics,
    render_topic,
)


def _all_topics():
    topics = {topic.name: topic for topic in list_base_topics()}
    topics.update({topic.name: topic for topic in timeline_topics()})
    return tuple(sorted(topics.values(), key=lambda topic: topic.name))


def _find_topics(query: str):
    topics = {topic.name: topic for topic in find_base_topics(query)}
    topics.update({topic.name: topic for topic in find_timeline_topics(query)})
    return tuple(sorted(topics.values(), key=lambda topic: topic.name))


def _get_topic(name: str):
    extension = timeline_topic(name)
    return extension if extension is not None else get_base_topic(name)


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
        help=(
            "Zum Beispiel search, build, folders, folder-timeline oder "
            "timeline-presets"
        ),
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
            topics = _find_topics(arguments.find)
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
            topics = _all_topics()
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
        topic = _get_topic(arguments.topic)
        if arguments.json:
            payload = topic.to_dict()
            payload["level"] = arguments.level
            payload["rendered_lines"] = list(render_topic(topic, arguments.level))
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
