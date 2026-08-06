from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from time import monotonic
from typing import Iterator

from datenbanktool.core.index_lock import IndexProcessLock
from datenbanktool.core.index_store import IndexDatabase
from datenbanktool.core.index_types import (
    IndexBuildOptions,
    IndexBuildResult,
    IndexStatus,
    RepairResult,
    ResumeCheckpointError,
    normalise_database_path,
    source_fingerprint,
    utc_now,
)
from datenbanktool.core.models import FileRecord, ScanError
from datenbanktool.core.progress import ProgressCallback, ProgressEvent, dispatch_progress
from datenbanktool.core.scanner import record_for_path, sha256_file


def iter_paths(
    root: Path,
    follow_symlinks: bool,
    checkpoint: str | None,
    errors: list[ScanError],
) -> Iterator[Path]:
    found_checkpoint = checkpoint is None

    def on_walk_error(error: OSError) -> None:
        errors.append(
            ScanError(
                path=str(getattr(error, "filename", root)),
                operation="walk",
                message=str(error),
            )
        )

    for current_root, directory_names, file_names in os.walk(
        root, followlinks=follow_symlinks, onerror=on_walk_error
    ):
        directory_names.sort(key=str.casefold)
        file_names.sort(key=str.casefold)
        current_path = Path(current_root)
        if not follow_symlinks:
            directory_names[:] = [
                name for name in directory_names if not (current_path / name).is_symlink()
            ]
        for file_name in file_names:
            path = current_path / file_name
            relative_path = path.relative_to(root).as_posix()
            if not found_checkpoint:
                if relative_path == checkpoint:
                    found_checkpoint = True
                continue
            yield path
    if not found_checkpoint:
        raise ResumeCheckpointError(
            "Der letzte sichere Haltepunkt wurde im Ordner nicht mehr gefunden. "
            f"Starte einen neuen Scan oder prüfe den Index. (Technisch: {checkpoint}.)"
        )


def emit_progress(
    database: IndexDatabase,
    callback: ProgressCallback | None,
    *,
    session_id: int,
    phase: str,
    kind: str,
    message: str,
    current: int | None = None,
    total: int | None = None,
    details: dict[str, object] | None = None,
) -> None:
    event = ProgressEvent(
        phase=phase,
        kind=kind,
        message=message,
        current=current,
        total=total,
        session_id=session_id,
        details=details or {},
    )
    database.add_progress_event(event)
    dispatch_progress(callback, event)


def _build_result(database: IndexDatabase, session_id: int, resumed: bool) -> IndexBuildResult:
    status = database.latest_status()
    return IndexBuildResult(
        database=status.database,
        session_id=session_id,
        status=status.status or "failed",
        phase=status.phase or "scanning",
        imported_count=status.imported_count,
        error_count=status.error_count,
        duplicate_group_count=status.duplicate_group_count,
        resumed=resumed,
        schema_version=status.schema_version,
    )


def _autosave_due(last_save: float, autosave_seconds: float) -> bool:
    return monotonic() - last_save >= autosave_seconds


def build_index(
    options: IndexBuildOptions,
    progress_callback: ProgressCallback | None = None,
) -> IndexBuildResult:
    if options.large_file_bytes < 0:
        raise ValueError("Die Grenze für große Dateien darf nicht negativ sein.")
    if options.batch_size < 1:
        raise ValueError("Die Autosave-Menge muss mindestens 1 Datei betragen.")
    if options.autosave_seconds <= 0:
        raise ValueError("Der Autosave-Abstand muss größer als 0 Sekunden sein.")
    if options.max_files is not None and options.max_files < 1:
        raise ValueError("Die Dateigrenze muss mindestens 1 sein.")
    root = options.root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"Der gewählte Ordner ist nicht vorhanden: {root}")
    payload = {
        "scan_mode": "full",
        "hash_duplicates": options.hash_duplicates,
        "large_file_bytes": options.large_file_bytes,
        "follow_symlinks": options.follow_symlinks,
    }
    fingerprint = source_fingerprint(root, payload)

    with IndexProcessLock(options.database, "index build", options.lock_timeout_seconds):
        with IndexDatabase(options.database) as database:
            database.migrate()
            row = database.resumable_session(fingerprint, "full") if options.resume else None
            resumed = row is not None
            if row is None:
                session_id = database.create_session(
                    root,
                    {
                        **payload,
                        "batch_size": options.batch_size,
                        "autosave_seconds": options.autosave_seconds,
                    },
                    fingerprint,
                    scan_mode="full",
                )
            else:
                session_id = int(row["id"])
                database.set_running(session_id)
            emit_progress(
                database,
                progress_callback,
                session_id=session_id,
                phase="scanning",
                kind="start" if not resumed else "resume",
                message=(
                    "Ordnerprüfung gestartet"
                    if not resumed
                    else "Ordnerprüfung wird am letzten sicheren Stand fortgesetzt"
                ),
                details={"autosave_seconds": options.autosave_seconds},
            )
            try:
                session = database.session(session_id)
                if str(session["phase"]) == "scanning":
                    records: list[FileRecord] = []
                    errors: list[ScanError] = []
                    processed_this_run = 0
                    checkpoint = session["last_relative_path"]
                    last_save = monotonic()
                    for path in iter_paths(root, options.follow_symlinks, checkpoint, errors):
                        if (
                            options.max_files is not None
                            and processed_this_run >= options.max_files
                        ):
                            if records or errors:
                                database.import_batch(session_id, records, errors, checkpoint)
                            database.mark_interrupted(session_id, truncated=True)
                            emit_progress(
                                database,
                                progress_callback,
                                session_id=session_id,
                                phase="scanning",
                                kind="interrupted",
                                message="Dateigrenze erreicht; sichere Fortsetzung möglich",
                                current=database.latest_status().imported_count,
                            )
                            return _build_result(database, session_id, resumed)
                        relative_path = path.relative_to(root).as_posix()
                        try:
                            records.append(
                                record_for_path(
                                    path,
                                    root,
                                    follow_symlinks=options.follow_symlinks,
                                    large_file_bytes=options.large_file_bytes,
                                )
                            )
                        except OSError as error:
                            errors.append(
                                ScanError(
                                    path=relative_path,
                                    operation="stat",
                                    message=str(error),
                                )
                            )
                        checkpoint = relative_path
                        processed_this_run += 1
                        if (
                            len(records) + len(errors) >= options.batch_size
                            or _autosave_due(last_save, options.autosave_seconds)
                        ):
                            database.import_batch(session_id, records, errors, checkpoint)
                            database.durable_checkpoint()
                            records.clear()
                            errors.clear()
                            last_save = monotonic()
                            emit_progress(
                                database,
                                progress_callback,
                                session_id=session_id,
                                phase="scanning",
                                kind="autosave",
                                message="Zwischenstand sicher gespeichert",
                                current=database.latest_status().imported_count,
                            )
                    if records or errors:
                        database.import_batch(session_id, records, errors, checkpoint)
                        database.durable_checkpoint()
                    database.set_phase(
                        session_id,
                        "hashing" if options.hash_duplicates else "finalizing",
                    )

                session = database.session(session_id)
                if str(session["phase"]) == "hashing":
                    hashes: list[tuple[str, int]] = []
                    errors = []
                    checkpoint = session["last_hash_path"]
                    hashed = 0
                    last_save = monotonic()
                    for candidate in database.hash_candidates(session_id, checkpoint):
                        relative_path = str(candidate["relative_path"])
                        try:
                            hashes.append(
                                (sha256_file(root / relative_path), int(candidate["id"]))
                            )
                        except OSError as error:
                            errors.append(
                                ScanError(
                                    path=relative_path,
                                    operation="sha256",
                                    message=str(error),
                                )
                            )
                        checkpoint = relative_path
                        hashed += 1
                        if (
                            len(hashes) + len(errors) >= options.batch_size
                            or _autosave_due(last_save, options.autosave_seconds)
                        ):
                            database.update_hash_batch(
                                session_id, hashes, errors, checkpoint
                            )
                            database.durable_checkpoint()
                            hashes.clear()
                            errors.clear()
                            last_save = monotonic()
                            emit_progress(
                                database,
                                progress_callback,
                                session_id=session_id,
                                phase="hashing",
                                kind="autosave",
                                message="Prüfsummen-Zwischenstand sicher gespeichert",
                                current=hashed,
                            )
                    if hashes or errors:
                        database.update_hash_batch(session_id, hashes, errors, checkpoint)
                        database.durable_checkpoint()
                    database.set_phase(session_id, "finalizing")

                if str(database.session(session_id)["phase"]) == "finalizing":
                    groups = database.rebuild_duplicate_groups(session_id)
                    database.mark_complete(session_id)
                    emit_progress(
                        database,
                        progress_callback,
                        session_id=session_id,
                        phase="complete",
                        kind="complete",
                        message="Ordnerprüfung erfolgreich abgeschlossen",
                        current=database.latest_status().imported_count,
                        details={"duplicate_groups": groups},
                    )
            except KeyboardInterrupt:
                database.mark_interrupted(session_id)
                emit_progress(
                    database,
                    progress_callback,
                    session_id=session_id,
                    phase=str(database.session(session_id)["phase"]),
                    kind="interrupted",
                    message="Abgebrochen; letzter sicherer Zwischenstand bleibt erhalten",
                )
                raise
            except Exception as error:
                database.mark_failed(session_id, str(error))
                emit_progress(
                    database,
                    progress_callback,
                    session_id=session_id,
                    phase=str(database.session(session_id)["phase"]),
                    kind="failed",
                    message="Ordnerprüfung konnte nicht abgeschlossen werden",
                    details={"error": str(error)},
                )
                raise
            return _build_result(database, session_id, resumed)


def inspect_index(path: Path) -> IndexStatus:
    if not path.expanduser().exists():
        raise FileNotFoundError(f"Die Indexdatei wurde nicht gefunden: {path.expanduser()}")
    with IndexDatabase(path) as database:
        database.migrate()
        return database.latest_status()


def integrity_rows(connection: sqlite3.Connection, pragma: str) -> tuple[str, ...]:
    return tuple(str(row[0]) for row in connection.execute(f"PRAGMA {pragma}"))


def repair_index(
    path: Path,
    *,
    create_backup: bool = True,
    vacuum: bool = False,
    lock_timeout_seconds: float = 0.0,
) -> RepairResult:
    from datenbanktool.core.index_admin import backup_index_unlocked

    target = normalise_database_path(path)
    if not target.exists():
        raise FileNotFoundError(f"Die Indexdatei wurde nicht gefunden: {target}")
    with IndexProcessLock(target, "index repair", lock_timeout_seconds):
        backup = (
            backup_index_unlocked(target, None, overwrite=False).backup
            if create_backup
            else None
        )
        actions: list[str] = []
        with IndexDatabase(target) as database:
            before = integrity_rows(database.connection, "quick_check")
            database.migrate()
            with database.connection:
                cursor = database.connection.execute(
                    "UPDATE scan_sessions SET status='interrupted', updated_utc=? WHERE status='running'",
                    (utc_now(),),
                )
                interrupted = int(cursor.rowcount)
            if interrupted:
                actions.append(
                    f"{interrupted} offene Prüfung(en) als unterbrochen markiert"
                )
            session_ids = [
                int(row[0])
                for row in database.connection.execute(
                    "SELECT id FROM scan_sessions WHERE imported_count>0"
                )
            ]
            for session_id in session_ids:
                database.rebuild_duplicate_groups(session_id)
            rebuilt = len(session_ids)
            if rebuilt:
                actions.append(
                    f"Doppelte Dateien für {rebuilt} Prüfung(en) neu zugeordnet"
                )
            with database.connection:
                database.connection.execute("REINDEX")
                database.connection.execute("ANALYZE")
            actions.extend(("Suchstruktur neu aufgebaut", "Abfragewerte aktualisiert"))
            if vacuum:
                database.connection.execute("VACUUM")
                actions.append("Indexdatei verkleinert")
            database.durable_checkpoint()
            foreign_key_errors = len(
                database.connection.execute("PRAGMA foreign_key_check").fetchall()
            )
            after = integrity_rows(database.connection, "integrity_check")
        successful = after == ("ok",) and foreign_key_errors == 0
        return RepairResult(
            database=str(target),
            backup=backup,
            before_integrity=before,
            after_integrity=after,
            foreign_key_errors=foreign_key_errors,
            interrupted_sessions=interrupted,
            rebuilt_duplicate_sessions=rebuilt,
            actions=tuple(actions),
            successful=successful,
        )
