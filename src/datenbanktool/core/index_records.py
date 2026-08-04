from __future__ import annotations

import sqlite3
from typing import Iterator

from datenbanktool.core.index_types import ResumeCheckpointError, utc_now
from datenbanktool.core.models import FileRecord, ScanError


class IndexRecordMixin:
    connection: sqlite3.Connection

    def _upsert_record(
        self,
        session_id: int,
        record: FileRecord,
        source_file_id: int | None,
    ) -> int:
        self.connection.execute(
            """
            INSERT INTO files(
                session_id, relative_path, size_bytes, modified_utc, suffix, category,
                is_symlink, is_large, sha256, source_file_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id, relative_path) DO UPDATE SET
                size_bytes=excluded.size_bytes,
                modified_utc=excluded.modified_utc,
                suffix=excluded.suffix,
                category=excluded.category,
                is_symlink=excluded.is_symlink,
                is_large=excluded.is_large,
                sha256=COALESCE(excluded.sha256, files.sha256),
                source_file_id=excluded.source_file_id
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
                source_file_id,
            ),
        )
        file_id = int(
            self.connection.execute(
                "SELECT id FROM files WHERE session_id=? AND relative_path=?",
                (session_id, record.relative_path),
            ).fetchone()[0]
        )
        self.connection.execute(
            """
            INSERT INTO file_identity(file_id, device_id, inode, modified_ns)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(file_id) DO UPDATE SET
                device_id=excluded.device_id, inode=excluded.inode, modified_ns=excluded.modified_ns
            """,
            (file_id, record.device_id, record.inode, record.modified_ns),
        )
        self.connection.execute("DELETE FROM filename_warnings WHERE file_id=?", (file_id,))
        self.connection.executemany(
            "INSERT INTO filename_warnings(file_id, code) VALUES (?, ?)",
            ((file_id, warning) for warning in sorted(set(record.filename_warnings))),
        )
        return file_id

    def _update_session_counts(self, session_id: int, checkpoint: str | None) -> None:
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

    def import_batch(
        self,
        session_id: int,
        records: list[FileRecord],
        errors: list[ScanError],
        checkpoint: str | None,
    ) -> None:
        with self.connection:
            for record in records:
                self._upsert_record(session_id, record, None)
            self.connection.executemany(
                "INSERT INTO scan_errors(session_id, path, operation, message) VALUES (?, ?, ?, ?)",
                ((session_id, item.path, item.operation, item.message) for item in errors),
            )
            self._update_session_counts(session_id, checkpoint)

    def import_incremental_batch(
        self,
        session_id: int,
        items: list[tuple[FileRecord, int | None, str, str | None]],
        errors: list[ScanError],
        checkpoint: str | None,
    ) -> None:
        with self.connection:
            for record, source_file_id, change_type, old_path in items:
                new_file_id = self._upsert_record(session_id, record, source_file_id)
                self.connection.execute(
                    """
                    INSERT INTO file_changes(
                        session_id, change_type, old_file_id, new_file_id, old_path, new_path, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, '{}')
                    ON CONFLICT(session_id, new_path) DO UPDATE SET
                        change_type=excluded.change_type,
                        old_file_id=excluded.old_file_id,
                        new_file_id=excluded.new_file_id,
                        old_path=excluded.old_path,
                        details_json=excluded.details_json
                    """,
                    (
                        session_id,
                        change_type,
                        source_file_id,
                        new_file_id,
                        old_path,
                        record.relative_path,
                    ),
                )
            self.connection.executemany(
                "INSERT INTO scan_errors(session_id, path, operation, message) VALUES (?, ?, ?, ?)",
                ((session_id, item.path, item.operation, item.message) for item in errors),
            )
            self._update_session_counts(session_id, checkpoint)

    def hash_candidates(self, session_id: int, after_path: str | None) -> Iterator[sqlite3.Row]:
        rows = self.connection.execute(
            """
            SELECT f.id, f.relative_path, f.sha256
            FROM files AS f
            JOIN (
                SELECT size_bytes FROM files
                WHERE session_id=? AND is_symlink=0 AND size_bytes>0
                GROUP BY size_bytes HAVING COUNT(*)>1
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
                    updated_utc=? WHERE id=?
                """,
                (checkpoint, session_id, utc_now(), session_id),
            )

    def rebuild_duplicate_groups(self, session_id: int) -> int:
        with self.connection:
            self.connection.execute("DELETE FROM duplicate_groups WHERE session_id=?", (session_id,))
            groups = self.connection.execute(
                """
                SELECT sha256, size_bytes FROM files
                WHERE session_id=? AND sha256 IS NOT NULL
                GROUP BY sha256, size_bytes HAVING COUNT(*)>1
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
                    SELECT ?, id FROM files WHERE session_id=? AND sha256=? AND size_bytes=?
                    """,
                    (group_id, session_id, group["sha256"], group["size_bytes"]),
                )
        return len(groups)
