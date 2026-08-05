from __future__ import annotations

from io import StringIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from datenbanktool.core.backup_catalog import delete_backup, list_backups
from datenbanktool.core.index_admin import backup_index
from datenbanktool.core.index_database import IndexBuildOptions, build_index
from datenbanktool.core.recovery import load_recovery_candidate
from datenbanktool.core.run_journal import RunJournal, load_resume_record
from datenbanktool.core.terminal_home import TerminalHome


class GuidedRecoveryTests(unittest.TestCase):
    def _interrupted_scan(self, directory: str) -> tuple[Path, Path]:
        root = Path(directory) / "daten"
        root.mkdir()
        for number in range(4):
            (root / f"datei-{number}.txt").write_text(str(number), encoding="utf-8")
        database = Path(directory) / "index.sqlite3"
        result = build_index(
            IndexBuildOptions(
                root=root,
                database=database,
                max_files=1,
                autosave_seconds=0.01,
            )
        )
        self.assertEqual(result.status, "interrupted")
        return root, database

    def _record_interrupted(self, root: Path, database: Path) -> tuple[str, ...]:
        command = (
            "index",
            "build",
            str(root),
            "--database",
            str(database),
            "--max-files",
            "1",
        )
        journal = RunJournal.begin(command, version="test")
        journal.record_active_command(command)
        journal.record_command_result(command, 1)
        return command

    def test_verified_candidate_prefills_root_database_and_resume(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ):
            root, database = self._interrupted_scan(directory)
            self._record_interrupted(root, database)
            candidate = load_recovery_candidate()
            self.assertIsNotNone(candidate)
            assert candidate is not None
            self.assertEqual(candidate.root, str(root.resolve()))
            self.assertEqual(candidate.database, str(database.resolve()))
            self.assertEqual(candidate.status, "interrupted")
            self.assertTrue(candidate.resumable)
            self.assertEqual(candidate.command[-1], "--resume")
            self.assertEqual(candidate.command.count("--resume"), 1)

    def test_successful_scan_result_removes_only_resume_marker(self) -> None:
        with TemporaryDirectory() as directory:
            state = Path(directory) / "state"
            command = ("index", "build", "/tmp/data", "--database", "/tmp/index.sqlite3")
            journal = RunJournal.begin(command, version="test", state_directory=state)
            journal.record_active_command(command)
            self.assertIsNotNone(load_resume_record(state))
            journal.record_command_result(command, 0)
            self.assertIsNone(load_resume_record(state))
            self.assertTrue(journal.path.exists())

    def test_start_page_declines_without_losing_recovery(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ):
            root, database = self._interrupted_scan(directory)
            self._record_interrupted(root, database)
            calls: list[tuple[str, ...]] = []
            output = StringIO()
            home = TerminalHome(
                lambda command: calls.append(tuple(command)) or 0,
                input_stream=StringIO("n\n0\n"),
                output_stream=output,
                error_stream=StringIO(),
                color_mode="never",
            )
            self.assertEqual(home.run(), 0)
            self.assertEqual(calls, [])
            self.assertIn("Gespeicherte Wiederanläufe: 1", output.getvalue())
            self.assertIn("Kein Eintrag verändert", output.getvalue())
            self.assertIsNotNone(load_resume_record())

    def test_start_page_confirms_exact_visible_resume_command(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ):
            root, database = self._interrupted_scan(directory)
            original = self._record_interrupted(root, database)
            calls: list[tuple[str, ...]] = []
            output = StringIO()
            home = TerminalHome(
                lambda command: calls.append(tuple(command)) or 0,
                input_stream=StringIO("1\nfortsetzen\n0\n"),
                output_stream=output,
                error_stream=StringIO(),
                color_mode="never",
            )
            self.assertEqual(home.run(), 0)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][:-1], original)
            self.assertEqual(calls[0][-1], "--resume")
            text = output.getvalue()
            self.assertIn("Wiederanlauf im Detail", text)
            self.assertLess(
                text.index("Ordner:"),
                text.index("Begründung:"),
            )


class BackupCatalogueTests(unittest.TestCase):
    def _prepared_catalogue(self, directory: str):
        root = Path(directory) / "data"
        root.mkdir()
        (root / "datei.txt").write_text("inhalt", encoding="utf-8")
        database = Path(directory) / "index.sqlite3"
        build_index(IndexBuildOptions(root=root, database=database))
        index_backup = Path(backup_index(database).backup)
        config = Path(directory) / "config"
        config.mkdir()
        valid_config = config / "search-presets.json.backup-20260805.json"
        valid_config.write_text(
            json.dumps({"schema_version": 1, "presets": []}),
            encoding="utf-8",
        )
        invalid_config = config / "timeline-presets.json.backup-20260805.json"
        invalid_config.write_text("{kaputt", encoding="utf-8")
        return database, index_backup, config, valid_config, invalid_config

    def test_catalogue_reports_kind_size_age_and_validation(self) -> None:
        with TemporaryDirectory() as directory:
            database, index_backup, config, valid_config, invalid_config = (
                self._prepared_catalogue(directory)
            )
            items = list_backups(database, config_directory=config)
            self.assertEqual({item.path for item in items}, {
                str(index_backup.absolute()),
                str(valid_config.absolute()),
                str(invalid_config.absolute()),
            })
            by_name = {item.name: item for item in items}
            self.assertEqual(by_name[index_backup.name].status_level, "green")
            self.assertEqual(by_name[valid_config.name].status_level, "green")
            self.assertEqual(by_name[invalid_config.name].status_level, "red")
            for item in items:
                self.assertGreater(item.size_bytes, 0)
                self.assertGreaterEqual(item.age_seconds, 0)
                self.assertTrue(item.modified_utc.endswith("+00:00"))

    def test_delete_requires_catalogue_exact_name_and_yes(self) -> None:
        with TemporaryDirectory() as directory:
            database, index_backup, config, _, _ = self._prepared_catalogue(directory)
            with self.assertRaises(ValueError):
                delete_backup(
                    database,
                    index_backup,
                    confirm_name=index_backup.name,
                    yes=False,
                    config_directory=config,
                )
            with self.assertRaises(ValueError):
                delete_backup(
                    database,
                    index_backup,
                    confirm_name="anderer-name.sqlite3",
                    yes=True,
                    config_directory=config,
                )
            with self.assertRaises(ValueError):
                delete_backup(
                    database,
                    database,
                    confirm_name=database.name,
                    yes=True,
                    config_directory=config,
                )
            deleted = delete_backup(
                database,
                index_backup,
                confirm_name=index_backup.name,
                yes=True,
                config_directory=config,
            )
            self.assertEqual(deleted.path, str(index_backup.absolute()))
            self.assertFalse(index_backup.exists())
            self.assertTrue(database.exists())

    def test_guided_backup_overview_dispatches_safe_argument_list(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ):
            database = Path(directory) / "index.sqlite3"
            calls: list[tuple[str, ...]] = []
            home = TerminalHome(
                lambda command: calls.append(tuple(command)) or 0,
                input_stream=StringIO(f"7\nanzeigen\n{database}\nj\n0\n"),
                output_stream=StringIO(),
                error_stream=StringIO(),
                color_mode="never",
            )
            self.assertEqual(home.run(), 0)
            self.assertEqual(
                calls,
                [("index", "backups", "list", str(database))],
            )


if __name__ == "__main__":
    unittest.main()
