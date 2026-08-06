from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from datenbanktool.core.durable_files import atomic_write_text
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
        raise argparse.ArgumentTypeError("Bitte eine ganze Zahl ab 1 eingeben.")
    return parsed


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("Bitte 0 oder eine größere ganze Zahl eingeben.")
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("Bitte 0 oder eine größere Zahl eingeben.")
    return parsed


def parser(*args: object, **kwargs: object) -> argparse.ArgumentParser:
    kwargs.setdefault("formatter_class", argparse.RawDescriptionHelpFormatter)
    return argparse.ArgumentParser(*args, **kwargs)


def add_scan_options(target: argparse.ArgumentParser) -> None:
    target.add_argument("path", type=Path, help="Ordner, der geprüft werden soll")
    target.add_argument(
        "--hash-duplicates",
        action="store_true",
        help=(
            "Auch den Dateiinhalt vergleichen, damit wirklich gleiche Dateien erkannt "
            "werden. (Technisch: SHA-256; sicher, aber langsamer.)"
        ),
    )
    target.add_argument(
        "--large-file-mib",
        type=non_negative_int,
        default=1024,
        help=(
            "Ab dieser Größe eine Datei als groß markieren. Standard: 1024 MiB. "
            "(Technisch: Schwelle in Mebibyte.)"
        ),
    )
    target.add_argument("--max-files", type=positive_int, default=None)
    target.add_argument(
        "--follow-symlinks",
        action="store_true",
        help=(
            "Auch Ordner hinter Verknüpfungen prüfen. Normalerweise aus, damit keine "
            "unerwarteten Bereiche einbezogen werden. (Technisch: Symlinks.)"
        ),
    )


def add_progress_options(target: argparse.ArgumentParser) -> None:
    target.add_argument(
        "--progress",
        choices=("human", "jsonl", "quiet"),
        default="human",
        help=(
            "Fortschritt normal anzeigen, als maschinenlesbare Zeilen oder gar nicht. "
            "(Technisch: human, JSONL oder quiet.)"
        ),
    )
    target.add_argument(
        "--lock-timeout",
        type=non_negative_float,
        default=0.0,
        help=(
            "So viele Sekunden auf eine andere laufende Indexprüfung warten. "
            "Standard 0 bedeutet: sofort verständlich abbrechen."
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
        help="Nur diesen Dateityp zeigen. Für mehrere Typen mehrfach angeben.",
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
            f"Der Bericht existiert schon: {target}. Wähle einen neuen Namen oder "
            "nutze bewusst --overwrite-report."
        )
    atomic_write_text(
        target,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        overwrite=overwrite,
    )


def human_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{int(value)} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size_bytes} B"