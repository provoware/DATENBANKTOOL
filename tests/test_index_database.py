from __future__ import annotations

import csv
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from datenbanktool.core.index_database import (
    SCHEMA_VERSION,
    IndexBuildOptions,
    IndexDatabase,
    _migration_1,
    build_index,
    inspect_index,
    repair_index,
)
from datenbanktool.core.reports import ReportFilter, export_reports


class IndexDatabaseTests(unittest.TestCase):
    def test_schema_is_created_at_current_version(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "index.sqlite3"
            with IndexDatabase(database_path) as database:
                self.assertEqual(database.migrate(), SCHEMA_VERSION)
                self.assertEqual(database.schema_version(), SCHEMA_VERSION)
                tables = {
                    row[0]
                    for row in database.connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
            self.assertTrue({"files", "scan_sessions", "schema_migrations"} <= tables)

    def test_v1_database_is_migrated_to_v2(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "legacy.sqlite3"
            connection = sqlite3.connect(database_path)
            _migration_1(connection)
            connection.execute(
                "INSERT INTO schema_migrations(version, applied_utc, description) "
                "VALUES (1, 'x', 'legacy')"
            )
            connection.execute("PRAGMA user_version=1")
            connection.commit()
            connection.close()

            with IndexDatabase(database_path) as database:
                self.assertEqual(database.migrate(), 2)
                columns = {
                    row[1]
                    for row in database.connection.execute("PRAGMA table_info(scan_sessions)")
                }
                migrations = [
                    row[0]
                    for row in database.connection.execute(
                        "SELECT version FROM schema_migrations ORDER BY version"
                    )
                ]
            self.assertIn("source_fingerprint", columns)
            self.assertEqual(migrations, [1, 2])

    def test_batch_import_can_resume_without_duplicates(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            for name, content in (
                ("a.txt", "gleich"),
                ("b.txt", "gleich"),
                ("c.wav", "audio"),
                ("d.py", "print('x')"),
            ):
                (root / name).write_text(content, encoding="utf-8")
            database_path = Path(directory) / "index.sqlite3"

            interrupted = build_index(
                IndexBuildOptions(
                    root=root,
                    database=database_path,
                    hash_duplicates=True,
                    batch_size=1,
                    max_files=2,
                )
            )
            self.assertEqual(interrupted.status, "interrupted")
            self.assertEqual(interrupted.imported_count, 2)

            completed = build_index(
                IndexBuildOptions(
                    root=root,
                    database=database_path,
                    hash_duplicates=True,
                    batch_size=2,
                    resume=True,
                )
            )
            self.assertTrue(completed.resumed)
            self.assertEqual(completed.status, "complete")
            self.assertEqual(completed.imported_count, 4)
            self.assertEqual(completed.duplicate_group_count, 1)

            with closing(sqlite3.connect(database_path)) as connection:
                file_count = connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]
                unique_count = connection.execute(
                    "SELECT COUNT(DISTINCT relative_path) FROM files"
                ).fetchone()[0]
            self.assertEqual(file_count, 4)
            self.assertEqual(unique_count, 4)

    def test_status_reports_latest_session(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            (root / "note.txt").write_text("x", encoding="utf-8")
            database_path = Path(directory) / "index.sqlite3"
            build_index(IndexBuildOptions(root=root, database=database_path))
            status = inspect_index(database_path)
            self.assertEqual(status.status, "complete")
            self.assertEqual(status.imported_count, 1)
            self.assertEqual(status.schema_version, SCHEMA_VERSION)

    def test_repair_marks_running_sessions_and_creates_backup(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            (root / "a.txt").write_text("a", encoding="utf-8")
            (root / "b.txt").write_text("b", encoding="utf-8")
            database_path = Path(directory) / "index.sqlite3"
            result = build_index(
                IndexBuildOptions(root=root, database=database_path, max_files=1)
            )
            with closing(sqlite3.connect(database_path)) as connection:
                connection.execute(
                    "UPDATE scan_sessions SET status='running' WHERE id=?", (result.session_id,)
                )
                connection.commit()

            repaired = repair_index(database_path)
            self.assertTrue(repaired.successful)
            self.assertEqual(repaired.interrupted_sessions, 1)
            self.assertIsNotNone(repaired.backup)
            backup_path = Path(repaired.backup or "")
            self.assertTrue(backup_path.exists())
            with closing(sqlite3.connect(backup_path)) as backup_connection:
                self.assertEqual(backup_connection.execute("PRAGMA quick_check").fetchone()[0], "ok")
            with closing(sqlite3.connect(database_path)) as connection:
                status = connection.execute(
                    "SELECT status FROM scan_sessions WHERE id=?", (result.session_id,)
                ).fetchone()[0]
            self.assertEqual(status, "interrupted")

    def test_filtered_csv_and_html_reports(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            (root / "bad?.wav").write_bytes(b"same-audio")
            (root / "clean.wav").write_bytes(b"same-audio")
            (root / "note.txt").write_text("same-audio", encoding="utf-8")
            database_path = Path(directory) / "index.sqlite3"
            build_index(
                IndexBuildOptions(root=root, database=database_path, hash_duplicates=True)
            )
            csv_path = Path(directory) / "report.csv"
            html_path = Path(directory) / "report.html"
            report = export_reports(
                database_path,
                csv_path=csv_path,
                html_path=html_path,
                filters=ReportFilter(
                    categories=("audio",), naming_warning_only=True, duplicate_only=True
                ),
            )
            self.assertEqual(report.row_count, 1)
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["category"], "audio")
            self.assertIn("cross-platform-risk-character", rows[0]["filename_warnings"])
            html_text = html_path.read_text(encoding="utf-8")
            self.assertIn("Interaktive Tabellenfilter", html_text)
            self.assertIn("bad?.wav", html_text)
            self.assertNotIn("note.txt", html_text)

    def test_multi_report_preflight_leaves_no_partial_output(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            (root / "a.txt").write_text("a", encoding="utf-8")
            database_path = Path(directory) / "index.sqlite3"
            build_index(IndexBuildOptions(root=root, database=database_path))
            csv_path = Path(directory) / "new.csv"
            html_path = Path(directory) / "existing.html"
            html_path.write_text("bestehend", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                export_reports(
                    database_path,
                    csv_path=csv_path,
                    html_path=html_path,
                )
            self.assertFalse(csv_path.exists())
            self.assertEqual(html_path.read_text(encoding="utf-8"), "bestehend")

    def test_report_does_not_overwrite_without_permission(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            (root / "a.txt").write_text("a", encoding="utf-8")
            database_path = Path(directory) / "index.sqlite3"
            build_index(IndexBuildOptions(root=root, database=database_path))
            csv_path = Path(directory) / "report.csv"
            export_reports(database_path, csv_path=csv_path)
            with self.assertRaises(FileExistsError):
                export_reports(database_path, csv_path=csv_path)


if __name__ == "__main__":
    unittest.main()
