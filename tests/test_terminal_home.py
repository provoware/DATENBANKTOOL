from __future__ import annotations

from io import StringIO
import unittest

from datenbanktool.core.terminal_home import TerminalHome, menu_actions
from datenbanktool.entrypoint import main as entrypoint_main


class TerminalHomeTests(unittest.TestCase):
    def home(self, user_input: str, runner=None):
        output = StringIO()
        error = StringIO()
        calls = []

        def record(arguments):
            calls.append(list(arguments))
            return 0 if runner is None else runner(arguments)

        home = TerminalHome(
            record,
            input_stream=StringIO(user_input),
            output_stream=output,
            error_stream=error,
            color_mode="never",
        )
        return home, output, error, calls

    def test_menu_keys_are_unique(self) -> None:
        keys = [action.key for action in menu_actions()]
        self.assertEqual(len(keys), len(set(keys)))

    def test_timeline_is_own_menu_action(self) -> None:
        actions = {action.key: action for action in menu_actions()}
        self.assertIn("11", actions)
        self.assertEqual(actions["11"].help_topic, "folder-timeline")
        self.assertEqual(actions["11"].builder_name, "folder_timeline")
        self.assertFalse(actions["11"].confirmation_required)

    def test_invalid_selection_returns_to_menu(self) -> None:
        home, output, error, calls = self.home("99\n0\n")
        self.assertEqual(home.run(), 0)
        self.assertIn("Ungültige Auswahl", error.getvalue())
        self.assertEqual(calls, [])

    def test_search_is_dispatched_as_argument_list(self) -> None:
        home, output, error, calls = self.home(
            "1\n/tmp/mein index.sqlite3\nurlaub bilder\n\n0\n"
        )
        self.assertEqual(home.run(), 0)
        self.assertEqual(
            calls[0],
            ["index", "search", "/tmp/mein index.sqlite3", "urlaub bilder"],
        )
        self.assertIn("'urlaub bilder'", output.getvalue())
        self.assertNotIn("\033[", output.getvalue())

    def test_timeline_is_dispatched_with_validated_fields_and_html(self) -> None:
        home, output, error, calls = self.home(
            "11\n/tmp/index.sqlite3\nMusik/Archiv\n3\n12\n250\nhtml\n"
            "/tmp/musik-verlauf.html\n0\n"
        )
        self.assertEqual(home.run(), 0)
        self.assertEqual(
            calls[0],
            [
                "index",
                "folder-timeline",
                "/tmp/index.sqlite3",
                "Musik/Archiv",
                "--from-session-id",
                "3",
                "--to-session-id",
                "12",
                "--limit",
                "250",
                "--html",
                "/tmp/musik-verlauf.html",
            ],
        )
        self.assertIn("Ordner-Zeitreihe", output.getvalue())
        self.assertIn("--html /tmp/musik-verlauf.html", output.getvalue())
        self.assertEqual(error.getvalue(), "")

    def test_timeline_field_help_and_number_validation(self) -> None:
        home, output, error, calls = self.home(
            "11\n/tmp/index.sqlite3\n?\n.\n\n\n1\n500\n\n0\n"
        )
        self.assertEqual(home.run(), 0)
        self.assertEqual(
            calls[0],
            [
                "index",
                "folder-timeline",
                "/tmp/index.sqlite3",
                ".",
                "--limit",
                "500",
            ],
        )
        self.assertIn("Absolute Pfade", output.getvalue())
        self.assertIn("zwischen 2 und 500", error.getvalue())

    def test_write_action_requires_confirmation(self) -> None:
        home, output, error, calls = self.home(
            "5\n/tmp/daten\n/tmp/index.sqlite3\nn\nn\n0\n"
        )
        self.assertEqual(home.run(), 0)
        self.assertEqual(calls, [])
        self.assertIn("Nicht ausgeführt", output.getvalue())

    def test_confirmed_build_is_dispatched(self) -> None:
        home, output, error, calls = self.home(
            "5\n/tmp/daten\n/tmp/index.sqlite3\nj\nj\n0\n"
        )
        self.assertEqual(home.run(), 0)
        self.assertEqual(
            calls[0],
            [
                "index",
                "build",
                "/tmp/daten",
                "--database",
                "/tmp/index.sqlite3",
                "--hash-duplicates",
            ],
        )

    def test_closed_input_ends_without_loop(self) -> None:
        home, output, error, calls = self.home("")
        self.assertEqual(home.run(), 0)
        self.assertIn("Eingabe beendet", output.getvalue())
        self.assertEqual(calls, [])

    def test_noninteractive_empty_entrypoint_does_not_block(self) -> None:
        output = StringIO()
        result = entrypoint_main(
            [], input_stream=StringIO(), output_stream=output, error_stream=StringIO()
        )
        self.assertEqual(result, 0)
        self.assertIn("datenbanktool start", output.getvalue())

    def test_explicit_start_can_exit_immediately(self) -> None:
        output = StringIO()
        result = entrypoint_main(
            ["start", "--color", "never"],
            input_stream=StringIO("0\n"),
            output_stream=output,
            error_stream=StringIO(),
        )
        self.assertEqual(result, 0)
        self.assertIn("geführte Startseite", output.getvalue())


if __name__ == "__main__":
    unittest.main()
