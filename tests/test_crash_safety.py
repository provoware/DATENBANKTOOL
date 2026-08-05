from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from datenbanktool.cli import build_parser, main as cli_main
from datenbanktool.core.diagnostics import run_diagnostics
from datenbanktool.core.durable_files import atomic_write_text
from datenbanktool.core.index_database import IndexBuildOptions, IndexDatabase, build_index
from datenbanktool.core.run_journal import RunJournal, previous_unfinished_run
from datenbanktool.entrypoint import main as entrypoint_main


class DurableFileTests(unittest.TestCase):
    def test_existing_file_is_kept_without_explicit_overwrite(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "state.json"
            target.write_text("alt\n", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                atomic_write_text(target, "neu\n")
            self.assertEqual(target.read_text(encoding="utf-8"), "alt\n")

    def test_failed_publish_keeps_old_file_and_removes_temporary_file(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "state.json"
            target.write_text("alt\n", encoding="utf-8")
            with patch(
                "datenbanktool.core.durable_files.os.replace",
                side_effect=OSError("simulierter Ausfall"),
            ):
                with self.assertRaises(OSError):
                    atomic_write_text(target, "neu\n", overwrite=True)
            self.assertEqual(target.read_text(encoding="utf-8"), "alt\n")
            self.assertEqual(
                [path for path in Path(directory).iterdir() if ".tmp-" in path.name],
                [],
            )

    def test_private_mode_and_complete_content_are_published(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "private.json"
            atomic_write_text(target, "vollständig\n", mode=0o600)
            self.assertEqual(target.read_text(encoding="utf-8"), "vollständig\n")
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)


class RunJournalTests(unittest.TestCase):
    def test_arguments_are_redacted_and_failure_report_is_durable(self) -> None:
        with TemporaryDirectory() as directory:
            state = Path(directory)
            journal = RunJournal.begin(
                ["check", "--token", "privat", "--password=geheim"],
                version="test",
                state_directory=state,
            )
            payload = json.loads(journal.path.read_text(encoding="utf-8"))
            self.assertNotIn("privat", json.dumps(payload))
            self.assertNotIn("geheim", json.dumps(payload))
            report = journal.unexpected_failure(RuntimeError("kaputt"))
            self.assertIsNotNone(report)
            report_payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(report_payload["exit_code"], 70)
            self.assertIn("RuntimeError", report_payload["technical_error"])

    def test_current_process_is_not_reported_as_previous_crash(self) -> None:
        with TemporaryDirectory() as directory:
            state = Path(directory)
            RunJournal.begin(["check"], version="test", state_directory=state)
            self.assertIsNone(
                previous_unfinished_run(state, ignore_process_id=os.getpid())
            )


class RecoveryBoundaryTests(unittest.TestCase):
    def test_unexpected_exception_creates_plain_language_crash_report(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ), patch("datenbanktool.entrypoint.cli.main", side_effect=RuntimeError("boom")):
            error = StringIO()
            code = entrypoint_main(["check"], error_stream=error)
            self.assertEqual(code, 70)
            text = error.getvalue()
            self.assertLess(text.index("unerwartet beendet"), text.index("RuntimeError"))
            self.assertIn("Originaldateien", text)
            reports = list((Path(directory) / "datenbanktool").glob("crash-*.json"))
            self.assertEqual(len(reports), 1)

    def test_keyboard_interrupt_returns_130_and_marks_interrupted(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ), patch("datenbanktool.entrypoint.cli.main", side_effect=KeyboardInterrupt):
            error = StringIO()
            code = entrypoint_main(["check"], error_stream=error)
            self.assertEqual(code, 130)
            self.assertIn("Zwischenstand bleibt erhalten", error.getvalue())
            payload = json.loads(
                (Path(directory) / "datenbanktool" / "last-run.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(payload["status"], "interrupted")


class AutosaveAndDiagnosticTests(unittest.TestCase):
    def test_scan_can_resume_after_controlled_interruption(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            for index in range(4):
                (root / f"datei-{index}.txt").write_text(str(index), encoding="utf-8")
            database = Path(directory) / "index.sqlite3"
            first = build_index(
                IndexBuildOptions(
                    root=root,
                    database=database,
                    max_files=1,
                    autosave_seconds=5.0,
                )
            )
            self.assertEqual(first.status, "interrupted")
            second = build_index(
                IndexBuildOptions(
                    root=root,
                    database=database,
                    resume=True,
                    autosave_seconds=5.0,
                )
            )
            self.assertEqual(second.status, "complete")
            self.assertTrue(second.resumed)
            self.assertEqual(second.imported_count, 4)

    def test_sqlite_uses_full_sync_and_diagnostics_are_read_only(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ):
            root = Path(directory) / "data"
            root.mkdir()
            (root / "datei.txt").write_text("inhalt", encoding="utf-8")
            database = Path(directory) / "index.sqlite3"
            build_index(IndexBuildOptions(root=root, database=database))
            with IndexDatabase(database) as index:
                synchronous = int(index.connection.execute("PRAGMA synchronous").fetchone()[0])
            self.assertEqual(synchronous, 2)
            before = database.read_bytes()
            result = run_diagnostics(database)
            self.assertTrue(result.ready)
            self.assertEqual(database.read_bytes(), before)

    def test_check_command_and_autosave_parser_are_connected(self) -> None:
        parser = build_parser()
        check = parser.parse_args(["check"])
        self.assertEqual(check._policy.name, "check")
        build = parser.parse_args(
            [
                "index",
                "build",
                "/tmp",
                "--database",
                "/tmp/index.sqlite3",
                "--autosave-seconds",
                "2.5",
            ]
        )
        self.assertEqual(build.autosave_seconds, 2.5)

    def test_check_output_uses_plain_language_before_technical_detail(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_STATE_HOME": directory, "XDG_CONFIG_HOME": directory},
        ):
            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                code = cli_main(["check", "--color", "never"])
            self.assertEqual(code, 0)
            text = output.getvalue()
            self.assertLess(text.index("Sicheres Speichern"), text.index("fsync"))


if __name__ == "__main__":
    unittest.main()
