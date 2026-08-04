from __future__ import annotations

import csv
import io
import os
from pathlib import Path

from datenbanktool.core.folders import FolderPage


def _write_atomic_bytes(path: Path, content: bytes, *, overwrite: bool) -> str:
    target = path.expanduser().resolve(strict=False)
    if target.exists() and not overwrite:
        raise FileExistsError(
            f"Bericht existiert bereits: {target}. Nutze --overwrite-report."
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    try:
        temporary.write_bytes(content)
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return str(target)


def export_folder_csv(
    page: FolderPage,
    path: Path,
    *,
    overwrite: bool = False,
) -> str:
    """Write a LibreOffice-friendly folder overview with stable columns."""

    largest_count = max((len(row.largest_files) for row in page.rows), default=0)
    header = [
        "Ampelstufe",
        "Ampelstatus",
        "Ampelbegründung",
        "Ordner",
        "Ordnertiefe",
        "Dateien direkt",
        "Dateien mit Unterordnern",
        "Größe direkt Byte",
        "Gesamtgröße Byte",
        "Namenshinweise",
        "Dateien in Duplikatgruppen",
    ]
    for index in range(1, largest_count + 1):
        header.extend((f"Platzfresser {index} Pfad", f"Platzfresser {index} Byte"))

    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=";", lineterminator="\n")
    writer.writerow(header)
    for row in page.rows:
        values: list[object] = [
            row.traffic_level,
            row.traffic_label,
            row.traffic_reason,
            row.folder,
            row.depth,
            row.direct_files,
            row.total_files,
            row.direct_size_bytes,
            row.total_size_bytes,
            row.warning_files,
            row.duplicate_files,
        ]
        for index in range(largest_count):
            if index < len(row.largest_files):
                item = row.largest_files[index]
                values.extend((item.relative_path, item.size_bytes))
            else:
                values.extend(("", ""))
        writer.writerow(values)

    return _write_atomic_bytes(
        path,
        stream.getvalue().encode("utf-8-sig"),
        overwrite=overwrite,
    )
