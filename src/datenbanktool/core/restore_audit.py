from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import BinaryIO

from datenbanktool.core.config_restore import ConfigRestoreResult
from datenbanktool.core.durable_files import atomic_write_text


_AUDIT_KEYS = {
    "schema_version",
    "event",
    "created_utc",
    "restore_completed_utc",
    "configuration_kind",
    "active_file",
    "selected_backup",
    "rollback_backup",
    "sha256",
}
_HASH_KEYS = {
    "active_after_restore",
    "selected_backup",
    "rollback_backup",
}
_HASH_ROLES = (
    ("active_after_restore", "Aktive Datei nach Wiederherstellung", "active_file"),
    ("selected_backup", "Ausgewählte Sicherung", "selected_backup"),
    ("rollback_backup", "Rückfallsicherung", "rollback_backup"),
)


@dataclass(frozen=True, slots=True)
class RestoreAuditResult:
    path: str
    size_bytes: int
    sha256: str
    created_utc: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RestoreAuditFileCheck:
    role: str
    label: str
    path: str
    expected_sha256: str
    actual_sha256: str | None
    state: str
    status_level: str
    status_label: str
    technical_detail: str

    @property
    def matches(self) -> bool:
        return self.state == "match"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["matches"] = self.matches
        return payload


@dataclass(frozen=True, slots=True)
class RestoreAuditVerification:
    protocol: str
    schema_version: int
    event: str
    created_utc: str
    restore_completed_utc: str
    configuration_kind: str
    status_level: str
    status_label: str
    technical_detail: str
    files: tuple[RestoreAuditFileCheck, ...]

    @property
    def all_files_match(self) -> bool:
        return all(item.matches for item in self.files)

    @property
    def matching_count(self) -> int:
        return sum(item.matches for item in self.files)

    @property
    def missing_count(self) -> int:
        return sum(item.state == "missing" for item in self.files)

    @property
    def mismatch_count(self) -> int:
        return sum(item.state == "mismatch" for item in self.files)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "event": self.event,
            "protocol": self.protocol,
            "created_utc": self.created_utc,
            "restore_completed_utc": self.restore_completed_utc,
            "configuration_kind": self.configuration_kind,
            "read_only": True,
            "status_level": self.status_level,
            "status_label": self.status_label,
            "technical_detail": self.technical_detail,
            "file_count": len(self.files),
            "matching_count": self.matching_count,
            "missing_count": self.missing_count,
            "mismatch_count": self.mismatch_count,
            "all_files_match": self.all_files_match,
            "files": [item.to_dict() for item in self.files],
        }


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


def _open_regular_no_follow(path: Path) -> BinaryIO:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        information = os.fstat(descriptor)
        if not stat.S_ISREG(information.st_mode):
            raise ValueError(f"Pfad ist keine normale Datei: {path}")
        return os.fdopen(descriptor, "rb")
    except BaseException:
        os.close(descriptor)
        raise


def _read_protocol(path: Path) -> bytes:
    target = _absolute(path)
    if target.is_symlink():
        raise ValueError(
            f"Symbolische Verknüpfung wird nicht als Wiederherstellungsprotokoll gelesen: {target}"
        )
    try:
        with _open_regular_no_follow(target) as stream:
            return stream.read()
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Wiederherstellungsprotokoll nicht gefunden: {target}") from error


def _require_exact_keys(
    payload: dict[str, object],
    expected: set[str],
    label: str,
) -> None:
    actual = set(payload)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append("fehlend: " + ", ".join(missing))
        if unexpected:
            details.append("unerwartet: " + ", ".join(unexpected))
        raise ValueError(f"{label} besitzt nicht das feste Schema ({'; '.join(details)}).")


def _parse_utc(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} muss eine UTC-Zeit als Text enthalten.")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(f"{label} ist keine gültige ISO-8601-Zeit: {value}") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{label} muss ausdrücklich in UTC angegeben sein: {value}")
    return parsed


def _require_absolute_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError(f"{label} muss einen nicht leeren absoluten Dateipfad enthalten.")
    path = Path(value)
    if not path.is_absolute():
        raise ValueError(f"{label} ist kein absoluter Dateipfad: {value}")
    return _absolute(path)


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} muss genau 64 hexadezimale Zeichen enthalten.")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} muss ein kleingeschriebener SHA-256-Wert sein.")
    return value


def _hash_stream(stream: BinaryIO) -> str:
    digest = hashlib.sha256()
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def _check_referenced_file(
    role: str,
    label: str,
    path: Path,
    expected: str,
) -> RestoreAuditFileCheck:
    if path.is_symlink():
        return RestoreAuditFileCheck(
            role,
            label,
            str(path),
            expected,
            None,
            "symlink-rejected",
            "red",
            "Symbolische Verknüpfung nicht geprüft",
            "Der Prüfpfad wird nicht verfolgt.",
        )
    try:
        with _open_regular_no_follow(path) as stream:
            actual = _hash_stream(stream)
    except FileNotFoundError:
        return RestoreAuditFileCheck(
            role,
            label,
            str(path),
            expected,
            None,
            "missing",
            "yellow",
            "Datei nicht vorhanden",
            "Der protokollierte Wert kann derzeit nicht gegen eine Datei bestätigt werden.",
        )
    except (OSError, ValueError) as error:
        return RestoreAuditFileCheck(
            role,
            label,
            str(path),
            expected,
            None,
            "unreadable",
            "red",
            "Datei nicht sicher lesbar",
            f"{type(error).__name__}: {error}",
        )
    if actual == expected:
        return RestoreAuditFileCheck(
            role,
            label,
            str(path),
            expected,
            actual,
            "match",
            "green",
            "SHA-256 stimmt überein",
            "Die vorhandene Datei entspricht dem protokollierten Wert.",
        )
    return RestoreAuditFileCheck(
        role,
        label,
        str(path),
        expected,
        actual,
        "mismatch",
        "red",
        "SHA-256 weicht ab",
        "Die vorhandene Datei entspricht nicht dem protokollierten Wert.",
    )


def verify_restore_audit_log(path: Path) -> RestoreAuditVerification:
    """Validate one explicitly selected audit log and compare referenced files read-only."""
    target = _absolute(path)
    raw = _read_protocol(target)
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(
            "Das Wiederherstellungsprotokoll ist kein gültiges UTF-8-JSON."
        ) from error
    if not isinstance(decoded, dict):
        raise ValueError("Die oberste Protokollebene muss ein JSON-Objekt sein.")
    payload: dict[str, object] = decoded
    _require_exact_keys(payload, _AUDIT_KEYS, "Wiederherstellungsprotokoll")

    if payload["schema_version"] != 1:
        raise ValueError("Unterstützt wird ausschließlich Protokollschema 1.")
    if payload["event"] != "configuration_restore":
        raise ValueError("Das Protokoll beschreibt keine Konfigurations-Wiederherstellung.")
    if payload["configuration_kind"] not in {"search", "timeline"}:
        raise ValueError("configuration_kind muss search oder timeline sein.")

    created = _parse_utc(payload["created_utc"], "created_utc")
    completed = _parse_utc(payload["restore_completed_utc"], "restore_completed_utc")
    if created < completed:
        raise ValueError("created_utc darf nicht vor restore_completed_utc liegen.")

    paths = {
        "active_file": _require_absolute_path(payload["active_file"], "active_file"),
        "selected_backup": _require_absolute_path(
            payload["selected_backup"], "selected_backup"
        ),
        "rollback_backup": _require_absolute_path(
            payload["rollback_backup"], "rollback_backup"
        ),
    }
    if len(set(paths.values())) != 3:
        raise ValueError("Das Protokoll muss drei unterschiedliche Dateipfade enthalten.")

    hashes = payload["sha256"]
    if not isinstance(hashes, dict):
        raise ValueError("sha256 muss ein JSON-Objekt sein.")
    _require_exact_keys(hashes, _HASH_KEYS, "sha256")
    expected_hashes = {
        key: _require_sha256(hashes[key], f"sha256.{key}") for key in _HASH_KEYS
    }

    checks = tuple(
        _check_referenced_file(
            role,
            label,
            paths[path_key],
            expected_hashes[role],
        )
        for role, label, path_key in _HASH_ROLES
    )
    if all(item.matches for item in checks):
        level = "green"
        label = "Protokoll und alle drei Dateien bestätigt"
        detail = "Schema, UTC-Zeiten, Pfade und sämtliche SHA-256-Werte sind konsistent."
    elif any(item.status_level == "red" for item in checks):
        level = "red"
        label = "Protokoll gültig, Dateinachweis fehlgeschlagen"
        detail = "Mindestens eine vorhandene Datei ist abweichend oder nicht sicher lesbar."
    else:
        level = "yellow"
        label = "Protokoll gültig, Dateinachweis unvollständig"
        detail = "Mindestens eine protokollierte Datei ist derzeit nicht vorhanden."

    return RestoreAuditVerification(
        protocol=str(target),
        schema_version=1,
        event="configuration_restore",
        created_utc=created.isoformat(),
        restore_completed_utc=completed.isoformat(),
        configuration_kind=str(payload["configuration_kind"]),
        status_level=level,
        status_label=label,
        technical_detail=detail,
        files=checks,
    )


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
