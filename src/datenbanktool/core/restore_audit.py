from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from datenbanktool.core.config_restore import ConfigRestoreResult
from datenbanktool.core.durable_files import atomic_write_text


@dataclass(frozen=True, slots=True)
class RestoreAuditResult:
    path: str
    size_bytes: int
    sha256: str
    created_utc: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _payload(result: ConfigRestoreResult, created_utc: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "event": "configuration_restore",
        "created_utc": created_utc,
        "restore_completed_utc": result.completed_utc,
        "configuration_kind": result.comparison.kind,
        "active_file": result.comparison.active,
        "selected_backup": result.comparison.backup,
        "rollback_backup": result.rollback_backup.backup,
        "sha256": {
            "active_after_restore": result.restored_sha256,
            "selected_backup": result.comparison.backup_sha256,
            "rollback_backup": result.rollback_backup.sha256,
        },
    }


def write_restore_audit_log(
    result: ConfigRestoreResult,
    destination: Path,
) -> RestoreAuditResult:
    """Write one explicit content-free restore log without overwrite or rotation."""
    target = _absolute(destination)
    if target.is_symlink():
        raise ValueError(
            f"Symbolische Verknüpfung wird nicht als Wiederherstellungsprotokoll verwendet: {target}"
        )
    if target.exists():
        raise FileExistsError(
            f"Wiederherstellungsprotokoll existiert bereits und wird nicht überschrieben: {target}"
        )

    created_utc = datetime.now(timezone.utc).isoformat()
    payload = _payload(result, created_utc)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    atomic_write_text(target, text, mode=0o600)

    written = target.read_bytes()
    try:
        confirmed = json.loads(written.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(
            "Das Wiederherstellungsprotokoll konnte nach dem Schreiben nicht als UTF-8-JSON bestätigt werden."
        ) from error
    if confirmed != payload:
        raise ValueError(
            "Das Wiederherstellungsprotokoll stimmt nach dem Schreiben nicht vollständig mit dem geplanten Nachweis überein."
        )

    return RestoreAuditResult(
        path=str(target),
        size_bytes=len(written),
        sha256=hashlib.sha256(written).hexdigest(),
        created_utc=created_utc,
    )
