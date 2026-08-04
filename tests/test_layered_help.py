from __future__ import annotations

from io import StringIO
import unittest

from datenbanktool.core.layered_help import (
    find_topics,
    get_topic,
    render_topic,
)
from datenbanktool.core.terminal_home import TerminalHome
from datenbanktool.help_command import run_help_command


class LayeredHelpTests(unittest.TestCase):
    def home(self, user_input: str, result: int = 0):
        output = StringIO()
        error = StringIO()
        calls: list[list[str]] = []

        def run(arguments):
            calls.append(list(arguments))
            return result

        home = TerminalHome(
            run,
            input_stream=StringIO(user_input),
            output_stream=output,
            error_stream=error,
            color_mode="never",
        )
        return home, output, error, calls

    def test_help_layers_increase_detail(self) -> None:
        topic = get_topic("build")
        quick = render_topic(topic, "quick")
        detail = render_topic(topic, "detail")
        guided = render_topic(topic, "guided")
        self.assertLess(len(quick), len(detail))
        self.assertLess(len(detail), len(guided))
        self.assertTrue(any("Schritt für Schritt" in line for line in guided))

    def test_help_search_accepts_everyday_word(self) -> None:
        matches = find_topics("Platzfresser")
        self.assertTrue(matches)
        self.assertEqual(matches[0].name, "folders")

    def test_detail_selection_does_not_start_action(self) -> None:
        home, output, error, calls = self.home("?5\n0\n")
        self.assertEqual(home.run(), 0)
        self.assertEqual(calls, [])
        self.assertIn("Vorher prüfen", output.getvalue())

    def test_guided_selection_shows_steps(self) -> None:
        home, output, error, calls = self.home("g5\n0\n")
        self.assertEqual(home.run(), 0)
        self.assertEqual(calls, [])
        self.assertIn("Schritt für Schritt", output.getvalue())

    def test_timeline_and_preset_help_are_connected(self) -> None:
        home, output, error, calls = self.home("?11\ng11\n?12\ng12\n0\n")
        self.assertEqual(home.run(), 0)
        self.assertEqual(calls, [])
        text = output.getvalue()
        self.assertIn("Ordner-Zeitreihe", text)
        self.assertIn("Absolute Pfade", text)
        self.assertIn("Trendgrenzen", text)
        self.assertIn("Zeitreihen-Vorlage speichern", text)
        self.assertIn("Schritt für Schritt", text)
        self.assertEqual(error.getvalue(), "")

    def test_question_mark_explains_current_field(self) -> None:
        home, output, error, calls = self.home(
            "1\n?\n/tmp/index.sqlite3\n\n\n0\n"
        )
        self.assertEqual(home.run(), 0)
        self.assertIn("Hilfe zu dieser Eingabe", output.getvalue())
        self.assertEqual(calls[0], ["index", "search", "/tmp/index.sqlite3"])

    def test_failed_action_shows_contextual_error_help(self) -> None:
        home, output, error, calls = self.home(
            "4\n/tmp/index.sqlite3\n0\n",
            result=2,
        )
        self.assertEqual(home.run(), 0)
        self.assertEqual(calls[0], ["index", "status", "/tmp/index.sqlite3"])
        self.assertIn("Fehlerhilfe", error.getvalue())
        self.assertIn("--level guided", error.getvalue())

    def test_failed_timeline_shows_specific_error_help(self) -> None:
        home, output, error, calls = self.home(
            "11\n/tmp/index.sqlite3\n.\n\n\n\n\n\n\n0\n",
            result=2,
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
                "100",
            ],
        )
        self.assertIn("Ordner-Zeitreihe wurde mit Fehlercode 2", error.getvalue())
        self.assertIn("mindestens zwei", error.getvalue())
        self.assertIn("folder-timeline --level guided", error.getvalue())

    def test_failed_preset_save_shows_specific_error_help(self) -> None:
        home, output, error, calls = self.home(
            "12\nMusik\nMusik/Archiv\nWöchentlich\nj\n0\n",
            result=2,
        )
        self.assertEqual(home.run(), 0)
        self.assertEqual(
            calls[0],
            [
                "index",
                "timeline-presets",
                "save",
                "Musik",
                "Musik/Archiv",
                "--description",
                "Wöchentlich",
            ],
        )
        self.assertIn("nicht gespeichert", error.getvalue())
        self.assertIn("--replace", error.getvalue())
        self.assertIn("timeline-presets --level guided", error.getvalue())

    def test_standalone_guided_help_command(self) -> None:
        output = StringIO()
        error = StringIO()
        result = run_help_command(
            ["build", "--level", "guided"],
            output_stream=output,
            error_stream=error,
        )
        self.assertEqual(result, 0)
        self.assertIn("Schritt für Schritt", output.getvalue())
        self.assertEqual(error.getvalue(), "")

    def test_standalone_timeline_help_and_search(self) -> None:
        output = StringIO()
        error = StringIO()
        result = run_help_command(
            ["folder-timeline", "--level", "guided"],
            output_stream=output,
            error_stream=error,
        )
        self.assertEqual(result, 0)
        self.assertIn("Ordner-Zeitreihe", output.getvalue())
        self.assertIn("Schritt für Schritt", output.getvalue())
        self.assertIn("Trendgrafiken", output.getvalue())
        self.assertIn("Warnschwelle", output.getvalue())
        self.assertEqual(error.getvalue(), "")

        found = StringIO()
        result = run_help_command(
            ["--find", "Speicherentwicklung"],
            output_stream=found,
            error_stream=StringIO(),
        )
        self.assertEqual(result, 0)
        self.assertIn("folder-timeline", found.getvalue())

    def test_standalone_preset_help_and_search(self) -> None:
        output = StringIO()
        result = run_help_command(
            ["timeline-presets", "--level", "guided"],
            output_stream=output,
            error_stream=StringIO(),
        )
        self.assertEqual(result, 0)
        self.assertIn("Zeitreihen-Vorlage speichern", output.getvalue())
        self.assertIn("überschrieben", output.getvalue())

        found = StringIO()
        result = run_help_command(
            ["--find", "häufiger Ordner"],
            output_stream=found,
            error_stream=StringIO(),
        )
        self.assertEqual(result, 0)
        self.assertIn("timeline-presets", found.getvalue())

    def test_standalone_help_finds_topic(self) -> None:
        output = StringIO()
        error = StringIO()
        result = run_help_command(
            ["--find", "große Ordner"],
            output_stream=output,
            error_stream=error,
        )
        self.assertEqual(result, 0)
        self.assertIn("folders", output.getvalue())

    def test_unknown_topic_fails_cleanly(self) -> None:
        output = StringIO()
        error = StringIO()
        result = run_help_command(
            ["unbekannt"],
            output_stream=output,
            error_stream=error,
        )
        self.assertEqual(result, 2)
        self.assertIn("Fehler:", error.getvalue())
        self.assertIn("datenbanktool help", error.getvalue())


if __name__ == "__main__":
    unittest.main()
