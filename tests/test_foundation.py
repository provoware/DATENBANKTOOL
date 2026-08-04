from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from datenbanktool.core.classification import classify_path
from datenbanktool.core.models import FileCategory
from datenbanktool.core.naming import filename_warnings
from datenbanktool.core.scanner import ScanOptions, scan_tree


class FoundationTests(unittest.TestCase):
    def test_classification_is_case_insensitive(self) -> None:
        self.assertEqual(classify_path(Path("TRACK.FLAC")), FileCategory.AUDIO)
        self.assertEqual(classify_path(Path("clip.MP4")), FileCategory.VIDEO)
        self.assertEqual(classify_path(Path("script.py")), FileCategory.CODE)

    def test_filename_risks_are_reported(self) -> None:
        warnings = filename_warnings(" -mix  ??.wav ")
        self.assertIn("leading-or-trailing-whitespace", warnings)
        self.assertIn("cross-platform-risk-character", warnings)
        self.assertIn("repeated-space", warnings)
        self.assertIn("leading-dash-shell-risk", filename_warnings("-rf.txt"))

    def test_scan_finds_exact_duplicates(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.txt").write_text("gleich", encoding="utf-8")
            (root / "b.txt").write_text("gleich", encoding="utf-8")
            (root / "sound.wav").write_bytes(b"RIFF-test")
            report = scan_tree(ScanOptions(root=root, hash_duplicates=True, large_file_bytes=4))
            self.assertEqual(len(report.files), 3)
            self.assertEqual(report.category_counts["text"], 2)
            self.assertEqual(report.category_counts["audio"], 1)
            self.assertEqual(len(report.duplicate_groups), 1)
            self.assertEqual(report.duplicate_groups[0].paths, ["a.txt", "b.txt"])
            self.assertEqual(report.errors, [])

    def test_max_files_marks_truncated_scan(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.txt").write_text("a", encoding="utf-8")
            (root / "b.txt").write_text("b", encoding="utf-8")
            report = scan_tree(ScanOptions(root=root, max_files=1))
            self.assertEqual(len(report.files), 1)
            self.assertTrue(report.truncated)


if __name__ == "__main__":
    unittest.main()
