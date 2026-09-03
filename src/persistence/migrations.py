from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone


class MigrationError(RuntimeError):
    """Raised when a database migration cannot be applied safely."""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    statements: tuple[str, ...]

    @property
    def checksum(self) -> str:
        payload = "\n-- statement --\n".join(self.statements).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class MigrationReport:
    from_version: int
    to_version: int
    applied_versions: tuple[int, ...]


MIGRATIONS = (
    Migration(
        version=1,
        name="initial_core_schema",
        statements=(
            """
            CREATE TABLE entries (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL CHECK(length(kind) BETWEEN 1 AND 64),
                title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 500),
                content TEXT NOT NULL DEFAULT '',
                parent_id TEXT REFERENCES entries(id) ON DELETE SET NULL,
                favorite INTEGER NOT NULL DEFAULT 0 CHECK(favorite IN (0, 1)),
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(length(status) BETWEEN 1 AND 32),
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK(parent_id IS NULL OR parent_id <> id)
            )
            """,
            "CREATE INDEX idx_entries_kind ON entries(kind)",
            "CREATE INDEX idx_entries_parent ON entries(parent_id)",
            "CREATE INDEX idx_entries_updated ON entries(updated_at DESC)",
            """
            CREATE TABLE tags (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE
                    CHECK(length(name) BETWEEN 1 AND 120)
            )
            """,
            """
            CREATE TABLE entry_tags (
                entry_id TEXT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
                tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (entry_id, tag_id)
            )
            """,
            "CREATE INDEX idx_entry_tags_tag ON entry_tags(tag_id)",
            """
            CREATE TABLE app_settings (
                key TEXT PRIMARY KEY CHECK(length(key) BETWEEN 1 AND 120),
                value_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
        ),
    ),
)

CURRENT_SCHEMA_VERSION = MIGRATIONS[-1].version


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ensure_migration_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            checksum TEXT NOT NULL
        )
        """
    )


def _known_by_version() -> dict[int, Migration]:
    return {migration.version: migration for migration in MIGRATIONS}


def _validate_existing(connection: sqlite3.Connection) -> int:
    known = _known_by_version()
    rows = connection.execute(
        "SELECT version, name, checksum FROM schema_migrations ORDER BY version"
    ).fetchall()

    current = 0
    for row in rows:
        version = int(row["version"])
        migration = known.get(version)
        if migration is None:
            raise MigrationError(
                f"Unbekannte Migration {version}. "
                "Die Datenbank ist neuer als diese Programmversion."
            )
        if row["name"] != migration.name or row["checksum"] != migration.checksum:
            raise MigrationError(
                f"Migration {version} stimmt nicht mehr mit dem geprüften Schema überein."
            )
        if version != current + 1:
            raise MigrationError("Die Migrationshistorie enthält eine Versionslücke.")
        current = version

    pragma_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    if pragma_version != current:
        raise MigrationError(
            "Schema-Metadaten widersprechen sich: "
            f"user_version={pragma_version}, Historie={current}."
        )
    if current > CURRENT_SCHEMA_VERSION:
        raise MigrationError("Die Datenbank ist neuer als diese Programmversion.")
    return current


def run_migrations(connection: sqlite3.Connection) -> MigrationReport:
    _ensure_migration_table(connection)
    start_version = _validate_existing(connection)
    applied: list[int] = []

    for migration in MIGRATIONS:
        if migration.version <= start_version:
            continue

        try:
            connection.execute("BEGIN IMMEDIATE")
            for statement in migration.statements:
                connection.execute(statement)
            connection.execute(
                """
                INSERT INTO schema_migrations(version, name, applied_at, checksum)
                VALUES (?, ?, ?, ?)
                """,
                (
                    migration.version,
                    migration.name,
                    _utc_now(),
                    migration.checksum,
                ),
            )
            connection.execute(f"PRAGMA user_version = {migration.version}")
            connection.commit()
        except Exception as exc:
            connection.rollback()
            raise MigrationError(
                f"Migration {migration.version} ({migration.name}) ist fehlgeschlagen."
            ) from exc

        applied.append(migration.version)

    end_version = _validate_existing(connection)
    return MigrationReport(
        from_version=start_version,
        to_version=end_version,
        applied_versions=tuple(applied),
    )
