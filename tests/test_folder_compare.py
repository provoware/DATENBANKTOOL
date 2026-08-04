from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from datenbanktool.cli import main
from datenbanktool.core.folder_compare import (
    FolderComparisonFilter,
    compare_folders,
)
from datenbanktool.core.guided_home import menu_actions
from datenbanktool.core.index_database import IndexBuildOptions, build_index
from datenbanktool.core.incremental import IncrementalScanOptions, incremental_rescan
from datenbanktool.core.layered_help import get_topic, render_topic


class FolderComparisonTests(unittest.TestCase):
    def _create_two_scans(self, directory: str):
        root = Path(directory) / "data"
        root.mkdir()
        (root / "grow").mkdir()
        (root / "shrink").mkdir()
        (root / "gone").mkdir()
        (root / "stable").mkdir()
        (root / "grow" / "a.bin").write_bytes(b"a" * 10)
        (root / "shrink" / "small.bin").write_bytes(b"s" * 60)
        (root / "gone" / "b.bin").write_bytes(b"b" * 30)
        (root / "stable" / "same.txt").write_text("gleich", encoding="utf-8")
        database = Path(directory) / "index.sqlite3"
        first = build_index(IndexBuildOptions(root=root, database=database))

        (root / "grow" / "a.bin").write_bytes(b"a" * 70)
        (root / "shrink" / "small.bin").write_bytes(b"s" * 5)
        (root / "gone" / "b.bin").unlink()
        (root / "new").mkdir()
        (root / "new" / "c.bin").write_bytes(b"c" * 20)
        second = incremental_rescan(
            IncrementalScanOptions(root=root, database=database)
        )
        return root, database, first, second

    def test_compare_detects_growth_shrink_new_removed_and_unchanged(self) -> None:
        with TemporaryDirectory() as directory:
            _, database, first, second = self._create_two_scans(directory)
            page = compare_folders(database)
            self.assertEqual(page.from_session_id, first.session_id)
            self.assertEqual(page.to_session_id, second.session_id)
            rows = {row.folder: row for row in page.rows}
            self.assertEqual(rows["grow"].change_type, "grown")
            self.assertEqual(rows["shrink"].change_type, "shrunk")
            self.assertEqual(rows["gone"].change_type, "removed")
            self.assertEqual(rows["new"].change_type, "new")
            self.assertNotIn("stable", rows)

            unchanged = compare_folders(
                database,
                filters=FolderComparisonFilter(change_types=("unchanged",)),
            )
            unchanged_rows = {row.folder: row for row in unchanged.rows}
            self.assertEqual(unchanged_rows["stable"].change_type, "unchanged")

    def test_compare_is_read_only_and_rejects_different_roots(self) -> None:
        with TemporaryDirectory() as directory:
            _, database, first, second = self._create_two_scans(directory)
            before = database.read_bytes()
            compare_folders(
                database,
                from_session_id=first.session_id,
                to_session_id=second.session_id,
            )
            self.assertEqual(database.read_bytes(), before)

            other = Path(directory) / "other"
            other.mkdir()
            (other / "x.txt").write_text("x", encoding="utf-8")
            third = build_index(IndexBuildOptions(root=other, database=database))
            with self.assertRaisesRegex(ValueError, "desselben Stammordners"):
                compare_folders(
                    database,
                    from_session_id=second.session_id,
                    to_session_id=third.session_id,
                )

    def test_cli_terminal_and_exports(self) -> None:
        with TemporaryDirectory() as directory:
            _, database, first, second = self._create_two_scans(directory)
            json_path = Path(directory) / "comparison.json"
            csv_path = Path(directory) / "comparison.csv"
            html_path = Path(directory) / "comparison.html"
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
                        "--json",
                        str(json_path),
                        "--csv",
                        str(csv_path),
                        "--html",
                        str(html_path),
                    ]
                )
            self.assertEqual(code, 0)
            self.assertIn("Vergleich:", output.getvalue())
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["from_session_id"], first.session_id)
            self.assertEqual(payload["to_session_id"], second.session_id)
            self.assertTrue(csv_path.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertIn("Ordnervergleich", html_path.read_text(encoding="utf-8"))

    def test_no_terminal_requires_export(self) -> None:
        with TemporaryDirectory() as directory:
            _, database, _, _ = self._create_two_scans(directory)
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(
                    main(
                        [
                            "index",
                            "folder-compare",
                            str(database),
                            "--no-terminal",
                        ]
                    ),
                    2,
                )

    def test_help_topic_and_home_menu_are_connected(self) -> None:
        topic = get_topic("folder-compare")
        self.assertIn("größer oder kleiner", topic.quick)
        self.assertTrue(any(action.key == "10" for action in menu_actions()))
        guided = "\n".join(render_topic(topic, "guided"))
        self.assertIn("Schritt für Schritt", guided)
        self.assertIn("rein lesend", guided.casefold())


if __name__ == "__main__":
    unittest.main()
