from __future__ import annotations

import fcntl
import hashlib
import json
import os
import platform
import sys
import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Sequence

from datenbanktool.core.durable_files import atomic_write_text, durable_remove

_RUN_SCHEMA_VERSION = 1
_RESUME_SCHEMA_VERSION = 2
_SECRET_MARKERS = ("token", "password", "passwort", "secret", "apikey", "api-key")
_RESUME_FILE = "resume-run.json"
_RESUME_LOCK_FILE = ".resume-run.lock"
MAX_RESUME_RECORDS = 12


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


def _database_argument(arguments: Sequence[str]) -> str | None:
    values = tuple(str(value) for value in arguments)
    for index, value in enumerate(values):
        if value == "--database" and index + 1 < len(values):
            return values[index + 1]
        if value.startswith("--database="):
            return value.split("=", 1)[1]
    return None


def _database_key(arguments: Sequence[str], working_directory: str | None = None) -> str | None:
    value = _database_argument(arguments)
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path(working_directory or Path.cwd()) / path
    return str(path.resolve(strict=False))


def _record_id(database_key: str) -> str:
    return hashlib.sha256(database_key.encode("utf-8")).hexdigest()


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
    except (OSError, ValueError):
        return False
    return True


@contextmanager
def _resume_lock(state_directory: Path, *, exclusive: bool) -> Iterator[None]:
    state_directory.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        state_directory / _RESUME_LOCK_FILE,
        os.O_RDWR | os.O_CREAT,
        0o600,
    )
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _normalise_resume_record(payload: object) -> dict[str, object] | None:
    if not isinstance(payload, dict):
        return None
    arguments = payload.get("arguments")
    if not isinstance(arguments, list) or not all(isinstance(item, str) for item in arguments):
        return None
    working_directory = str(payload.get("working_directory") or Path.cwd())
    database_key = str(payload.get("database_key") or "") or _database_key(
        arguments,
        working_directory,
    )
    if not database_key or _scan_command(arguments) is None:
        return None
    value = dict(payload)
    value.update(
        {
            "record_id": str(payload.get("record_id") or _record_id(database_key)),
            "database_key": database_key,
            "working_directory": working_directory,
            "arguments": list(arguments),
            "started_utc": str(payload.get("started_utc") or utc_now()),
            "updated_utc": str(payload.get("updated_utc") or utc_now()),
        }
    )
    return value


def _load_resume_records_unlocked(state_directory: Path) -> list[dict[str, object]]:
    payload = _read_json(default_resume_path(state_directory))
    if not payload:
        return []
    if payload.get("schema_version") == _RESUME_SCHEMA_VERSION:
        raw_records = payload.get("records")
        if not isinstance(raw_records, list):
            return []
    elif payload.get("schema_version") == _RUN_SCHEMA_VERSION:
        raw_records = [payload]
    else:
        return []
    records = [
        record
        for item in raw_records
        if (record := _normalise_resume_record(item)) is not None
    ]
    records.sort(key=lambda item: str(item.get("updated_utc", "")), reverse=True)
    return records


def _write_resume_records_unlocked(
    state_directory: Path,
    records: Sequence[dict[str, object]],
) -> bool:
    newest_by_database: dict[str, dict[str, object]] = {}
    for raw in sorted(
        records,
        key=lambda item: str(item.get("updated_utc", "")),
        reverse=True,
    ):
        record = _normalise_resume_record(raw)
        if record is None:
            continue
        newest_by_database.setdefault(str(record["database_key"]), record)
    limited = list(newest_by_database.values())[:MAX_RESUME_RECORDS]
    path = default_resume_path(state_directory)
    if not limited:
        try:
            durable_remove(path, missing_ok=True)
        except (OSError, ValueError):
            return False
        return True
    return _safe_write(
        path,
        {
            "schema_version": _RESUME_SCHEMA_VERSION,
            "maximum_records": MAX_RESUME_RECORDS,
            "updated_utc": utc_now(),
            "records": limited,
        },
    )


def load_resume_records(
    state_directory: Path | None = None,
) -> tuple[dict[str, object], ...]:
    directory = state_directory or default_state_directory()
    try:
        with _resume_lock(directory, exclusive=True):
            records = _load_resume_records_unlocked(directory)
            payload = _read_json(default_resume_path(directory))
            if records and payload and payload.get("schema_version") != _RESUME_SCHEMA_VERSION:
                _write_resume_records_unlocked(directory, records)
            return tuple(dict(item) for item in records)
    except OSError:
        return ()


def load_resume_record(state_directory: Path | None = None) -> dict[str, object] | None:
    """Compatibility helper returning the newest stored scan record."""
    records = load_resume_records(state_directory)
    return dict(records[0]) if records else None


def discard_resume_record(
    record_id: str,
    state_directory: Path | None = None,
) -> bool:
    directory = state_directory or default_state_directory()
    try:
        with _resume_lock(directory, exclusive=True):
            records = _load_resume_records_unlocked(directory)
            remaining = [item for item in records if item.get("record_id") != record_id]
            if len(remaining) == len(records):
                return False
            return _write_resume_records_unlocked(directory, remaining)
    except OSError:
        return False


def clear_resume_record(state_directory: Path | None = None) -> bool:
    """Compatibility helper clearing all internal recovery records."""
    directory = state_directory or default_state_directory()
    try:
        with _resume_lock(directory, exclusive=True):
            existed = default_resume_path(directory).exists()
            if not _write_resume_records_unlocked(directory, []):
                return False
            return existed
    except OSError:
        return False


def _upsert_resume_record(
    arguments: Sequence[str],
    *,
    state_directory: Path,
) -> str | None:
    values = tuple(str(value) for value in arguments)
    scan = _scan_command(values)
    working_directory = str(Path.cwd().resolve(strict=False))
    database_key = _database_key(values, working_directory)
    if scan is None or database_key is None:
        return None
    identifier = _record_id(database_key)
    try:
        with _resume_lock(state_directory, exclusive=True):
            records = _load_resume_records_unlocked(state_directory)
            existing = next(
                (item for item in records if item.get("record_id") == identifier),
                None,
            )
            now = utc_now()
            record: dict[str, object] = {
                "record_id": identifier,
                "database_key": database_key,
                "working_directory": working_directory,
                "status": "running",
                "started_utc": (
                    str(existing.get("started_utc")) if existing is not None else now
                ),
                "updated_utc": now,
                "finished_utc": None,
                "exit_code": None,
                "arguments": list(values),
                "message": "Scan kann nach Unterbrechung mit --resume fortgesetzt werden",
            }
            records = [item for item in records if item.get("record_id") != identifier]
            records.insert(0, record)
            if not _write_resume_records_unlocked(state_directory, records):
                return None
            return identifier
    except OSError:
        return None


def _update_resume_record(
    record_id: str | None,
    *,
    state_directory: Path,
    status: str,
    exit_code: int,
    message: str,
) -> None:
    if not record_id:
        return
    try:
        with _resume_lock(state_directory, exclusive=True):
            records = _load_resume_records_unlocked(state_directory)
            changed = False
            now = utc_now()
            for record in records:
                if record.get("record_id") != record_id:
                    continue
                record.update(
                    {
                        "status": status,
                        "updated_utc": now,
                        "finished_utc": now,
                        "exit_code": exit_code,
                        "message": message,
                    }
                )
                changed = True
                break
            if changed:
                _write_resume_records_unlocked(state_directory, records)
    except OSError:
        return


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
            "schema_version": _RUN_SCHEMA_VERSION,
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
            "active_resume_id": None,
            "message": "Befehl läuft",
            "technical_error": None,
            "crash_report": None,
        }
        _safe_write(path, payload)
        return cls(path=path, payload=payload, previous_unfinished=previous)

    def record_active_command(self, arguments: Sequence[str]) -> None:
        values = tuple(str(value) for value in arguments)
        resume_id = _upsert_resume_record(values, state_directory=self.state_directory)
        self.payload.update(
            {
                "updated_utc": utc_now(),
                "active_arguments": _redact(values),
                "active_resume_id": resume_id,
                "message": "Bestätigter Befehl läuft",
            }
        )
        _safe_write(self.path, self.payload)

    def record_command_result(self, arguments: Sequence[str], exit_code: int) -> None:
        if _scan_command(arguments) is None:
            return
        record_id = str(self.payload.get("active_resume_id") or "") or None
        if exit_code == 0:
            if record_id:
                discard_resume_record(record_id, self.state_directory)
            return
        _update_resume_record(
            record_id,
            state_directory=self.state_directory,
            status="needs-resume",
            exit_code=exit_code,
            message=(
                "Der Scan wurde nicht vollständig abgeschlossen; der bestätigte "
                "Befehl bleibt erhalten"
            ),
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
        _update_resume_record(
            str(self.payload.get("active_resume_id") or "") or None,
            state_directory=self.state_directory,
            status="interrupted",
            exit_code=130,
            message=message,
        )
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
        _update_resume_record(
            str(self.payload.get("active_resume_id") or "") or None,
            state_directory=self.state_directory,
            status="failed",
            exit_code=70,
            message="Unerwarteter Programmfehler; Fortsetzung bleibt vorgemerkt",
        )
        self._finish(
            "failed",
            exit_code=70,
            message="Unerwarteter Programmfehler",
            technical_error=technical,
            crash_report=report_value,
        )
        return report if written else None
