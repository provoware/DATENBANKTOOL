from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from datenbanktool.core.durable_files import atomic_write_text
from datenbanktool.core.folder_timeline import normalise_folder

_PRESET_SCHEMA_VERSION = 1
_NAME_PATTERN = re.compile(r"^[\w .-]{1,64}$", re.UNICODE)
_MAX_DESCRIPTION_LENGTH = 240


@dataclass(frozen=True, slots=True)
class TimelinePreset:
    name: str
    folder: str
    description: str
    created_utc: str
    updated_utc: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def default_timeline_preset_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "datenbanktool" / "timeline-presets.json"


def _normalise_name(name: str) -> str:
    value = " ".join(name.strip().split())
    if not _NAME_PATTERN.fullmatch(value):
        raise ValueError(
            "Bitte gib einen kurzen Vorlagennamen mit 1 bis 64 Zeichen ein. "
            "Erlaubt sind Buchstaben, Zahlen, Leerzeichen, Punkt, Unterstrich und "
            "Bindestrich. (Technisch: ungültiger Vorlagenname.)"
        )
    return value


def _normalise_description(description: str) -> str:
    value = " ".join(description.strip().split())
    if len(value) > _MAX_DESCRIPTION_LENGTH:
        raise ValueError(
            f"Die Beschreibung ist zu lang. Erlaubt sind höchstens "
            f"{_MAX_DESCRIPTION_LENGTH} Zeichen."
        )
    return value


def _path(path: Path | None) -> Path:
    return (path or default_timeline_preset_path()).expanduser().resolve(strict=False)


def _load_document(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"schema_version": _PRESET_SCHEMA_VERSION, "presets": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != _PRESET_SCHEMA_VERSION:
        raise ValueError(
            "Die gespeicherten Zeitreihen-Vorlagen stammen aus einer unbekannten "
            "Version. (Technisch: nicht unterstützte Vorlagen-Schemaversion.)"
        )
    presets = payload.get("presets")
    if not isinstance(presets, list):
        raise ValueError(
            "Die Vorlagendatei ist unvollständig oder beschädigt. Die bisherige Datei "
            "wurde nicht überschrieben. (Technisch: 'presets' ist keine Liste.)"
        )
    return payload


def _preset_from_dict(payload: object) -> TimelinePreset:
    if not isinstance(payload, dict):
        raise ValueError("Ein gespeicherter Vorlageneintrag ist ungültig.")
    allowed = {"name", "folder", "description", "created_utc", "updated_utc"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(
            "Eine Vorlage enthält unbekannte Angaben. Die Datei bleibt unverändert. "
            f"(Technisch: unbekannte Felder: {', '.join(unknown)}.)"
        )
    return TimelinePreset(
        name=_normalise_name(str(payload.get("name", ""))),
        folder=normalise_folder(str(payload.get("folder", ""))),
        description=_normalise_description(str(payload.get("description", ""))),
        created_utc=str(payload.get("created_utc", "")),
        updated_utc=str(payload.get("updated_utc", "")),
    )


def list_timeline_presets(path: Path | None = None) -> tuple[TimelinePreset, ...]:
    document = _load_document(_path(path))
    values = tuple(_preset_from_dict(item) for item in document["presets"])
    return tuple(sorted(values, key=lambda item: (item.name.casefold(), item.name)))


def get_timeline_preset(name: str, path: Path | None = None) -> TimelinePreset:
    wanted = _normalise_name(name).casefold()
    for preset in list_timeline_presets(path):
        if preset.name.casefold() == wanted:
            return preset
    raise KeyError(f"Diese Zeitreihen-Vorlage wurde nicht gefunden: {name}")


def _write_document(path: Path, presets: list[TimelinePreset]) -> None:
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


def save_timeline_preset(
    name: str,
    folder: str,
    *,
    description: str = "",
    path: Path | None = None,
    replace: bool = False,
) -> TimelinePreset:
    target = _path(path)
    normalised_name = _normalise_name(name)
    normalised_folder = normalise_folder(folder)
    normalised_description = _normalise_description(description)
    current = list(list_timeline_presets(target))
    existing = next(
        (item for item in current if item.name.casefold() == normalised_name.casefold()),
        None,
    )
    if existing is not None and not replace:
        raise FileExistsError(
            f"Die Vorlage '{existing.name}' gibt es schon. Sie wurde nicht verändert. "
            "Nutze --replace nur zum bewussten Ersetzen."
        )
    now = datetime.now(timezone.utc).isoformat()
    preset = TimelinePreset(
        name=normalised_name,
        folder=normalised_folder,
        description=normalised_description,
        created_utc=existing.created_utc if existing else now,
        updated_utc=now,
    )
    current = [
        item for item in current if item.name.casefold() != normalised_name.casefold()
    ]
    current.append(preset)
    _write_document(target, current)
    return preset


def delete_timeline_preset(
    name: str,
    *,
    path: Path | None = None,
) -> TimelinePreset:
    target = _path(path)
    wanted = _normalise_name(name).casefold()
    current = list(list_timeline_presets(target))
    deleted = next((item for item in current if item.name.casefold() == wanted), None)
    if deleted is None:
        raise KeyError(f"Diese Zeitreihen-Vorlage wurde nicht gefunden: {name}")
    _write_document(target, [item for item in current if item.name.casefold() != wanted])
    return deleted
