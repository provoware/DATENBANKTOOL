from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import BinaryIO


@dataclass(frozen=True, slots=True)
class RestoreAuditIdentity:
    protocol: str
    expected_sha256: str
    actual_sha256: str
    matches: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def require_sha256(value: str, label: str = "Erwartete Protokoll-SHA-256") -> str:
    if len(value) != 64:
        raise ValueError(f"{label} muss genau 64 hexadezimale Zeichen enthalten.")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} muss ein kleingeschriebener SHA-256-Wert sein.")
    return value


def _open_regular_no_follow(path: Path) -> BinaryIO:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        information = os.fstat(descriptor)
        if not stat.S_ISREG(information.st_mode):
            raise ValueError(f"Pfad ist keine normale Datei: {path}")
        return os.fdopen(descriptor, "rb")
    except BaseException:
        os.close(descriptor)
        raise


def verify_restore_audit_identity(
    protocol: Path,
    expected_sha256: str,
) -> RestoreAuditIdentity:
    """Confirm one explicitly selected protocol before any JSON schema evaluation."""
    expected = require_sha256(expected_sha256)
    target = _absolute(protocol)
    if target.is_symlink():
        raise ValueError(
            f"Symbolische Verknüpfung wird nicht als Wiederherstellungsprotokoll gelesen: {target}"
        )
    try:
        with _open_regular_no_follow(target) as stream:
            digest = hashlib.sha256()
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"Wiederherstellungsprotokoll nicht gefunden: {target}"
        ) from error
    actual = digest.hexdigest()
    if actual != expected:
        raise ValueError(
            "Die ausdrücklich erwartete SHA-256 stimmt nicht mit der ausgewählten "
            f"Protokolldatei überein: erwartet {expected}, tatsächlich {actual}."
        )
    return RestoreAuditIdentity(
        protocol=str(target),
        expected_sha256=expected,
        actual_sha256=actual,
        matches=True,
    )
