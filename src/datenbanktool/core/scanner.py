from __future__ import annotations

import hashlib
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from datenbanktool.core.classification import classify_path
from datenbanktool.core.models import DuplicateGroup, FileRecord, ScanError, ScanReport
from datenbanktool.core.naming import filename_warnings

_HASH_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True, slots=True)
class ScanOptions:
    root: Path
    hash_duplicates: bool = False
    large_file_bytes: int = 1024 * 1024 * 1024
    follow_symlinks: bool = False
    max_files: int | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_HASH_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def scan_tree(options: ScanOptions) -> ScanReport:
    root = options.root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"Kein Verzeichnis: {root}")
    if options.large_file_bytes < 0:
        raise ValueError("large_file_bytes darf nicht negativ sein")
    if options.max_files is not None and options.max_files < 1:
        raise ValueError("max_files muss mindestens 1 sein")

    started_utc = _utc_now()
    records: list[FileRecord] = []
    errors: list[ScanError] = []
    truncated = False

    def on_walk_error(error: OSError) -> None:
        errors.append(ScanError(path=str(getattr(error, "filename", root)), operation="walk", message=str(error)))

    for current_root, directory_names, file_names in os.walk(root, followlinks=options.follow_symlinks, onerror=on_walk_error):
        current_path = Path(current_root)
        if not options.follow_symlinks:
            directory_names[:] = [name for name in directory_names if not (current_path / name).is_symlink()]

        for file_name in file_names:
            if options.max_files is not None and len(records) >= options.max_files:
                truncated = True
                break
            path = current_path / file_name
            try:
                stat_result = path.stat(follow_symlinks=options.follow_symlinks)
            except OSError as error:
                errors.append(ScanError(path=path.as_posix(), operation="stat", message=str(error)))
                continue
            relative_path = path.relative_to(root).as_posix()
            records.append(FileRecord(
                relative_path=relative_path,
                size_bytes=stat_result.st_size,
                modified_utc=datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc).isoformat(),
                suffix=path.suffix.casefold(),
                category=classify_path(path),
                filename_warnings=filename_warnings(path.name),
                is_symlink=path.is_symlink(),
                is_large=stat_result.st_size >= options.large_file_bytes,
            ))
        if truncated:
            break

    records.sort(key=lambda record: record.relative_path.casefold())
    duplicate_groups: list[DuplicateGroup] = []

    if options.hash_duplicates:
        by_size: dict[int, list[FileRecord]] = defaultdict(list)
        for record in records:
            if not record.is_symlink and record.size_bytes > 0:
                by_size[record.size_bytes].append(record)
        for size_bytes, candidates in sorted(by_size.items()):
            if len(candidates) < 2:
                continue
            by_hash: dict[str, list[FileRecord]] = defaultdict(list)
            for record in candidates:
                try:
                    record.sha256 = _sha256(root / record.relative_path)
                except OSError as error:
                    errors.append(ScanError(path=record.relative_path, operation="sha256", message=str(error)))
                    continue
                by_hash[record.sha256].append(record)
            for digest, matches in sorted(by_hash.items()):
                if len(matches) > 1:
                    duplicate_groups.append(DuplicateGroup(
                        sha256=digest,
                        size_bytes=size_bytes,
                        paths=sorted((record.relative_path for record in matches), key=str.casefold),
                    ))

    category_counts = Counter(record.category.value for record in records)
    return ScanReport(
        root=str(root),
        started_utc=started_utc,
        finished_utc=_utc_now(),
        files=records,
        errors=errors,
        duplicate_groups=duplicate_groups,
        category_counts=dict(sorted(category_counts.items())),
        total_size_bytes=sum(record.size_bytes for record in records),
        large_file_count=sum(record.is_large for record in records),
        truncated=truncated,
    )
