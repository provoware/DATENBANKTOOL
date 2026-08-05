from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

import datenbanktool

ROOT = Path(__file__).resolve().parents[1]


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^\[project\]\s+.*?^version\s*=\s*\"([^\"]+)\"",
        text,
    )
    if match is None:
        raise AssertionError("[project].version fehlt in pyproject.toml")
    return match.group(1)


class VersionRegistryTests(unittest.TestCase):
    def test_versions_do_not_drift(self) -> None:
        registry = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
        project_registry = json.loads(
            (ROOT / "project_registry.json").read_text(encoding="utf-8")
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        developer_docs = (ROOT / "ENTWICKLERDOKU.md").read_text(encoding="utf-8")

        package_version = str(registry["version"])
        display_version = str(registry["display_version"])

        self.assertRegex(package_version, r"^\d+\.\d+\.\d+(?:a\d+)?$")
        self.assertRegex(display_version, r"^\d+\.\d+\.\d+-alpha\.\d+$")
        self.assertEqual(project_registry["package_version"], package_version)
        self.assertEqual(project_registry["version"], display_version)
        self.assertEqual(_pyproject_version(), package_version)
        self.assertEqual(datenbanktool.__version__, package_version)
        self.assertIn(package_version, readme)
        self.assertIn(display_version, readme)
        self.assertIn(package_version, developer_docs)
        self.assertIn(display_version, developer_docs)

        result = subprocess.run(
            [sys.executable, "-m", "datenbanktool", "--version"],
            check=True,
            cwd=ROOT,
            env={"PYTHONPATH": "src"},
            text=True,
            stdout=subprocess.PIPE,
        )
        self.assertEqual(result.stdout.strip(), package_version)


if __name__ == "__main__":
    unittest.main()
