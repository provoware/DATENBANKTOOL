from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from datenbanktool.gui_assistant import AssistantTimeline
from datenbanktool.gui_presets import DEFAULT_PRESETS, preset_by_id, validate_presets
from datenbanktool.gui_quality import quality_gate_passed, run_gui_quality_gate
from datenbanktool.gui_readonly import ReadOnlyIndexAdapter
from datenbanktool.gui_testlab import DEFAULT_TEST_FOLDER, run_validation


class ReadOnlyAdapterTests(unittest.TestCase):
    def _database(self, path: Path) -> None:
        connection = sqlite3.connect(path)
        connection.executescript(
            """
            CREATE TABLE scan_sessions (
                id INTEGER PRIMARY KEY, root TEXT NOT NULL, status TEXT NOT NULL,
                phase TEXT NOT NULL, error_count INTEGER NOT NULL, updated_utc TEXT NOT NULL
            );
            CREATE TABLE files (
                id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL, relative_path TEXT NOT NULL,
                size_bytes INTEGER NOT NULL, modified_utc TEXT NOT NULL, suffix TEXT NOT NULL,
                category TEXT NOT NULL, is_large INTEGER NOT NULL
            );
            CREATE TABLE filename_warnings (file_id INTEGER NOT NULL, code TEXT NOT NULL);
            CREATE TABLE duplicate_groups (
                id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL,
                sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL
            );
            CREATE TABLE duplicate_members (group_id INTEGER NOT NULL, file_id INTEGER NOT NULL);
            INSERT INTO scan_sessions VALUES (1, '/archive', 'complete', 'complete', 0, '2026-08-08T01:00:00Z');
            INSERT INTO files VALUES
                (1, 1, 'Fotos/2020/a.jpg', 100, '2020-01-01T00:00:00Z', '.jpg', 'image', 0),
                (2, 1, 'Fotos/2020/a-copy.jpg', 100, '2020-01-01T00:00:00Z', '.jpg', 'image', 0),
                (3, 1, 'Videos/b.mp4', 5000, '2020-01-02T00:00:00Z', '.mp4', 'video', 1),
                (4, 1, 'Unklar/blob', 5, '2020-01-03T00:00:00Z', '', 'unknown', 0);
            INSERT INTO filename_warnings VALUES (4, 'missing_suffix');
            INSERT INTO duplicate_groups VALUES (7, 1, 'abc', 100);
            INSERT INTO duplicate_members VALUES (7, 1), (7, 2);
            """
        )
        connection.commit()
        connection.close()

    def test_adapter_reads_existing_index_without_write_capability(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "index.sqlite3"
            self._database(database)
            before = database.read_bytes()
            adapter = ReadOnlyIndexAdapter(database)
            summary = adapter.summary()
            self.assertEqual(summary.file_count, 4)
            self.assertEqual(summary.folder_count, 3)
            self.assertEqual(summary.duplicate_groups, 1)
            self.assertEqual(summary.duplicate_files, 2)
            self.assertEqual(summary.duplicate_bytes, 100)
            self.assertEqual(summary.warning_count, 1)
            self.assertEqual(summary.unknown_count, 1)
            self.assertEqual(summary.large_count, 1)
            self.assertEqual(database.read_bytes(), before)

            categories = adapter.categories()
            self.assertEqual(categories[0].category, "video")
            rows = adapter.files(limit=2)
            self.assertEqual(rows[0].relative_path, "Videos/b.mp4")
            self.assertEqual(database.read_bytes(), before)

    def test_missing_index_is_clear_error(self) -> None:
        adapter = ReadOnlyIndexAdapter(Path("/definitely/not/here/index.sqlite3"))
        with self.assertRaises(FileNotFoundError):
            adapter.summary()


class PresetTests(unittest.TestCase):
    def test_defaults_are_non_destructive_and_valid(self) -> None:
        self.assertFalse(validate_presets())
        self.assertTrue(DEFAULT_PRESETS)
        self.assertTrue(all(not preset.destructive for preset in DEFAULT_PRESETS))

    def test_editable_preset_cannot_change_action_or_safety(self) -> None:
        preset = preset_by_id("photos-by-date")
        changed = preset.edited(title="Eigene Fotoordnung")
        self.assertEqual(changed.title, "Eigene Fotoordnung")
        with self.assertRaises(ValueError):
            preset.edited(action="mark")
        with self.assertRaises(ValueError):
            preset.edited(destructive=True)


class TestLabTests(unittest.TestCase):
    def test_default_test_folder_passes_automated_validation(self) -> None:
        report = run_validation(DEFAULT_TEST_FOLDER)
        self.assertEqual(report.failed, 0)
        self.assertGreaterEqual(report.passed, 6)
        self.assertGreater(report.warnings, 0)
        self.assertGreater(report.total_bytes, 0)


class AssistantTests(unittest.TestCase):
    def test_assistant_explains_without_silent_state_changes(self) -> None:
        timeline = AssistantTimeline()
        message = timeline.explain_scan(files=1000, warnings=2, errors=0)
        self.assertEqual(message.severity, "info")
        entry = timeline.explain_action(
            action="Duplikat markieren",
            reason="Hash identisch",
            effect="Nur Vorschau; Original bleibt erhalten",
            reversible=True,
        )
        self.assertEqual(entry.sequence, 1)
        self.assertTrue(entry.reversible)
        self.assertEqual(len(timeline.entries()), 1)


class QualityGateTests(unittest.TestCase):
    def test_gui_quality_gate_is_green(self) -> None:
        findings = run_gui_quality_gate()
        self.assertTrue(findings)
        self.assertTrue(quality_gate_passed())
        self.assertTrue(all(item.passed for item in findings))


if __name__ == "__main__":
    unittest.main()
