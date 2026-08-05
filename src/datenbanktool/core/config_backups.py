from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from datenbanktool.core.durable_files import atomic_write_bytes, durable_remove


@dataclass(frozen=True, slots=True)
class ConfigBackupResult:
    source: str
    backup: str
    size_bytes: int
    sha256: str
    schema_version: int
    preset_count: int
    created_utc: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _validated_document(path: Path) -> tuple[bytes, int, int]:
    target = path.expanduser().absolute()
    if target.is_symlink():
        raise ValueError(
            "Symbolische Verknüpfungen werden nicht als Konfigurationsdatei gesichert."
        )
    if not target.is_file():
        raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {target}")
    content = target.read_bytes()
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(
            "Die Konfigurationsdatei ist kein gültiges UTF-8-JSON und wurde nicht gesichert."
        ) from error
    if not isinstance(payload, dict):
        raise ValueError("Die oberste JSON-Ebene muss ein Objekt sein.")
    schema = payload.get("schema_version")
    presets = payload.get("presets")
    if not isinstance(schema, int) or not isinstance(presets, list):
        raise ValueError(
            "Die Konfiguration enthält keine gültige schema_version oder presets-Liste."
        )
    return content, schema, len(presets)


def _backup_path(source: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S-%fZ")
    return source.with_name(f"{source.name}.backup-{stamp}-{os.getpid()}.json")


def create_config_backup(source: Path) -> ConfigBackupResult:
    """Create one validated timestamped JSON backup without rotation or deletion."""
    source_path = source.expanduser().absolute()
    content, schema, preset_count = _validated_document(source_path)
    digest = hashlib.sha256(content).hexdigest()
    backup = _backup_path(source_path)
    atomic_write_bytes(backup, content, mode=0o600)
    try:
        copied, copied_schema, copied_count = _validated_document(backup)
        copied_digest = hashlib.sha256(copied).hexdigest()
        if copied_digest != digest or copied_schema != schema or copied_count != preset_count:
            raise ValueError(
                "Die neue Konfigurationssicherung stimmt nicht vollständig mit der Quelle überein."
            )
    except BaseException:
        try:
            durable_remove(backup, missing_ok=True)
        except (OSError, ValueError):
            pass
        raise
    created = datetime.fromtimestamp(backup.stat().st_mtime, timezone.utc).isoformat()
    return ConfigBackupResult(
        source=str(source_path),
        backup=str(backup),
        size_bytes=len(content),
        sha256=digest,
        schema_version=schema,
        preset_count=preset_count,
        created_utc=created,
    )
