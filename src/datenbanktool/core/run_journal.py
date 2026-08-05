from __future__ import annotations

import json
import os
import platform
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from datenbanktool.core.durable_files import atomic_write_text

_SCHEMA_VERSION = 1
_SECRET_MARKERS = ("token", "password", "passwort", "secret", "apikey", "api-key")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_state_directory() -> Path:
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "datenbanktool"


def _redact(arguments: Sequence[str]) -> list[str]:
    result: list[str] = []
    hide_next = False
    for value in arguments:
        if hide_next:
            result.append("<ausgeblendet>")
            hide_next = False
            continue
        lowered = value.casefold()
        if value.startswith("--") and any(marker in lowered for marker in _SECRET_MARKERS):
            if "=" in value:
                result.append(value.split("=", 1)[0] + "=<ausgeblendet>")
            else:
                result.append(value)
                hide_next = True
            continue
        result.append(value)
    return result


def _read_json(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError, UnicodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _safe_write(path: Path, payload: dict[str, object]) -> bool:
    try:
        atomic_write_text(
            path,
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            overwrite=True,
            mode=0o600,
        )
    except OSError:
        return False
    return True


def previous_unfinished_run(state_directory: Path | None = None) -> dict[str, object] | None:
    path = (state_directory or default_state_directory()) / "last-run.json"
    payload = _read_json(path)
    if payload and payload.get("status") in {"running", "failed", "interrupted"}:
        return payload
    return None


@dataclass(slots=True)
class RunJournal:
    path: Path
    payload: dict[str, object]
    previous_unfinished: dict[str, object] | None = None

    @classmethod
    def begin(
        cls,
        arguments: Sequence[str],
        *,
        version: str,
        state_directory: Path | None = None,
    ) -> "RunJournal":
        directory = state_directory or default_state_directory()
        path = directory / "last-run.json"
        previous = previous_unfinished_run(directory)
        payload: dict[str, object] = {
            "schema_version": _SCHEMA_VERSION,
            "status": "running",
            "started_utc": utc_now(),
            "updated_utc": utc_now(),
            "finished_utc": None,
            "exit_code": None,
            "version": version,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "process_id": os.getpid(),
            "arguments": _redact(arguments),
            "message": "Befehl läuft",
            "technical_error": None,
            "crash_report": None,
        }
        _safe_write(path, payload)
        return cls(path=path, payload=payload, previous_unfinished=previous)

    def _finish(
        self,
        status: str,
        *,
        exit_code: int,
        message: str,
        technical_error: str | None = None,
        crash_report: str | None = None,
    ) -> None:
        self.payload.update(
            {
                "status": status,
                "updated_utc": utc_now(),
                "finished_utc": utc_now(),
                "exit_code": exit_code,
                "message": message,
                "technical_error": technical_error,
                "crash_report": crash_report,
            }
        )
        _safe_write(self.path, self.payload)

    def complete(self, exit_code: int) -> None:
        status = "complete" if exit_code == 0 else "controlled-error"
        message = "Befehl abgeschlossen" if exit_code == 0 else "Befehl kontrolliert beendet"
        self._finish(status, exit_code=exit_code, message=message)

    def interrupted(self, message: str = "Vom Nutzer abgebrochen") -> None:
        self._finish("interrupted", exit_code=130, message=message)

    def unexpected_failure(self, error: BaseException) -> Path | None:
        directory = self.path.parent
        report = directory / f"crash-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.getpid()}.json"
        technical = f"{type(error).__name__}: {error}"
        payload = {
            **self.payload,
            "status": "failed",
            "updated_utc": utc_now(),
            "finished_utc": utc_now(),
            "exit_code": 70,
            "message": "Unerwarteter Programmfehler",
            "technical_error": technical,
            "traceback": "".join(traceback.format_exception(type(error), error, error.__traceback__)),
            "executable": sys.executable,
        }
        written = _safe_write(report, payload)
        report_value = str(report) if written else None
        self._finish(
            "failed",
            exit_code=70,
            message="Unerwarteter Programmfehler",
            technical_error=technical,
            crash_report=report_value,
        )
        return report if written else None
