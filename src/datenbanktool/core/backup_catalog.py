from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from datenbanktool.core.durable_files import durable_remove
from datenbanktool.core.index_types import SCHEMA_VERSION
from datenbanktool.core.presets import default_preset_path
from datenbanktool.core.timeline_presets import default_timeline_preset_path


@dataclass(frozen=True, slots=True)
class BackupItem:
    path: str
    name: str
    kind: str
    kind_label: str
    size_bytes: int
    modified_utc: str
    age_seconds: int
    status_level: str
    status_label: str
    technical_detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def default_config_directory() -> Path:
    return default_preset_path().parent


def _looks_like_index_backup(path: Path, database: Path) -> bool:
    name = path.name
    prefixes = (
        f"{database.name}.backup-",
        f"{database.name}.pre-restore-",
    )
    return name.endswith(".sqlite3") and name.startswith(prefixes)


def _looks_like_config_backup(path: Path) -> bool:
    for active in (default_preset_path().name, default_timeline_preset_path().name):
        active_path = Path(active)
        prefixes = (
            f"{active}.backup-",
            f"{active_path.stem}.backup-",
            f"{active_path.stem}-backup-",
        )
        exact = {f"{active}.bak", f"{active}.backup"}
        if path.name in exact or path.name.startswith(prefixes):
            return True
    return False


def _sqlite_status(path: Path) -> tuple[str, str, str]:
    if path.is_symlink():
        return "red", "Nicht freigegeben", "symbolische Verknüpfung statt Sicherungsdatei"
    uri = f"file:{quote(str(path), safe='/')}?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
        try:
            connection.execute("PRAGMA query_only = ON")
            schema = int(connection.execute("PRAGMA user_version").fetchone()[0])
            rows = tuple(
                str(row[0])
                for row in connection.execute("PRAGMA quick_check").fetchall()
            )
        finally:
            connection.close()
    except (OSError, sqlite3.Error) as error:
        return "red", "Nicht lesbar", f"SQLite-Prüfung fehlgeschlagen: {error}"
    if rows != ("ok",):
        return "red", "Beschädigt", "SQLite quick_check: " + ", ".join(rows)
    if schema > SCHEMA_VERSION:
        return (
            "yellow",
            "Neuere Datenbankversion",
            f"SQLite quick_check ok; Schema {schema}, unterstützt bis {SCHEMA_VERSION}",
        )
    return "green", "Geprüft und nutzbar", f"SQLite quick_check ok; Schema {schema}"


def _config_status(path: Path) -> tuple[str, str, str]:
    if path.is_symlink():
        return "red", "Nicht freigegeben", "symbolische Verknüpfung statt Sicherungsdatei"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return "red", "Beschädigt", f"JSON-Prüfung fehlgeschlagen: {error}"
    if not isinstance(payload, dict):
        return "red", "Beschädigt", "oberste JSON-Ebene ist kein Objekt"
    schema = payload.get("schema_version")
    presets = payload.get("presets")
    if not isinstance(schema, int) or not isinstance(presets, list):
        return "red", "Unvollständig", "schema_version oder presets-Liste fehlt"
    if schema != 1:
        return "yellow", "Unbekannte Version", f"Konfigurationsschema {schema}"
    return "green", "Geprüft und nutzbar", "JSON-Schema 1 und presets-Liste lesbar"


def _item(path: Path, kind: str) -> BackupItem:
    stat = path.lstat()
    modified = datetime.fromtimestamp(stat.st_mtime, timezone.utc)
    now = datetime.now(timezone.utc)
    age_seconds = max(0, int((now - modified).total_seconds()))
    if kind == "index":
        level, label, detail = _sqlite_status(path)
        kind_label = "Index-Sicherung"
    else:
        level, label, detail = _config_status(path)
        kind_label = "Konfigurations-Sicherung"
    return BackupItem(
        path=str(path.absolute()),
        name=path.name,
        kind=kind,
        kind_label=kind_label,
        size_bytes=stat.st_size,
        modified_utc=modified.isoformat(),
        age_seconds=age_seconds,
        status_level=level,
        status_label=label,
        technical_detail=detail,
    )


def list_backups(
    database: Path,
    *,
    config_directory: Path | None = None,
) -> tuple[BackupItem, ...]:
    """List recognized backup files without changing or opening active user files."""
    database_path = database.expanduser().resolve(strict=False)
    config_path = (config_directory or default_config_directory()).expanduser().resolve(
        strict=False
    )
    candidates: dict[str, tuple[Path, str]] = {}
    if database_path.parent.is_dir():
        for path in database_path.parent.iterdir():
            if path.is_file() and _looks_like_index_backup(path, database_path):
                candidates[str(path.absolute())] = (path, "index")
    if config_path.is_dir():
        for path in config_path.iterdir():
            if path.is_file() and _looks_like_config_backup(path):
                candidates[str(path.absolute())] = (path, "configuration")
    items: list[BackupItem] = []
    for path, kind in candidates.values():
        try:
            items.append(_item(path, kind))
        except OSError:
            continue
    return tuple(sorted(items, key=lambda item: (-item.age_seconds, item.path), reverse=True))


def delete_backup(
    database: Path,
    backup: Path,
    *,
    confirm_name: str,
    yes: bool,
    config_directory: Path | None = None,
) -> BackupItem:
    """Delete one explicitly selected recognized backup after exact-name confirmation."""
    if not yes:
        raise ValueError("Löschen benötigt die ausdrückliche Option --yes")
    target = backup.expanduser().absolute()
    if target.is_symlink():
        raise ValueError("Symbolische Verknüpfungen werden nicht als Sicherung gelöscht")
    items = list_backups(database, config_directory=config_directory)
    selected = next((item for item in items if item.path == str(target)), None)
    if selected is None:
        raise ValueError(
            "Die Datei gehört nicht zur geprüften Sicherungsübersicht. Sie wurde nicht gelöscht."
        )
    if confirm_name != selected.name:
        raise ValueError(
            "Der bestätigte Dateiname stimmt nicht exakt überein. Es wurde nichts gelöscht."
        )
    durable_remove(target)
    return selected
