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

from datenbanktool.core.durable_files import atomic_write_text, durable_remove

_SCHEMA_VERSION = 1
_SECRET_MARKERS = ("token", "password", "passwort", "secret", "apikey", "api-key")
_RESUME_FILE = "resume-run.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_state_directory() -> Path:
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "datenbanktool"


def default_resume_path(state_directory: Path | None = None) -> Path:
    return (state_directory or default_state_directory()) / _RESUME_FILE


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


def _scan_command(arguments: Sequence[str]) -> tuple[str, ...] | None:
    values = tuple(str(value) for value in arguments)
    for index in range(max(0, len(values) - 1)):
        if values[index] == "index" and values[index + 1] in {"build", "rescan"}:
            return values
    return None


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


def load_resume_record(state_directory: Path | None = None) -> dict[str, object] | None:
    payload = _read_json(default_resume_path(state_directory))
    if not payload or payload.get("schema_version") != _SCHEMA_VERSION:
        return None
    arguments = payload.get("arguments")
    if not isinstance(arguments, list) or not all(isinstance(item, str) for item in arguments):
        return None
    return payload


def clear_resume_record(state_directory: Path | None = None) -> bool:
    try:
        return durable_remove(default_resume_path(state_directory), missing_ok=True)
    except OSError:
        return False


def previous_unfinished_run(
    state_directory: Path | None = None,
    *,
    ignore_process_id: int | None = None,
) -> dict[str, object] | None:
    path = (state_directory or default_state_directory()) / "last-run.json"
    payload = _read_json(path)
    if not payload or payload.get("status") not in {"running", "failed", "interrupted"}:
        return None
    if ignore_process_id is not None and payload.get("process_id") == ignore_process_id:
        return None
    return payload


@dataclass(slots=True)
class RunJournal:
    path: Path
    payload: dict[str, object]
    previous_unfinished: dict[str, object] | None = None

    @property
    def state_directory(self) -> Path:
        return self.path.parent

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
        previous = previous_unfinished_run(directory, ignore_process_id=os.getpid())
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
            "active_arguments": None,
            "message": "Befehl läuft",
            "technical_error": None,
            "crash_report": None,
        }
        _safe_write(path, payload)
        return cls(path=path, payload=payload, previous_unfinished=previous)

    def record_active_command(self, arguments: Sequence[str]) -> None:
        values = tuple(str(value) for value in arguments)
        self.payload.update(
            {
                "updated_utc": utc_now(),
                "active_arguments": _redact(values),
                "message": "Bestätigter Befehl läuft",
            }
        )
        _safe_write(self.path, self.payload)
        scan = _scan_command(values)
        if scan is None:
            return
        existing = load_resume_record(self.state_directory)
        started = (
            str(existing.get("started_utc"))
            if existing and existing.get("arguments") == list(values)
            else utc_now()
        )
        _safe_write(
            default_resume_path(self.state_directory),
            {
                "schema_version": _SCHEMA_VERSION,
                "status": "running",
                "started_utc": started,
                "updated_utc": utc_now(),
                "finished_utc": None,
                "exit_code": None,
                "arguments": list(values),
                "message": "Scan kann nach Unterbrechung mit --resume fortgesetzt werden",
            },
        )

    def _update_resume(self, status: str, exit_code: int, message: str) -> None:
        payload = load_resume_record(self.state_directory)
        if payload is None:
            return
        payload.update(
            {
                "status": status,
                "updated_utc": utc_now(),
                "finished_utc": utc_now(),
                "exit_code": exit_code,
                "message": message,
            }
        )
        _safe_write(default_resume_path(self.state_directory), payload)

    def record_command_result(self, arguments: Sequence[str], exit_code: int) -> None:
        if _scan_command(arguments) is None:
            return
        if exit_code == 0:
            clear_resume_record(self.state_directory)
            return
        self._update_resume(
            "needs-resume",
            exit_code,
            "Der Scan wurde nicht vollständig abgeschlossen; der bestätigte Befehl bleibt erhalten",
        )

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
        self._update_resume("interrupted", 130, message)
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
        self._update_resume("failed", 70, "Unerwarteter Programmfehler; Fortsetzung bleibt vorgemerkt")
        self._finish(
            "failed",
            exit_code=70,
            message="Unerwarteter Programmfehler",
            technical_error=technical,
            crash_report=report_value,
        )
        return report if written else None
