from __future__ import annotations

import argparse
import json

from datenbanktool.cli_common import colour_mode, print_hint
from datenbanktool.cli_contract import CommandPolicy, bind_handler
from datenbanktool.core.help_system import get_topic, list_topics
from datenbanktool.core.presentation import paint


def register_explain_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    explain = subparsers.add_parser(
        "explain",
        help="Funktion, Auswirkung und Sicherheitsniveau verständlich erklären",
        description=(
            "Zeigt ausführlich, was eine Funktion macht, was sie schreibt "
            "und wann sie sinnvoll ist."
        ),
    )
    explain.add_argument(
        "topic",
        nargs="?",
        help="Zum Beispiel folders, search, presets oder restore",
    )
    explain.add_argument("--json", action="store_true")
    bind_handler(explain, run_explain, CommandPolicy("explain"))


def run_explain(arguments: argparse.Namespace) -> int:
    if arguments.topic is None:
        topics = list_topics()
        if arguments.json:
            print(
                json.dumps(
                    [topic.to_dict() for topic in topics],
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        print("Verfügbare Hilfethemen:")
        for topic in topics:
            print(f"- {topic.name}: {topic.purpose}")
        print_hint(arguments, "Details anzeigen: datenbanktool explain THEMA")
        return 0
    topic = get_topic(arguments.topic)
    if arguments.json:
        print(json.dumps(topic.to_dict(), ensure_ascii=False, indent=2))
        return 0
    print(paint(topic.title, "bold", mode=colour_mode(arguments)))
    print(f"Zweck: {topic.purpose}")
    print(f"Wirkung: {topic.effect}")
    print(f"Schreibt: {topic.writes}")
    print(f"Risiko: {topic.risk}")
    print(f"Sinnvoll wenn: {topic.use_when}")
    print(f"Beispiel: {topic.example}")
    return 0
