from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from datenbanktool.cli import main as cli_main
from datenbanktool.core.backup_catalog import delete_backup
from datenbanktool.core.incremental import IncrementalScanOptions, incremental_rescan
from datenbanktool.core.index_admin import backup_index
from datenbanktool.core.index_database import IndexBuildOptions, build_index
from datenbanktool.core.recovery import (
    discard_recovery_candidate,
    load_recovery_candidate,
    load_recovery_candidates,
)
from datenbanktool.core.run_journal import RunJournal, load_resume_record


class RecoveryEdgeTests(unittest.TestCase):
    def test_stale_marker_stays_visible_until_consciously_discarded(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ):
            root = Path(directory) / "data"
            root.mkdir()
            (root / "datei.txt").write_text("inhalt", encoding="utf-8")
            database = Path(directory) / "index.sqlite3"
            build_index(IndexBuildOptions(root=root, database=database))
            command = (
                "index",
                "build",
                str(root),
                "--database",
                str(database),
            )
            journal = RunJournal.begin(command, version="test")
            journal.record_active_command(command)
            self.assertIsNotNone(load_resume_record())
            self.assertIsNone(load_recovery_candidate())
            candidates = load_recovery_candidates()
            self.assertEqual(len(candidates), 1)
            self.assertFalse(candidates[0].resumable)
            self.assertIn("Kein fortsetzbarer", candidates[0].validation_label)
            self.assertIsNotNone(load_resume_record())
            self.assertTrue(discard_recovery_candidate(candidates[0].record_id))
            self.assertIsNone(load_resume_record())

    def test_incremental_interruption_creates_verified_rescan_candidate(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ):
            root = Path(directory) / "data"
            root.mkdir()
            for number in range(3):
                (root / f"datei-{number}.txt").write_text(str(number), encoding="utf-8")
            database = Path(directory) / "index.sqlite3"
            build_index(IndexBuildOptions(root=root, database=database))
            (root / "neu.txt").write_text("neu", encoding="utf-8")
            result = incremental_rescan(
                IncrementalScanOptions(
                    root=root,
                    database=database,
                    max_files=1,
                    autosave_seconds=0.01,
                )
            )
            self.assertEqual(result.status, "interrupted")
            command = (
                "index",
                "rescan",
                str(root),
                "--database",
                str(database),
                "--max-files",
                "1",
            )
            journal = RunJournal.begin(command, version="test")
            journal.record_active_command(command)
            journal.record_command_result(command, 1)
            candidate = load_recovery_candidate()
            self.assertIsNotNone(candidate)
            assert candidate is not None
            self.assertEqual(candidate.operation, "rescan")
            self.assertEqual(candidate.operation_label, "Änderungsprüfung")
            self.assertTrue(candidate.resumable)
            self.assertEqual(candidate.command[-1], "--resume")


class BackupCliEdgeTests(unittest.TestCase):
    def _database_and_backup(self, directory: str) -> tuple[Path, Path]:
        root = Path(directory) / "data"
        root.mkdir()
        (root / "datei.txt").write_text("inhalt", encoding="utf-8")
        database = Path(directory) / "index.sqlite3"
        build_index(IndexBuildOptions(root=root, database=database))
        return database, Path(backup_index(database).backup)

    def test_cli_json_list_and_single_delete(self) -> None:
        with TemporaryDirectory() as directory:
            database, backup = self._database_and_backup(directory)
            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                code = cli_main(
                    [
                        "--color",
                        "never",
                        "index",
                        "backups",
                        "list",
                        str(database),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(len(payload), 1)
            self.assertEqual(payload[0]["path"], str(backup.absolute()))
            self.assertEqual(payload[0]["status_level"], "green")

            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                code = cli_main(
                    [
                        "--color",
                        "never",
                        "index",
                        "backups",
                        "delete",
                        str(database),
                        str(backup),
                        "--confirm-name",
                        backup.name,
                        "--yes",
                    ]
                )
            self.assertEqual(code, 0)
            self.assertIn("Genau eine Sicherung gelöscht", output.getvalue())
            self.assertFalse(backup.exists())
            self.assertTrue(database.exists())

    def test_symlink_backup_is_never_deleted(self) -> None:
        with TemporaryDirectory() as directory:
            database, backup = self._database_and_backup(directory)
            link = backup.with_name(f"{database.name}.backup-link.sqlite3")
            link.symlink_to(backup)
            with self.assertRaises(ValueError):
                delete_backup(
                    database,
                    link,
                    confirm_name=link.name,
                    yes=True,
                )
            self.assertTrue(link.is_symlink())
            self.assertTrue(backup.exists())


if __name__ == "__main__":
    unittest.main()
