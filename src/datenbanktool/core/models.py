from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class FileCategory(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    TEXT = "text"
    ARCHIVE = "archive"
    CODE = "code"
    DOCUMENT = "document"
    OTHER = "other"


@dataclass(slots=True)
class FileRecord:
    relative_path: str
    size_bytes: int
    modified_utc: str
    suffix: str
    category: FileCategory
    filename_warnings: list[str] = field(default_factory=list)
    is_symlink: bool = False
    is_large: bool = False
    sha256: str | None = None


@dataclass(slots=True)
class ScanError:
    path: str
    operation: str
    message: str


@dataclass(slots=True)
class DuplicateGroup:
    sha256: str
    size_bytes: int
    paths: list[str]


@dataclass(slots=True)
class ScanReport:
    root: str
    started_utc: str
    finished_utc: str
    files: list[FileRecord]
    errors: list[ScanError]
    duplicate_groups: list[DuplicateGroup]
    category_counts: dict[str, int]
    total_size_bytes: int
    large_file_count: int
    truncated: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
