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
from datenbanktool.core.config_backups import create_config_backup
from datenbanktool.core.index_database import IndexBuildOptions, build_index
from datenbanktool.core.presets import save_preset
from datenbanktool.core.run_journal import RunJournal, default_resume_path
from datenbanktool.core.search import SearchFilter


class RecoveryDiagnosticsTests(unittest.TestCase):
    def _cli(self, arguments: list[str]) -> tuple[int, str, str]:
        output = StringIO()
        error = StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            code = cli_main(["--color", "never", *arguments])
        return code, output.getvalue(), error.getvalue()

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
        return root, database

    def test_terminal_diagnostics_are_complete_and_do_not_change_recovery_or_index(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ):
            root, database = self._interrupted_scan(directory)
            resume = default_resume_path()
            resume_before = resume.read_bytes()
            database_before = database.read_bytes()

            code, output, error = self._cli(["index", "recovery"])

            self.assertEqual(code, 0, error)
            self.assertIn("Wiederanlauf-Diagnose – vollständig lesend", output)
            self.assertIn("Prüfstatus: Geprüft und fortsetzbar", output)
            self.assertIn(f"Ordner: {root.resolve()}", output)
            self.assertIn(f"Indexdatei: {database.resolve()}", output)
            self.assertIn("Sitzung: #", output)
            self.assertIn("Phase:", output)
            self.assertIn("startbar: 1", output)
            self.assertIn("kein Scan gestartet", output)
            self.assertEqual(resume.read_bytes(), resume_before)
            self.assertEqual(database.read_bytes(), database_before)

    def test_json_diagnostics_include_requested_fields_without_ansi(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ):
            root, database = self._interrupted_scan(directory)
            code, output, error = self._cli(["index", "recovery", "--json"])
            self.assertEqual(code, 0, error)
            payload = json.loads(output)
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["record_count"], 1)
            self.assertEqual(payload["startable_count"], 1)
            item = payload["items"][0]
            self.assertEqual(item["root"], str(root.resolve()))
            self.assertEqual(item["database"], str(database.resolve()))
            self.assertIsInstance(item["session_id"], int)
            self.assertTrue(item["phase"])
            self.assertTrue(item["startable"])
            self.assertTrue(item["validation_label"])
            self.assertNotIn("\x1b[", output)

    def test_empty_diagnostics_are_successful_and_read_only(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ):
            code, output, error = self._cli(["index", "recovery", "--json"])
            self.assertEqual(code, 0, error)
            payload = json.loads(output)
            self.assertEqual(payload["record_count"], 0)
            self.assertEqual(payload["items"], [])
            self.assertFalse(default_resume_path().exists())


class RestoreLogTests(unittest.TestCase):
    def _cli(self, arguments: list[str]) -> tuple[int, str, str]:
        output = StringIO()
        error = StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            code = cli_main(["--color", "never", *arguments])
        return code, output.getvalue(), error.getvalue()

    def _difference(self, directory: str) -> tuple[Path, Path, Path, bytes]:
        config = Path(directory) / "config"
        config.mkdir()
        active = config / "search-presets.json"
        save_preset(
            "Alt",
            SearchFilter(text="NICHT_INS_PROTOKOLL_SECRET_TOKEN"),
            path=active,
        )
        selected = Path(create_config_backup(active).backup)
        save_preset(
            "Alt",
            SearchFilter(text="neuer aktiver Stand"),
            path=active,
            replace=True,
        )
        return config, active, selected, selected.read_bytes()

    def test_optional_restore_log_contains_only_paths_times_and_three_hashes(self) -> None:
        with TemporaryDirectory() as directory:
            config, active, selected, selected_content = self._difference(directory)
            database = Path(directory) / "index.sqlite3"
            restore_log = Path(directory) / "nachweise" / "restore.json"

            code, output, error = self._cli(
                [
                    "index",
                    "backups",
                    "restore",
                    str(database),
                    str(selected),
                    "--config-directory",
                    str(config),
                    "--confirm-name",
                    selected.name,
                    "--yes",
                    "--restore-log",
                    str(restore_log),
                    "--json",
                ]
            )

            self.assertEqual(code, 0, error)
            result = json.loads(output)
            self.assertEqual(active.read_bytes(), selected_content)
            self.assertEqual(result["restore_log"]["path"], str(restore_log.absolute()))
            self.assertIsNone(result["restore_log_error"])
            self.assertEqual(restore_log.stat().st_mode & 0o777, 0o600)

            audit_text = restore_log.read_text(encoding="utf-8")
            audit = json.loads(audit_text)
            self.assertEqual(audit["schema_version"], 1)
            self.assertEqual(audit["event"], "configuration_restore")
            self.assertEqual(audit["active_file"], str(active.absolute()))
            self.assertEqual(audit["selected_backup"], str(selected.absolute()))
            self.assertTrue(Path(audit["rollback_backup"]).is_file())
            self.assertEqual(
                set(audit["sha256"]),
                {"active_after_restore", "selected_backup", "rollback_backup"},
            )
            self.assertEqual(
                audit["sha256"]["active_after_restore"],
                audit["sha256"]["selected_backup"],
            )
            self.assertNotIn("presets", audit_text)
            self.assertNotIn("NICHT_INS_PROTOKOLL_SECRET_TOKEN", audit_text)

    def test_no_restore_log_is_created_without_explicit_option(self) -> None:
        with TemporaryDirectory() as directory:
            config, active, selected, selected_content = self._difference(directory)
            database = Path(directory) / "index.sqlite3"
            code, output, error = self._cli(
                [
                    "index",
                    "backups",
                    "restore",
                    str(database),
                    str(selected),
                    "--config-directory",
                    str(config),
                    "--confirm-name",
                    selected.name,
                    "--yes",
                    "--json",
                ]
            )
            self.assertEqual(code, 0, error)
            self.assertEqual(active.read_bytes(), selected_content)
            self.assertNotIn("restore_log", json.loads(output))
            self.assertEqual(list(Path(directory).glob("**/*restore*.json")), [])

    def test_existing_log_is_not_overwritten_and_restore_remains_successful(self) -> None:
        with TemporaryDirectory() as directory:
            config, active, selected, selected_content = self._difference(directory)
            database = Path(directory) / "index.sqlite3"
            restore_log = Path(directory) / "restore.json"
            restore_log.write_text("vorhanden", encoding="utf-8")

            code, output, error = self._cli(
                [
                    "index",
                    "backups",
                    "restore",
                    str(database),
                    str(selected),
                    "--config-directory",
                    str(config),
                    "--confirm-name",
                    selected.name,
                    "--yes",
                    "--restore-log",
                    str(restore_log),
                    "--json",
                ]
            )

            self.assertEqual(code, 1, error)
            payload = json.loads(output)
            self.assertEqual(active.read_bytes(), selected_content)
            self.assertEqual(restore_log.read_text(encoding="utf-8"), "vorhanden")
            self.assertIsNone(payload["restore_log"])
            self.assertIn("existiert bereits", payload["restore_log_error"])


if __name__ == "__main__":
    unittest.main()
