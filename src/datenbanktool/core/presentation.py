from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import TextIO

_COLOR_CODES = {
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "bold": "1",
    "dim": "2",
}
_VALID_COLOR_MODES = frozenset({"auto", "always", "never"})


@dataclass(frozen=True, slots=True)
class TrafficLight:
    level: str
    label: str
    reason: str


_TRAFFIC = {
    "green": ("GRÜN", "green"),
    "yellow": ("GELB", "yellow"),
    "red": ("ROT", "red"),
}


def colour_enabled(mode: str = "auto", stream: TextIO = sys.stdout) -> bool:
    if mode not in _VALID_COLOR_MODES:
        raise ValueError(f"Unbekannter Farbmodus: {mode}")
    if mode == "always":
        return True
    if mode == "never" or os.environ.get("NO_COLOR") is not None:
        return False
    return bool(getattr(stream, "isatty", lambda: False)())


def paint(text: str, colour: str, *, mode: str = "auto", stream: TextIO = sys.stdout) -> str:
    if colour not in _COLOR_CODES:
        raise ValueError(f"Unbekannte Farbe: {colour}")
    if not colour_enabled(mode, stream):
        return text
    return f"\033[{_COLOR_CODES[colour]}m{text}\033[0m"


def traffic_text(light: TrafficLight, *, mode: str = "auto", stream: TextIO = sys.stdout) -> str:
    if light.level not in _TRAFFIC:
        raise ValueError(f"Unbekannte Ampelstufe: {light.level}")
    word, colour = _TRAFFIC[light.level]
    marker = paint("●", colour, mode=mode, stream=stream)
    label = paint(f"{word} – {light.label}", colour, mode=mode, stream=stream)
    return f"{marker} {label}: {light.reason}"


def status_text(status: str, *, mode: str = "auto", stream: TextIO = sys.stdout) -> str:
    normalised = status.casefold()
    if normalised in {"complete", "success", "successful", "ok", "erfolgreich"}:
        colour = "green"
    elif normalised in {"running", "interrupted", "warning", "prüfen", "teilweise"}:
        colour = "yellow"
    elif normalised in {"failed", "error", "fehlgeschlagen", "kritisch"}:
        colour = "red"
    else:
        colour = "cyan"
    return paint(status, colour, mode=mode, stream=stream)


def change_text(change_type: str, label: str, *, mode: str = "auto", stream: TextIO = sys.stdout) -> str:
    colour = {
        "added": "green",
        "modified": "yellow",
        "moved": "cyan",
        "removed": "red",
        "unchanged": "dim",
    }.get(change_type, "cyan")
    return paint(label, colour, mode=mode, stream=stream)


def hint_text(text: str, *, mode: str = "auto", stream: TextIO = sys.stdout) -> str:
    prefix = paint("ⓘ Hinweis", "cyan", mode=mode, stream=stream)
    return f"{prefix}: {text}"
