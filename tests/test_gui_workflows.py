from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from datenbanktool.gui_duplicate_decision import DuplicateCandidate, propose_duplicate_keeper
from datenbanktool.gui_query import QueryFilter, ReadOnlyQueryService
from datenbanktool.gui_rename_preview import RenameInput, RenameRule, build_rename_preview


class QueryServiceTests(unittest.TestCase):
    def _database(self, path: Path) -> None:
        connection = sqlite3.connect(path)
        connection.executescript(
            """
            CREATE TABLE scan_sessions (id INTEGER PRIMARY KEY);
            CREATE TABLE files (
                id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL, relative_path TEXT NOT NULL,
                size_bytes INTEGER NOT NULL, modified_utc TEXT NOT NULL, suffix TEXT NOT NULL,
                category TEXT NOT NULL
            );
            CREATE TABLE filename_warnings (file_id INTEGER NOT NULL, code TEXT NOT NULL);
            CREATE TABLE duplicate_members (group_id INTEGER NOT NULL, file_id INTEGER NOT NULL);
            INSERT INTO scan_sessions VALUES (1);
            INSERT INTO files VALUES
                (1, 1, 'Fotos/urlaub.jpg', 100, '2020-01-01', '.jpg', 'image'),
                (2, 1, 'Fotos/urlaub_kopie.jpg', 100, '2020-01-01', '.jpg', 'image'),
                (3, 1, 'Videos/clip.mp4', 9000, '2021-01-01', '.mp4', 'video'),
                (4, 1, 'Dokumente/bericht.pdf', 500, '2022-01-01', '.pdf', 'document');
            INSERT INTO filename_warnings VALUES (4, 'name');
            INSERT INTO duplicate_members VALUES (9, 1), (9, 2);
            """
        )
        connection.commit()
        connection.close()

    def test_filter_pagination_and_query_timing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "index.sqlite3"
            self._database(database)
            before = database.read_bytes()
            service = ReadOnlyQueryService(database)
            page = service.page(QueryFilter(category="image"), limit=1, sort="path")
            self.assertEqual(page.total_count, 2)
            self.assertEqual(len(page.items), 1)
            self.assertTrue(page.has_next)
            self.assertFalse(page.has_previous)
            self.assertGreaterEqual(page.query_seconds, 0.0)
            next_page = service.page(QueryFilter(category="image"), offset=1, limit=1, sort="path")
            self.assertTrue(next_page.has_previous)
            self.assertFalse(next_page.has_next)
            self.assertEqual(database.read_bytes(), before)

    def test_warning_duplicate_and_escaped_path_filters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "index.sqlite3"
            self._database(database)
            service = ReadOnlyQueryService(database)
            warnings = service.page(QueryFilter(warnings_only=True))
            duplicates = service.page(QueryFilter(duplicates_only=True))
            literal = service.page(QueryFilter(path_contains="urlaub_"))
            self.assertEqual(warnings.total_count, 1)
            self.assertEqual(duplicates.total_count, 2)
            self.assertEqual(literal.total_count, 1)


class DuplicateDecisionTests(unittest.TestCase):
    def test_preferred_original_is_only_a_reviewable_keep_proposal(self) -> None:
        decision = propose_duplicate_keeper((
            DuplicateCandidate(1, "/Fotos/Original/a.jpg", 100, "2020", is_preferred_location=True),
            DuplicateCandidate(2, "/Backup/a_kopie.jpg", 100, "2020"),
        ))
        self.assertEqual(decision.keep_file_id, 1)
        self.assertTrue(decision.requires_user_review)
        self.assertIn(decision.confidence, {"medium", "high"})
        self.assertIn("Löschaktionen", decision.explanation)

    def test_size_mismatch_blocks_exact_duplicate_proposal(self) -> None:
        decision = propose_duplicate_keeper((
            DuplicateCandidate(1, "/a.jpg", 100, "2020"),
            DuplicateCandidate(2, "/b.jpg", 101, "2020"),
        ))
        self.assertIsNone(decision.keep_file_id)
        self.assertEqual(decision.confidence, "none")


class RenamePreviewTests(unittest.TestCase):
    def test_preview_is_deterministic_and_preserves_extension(self) -> None:
        rule = RenameRule(prefix="Urlaub 2020", sequence_width=3, lowercase=True)
        preview = build_rename_preview((
            RenameInput(1, "IMG 0001.JPG", 1),
            RenameInput(2, "IMG 0002.JPG", 2),
        ), rule)
        self.assertTrue(all(item.valid for item in preview))
        self.assertEqual(preview[0].proposed_name, "urlaub_2020_img_0001_001.jpg")
        self.assertEqual(preview[1].proposed_name, "urlaub_2020_img_0002_002.jpg")

    def test_collision_is_visible_and_blocks_valid_state(self) -> None:
        rule = RenameRule(prefix="Foto", sequence_width=None)
        preview = build_rename_preview((
            RenameInput(1, "gleich.JPG", 1),
            RenameInput(2, "gleich.JPG", 2),
        ), rule)
        self.assertTrue(all(item.collision for item in preview))
        self.assertTrue(all(not item.valid for item in preview))


if __name__ == "__main__":
    unittest.main()
