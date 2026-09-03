from __future__ import annotations

import threading
from pathlib import Path


class DatabaseOperationGate:
    """Process-local exclusive gate shared by mutations and restore swaps."""

    _registry_guard = threading.Lock()
    _locks: dict[str, threading.Lock] = {}

    def __init__(self, database_path: Path) -> None:
        key = str(Path(database_path).resolve())
        with self._registry_guard:
            self._lock = self._locks.setdefault(key, threading.Lock())

    def acquire(self) -> bool:
        return self._lock.acquire(blocking=False)

    def release(self) -> None:
        self._lock.release()
