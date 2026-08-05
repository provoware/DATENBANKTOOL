from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import quote

from datenbanktool.core.run_journal import clear_resume_record, load_resume_record


@dataclass(frozen=True, slots=True)
class RecoveryCandidate:
    command: tuple[str, ...]
    operation: str
    operation_label: str
    root: str
    database: str
    session_id: int
    status: str
    phase: str
    imported_count: int
    updated_utc: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _scan_slice(arguments: tuple[str, ...]) -> tuple[int, str] | None:
    for index in range(max(0, len(arguments) - 1)):
        if arguments[index] == "index" and arguments[index + 1] in {"build", "rescan"}:
            return index, arguments[index + 1]
    return None


def _database_argument(arguments: tuple[str, ...]) -> str | None:
    for index, value in enumerate(arguments):
        if value == "--database" and index + 1 < len(arguments):
            return arguments[index + 1]
        if value.startswith("--database="):
            return value.split("=", 1)[1]
    return None


def _resume_command(arguments: tuple[str, ...]) -> tuple[str, ...]:
    values = [value for value in arguments if value != "--resume"]
    values.append("--resume")
    return tuple(values)


def _read_resumable_session(
    database: Path,
    root: Path,
    scan_mode: str,
) -> sqlite3.Row | None:
    uri = f"file:{quote(str(database), safe='/')}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        return connection.execute(
            """
            SELECT id, status, phase, imported_count, updated_utc
            FROM scan_sessions
            WHERE root=? AND scan_mode=?
              AND status IN ('running', 'interrupted', 'failed')
            ORDER BY id DESC LIMIT 1
            """,
            (str(root), scan_mode),
        ).fetchone()
    finally:
        connection.close()


def load_recovery_candidate() -> RecoveryCandidate | None:
    """Return one verified resumable scan without changing user files or the index."""
    record = load_resume_record()
    if record is None:
        return None
    raw_arguments = record.get("arguments")
    if not isinstance(raw_arguments, list) or not all(
        isinstance(value, str) for value in raw_arguments
    ):
        clear_resume_record()
        return None
    arguments = tuple(raw_arguments)
    detected = _scan_slice(arguments)
    if detected is None:
        clear_resume_record()
        return None
    start, operation = detected
    if start + 2 >= len(arguments):
        clear_resume_record()
        return None
    root = Path(arguments[start + 2]).expanduser().resolve(strict=False)
    database_value = _database_argument(arguments[start:])
    if not database_value:
        clear_resume_record()
        return None
    database = Path(database_value).expanduser().resolve(strict=False)
    if not database.is_file() or not root.is_dir():
        return None
    scan_mode = "full" if operation == "build" else "incremental"
    try:
        row = _read_resumable_session(database, root, scan_mode)
    except (OSError, sqlite3.Error):
        return None
    if row is None:
        clear_resume_record()
        return None
    return RecoveryCandidate(
        command=_resume_command(arguments),
        operation=operation,
        operation_label=(
            "erste Ordnerprüfung" if operation == "build" else "Änderungsprüfung"
        ),
        root=str(root),
        database=str(database),
        session_id=int(row["id"]),
        status=str(row["status"]),
        phase=str(row["phase"]),
        imported_count=int(row["imported_count"]),
        updated_utc=str(row["updated_utc"]),
    )
