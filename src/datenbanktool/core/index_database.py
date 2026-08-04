from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from datenbanktool.core.classification import classify_path
from datenbanktool.core.models import FileRecord, ScanError
from datenbanktool.core.naming import filename_warnings
from datenbanktool.core.scanner import sha256_file

SCHEMA_VERSION = 2
_DEFAULT_BATCH_SIZE = 500
_VALID_PHASES = frozenset({"scanning", "hashing", "finalizing", "complete"})


class IndexErrorBase(RuntimeError):
    """Base class for index-specific errors."""


class UnsupportedSchemaError(IndexErrorBase):
    """Raised when a database is newer than this program."""


class ResumeCheckpointError(IndexErrorBase):
    """Raised when a safe resume checkpoint cannot be found."""


@dataclass(frozen=True, slots=True)
class IndexBuildOptions:
    root: Path
    database: Path
    hash_duplicates: bool = False
    large_file_bytes: int = 1024 * 1024 * 1024
    follow_symlinks: bool = False
    batch_size: int = _DEFAULT_BATCH_SIZE
    resume: bool = False
    max_files: int | None = None


@dataclass(frozen=True, slots=True)
class IndexBuildResult:
    database: str
    session_id: int
    status: str
    phase: str
    imported_count: int
    error_count: int
    duplicate_group_count: int
    resumed: bool
    schema_version: int


@dataclass(frozen=True, slots=True)
class IndexStatus:
    database: str
    schema_version: int
    session_id: int | None
    root: str | None
    status: str | None
    phase: str | None
    imported_count: int
    error_count: int
    duplicate_group_count: int
    updated_utc: str | None


@dataclass(frozen=True, slots=True)
class RepairResult:
    database: str
    backup: str | None
    before_integrity: tuple[str, ...]
    after_integrity: tuple[str, ...]
    foreign_key_errors: int
    interrupted_sessions: int
    rebuilt_duplicate_sessions: int
    actions: tuple[str, ...]
    successful: bool


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalise_database_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _source_fingerprint(root: Path, options: IndexBuildOptions) -> str:
    payload = {
        "root": str(root),
        "hash_duplicates": options.hash_duplicates,
        "large_file_bytes": options.large_file_bytes,
        "follow_symlinks": options.follow_symlinks,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _migration_1(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_utc TEXT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS scan_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root TEXT NOT NULL,
            options_json TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('running', 'interrupted', 'complete', 'failed')),
            phase TEXT NOT NULL CHECK (phase IN ('scanning', 'hashing', 'finalizing', 'complete')),
            started_utc TEXT NOT NULL,
            updated_utc TEXT NOT NULL,
            finished_utc TEXT,
            last_relative_path TEXT,
            last_hash_path TEXT,
            imported_count INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER NOT NULL DEFAULT 0,
            truncated INTEGER NOT NULL DEFAULT 0 CHECK (truncated IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE,
            relative_path TEXT NOT NULL,
            size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
            modified_utc TEXT NOT NULL,
            suffix TEXT NOT NULL,
            category TEXT NOT NULL,
            is_symlink INTEGER NOT NULL CHECK (is_symlink IN (0, 1)),
            is_large INTEGER NOT NULL CHECK (is_large IN (0, 1)),
            sha256 TEXT,
            UNIQUE (session_id, relative_path)
        );

        CREATE TABLE IF NOT EXISTS filename_warnings (
            file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
            code TEXT NOT NULL,
            PRIMARY KEY (file_id, code)
        );

        CREATE TABLE IF NOT EXISTS scan_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE,
            path TEXT NOT NULL,
            operation TEXT NOT NULL,
            message TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS duplicate_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE,
            sha256 TEXT NOT NULL,
            size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
            UNIQUE (session_id, sha256, size_bytes)
        );

        CREATE TABLE IF NOT EXISTS duplicate_members (
            group_id INTEGER NOT NULL REFERENCES duplicate_groups(id) ON DELETE CASCADE,
            file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
            PRIMARY KEY (group_id, file_id)
        );
        """
    )


def _migration_2(connection: sqlite3.Connection) -> None:
    columns = {row[1] for row in connection.execute("PRAGMA table_info(scan_sessions)")}
    if "source_fingerprint" not in columns:
        connection.execute("ALTER TABLE scan_sessions ADD COLUMN source_fingerprint TEXT")
    connection.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_sessions_status_updated
            ON scan_sessions(status, updated_utc DESC);
        CREATE INDEX IF NOT EXISTS idx_sessions_fingerprint
            ON scan_sessions(source_fingerprint, id DESC);
        CREATE INDEX IF NOT EXISTS idx_files_session_path
            ON files(session_id, relative_path COLLATE NOCASE);
        CREATE INDEX IF NOT EXISTS idx_files_session_category
            ON files(session_id, category);
        CREATE INDEX IF NOT EXISTS idx_files_session_size
            ON files(session_id, size_bytes);
        CREATE INDEX IF NOT EXISTS idx_files_session_sha
            ON files(session_id, sha256, size_bytes);
        CREATE INDEX IF NOT EXISTS idx_warnings_code
            ON filename_warnings(code, file_id);
        CREATE INDEX IF NOT EXISTS idx_errors_session
            ON scan_errors(session_id, id);
        CREATE INDEX IF NOT EXISTS idx_duplicate_groups_session
            ON duplicate_groups(session_id, id);
        CREATE INDEX IF NOT EXISTS idx_duplicate_members_file
            ON duplicate_members(file_id, group_id);
        """
    )


_MIGRATIONS = {
    1: ("Initialer transaktionaler Dateiindex", _migration_1),
    2: ("Wiederaufnahme-Fingerabdruck und Berichtindizes", _migration_2),
}


class IndexDatabase:
    def __init__(self, path: Path) -> None:
        self.path = _normalise_database_path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 5000")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = NORMAL")

    def __enter__(self) -> "IndexDatabase":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    def schema_version(self) -> int:
        return int(self.connection.execute("PRAGMA user_version").fetchone()[0])

    def migrate(self) -> int:
        current = self.schema_version()
        if current > SCHEMA_VERSION:
            raise UnsupportedSchemaError(
                f"Datenbankschema {current} ist neuer als unterstützte Version {SCHEMA_VERSION}."
            )
        for version in range(current + 1, SCHEMA_VERSION + 1):
            description, migration = _MIGRATIONS[version]
            with self.connection:
                migration(self.connection)
                self.connection.execute(
                    "INSERT OR REPLACE INTO schema_migrations(version, applied_utc, description) VALUES (?, ?, ?)",
                    (version, utc_now(), description),
                )
                self.connection.execute(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES ('schema_version', ?)",
                    (str(version),),
                )
                self.connection.execute(f"PRAGMA user_version = {version}")
        if self.schema_version() == SCHEMA_VERSION:
            with self.connection:
                self.connection.execute(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES ('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
        return self.schema_version()

    def create_session(self, root: Path, options: IndexBuildOptions, fingerprint: str) -> int:
        now = utc_now()
        options_json = json.dumps(
            {
                "hash_duplicates": options.hash_duplicates,
                "large_file_bytes": options.large_file_bytes,
                "follow_symlinks": options.follow_symlinks,
                "batch_size": options.batch_size,
            },
            sort_keys=True,
        )
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO scan_sessions(
                    root, options_json, status, phase, started_utc, updated_utc, source_fingerprint
                ) VALUES (?, ?, 'running', 'scanning', ?, ?, ?)
                """,
                (str(root), options_json, now, now, fingerprint),
            )
        return int(cursor.lastrowid)

    def resumable_session(self, fingerprint: str) -> sqlite3.Row | None:
        return self.connection.execute(
            """
            SELECT * FROM scan_sessions
            WHERE source_fingerprint = ? AND status IN ('running', 'interrupted', 'failed')
            ORDER BY id DESC LIMIT 1
            """,
            (fingerprint,),
        ).fetchone()

    def session(self, session_id: int) -> sqlite3.Row:
        row = self.connection.execute(
            "SELECT * FROM scan_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise IndexErrorBase(f"Index-Sitzung nicht gefunden: {session_id}")
        return row

    def set_running(self, session_id: int) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE scan_sessions SET status='running', updated_utc=?, truncated=0 WHERE id=?",
                (utc_now(), session_id),
            )

    def import_batch(
        self,
        session_id: int,
        records: list[FileRecord],
        errors: list[ScanError],
        checkpoint: str | None,
    ) -> None:
        with self.connection:
            for record in records:
                self.connection.execute(
                    """
                    INSERT INTO files(
                        session_id, relative_path, size_bytes, modified_utc, suffix, category,
                        is_symlink, is_large, sha256
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id, relative_path) DO UPDATE SET
                        size_bytes=excluded.size_bytes,
                        modified_utc=excluded.modified_utc,
                        suffix=excluded.suffix,
                        category=excluded.category,
                        is_symlink=excluded.is_symlink,
                        is_large=excluded.is_large,
                        sha256=COALESCE(excluded.sha256, files.sha256)
                    """,
                    (
                        session_id,
                        record.relative_path,
                        record.size_bytes,
                        record.modified_utc,
                        record.suffix,
                        record.category.value,
                        int(record.is_symlink),
                        int(record.is_large),
                        record.sha256,
                    ),
                )
                file_id = int(
                    self.connection.execute(
                        "SELECT id FROM files WHERE session_id=? AND relative_path=?",
                        (session_id, record.relative_path),
                    ).fetchone()[0]
                )
                self.connection.execute("DELETE FROM filename_warnings WHERE file_id=?", (file_id,))
                self.connection.executemany(
                    "INSERT INTO filename_warnings(file_id, code) VALUES (?, ?)",
                    ((file_id, warning) for warning in sorted(set(record.filename_warnings))),
                )
            self.connection.executemany(
                "INSERT INTO scan_errors(session_id, path, operation, message) VALUES (?, ?, ?, ?)",
                ((session_id, item.path, item.operation, item.message) for item in errors),
            )
            imported_count = int(
                self.connection.execute(
                    "SELECT COUNT(*) FROM files WHERE session_id=?", (session_id,)
                ).fetchone()[0]
            )
            error_count = int(
                self.connection.execute(
                    "SELECT COUNT(*) FROM scan_errors WHERE session_id=?", (session_id,)
                ).fetchone()[0]
            )
            self.connection.execute(
                """
                UPDATE scan_sessions
                SET last_relative_path=?, imported_count=?, error_count=?, updated_utc=?
                WHERE id=?
                """,
                (checkpoint, imported_count, error_count, utc_now(), session_id),
            )

    def set_phase(self, session_id: int, phase: str) -> None:
        if phase not in _VALID_PHASES:
            raise ValueError(f"Ungültige Indexphase: {phase}")
        with self.connection:
            self.connection.execute(
                "UPDATE scan_sessions SET phase=?, updated_utc=? WHERE id=?",
                (phase, utc_now(), session_id),
            )

    def mark_interrupted(self, session_id: int, truncated: bool = False) -> None:
        with self.connection:
            self.connection.execute(
                """
                UPDATE scan_sessions
                SET status='interrupted', truncated=?, updated_utc=?
                WHERE id=?
                """,
                (int(truncated), utc_now(), session_id),
            )

    def mark_failed(self, session_id: int, message: str) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO scan_errors(session_id, path, operation, message) VALUES (?, '', 'index', ?)",
                (session_id, message),
            )
            self.connection.execute(
                """
                UPDATE scan_sessions
                SET status='failed', error_count=(SELECT COUNT(*) FROM scan_errors WHERE session_id=?),
                    updated_utc=?
                WHERE id=?
                """,
                (session_id, utc_now(), session_id),
            )

    def hash_candidates(self, session_id: int, after_path: str | None) -> Iterator[sqlite3.Row]:
        rows = self.connection.execute(
            """
            SELECT f.id, f.relative_path, f.sha256
            FROM files AS f
            JOIN (
                SELECT size_bytes
                FROM files
                WHERE session_id=? AND is_symlink=0 AND size_bytes>0
                GROUP BY size_bytes
                HAVING COUNT(*) > 1
            ) AS candidates ON candidates.size_bytes=f.size_bytes
            WHERE f.session_id=? AND f.is_symlink=0
            ORDER BY f.relative_path COLLATE NOCASE, f.relative_path
            """,
            (session_id, session_id),
        )
        skipping = after_path is not None
        found = after_path is None
        for row in rows:
            path = str(row["relative_path"])
            if skipping:
                if path == after_path:
                    skipping = False
                    found = True
                continue
            if row["sha256"] is None:
                yield row
        if not found:
            raise ResumeCheckpointError(
                f"Hash-Wiederaufnahmepunkt fehlt: {after_path}. Reparatur oder neuer Scan erforderlich."
            )

    def update_hash_batch(
        self,
        session_id: int,
        hashes: list[tuple[str, int]],
        errors: list[ScanError],
        checkpoint: str | None,
    ) -> None:
        with self.connection:
            self.connection.executemany(
                "UPDATE files SET sha256=? WHERE id=? AND session_id=?",
                ((digest, file_id, session_id) for digest, file_id in hashes),
            )
            self.connection.executemany(
                "INSERT INTO scan_errors(session_id, path, operation, message) VALUES (?, ?, ?, ?)",
                ((session_id, item.path, item.operation, item.message) for item in errors),
            )
            self.connection.execute(
                """
                UPDATE scan_sessions
                SET last_hash_path=?, error_count=(SELECT COUNT(*) FROM scan_errors WHERE session_id=?),
                    updated_utc=?
                WHERE id=?
                """,
                (checkpoint, session_id, utc_now(), session_id),
            )

    def rebuild_duplicate_groups(self, session_id: int) -> int:
        with self.connection:
            self.connection.execute("DELETE FROM duplicate_groups WHERE session_id=?", (session_id,))
            groups = self.connection.execute(
                """
                SELECT sha256, size_bytes
                FROM files
                WHERE session_id=? AND sha256 IS NOT NULL
                GROUP BY sha256, size_bytes
                HAVING COUNT(*) > 1
                ORDER BY size_bytes DESC, sha256
                """,
                (session_id,),
            ).fetchall()
            for group in groups:
                cursor = self.connection.execute(
                    "INSERT INTO duplicate_groups(session_id, sha256, size_bytes) VALUES (?, ?, ?)",
                    (session_id, group["sha256"], group["size_bytes"]),
                )
                group_id = int(cursor.lastrowid)
                self.connection.execute(
                    """
                    INSERT INTO duplicate_members(group_id, file_id)
                    SELECT ?, id FROM files
                    WHERE session_id=? AND sha256=? AND size_bytes=?
                    """,
                    (group_id, session_id, group["sha256"], group["size_bytes"]),
                )
        return len(groups)

    def mark_complete(self, session_id: int) -> None:
        with self.connection:
            self.connection.execute(
                """
                UPDATE scan_sessions
                SET status='complete', phase='complete', finished_utc=?, updated_utc=?, truncated=0
                WHERE id=?
                """,
                (utc_now(), utc_now(), session_id),
            )

    def latest_status(self) -> IndexStatus:
        row = self.connection.execute(
            "SELECT * FROM scan_sessions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return IndexStatus(
                database=str(self.path), schema_version=self.schema_version(), session_id=None,
                root=None, status=None, phase=None, imported_count=0, error_count=0,
                duplicate_group_count=0, updated_utc=None,
            )
        duplicate_count = int(
            self.connection.execute(
                "SELECT COUNT(*) FROM duplicate_groups WHERE session_id=?", (row["id"],)
            ).fetchone()[0]
        )
        return IndexStatus(
            database=str(self.path), schema_version=self.schema_version(), session_id=int(row["id"]),
            root=str(row["root"]), status=str(row["status"]), phase=str(row["phase"]),
            imported_count=int(row["imported_count"]), error_count=int(row["error_count"]),
            duplicate_group_count=duplicate_count, updated_utc=str(row["updated_utc"]),
        )


def _iter_paths(
    root: Path,
    follow_symlinks: bool,
    checkpoint: str | None,
    errors: list[ScanError],
) -> Iterator[Path]:
    found_checkpoint = checkpoint is None

    def on_walk_error(error: OSError) -> None:
        errors.append(
            ScanError(
                path=str(getattr(error, "filename", root)), operation="walk", message=str(error)
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
            f"Scan-Wiederaufnahmepunkt fehlt: {checkpoint}. Reparatur oder neuer Scan erforderlich."
        )


def _record_for_path(path: Path, root: Path, options: IndexBuildOptions) -> FileRecord:
    stat_result = path.stat(follow_symlinks=options.follow_symlinks)
    return FileRecord(
        relative_path=path.relative_to(root).as_posix(),
        size_bytes=stat_result.st_size,
        modified_utc=datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc).isoformat(),
        suffix=path.suffix.casefold(),
        category=classify_path(path),
        filename_warnings=filename_warnings(path.name),
        is_symlink=path.is_symlink(),
        is_large=stat_result.st_size >= options.large_file_bytes,
    )


def _flush_scan_batch(
    database: IndexDatabase,
    session_id: int,
    records: list[FileRecord],
    errors: list[ScanError],
    checkpoint: str | None,
) -> None:
    if records or errors:
        database.import_batch(session_id, records, errors, checkpoint)
        records.clear()
        errors.clear()


def build_index(options: IndexBuildOptions) -> IndexBuildResult:
    if options.large_file_bytes < 0:
        raise ValueError("large_file_bytes darf nicht negativ sein")
    if options.batch_size < 1:
        raise ValueError("batch_size muss mindestens 1 sein")
    if options.max_files is not None and options.max_files < 1:
        raise ValueError("max_files muss mindestens 1 sein")

    root = options.root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"Kein Verzeichnis: {root}")
    fingerprint = _source_fingerprint(root, options)

    with IndexDatabase(options.database) as database:
        database.migrate()
        resumed = False
        row = database.resumable_session(fingerprint) if options.resume else None
        if row is None:
            session_id = database.create_session(root, options, fingerprint)
        else:
            session_id = int(row["id"])
            resumed = True
            database.set_running(session_id)

        try:
            session = database.session(session_id)
            phase = str(session["phase"])
            if phase == "scanning":
                records: list[FileRecord] = []
                errors: list[ScanError] = []
                processed_this_run = 0
                checkpoint = session["last_relative_path"]
                for path in _iter_paths(root, options.follow_symlinks, checkpoint, errors):
                    if options.max_files is not None and processed_this_run >= options.max_files:
                        _flush_scan_batch(database, session_id, records, errors, checkpoint)
                        database.mark_interrupted(session_id, truncated=True)
                        status = database.latest_status()
                        return IndexBuildResult(
                            database=status.database, session_id=session_id, status="interrupted",
                            phase="scanning", imported_count=status.imported_count,
                            error_count=status.error_count,
                            duplicate_group_count=status.duplicate_group_count,
                            resumed=resumed, schema_version=status.schema_version,
                        )
                    relative_path = path.relative_to(root).as_posix()
                    try:
                        records.append(_record_for_path(path, root, options))
                    except OSError as error:
                        errors.append(
                            ScanError(path=relative_path, operation="stat", message=str(error))
                        )
                    checkpoint = relative_path
                    processed_this_run += 1
                    if len(records) + len(errors) >= options.batch_size:
                        _flush_scan_batch(database, session_id, records, errors, checkpoint)
                _flush_scan_batch(database, session_id, records, errors, checkpoint)
                database.set_phase(session_id, "hashing" if options.hash_duplicates else "finalizing")

            session = database.session(session_id)
            if str(session["phase"]) == "hashing":
                hashes: list[tuple[str, int]] = []
                errors = []
                checkpoint = session["last_hash_path"]
                for candidate in database.hash_candidates(session_id, checkpoint):
                    relative_path = str(candidate["relative_path"])
                    try:
                        hashes.append((sha256_file(root / relative_path), int(candidate["id"])))
                    except OSError as error:
                        errors.append(
                            ScanError(path=relative_path, operation="sha256", message=str(error))
                        )
                    checkpoint = relative_path
                    if len(hashes) + len(errors) >= options.batch_size:
                        database.update_hash_batch(session_id, hashes, errors, checkpoint)
                        hashes.clear()
                        errors.clear()
                if hashes or errors:
                    database.update_hash_batch(session_id, hashes, errors, checkpoint)
                database.set_phase(session_id, "finalizing")

            if str(database.session(session_id)["phase"]) == "finalizing":
                database.rebuild_duplicate_groups(session_id)
                database.mark_complete(session_id)
        except Exception as error:
            database.mark_failed(session_id, str(error))
            raise

        status = database.latest_status()
        return IndexBuildResult(
            database=status.database, session_id=session_id, status=status.status or "failed",
            phase=status.phase or "scanning", imported_count=status.imported_count,
            error_count=status.error_count, duplicate_group_count=status.duplicate_group_count,
            resumed=resumed, schema_version=status.schema_version,
        )


def inspect_index(path: Path) -> IndexStatus:
    if not path.expanduser().exists():
        raise FileNotFoundError(f"Indexdatenbank nicht gefunden: {path.expanduser()}")
    with IndexDatabase(path) as database:
        database.migrate()
        return database.latest_status()


def _integrity_rows(connection: sqlite3.Connection, pragma: str) -> tuple[str, ...]:
    return tuple(str(row[0]) for row in connection.execute(f"PRAGMA {pragma}"))


def repair_index(path: Path, *, create_backup: bool = True, vacuum: bool = False) -> RepairResult:
    target = _normalise_database_path(path)
    if not target.exists():
        raise FileNotFoundError(f"Indexdatenbank nicht gefunden: {target}")
    backup: Path | None = None
    if create_backup:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = target.with_name(f"{target.name}.repair-backup-{timestamp}")
        source = sqlite3.connect(target)
        destination = sqlite3.connect(backup)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

    actions: list[str] = []
    with IndexDatabase(target) as database:
        before = _integrity_rows(database.connection, "quick_check")
        database.migrate()
        with database.connection:
            cursor = database.connection.execute(
                "UPDATE scan_sessions SET status='interrupted', updated_utc=? WHERE status='running'",
                (utc_now(),),
            )
            interrupted = int(cursor.rowcount)
        if interrupted:
            actions.append(f"{interrupted} laufende Sitzung(en) als unterbrochen markiert")

        session_ids = [
            int(row[0])
            for row in database.connection.execute(
                "SELECT id FROM scan_sessions WHERE imported_count > 0"
            )
        ]
        rebuilt = 0
        for session_id in session_ids:
            database.rebuild_duplicate_groups(session_id)
            rebuilt += 1
        if rebuilt:
            actions.append(f"Duplikatgruppen für {rebuilt} Sitzung(en) neu aufgebaut")

        with database.connection:
            database.connection.execute("REINDEX")
            database.connection.execute("ANALYZE")
        actions.extend(("Indizes neu aufgebaut", "Abfragestatistik aktualisiert"))
        if vacuum:
            database.connection.execute("VACUUM")
            actions.append("Datenbank komprimiert")

        foreign_key_errors = len(database.connection.execute("PRAGMA foreign_key_check").fetchall())
        after = _integrity_rows(database.connection, "integrity_check")

    successful = after == ("ok",) and foreign_key_errors == 0
    return RepairResult(
        database=str(target), backup=str(backup) if backup else None,
        before_integrity=before, after_integrity=after,
        foreign_key_errors=foreign_key_errors, interrupted_sessions=interrupted,
        rebuilt_duplicate_sessions=rebuilt, actions=tuple(actions), successful=successful,
    )
