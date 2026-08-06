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
from datenbanktool.core.backup_catalog import list_backups
from datenbanktool.core.config_backups import create_config_backup
from datenbanktool.core.index_database import IndexBuildOptions, build_index
from datenbanktool.core.presets import save_preset
from datenbanktool.core.recovery import load_recovery_candidates
from datenbanktool.core.run_journal import (
    MAX_RESUME_RECORDS,
    RunJournal,
    load_resume_records,
)
from datenbanktool.core.search import SearchFilter
from datenbanktool.core.terminal_home import TerminalHome
from datenbanktool.core.timeline_presets import save_timeline_preset


class MultipleRecoveryTests(unittest.TestCase):
    def _interrupted(
        self,
        directory: str,
        name: str,
    ) -> tuple[Path, Path, tuple[str, ...], RunJournal]:
        root = Path(directory) / f"data-{name}"
        root.mkdir()
        for number in range(3):
            (root / f"file-{number}.txt").write_text(str(number), encoding="utf-8")
        database = Path(directory) / f"{name}.sqlite3"
        result = build_index(
            IndexBuildOptions(
                root=root,
                database=database,
                max_files=1,
                autosave_seconds=0.01,
            )
        )
        self.assertEqual(result.status, "interrupted")
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
        return root, database, command, journal

    def test_two_index_files_are_kept_and_validated_separately(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ):
            _, first_database, first_command, first_journal = self._interrupted(
                directory,
                "first",
            )
            _, second_database, _, _ = self._interrupted(directory, "second")
            records = load_resume_records()
            self.assertEqual(len(records), 2)
            self.assertEqual(
                {record["database_key"] for record in records},
                {str(first_database.resolve()), str(second_database.resolve())},
            )
            candidates = load_recovery_candidates()
            self.assertEqual(len(candidates), 2)
            self.assertTrue(all(candidate.resumable for candidate in candidates))
            first_journal.record_command_result(first_command, 0)
            remaining = load_resume_records()
            self.assertEqual(len(remaining), 1)
            self.assertEqual(remaining[0]["database_key"], str(second_database.resolve()))

    def test_same_database_is_deduplicated(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory},
        ):
            root = Path(directory) / "data"
            root.mkdir()
            database = Path(directory) / "index.sqlite3"
            command = ("index", "build", str(root), "--database", str(database))
            first = RunJournal.begin(command, version="test")
            first.record_active_command(command)
            second = RunJournal.begin(command, version="test")
            second.record_active_command((*command, "--resume"))
            records = load_resume_records()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["arguments"].count("--resume"), 1)

    def test_record_list_is_bounded_without_deleting_index_files(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory},
        ):
            root = Path(directory) / "data"
            root.mkdir()
            databases = []
            for number in range(MAX_RESUME_RECORDS + 4):
                database = Path(directory) / f"index-{number}.sqlite3"
                databases.append(database)
                command = ("index", "build", str(root), "--database", str(database))
                journal = RunJournal.begin(command, version="test")
                journal.record_active_command(command)
            self.assertEqual(len(load_resume_records()), MAX_RESUME_RECORDS)
            self.assertTrue(all(not database.exists() for database in databases))

    def test_guided_discard_removes_only_selected_entry(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ):
            self._interrupted(directory, "first")
            self._interrupted(directory, "second")
            calls: list[tuple[str, ...]] = []
            output = StringIO()
            home = TerminalHome(
                lambda command: calls.append(tuple(command)) or 0,
                input_stream=StringIO("1\nverwerfen\nj\nn\n0\n"),
                output_stream=output,
                error_stream=StringIO(),
                color_mode="never",
            )
            self.assertEqual(home.run(), 0)
            self.assertEqual(calls, [])
            self.assertEqual(len(load_resume_records()), 1)
            self.assertIn("Wiederanlaufhinweis verworfen", output.getvalue())
            self.assertIn("Gespeicherte Wiederanläufe: 2", output.getvalue())
            self.assertIn("Gespeicherte Wiederanläufe: 1", output.getvalue())

    def test_unavailable_entry_is_visible_and_not_started(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory},
        ):
            command = (
                "index",
                "build",
                str(Path(directory) / "missing-root"),
                "--database",
                str(Path(directory) / "missing.sqlite3"),
            )
            journal = RunJournal.begin(command, version="test")
            journal.record_active_command(command)
            candidates = load_recovery_candidates()
            self.assertEqual(len(candidates), 1)
            self.assertFalse(candidates[0].resumable)
            output = StringIO()
            home = TerminalHome(
                lambda command: self.fail(f"Nicht startbar: {command}"),
                input_stream=StringIO("n\n0\n"),
                output_stream=output,
                error_stream=StringIO(),
                color_mode="never",
            )
            self.assertEqual(home.run(), 0)
            self.assertIn("derzeit nicht fortsetzbar", output.getvalue())
            self.assertEqual(len(load_resume_records()), 1)


class ConfigBackupTests(unittest.TestCase):
    def _cli(self, arguments: list[str]) -> tuple[int, str, str]:
        output = StringIO()
        error = StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            code = cli_main(["--color", "never", *arguments])
        return code, output.getvalue(), error.getvalue()

    def test_search_replace_creates_verified_backup_of_old_content(self) -> None:
        with TemporaryDirectory() as directory:
            preset_file = Path(directory) / "search-presets.json"
            save_preset("Audio", SearchFilter(text="alt"), path=preset_file)
            old_content = preset_file.read_bytes()
            code, output, error = self._cli(
                [
                    "index",
                    "presets",
                    "save",
                    "Audio",
                    "--preset-file",
                    str(preset_file),
                    "--replace",
                    "--backup-before-change",
                    "--text",
                    "neu",
                ]
            )
            self.assertEqual(code, 0, error)
            backups = list(preset_file.parent.glob(f"{preset_file.name}.backup-*.json"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), old_content)
            self.assertNotEqual(preset_file.read_bytes(), old_content)
            self.assertIn("Konfigurationssicherung geprüft", output)

    def test_timeline_delete_creates_backup_and_keeps_it(self) -> None:
        with TemporaryDirectory() as directory:
            preset_file = Path(directory) / "timeline-presets.json"
            save_timeline_preset("Musik", "Musik/Archiv", path=preset_file)
            code, output, error = self._cli(
                [
                    "index",
                    "timeline-presets",
                    "delete",
                    "Musik",
                    "--preset-file",
                    str(preset_file),
                    "--backup-before-change",
                    "--yes",
                ]
            )
            self.assertEqual(code, 0, error)
            backups = list(preset_file.parent.glob(f"{preset_file.name}.backup-*.json"))
            self.assertEqual(len(backups), 1)
            payload = json.loads(backups[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["presets"][0]["name"], "Musik")
            active = json.loads(preset_file.read_text(encoding="utf-8"))
            self.assertEqual(active["presets"], [])
            self.assertIn("Zeitreihen-Vorlage gelöscht", output)

    def test_backup_is_optional_and_never_rotated(self) -> None:
        with TemporaryDirectory() as directory:
            preset_file = Path(directory) / "timeline-presets.json"
            save_timeline_preset("Musik", "Musik", path=preset_file)
            code, _, error = self._cli(
                [
                    "index",
                    "timeline-presets",
                    "save",
                    "Musik",
                    "Archiv",
                    "--preset-file",
                    str(preset_file),
                    "--replace",
                ]
            )
            self.assertEqual(code, 0, error)
            self.assertEqual(
                list(preset_file.parent.glob(f"{preset_file.name}.backup-*.json")),
                [],
            )
            for folder in ("Bilder", "Videos"):
                code, _, error = self._cli(
                    [
                        "index",
                        "timeline-presets",
                        "save",
                        "Musik",
                        folder,
                        "--preset-file",
                        str(preset_file),
                        "--replace",
                        "--backup-before-change",
                    ]
                )
                self.assertEqual(code, 0, error)
            backups = list(preset_file.parent.glob(f"{preset_file.name}.backup-*.json"))
            self.assertEqual(len(backups), 2)
            self.assertTrue(all(path.exists() for path in backups))

    def test_corrupt_configuration_is_not_backed_up(self) -> None:
        with TemporaryDirectory() as directory:
            source = Path(directory) / "search-presets.json"
            source.write_text("{kaputt", encoding="utf-8")
            with self.assertRaises(ValueError):
                create_config_backup(source)
            self.assertEqual(list(Path(directory).glob("*.backup-*.json")), [])

    def test_new_backup_is_visible_in_existing_catalogue(self) -> None:
        with TemporaryDirectory() as directory:
            config = Path(directory) / "config"
            config.mkdir()
            preset_file = config / "timeline-presets.json"
            save_timeline_preset("Musik", "Musik", path=preset_file)
            backup = create_config_backup(preset_file)
            items = list_backups(
                Path(directory) / "index.sqlite3",
                config_directory=config,
            )
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].path, backup.backup)
            self.assertEqual(items[0].status_level, "green")


if __name__ == "__main__":
    unittest.main()
