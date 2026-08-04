import contextlib
import io
from pathlib import Path
import sqlite3
import tempfile
import unittest

from datenbanktool.cli import main
from datenbanktool.core import DatabaseError, list_tables, summarize


class DatabaseToolTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary_directory.name) / "sample.sqlite"
        with sqlite3.connect(self.database) as connection:
            connection.execute("CREATE TABLE person (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_summary_and_tables(self) -> None:
        self.assertEqual(summarize(str(self.database))["table_count"], 1)
        self.assertEqual(
            list_tables(str(self.database))[0]["columns"][1],
            {"name": "name", "type": "TEXT", "required": True, "primary_key": False},
        )

    def test_invalid_input_is_rejected(self) -> None:
        invalid = Path(self.temporary_directory.name) / "invalid.txt"
        invalid.write_text("keine Datenbank", encoding="utf-8")
        with self.assertRaisesRegex(DatabaseError, "keine gültige SQLite-Datenbank"):
            summarize(str(invalid))

    def test_json_output_and_error_output(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(["--json", "summary", str(self.database)])
        self.assertEqual(exit_code, 0)
        self.assertIn('"table_count": 1', output.getvalue())

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(["--json", "tables", "fehlt.sqlite"])
        self.assertEqual(exit_code, 2)
        self.assertIn('"error":', output.getvalue())
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sqlite3
import unittest

from datenbanktool.cli import main
from datenbanktool.core.incremental import IncrementalScanOptions, incremental_rescan
from datenbanktool.core.index_admin import backup_index, list_sessions, restore_index
from datenbanktool.core.index_database import IndexBuildOptions, IndexDatabase, build_index


class AdminAndCliTests(unittest.TestCase):
    def test_sessions_backup_and_restore(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            db = Path(directory) / "index.sqlite3"
            (root / "a.txt").write_text("a", encoding="utf-8")
            first = build_index(IndexBuildOptions(root=root, database=db))
            backup = backup_index(db)
            self.assertEqual(backup.integrity, ("ok",))
            (root / "b.txt").write_text("b", encoding="utf-8")
            second = incremental_rescan(IncrementalScanOptions(root=root, database=db))
            self.assertGreater(second.session_id, first.session_id)
            self.assertEqual(len(list_sessions(db)), 2)
            restored = restore_index(db, Path(backup.backup))
            self.assertTrue(restored.successful)
            self.assertIsNotNone(restored.safety_backup)
            sessions = list_sessions(db)
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0].session_id, first.session_id)

    def test_restore_rejects_corrupt_backup_without_changing_target(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            db = Path(directory) / "index.sqlite3"
            (root / "a.txt").write_text("a", encoding="utf-8")
            result = build_index(IndexBuildOptions(root=root, database=db))
            corrupt = Path(directory) / "bad.sqlite3"
            corrupt.write_bytes(b"not sqlite")
            with self.assertRaises(sqlite3.DatabaseError):
                restore_index(db, corrupt)
            with IndexDatabase(db) as index:
                self.assertEqual(index.latest_status().session_id, result.session_id)

    def test_cli_rescan_sessions_backup_restore(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            db = Path(directory) / "index.sqlite3"
            backup = Path(directory) / "backup.sqlite3"
            (root / "a.txt").write_text("a", encoding="utf-8")
            stdout = StringIO()
            stderr = StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(
                    main(["index", "build", str(root), "--database", str(db), "--progress", "quiet"]),
                    0,
                )
            (root / "b.txt").write_text("b", encoding="utf-8")
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(
                    main(["index", "rescan", str(root), "--database", str(db), "--progress", "quiet"]),
                    0,
                )
            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                self.assertEqual(main(["index", "sessions", str(db), "--json"]), 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(len(payload), 2)
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(
                    main(["index", "backup", str(db), "--output", str(backup)]),
                    0,
                )
                self.assertEqual(
                    main(["index", "restore", str(db), "--backup", str(backup)]),
                    0,
                )

    def test_report_command_still_works(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            db = Path(directory) / "index.sqlite3"
            html = Path(directory) / "report.html"
            csv = Path(directory) / "report.csv"
            (root / " bad?.txt").write_text("x", encoding="utf-8")
            build_index(IndexBuildOptions(root=root, database=db))
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                code = main(
                    [
                        "report", str(db), "--html", str(html), "--csv", str(csv),
                        "--name-warning-only",
                    ]
                )
            self.assertEqual(code, 0)
            self.assertIn("DATENBANKTOOL-Bericht", html.read_text(encoding="utf-8"))
            self.assertTrue(csv.read_bytes().startswith(b"\xef\xbb\xbf"))


if __name__ == "__main__":
    unittest.main()

class BackupRestoreEdgeTests(unittest.TestCase):
    def test_backup_does_not_overwrite_without_permission(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            db = Path(directory) / "index.sqlite3"
            target = Path(directory) / "fixed.sqlite3"
            (root / "a.txt").write_text("a", encoding="utf-8")
            build_index(IndexBuildOptions(root=root, database=db))
            backup_index(db, target)
            with self.assertRaises(FileExistsError):
                backup_index(db, target)
            backup_index(db, target, overwrite=True)

    def test_sessions_filters_status_and_root(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            other = Path(directory) / "other"
            other.mkdir()
            db = Path(directory) / "index.sqlite3"
            (root / "a.txt").write_text("a", encoding="utf-8")
            (other / "b.txt").write_text("b", encoding="utf-8")
            build_index(IndexBuildOptions(root=root, database=db))
            build_index(IndexBuildOptions(root=other, database=db))
            filtered = list_sessions(db, status="complete", root=root)
            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0].root, str(root.resolve()))
