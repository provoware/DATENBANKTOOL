import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import src.logging_core as logging_core
from src.logging_core import EventLogger, sanitize_details


def test_logging_redacts_sensitive_values(tmp_path: Path) -> None:
    logger = EventLogger(tmp_path)
    logger.log(
        "PRV-TEST-001",
        "Testereignis",
        details={"token": "geheim", "sichtbar": "ok"},
    )
    line = logger.machine_path.read_text(encoding="utf-8").strip()
    record = json.loads(line)
    assert record["details"]["token"] == "[GESCHWÄRZT]"
    assert record["details"]["sichtbar"] == "ok"


def test_short_report_is_layperson_friendly(tmp_path: Path) -> None:
    logger = EventLogger(tmp_path)
    logger.log("PRV-TEST-002", "Warnung", level="WARN")
    report = logger.write_short_report("beendet").read_text(encoding="utf-8")
    assert "Ampel: GELB" in report
    assert "Tipp:" in report


def test_logging_redacts_sensitive_keys_in_nested_lists(tmp_path: Path) -> None:
    logger = EventLogger(tmp_path)
    logger.log(
        "PRV-TEST-003",
        "Verschachteltes Ereignis",
        details={
            "requests": [
                {
                    "headers": [
                        {"Authorization": "Bearer TOPSECRET"},
                        {"cookie": "sessionsecret"},
                    ],
                    "status": "ok",
                }
            ],
        },
    )
    line = logger.machine_path.read_text(encoding="utf-8")
    record = json.loads(line)
    assert "TOPSECRET" not in line
    assert "sessionsecret" not in line
    assert record["details"]["requests"][0]["headers"][0]["Authorization"] == "[GESCHWÄRZT]"
    assert record["details"]["requests"][0]["status"] == "ok"


def test_logging_bounds_nested_and_cyclic_values() -> None:
    cyclic = {}
    cyclic["next"] = [cyclic]
    result = sanitize_details({"root": cyclic, "list": list(range(100))})
    assert result["root"]["next"][0] == "[Zirkuläre Referenz]"
    assert len(result["list"]) == 40

    deep = {"value": "ok"}
    for _ in range(40):
        deep = {"child": deep}
    assert "[Tiefe begrenzt]" in str(sanitize_details(deep))


def _session_segments(logger: EventLogger) -> list[Path]:
    archives = sorted(
        logger.log_dir.glob(f"maschinenlog_status_archiv_{logger.session_id}_*.jsonl")
    )
    return archives + [logger.machine_path]


def _session_records(logger: EventLogger) -> list[dict]:
    return [
        json.loads(line)
        for path in _session_segments(logger)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def test_logging_limits_match_manifest() -> None:
    manifest = json.loads(
        (Path(__file__).resolve().parents[1] / "MANIFEST.json").read_text(encoding="utf-8")
    )
    assert manifest["logging"]["max_jsonl_lines_per_file"] == logging_core.MAX_JSONL_LINES
    assert manifest["logging"]["max_jsonl_bytes_per_file"] == logging_core.MAX_JSONL_BYTES


def test_logging_rotates_by_line_count_without_losing_events(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(logging_core, "MAX_JSONL_LINES", 2)
    logger = EventLogger(tmp_path)
    for index in range(5):
        logger.log(f"PRV-TEST-{index}", "Rotationsprüfung")

    segments = _session_segments(logger)
    assert len(segments) == 3
    assert [len(path.read_text(encoding="utf-8").splitlines()) for path in segments] == [
        2,
        2,
        1,
    ]
    assert [record["code"] for record in _session_records(logger)] == [
        f"PRV-TEST-{index}" for index in range(5)
    ]


def test_logging_rotates_by_utf8_byte_count(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(logging_core, "MAX_JSONL_BYTES", 580)
    logger = EventLogger(tmp_path)
    for index in range(5):
        logger.log(f"PRV-TEST-{index}", "Ä" * 110)

    segments = _session_segments(logger)
    assert len(segments) >= 2
    assert all(0 < path.stat().st_size <= 580 for path in segments)
    assert len(_session_records(logger)) == 5


def test_logging_rotation_is_thread_safe(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(logging_core, "MAX_JSONL_LINES", 3)
    logger = EventLogger(tmp_path)

    def write(index: int) -> None:
        logger.log(f"PRV-THREAD-{index}", "Paralleltest")

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(write, range(40)))

    segments = _session_segments(logger)
    assert all(len(path.read_text(encoding="utf-8").splitlines()) <= 3 for path in segments)
    records = _session_records(logger)
    assert len(records) == 40
    assert {record["code"] for record in records} == {f"PRV-THREAD-{index}" for index in range(40)}


def test_logging_oversized_single_event_is_rejected(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(logging_core, "MAX_JSONL_BYTES", 320)
    logger = EventLogger(tmp_path)
    with pytest.raises(ValueError, match="Dateigrenze"):
        logger.log("PRV-TEST-OVERSIZE", "X" * 2000, level="ERROR")
    assert not logger.machine_path.exists()
    assert logger.errors == 0


def test_logging_restart_preserves_existing_segments(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(logging_core, "MAX_JSONL_LINES", 2)
    first = EventLogger(tmp_path, session_id="test-session")
    first.log("PRV-FIRST-1", "Erster Lauf")
    first.log("PRV-FIRST-2", "Erster Lauf")
    resumed = EventLogger(tmp_path, session_id="test-session")
    resumed.log("PRV-SECOND-1", "Wiederaufnahme")
    resumed.log("PRV-SECOND-2", "Wiederaufnahme")
    resumed.log("PRV-SECOND-3", "Wiederaufnahme")
    assert [record["code"] for record in _session_records(resumed)] == [
        "PRV-FIRST-1",
        "PRV-FIRST-2",
        "PRV-SECOND-1",
        "PRV-SECOND-2",
        "PRV-SECOND-3",
    ]
