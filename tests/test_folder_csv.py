from __future__ import annotations

import csv
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from datenbanktool.cli import main
from datenbanktool.core.folder_csv import export_folder_csv
from datenbanktool.core.folders import (
    FolderFilter,
    analyse_folders,
    paginate_folder_page,
)
from datenbanktool.core.index_database import IndexBuildOptions, build_index


class FolderCsvTests(unittest.TestCase):
    def _build_many_folders(self, directory: str) -> Path:
        root = Path(directory) / "data"
        for index in range(30):
            folder = root / f"ordner-{index:02d}"
            folder.mkdir(parents=True)
            (folder / f"datei-{index:02d}.txt").write_bytes(
                bytes([index % 251]) * (index + 1)
            )
        database = Path(directory) / "index.sqlite3"
        build_index(IndexBuildOptions(root=root, database=database))
        return database

    def test_all_rows_can_be_paginated_without_reanalysis(self) -> None:
        with TemporaryDirectory() as directory:
            database = self._build_many_folders(directory)
            complete = analyse_folders(
                database,
                filters=FolderFilter(page=3, page_size=5, sort_by="path", descending=False),
                all_rows=True,
            )
            self.assertEqual(len(complete.rows), complete.total_rows)
            self.assertGreater(complete.total_rows, 25)
            page = paginate_folder_page(complete, page=3, page_size=5)
            self.assertEqual(len(page.rows), 5)
            self.assertEqual(page.page, 3)
            self.assertGreater(page.total_pages, 1)

    def test_csv_has_bom_stable_columns_and_largest_files(self) -> None:
        with TemporaryDirectory() as directory:
            database = self._build_many_folders(directory)
            page = analyse_folders(
                database,
                filters=FolderFilter(top_files=2, sort_by="path", descending=False),
                all_rows=True,
            )
            target = Path(directory) / "folders.csv"
            export_folder_csv(page, target)
            self.assertTrue(target.read_bytes().startswith(b"\xef\xbb\xbf"))
            with target.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.reader(handle, delimiter=";"))
            self.assertEqual(len(rows) - 1, page.total_rows)
            self.assertIn("Ampelbegründung", rows[0])
            self.assertIn("Gesamtgröße Byte", rows[0])
            self.assertIn("Platzfresser 1 Pfad", rows[0])
            self.assertIn("Platzfresser 1 Byte", rows[0])
            with self.assertRaises(FileExistsError):
                export_folder_csv(page, target)

    def test_cli_all_pages_exports_every_matching_folder(self) -> None:
        with TemporaryDirectory() as directory:
            database = self._build_many_folders(directory)
            target = Path(directory) / "folders.csv"
            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                code = main(
                    [
                        "--no-hints",
                        "index",
                        "folders",
                        str(database),
                        "--page-size",
                        "5",
                        "--sort",
                        "path",
                        "--no-descending",
                        "--csv",
                        str(target),
                        "--all-pages",
                    ]
                )
            self.assertEqual(code, 0)
            self.assertIn("Exportumfang: alle", output.getvalue())
            with target.open("r", encoding="utf-8-sig", newline="") as handle:
                row_count = max(0, sum(1 for _ in csv.reader(handle, delimiter=";")) - 1)
            complete = analyse_folders(
                database,
                filters=FolderFilter(sort_by="path", descending=False),
                all_rows=True,
            )
            self.assertEqual(row_count, complete.total_rows)

    def test_all_pages_requires_an_export(self) -> None:
        with TemporaryDirectory() as directory:
            database = self._build_many_folders(directory)
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(
                    main(
                        [
                            "index",
                            "folders",
                            str(database),
                            "--all-pages",
                        ]
                    ),
                    2,
                )


if __name__ == "__main__":
    unittest.main()
