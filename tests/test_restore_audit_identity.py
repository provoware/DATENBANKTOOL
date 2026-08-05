from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from datenbanktool.cli import main as cli_main


class RestoreAuditIdentityTests(unittest.TestCase):
    def _cli(self, arguments: list[str]) -> tuple[int, str, str]:
        output = StringIO()
        error = StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            code = cli_main(["--color", "never", *arguments])
        return code, output.getvalue(), error.getvalue()

    def _protocol(self, directory: str) -> tuple[Path, tuple[Path, ...]]:
        root = Path(directory)
        active = root / "active.json"
        selected = root / "selected.json"
        rollback = root / "rollback.json"
        active.write_bytes(b"restored")
        selected.write_bytes(b"restored")
        rollback.write_bytes(b"previous")
        paths = (active, selected, rollback)
        payload = {
            "schema_version": 1,
            "event": "configuration_restore",
            "created_utc": "2026-08-05T11:00:01+00:00",
            "restore_completed_utc": "2026-08-05T11:00:00+00:00",
            "configuration_kind": "search",
            "active_file": str(active),
            "selected_backup": str(selected),
            "rollback_backup": str(rollback),
            "sha256": {
                "active_after_restore": hashlib.sha256(active.read_bytes()).hexdigest(),
                "selected_backup": hashlib.sha256(selected.read_bytes()).hexdigest(),
                "rollback_backup": hashlib.sha256(rollback.read_bytes()).hexdigest(),
            },
        }
        protocol = root / "restore.json"
        protocol.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return protocol, paths

    def test_matching_pin_is_reported_and_all_files_remain_unchanged(self) -> None:
        with TemporaryDirectory() as directory:
            protocol, paths = self._protocol(directory)
            expected = hashlib.sha256(protocol.read_bytes()).hexdigest()
            before = {path: path.read_bytes() for path in (protocol, *paths)}

            code, output, error = self._cli([
                "index",
                "backups",
                "verify-log",
                str(protocol),
                "--expected-protocol-sha256",
                expected,
                "--json",
            ])

            self.assertEqual(code, 0, error)
            payload = json.loads(output)
            identity = payload["protocol_identity"]
            self.assertEqual(identity["protocol"], str(protocol))
            self.assertEqual(identity["expected_sha256"], expected)
            self.assertEqual(identity["actual_sha256"], expected)
            self.assertTrue(identity["matches"])
            self.assertTrue(payload["all_files_match"])
            self.assertEqual(
                {path: path.read_bytes() for path in (protocol, *paths)},
                before,
            )

    def test_wrong_pin_fails_before_json_schema_evaluation(self) -> None:
        with TemporaryDirectory() as directory:
            protocol = Path(directory) / "ungueltig.json"
            protocol.write_bytes(b"kein json")
            before = protocol.read_bytes()

            with patch(
                "datenbanktool.cli_restore_audit.verify_restore_audit_log"
            ) as schema_verifier:
                code, output, error = self._cli([
                    "index",
                    "backups",
                    "verify-log",
                    str(protocol),
                    "--expected-protocol-sha256",
                    "0" * 64,
                ])

            self.assertEqual(code, 2)
            self.assertEqual(output, "")
            self.assertIn("erwartete SHA-256 stimmt nicht", error)
            schema_verifier.assert_not_called()
            self.assertEqual(protocol.read_bytes(), before)

    def test_invalid_pin_format_is_rejected_without_schema_evaluation(self) -> None:
        with TemporaryDirectory() as directory:
            protocol, _ = self._protocol(directory)
            with patch(
                "datenbanktool.cli_restore_audit.verify_restore_audit_log"
            ) as schema_verifier:
                code, _, error = self._cli([
                    "index",
                    "backups",
                    "verify-log",
                    str(protocol),
                    "--expected-protocol-sha256",
                    "A" * 64,
                ])

            self.assertEqual(code, 2)
            self.assertIn("kleingeschriebener SHA-256", error)
            schema_verifier.assert_not_called()


if __name__ == "__main__":
    unittest.main()
