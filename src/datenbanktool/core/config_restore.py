from __future__ import annotations

import hashlib
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from datenbanktool.core.backup_catalog import (
    BackupItem,
    default_config_directory,
    list_backups,
)
from datenbanktool.core.config_backups import ConfigBackupResult, create_config_backup
from datenbanktool.core.durable_files import atomic_write_bytes
from datenbanktool.core.presets import SearchPreset, default_preset_path, list_presets
from datenbanktool.core.timeline_presets import (
    TimelinePreset,
    default_timeline_preset_path,
    list_timeline_presets,
)


@dataclass(frozen=True, slots=True)
class ConfigRestoreComparison:
    backup: str
    backup_name: str
    active: str
    active_name: str
    kind: str
    kind_label: str
    backup_sha256: str
    active_sha256: str
    backup_preset_count: int
    active_preset_count: int
    add_names: tuple[str, ...]
    remove_names: tuple[str, ...]
    change_names: tuple[str, ...]
    unchanged_names: tuple[str, ...]
    identical: bool
    can_restore: bool
    validation_detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConfigRestoreResult:
    comparison: ConfigRestoreComparison
    rollback_backup: ConfigBackupResult
    restored_sha256: str
    completed_utc: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _matches_backup_name(backup_name: str, active_name: str) -> bool:
    stem = Path(active_name).stem
    prefixes = (
        f"{active_name}.backup-",
        f"{stem}.backup-",
        f"{stem}-backup-",
    )
    exact = {f"{active_name}.bak", f"{active_name}.backup"}
    return backup_name in exact or backup_name.startswith(prefixes)


def _active_target(
    backup_name: str,
    config_directory: Path | None,
) -> tuple[str, str, Path]:
    directory = _absolute(config_directory or default_config_directory())
    options = (
        (
            "search",
            "Suchvorlagen",
            directory / default_preset_path().name,
        ),
        (
            "timeline",
            "Zeitreihen-Vorlagen",
            directory / default_timeline_preset_path().name,
        ),
    )
    for kind, label, active in options:
        if _matches_backup_name(backup_name, active.name):
            return kind, label, active
    raise ValueError(
        "Die Sicherung kann keiner unterstützten aktiven Vorlagendatei zugeordnet werden."
    )


def _catalogued_configuration_backup(
    database: Path,
    backup: Path,
    config_directory: Path | None,
) -> tuple[BackupItem, str, str, Path]:
    target = _absolute(backup)
    selected = next(
        (
            item
            for item in list_backups(database, config_directory=config_directory)
            if item.path == str(target)
        ),
        None,
    )
    if selected is None:
        raise ValueError(
            "Die Datei gehört nicht zur aktuell geprüften Sicherungsübersicht."
        )
    if selected.kind != "configuration":
        raise ValueError(
            "Nur geprüfte Such- oder Zeitreihen-Konfigurationssicherungen können "
            "über diesen Assistenten wiederhergestellt werden."
        )
    if selected.status_level != "green":
        raise ValueError(
            "Die ausgewählte Konfigurationssicherung ist nicht als geprüft und nutzbar "
            f"freigegeben: {selected.status_label}."
        )
    kind, label, active = _active_target(selected.name, config_directory)
    return selected, kind, label, active


def _normal_file_bytes(path: Path, label: str) -> bytes:
    target = _absolute(path)
    if target.is_symlink():
        raise ValueError(f"{label} ist eine symbolische Verknüpfung und wurde abgelehnt.")
    if not target.is_file():
        raise FileNotFoundError(f"{label} nicht gefunden: {target}")
    return target.read_bytes()


def _records(path: Path, kind: str) -> tuple[SearchPreset | TimelinePreset, ...]:
    if kind == "search":
        return list_presets(path)
    if kind == "timeline":
        return list_timeline_presets(path)
    raise ValueError(f"Nicht unterstützte Konfigurationsart: {kind}")


def _record_map(
    records: tuple[SearchPreset | TimelinePreset, ...],
    *,
    label: str,
) -> dict[str, SearchPreset | TimelinePreset]:
    values: dict[str, SearchPreset | TimelinePreset] = {}
    for record in records:
        key = record.name.casefold()
        if key in values:
            raise ValueError(
                f"{label} enthält den Vorlagennamen '{record.name}' mehrfach. "
                "Eine eindeutige Wiederherstellung ist nicht möglich."
            )
        values[key] = record
    return values


def _payload(record: SearchPreset | TimelinePreset) -> dict[str, Any]:
    return record.to_dict()


def compare_config_backup(
    database: Path,
    backup: Path,
    *,
    config_directory: Path | None = None,
) -> ConfigRestoreComparison:
    """Compare one catalogued configuration backup with its active file read-only."""
    selected, kind, kind_label, active = _catalogued_configuration_backup(
        database,
        backup,
        config_directory,
    )
    backup_path = Path(selected.path)
    backup_content = _normal_file_bytes(backup_path, "Konfigurationssicherung")
    active_content = _normal_file_bytes(active, "Aktive Konfigurationsdatei")
    backup_records = _record_map(
        _records(backup_path, kind),
        label="Die Sicherung",
    )
    active_records = _record_map(
        _records(active, kind),
        label="Die aktive Konfiguration",
    )

    backup_keys = set(backup_records)
    active_keys = set(active_records)
    add_keys = backup_keys - active_keys
    remove_keys = active_keys - backup_keys
    common_keys = backup_keys & active_keys
    change_keys = {
        key
        for key in common_keys
        if _payload(backup_records[key]) != _payload(active_records[key])
    }
    unchanged_keys = common_keys - change_keys

    def names(keys: set[str]) -> tuple[str, ...]:
        return tuple(
            sorted(
                (backup_records.get(key) or active_records[key]).name for key in keys
            )
        )

    backup_sha = hashlib.sha256(backup_content).hexdigest()
    active_sha = hashlib.sha256(active_content).hexdigest()
    identical = backup_sha == active_sha
    detail = (
        f"{len(add_keys)} hinzufügen, {len(remove_keys)} entfernen, "
        f"{len(change_keys)} ersetzen, {len(unchanged_keys)} unverändert."
    )
    if identical:
        detail += " Sicherung und aktive Datei sind bytegenau identisch."

    return ConfigRestoreComparison(
        backup=str(backup_path),
        backup_name=selected.name,
        active=str(active),
        active_name=active.name,
        kind=kind,
        kind_label=kind_label,
        backup_sha256=backup_sha,
        active_sha256=active_sha,
        backup_preset_count=len(backup_records),
        active_preset_count=len(active_records),
        add_names=names(add_keys),
        remove_names=names(remove_keys),
        change_names=names(change_keys),
        unchanged_names=names(unchanged_keys),
        identical=identical,
        can_restore=not identical,
        validation_detail=detail,
    )


def _verify_restored_file(
    path: Path,
    *,
    kind: str,
    expected_sha256: str,
) -> None:
    content = _normal_file_bytes(path, "Wiederhergestellte Konfigurationsdatei")
    digest = hashlib.sha256(content).hexdigest()
    if digest != expected_sha256:
        raise ValueError(
            "Die wiederhergestellte Datei stimmt nicht bytegenau mit der ausgewählten "
            "Sicherung überein."
        )
    _records(path, kind)


def restore_config_backup(
    database: Path,
    backup: Path,
    *,
    confirm_name: str,
    yes: bool,
    config_directory: Path | None = None,
) -> ConfigRestoreResult:
    """Restore one selected configuration backup after a verified rollback backup."""
    if not yes:
        raise ValueError("Wiederherstellen benötigt die ausdrückliche Option --yes")

    comparison = compare_config_backup(
        database,
        backup,
        config_directory=config_directory,
    )
    if confirm_name != comparison.backup_name:
        raise ValueError(
            "Der bestätigte Sicherungsname stimmt nicht exakt überein. "
            "Es wurde nichts wiederhergestellt."
        )
    if not comparison.can_restore:
        raise ValueError(
            "Sicherung und aktive Konfiguration sind bereits identisch. "
            "Es wurde nichts überschrieben."
        )

    active = Path(comparison.active)
    selected = Path(comparison.backup)
    active_content = _normal_file_bytes(active, "Aktive Konfigurationsdatei")
    selected_content = _normal_file_bytes(selected, "Konfigurationssicherung")
    if hashlib.sha256(active_content).hexdigest() != comparison.active_sha256:
        raise ValueError(
            "Die aktive Konfiguration hat sich seit dem Vergleich verändert. "
            "Bitte den Vergleich erneut ausführen."
        )
    if hashlib.sha256(selected_content).hexdigest() != comparison.backup_sha256:
        raise ValueError(
            "Die ausgewählte Sicherung hat sich seit dem Vergleich verändert. "
            "Bitte den Vergleich erneut ausführen."
        )

    rollback = create_config_backup(active)
    if rollback.sha256 != comparison.active_sha256:
        raise ValueError(
            "Die aktive Konfiguration änderte sich während der Rückfallsicherung. "
            "Die Wiederherstellung wurde nicht gestartet."
        )
    current_content = _normal_file_bytes(active, "Aktive Konfigurationsdatei")
    if hashlib.sha256(current_content).hexdigest() != rollback.sha256:
        raise ValueError(
            "Die aktive Konfiguration änderte sich unmittelbar vor dem Überschreiben. "
            "Die Wiederherstellung wurde nicht gestartet."
        )

    try:
        atomic_write_bytes(active, selected_content, overwrite=True, mode=0o600)
        _verify_restored_file(
            active,
            kind=comparison.kind,
            expected_sha256=comparison.backup_sha256,
        )
    except BaseException as restore_error:
        try:
            rollback_content = _normal_file_bytes(
                Path(rollback.backup),
                "Automatische Rückfallsicherung",
            )
            atomic_write_bytes(active, rollback_content, overwrite=True, mode=0o600)
            _verify_restored_file(
                active,
                kind=comparison.kind,
                expected_sha256=rollback.sha256,
            )
        except BaseException as rollback_error:
            raise RuntimeError(
                "Wiederherstellung und automatischer Rückfall konnten nicht vollständig "
                "bestätigt werden. Die Rückfallsicherung bleibt erhalten: "
                f"{rollback.backup}"
            ) from rollback_error
        raise ValueError(
            "Die Wiederherstellung konnte nicht bestätigt werden. Die aktive Datei "
            "wurde automatisch aus der neuen Rückfallsicherung zurückgesetzt."
        ) from restore_error

    return ConfigRestoreResult(
        comparison=comparison,
        rollback_backup=rollback,
        restored_sha256=comparison.backup_sha256,
        completed_utc=datetime.now(timezone.utc).isoformat(),
    )
