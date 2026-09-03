import subprocess
import sys
from pathlib import Path

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
