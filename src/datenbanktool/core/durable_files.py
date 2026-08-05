from __future__ import annotations

import os
import tempfile
from pathlib import Path


def _sync_directory(path: Path) -> None:
    """Persist a completed rename where the platform supports directory fsync."""
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def sync_file(path: Path) -> None:
    """Flush one already written file before it becomes the visible final version."""
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def publish_temp_file(
    temporary: Path,
    target: Path,
    *,
    overwrite: bool = False,
    mode: int | None = None,
) -> str:
    """Durably publish a fully prepared same-directory temporary file."""
    source = temporary.expanduser().resolve(strict=True)
    destination = target.expanduser().resolve(strict=False)
    if source.parent != destination.parent:
        raise ValueError("Temporärdatei und Ziel müssen im selben Ordner liegen")
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Datei existiert bereits: {destination}")
    sync_file(source)
    if mode is not None:
        os.chmod(source, mode)
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Datei existiert bereits: {destination}")
    os.replace(source, destination)
    _sync_directory(destination.parent)
    return str(destination)


def atomic_write_bytes(
    path: Path,
    content: bytes,
    *,
    overwrite: bool = False,
    mode: int | None = None,
) -> str:
    """Write, flush and atomically publish one file without exposing partial data."""
    target = path.expanduser().resolve(strict=False)
    if target.exists() and not overwrite:
        raise FileExistsError(f"Datei existiert bereits: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.tmp-",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        publish_temp_file(
            temporary,
            target,
            overwrite=overwrite,
            mode=mode,
        )
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return str(target)


def atomic_write_text(
    path: Path,
    content: str,
    *,
    overwrite: bool = False,
    mode: int | None = None,
    encoding: str = "utf-8",
) -> str:
    return atomic_write_bytes(
        path,
        content.encode(encoding),
        overwrite=overwrite,
        mode=mode,
    )
