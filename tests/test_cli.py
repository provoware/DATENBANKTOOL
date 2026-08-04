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


if __name__ == "__main__":
    unittest.main()
