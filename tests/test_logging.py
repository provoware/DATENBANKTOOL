import json
from pathlib import Path

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
