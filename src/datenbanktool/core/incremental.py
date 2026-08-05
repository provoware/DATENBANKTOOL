from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from time import monotonic

from datenbanktool.core.index_database import (
    IndexDatabase,
    IndexErrorBase,
    iter_paths,
    source_fingerprint,
)
from datenbanktool.core.index_lock import IndexProcessLock
from datenbanktool.core.models import FileRecord, ScanError
from datenbanktool.core.progress import ProgressCallback, ProgressEvent, dispatch_progress
from datenbanktool.core.scanner import record_for_path, sha256_file


@dataclass(frozen=True, slots=True)
class IncrementalScanOptions:
    root: Path
    database: Path
    baseline_session_id: int | None = None
    hash_duplicates: bool | None = None
    large_file_bytes: int | None = None
    follow_symlinks: bool | None = None
    detect_moves_by_hash: bool = True
    batch_size: int = 500
    autosave_seconds: float = 5.0
    resume: bool = False
    max_files: int | None = None
    lock_timeout_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class IncrementalScanResult:
    database: str
    session_id: int
    baseline_session_id: int
    status: str
    phase: str
    imported_count: int
    error_count: int
    duplicate_group_count: int
    added_count: int
    modified_count: int
    moved_count: int
    removed_count: int
    unchanged_count: int
    resumed: bool
    schema_version: int


def _emit(
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


def _baseline_file(database: IndexDatabase, session_id: int, relative_path: str):
    return database.connection.execute(
        """
        SELECT f.*, COALESCE(i.device_id,0) AS device_id,
               COALESCE(i.inode,0) AS inode, COALESCE(i.modified_ns,0) AS modified_ns
        FROM files AS f
        LEFT JOIN file_identity AS i ON i.file_id=f.id
        WHERE f.session_id=? AND f.relative_path=?
        """,
        (session_id, relative_path),
    ).fetchone()


def _same_file_state(record: FileRecord, baseline) -> bool:
    if int(baseline["size_bytes"]) != record.size_bytes:
        return False
    if bool(baseline["is_symlink"]) != record.is_symlink:
        return False
    baseline_device = int(baseline["device_id"])
    baseline_inode = int(baseline["inode"])
    if baseline_device > 0 and baseline_inode > 0 and record.device_id > 0 and record.inode > 0:
        if baseline_device != record.device_id or baseline_inode != record.inode:
            return False
    baseline_ns = int(baseline["modified_ns"])
    if baseline_ns > 0 and record.modified_ns > 0:
        return baseline_ns == record.modified_ns
    return str(baseline["modified_utc"]) == record.modified_utc


def _resolved_settings(options: IncrementalScanOptions, baseline) -> tuple[bool, int, bool]:
    stored = json.loads(str(baseline["options_json"]))
    hash_duplicates = (
        bool(stored.get("hash_duplicates", False))
        if options.hash_duplicates is None
        else options.hash_duplicates
    )
    large_file_bytes = (
        int(stored.get("large_file_bytes", 1024 * 1024 * 1024))
        if options.large_file_bytes is None
        else options.large_file_bytes
    )
    follow_symlinks = (
        bool(stored.get("follow_symlinks", False))
        if options.follow_symlinks is None
        else options.follow_symlinks
    )
    return hash_duplicates, large_file_bytes, follow_symlinks


def _autosave_due(last_save: float, autosave_seconds: float) -> bool:
    return monotonic() - last_save >= autosave_seconds


def _match_inode_moves(database: IndexDatabase, session_id: int, baseline_id: int) -> int:
    matches = database.connection.execute(
        """
        WITH old_unique AS (
            SELECT i.device_id, i.inode, MIN(f.id) AS old_id
            FROM files AS f JOIN file_identity AS i ON i.file_id=f.id
            WHERE f.session_id=? AND i.device_id<>0 AND i.inode<>0
              AND NOT EXISTS (
                  SELECT 1 FROM files AS current
                  WHERE current.session_id=? AND current.source_file_id=f.id
              )
            GROUP BY i.device_id, i.inode HAVING COUNT(*)=1
        ),
        new_unique AS (
            SELECT i.device_id, i.inode, MIN(f.id) AS new_id
            FROM files AS f JOIN file_identity AS i ON i.file_id=f.id
            WHERE f.session_id=? AND f.source_file_id IS NULL
            GROUP BY i.device_id, i.inode HAVING COUNT(*)=1
        )
        SELECT old.id AS old_id, old.relative_path AS old_path, old.sha256 AS old_sha,
               old.size_bytes AS old_size, old_i.modified_ns AS old_ns,
               new.id AS new_id, new.relative_path AS new_path,
               new.size_bytes AS new_size, new_i.modified_ns AS new_ns
        FROM old_unique AS ou
        JOIN new_unique AS nu USING(device_id, inode)
        JOIN files AS old ON old.id=ou.old_id
        JOIN files AS new ON new.id=nu.new_id
        JOIN file_identity AS old_i ON old_i.file_id=old.id
        JOIN file_identity AS new_i ON new_i.file_id=new.id
        WHERE old.relative_path<>new.relative_path
          AND old.size_bytes=new.size_bytes
          AND old_i.modified_ns=new_i.modified_ns
        """,
        (baseline_id, session_id, session_id),
    ).fetchall()
    with database.connection:
        for row in matches:
            preserve_hash = (
                row["old_sha"] is not None
                and int(row["old_size"]) == int(row["new_size"])
                and int(row["old_ns"]) == int(row["new_ns"])
            )
            database.connection.execute(
                "UPDATE files SET source_file_id=?, sha256=COALESCE(?, sha256) WHERE id=?",
                (row["old_id"], row["old_sha"] if preserve_hash else None, row["new_id"]),
            )
            database.connection.execute(
                """
                UPDATE file_changes
                SET change_type='moved', old_file_id=?, old_path=?, details_json=?
                WHERE session_id=? AND new_file_id=?
                """,
                (
                    row["old_id"],
                    row["old_path"],
                    json.dumps({"identity": "device-inode", "content_changed": not preserve_hash}),
                    session_id,
                    row["new_id"],
                ),
            )
    return len(matches)


def _hash_added_move_candidates(
    database: IndexDatabase,
    root: Path,
    session_id: int,
    baseline_id: int,
) -> int:
    candidates = database.connection.execute(
        """
        SELECT current.id, current.relative_path
        FROM files AS current
        WHERE current.session_id=? AND current.source_file_id IS NULL
          AND EXISTS (
              SELECT 1 FROM files AS old
              WHERE old.session_id=? AND old.sha256 IS NOT NULL
                AND old.size_bytes=current.size_bytes
                AND NOT EXISTS (
                    SELECT 1 FROM files AS mapped
                    WHERE mapped.session_id=? AND mapped.source_file_id=old.id
                )
          )
        ORDER BY current.relative_path COLLATE NOCASE, current.relative_path
        """,
        (session_id, baseline_id, session_id),
    ).fetchall()
    with database.connection:
        for row in candidates:
            digest = sha256_file(root / str(row["relative_path"]))
            database.connection.execute("UPDATE files SET sha256=? WHERE id=?", (digest, row["id"]))

    matches = database.connection.execute(
        """
        WITH old_unique AS (
            SELECT sha256, size_bytes, MIN(id) AS old_id
            FROM files
            WHERE session_id=? AND sha256 IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM files AS mapped
                  WHERE mapped.session_id=? AND mapped.source_file_id=files.id
              )
            GROUP BY sha256, size_bytes HAVING COUNT(*)=1
        ),
        new_unique AS (
            SELECT sha256, size_bytes, MIN(id) AS new_id
            FROM files
            WHERE session_id=? AND source_file_id IS NULL AND sha256 IS NOT NULL
            GROUP BY sha256, size_bytes HAVING COUNT(*)=1
        )
        SELECT old.id AS old_id, old.relative_path AS old_path,
               new.id AS new_id, new.relative_path AS new_path
        FROM old_unique AS ou
        JOIN new_unique AS nu USING(sha256, size_bytes)
        JOIN files AS old ON old.id=ou.old_id
        JOIN files AS new ON new.id=nu.new_id
        WHERE old.relative_path<>new.relative_path
        """,
        (baseline_id, session_id, session_id),
    ).fetchall()
    with database.connection:
        for row in matches:
            database.connection.execute(
                "UPDATE files SET source_file_id=? WHERE id=?",
                (row["old_id"], row["new_id"]),
            )
            database.connection.execute(
                """
                UPDATE file_changes
                SET change_type='moved', old_file_id=?, old_path=?,
                    details_json='{"identity":"sha256"}'
                WHERE session_id=? AND new_file_id=?
                """,
                (row["old_id"], row["old_path"], session_id, row["new_id"]),
            )
    return len(matches)


def _record_removed(database: IndexDatabase, session_id: int, baseline_id: int) -> int:
    with database.connection:
        database.connection.execute(
            "DELETE FROM file_changes WHERE session_id=? AND change_type='removed'",
            (session_id,),
        )
        cursor = database.connection.execute(
            """
            INSERT INTO file_changes(
                session_id, change_type, old_file_id, new_file_id, old_path, new_path, details_json
            )
            SELECT ?, 'removed', old.id, NULL, old.relative_path, NULL, '{}'
            FROM files AS old
            WHERE old.session_id=?
              AND NOT EXISTS (
                  SELECT 1 FROM files AS current
                  WHERE current.session_id=? AND current.source_file_id=old.id
              )
            """,
            (session_id, baseline_id, session_id),
        )
    return int(cursor.rowcount)


def _result(database: IndexDatabase, session_id: int, baseline_id: int, resumed: bool) -> IncrementalScanResult:
    status = database.latest_status()
    counts = database.change_counts(session_id)
    return IncrementalScanResult(
        database=status.database,
        session_id=session_id,
        baseline_session_id=baseline_id,
        status=status.status or "failed",
        phase=status.phase or "scanning",
        imported_count=status.imported_count,
        error_count=status.error_count,
        duplicate_group_count=status.duplicate_group_count,
        added_count=counts["added"],
        modified_count=counts["modified"],
        moved_count=counts["moved"],
        removed_count=counts["removed"],
        unchanged_count=counts["unchanged"],
        resumed=resumed,
        schema_version=status.schema_version,
    )


def incremental_rescan(
    options: IncrementalScanOptions,
    progress_callback: ProgressCallback | None = None,
) -> IncrementalScanResult:
    if options.batch_size < 1:
        raise ValueError("Die Autosave-Menge muss mindestens 1 Datei betragen.")
    if options.autosave_seconds <= 0:
        raise ValueError("Der Autosave-Abstand muss größer als 0 Sekunden sein.")
    if options.max_files is not None and options.max_files < 1:
        raise ValueError("Die Dateigrenze muss mindestens 1 sein.")
    root = options.root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"Der gewählte Ordner ist nicht vorhanden: {root}")

    with IndexProcessLock(options.database, "index rescan", options.lock_timeout_seconds):
        with IndexDatabase(options.database) as database:
            database.migrate()
            if options.baseline_session_id is None:
                baseline = database.latest_complete_session(root)
            else:
                baseline = database.session(options.baseline_session_id)
                if str(baseline["status"]) != "complete":
                    raise IndexErrorBase(
                        "Der Vergleichsstand ist noch nicht vollständig abgeschlossen."
                    )
                if str(baseline["root"]) != str(root):
                    raise IndexErrorBase(
                        "Der frühere Scan gehört zu einem anderen Stammordner."
                    )
            if baseline is None:
                raise IndexErrorBase(
                    "Es gibt noch keinen vollständigen Ausgangsstand. Starte zuerst "
                    "'datenbanktool index build'. (Technisch: keine Baseline.)"
                )
            baseline_id = int(baseline["id"])
            hash_duplicates, large_file_bytes, follow_symlinks = _resolved_settings(options, baseline)
            if large_file_bytes < 0:
                raise ValueError("Die Grenze für große Dateien darf nicht negativ sein.")
            payload = {
                "scan_mode": "incremental",
                "baseline_session_id": baseline_id,
                "hash_duplicates": hash_duplicates,
                "large_file_bytes": large_file_bytes,
                "follow_symlinks": follow_symlinks,
                "detect_moves_by_hash": options.detect_moves_by_hash,
            }
            fingerprint = source_fingerprint(root, payload)
            resumable = database.resumable_session(fingerprint, "incremental") if options.resume else None
            resumed = resumable is not None
            if resumable is None:
                session_id = database.create_session(
                    root,
                    {
                        **payload,
                        "batch_size": options.batch_size,
                        "autosave_seconds": options.autosave_seconds,
                    },
                    fingerprint,
                    scan_mode="incremental",
                    parent_session_id=baseline_id,
                )
            else:
                session_id = int(resumable["id"])
                if int(resumable["parent_session_id"]) != baseline_id:
                    raise IndexErrorBase(
                        "Der gespeicherte Zwischenstand passt nicht mehr zum Vergleichsstand."
                    )
                database.set_running(session_id)
            _emit(
                database,
                progress_callback,
                session_id=session_id,
                phase="scanning",
                kind="resume" if resumed else "start",
                message=(
                    "Änderungsprüfung wird am letzten sicheren Stand fortgesetzt"
                    if resumed
                    else "Änderungsprüfung gestartet"
                ),
                details={
                    "baseline_session_id": baseline_id,
                    "autosave_seconds": options.autosave_seconds,
                },
            )
            try:
                session = database.session(session_id)
                if str(session["phase"]) == "scanning":
                    items: list[tuple[FileRecord, int | None, str, str | None]] = []
                    errors: list[ScanError] = []
                    checkpoint = session["last_relative_path"]
                    processed_this_run = 0
                    last_save = monotonic()
                    for path in iter_paths(root, follow_symlinks, checkpoint, errors):
                        if options.max_files is not None and processed_this_run >= options.max_files:
                            if items or errors:
                                database.import_incremental_batch(session_id, items, errors, checkpoint)
                            database.mark_interrupted(session_id, truncated=True)
                            _emit(
                                database,
                                progress_callback,
                                session_id=session_id,
                                phase="scanning",
                                kind="interrupted",
                                message="Dateigrenze erreicht; sichere Fortsetzung möglich",
                                current=database.latest_status().imported_count,
                            )
                            return _result(database, session_id, baseline_id, resumed)
                        relative_path = path.relative_to(root).as_posix()
                        try:
                            record = record_for_path(
                                path,
                                root,
                                follow_symlinks=follow_symlinks,
                                large_file_bytes=large_file_bytes,
                            )
                            old = _baseline_file(database, baseline_id, relative_path)
                            if old is None:
                                items.append((record, None, "added", None))
                            elif _same_file_state(record, old):
                                record.sha256 = old["sha256"]
                                items.append((record, int(old["id"]), "unchanged", relative_path))
                            else:
                                items.append((record, int(old["id"]), "modified", relative_path))
                        except OSError as error:
                            errors.append(ScanError(path=relative_path, operation="stat", message=str(error)))
                        checkpoint = relative_path
                        processed_this_run += 1
                        if (
                            len(items) + len(errors) >= options.batch_size
                            or _autosave_due(last_save, options.autosave_seconds)
                        ):
                            database.import_incremental_batch(session_id, items, errors, checkpoint)
                            database.durable_checkpoint()
                            items.clear()
                            errors.clear()
                            last_save = monotonic()
                            _emit(
                                database,
                                progress_callback,
                                session_id=session_id,
                                phase="scanning",
                                kind="autosave",
                                message="Zwischenstand sicher gespeichert",
                                current=database.latest_status().imported_count,
                            )
                    if items or errors:
                        database.import_incremental_batch(session_id, items, errors, checkpoint)
                        database.durable_checkpoint()
                    database.set_incremental_stage(session_id, "comparing", phase="finalizing")

                if str(database.session(session_id)["incremental_stage"]) == "comparing":
                    inode_moves = _match_inode_moves(database, session_id, baseline_id)
                    hash_moves = 0
                    if options.detect_moves_by_hash:
                        hash_moves = _hash_added_move_candidates(database, root, session_id, baseline_id)
                    removed = _record_removed(database, session_id, baseline_id)
                    database.durable_checkpoint()
                    database.set_incremental_stage(
                        session_id,
                        "hashing" if hash_duplicates else "finalizing",
                        phase="hashing" if hash_duplicates else "finalizing",
                    )
                    _emit(
                        database,
                        progress_callback,
                        session_id=session_id,
                        phase="comparing",
                        kind="complete",
                        message="Änderungen vollständig verglichen",
                        details={
                            "inode_moves": inode_moves,
                            "hash_moves": hash_moves,
                            "removed": removed,
                            **database.change_counts(session_id),
                        },
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
                            hashes.append((sha256_file(root / relative_path), int(candidate["id"])))
                        except OSError as error:
                            errors.append(ScanError(path=relative_path, operation="sha256", message=str(error)))
                        checkpoint = relative_path
                        hashed += 1
                        if (
                            len(hashes) + len(errors) >= options.batch_size
                            or _autosave_due(last_save, options.autosave_seconds)
                        ):
                            database.update_hash_batch(session_id, hashes, errors, checkpoint)
                            database.durable_checkpoint()
                            hashes.clear()
                            errors.clear()
                            last_save = monotonic()
                            _emit(
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
                    database.set_incremental_stage(session_id, "finalizing", phase="finalizing")

                if (
                    str(database.session(session_id)["phase"]) == "finalizing"
                    and str(database.session(session_id)["incremental_stage"]) == "finalizing"
                ):
                    groups = database.rebuild_duplicate_groups(session_id)
                    database.mark_complete(session_id)
                    _emit(
                        database,
                        progress_callback,
                        session_id=session_id,
                        phase="complete",
                        kind="complete",
                        message="Änderungsprüfung erfolgreich abgeschlossen",
                        current=database.latest_status().imported_count,
                        details={"duplicate_groups": groups, **database.change_counts(session_id)},
                    )
            except KeyboardInterrupt:
                database.mark_interrupted(session_id)
                _emit(
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
                _emit(
                    database,
                    progress_callback,
                    session_id=session_id,
                    phase=str(database.session(session_id)["phase"]),
                    kind="failed",
                    message="Änderungsprüfung konnte nicht abgeschlossen werden",
                    details={"error": str(error)},
                )
                raise
            return _result(database, session_id, baseline_id, resumed)
