from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

from datenbanktool.cli import build_parser
from datenbanktool.cli_contract import (
    GLOBAL_CLI_RULES,
    CommandPolicy,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "datenbanktool"
RULES_PATH = ROOT / "maintenance_rules.json"


class CliArchitectureTests(unittest.TestCase):
    def test_global_rules_manifest_is_versioned_and_complete(self) -> None:
        payload = json.loads(RULES_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["scope"], "global")
        self.assertEqual(payload["status"], "enforced")
        identifiers = [rule["id"] for rule in payload["rules"]]
        self.assertGreaterEqual(len(identifiers), 12)
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertGreaterEqual(len(GLOBAL_CLI_RULES), 12)

    def test_cli_entry_and_modules_stay_below_global_limits(self) -> None:
        payload = json.loads(RULES_PATH.read_text(encoding="utf-8"))
        limits = payload["limits"]
        entry_lines = len((PACKAGE / "cli.py").read_text(encoding="utf-8").splitlines())
        self.assertLessEqual(entry_lines, limits["cli_entry_max_lines"])
        for path in sorted(PACKAGE.glob("cli_*.py")):
            module_lines = len(path.read_text(encoding="utf-8").splitlines())
            self.assertLessEqual(
                module_lines,
                limits["cli_module_max_lines"],
                f"{path.name} ist erneut zu groß",
            )

    def test_cli_modules_do_not_import_cli_or_execute_shell_code(self) -> None:
        for path in sorted(PACKAGE.glob("cli_*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(
                        node.module,
                        "datenbanktool.cli",
                        f"Zyklischer CLI-Import in {path.name}",
                    )
                if isinstance(node, ast.Import):
                    imported = {alias.name for alias in node.names}
                    self.assertNotIn("subprocess", imported, path.name)
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        self.assertNotIn(node.func.id, {"eval", "exec"}, path.name)
                    if isinstance(node.func, ast.Attribute):
                        self.assertFalse(
                            isinstance(node.func.value, ast.Name)
                            and node.func.value.id == "os"
                            and node.func.attr == "system",
                            path.name,
                        )
                    for keyword in node.keywords:
                        if keyword.arg == "shell":
                            self.assertNotEqual(
                                getattr(keyword.value, "value", None),
                                True,
                                path.name,
                            )

    def test_all_public_commands_bind_handler_and_policy(self) -> None:
        parser = build_parser()
        commands = (
            ["check"],
            ["explain"],
            ["scan", "/tmp"],
            ["acceptance", "--workspace", "/tmp/neue-abnahme"],
            ["index", "build", "/tmp", "--database", "/tmp/index.sqlite3"],
            ["index", "rescan", "/tmp", "--database", "/tmp/index.sqlite3"],
            ["index", "recovery"],
            ["index", "status", "/tmp/index.sqlite3"],
            ["index", "sessions", "/tmp/index.sqlite3"],
            ["index", "search", "/tmp/index.sqlite3"],
            ["index", "folders", "/tmp/index.sqlite3"],
            ["index", "folder-compare", "/tmp/index.sqlite3"],
            ["index", "folder-timeline", "/tmp/index.sqlite3", "musik"],
            ["index", "changes", "/tmp/index.sqlite3"],
            ["index", "presets", "list"],
            ["index", "presets", "show", "beispiel"],
            ["index", "presets", "save", "beispiel"],
            ["index", "presets", "delete", "beispiel"],
            ["index", "timeline-presets", "list"],
            ["index", "timeline-presets", "show", "beispiel"],
            ["index", "timeline-presets", "save", "beispiel", "Musik"],
            ["index", "timeline-presets", "delete", "beispiel"],
            ["index", "backup", "/tmp/index.sqlite3"],
            ["index", "backups", "list", "/tmp/index.sqlite3"],
            [
                "index",
                "backups",
                "compare",
                "/tmp/index.sqlite3",
                "/tmp/search-presets.json.backup-test.json",
            ],
            [
                "index",
                "backups",
                "restore",
                "/tmp/index.sqlite3",
                "/tmp/search-presets.json.backup-test.json",
                "--confirm-name",
                "search-presets.json.backup-test.json",
                "--yes",
            ],
            ["index", "backups", "verify-log", "/tmp/restore.json"],
            [
                "index",
                "backups",
                "delete",
                "/tmp/index.sqlite3",
                "/tmp/index.sqlite3.backup-20260805.sqlite3",
                "--confirm-name",
                "index.sqlite3.backup-20260805.sqlite3",
                "--yes",
            ],
            [
                "index",
                "restore",
                "/tmp/index.sqlite3",
                "--backup",
                "/tmp/backup.sqlite3",
            ],
            ["index", "repair", "/tmp/index.sqlite3"],
            ["report", "/tmp/index.sqlite3"],
        )
        for command in commands:
            with self.subTest(command=command):
                namespace = parser.parse_args(command)
                self.assertTrue(callable(namespace._handler))
                self.assertIsInstance(namespace._policy, CommandPolicy)
                namespace._policy.validate()

    def test_original_file_write_policy_is_rejected(self) -> None:
        policy = CommandPolicy(
            "unsicher",
            writes_original_files=True,
        )
        with self.assertRaises(ValueError):
            policy.validate()

    def test_command_ownership_matches_module_boundaries(self) -> None:
        parser = build_parser()
        expected = {
            ("check",): "datenbanktool.cli_check",
            ("scan", "/tmp"): "datenbanktool.cli_scan",
            (
                "acceptance",
                "--workspace",
                "/tmp/neue-abnahme",
            ): "datenbanktool.cli_acceptance",
            ("index", "recovery"): "datenbanktool.cli_recovery",
            ("index", "search", "/tmp/index.sqlite3"): "datenbanktool.cli_search",
            ("index", "folders", "/tmp/index.sqlite3"): "datenbanktool.cli_reports",
            (
                "index",
                "folder-compare",
                "/tmp/index.sqlite3",
            ): "datenbanktool.cli_folder_compare",
            (
                "index",
                "folder-timeline",
                "/tmp/index.sqlite3",
                "musik",
            ): "datenbanktool.cli_folder_timeline",
            (
                "index",
                "timeline-presets",
                "list",
            ): "datenbanktool.cli_timeline_presets",
            (
                "index",
                "backups",
                "list",
                "/tmp/index.sqlite3",
            ): "datenbanktool.cli_backups",
            (
                "index",
                "backups",
                "compare",
                "/tmp/index.sqlite3",
                "/tmp/search-presets.json.backup-test.json",
            ): "datenbanktool.cli_backups",
            (
                "index",
                "backups",
                "restore",
                "/tmp/index.sqlite3",
                "/tmp/search-presets.json.backup-test.json",
                "--confirm-name",
                "search-presets.json.backup-test.json",
                "--yes",
            ): "datenbanktool.cli_backups",
            (
                "index",
                "backups",
                "verify-log",
                "/tmp/restore.json",
            ): "datenbanktool.cli_restore_audit",
            (
                "index",
                "build",
                "/tmp",
                "--database",
                "/tmp/index.sqlite3",
            ): "datenbanktool.cli_index",
            ("explain",): "datenbanktool.cli_help",
        }
        for command, module in expected.items():
            with self.subTest(command=command):
                namespace = parser.parse_args(list(command))
                self.assertEqual(namespace._handler.__module__, module)


if __name__ == "__main__":
    unittest.main()
