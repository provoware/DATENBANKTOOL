from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import quote

from datenbanktool.core.run_journal import (
    discard_resume_record,
    load_resume_records,
)


@dataclass(frozen=True, slots=True)
class RecoveryCandidate:
    record_id: str
    command: tuple[str, ...]
    operation: str
    operation_label: str
    root: str
    database: str
    session_id: int | None
    status: str
    phase: str
    imported_count: int
    updated_utc: str
    resumable: bool
    validation_label: str
    validation_detail: str

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


def _candidate_from_record(record: dict[str, object]) -> RecoveryCandidate | None:
    raw_arguments = record.get("arguments")
    if not isinstance(raw_arguments, list) or not all(
        isinstance(value, str) for value in raw_arguments
    ):
        return None
    arguments = tuple(raw_arguments)
    detected = _scan_slice(arguments)
    if detected is None:
        return None
    start, operation = detected
    if start + 2 >= len(arguments):
        return None
    working_directory = Path(str(record.get("working_directory") or Path.cwd()))
    root = Path(arguments[start + 2]).expanduser()
    if not root.is_absolute():
        root = working_directory / root
    root = root.resolve(strict=False)
    database_value = _database_argument(arguments[start:])
    if not database_value:
        return None
    database = Path(database_value).expanduser()
    if not database.is_absolute():
        database = working_directory / database
    database = database.resolve(strict=False)
    operation_label = (
        "erste Ordnerprüfung" if operation == "build" else "Änderungsprüfung"
    )
    base = {
        "record_id": str(record.get("record_id") or ""),
        "command": _resume_command(arguments),
        "operation": operation,
        "operation_label": operation_label,
        "root": str(root),
        "database": str(database),
        "updated_utc": str(record.get("updated_utc") or ""),
    }
    if not root.is_dir():
        return RecoveryCandidate(
            **base,
            session_id=None,
            status=str(record.get("status") or "unbekannt"),
            phase="nicht geprüft",
            imported_count=0,
            resumable=False,
            validation_label="Ordner nicht verfügbar",
            validation_detail=(
                "Der gespeicherte Quellordner ist derzeit nicht erreichbar. "
                "Der Eintrag bleibt erhalten und kann bewusst verworfen werden."
            ),
        )
    if not database.is_file():
        return RecoveryCandidate(
            **base,
            session_id=None,
            status=str(record.get("status") or "unbekannt"),
            phase="nicht geprüft",
            imported_count=0,
            resumable=False,
            validation_label="Indexdatei nicht verfügbar",
            validation_detail=(
                "Die gespeicherte Indexdatei ist derzeit nicht erreichbar. "
                "Der Eintrag bleibt erhalten und kann bewusst verworfen werden."
            ),
        )
    scan_mode = "full" if operation == "build" else "incremental"
    try:
        row = _read_resumable_session(database, root, scan_mode)
    except (OSError, sqlite3.Error) as error:
        return RecoveryCandidate(
            **base,
            session_id=None,
            status=str(record.get("status") or "unbekannt"),
            phase="Prüfung fehlgeschlagen",
            imported_count=0,
            resumable=False,
            validation_label="Index konnte nicht geprüft werden",
            validation_detail=f"Nur-Lese-SQLite-Prüfung fehlgeschlagen: {error}",
        )
    if row is None:
        return RecoveryCandidate(
            **base,
            session_id=None,
            status=str(record.get("status") or "veraltet"),
            phase="kein fortsetzbarer Stand",
            imported_count=0,
            resumable=False,
            validation_label="Kein fortsetzbarer SQLite-Stand",
            validation_detail=(
                "Die Indexdatei enthält für diesen Ordner und diese Scanart keine "
                "laufende, unterbrochene oder fehlgeschlagene Sitzung."
            ),
        )
    return RecoveryCandidate(
        **base,
        session_id=int(row["id"]),
        status=str(row["status"]),
        phase=str(row["phase"]),
        imported_count=int(row["imported_count"]),
        updated_utc=str(row["updated_utc"]),
        resumable=True,
        validation_label="Geprüft und fortsetzbar",
        validation_detail=(
            "Ordner, Indexdatei, Scanart und neueste fortsetzbare SQLite-Sitzung passen zusammen."
        ),
    )


def load_recovery_candidates() -> tuple[RecoveryCandidate, ...]:
    """Return every stored scan entry after an independent read-only validation."""
    candidates = [
        candidate
        for record in load_resume_records()
        if (candidate := _candidate_from_record(record)) is not None
    ]
    return tuple(
        sorted(candidates, key=lambda item: item.updated_utc, reverse=True)
    )


def load_recovery_candidate() -> RecoveryCandidate | None:
    """Compatibility helper returning the newest actually resumable scan."""
    return next(
        (candidate for candidate in load_recovery_candidates() if candidate.resumable),
        None,
    )


def discard_recovery_candidate(record_id: str) -> bool:
    """Discard exactly one internal recovery hint without touching index or source files."""
    return discard_resume_record(record_id)
