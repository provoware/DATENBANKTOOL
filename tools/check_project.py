from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
TOOL_SCHEMA = json.loads((ROOT / "TOOL_SCHEMA.json").read_text(encoding="utf-8"))

TYPE_BY_SUFFIX = {
    ".py": "python",
    ".js": "javascript",
    ".css": "css",
    ".html": "html",
    ".md": "markdown",
    ".json": "json",
}

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "data/user",
    "config/local",
    "logs",
    "runtime",
    "backups",
}

BASE_REQUIRED_FILES = [
    "README.md",
    "TODO.md",
    "CHANGELOG.md",
    "FORTSCHRITTSINFO.md",
    "ENTWICKLUNGSPLAN.md",
    "TOOL_SCHEMA.json",
    "ORDNER_UND_DATEIINDEX.md",
    "docs/ENTWICKLUNGSDISZIPLIN.md",
]
REQUIRED_FILES = tuple(dict.fromkeys([*BASE_REQUIRED_FILES, *TOOL_SCHEMA["critical_files"]]))


def excluded(path: Path) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    if relative in {"logs/README.md", "runtime/README.md"}:
        return False
    return any(relative == part or relative.startswith(part + "/") for part in EXCLUDED_PARTS)


def check_file(path: Path, kind: str) -> list[str]:
    rules = MANIFEST["file_limits"][kind]
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    errors: list[str] = []
    relative = path.relative_to(ROOT)
    if len(lines) > rules["max_lines"]:
        errors.append(f"{relative}: {len(lines)} Zeilen > Maximum {rules['max_lines']}")

    long_lines: list[int] = []
    for index, line in enumerate(lines, 1):
        if len(line) > rules["max_line_length"]:
            long_lines.append(index)
    if long_lines:
        preview = ", ".join(map(str, long_lines[:5]))
        errors.append(f"{relative}: Zeilen über {rules['max_line_length']} Zeichen: {preview}")
    return errors


def main() -> int:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        if not (ROOT / name).is_file():
            errors.append(f"Pflichtdatei fehlt: {name}")

    for path in ROOT.rglob("*"):
        if not path.is_file() or excluded(path):
            continue
        kind = TYPE_BY_SUFFIX.get(path.suffix.lower())
        if kind:
            errors.extend(check_file(path, kind))

    print("PROVOWARE PROJEKTPRÜFUNG")
    print("=" * 60)
    if errors:
        print("🔴 FAIL")
        for error in errors:
            print(f"- {error}")
        return 2
    print("🟢 PASS · Pflichtdateien und harte Dateigrenzen eingehalten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
