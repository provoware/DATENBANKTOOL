from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from datenbanktool.cli import main


class CliTests(unittest.TestCase):
    def test_index_report_and_status_commands(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            (root / "a.txt").write_text("gleich", encoding="utf-8")
            (root / "b.txt").write_text("gleich", encoding="utf-8")
            database = Path(directory) / "index.sqlite3"
            csv_path = Path(directory) / "report.csv"
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(
                    main(
                        [
                            "index",
                            "build",
                            str(root),
                            "--database",
                            str(database),
                            "--hash-duplicates",
                            "--batch-size",
                            "1",
                        ]
                    ),
                    0,
                )
                self.assertEqual(main(["index", "status", str(database)]), 0)
                self.assertEqual(
                    main(
                        [
                            "report",
                            str(database),
                            "--csv",
                            str(csv_path),
                            "--duplicates-only",
                        ]
                    ),
                    0,
                )
            self.assertTrue(csv_path.exists())
            self.assertIn("Status: complete", output.getvalue())

    def test_report_requires_output_target(self) -> None:
        errors = StringIO()
        with redirect_stderr(errors):
            code = main(["report", "missing.sqlite3"])
        self.assertEqual(code, 2)
        self.assertIn("Fehler:", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
