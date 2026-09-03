import subprocess
import sys
from pathlib import Path

from src import server
from src.logging_core import EventLogger
from src.recovery import EvidenceJournal

ROOT = Path(__file__).resolve().parents[1]


def test_server_module_cli_imports_cleanly() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "src.server", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "PROVOWARE DATENBANKTOOL Clean Foundation" in result.stdout


def test_recovery_start_gate_accepts_clean_journal(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(server, "ROOT", tmp_path)
    logger = EventLogger(tmp_path)

    assert server._check_recovery_state(logger) is True


def test_recovery_start_gate_blocks_incomplete_operation(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(server, "ROOT", tmp_path)
    journal = EvidenceJournal(tmp_path / "runtime")
    journal.append_transition(
        operation_id="op-incomplete",
        operation_kind="entry.create",
        target="entry:test",
        state="COMMITTING",
        key_hash=None,
    )
    logger = EventLogger(tmp_path)

    assert server._check_recovery_state(logger) is False
    log_text = logger.machine_path.read_text(encoding="utf-8")
    assert "PRV-REC-001" in log_text
