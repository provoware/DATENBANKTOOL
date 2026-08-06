from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 3
DEFAULT_BATCH_SIZE = 500
DEFAULT_AUTOSAVE_SECONDS = 5.0
VALID_PHASES = frozenset({"scanning", "hashing", "finalizing", "complete"})


class IndexErrorBase(RuntimeError):
    """Base class for index-specific errors."""


class UnsupportedSchemaError(IndexErrorBase):
    """Raised when a database is newer than this program."""


class ResumeCheckpointError(IndexErrorBase):
    """Raised when a safe resume checkpoint cannot be found."""


@dataclass(frozen=True, slots=True)
class IndexBuildOptions:
    root: Path
    database: Path
    hash_duplicates: bool = False
    large_file_bytes: int = 1024 * 1024 * 1024
    follow_symlinks: bool = False
    batch_size: int = DEFAULT_BATCH_SIZE
    autosave_seconds: float = DEFAULT_AUTOSAVE_SECONDS
    resume: bool = False
    max_files: int | None = None
    lock_timeout_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class IndexBuildResult:
    database: str
    session_id: int
    status: str
    phase: str
    imported_count: int
    error_count: int
    duplicate_group_count: int
    resumed: bool
    schema_version: int


@dataclass(frozen=True, slots=True)
class IndexStatus:
    database: str
    schema_version: int
    session_id: int | None
    root: str | None
    status: str | None
    phase: str | None
    imported_count: int
    error_count: int
    duplicate_group_count: int
    updated_utc: str | None
    scan_mode: str | None = None
    parent_session_id: int | None = None


@dataclass(frozen=True, slots=True)
class RepairResult:
    database: str
    backup: str | None
    before_integrity: tuple[str, ...]
    after_integrity: tuple[str, ...]
    foreign_key_errors: int
    interrupted_sessions: int
    rebuilt_duplicate_sessions: int
    actions: tuple[str, ...]
    successful: bool


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalise_database_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def source_fingerprint(root: Path, payload: dict[str, object]) -> str:
    encoded = json.dumps(
        {"root": str(root), **payload}, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
