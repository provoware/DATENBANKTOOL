from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

SENSITIVE_PARTS = (
    "password",
    "passwort",
    "token",
    "secret",
    "api_key",
    "authorization",
    "cookie",
    "credential",
)


def now_text() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def new_session_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{secrets.token_hex(3)}"


def _sensitive(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_PARTS)


def sanitize_details(details: dict[str, Any], limit: int = 2000) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in list(details.items())[:40]:
        if _sensitive(str(key)):
            result[str(key)] = "[GESCHWÄRZT]"
            continue
        if isinstance(value, dict):
            result[str(key)] = sanitize_details(value, limit)
            continue
        text = str(value)
        result[str(key)] = text if len(text) <= limit else text[: limit - 12] + " … [gekürzt]"
    return result


@dataclass
class EventLogger:
    root: Path
    session_id: str = field(default_factory=new_session_id)
    warnings: int = 0
    errors: int = 0

    def __post_init__(self) -> None:
        self.log_dir = self.root / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.machine_path = self.log_dir / (f"maschinenlog_status_laufend_{self.session_id}.jsonl")

    def log(
        self,
        code: str,
        summary: str,
        *,
        level: str = "INFO",
        component: str = "core",
        action: str = "Keine Aktion nötig.",
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = level.upper()
        if normalized == "WARN":
            self.warnings += 1
        if normalized in {"ERROR", "CRITICAL"}:
            self.errors += 1
        record = {
            "schema_version": 1,
            "session_id": self.session_id,
            "event_id": f"evt-{secrets.token_hex(5)}",
            "timestamp": now_text(),
            "level": normalized,
            "code": code,
            "component": component,
            "summary": summary,
            "action": action,
            "details": sanitize_details(details or {}),
        }
        with self.machine_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def write_short_report(self, status: str = "beendet") -> Path:
        color = "ROT" if self.errors else "GELB" if self.warnings else "GRÜN"
        path = self.log_dir / f"kurzbericht_status_{status}_{self.session_id}.txt"
        lines = [
            "PROVOWARE DATENBANKTOOL – KURZBERICHT",
            "=" * 60,
            f"Ampel: {color}",
            f"Status: {status.upper()}",
            f"Session: {self.session_id}",
            f"Warnungen: {self.warnings}",
            f"Fehler: {self.errors}",
            "",
            "Tipp:",
            "Bei ROT zuerst den Fehlercode im Maschinenlog suchen.",
            f"Maschinenlog: {self.machine_path.name}",
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path
