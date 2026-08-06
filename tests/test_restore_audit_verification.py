from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from datenbanktool.cli import main as cli_main
from datenbanktool.core.config_backups import create_config_backup
from datenbanktool.core.config_restore import restore_config_backup
from datenbanktool.core.presets import save_preset
from datenbanktool.core.restore_audit import (
    verify_restore_audit_log,
    write_restore_audit_log,
)
from datenbanktool.core.search import SearchFilter


class RestoreAuditVerificationTests(unittest.TestCase):
    def _cli(self, arguments: list[str]) -> tuple[int, str, str]:
        output = StringIO()
        error = StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            code = cli_main(["--color", "never", *arguments])
        return code, output.getvalue(), error.getvalue()

    def _prepared_audit(
        self,
        directory: str,
    ) -> tuple[Path, Path, Path, Path, Path]:
        config = Path(directory) / "config"
        config.mkdir()
        active = config / "search-presets.json"
        save_preset(
            "Beispiel",
            SearchFilter(text="ursprünglicher Sicherungsstand"),
            path=active,
        )
        selected = Path(create_config_backup(active).backup)
        save_preset(
            "Beispiel",
            SearchFilter(text="späterer aktiver Stand"),
            path=active,
            replace=True,
        )
        database = Path(directory) / "index.sqlite3"
        restored = restore_config_backup(
            database,
            selected,
            confirm_name=selected.name,
            yes=True,
            config_directory=config,
        )
        rollback = Path(restored.rollback_backup.backup)
        protocol = Path(directory) / "nachweise" / "restore.json"
        write_restore_audit_log(restored, protocol)
        return protocol, active, selected, rollback, database

    def test_valid_protocol_and_three_files_are_confirmed_without_changes(self) -> None:
        with TemporaryDirectory() as directory:
            protocol, active, selected, rollback, _ = self._prepared_audit(directory)
            paths = (protocol, active, selected, rollback)
            before = {path: path.read_bytes() for path in paths}
            entries_before = {path for path in Path(directory).rglob("*")}

            result = verify_restore_audit_log(protocol)

            self.assertEqual(result.status_level, "green")
            self.assertTrue(result.all_files_match)
            self.assertEqual(result.matching_count, 3)
            self.assertEqual(result.missing_count, 0)
            self.assertEqual(result.mismatch_count, 0)
            self.assertEqual(len(result.files), 3)
            self.assertEqual({item.state for item in result.files}, {"match"})
            self.assertEqual({path: path.read_bytes() for path in paths}, before)
            self.assertEqual({path for path in Path(directory).rglob("*")}, entries_before)

    def test_changed_existing_file_is_reported_as_hash_mismatch(self) -> None:
        with TemporaryDirectory() as directory:
            protocol, active, _, _, _ = self._prepared_audit(directory)
            protocol_before = protocol.read_bytes()
            active.write_bytes(b"bewusst veraendert")

            result = verify_restore_audit_log(protocol)

            self.assertEqual(result.status_level, "red")
            self.assertFalse(result.all_files_match)
            self.assertEqual(result.mismatch_count, 1)
            active_check = next(item for item in result.files if item.role == "active_after_restore")
            self.assertEqual(active_check.state, "mismatch")
            self.assertNotEqual(active_check.actual_sha256, active_check.expected_sha256)
            self.assertEqual(protocol.read_bytes(), protocol_before)

    def test_missing_file_keeps_protocol_valid_but_verification_incomplete(self) -> None:
        with TemporaryDirectory() as directory:
            protocol, _, selected, _, _ = self._prepared_audit(directory)
            selected.unlink()

            result = verify_restore_audit_log(protocol)

            self.assertEqual(result.status_level, "yellow")
            self.assertFalse(result.all_files_match)
            self.assertEqual(result.missing_count, 1)
            selected_check = next(item for item in result.files if item.role == "selected_backup")
            self.assertEqual(selected_check.state, "missing")
            self.assertIsNone(selected_check.actual_sha256)

    def test_fixed_schema_utc_paths_and_hashes_are_strictly_validated(self) -> None:
        with TemporaryDirectory() as directory:
            protocol, _, _, _, _ = self._prepared_audit(directory)
            valid = json.loads(protocol.read_text(encoding="utf-8"))

            cases: dict[str, dict[str, object]] = {}

            extra = deepcopy(valid)
            extra["configuration_content"] = {"secret": "nicht zulässig"}
            cases["Zusatzfeld"] = extra

            local_time = deepcopy(valid)
            local_time["created_utc"] = "2026-08-05T12:00:00+02:00"
            cases["Nicht-UTC"] = local_time

            wrong_order = deepcopy(valid)
            wrong_order["created_utc"] = "2000-01-01T00:00:00+00:00"
            cases["Zeitreihenfolge"] = wrong_order

            relative = deepcopy(valid)
            relative["active_file"] = "relative/search-presets.json"
            cases["Relativer Pfad"] = relative

            duplicate = deepcopy(valid)
            duplicate["selected_backup"] = duplicate["active_file"]
            cases["Doppelter Pfad"] = duplicate

            missing_hash = deepcopy(valid)
            del missing_hash["sha256"]["rollback_backup"]
            cases["Fehlende Hashrolle"] = missing_hash

            uppercase_hash = deepcopy(valid)
            uppercase_hash["sha256"]["selected_backup"] = (
                uppercase_hash["sha256"]["selected_backup"].upper()
            )
            cases["Großgeschriebener Hash"] = uppercase_hash

            for label, payload in cases.items():
                with self.subTest(label=label):
                    invalid = Path(directory) / f"ungueltig-{len(label)}-{label}.json"
                    invalid.write_text(
                        json.dumps(payload, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    with self.assertRaises(ValueError):
                        verify_restore_audit_log(invalid)

    def test_protocol_symlink_is_rejected_without_following_it(self) -> None:
        with TemporaryDirectory() as directory:
            protocol, _, _, _, _ = self._prepared_audit(directory)
            target_before = protocol.read_bytes()
            link = Path(directory) / "protokoll-link.json"
            link.symlink_to(protocol)

            with self.assertRaises(ValueError):
                verify_restore_audit_log(link)

            self.assertTrue(link.is_symlink())
            self.assertEqual(protocol.read_bytes(), target_before)

    def test_terminal_and_json_cli_are_read_only_and_use_clear_exit_codes(self) -> None:
        with TemporaryDirectory() as directory:
            protocol, active, _, _, _ = self._prepared_audit(directory)
            before = protocol.read_bytes()

            code, output, error = self._cli(
                ["index", "backups", "verify-log", str(protocol)]
            )
            self.assertEqual(code, 0, error)
            self.assertIn("vollständig lesende Prüfung", output)
            self.assertIn("Protokoll und alle drei Dateien bestätigt", output)
            self.assertIn("keine Datei verändert oder gelöscht", output)
            self.assertEqual(protocol.read_bytes(), before)

            code, output, error = self._cli(
                ["index", "backups", "verify-log", str(protocol), "--json"]
            )
            self.assertEqual(code, 0, error)
            payload = json.loads(output)
            self.assertTrue(payload["read_only"])
            self.assertTrue(payload["all_files_match"])
            self.assertEqual(payload["file_count"], 3)
            self.assertEqual(payload["matching_count"], 3)
            self.assertNotIn("\x1b[", output)

            active.write_bytes(b"abweichung")
            code, output, error = self._cli(
                ["index", "backups", "verify-log", str(protocol), "--json"]
            )
            self.assertEqual(code, 1, error)
            payload = json.loads(output)
            self.assertFalse(payload["all_files_match"])
            self.assertEqual(payload["mismatch_count"], 1)
            self.assertEqual(protocol.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
