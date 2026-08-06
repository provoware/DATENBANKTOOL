from __future__ import annotations

import os
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from datenbanktool.core.durable_files import publish_temp_file
from datenbanktool.core.index_database import (
    SCHEMA_VERSION,
    IndexDatabase,
    UnsupportedSchemaError,
    integrity_rows,
    normalise_database_path,
)
from datenbanktool.core.index_lock import IndexProcessLock


@dataclass(frozen=True, slots=True)
class SessionSummary:
    session_id: int
    parent_session_id: int | None
    scan_mode: str
    root: str
    status: str
    phase: str
    started_utc: str
    updated_utc: str
    finished_utc: str | None
    imported_count: int
    error_count: int
    duplicate_group_count: int
    added_count: int
    modified_count: int
    moved_count: int
    removed_count: int
    unchanged_count: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BackupResult:
    database: str
    backup: str
    schema_version: int
    integrity: tuple[str, ...]
    size_bytes: int


@dataclass(frozen=True, slots=True)
class RestoreResult:
    database: str
    restored_from: str
    safety_backup: str | None
    schema_version: int
    integrity: tuple[str, ...]
    successful: bool


def list_sessions(
    path: Path,
    *,
    limit: int = 20,
    status: str | None = None,
    root: Path | None = None,
) -> list[SessionSummary]:
    if limit < 1:
        raise ValueError("Bitte zeige mindestens einen gespeicherten Scan an.")
    target = normalise_database_path(path)
    if not target.exists():
        raise FileNotFoundError(f"Die Indexdatei wurde nicht gefunden: {target}")
    with IndexDatabase(target) as database:
        database.migrate()
        clauses: list[str] = []
        parameters: list[object] = []
        if status is not None:
            clauses.append("s.status=?")
            parameters.append(status)
        if root is not None:
            clauses.append("s.root=?")
            parameters.append(str(root.expanduser().resolve(strict=False)))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        parameters.append(limit)
        rows = database.connection.execute(
            f"""
            SELECT s.*,
                   (SELECT COUNT(*) FROM duplicate_groups dg WHERE dg.session_id=s.id) AS duplicate_count,
                   (SELECT COUNT(*) FROM file_changes c WHERE c.session_id=s.id AND c.change_type='added') AS added_count,
                   (SELECT COUNT(*) FROM file_changes c WHERE c.session_id=s.id AND c.change_type='modified') AS modified_count,
                   (SELECT COUNT(*) FROM file_changes c WHERE c.session_id=s.id AND c.change_type='moved') AS moved_count,
                   (SELECT COUNT(*) FROM file_changes c WHERE c.session_id=s.id AND c.change_type='removed') AS removed_count,
                   (SELECT COUNT(*) FROM file_changes c WHERE c.session_id=s.id AND c.change_type='unchanged') AS unchanged_count
            FROM scan_sessions AS s
            {where}
            ORDER BY s.id DESC LIMIT ?
            """,
            parameters,
        ).fetchall()
        return [
            SessionSummary(
                session_id=int(row["id"]),
                parent_session_id=(
                    int(row["parent_session_id"]) if row["parent_session_id"] is not None else None
                ),
                scan_mode=str(row["scan_mode"]),
                root=str(row["root"]),
                status=str(row["status"]),
                phase=str(row["phase"]),
                started_utc=str(row["started_utc"]),
                updated_utc=str(row["updated_utc"]),
                finished_utc=str(row["finished_utc"]) if row["finished_utc"] is not None else None,
                imported_count=int(row["imported_count"]),
                error_count=int(row["error_count"]),
                duplicate_group_count=int(row["duplicate_count"]),
                added_count=int(row["added_count"]),
                modified_count=int(row["modified_count"]),
                moved_count=int(row["moved_count"]),
                removed_count=int(row["removed_count"]),
                unchanged_count=int(row["unchanged_count"]),
            )
            for row in rows
        ]


def _default_backup_path(source: Path, label: str = "backup") -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    return source.with_name(f"{source.name}.{label}-{stamp}.sqlite3")


def _validate_database(path: Path) -> tuple[int, tuple[str, ...]]:
    connection = sqlite3.connect(path)
    try:
        schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        integrity = integrity_rows(connection, "quick_check")
    finally:
        connection.close()
    if schema_version > SCHEMA_VERSION:
        raise UnsupportedSchemaError(
            f"Die Sicherung stammt aus einer neueren Tool-Version. "
            f"(Technisch: Schema {schema_version}, unterstützt bis {SCHEMA_VERSION}.)"
        )
    if integrity != ("ok",):
        raise sqlite3.DatabaseError(
            "Die Sicherung ist nicht vollständig in Ordnung. "
            f"(Technisch: SQLite quick_check: {', '.join(integrity)}.)"
        )
    return schema_version, integrity


def backup_index_unlocked(
    path: Path,
    output: Path | None,
    *,
    overwrite: bool = False,
    label: str = "backup",
) -> BackupResult:
    source_path = normalise_database_path(path)
    if not source_path.exists():
        raise FileNotFoundError(f"Die Indexdatei wurde nicht gefunden: {source_path}")
    target = (
        output.expanduser().resolve(strict=False)
        if output is not None
        else _default_backup_path(source_path, label)
    )
    if target == source_path:
        raise ValueError("Die Sicherung darf nicht dieselbe Datei wie der aktive Index sein.")
    if target.exists() and not overwrite:
        raise FileExistsError(f"Diese Sicherung gibt es bereits: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    temporary.unlink(missing_ok=True)
    source = sqlite3.connect(source_path)
    destination = sqlite3.connect(temporary)
    try:
        source.execute("PRAGMA wal_checkpoint(PASSIVE)")
        source.backup(destination)
        destination.commit()
    except BaseException:
        destination.close()
        source.close()
        temporary.unlink(missing_ok=True)
        raise
    else:
        destination.close()
        source.close()
    try:
        schema_version, integrity = _validate_database(temporary)
        publish_temp_file(temporary, target, overwrite=overwrite)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return BackupResult(
        database=str(source_path),
        backup=str(target),
        schema_version=schema_version,
        integrity=integrity,
        size_bytes=target.stat().st_size,
    )


def backup_index(
    path: Path,
    output: Path | None = None,
    *,
    overwrite: bool = False,
    lock_timeout_seconds: float = 0.0,
) -> BackupResult:
    target = normalise_database_path(path)
    with IndexProcessLock(target, "index backup", lock_timeout_seconds):
        return backup_index_unlocked(target, output, overwrite=overwrite)


def restore_index(
    path: Path,
    backup: Path,
    *,
    create_safety_backup: bool = True,
    lock_timeout_seconds: float = 0.0,
) -> RestoreResult:
    target = normalise_database_path(path)
    source_backup = backup.expanduser().resolve(strict=True)
    if not source_backup.is_file():
        raise FileNotFoundError(f"Die Sicherung wurde nicht gefunden: {source_backup}")
    schema_version, _ = _validate_database(source_backup)
    if source_backup == target:
        raise ValueError("Aktive Indexdatei und Sicherung dürfen nicht identisch sein.")

    with IndexProcessLock(target, "index restore", lock_timeout_seconds):
        safety: BackupResult | None = None
        if target.exists() and create_safety_backup:
            safety = backup_index_unlocked(target, None, label="pre-restore")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.restore-{os.getpid()}.tmp")
        temporary.unlink(missing_ok=True)
        source = sqlite3.connect(source_backup)
        destination = sqlite3.connect(temporary)
        try:
            source.backup(destination)
            destination.commit()
        except BaseException:
            destination.close()
            source.close()
            temporary.unlink(missing_ok=True)
            raise
        else:
            destination.close()
            source.close()
        try:
            _validate_database(temporary)
            if target.exists():
                connection = sqlite3.connect(target)
                try:
                    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                finally:
                    connection.close()
            publish_temp_file(temporary, target, overwrite=True)
            target.with_name(f"{target.name}-wal").unlink(missing_ok=True)
            target.with_name(f"{target.name}-shm").unlink(missing_ok=True)
            restored_schema, integrity = _validate_database(target)
        except BaseException:
            temporary.unlink(missing_ok=True)
            if safety is not None:
                fallback = Path(safety.backup)
                source = sqlite3.connect(fallback)
                destination = sqlite3.connect(target)
                try:
                    source.backup(destination)
                    destination.commit()
                finally:
                    destination.close()
                    source.close()
            raise
        return RestoreResult(
            database=str(target),
            restored_from=str(source_backup),
            safety_backup=safety.backup if safety else None,
            schema_version=restored_schema,
            integrity=integrity,
            successful=integrity == ("ok",) and restored_schema == schema_version,
        )
