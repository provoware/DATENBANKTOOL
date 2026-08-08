from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePath


_INVALID = re.compile(r"[\x00-\x1f<>:\"/\\|?*]+")
_SPACES = re.compile(r"\s+")


@dataclass(frozen=True)
class RenameRule:
    prefix: str = ""
    suffix: str = ""
    lowercase: bool = False
    replace_spaces: str | None = "_"
    sequence_width: int | None = None
    preserve_extension: bool = True
    max_name_length: int = 180


@dataclass(frozen=True)
class RenameInput:
    file_id: int
    current_name: str
    sequence: int


@dataclass(frozen=True)
class RenamePreview:
    file_id: int
    current_name: str
    proposed_name: str | None
    valid: bool
    collision: bool
    reasons: tuple[str, ...]


def _clean_component(value: str, replacement: str | None) -> str:
    cleaned = _INVALID.sub("-", value).strip()
    cleaned = _SPACES.sub(replacement if replacement is not None else " ", cleaned)
    return cleaned.strip(" .")


def propose_name(item: RenameInput, rule: RenameRule) -> tuple[str | None, tuple[str, ...]]:
    reasons: list[str] = []
    if rule.max_name_length < 16 or rule.max_name_length > 255:
        raise ValueError("max_name_length muss zwischen 16 und 255 liegen")
    if rule.sequence_width is not None and (rule.sequence_width < 1 or rule.sequence_width > 12):
        raise ValueError("sequence_width muss zwischen 1 und 12 liegen")

    source = PurePath(item.current_name)
    extension = source.suffix if rule.preserve_extension else ""
    stem = source.stem if source.suffix else source.name
    stem = _clean_component(stem, rule.replace_spaces)
    if not stem:
        return None, ("Name wäre nach Bereinigung leer",)

    parts: list[str] = []
    if rule.prefix.strip():
        parts.append(_clean_component(rule.prefix, rule.replace_spaces))
    parts.append(stem)
    if rule.sequence_width is not None:
        parts.append(f"{item.sequence:0{rule.sequence_width}d}")
    if rule.suffix.strip():
        parts.append(_clean_component(rule.suffix, rule.replace_spaces))
    separator = rule.replace_spaces if rule.replace_spaces is not None else " "
    proposed_stem = separator.join(part for part in parts if part)
    if rule.lowercase:
        proposed_stem = proposed_stem.casefold()
        extension = extension.casefold()
    proposed = f"{proposed_stem}{extension}"

    if len(proposed) > rule.max_name_length:
        reasons.append(f"Name überschreitet {rule.max_name_length} Zeichen")
        return None, tuple(reasons)
    if proposed in {".", ".."}:
        reasons.append("reservierter Dateiname")
        return None, tuple(reasons)
    if proposed == item.current_name:
        reasons.append("keine Änderung erforderlich")
    else:
        reasons.append("deterministische Vorschau erzeugt")
    return proposed, tuple(reasons)


def build_rename_preview(
    items: tuple[RenameInput, ...],
    rule: RenameRule,
) -> tuple[RenamePreview, ...]:
    proposals: list[tuple[RenameInput, str | None, tuple[str, ...]]] = []
    names: dict[str, int] = {}
    for item in items:
        proposed, reasons = propose_name(item, rule)
        proposals.append((item, proposed, reasons))
        if proposed is not None:
            key = proposed.casefold()
            names[key] = names.get(key, 0) + 1

    result: list[RenamePreview] = []
    for item, proposed, reasons in proposals:
        collision = proposed is not None and names[proposed.casefold()] > 1
        extra = reasons + (("Namenskollision in Vorschau",) if collision else ())
        result.append(RenamePreview(
            file_id=item.file_id,
            current_name=item.current_name,
            proposed_name=proposed,
            valid=proposed is not None and not collision,
            collision=collision,
            reasons=extra,
        ))
    return tuple(result)
