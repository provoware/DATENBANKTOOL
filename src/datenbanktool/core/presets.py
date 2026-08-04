from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

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
            "Vorlagenname muss 1–64 Zeichen lang sein und darf Buchstaben, Zahlen, "
            "Leerzeichen, Punkt, Unterstrich und Bindestrich enthalten"
        )
    return value


def _path(path: Path | None) -> Path:
    return (path or default_preset_path()).expanduser().resolve(strict=False)


def _load_document(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"schema_version": _PRESET_SCHEMA_VERSION, "presets": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != _PRESET_SCHEMA_VERSION:
        raise ValueError("Suchvorlagen-Datei besitzt eine unbekannte Version")
    presets = payload.get("presets")
    if not isinstance(presets, list):
        raise ValueError("Suchvorlagen-Datei ist beschädigt: 'presets' muss eine Liste sein")
    return payload


def _preset_from_dict(payload: object) -> SearchPreset:
    if not isinstance(payload, dict):
        raise ValueError("Ungültiger Suchvorlagen-Eintrag")
    filters_raw = payload.get("filters")
    if not isinstance(filters_raw, dict):
        raise ValueError("Suchvorlage enthält keine gültigen Filter")
    allowed = set(SearchFilter.__dataclass_fields__)
    unknown = sorted(set(filters_raw) - allowed)
    if unknown:
        raise ValueError(f"Suchvorlage enthält unbekannte Filter: {', '.join(unknown)}")
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
    raise KeyError(f"Suchvorlage nicht gefunden: {name}")


def _write_document(path: Path, presets: list[SearchPreset]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": _PRESET_SCHEMA_VERSION,
        "presets": [
            item.to_dict()
            for item in sorted(presets, key=lambda value: value.name.casefold())
        ],
    }
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.chmod(temporary, 0o600)
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


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
            f"Suchvorlage existiert bereits: {existing.name}. Nutze --replace zum Ersetzen."
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
        raise KeyError(f"Suchvorlage nicht gefunden: {name}")
    _write_document(target, [item for item in current if item.name.casefold() != wanted])
    return deleted
