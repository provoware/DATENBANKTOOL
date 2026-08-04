from __future__ import annotations

import sqlite3

from datenbanktool.core.index_types import SCHEMA_VERSION, UnsupportedSchemaError, utc_now


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
            phase TEXT NOT NULL,
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
    columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(scan_sessions)")}
    if "source_fingerprint" not in columns:
        connection.execute("ALTER TABLE scan_sessions ADD COLUMN source_fingerprint TEXT")
    connection.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_sessions_status_updated ON scan_sessions(status, updated_utc DESC);
        CREATE INDEX IF NOT EXISTS idx_sessions_fingerprint ON scan_sessions(source_fingerprint, id DESC);
        CREATE INDEX IF NOT EXISTS idx_files_session_path ON files(session_id, relative_path COLLATE NOCASE);
        CREATE INDEX IF NOT EXISTS idx_files_session_category ON files(session_id, category);
        CREATE INDEX IF NOT EXISTS idx_files_session_size ON files(session_id, size_bytes);
        CREATE INDEX IF NOT EXISTS idx_files_session_sha ON files(session_id, sha256, size_bytes);
        CREATE INDEX IF NOT EXISTS idx_warnings_code ON filename_warnings(code, file_id);
        CREATE INDEX IF NOT EXISTS idx_errors_session ON scan_errors(session_id, id);
        CREATE INDEX IF NOT EXISTS idx_duplicate_groups_session ON duplicate_groups(session_id, id);
        CREATE INDEX IF NOT EXISTS idx_duplicate_members_file ON duplicate_members(file_id, group_id);
        """
    )


def _migration_3(connection: sqlite3.Connection) -> None:
    session_columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(scan_sessions)")}
    if "parent_session_id" not in session_columns:
        connection.execute(
            "ALTER TABLE scan_sessions ADD COLUMN parent_session_id INTEGER REFERENCES scan_sessions(id)"
        )
    if "scan_mode" not in session_columns:
        connection.execute("ALTER TABLE scan_sessions ADD COLUMN scan_mode TEXT NOT NULL DEFAULT 'full'")
    if "incremental_stage" not in session_columns:
        connection.execute(
            "ALTER TABLE scan_sessions ADD COLUMN incremental_stage TEXT NOT NULL DEFAULT 'scan'"
        )
    file_columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(files)")}
    if "source_file_id" not in file_columns:
        connection.execute("ALTER TABLE files ADD COLUMN source_file_id INTEGER REFERENCES files(id)")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS file_identity (
            file_id INTEGER PRIMARY KEY REFERENCES files(id) ON DELETE CASCADE,
            device_id INTEGER NOT NULL DEFAULT 0,
            inode INTEGER NOT NULL DEFAULT 0,
            modified_ns INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS file_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE,
            change_type TEXT NOT NULL CHECK (change_type IN ('added','modified','moved','removed','unchanged')),
            old_file_id INTEGER REFERENCES files(id),
            new_file_id INTEGER REFERENCES files(id),
            old_path TEXT,
            new_path TEXT,
            details_json TEXT NOT NULL DEFAULT '{}',
            UNIQUE(session_id, new_path)
        );
        CREATE TABLE IF NOT EXISTS progress_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES scan_sessions(id) ON DELETE CASCADE,
            event_utc TEXT NOT NULL,
            phase TEXT NOT NULL,
            kind TEXT NOT NULL,
            current_value INTEGER,
            total_value INTEGER,
            message TEXT NOT NULL,
            details_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_parent ON scan_sessions(parent_session_id, id);
        CREATE INDEX IF NOT EXISTS idx_sessions_mode ON scan_sessions(scan_mode, id DESC);
        CREATE INDEX IF NOT EXISTS idx_files_source ON files(source_file_id);
        CREATE INDEX IF NOT EXISTS idx_identity_inode ON file_identity(device_id, inode, file_id);
        CREATE INDEX IF NOT EXISTS idx_changes_session_type ON file_changes(session_id, change_type);
        CREATE INDEX IF NOT EXISTS idx_changes_old_file ON file_changes(old_file_id);
        CREATE INDEX IF NOT EXISTS idx_progress_session_id ON progress_events(session_id, id);
        """
    )


_MIGRATIONS = {
    1: ("Initialer transaktionaler Dateiindex", _migration_1),
    2: ("Wiederaufnahme-Fingerabdruck und Berichtindizes", _migration_2),
    3: ("Inkrementeller Re-Scan, Dateiidentitäten, Änderungen und Fortschrittsereignisse", _migration_3),
}


def migrate_connection(connection: sqlite3.Connection) -> int:
    current = int(connection.execute("PRAGMA user_version").fetchone()[0])
    if current > SCHEMA_VERSION:
        raise UnsupportedSchemaError(
            f"Datenbankschema {current} ist neuer als unterstützte Version {SCHEMA_VERSION}."
        )
    for version in range(current + 1, SCHEMA_VERSION + 1):
        description, migration = _MIGRATIONS[version]
        with connection:
            migration(connection)
            connection.execute(
                "INSERT OR REPLACE INTO schema_migrations(version, applied_utc, description) VALUES (?, ?, ?)",
                (version, utc_now(), description),
            )
            connection.execute(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES ('schema_version', ?)",
                (str(version),),
            )
            connection.execute(f"PRAGMA user_version = {version}")
    with connection:
        connection.execute(
            "INSERT OR REPLACE INTO metadata(key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
    return int(connection.execute("PRAGMA user_version").fetchone()[0])
