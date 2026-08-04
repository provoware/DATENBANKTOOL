from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from datenbanktool.cli import main
from datenbanktool.core.folder_timeline import (
    FolderTimelineOptions,
    build_folder_timeline,
)
from datenbanktool.core.folder_timeline_exports import export_folder_timeline
from datenbanktool.core.index_database import IndexBuildOptions, build_index
from datenbanktool.core.incremental import IncrementalScanOptions, incremental_rescan
from datenbanktool.core.timeline_presets import (
    delete_timeline_preset,
    get_timeline_preset,
    list_timeline_presets,
    save_timeline_preset,
)


class TimelinePresetAndThresholdTests(unittest.TestCase):
    def _create_three_scans(self, directory: str):
        root = Path(directory) / "data"
        (root / "music").mkdir(parents=True)
        (root / "music" / "a.bin").write_bytes(b"a" * 10)
        database = Path(directory) / "index.sqlite3"
        build_index(IndexBuildOptions(root=root, database=database))

        (root / "music" / "a.bin").write_bytes(b"a" * 30)
        (root / "music" / "b.bin").write_bytes(b"b" * 5)
        incremental_rescan(IncrementalScanOptions(root=root, database=database))

        (root / "music" / "a.bin").unlink()
        incremental_rescan(IncrementalScanOptions(root=root, database=database))
        return database

    def test_timeline_presets_roundtrip_protection_and_permissions(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "timeline-presets.json"
            saved = save_timeline_preset(
                "Musik Verlauf",
                "music/archive",
                description="Regelmäßige Prüfung",
                path=path,
            )
            self.assertEqual(saved.folder, "music/archive")
            self.assertEqual(get_timeline_preset("musik verlauf", path), saved)
            self.assertEqual(list_timeline_presets(path), (saved,))
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                save_timeline_preset("Musik Verlauf", "music", path=path)
            replaced = save_timeline_preset(
                "Musik Verlauf",
                "music",
                path=path,
                replace=True,
            )
            self.assertEqual(replaced.folder, "music")
            self.assertEqual(replaced.created_utc, saved.created_utc)
            with self.assertRaisesRegex(ValueError, "relativ"):
                save_timeline_preset("Unsicher", "../privat", path=path)
            deleted = delete_timeline_preset("Musik Verlauf", path=path)
            self.assertEqual(deleted.name, "Musik Verlauf")
            self.assertEqual(list_timeline_presets(path), ())

    def test_timeline_preset_cli_roundtrip_and_confirmation(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "presets.json"
            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                code = main(
                    [
                        "index",
                        "timeline-presets",
                        "save",
                        "Musik",
                        "music",
                        "--description",
                        "Wöchentlich",
                        "--preset-file",
                        str(path),
                    ]
                )
            self.assertEqual(code, 0)
            self.assertIn("gespeichert", output.getvalue())

            json_output = StringIO()
            with redirect_stdout(json_output), redirect_stderr(StringIO()):
                code = main(
                    [
                        "index",
                        "timeline-presets",
                        "list",
                        "--preset-file",
                        str(path),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(json_output.getvalue())
            self.assertEqual(payload[0]["folder"], "music")

            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                code = main(
                    [
                        "index",
                        "timeline-presets",
                        "delete",
                        "Musik",
                        "--preset-file",
                        str(path),
                    ]
                )
            self.assertEqual(code, 2)
            self.assertEqual(len(list_timeline_presets(path)), 1)

    def test_thresholds_mark_growth_with_clear_reasons_and_exports(self) -> None:
        with TemporaryDirectory() as directory:
            database = self._create_three_scans(directory)
            timeline = build_folder_timeline(
                database,
                options=FolderTimelineOptions(
                    folder="music",
                    warn_size_growth_percent=200,
                    warn_file_growth_percent=50,
                ),
            )
            growth = timeline.points[1]
            self.assertEqual(growth.size_delta_percent, 250.0)
            self.assertEqual(growth.file_delta_percent, 100.0)
            self.assertTrue(growth.threshold_triggered)
            self.assertEqual(growth.traffic_level, "red")
            self.assertEqual(growth.traffic_label, "Trendgrenze erreicht")
            self.assertIn("Größe +250,00 %", growth.traffic_reason)
            self.assertIn("Dateizahl +100,00 %", growth.traffic_reason)
            self.assertIn("keine Schadensbewertung", growth.traffic_reason)
            self.assertFalse(timeline.points[2].threshold_triggered)
            self.assertEqual(timeline.threshold_trigger_count, 1)

            csv_path = Path(directory) / "timeline.csv"
            html_path = Path(directory) / "timeline.html"
            export_folder_timeline(timeline, csv_path=csv_path, html_path=html_path)
            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.reader(handle, delimiter=";"))
            self.assertIn("Dateidifferenz Prozent", rows[0])
            self.assertIn("Trendgrenze erreicht", rows[0])
            html_text = html_path.read_text(encoding="utf-8")
            self.assertIn("Aktive rein lesende Trendgrenzen", html_text)
            self.assertIn("Trendgrenze erreicht", html_text)
            self.assertIn("warning-point", html_text)
            self.assertIn(">Warnung</text>", html_text)
            self.assertNotIn("<script", html_text.casefold())

    def test_cli_uses_preset_and_prints_threshold_reason(self) -> None:
        with TemporaryDirectory() as directory:
            database = self._create_three_scans(directory)
            preset_path = Path(directory) / "presets.json"
            save_timeline_preset("Musik", "music", path=preset_path)
            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                code = main(
                    [
                        "index",
                        "folder-timeline",
                        str(database),
                        "--preset",
                        "Musik",
                        "--preset-file",
                        str(preset_path),
                        "--warn-size-growth-percent",
                        "200",
                        "--warn-file-growth-percent",
                        "50",
                    ]
                )
            self.assertEqual(code, 0)
            text = output.getvalue()
            self.assertIn("Zeitreihen-Vorlage: Musik", text)
            self.assertIn("Trendgrenze erreicht", text)
            self.assertIn("Größe +250,00 %", text)
            self.assertIn("keine Schadensbewertung", text)

    def test_threshold_validation_rejects_non_finite_and_out_of_range(self) -> None:
        for value in (float("nan"), float("inf"), -1.0, 1_000_001.0):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "Warnschwelle"):
                    FolderTimelineOptions(
                        warn_size_growth_percent=value
                    ).validate()


if __name__ == "__main__":
    unittest.main()
