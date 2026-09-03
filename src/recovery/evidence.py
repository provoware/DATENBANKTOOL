from __future__ import annotations

import json
import os
import tempfile
from contextlib import suppress
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.logging_core import sanitize_details

FINAL_STATES = {"COMMITTED", "ROLLED_BACK", "REJECTED", "FAILED"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class RecoveryEvidence:
    schema_version: int
    operation_id: str
    operation_kind: str
    target: str
    state: str
    started_at: str
    finished_at: str
    key_hash: str | None
    transitions: tuple[str, ...]
    details: dict[str, Any]
    error_type: str | None = None


class EvidenceJournal:
    """Durable evidence outside the business-data transaction."""

    def __init__(self, runtime_dir: Path) -> None:
        self.root = Path(runtime_dir) / "recovery"
        self.root.mkdir(parents=True, exist_ok=True)
        self.journal_path = self.root / "recovery_journal_status_laufend.jsonl"
        self.evidence_dir = self.root / "evidence"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def append_transition(
        self,
        *,
        operation_id: str,
        operation_kind: str,
        target: str,
        state: str,
        key_hash: str | None,
        details: dict[str, Any] | None = None,
    ) -> None:
        record = {
            "schema_version": 1,
            "operation_id": operation_id,
            "operation_kind": operation_kind,
            "target": target,
            "state": state,
            "timestamp": _utc_now(),
            "key_hash": key_hash,
            "details": sanitize_details(details or {}),
        }
        line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        with self.journal_path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())

    def write_final(self, evidence: RecoveryEvidence) -> Path:
        safe_state = evidence.state.lower().replace("_", "-")
        filename = f"recovery_evidence_status_{safe_state}_{evidence.operation_id}.json"
        destination = self.evidence_dir / filename
        data = asdict(evidence)
        data["details"] = sanitize_details(evidence.details)
        payload = json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"
        self._atomic_write(destination, payload)
        return destination

    def find_completed_key(self, key_hash: str, *, limit: int = 250) -> Path | None:
        files = sorted(
            self.evidence_dir.glob("recovery_evidence_status_*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for path in files[:limit]:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("key_hash") == key_hash and data.get("state") == "COMMITTED":
                return path
        return None

    def incomplete_operations(self) -> dict[str, dict[str, Any]]:
        if not self.journal_path.exists():
            return {}
        latest: dict[str, dict[str, Any]] = {}
        try:
            lines = self.journal_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return {}
        for line in lines:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            operation_id = str(record.get("operation_id") or "")
            if operation_id:
                latest[operation_id] = record
        return {
            operation_id: record
            for operation_id, record in latest.items()
            if record.get("state") not in FINAL_STATES
        }

    @staticmethod
    def _atomic_write(destination: Path, payload: str) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(
            prefix=destination.name + ".",
            suffix=".tmp",
            dir=destination.parent,
            text=True,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, destination)
        finally:
            with suppress(FileNotFoundError):
                os.unlink(temporary_name)
