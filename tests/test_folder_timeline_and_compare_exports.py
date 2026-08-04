from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from datenbanktool.cli import main
from datenbanktool.core.folder_timeline import (
    FolderTimelineOptions,
    build_folder_timeline,
)
from datenbanktool.core.folder_timeline_exports import export_folder_timeline
from datenbanktool.core.index_database import IndexBuildOptions, build_index
from datenbanktool.core.incremental import IncrementalScanOptions, incremental_rescan


class FolderTimelineAndCompleteExportTests(unittest.TestCase):
    def _create_three_scans(self, directory: str):
        root = Path(directory) / "data"
        (root / "music").mkdir(parents=True)
        (root / "music" / "a.bin").write_bytes(b"a" * 10)
        database = Path(directory) / "index.sqlite3"
        first = build_index(IndexBuildOptions(root=root, database=database))

        (root / "music" / "a.bin").write_bytes(b"a" * 30)
        (root / "music" / "b.bin").write_bytes(b"b" * 5)
        second = incremental_rescan(
            IncrementalScanOptions(root=root, database=database)
        )

        (root / "music" / "a.bin").unlink()
        third = incremental_rescan(
            IncrementalScanOptions(root=root, database=database)
        )
        return root, database, first, second, third

    def _create_many_changes(self, directory: str):
        root = Path(directory) / "many"
        root.mkdir()
        for index in range(8):
            folder = root / f"folder-{index:02d}"
            folder.mkdir()
            (folder / "item.bin").write_bytes(b"x" * (index + 1))
        database = Path(directory) / "many.sqlite3"
        first = build_index(IndexBuildOptions(root=root, database=database))
        for index in range(8):
            (root / f"folder-{index:02d}" / "item.bin").write_bytes(
                b"y" * (index + 20)
            )
        second = incremental_rescan(
            IncrementalScanOptions(root=root, database=database)
        )
        return database, first, second

    def test_timeline_tracks_recursive_size_and_file_count_read_only(self) -> None:
        with TemporaryDirectory() as directory:
            _, database, first, second, third = self._create_three_scans(directory)
            before = database.read_bytes()
            timeline = build_folder_timeline(
                database,
                options=FolderTimelineOptions(folder="music"),
            )
            self.assertEqual(database.read_bytes(), before)
            self.assertEqual(
                [point.session_id for point in timeline.points],
                [first.session_id, second.session_id, third.session_id],
            )
            self.assertEqual(
                [point.file_count for point in timeline.points],
                [1, 2, 1],
            )
            self.assertEqual(
                [point.size_bytes for point in timeline.points],
                [10, 35, 5],
            )
            self.assertEqual(timeline.points[1].status, "grown")
            self.assertEqual(timeline.points[2].status, "shrunk")
            self.assertEqual(timeline.net_file_delta, 0)
            self.assertEqual(timeline.net_size_delta_bytes, -5)

    def test_timeline_exports_json_csv_html_and_cli(self) -> None:
        with TemporaryDirectory() as directory:
            _, database, _, _, _ = self._create_three_scans(directory)
            timeline = build_folder_timeline(
                database,
                options=FolderTimelineOptions(folder="music"),
            )
            json_path = Path(directory) / "timeline.json"
            csv_path = Path(directory) / "timeline.csv"
            html_path = Path(directory) / "timeline.html"
            exported = export_folder_timeline(
                timeline,
                json_path=json_path,
                csv_path=csv_path,
                html_path=html_path,
            )
            self.assertEqual(exported.row_count, 3)
            self.assertEqual(
                len(json.loads(json_path.read_text(encoding="utf-8"))["points"]),
                3,
            )
            self.assertTrue(csv_path.read_bytes().startswith(b"\xef\xbb\xbf"))
            html_text = html_path.read_text(encoding="utf-8")
            self.assertIn("Ordner-Zeitreihe", html_text)
            self.assertEqual(html_text.count("<svg"), 2)
            self.assertIn("Größenverlauf", html_text)
            self.assertIn("Dateizahlverlauf", html_text)
            self.assertIn('role="img"', html_text)
            self.assertIn('aria-labelledby="size-chart-title size-chart-description"', html_text)
            self.assertIn("<desc id=\"files-chart-description\">", html_text)
            self.assertIn('tabindex="0"', html_text)
            self.assertIn("Vollständige Zeitreihenwerte", html_text)
            self.assertNotIn("<script", html_text.casefold())
            self.assertNotIn("https://", html_text.casefold())
            self.assertNotIn("http://", html_text.casefold())

            cli_json = Path(directory) / "cli-timeline.json"
            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                code = main(
                    [
                        "index",
                        "folder-timeline",
                        str(database),
                        "music",
                        "--json",
                        str(cli_json),
                    ]
                )
            self.assertEqual(code, 0)
            self.assertIn("Ordner-Zeitreihe:", output.getvalue())
            self.assertEqual(
                len(json.loads(cli_json.read_text(encoding="utf-8"))["points"]),
                3,
            )

    def test_timeline_rejects_unsafe_folder_and_requires_two_scans(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "single"
            root.mkdir()
            (root / "x.txt").write_text("x", encoding="utf-8")
            database = Path(directory) / "single.sqlite3"
            build_index(IndexBuildOptions(root=root, database=database))
            with self.assertRaisesRegex(ValueError, "mindestens zwei"):
                build_folder_timeline(database)
            with self.assertRaisesRegex(ValueError, "relativ"):
                build_folder_timeline(
                    database,
                    options=FolderTimelineOptions(folder="../privat"),
                )

    def test_folder_compare_all_pages_exports_every_filtered_row(self) -> None:
        with TemporaryDirectory() as directory:
            database, first, second = self._create_many_changes(directory)
            json_path = Path(directory) / "all.json"
            csv_path = Path(directory) / "all.csv"
            html_path = Path(directory) / "all.html"
            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                code = main(
                    [
                        "index",
                        "folder-compare",
                        str(database),
                        "--from-session-id",
                        str(first.session_id),
                        "--to-session-id",
                        str(second.session_id),
                        "--page-size",
                        "2",
                        "--all-pages",
                        "--json",
                        str(json_path),
                        "--csv",
                        str(csv_path),
                        "--html",
                        str(html_path),
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertGreater(payload["total_rows"], 2)
            self.assertEqual(len(payload["rows"]), payload["total_rows"])
            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                csv_rows = list(csv.reader(handle, delimiter=";"))
            self.assertEqual(len(csv_rows) - 1, payload["total_rows"])
            self.assertEqual(
                html_path.read_text(encoding="utf-8").count("<tr>") - 1,
                payload["total_rows"],
            )
            self.assertIn("Seite 1 von", output.getvalue())

    def test_folder_compare_all_pages_requires_export(self) -> None:
        with TemporaryDirectory() as directory:
            database, _, _ = self._create_many_changes(directory)
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                code = main(
                    [
                        "index",
                        "folder-compare",
                        str(database),
                        "--all-pages",
                    ]
                )
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
