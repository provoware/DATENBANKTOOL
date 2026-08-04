from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from datenbanktool import __version__
from datenbanktool.core.scanner import ScanOptions, scan_tree


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="datenbanktool", description="Rein lesende Basisanalyse großer Linux-Datensammlungen.")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan", help="Verzeichnis sicher und rein lesend prüfen")
    scan.add_argument("path", type=Path)
    scan.add_argument("--json", dest="json_path", type=Path)
    scan.add_argument("--overwrite-report", action="store_true")
    scan.add_argument("--hash-duplicates", action="store_true")
    scan.add_argument("--large-file-mib", type=int, default=1024)
    scan.add_argument("--max-files", type=int, default=None)
    scan.add_argument("--follow-symlinks", action="store_true")
    return parser


def _write_json_atomic(path: Path, payload: dict[str, object], overwrite: bool) -> None:
    target = path.expanduser()
    if target.exists() and not overwrite:
        raise FileExistsError(f"Bericht existiert bereits: {target}. Nutze --overwrite-report zum Ersetzen.")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)


def _run_scan(arguments: argparse.Namespace) -> int:
    if arguments.large_file_mib < 0:
        raise ValueError("--large-file-mib darf nicht negativ sein")
    report = scan_tree(ScanOptions(
        root=arguments.path,
        hash_duplicates=arguments.hash_duplicates,
        large_file_bytes=arguments.large_file_mib * 1024 * 1024,
        follow_symlinks=arguments.follow_symlinks,
        max_files=arguments.max_files,
    ))
    print(f"Wurzel: {report.root}")
    print(f"Dateien: {len(report.files)}")
    print(f"Gesamtgröße: {report.total_size_bytes} Byte")
    print(f"Große Dateien: {report.large_file_count}")
    print(f"Exakte Duplikatgruppen: {len(report.duplicate_groups)}")
    print(f"Lesefehler: {len(report.errors)}")
    print(f"Abgebrochen durch Dateigrenze: {'ja' if report.truncated else 'nein'}")
    if arguments.json_path is not None:
        _write_json_atomic(arguments.json_path, report.to_dict(), overwrite=arguments.overwrite_report)
        print(f"JSON-Bericht: {arguments.json_path.expanduser()}")
    return 1 if report.errors else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "scan":
            return _run_scan(arguments)
    except (FileExistsError, NotADirectoryError, OSError, ValueError) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 2
    parser.error("Unbekannter Befehl")
    return 2
