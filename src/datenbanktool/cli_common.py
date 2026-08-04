from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from datenbanktool.core.presentation import hint_text, paint
from datenbanktool.core.progress import ProgressEvent

CATEGORIES = (
    "audio",
    "video",
    "image",
    "text",
    "archive",
    "code",
    "document",
    "other",
)
CHANGE_TYPES = ("added", "modified", "moved", "removed", "unchanged")
CHANGE_LABELS = {
    "added": "Neu",
    "modified": "Geändert",
    "moved": "Verschoben",
    "removed": "Entfernt",
    "unchanged": "Unverändert",
}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("Wert muss mindestens 1 sein")
    return parsed


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("Wert darf nicht negativ sein")
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("Wert darf nicht negativ sein")
    return parsed


def parser(*args: object, **kwargs: object) -> argparse.ArgumentParser:
    kwargs.setdefault("formatter_class", argparse.RawDescriptionHelpFormatter)
    return argparse.ArgumentParser(*args, **kwargs)


def add_scan_options(target: argparse.ArgumentParser) -> None:
    target.add_argument("path", type=Path, help="Ordner, der geprüft werden soll")
    target.add_argument(
        "--hash-duplicates",
        action="store_true",
        help="Dateiinhalte vergleichen. Sicher, aber bei großen Beständen langsamer.",
    )
    target.add_argument(
        "--large-file-mib",
        type=non_negative_int,
        default=1024,
        help="Ab dieser Größe wird eine Datei als groß markiert. Standard: 1024 MiB.",
    )
    target.add_argument("--max-files", type=positive_int, default=None)
    target.add_argument(
        "--follow-symlinks",
        action="store_true",
        help=(
            "Symbolischen Verzeichnissen folgen. Standardmäßig aus "
            "Sicherheitsgründen aus."
        ),
    )


def add_progress_options(target: argparse.ArgumentParser) -> None:
    target.add_argument(
        "--progress",
        choices=("human", "jsonl", "quiet"),
        default="human",
        help="Fortschritt verständlich, als JSONL oder gar nicht ausgeben.",
    )
    target.add_argument(
        "--lock-timeout",
        type=non_negative_float,
        default=0.0,
        help=(
            "Wie lange auf einen anderen Indexprozess gewartet wird. "
            "Standard: sofort abbrechen."
        ),
    )


def add_category_filter(
    target: argparse.ArgumentParser,
    *,
    default: list[str] | None = None,
) -> None:
    target.add_argument(
        "--category",
        action="append",
        default=default,
        choices=CATEGORIES,
        help="Nur diesen Dateityp zeigen. Mehrfach nutzbar.",
    )


def add_preset_filter_options(target: argparse.ArgumentParser) -> None:
    target.add_argument("--text", default="", help="Suchwort oder mehrere Wörter")
    add_category_filter(target, default=[])
    target.add_argument("--min-size-mib", type=non_negative_int)
    target.add_argument("--max-size-mib", type=non_negative_int)
    target.add_argument("--name-warning-only", action="store_true")
    target.add_argument("--duplicates-only", action="store_true")
    target.add_argument("--page-size", type=positive_int, default=25)
    target.add_argument(
        "--sort",
        choices=("path", "size", "date", "type", "relevance"),
        default="path",
    )
    target.add_argument("--descending", action="store_true")
    target.add_argument(
        "--fulltext",
        choices=("auto", "off", "required"),
        default="auto",
    )


def colour_mode(arguments: argparse.Namespace) -> str:
    return str(arguments.color)


def print_hint(
    arguments: argparse.Namespace,
    text: str,
    *,
    stream: TextIO | None = None,
) -> None:
    target = stream if stream is not None else sys.stdout
    if arguments.hints:
        print(
            hint_text(text, mode=colour_mode(arguments), stream=target),
            file=target,
        )


def progress_callback(mode: str, colour: str):
    if mode == "quiet":
        return None

    def emit(event: ProgressEvent) -> None:
        if mode == "jsonl":
            print(
                json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True),
                file=sys.stderr,
            )
            return
        amount = ""
        if event.current is not None:
            total = f"/{event.total}" if event.total is not None else ""
            amount = f" [{event.current}{total}]"
        prefix = paint(
            f"[{event.phase}:{event.kind}]",
            "cyan",
            mode=colour,
            stream=sys.stderr,
        )
        print(f"{prefix} {event.message}{amount}", file=sys.stderr)

    return emit


def write_json_atomic(
    path: Path,
    payload: dict[str, object],
    overwrite: bool,
) -> None:
    target = path.expanduser().resolve(strict=False)
    if target.exists() and not overwrite:
        raise FileExistsError(
            f"Bericht existiert bereits: {target}. Nutze --overwrite-report."
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def human_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{int(value)} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size_bytes} B"
