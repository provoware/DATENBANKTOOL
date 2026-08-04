from __future__ import annotations

import json
import os
import sqlite3
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from datenbanktool.cli import main
from datenbanktool.core.changes import ChangeFilter, export_changes, query_changes
from datenbanktool.core.incremental import IncrementalScanOptions, incremental_rescan
from datenbanktool.core.index_database import IndexBuildOptions, build_index
from datenbanktool.core.search import SearchFilter, build_fulltext_index, search_index


class SearchAndChangeIntegrationTests(unittest.TestCase):
    def _create_history(self, directory: str) -> tuple[Path, Path, int]:
        root = Path(directory) / "data"
        root.mkdir()
        database = Path(directory) / "index.sqlite3"
        (root / "alt").mkdir()
        (root / "texte").mkdir()
        (root / "alt" / "track.mp3").write_bytes(b"audio-data")
        (root / "texte" / "notiz.txt").write_text("alt", encoding="utf-8")
        (root / "weg.bin").write_bytes(b"weg")
        build_index(IndexBuildOptions(root=root, database=database, hash_duplicates=True))

        (root / "neu").mkdir()
        (root / "alt" / "track.mp3").rename(root / "neu" / "track.mp3")
        (root / "texte" / "notiz.txt").write_text("deutlich geändert", encoding="utf-8")
        (root / "weg.bin").unlink()
        (root / "bilder").mkdir()
        (root / "bilder" / "foto.jpg").write_bytes(b"jpeg-data")
        (root / " zick?.txt").write_text("problemname", encoding="utf-8")
        os.utime(root / "texte" / "notiz.txt", None)
        result = incremental_rescan(IncrementalScanOptions(root=root, database=database))
        return root, database, result.session_id

    def test_search_pagination_filters_and_stable_sorting(self) -> None:
        with TemporaryDirectory() as directory:
            _, database, session_id = self._create_history(directory)
            page = search_index(
                database,
                session_id=session_id,
                filters=SearchFilter(page=1, page_size=2, sort_by="path"),
            )
            self.assertGreaterEqual(page.total_rows, 4)
            self.assertEqual(len(page.rows), 2)
            self.assertEqual(
                [row.relative_path for row in page.rows],
                sorted(
                    (row.relative_path for row in page.rows),
                    key=lambda value: (value.casefold(), value),
                ),
            )
            warning_page = search_index(
                database,
                session_id=session_id,
                filters=SearchFilter(naming_warning_only=True),
            )
            self.assertEqual([row.relative_path for row in warning_page.rows], [" zick?.txt"])
            text_page = search_index(
                database,
                session_id=session_id,
                filters=SearchFilter(text="track", categories=("audio",)),
            )
            self.assertEqual([row.relative_path for row in text_page.rows], ["neu/track.mp3"])

    def test_optional_fts5_index_is_explicit_and_searchable(self) -> None:
        with TemporaryDirectory() as directory:
            _, database, session_id = self._create_history(directory)
            fallback = search_index(
                database, session_id=session_id, filters=SearchFilter(text="notiz")
            )
            self.assertEqual(fallback.engine, "like")
            try:
                built = build_fulltext_index(database, session_id=session_id)
            except Exception as error:
                if "FTS5" in str(error).upper():
                    self.skipTest(str(error))
                raise
            self.assertEqual(built.session_id, session_id)
            fast = search_index(
                database,
                session_id=session_id,
                filters=SearchFilter(
                    text="notiz", fulltext_mode="required", sort_by="relevance"
                ),
            )
            self.assertEqual(fast.engine, "fts5")
            self.assertEqual([row.relative_path for row in fast.rows], ["texte/notiz.txt"])

    def test_changes_terminal_json_csv_and_html(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            _, database, session_id = self._create_history(directory)
            page = query_changes(database, session_id=session_id)
            self.assertEqual(page.counts["added"], 2)
            self.assertEqual(page.counts["modified"], 1)
            self.assertEqual(page.counts["moved"], 1)
            self.assertEqual(page.counts["removed"], 1)

            json_path = base / "changes.json"
            csv_path = base / "changes.csv"
            html_path = base / "changes.html"
            exported = export_changes(
                database,
                session_id=session_id,
                filters=ChangeFilter(change_types=("added", "moved")),
                json_path=json_path,
                csv_path=csv_path,
                html_path=html_path,
            )
            self.assertEqual(exported.row_count, 3)
            self.assertEqual(len(json.loads(json_path.read_text(encoding="utf-8"))["changes"]), 3)
            self.assertTrue(csv_path.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertIn(
                "Änderungen seit dem vorherigen Scan",
                html_path.read_text(encoding="utf-8"),
            )

    def test_cli_search_and_changes_are_layperson_readable(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            _, database, session_id = self._create_history(directory)
            search_output = StringIO()
            with redirect_stdout(search_output), redirect_stderr(StringIO()):
                self.assertEqual(
                    main(
                        [
                            "index", "search", str(database), "track",
                            "--session-id", str(session_id),
                        ]
                    ),
                    0,
                )
            self.assertIn("Treffer:", search_output.getvalue())
            self.assertIn("neu/track.mp3", search_output.getvalue())

            changes_output = StringIO()
            with redirect_stdout(changes_output), redirect_stderr(StringIO()):
                self.assertEqual(
                    main(
                        [
                            "index", "changes", str(database), "--session-id", str(session_id),
                            "--type", "moved", "--json", str(base / "moved.json"),
                        ]
                    ),
                    0,
                )
            self.assertIn("[Verschoben]", changes_output.getvalue())
            self.assertTrue((base / "moved.json").exists())

    def test_search_does_not_modify_database(self) -> None:
        with TemporaryDirectory() as directory:
            _, database, session_id = self._create_history(directory)
            before = database.stat().st_mtime_ns
            search_index(database, session_id=session_id, filters=SearchFilter(text="foto"))
            after = database.stat().st_mtime_ns
            self.assertEqual(before, after)
            connection = sqlite3.connect(database)
            try:
                self.assertEqual(connection.execute("PRAGMA quick_check").fetchone()[0], "ok")
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
