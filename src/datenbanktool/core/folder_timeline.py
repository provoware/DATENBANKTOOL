from __future__ import annotations

import math
import os
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from datenbanktool.core.index_types import (
    SCHEMA_VERSION,
    UnsupportedSchemaError,
    normalise_database_path,
)
from datenbanktool.core.presentation import TrafficLight

_MAX_POINTS = 500
_MAX_THRESHOLD_PERCENT = 1_000_000.0
_STATUS_LABELS = {
    "baseline": "Ausgangswert",
    "grown": "Gewachsen",
    "shrunk": "Kleiner geworden",
    "new": "Neu",
    "removed": "Nicht mehr vorhanden",
    "changed": "Dateizahl geändert",
    "unchanged": "Unverändert",
}


@dataclass(frozen=True, slots=True)
class FolderTimelineOptions:
    folder: str = "."
    from_session_id: int | None = None
    to_session_id: int | None = None
    limit: int = 100
    warn_size_growth_percent: float | None = None
    warn_file_growth_percent: float | None = None

    def validate(self) -> None:
        normalise_folder(self.folder)
        if self.from_session_id is not None and self.from_session_id < 1:
            raise ValueError("Ausgangssitzung muss mindestens 1 sein")
        if self.to_session_id is not None and self.to_session_id < 1:
            raise ValueError("Zielsitzung muss mindestens 1 sein")
        if not 2 <= self.limit <= _MAX_POINTS:
            raise ValueError(f"Anzahl Zeitpunkte muss zwischen 2 und {_MAX_POINTS} liegen")
        _validate_threshold("Größenwachstum", self.warn_size_growth_percent)
        _validate_threshold("Dateizahlwachstum", self.warn_file_growth_percent)


@dataclass(frozen=True, slots=True)
class FolderTimelinePoint:
    session_id: int
    recorded_utc: str
    scan_mode: str
    file_count: int
    size_bytes: int
    file_delta: int | None
    file_delta_percent: float | None
    size_delta_bytes: int | None
    size_delta_percent: float | None
    status: str
    status_label: str
    threshold_triggered: bool
    threshold_reasons: tuple[str, ...]
    traffic_level: str
    traffic_label: str
    traffic_reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @property
    def traffic_light(self) -> TrafficLight:
        return TrafficLight(self.traffic_level, self.traffic_label, self.traffic_reason)


@dataclass(frozen=True, slots=True)
class FolderTimeline:
    database: str
    root: str
    folder: str
    total_available_sessions: int
    truncated: bool
    first_session_id: int
    last_session_id: int
    net_file_delta: int
    net_size_delta_bytes: int
    minimum_size_bytes: int
    maximum_size_bytes: int
    warn_size_growth_percent: float | None
    warn_file_growth_percent: float | None
    threshold_trigger_count: int
    points: tuple[FolderTimelinePoint, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["points"] = [point.to_dict() for point in self.points]
        return payload


def normalise_folder(value: str) -> str:
    candidate = value.strip().replace("\\", "/")
    if candidate in {"", ".", "./"}:
        return "."
    path = PurePosixPath(candidate)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Ordnerpfad muss relativ sein und darf kein '..' enthalten")
    normalised = path.as_posix().strip("/")
    return "." if normalised in {"", "."} else normalised


def _validate_threshold(label: str, value: float | None) -> None:
    if value is None:
        return
    if not math.isfinite(value) or not 0 <= value <= _MAX_THRESHOLD_PERCENT:
        raise ValueError(
            f"Warnschwelle {label} muss zwischen 0 und "
            f"{_MAX_THRESHOLD_PERCENT:g} Prozent liegen"
        )


def _readonly_connection(path: Path) -> sqlite3.Connection:
    target = normalise_database_path(path)
    if not target.exists():
        raise FileNotFoundError(f"Indexdatenbank nicht gefunden: {target}")
    uri = f"file:{quote(str(target), safe='/')}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    if version > SCHEMA_VERSION:
        connection.close()
        raise UnsupportedSchemaError(
            f"Datenbankschema {version} ist neuer als unterstützte Version {SCHEMA_VERSION}."
        )
    if version < 3:
        connection.close()
        raise ValueError(
            "Ordner-Zeitreihe benötigt SQLite-Schema 3. "
            "Öffne den Index einmal mit einem aktuellen DATENBANKTOOL-Befehl."
        )
    return connection


def _complete_session(connection: sqlite3.Connection, session_id: int) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM scan_sessions WHERE id=?",
        (session_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Scan-Sitzung {session_id} wurde nicht gefunden")
    if str(row["status"]) != "complete":
        raise ValueError(f"Scan-Sitzung {session_id} ist nicht abgeschlossen")
    return row


def _target_session(
    connection: sqlite3.Connection,
    session_id: int | None,
) -> sqlite3.Row:
    if session_id is not None:
        return _complete_session(connection, session_id)
    row = connection.execute(
        "SELECT * FROM scan_sessions "
        "WHERE status='complete' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        raise ValueError("Keine abgeschlossene Scan-Sitzung gefunden")
    return row


def _session_rows(
    connection: sqlite3.Connection,
    *,
    target: sqlite3.Row,
    from_session_id: int | None,
    limit: int,
) -> tuple[tuple[sqlite3.Row, ...], int, bool]:
    root = str(target["root"])
    lower_id = 0
    if from_session_id is not None:
        baseline = _complete_session(connection, from_session_id)
        if int(baseline["id"]) > int(target["id"]):
            raise ValueError("Ausgangssitzung darf nicht neuer als die Zielsitzung sein")
        if os.path.normpath(str(baseline["root"])) != os.path.normpath(root):
            raise ValueError(
                "Ordner-Zeitreihe benötigt Sitzungen desselben Stammordners"
            )
        lower_id = int(baseline["id"])
    rows = tuple(
        connection.execute(
            """
            SELECT id, root, scan_mode, started_utc, updated_utc, finished_utc
            FROM scan_sessions
            WHERE status='complete' AND root=? AND id>=? AND id<=?
            ORDER BY id
            """,
            (root, lower_id, int(target["id"])),
        )
    )
    total = len(rows)
    truncated = total > limit
    selected = rows[-limit:] if truncated else rows
    if len(selected) < 2:
        raise ValueError(
            "Ordner-Zeitreihe benötigt mindestens zwei abgeschlossene Scans "
            "desselben Stammordners"
        )
    return selected, total, truncated


def _folder_totals(
    connection: sqlite3.Connection,
    *,
    session_id: int,
    folder: str,
) -> tuple[int, int]:
    if folder == ".":
        row = connection.execute(
            "SELECT COUNT(*) AS file_count, COALESCE(SUM(size_bytes), 0) AS size_bytes "
            "FROM files WHERE session_id=?",
            (session_id,),
        ).fetchone()
    else:
        prefix = folder + "/"
        row = connection.execute(
            """
            SELECT COUNT(*) AS file_count, COALESCE(SUM(size_bytes), 0) AS size_bytes
            FROM files
            WHERE session_id=? AND substr(relative_path, 1, ?) = ?
            """,
            (session_id, len(prefix), prefix),
        ).fetchone()
    return int(row["file_count"]), int(row["size_bytes"])


def _status(
    previous_files: int,
    previous_size: int,
    current_files: int,
    current_size: int,
) -> str:
    if previous_files == 0 and current_files > 0:
        return "new"
    if previous_files > 0 and current_files == 0:
        return "removed"
    if current_size > previous_size:
        return "grown"
    if current_size < previous_size:
        return "shrunk"
    if current_files != previous_files:
        return "changed"
    return "unchanged"


def _change_percent(previous: int, current: int) -> float | None:
    if previous <= 0:
        return None
    return round((current - previous) / previous * 100.0, 2)


def _percent_text(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def _traffic(
    status: str,
    *,
    file_delta: int | None,
    size_delta: int | None,
    file_percent: float | None,
    size_percent: float | None,
    warn_file_percent: float | None,
    warn_size_percent: float | None,
) -> tuple[TrafficLight, tuple[str, ...]]:
    threshold_reasons: list[str] = []
    if (
        size_delta is not None
        and size_delta > 0
        and size_percent is not None
        and warn_size_percent is not None
        and size_percent >= warn_size_percent
    ):
        threshold_reasons.append(
            f"Größe +{_percent_text(size_percent)} % erreicht Warnschwelle "
            f"{_percent_text(warn_size_percent)} %"
        )
    if (
        file_delta is not None
        and file_delta > 0
        and file_percent is not None
        and warn_file_percent is not None
        and file_percent >= warn_file_percent
    ):
        threshold_reasons.append(
            f"Dateizahl +{_percent_text(file_percent)} % erreicht Warnschwelle "
            f"{_percent_text(warn_file_percent)} %"
        )
    if threshold_reasons:
        reason = "; ".join(threshold_reasons) + ". Rein lesender Hinweis, keine Schadensbewertung."
        return TrafficLight("red", "Trendgrenze erreicht", reason), tuple(threshold_reasons)
    if status == "baseline":
        return TrafficLight("green", "Ausgangswert", "erster angezeigter Scan"), ()
    if status == "grown":
        return TrafficLight("yellow", "Gewachsen", "Speicherbedarf ist gestiegen"), ()
    if status == "new":
        return TrafficLight("yellow", "Neu", "Ordner enthält erstmals Dateien"), ()
    if status == "changed":
        return (
            TrafficLight(
                "yellow",
                "Dateizahl geändert",
                f"Größe gleich, Dateidifferenz {file_delta or 0:+d}",
            ),
            (),
        )
    if status == "shrunk":
        return TrafficLight("green", "Kleiner geworden", "Speicherbedarf ist gesunken"), ()
    if status == "removed":
        return (
            TrafficLight(
                "green",
                "Nicht mehr vorhanden",
                "Ordner enthält in diesem Scan keine Dateien",
            ),
            (),
        )
    return TrafficLight("green", "Unverändert", "Größe und Dateizahl sind gleich"), ()


def build_folder_timeline(
    database_path: Path,
    *,
    options: FolderTimelineOptions = FolderTimelineOptions(),
) -> FolderTimeline:
    options.validate()
    folder = normalise_folder(options.folder)
    with closing(_readonly_connection(database_path)) as connection:
        target = _target_session(connection, options.to_session_id)
        sessions, total_available, truncated = _session_rows(
            connection,
            target=target,
            from_session_id=options.from_session_id,
            limit=options.limit,
        )
        points: list[FolderTimelinePoint] = []
        previous_files: int | None = None
        previous_size: int | None = None
        for session in sessions:
            file_count, size_bytes = _folder_totals(
                connection,
                session_id=int(session["id"]),
                folder=folder,
            )
            if previous_files is None or previous_size is None:
                status = "baseline"
                file_delta = None
                file_percent = None
                size_delta = None
                size_percent = None
            else:
                file_delta = file_count - previous_files
                file_percent = _change_percent(previous_files, file_count)
                size_delta = size_bytes - previous_size
                size_percent = _change_percent(previous_size, size_bytes)
                status = _status(
                    previous_files,
                    previous_size,
                    file_count,
                    size_bytes,
                )
            light, threshold_reasons = _traffic(
                status,
                file_delta=file_delta,
                size_delta=size_delta,
                file_percent=file_percent,
                size_percent=size_percent,
                warn_file_percent=options.warn_file_growth_percent,
                warn_size_percent=options.warn_size_growth_percent,
            )
            recorded = str(
                session["finished_utc"]
                or session["updated_utc"]
                or session["started_utc"]
            )
            points.append(
                FolderTimelinePoint(
                    session_id=int(session["id"]),
                    recorded_utc=recorded,
                    scan_mode=str(session["scan_mode"]),
                    file_count=file_count,
                    size_bytes=size_bytes,
                    file_delta=file_delta,
                    file_delta_percent=file_percent,
                    size_delta_bytes=size_delta,
                    size_delta_percent=size_percent,
                    status=status,
                    status_label=_STATUS_LABELS[status],
                    threshold_triggered=bool(threshold_reasons),
                    threshold_reasons=threshold_reasons,
                    traffic_level=light.level,
                    traffic_label=light.label,
                    traffic_reason=light.reason,
                )
            )
            previous_files = file_count
            previous_size = size_bytes

    first = points[0]
    last = points[-1]
    sizes = [point.size_bytes for point in points]
    return FolderTimeline(
        database=str(normalise_database_path(database_path)),
        root=str(target["root"]),
        folder=folder,
        total_available_sessions=total_available,
        truncated=truncated,
        first_session_id=first.session_id,
        last_session_id=last.session_id,
        net_file_delta=last.file_count - first.file_count,
        net_size_delta_bytes=last.size_bytes - first.size_bytes,
        minimum_size_bytes=min(sizes),
        maximum_size_bytes=max(sizes),
        warn_size_growth_percent=options.warn_size_growth_percent,
        warn_file_growth_percent=options.warn_file_growth_percent,
        threshold_trigger_count=sum(point.threshold_triggered for point in points),
        points=tuple(points),
    )
