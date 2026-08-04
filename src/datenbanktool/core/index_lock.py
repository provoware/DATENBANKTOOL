from __future__ import annotations

import fcntl
import json
import os
import socket
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO


class IndexLockedError(RuntimeError):
    """Raised when another DATENBANKTOOL process owns the index lock."""


@dataclass(frozen=True, slots=True)
class LockInfo:
    pid: int
    host: str
    started_utc: str
    operation: str
    database: str


class IndexProcessLock:
    def __init__(self, database: Path, operation: str, timeout_seconds: float = 0.0) -> None:
        if timeout_seconds < 0:
            raise ValueError("lock timeout darf nicht negativ sein")
        self.database = database.expanduser().resolve(strict=False)
        self.path = self.database.with_name(f"{self.database.name}.lock")
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        self._handle: TextIO | None = None

    def __enter__(self) -> "IndexProcessLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+", encoding="utf-8")
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    handle.seek(0)
                    owner = handle.read().strip() or "unbekannter Prozess"
                    handle.close()
                    raise IndexLockedError(
                        f"Index ist bereits gesperrt: {self.database}. Besitzer: {owner}"
                    )
                time.sleep(0.1)
        self._handle = handle
        info = LockInfo(
            pid=os.getpid(),
            host=socket.gethostname(),
            started_utc=datetime.now(timezone.utc).isoformat(),
            operation=self.operation,
            database=str(self.database),
        )
        handle.seek(0)
        handle.truncate()
        json.dump(asdict(info), handle, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._handle is None:
            return
        try:
            self._handle.seek(0)
            self._handle.truncate()
            self._handle.flush()
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._handle.close()
            self._handle = None
