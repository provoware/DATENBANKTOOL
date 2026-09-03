from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_base_ui_files_exist() -> None:
    assert (ROOT / "src" / "web" / "index.html").is_file()
    assert (ROOT / "src" / "web" / "app.js").is_file()
    assert (ROOT / "src" / "web" / "styles.css").is_file()


def test_runtime_directories_are_documented() -> None:
    assert (ROOT / "data" / "README.md").is_file()
    assert (ROOT / "logs" / "README.md").is_file()
    assert (ROOT / "runtime" / "README.md").is_file()
