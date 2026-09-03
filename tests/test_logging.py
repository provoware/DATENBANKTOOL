import json
from pathlib import Path

from src.logging_core import EventLogger


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
