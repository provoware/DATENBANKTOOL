from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
import uuid
from contextlib import suppress
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.persistence.database import Database
from src.persistence.migrations import CURRENT_SCHEMA_VERSION

BACKUP_MANIFEST_VERSION = 1
BACKUP_DATABASE_FILENAME = "database.sqlite3"
BACKUP_MANIFEST_FILENAME = "backup_manifest.json"


class BackupCreationError(RuntimeError):
    """Backup could not be created safely."""


class BackupVerificationError(RuntimeError):
    """Backup failed the independent verification gate."""


@dataclass(frozen=True)
class BackupManifest:
    manifest_version: int
    backup_id: str
    status: str
    created_at_utc: str
    database_file: str
    sha256: str
    size_bytes: int
    schema_version: int
    integrity_ok: bool
    quick_check: tuple[str, ...]
    foreign_key_violations: int


@dataclass(frozen=True)
class BackupVerificationReport:
    ok: bool
    backup_id: str
    backup_path: Path
    manifest: BackupManifest
    measured_sha256: str
    measured_size_bytes: int
    measured_schema_version: int
    quick_check: tuple[str, ...]
    foreign_key_violations: int


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        _fsync_directory(path.parent)
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name)


def _inspect_database(path: Path) -> tuple[int, tuple[str, ...], int]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        quick_rows = connection.execute("PRAGMA quick_check").fetchall()
        foreign_rows = connection.execute("PRAGMA foreign_key_check").fetchall()
    finally:
        connection.close()
    return (
        schema_version,
        tuple(str(row[0]) for row in quick_rows),
        len(foreign_rows),
    )


def _manifest_from_dict(data: dict[str, Any]) -> BackupManifest:
    try:
        quick_check = tuple(str(value) for value in data["quick_check"])
        return BackupManifest(
            manifest_version=int(data["manifest_version"]),
            backup_id=str(data["backup_id"]),
            status=str(data["status"]),
            created_at_utc=str(data["created_at_utc"]),
            database_file=str(data["database_file"]),
            sha256=str(data["sha256"]),
            size_bytes=int(data["size_bytes"]),
            schema_version=int(data["schema_version"]),
            integrity_ok=bool(data["integrity_ok"]),
            quick_check=quick_check,
            foreign_key_violations=int(data["foreign_key_violations"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise BackupVerificationError("Backup-Manifest ist unvollständig oder ungültig.") from exc


class BackupManager:
    def __init__(self, database: Database, backup_root: Path) -> None:
        self.database = database
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> BackupVerificationReport:
        source_status = self.database.schema_status()
        if not source_status.ready:
            raise BackupCreationError("Quelldatenbank ist nicht schema-bereit.")
        source_integrity = self.database.integrity_check()
        if not source_integrity.ok:
            raise BackupCreationError("Quelldatenbank hat die Integritätsprüfung nicht bestanden.")

        backup_id = f"bkp-{uuid.uuid4().hex}"
        staging = self.backup_root / f".incomplete_{backup_id}"
        final = self.backup_root / f"backup_status_verified_{_safe_stamp()}_{backup_id}"
        if staging.exists() or final.exists():
            raise BackupCreationError("Backup-Ziel existiert bereits.")

        staging.mkdir(parents=True, exist_ok=False)
        snapshot = staging / BACKUP_DATABASE_FILENAME
        try:
            self._create_sqlite_snapshot(snapshot)
            schema_version, quick_check, fk_violations = _inspect_database(snapshot)
            integrity_ok = quick_check == ("ok",) and fk_violations == 0
            if schema_version != CURRENT_SCHEMA_VERSION:
                raise BackupCreationError("Backup-Schema entspricht nicht der Zielversion.")
            if not integrity_ok:
                raise BackupCreationError("Backup-Snapshot ist nicht integer.")

            manifest = BackupManifest(
                manifest_version=BACKUP_MANIFEST_VERSION,
                backup_id=backup_id,
                status="verified",
                created_at_utc=_utc_now(),
                database_file=BACKUP_DATABASE_FILENAME,
                sha256=_sha256(snapshot),
                size_bytes=snapshot.stat().st_size,
                schema_version=schema_version,
                integrity_ok=True,
                quick_check=quick_check,
                foreign_key_violations=fk_violations,
            )
            _atomic_json_write(staging / BACKUP_MANIFEST_FILENAME, asdict(manifest))
            verification = self.verify_backup(staging, allow_staging=True)
            os.replace(staging, final)
            _fsync_directory(self.backup_root)
            return BackupVerificationReport(
                ok=True,
                backup_id=verification.backup_id,
                backup_path=final,
                manifest=verification.manifest,
                measured_sha256=verification.measured_sha256,
                measured_size_bytes=verification.measured_size_bytes,
                measured_schema_version=verification.measured_schema_version,
                quick_check=verification.quick_check,
                foreign_key_violations=verification.foreign_key_violations,
            )
        except Exception:
            if staging.exists():
                marker = staging / "STATUS_UNVOLLSTAENDIG.txt"
                with suppress(OSError):
                    marker.write_text(
                        "Dieses Backup ist unvollständig und darf nicht "
                        "wiederhergestellt werden.\n",
                        encoding="utf-8",
                    )
            raise

    def verify_backup(
        self,
        backup_path: Path,
        *,
        allow_staging: bool = False,
    ) -> BackupVerificationReport:
        path = Path(backup_path)
        if not path.is_dir():
            raise BackupVerificationError("Backup-Verzeichnis fehlt.")
        if path.name.startswith(".incomplete_") and not allow_staging:
            raise BackupVerificationError("Unvollständiges Staging-Backup ist nicht gültig.")
        manifest_path = path / BACKUP_MANIFEST_FILENAME
        database_path = path / BACKUP_DATABASE_FILENAME
        if not manifest_path.is_file() or not database_path.is_file():
            raise BackupVerificationError("Backup-Datei oder Manifest fehlt.")

        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BackupVerificationError("Backup-Manifest kann nicht gelesen werden.") from exc
        manifest = _manifest_from_dict(raw)
        if manifest.manifest_version != BACKUP_MANIFEST_VERSION:
            raise BackupVerificationError("Unbekannte Backup-Manifest-Version.")
        if manifest.status != "verified":
            raise BackupVerificationError("Backup ist nicht als verifiziert markiert.")
        if manifest.database_file != BACKUP_DATABASE_FILENAME:
            raise BackupVerificationError("Manifest verweist auf eine unerwartete Datenbankdatei.")

        measured_hash = _sha256(database_path)
        measured_size = database_path.stat().st_size
        schema_version, quick_check, fk_violations = _inspect_database(database_path)
        ok = (
            measured_hash == manifest.sha256
            and measured_size == manifest.size_bytes
            and schema_version == manifest.schema_version == CURRENT_SCHEMA_VERSION
            and quick_check == ("ok",)
            and fk_violations == 0
            and manifest.integrity_ok
            and manifest.quick_check == ("ok",)
            and manifest.foreign_key_violations == 0
        )
        if not ok:
            raise BackupVerificationError("Backup-Verifikation ist fehlgeschlagen.")

        return BackupVerificationReport(
            ok=True,
            backup_id=manifest.backup_id,
            backup_path=path,
            manifest=manifest,
            measured_sha256=measured_hash,
            measured_size_bytes=measured_size,
            measured_schema_version=schema_version,
            quick_check=quick_check,
            foreign_key_violations=fk_violations,
        )

    def list_verified_backups(self) -> tuple[Path, ...]:
        candidates = sorted(
            self.backup_root.glob("backup_status_verified_*"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        verified: list[Path] = []
        for candidate in candidates:
            try:
                self.verify_backup(candidate)
            except BackupVerificationError:
                continue
            verified.append(candidate)
        return tuple(verified)

    def _create_sqlite_snapshot(self, destination: Path) -> None:
        source = self.database.connect_raw()
        target = sqlite3.connect(destination)
        try:
            source.backup(target)
            target.commit()
        finally:
            target.close()
            source.close()
