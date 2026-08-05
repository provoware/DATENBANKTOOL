from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from datenbanktool.core.durable_files import atomic_write_text, durable_remove


class DurableSymlinkTests(unittest.TestCase):
    def test_atomic_write_does_not_follow_existing_symlink(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real.json"
            real.write_text("alt\n", encoding="utf-8")
            link = root / "state.json"
            link.symlink_to(real)
            with self.assertRaises(ValueError):
                atomic_write_text(link, "neu\n", overwrite=True)
            self.assertTrue(link.is_symlink())
            self.assertEqual(real.read_text(encoding="utf-8"), "alt\n")

    def test_durable_remove_does_not_follow_symlink(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real.json"
            real.write_text("bleibt\n", encoding="utf-8")
            link = root / "resume-run.json"
            link.symlink_to(real)
            with self.assertRaises(ValueError):
                durable_remove(link)
            self.assertTrue(link.is_symlink())
            self.assertEqual(real.read_text(encoding="utf-8"), "bleibt\n")


if __name__ == "__main__":
    unittest.main()
