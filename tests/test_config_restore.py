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
from datenbanktool.core.config_restore import (
    compare_config_backup,
    restore_config_backup,
)
from datenbanktool.core.presets import delete_preset, save_preset
from datenbanktool.core.search import SearchFilter
from datenbanktool.core.terminal_home import TerminalHome
from datenbanktool.core.timeline_presets import (
    delete_timeline_preset,
    save_timeline_preset,
)


class ConfigRestoreTests(unittest.TestCase):
    def _search_difference(
        self,
        directory: str,
    ) -> tuple[Path, Path, Path, bytes]:
        config = Path(directory) / "config"
        config.mkdir()
        active = config / "search-presets.json"
        save_preset("Audio", SearchFilter(text="alt"), path=active)
        save_preset("Archiv", SearchFilter(categories=("archive",)), path=active)
        backup = Path(create_config_backup(active).backup)
        save_preset(
            "Audio",
            SearchFilter(text="neu"),
            path=active,
            replace=True,
        )
        delete_preset("Archiv", path=active)
        save_preset("Neu", SearchFilter(categories=("audio",)), path=active)
        return config, active, backup, active.read_bytes()

    def _cli(self, arguments: list[str]) -> tuple[int, str, str]:
        output = StringIO()
        error = StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            code = cli_main(["--color", "never", *arguments])
        return code, output.getvalue(), error.getvalue()

    def test_compare_reports_exact_effects_without_writing(self) -> None:
        with TemporaryDirectory() as directory:
            config, active, backup, active_before = self._search_difference(directory)
            backup_before = backup.read_bytes()
            comparison = compare_config_backup(
                Path(directory) / "index.sqlite3",
                backup,
                config_directory=config,
            )
            self.assertEqual(comparison.kind, "search")
            self.assertEqual(comparison.add_names, ("Archiv",))
            self.assertEqual(comparison.remove_names, ("Neu",))
            self.assertEqual(comparison.change_names, ("Audio",))
            self.assertFalse(comparison.identical)
            self.assertTrue(comparison.can_restore)
            self.assertEqual(active.read_bytes(), active_before)
            self.assertEqual(backup.read_bytes(), backup_before)

    def test_timeline_backup_is_compared_with_timeline_active_file(self) -> None:
        with TemporaryDirectory() as directory:
            config = Path(directory) / "config"
            config.mkdir()
            active = config / "timeline-presets.json"
            save_timeline_preset("Musik", "Musik/Alt", path=active)
            save_timeline_preset("Bilder", "Bilder", path=active)
            backup = Path(create_config_backup(active).backup)
            save_timeline_preset(
                "Musik",
                "Musik/Neu",
                path=active,
                replace=True,
            )
            delete_timeline_preset("Bilder", path=active)
            comparison = compare_config_backup(
                Path(directory) / "index.sqlite3",
                backup,
                config_directory=config,
            )
            self.assertEqual(comparison.kind, "timeline")
            self.assertEqual(comparison.add_names, ("Bilder",))
            self.assertEqual(comparison.change_names, ("Musik",))
            self.assertEqual(comparison.remove_names, ())

    def test_restore_creates_verified_rollback_and_keeps_both_backups(self) -> None:
        with TemporaryDirectory() as directory:
            config, active, backup, active_before = self._search_difference(directory)
            selected_content = backup.read_bytes()
            result = restore_config_backup(
                Path(directory) / "index.sqlite3",
                backup,
                confirm_name=backup.name,
                yes=True,
                config_directory=config,
            )
            rollback = Path(result.rollback_backup.backup)
            self.assertEqual(active.read_bytes(), selected_content)
            self.assertEqual(rollback.read_bytes(), active_before)
            self.assertTrue(backup.exists())
            self.assertTrue(rollback.exists())
            self.assertEqual(rollback.stat().st_mode & 0o777, 0o600)
            self.assertEqual(active.stat().st_mode & 0o777, 0o600)
            backups = list(config.glob("search-presets.json.backup-*.json"))
            self.assertEqual(len(backups), 2)

    def test_restore_requires_yes_exact_name_and_real_change(self) -> None:
        with TemporaryDirectory() as directory:
            config, active, backup, _ = self._search_difference(directory)
            database = Path(directory) / "index.sqlite3"
            with self.assertRaisesRegex(ValueError, "--yes"):
                restore_config_backup(
                    database,
                    backup,
                    confirm_name=backup.name,
                    yes=False,
                    config_directory=config,
                )
            with self.assertRaisesRegex(ValueError, "nicht exakt"):
                restore_config_backup(
                    database,
                    backup,
                    confirm_name="falsch.json",
                    yes=True,
                    config_directory=config,
                )
            restore_config_backup(
                database,
                backup,
                confirm_name=backup.name,
                yes=True,
                config_directory=config,
            )
            count = len(list(config.glob("search-presets.json.backup-*.json")))
            with self.assertRaisesRegex(ValueError, "bereits identisch"):
                restore_config_backup(
                    database,
                    backup,
                    confirm_name=backup.name,
                    yes=True,
                    config_directory=config,
                )
            self.assertEqual(
                len(list(config.glob("search-presets.json.backup-*.json"))),
                count,
            )
            self.assertEqual(active.read_bytes(), backup.read_bytes())

    def test_unknown_corrupt_and_index_backups_are_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            config = Path(directory) / "config"
            config.mkdir()
            active = config / "search-presets.json"
            save_preset("Audio", SearchFilter(text="ok"), path=active)
            database = Path(directory) / "index.sqlite3"

            unknown = config / "manuell.json"
            unknown.write_text('{"schema_version": 1, "presets": []}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "geprüften Sicherungsübersicht"):
                compare_config_backup(database, unknown, config_directory=config)

            corrupt = config / "search-presets.json.backup-kaputt.json"
            corrupt.write_text("{kaputt", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nicht als geprüft"):
                compare_config_backup(database, corrupt, config_directory=config)

            index_backup = Path(directory) / "index.sqlite3.backup-test.sqlite3"
            index_backup.write_bytes(b"keine sqlite datei")
            with self.assertRaisesRegex(ValueError, "Nur geprüfte Such"):
                compare_config_backup(database, index_backup, config_directory=config)

    def test_failed_postvalidation_restores_active_file_automatically(self) -> None:
        with TemporaryDirectory() as directory:
            config, active, backup, active_before = self._search_difference(directory)
            existing = set(config.glob("search-presets.json.backup-*.json"))
            with patch(
                "datenbanktool.core.config_restore._verify_restored_file",
                side_effect=[ValueError("simulierter Prüffehler"), None],
            ):
                with self.assertRaisesRegex(ValueError, "automatisch"):
                    restore_config_backup(
                        Path(directory) / "index.sqlite3",
                        backup,
                        confirm_name=backup.name,
                        yes=True,
                        config_directory=config,
                    )
            self.assertEqual(active.read_bytes(), active_before)
            self.assertTrue(backup.exists())
            new_backups = set(config.glob("search-presets.json.backup-*.json")) - existing
            self.assertEqual(len(new_backups), 1)
            rollback = new_backups.pop()
            self.assertEqual(rollback.read_bytes(), active_before)

    def test_cli_compare_and_restore_json(self) -> None:
        with TemporaryDirectory() as directory:
            config, active, backup, _ = self._search_difference(directory)
            database = Path(directory) / "index.sqlite3"
            code, output, error = self._cli(
                [
                    "index",
                    "backups",
                    "compare",
                    str(database),
                    str(backup),
                    "--config-directory",
                    str(config),
                    "--json",
                ]
            )
            self.assertEqual(code, 0, error)
            comparison = json.loads(output)
            self.assertEqual(comparison["add_names"], ["Archiv"])
            self.assertEqual(comparison["remove_names"], ["Neu"])

            code, output, error = self._cli(
                [
                    "index",
                    "backups",
                    "restore",
                    str(database),
                    str(backup),
                    "--config-directory",
                    str(config),
                    "--confirm-name",
                    backup.name,
                    "--yes",
                    "--json",
                ]
            )
            self.assertEqual(code, 0, error)
            restored = json.loads(output)
            self.assertEqual(restored["comparison"]["active"], str(active))
            self.assertTrue(Path(restored["rollback_backup"]["backup"]).exists())
            self.assertEqual(active.read_bytes(), backup.read_bytes())

    def test_guided_restore_shows_comparison_and_dispatches_exact_command(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {
                "XDG_CONFIG_HOME": directory,
                "XDG_STATE_HOME": directory,
            },
        ):
            config = Path(directory) / "datenbanktool"
            active = config / "search-presets.json"
            save_preset("Audio", SearchFilter(text="alt"), path=active)
            backup = Path(create_config_backup(active).backup)
            save_preset(
                "Audio",
                SearchFilter(text="neu"),
                path=active,
                replace=True,
            )
            database = Path(directory) / "index.sqlite3"
            calls: list[list[str]] = []
            output = StringIO()
            errors = StringIO()
            home = TerminalHome(
                lambda command: calls.append(list(command)) or 0,
                input_stream=StringIO(
                    f"7\nwiederherstellen\n{database}\n1\n{backup.name}\nj\n0\n"
                ),
                output_stream=output,
                error_stream=errors,
                color_mode="never",
            )
            self.assertEqual(home.run(), 0)
            self.assertEqual(
                calls,
                [
                    [
                        "index",
                        "backups",
                        "restore",
                        str(database),
                        str(backup),
                        "--confirm-name",
                        backup.name,
                        "--yes",
                    ]
                ],
            )
            self.assertIn("Nur-Lese-Vergleich", output.getvalue())
            self.assertIn("Würde ersetzen: Audio", output.getvalue())
            self.assertIn("Rückfallsicherung", output.getvalue())
            self.assertEqual(errors.getvalue(), "")

    def test_guided_restore_rejects_wrong_repeated_name(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {
                "XDG_CONFIG_HOME": directory,
                "XDG_STATE_HOME": directory,
            },
        ):
            config = Path(directory) / "datenbanktool"
            active = config / "timeline-presets.json"
            save_timeline_preset("Musik", "Musik/Alt", path=active)
            create_config_backup(active)
            save_timeline_preset(
                "Musik",
                "Musik/Neu",
                path=active,
                replace=True,
            )
            calls: list[list[str]] = []
            errors = StringIO()
            home = TerminalHome(
                lambda command: calls.append(list(command)) or 0,
                input_stream=StringIO(
                    f"7\nwiederherstellen\n{Path(directory) / 'index.sqlite3'}\n1\nfalsch\n0\n"
                ),
                output_stream=StringIO(),
                error_stream=errors,
                color_mode="never",
            )
            self.assertEqual(home.run(), 0)
            self.assertEqual(calls, [])
            self.assertIn("Sicherungsname stimmt nicht", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
