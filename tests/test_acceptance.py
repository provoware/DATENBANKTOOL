from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from datenbanktool.cli import build_parser
from datenbanktool.cli_contract import CommandPolicy
from datenbanktool.core.acceptance import AcceptanceProfile, run_acceptance


class AcceptanceTests(unittest.TestCase):
    def _profile(self) -> AcceptanceProfile:
        return AcceptanceProfile(
            name="test",
            file_count=48,
            folder_count=6,
            max_sparse_file_bytes=4096,
            max_seconds=30.0,
            max_python_memory_mib=128,
            description="Kleines automatisiertes Testprofil.",
        )

    def test_reproducible_acceptance_creates_reports_and_preserves_sources(self) -> None:
        with TemporaryDirectory() as directory:
            workspace = Path(directory) / "acceptance"
            result = run_acceptance(self._profile(), workspace, seed=12345)
            self.assertTrue(result.passed)
            self.assertEqual(result.file_count, 48)
            self.assertEqual(result.imported_count, 48)
            self.assertEqual(result.index_error_count, 0)
            self.assertEqual(result.manual_novice_status, "pending-real-person")
            self.assertTrue(Path(result.json_report).is_file())
            self.assertTrue(Path(result.markdown_report).is_file())
            self.assertTrue(Path(result.novice_checklist).is_file())
            self.assertTrue(
                (workspace / "ordneruebersicht.csv")
                .read_bytes()
                .startswith(b"\xef\xbb\xbf")
            )
            payload = json.loads(Path(result.json_report).read_text(encoding="utf-8"))
            self.assertTrue(payload["passed"])
            self.assertEqual(payload["seed"], 12345)
            self.assertEqual(payload["manual_novice_status"], "pending-real-person")
            checklist = Path(result.novice_checklist).read_text(encoding="utf-8")
            self.assertIn("Noch nicht durch eine reale Testperson", checklist)
            self.assertIn("Abnahmekriterien", checklist)
            self.assertTrue(
                next(
                    check.passed
                    for check in result.checks
                    if check.name == "Quelldateien unverändert"
                )
            )

    def test_existing_workspace_is_never_reused_or_overwritten(self) -> None:
        with TemporaryDirectory() as directory:
            workspace = Path(directory) / "existing"
            workspace.mkdir()
            marker = workspace / "behalten.txt"
            marker.write_text("unverändert", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                run_acceptance(self._profile(), workspace)
            self.assertEqual(marker.read_text(encoding="utf-8"), "unverändert")

    def test_cli_policy_declares_only_reports_and_synthetic_test_data(self) -> None:
        namespace = build_parser().parse_args(
            [
                "acceptance",
                "--profile",
                "quick",
                "--workspace",
                "/tmp/neue-abnahme",
            ]
        )
        self.assertIsInstance(namespace._policy, CommandPolicy)
        self.assertTrue(namespace._policy.writes_reports)
        self.assertTrue(namespace._policy.writes_test_data)
        self.assertFalse(namespace._policy.reads_original_files)
        self.assertFalse(namespace._policy.writes_original_files)
        self.assertFalse(namespace._policy.writes_index)


if __name__ == "__main__":
    unittest.main()
