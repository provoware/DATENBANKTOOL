from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

MAX_JSONL_LINES = 2500
MAX_JSONL_BYTES = 2_097_152

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


def _sanitize_value(value: Any, limit: int, depth: int, active: set[int]) -> Any:
    if depth >= 8:
        return "[Tiefe begrenzt]"
    if isinstance(value, (dict, list, tuple)):
        identity = id(value)
        if identity in active:
            return "[Zirkuläre Referenz]"
        active.add(identity)
        try:
            if isinstance(value, dict):
                result: dict[str, Any] = {}
                for index, (key, item) in enumerate(value.items()):
                    if index >= 40:
                        break
                    name = str(key)
                    result[name] = (
                        "[GESCHWÄRZT]"
                        if _sensitive(name)
                        else _sanitize_value(item, limit, depth + 1, active)
                    )
                return result
            return [_sanitize_value(item, limit, depth + 1, active) for item in value[:40]]
        finally:
            active.remove(identity)
    text = str(value)
    return text if len(text) <= limit else text[: max(0, limit - 12)] + " … [gekürzt]"


def sanitize_details(details: dict[str, Any], limit: int = 2000) -> dict[str, Any]:
    """Redact nested sensitive keys, including keys in lists, before writing JSONL."""
    return _sanitize_value(details, limit, 0, set())


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
        self._write_lock = Lock()
        if self.machine_path.is_symlink():
            raise OSError("Maschinenlog darf kein symbolischer Link sein.")
        self._byte_count = self.machine_path.stat().st_size if self.machine_path.exists() else 0
        self._line_count = 0
        if self.machine_path.exists():
            with self.machine_path.open("rb") as handle:
                self._line_count = sum(1 for _ in handle)

    def _rotate_machine_log(self) -> None:
        """Archive the full segment without deleting or overwriting earlier evidence."""
        index = 1
        while True:
            archived = self.log_dir / (
                f"maschinenlog_status_archiv_{self.session_id}_{index:04d}.jsonl"
            )
            if not archived.exists() and not archived.is_symlink():
                break
            index += 1
        self.machine_path.rename(archived)
        self._line_count = 0
        self._byte_count = 0

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
        payload = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
        if len(payload) > MAX_JSONL_BYTES:
            raise ValueError("Einzelner Logeintrag überschreitet die Dateigrenze.")
        with self._write_lock:
            if (
                self._line_count >= MAX_JSONL_LINES
                or self._byte_count + len(payload) > MAX_JSONL_BYTES
            ):
                self._rotate_machine_log()
            with self.machine_path.open("ab") as handle:
                handle.write(payload)
            self._line_count += 1
            self._byte_count += len(payload)
            if normalized == "WARN":
                self.warnings += 1
            if normalized in {"ERROR", "CRITICAL"}:
                self.errors += 1
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
