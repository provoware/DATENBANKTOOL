from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal


PresetAction = Literal["analyse", "filter", "group", "mark", "rename_preview"]


@dataclass(frozen=True)
class PresetRule:
    field: str
    operator: str
    value: str


@dataclass(frozen=True)
class WorkflowPreset:
    preset_id: str
    title: str
    description: str
    action: PresetAction
    rules: tuple[PresetRule, ...]
    editable: bool = True
    destructive: bool = False

    def edited(self, **changes: object) -> "WorkflowPreset":
        allowed = {"title", "description", "rules"}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"Nicht editierbare Preset-Felder: {sorted(unknown)}")
        return replace(self, **changes)


DEFAULT_PRESETS = (
    WorkflowPreset(
        "photos-by-date", "Fotos ordnen", "Nach Datum, Kamera und Ordnerkontext gruppieren.",
        "group", (PresetRule("category", "eq", "image"), PresetRule("modified_utc", "year", "auto")),
    ),
    WorkflowPreset(
        "videos-by-source", "Videos gruppieren", "Videos nach Quelle, Datum und Größe sichtbar clustern.",
        "group", (PresetRule("category", "eq", "video"), PresetRule("size_bytes", "gt", "0")),
    ),
    WorkflowPreset(
        "music-review", "Musik sortieren", "Musikbestand nach Endung, Pfadwörtern und Größe vorsortieren.",
        "filter", (PresetRule("category", "eq", "audio"),),
    ),
    WorkflowPreset(
        "projects-detect", "Projektordner erkennen", "Projektnahe Pfade und typische Projektdateien sammeln.",
        "filter", (PresetRule("relative_path", "contains_any", "project,projekt,src,layout,tool"),),
    ),
    WorkflowPreset(
        "system-noise", "Systemreste isolieren", "Cache-, Temp-, Log- und Systemartefakte nur markieren.",
        "mark", (PresetRule("relative_path", "contains_any", "cache,temp,thumb,log,system"),),
    ),
    WorkflowPreset(
        "duplicates", "Duplikate prüfen", "Exakte Hash-Gruppen sichtbar machen; niemals automatisch löschen.",
        "filter", (PresetRule("duplicate_group_id", "not_null", "true"),),
    ),
    WorkflowPreset(
        "name-repair", "Namensreparatur", "Unscharfe Namen erkennen und sichere Umbenennungs-Vorschau erzeugen.",
        "rename_preview", (PresetRule("warning_count", "gt", "0"),),
    ),
    WorkflowPreset(
        "analyse-only", "Nur analysieren", "Komplette Bestandsaufnahme ohne Änderungsvorschlag.",
        "analyse", (), editable=False,
    ),
)


def preset_by_id(preset_id: str) -> WorkflowPreset:
    for preset in DEFAULT_PRESETS:
        if preset.preset_id == preset_id:
            return preset
    raise KeyError(preset_id)


def validate_presets(presets: tuple[WorkflowPreset, ...] = DEFAULT_PRESETS) -> tuple[str, ...]:
    problems: list[str] = []
    identifiers: set[str] = set()
    for preset in presets:
        if not preset.preset_id or preset.preset_id in identifiers:
            problems.append(f"Preset-ID ungültig oder doppelt: {preset.preset_id!r}")
        identifiers.add(preset.preset_id)
        if preset.destructive:
            problems.append(f"Destruktives Preset unzulässig: {preset.preset_id}")
        if not preset.title.strip() or not preset.description.strip():
            problems.append(f"Preset ohne verständlichen Titel/Beschreibung: {preset.preset_id}")
    return tuple(problems)
