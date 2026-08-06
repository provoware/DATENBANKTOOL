from __future__ import annotations

import os
import tempfile
from pathlib import Path


def _absolute_path(path: Path) -> Path:
    """Normalize spelling without following the final path component."""
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _sync_directory(path: Path) -> None:
    """Persist a completed directory entry change where the platform supports it."""
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
    source = _absolute_path(temporary)
    destination = _absolute_path(target)
    if source.is_symlink() or not source.is_file():
        raise ValueError("Temporärdatei muss eine normale Datei sein")
    if source.parent != destination.parent:
        raise ValueError("Temporärdatei und Ziel müssen im selben Ordner liegen")
    if destination.is_symlink():
        raise ValueError(f"Symbolische Verknüpfung wird nicht überschrieben: {destination}")
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Datei existiert bereits: {destination}")
    sync_file(source)
    if mode is not None:
        os.chmod(source, mode)
    if destination.is_symlink():
        raise ValueError(f"Symbolische Verknüpfung wird nicht überschrieben: {destination}")
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
    target = _absolute_path(path)
    if target.is_symlink():
        raise ValueError(f"Symbolische Verknüpfung wird nicht überschrieben: {target}")
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


def durable_remove(path: Path, *, missing_ok: bool = False) -> bool:
    """Remove exactly one regular file and persist the directory entry change."""
    target = _absolute_path(path)
    if target.is_symlink():
        raise ValueError(f"Symbolische Verknüpfung wird nicht entfernt: {target}")
    if not target.exists():
        if missing_ok:
            return False
        raise FileNotFoundError(f"Datei nicht gefunden: {target}")
    if not target.is_file():
        raise ValueError(f"Nur eine normale Datei darf entfernt werden: {target}")
    target.unlink()
    _sync_directory(target.parent)
    return True
