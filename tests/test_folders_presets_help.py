from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from datenbanktool.cli import main
from datenbanktool.core.folders import (
    FolderFilter,
    analyse_folders,
    export_folder_html,
)
from datenbanktool.core.index_database import IndexBuildOptions, build_index
from datenbanktool.core.presets import (
    delete_preset,
    get_preset,
    list_presets,
    save_preset,
)
from datenbanktool.core.search import SearchFilter


class FolderPresetHelpTests(unittest.TestCase):
    def _build_sample(self, directory: str) -> tuple[Path, Path]:
        root = Path(directory) / "data"
        (root / "music" / "live").mkdir(parents=True)
        (root / "docs").mkdir()
        (root / "music" / "song.wav").write_bytes(b"same-audio")
        (root / "music" / "live" / "copy.wav").write_bytes(b"same-audio")
        (root / "music" / "live" / "large.wav").write_bytes(b"x" * 128)
        (root / "docs" / " bad?.txt").write_text("text", encoding="utf-8")
        database = Path(directory) / "index.sqlite3"
        build_index(
            IndexBuildOptions(
                root=root,
                database=database,
                hash_duplicates=True,
                large_file_bytes=64,
            )
        )
        return root, database

    def test_folder_overview_aggregates_subfolders_and_largest_files(self) -> None:
        with TemporaryDirectory() as directory:
            _, database = self._build_sample(directory)
            page = analyse_folders(
                database,
                filters=FolderFilter(top_files=2, attention_file_bytes=64),
            )
            by_name = {row.folder: row for row in page.rows}
            self.assertEqual(by_name["music"].total_files, 3)
            self.assertEqual(by_name["music"].direct_files, 1)
            self.assertEqual(by_name["music/live"].direct_files, 2)
            self.assertEqual(
                by_name["music"].largest_files[0].relative_path,
                "music/live/large.wav",
            )
            self.assertIn(by_name["music"].traffic_level, {"yellow", "red"})

    def test_folder_html_contains_real_tooltips_and_text_labels(self) -> None:
        with TemporaryDirectory() as directory:
            _, database = self._build_sample(directory)
            page = analyse_folders(
                database,
                filters=FolderFilter(attention_file_bytes=64),
            )
            html_path = Path(directory) / "folders.html"
            export_folder_html(page, html_path)
            document = html_path.read_text(encoding="utf-8")
            self.assertIn("title=", document)
            self.assertIn("aria-label=", document)
            self.assertIn("Größte Platzfresser", document)
            self.assertIn("Ampel", document)

    def test_search_presets_roundtrip_and_protection(self) -> None:
        with TemporaryDirectory() as directory:
            preset_file = Path(directory) / "presets.json"
            filters = SearchFilter(
                text="song",
                categories=("audio",),
                min_size_bytes=10,
                sort_by="size",
                descending=True,
            )
            saved = save_preset(
                "Große Audios",
                filters,
                description="Audio ab zehn Byte",
                path=preset_file,
            )
            self.assertEqual(saved.name, "Große Audios")
            self.assertEqual(
                get_preset("große audios", preset_file).filters.text,
                "song",
            )
            self.assertEqual(len(list_presets(preset_file)), 1)
            with self.assertRaises(FileExistsError):
                save_preset("Große Audios", filters, path=preset_file)
            replaced = save_preset(
                "Große Audios",
                SearchFilter(text="live"),
                path=preset_file,
                replace=True,
            )
            self.assertEqual(replaced.filters.text, "live")
            deleted = delete_preset("Große Audios", path=preset_file)
            self.assertEqual(deleted.name, "Große Audios")
            self.assertEqual(list_presets(preset_file), ())

    def test_cli_search_runs_saved_preset(self) -> None:
        with TemporaryDirectory() as directory:
            _, database = self._build_sample(directory)
            preset_file = Path(directory) / "presets.json"
            save_preset(
                "Nur Song",
                SearchFilter(text="song", categories=("audio",)),
                path=preset_file,
            )
            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                code = main(
                    [
                        "--no-hints",
                        "index",
                        "search",
                        str(database),
                        "--preset",
                        "Nur Song",
                        "--preset-file",
                        str(preset_file),
                    ]
                )
            self.assertEqual(code, 0)
            text = output.getvalue()
            self.assertIn("music/song.wav", text)
            self.assertNotIn("bad?.txt", text)

    def test_cli_folder_overview_exports_json_and_html(self) -> None:
        with TemporaryDirectory() as directory:
            _, database = self._build_sample(directory)
            json_path = Path(directory) / "folders.json"
            html_path = Path(directory) / "folders.html"
            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                code = main(
                    [
                        "--no-hints",
                        "index",
                        "folders",
                        str(database),
                        "--attention-file-mib",
                        "1",
                        "--json",
                        str(json_path),
                        "--html",
                        str(html_path),
                    ]
                )
            self.assertEqual(code, 0)
            self.assertIn("GRÜN", output.getvalue())
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertGreaterEqual(payload["total_rows"], 3)
            self.assertIn(
                "Ordnerübersicht",
                html_path.read_text(encoding="utf-8"),
            )

    def test_colour_mode_and_explain_output_are_accessible(self) -> None:
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(StringIO()):
            self.assertEqual(
                main(["--color", "always", "explain", "ampel"]),
                0,
            )
        text = output.getvalue()
        self.assertIn("\x1b[", text)
        self.assertIn("Wirkung:", text)
        self.assertIn("Keine Datenänderung", text)

    def test_json_help_stays_free_of_ansi_colours(self) -> None:
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(StringIO()):
            self.assertEqual(
                main(
                    [
                        "--color",
                        "always",
                        "explain",
                        "folders",
                        "--json",
                    ]
                ),
                0,
            )
        self.assertNotIn("\x1b[", output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["name"], "folders")


if __name__ == "__main__":
    unittest.main()
