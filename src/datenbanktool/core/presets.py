from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from datenbanktool.core.durable_files import atomic_write_text
from datenbanktool.core.search import SearchFilter

_PRESET_SCHEMA_VERSION = 1
_NAME_PATTERN = re.compile(r"^[\w .-]{1,64}$", re.UNICODE)


@dataclass(frozen=True, slots=True)
class SearchPreset:
    name: str
    description: str
    created_utc: str
    updated_utc: str
    filters: SearchFilter

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
            "filters": asdict(self.filters),
        }


def default_preset_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "datenbanktool" / "search-presets.json"


def _normalise_name(name: str) -> str:
    value = " ".join(name.strip().split())
    if not _NAME_PATTERN.fullmatch(value):
        raise ValueError(
            "Bitte gib einen kurzen Vorlagennamen mit 1 bis 64 Zeichen ein. "
            "Erlaubt sind Buchstaben, Zahlen, Leerzeichen, Punkt, Unterstrich und "
            "Bindestrich. (Technisch: ungültiger Vorlagenname.)"
        )
    return value


def _path(path: Path | None) -> Path:
    return (path or default_preset_path()).expanduser().resolve(strict=False)


def _load_document(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"schema_version": _PRESET_SCHEMA_VERSION, "presets": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != _PRESET_SCHEMA_VERSION:
        raise ValueError(
            "Die gespeicherten Suchvorlagen stammen aus einer unbekannten Version. "
            "Die Datei wurde nicht verändert. (Technisch: unbekannte Schemaversion.)"
        )
    presets = payload.get("presets")
    if not isinstance(presets, list):
        raise ValueError(
            "Die Suchvorlagendatei ist unvollständig oder beschädigt. Die bisherige "
            "Datei wurde nicht überschrieben. (Technisch: 'presets' ist keine Liste.)"
        )
    return payload


def _preset_from_dict(payload: object) -> SearchPreset:
    if not isinstance(payload, dict):
        raise ValueError("Ein gespeicherter Suchvorlagen-Eintrag ist ungültig.")
    filters_raw = payload.get("filters")
    if not isinstance(filters_raw, dict):
        raise ValueError("Eine Suchvorlage enthält keine verwendbaren Suchregeln.")
    allowed = set(SearchFilter.__dataclass_fields__)
    unknown = sorted(set(filters_raw) - allowed)
    if unknown:
        raise ValueError(
            "Eine Suchvorlage enthält unbekannte Regeln. Die Datei bleibt unverändert. "
            f"(Technisch: {', '.join(unknown)}.)"
        )
    filters = SearchFilter(**filters_raw)
    filters.validate()
    return SearchPreset(
        name=_normalise_name(str(payload.get("name", ""))),
        description=str(payload.get("description", "")),
        created_utc=str(payload.get("created_utc", "")),
        updated_utc=str(payload.get("updated_utc", "")),
        filters=filters,
    )


def list_presets(path: Path | None = None) -> tuple[SearchPreset, ...]:
    document = _load_document(_path(path))
    values = tuple(_preset_from_dict(item) for item in document["presets"])
    return tuple(sorted(values, key=lambda item: (item.name.casefold(), item.name)))


def get_preset(name: str, path: Path | None = None) -> SearchPreset:
    wanted = _normalise_name(name).casefold()
    for preset in list_presets(path):
        if preset.name.casefold() == wanted:
            return preset
    raise KeyError(f"Diese Suchvorlage wurde nicht gefunden: {name}")


def _write_document(path: Path, presets: list[SearchPreset]) -> None:
    payload = {
        "schema_version": _PRESET_SCHEMA_VERSION,
        "presets": [
            item.to_dict()
            for item in sorted(presets, key=lambda value: value.name.casefold())
        ],
    }
    atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        overwrite=True,
        mode=0o600,
    )


def save_preset(
    name: str,
    filters: SearchFilter,
    *,
    description: str = "",
    path: Path | None = None,
    replace: bool = False,
) -> SearchPreset:
    filters.validate()
    target = _path(path)
    normalised = _normalise_name(name)
    current = list(list_presets(target))
    existing = next(
        (item for item in current if item.name.casefold() == normalised.casefold()),
        None,
    )
    if existing is not None and not replace:
        raise FileExistsError(
            f"Die Suchvorlage '{existing.name}' gibt es schon. Sie wurde nicht "
            "verändert. Nutze --replace nur zum bewussten Ersetzen."
        )
    now = datetime.now(timezone.utc).isoformat()
    preset = SearchPreset(
        name=normalised,
        description=description.strip(),
        created_utc=existing.created_utc if existing else now,
        updated_utc=now,
        filters=filters,
    )
    current = [item for item in current if item.name.casefold() != normalised.casefold()]
    current.append(preset)
    _write_document(target, current)
    return preset


def delete_preset(name: str, *, path: Path | None = None) -> SearchPreset:
    target = _path(path)
    wanted = _normalise_name(name).casefold()
    current = list(list_presets(target))
    deleted = next((item for item in current if item.name.casefold() == wanted), None)
    if deleted is None:
        raise KeyError(f"Diese Suchvorlage wurde nicht gefunden: {name}")
    _write_document(target, [item for item in current if item.name.casefold() != wanted])
    return deleted
