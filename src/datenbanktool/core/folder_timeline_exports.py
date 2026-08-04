from __future__ import annotations

import csv
import html
import io
import json
import os
from dataclasses import dataclass
from pathlib import Path

from datenbanktool.core.folder_timeline import FolderTimeline


@dataclass(frozen=True, slots=True)
class FolderTimelineExportResult:
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


def _signed_size(value: int | None) -> str:
    if value is None:
        return "–"
    if value == 0:
        return "0 B"
    return ("+" if value > 0 else "−") + _human_size(value)


def export_folder_timeline(
    timeline: FolderTimeline,
    *,
    json_path: Path | None = None,
    csv_path: Path | None = None,
    html_path: Path | None = None,
    overwrite: bool = False,
) -> FolderTimelineExportResult:
    json_result = None
    csv_result = None
    html_result = None
    if json_path is not None:
        content = json.dumps(timeline.to_dict(), ensure_ascii=False, indent=2) + "\n"
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
                "Scan-ID",
                "Zeitpunkt UTC",
                "Scan-Modus",
                "Status",
                "Dateien",
                "Dateidifferenz",
                "Größe Byte",
                "Größendifferenz Byte",
                "Größendifferenz Prozent",
                "Ampel",
                "Begründung",
                "Ordner",
                "Stammordner",
            )
        )
        for point in timeline.points:
            writer.writerow(
                (
                    point.session_id,
                    point.recorded_utc,
                    point.scan_mode,
                    point.status_label,
                    point.file_count,
                    "" if point.file_delta is None else point.file_delta,
                    point.size_bytes,
                    "" if point.size_delta_bytes is None else point.size_delta_bytes,
                    "" if point.size_delta_percent is None else point.size_delta_percent,
                    point.traffic_label,
                    point.traffic_reason,
                    timeline.folder,
                    timeline.root,
                )
            )
        csv_result = _atomic_bytes(
            csv_path,
            stream.getvalue().encode("utf-8-sig"),
            overwrite=overwrite,
        )
    if html_path is not None:
        rows: list[str] = []
        for point in timeline.points:
            percent = (
                "–"
                if point.size_delta_percent is None
                else f"{point.size_delta_percent:+.2f} %"
            )
            file_delta = "–" if point.file_delta is None else f"{point.file_delta:+d}"
            tooltip = html.escape(point.traffic_reason, quote=True)
            rows.append(
                "<tr>"
                f"<td>#{point.session_id}</td>"
                f"<td>{html.escape(point.recorded_utc)}</td>"
                f"<td>{html.escape(point.scan_mode)}</td>"
                f"<td><span class=\"light {point.traffic_level}\" "
                f"title=\"{tooltip}\" aria-label=\"{html.escape(point.traffic_label)}: "
                f"{tooltip}\">● {html.escape(point.traffic_label)}</span></td>"
                f"<td>{point.file_count}</td>"
                f"<td>{file_delta}</td>"
                f"<td>{_human_size(point.size_bytes)}</td>"
                f"<td>{_signed_size(point.size_delta_bytes)}</td>"
                f"<td>{percent}</td>"
                "</tr>"
            )
        truncation = (
            f"Es werden die neuesten {len(timeline.points)} von "
            f"{timeline.total_available_sessions} passenden Scans gezeigt."
            if timeline.truncated
            else f"Alle {len(timeline.points)} passenden Scans werden gezeigt."
        )
        document = f"""<!doctype html>
<html lang=\"de\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\">
<title>DATENBANKTOOL – Ordner-Zeitreihe</title>
<style>
body{{font-family:system-ui,sans-serif;margin:1.5rem;background:#f6f7f9;color:#15171a}}
.hint{{background:#e8f4ff;padding:.8rem;border-radius:.5rem}}table{{width:100%;border-collapse:collapse;background:white;margin-top:1rem}}
th,td{{padding:.6rem;border:1px solid #c8ccd0;text-align:left;vertical-align:top}}
th{{background:#e9ecef;position:sticky;top:0}}.light{{font-weight:700}}
.green{{color:#176b2c}}.yellow{{color:#7a5600}}.red{{color:#a11b1b}}
</style></head><body>
<h1>Ordner-Zeitreihe</h1>
<p>Stammordner: {html.escape(timeline.root)}<br>Ordner: {html.escape(timeline.folder)}<br>
Scans: #{timeline.first_session_id} bis #{timeline.last_session_id}</p>
<p class=\"hint\">Reine Auswertung gespeicherter Scans. {html.escape(truncation)}
Elternordner enthalten ihre Unterordner. Farben werden immer durch Klartext ergänzt.</p>
<table><thead><tr><th>Scan</th><th>Zeitpunkt UTC</th><th>Modus</th><th>Status</th>
<th>Dateien</th><th>Δ Dateien</th><th>Größe</th><th>Δ Größe</th><th>Δ Prozent</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</body></html>
"""
        html_result = _atomic_bytes(
            html_path,
            document.encode("utf-8"),
            overwrite=overwrite,
        )
    return FolderTimelineExportResult(
        row_count=len(timeline.points),
        json_path=json_result,
        csv_path=csv_result,
        html_path=html_result,
    )
