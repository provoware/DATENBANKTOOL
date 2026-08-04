from __future__ import annotations

import csv
import html
import io
import json
import os
from dataclasses import dataclass
from pathlib import Path

from datenbanktool.core.folder_compare import FolderComparisonPage


@dataclass(frozen=True, slots=True)
class FolderComparisonExportResult:
    row_count: int
    json_path: str | None
    csv_path: str | None
    html_path: str | None


def _atomic_bytes(path: Path, content: bytes, *, overwrite: bool) -> str:
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


def _human_size(size_bytes: int) -> str:
    value = float(abs(size_bytes))
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{int(value)} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{abs(size_bytes)} B"


def _signed_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    sign = "+" if size_bytes > 0 else "−"
    return sign + _human_size(size_bytes)


def export_folder_comparison(
    page: FolderComparisonPage,
    *,
    json_path: Path | None = None,
    csv_path: Path | None = None,
    html_path: Path | None = None,
    overwrite: bool = False,
) -> FolderComparisonExportResult:
    json_result = None
    csv_result = None
    html_result = None
    if json_path is not None:
        content = json.dumps(page.to_dict(), ensure_ascii=False, indent=2) + "\n"
        json_result = _atomic_bytes(
            json_path,
            content.encode("utf-8"),
            overwrite=overwrite,
        )
    if csv_path is not None:
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(
            (
                "Status",
                "Ordner",
                "Dateien vorher",
                "Dateien nachher",
                "Dateidifferenz",
                "Größe vorher Byte",
                "Größe nachher Byte",
                "Größendifferenz Byte",
                "Größendifferenz Prozent",
                "Ampel",
                "Begründung",
            )
        )
        for row in page.rows:
            writer.writerow(
                (
                    row.change_label,
                    row.folder,
                    row.before_files,
                    row.after_files,
                    row.file_delta,
                    row.before_size_bytes,
                    row.after_size_bytes,
                    row.size_delta_bytes,
                    "" if row.size_delta_percent is None else row.size_delta_percent,
                    row.traffic_label,
                    row.traffic_reason,
                )
            )
        csv_result = _atomic_bytes(
            csv_path,
            stream.getvalue().encode("utf-8-sig"),
            overwrite=overwrite,
        )
    if html_path is not None:
        rows = []
        for row in page.rows:
            percent = (
                "–"
                if row.size_delta_percent is None
                else f"{row.size_delta_percent:+.2f} %"
            )
            tooltip = html.escape(row.traffic_reason, quote=True)
            rows.append(
                "<tr>"
                f"<td><span class=\"light {row.traffic_level}\" title=\"{tooltip}\" "
                f"aria-label=\"{html.escape(row.traffic_label)}: {tooltip}\">"
                f"● {html.escape(row.traffic_label)}</span></td>"
                f"<td>{html.escape(row.folder)}</td>"
                f"<td>{html.escape(row.change_label)}</td>"
                f"<td>{row.before_files}</td><td>{row.after_files}</td>"
                f"<td>{row.file_delta:+d}</td>"
                f"<td>{_human_size(row.before_size_bytes)}</td>"
                f"<td>{_human_size(row.after_size_bytes)}</td>"
                f"<td>{_signed_size(row.size_delta_bytes)}</td>"
                f"<td>{percent}</td>"
                "</tr>"
            )
        document = f"""<!doctype html>
<html lang=\"de\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\">
<title>DATENBANKTOOL – Ordnervergleich</title>
<style>
body{{font-family:system-ui,sans-serif;margin:1.5rem;background:#f6f7f9;color:#15171a}}
.hint{{background:#e8f4ff;padding:.8rem;border-radius:.5rem}}table{{width:100%;border-collapse:collapse;background:white;margin-top:1rem}}
th,td{{padding:.6rem;border:1px solid #c8ccd0;text-align:left;vertical-align:top}}
th{{background:#e9ecef}}.light{{font-weight:700}}.green{{color:#176b2c}}.yellow{{color:#7a5600}}.red{{color:#a11b1b}}
</style></head><body>
<h1>Ordnervergleich</h1>
<p>Stammordner: {html.escape(page.root)}<br>Vergleich: Scan #{page.from_session_id} → #{page.to_session_id}</p>
<p class=\"hint\">Reine Auswertung gespeicherter Scans. Grün, Gelb und Rot werden immer durch Status und Begründung ergänzt.</p>
<table><thead><tr><th>Ampel</th><th>Ordner</th><th>Zustand</th><th>Dateien vorher</th><th>Dateien nachher</th><th>Δ Dateien</th><th>Größe vorher</th><th>Größe nachher</th><th>Δ Größe</th><th>Δ Prozent</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</body></html>
"""
        html_result = _atomic_bytes(
            html_path,
            document.encode("utf-8"),
            overwrite=overwrite,
        )
    return FolderComparisonExportResult(
        row_count=len(page.rows),
        json_path=json_result,
        csv_path=csv_result,
        html_path=html_result,
    )
