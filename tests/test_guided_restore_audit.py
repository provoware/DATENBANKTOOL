from __future__ import annotations

import hashlib
from io import StringIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from datenbanktool.core.config_backups import create_config_backup
from datenbanktool.core.presets import save_preset
from datenbanktool.core.search import SearchFilter
from datenbanktool.core.terminal_home_restore_audit import TerminalHome


class GuidedRestoreAuditTests(unittest.TestCase):
    def _prepared_restore(self, directory: str) -> tuple[Path, Path]:
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
        return Path(directory) / "index.sqlite3", backup

    def test_guided_restore_appends_only_explicit_new_log_path(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": directory, "XDG_STATE_HOME": directory},
        ):
            database, backup = self._prepared_restore(directory)
            log_path = Path(directory) / "nachweise" / "restore.json"
            calls: list[list[str]] = []
            output = StringIO()
            errors = StringIO()
            home = TerminalHome(
                lambda command: calls.append(list(command)) or 0,
                input_stream=StringIO(
                    f"7\nwiederherstellen\n{database}\n1\n{backup.name}\n{log_path}\nj\n0\n"
                ),
                output_stream=output,
                error_stream=errors,
                color_mode="never",
            )

            self.assertEqual(home.run(), 0)
            self.assertEqual(
                calls,
                [[
                    "index",
                    "backups",
                    "restore",
                    str(database),
                    str(backup),
                    "--confirm-name",
                    backup.name,
                    "--yes",
                    "--restore-log",
                    str(log_path),
                ]],
            )
            self.assertIn(f"Neuer Wiederherstellungsprotokollpfad: {log_path}", output.getvalue())
            self.assertFalse(log_path.exists())
            self.assertEqual(errors.getvalue(), "")

    def test_guided_restore_blank_or_existing_path_never_adds_restore_log(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": directory, "XDG_STATE_HOME": directory},
        ):
            database, backup = self._prepared_restore(directory)
            existing = Path(directory) / "vorhanden.json"
            existing.write_bytes(b"unveraendert")
            calls: list[list[str]] = []
            errors = StringIO()
            home = TerminalHome(
                lambda command: calls.append(list(command)) or 0,
                input_stream=StringIO(
                    f"7\nwiederherstellen\n{database}\n1\n{backup.name}\n{existing}\n\nj\n0\n"
                ),
                output_stream=StringIO(),
                error_stream=errors,
                color_mode="never",
            )

            self.assertEqual(home.run(), 0)
            self.assertEqual(len(calls), 1)
            self.assertNotIn("--restore-log", calls[0])
            self.assertEqual(existing.read_bytes(), b"unveraendert")
            self.assertIn("existiert bereits", errors.getvalue())

    def test_guided_protocol_verification_uses_exact_path_and_optional_pin(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": directory, "XDG_STATE_HOME": directory},
        ):
            protocol = Path(directory) / "restore.json"
            protocol.write_bytes(b'{"schema_version": 1}\n')
            expected = hashlib.sha256(protocol.read_bytes()).hexdigest()
            calls: list[list[str]] = []
            output = StringIO()
            home = TerminalHome(
                lambda command: calls.append(list(command)) or 0,
                input_stream=StringIO(
                    f"7\nprotokoll prüfen\n{protocol}\n{expected}\nj\n0\n"
                ),
                output_stream=output,
                error_stream=StringIO(),
                color_mode="never",
            )

            self.assertEqual(home.run(), 0)
            self.assertEqual(
                calls,
                [[
                    "index",
                    "backups",
                    "verify-log",
                    str(protocol),
                    "--expected-protocol-sha256",
                    expected,
                ]],
            )
            text = output.getvalue()
            self.assertIn(f"Vollständiger Protokollpfad: {protocol}", text)
            self.assertIn(f"Erwartete Protokoll-SHA-256: {expected}", text)
            self.assertNotIn("Indexdatei angeben", text)
            self.assertEqual(protocol.read_bytes(), b'{"schema_version": 1}\n')

    def test_guided_protocol_verification_can_skip_pin(self) -> None:
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": directory, "XDG_STATE_HOME": directory},
        ):
            protocol = Path(directory) / "restore.json"
            protocol.write_text("{}\n", encoding="utf-8")
            calls: list[list[str]] = []
            home = TerminalHome(
                lambda command: calls.append(list(command)) or 0,
                input_stream=StringIO(
                    f"7\nprotokoll prüfen\n{protocol}\n\nj\n0\n"
                ),
                output_stream=StringIO(),
                error_stream=StringIO(),
                color_mode="never",
            )

            self.assertEqual(home.run(), 0)
            self.assertEqual(
                calls,
                [["index", "backups", "verify-log", str(protocol)]],
            )


if __name__ == "__main__":
    unittest.main()
