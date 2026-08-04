from __future__ import annotations

import json
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path

import datenbanktool

ROOT = Path(__file__).resolve().parents[1]


class VersionRegistryTests(unittest.TestCase):
    def test_versions_do_not_drift(self) -> None:
        registry = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
        project_registry = json.loads((ROOT / "project_registry.json").read_text(encoding="utf-8"))
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        developer_docs = (ROOT / "ENTWICKLERDOKU.md").read_text(encoding="utf-8")

        package_version = "0.13.0a1"
        display_version = "0.13.0-alpha.1"

        self.assertEqual(registry["version"], package_version)
        self.assertEqual(registry["display_version"], display_version)
        self.assertEqual(project_registry["package_version"], package_version)
        self.assertEqual(project_registry["version"], display_version)
        self.assertEqual(pyproject["project"]["version"], package_version)
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
