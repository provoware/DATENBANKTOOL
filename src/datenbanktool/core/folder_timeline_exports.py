from __future__ import annotations

import csv
import html
import io
import json
import os
from dataclasses import dataclass
from pathlib import Path

from datenbanktool.core.folder_timeline import FolderTimeline
from datenbanktool.core.folder_timeline_charts import render_timeline_charts


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


def _percent(value: float | None) -> str:
    return "–" if value is None else f"{value:+.2f} %"


def _threshold_summary(timeline: FolderTimeline) -> str:
    thresholds: list[str] = []
    if timeline.warn_size_growth_percent is not None:
        thresholds.append(
            f"Größenwachstum ab {timeline.warn_size_growth_percent:.2f} %"
        )
    if timeline.warn_file_growth_percent is not None:
        thresholds.append(
            f"Dateizahlwachstum ab {timeline.warn_file_growth_percent:.2f} %"
        )
    if not thresholds:
        return (
            "Trendgrenzen sind nicht aktiviert. Die Ampeln beschreiben nur den "
            "gespeicherten Verlauf."
        )
    return (
        "Aktive rein lesende Trendgrenzen: "
        + "; ".join(thresholds)
        + f". Erreicht in {timeline.threshold_trigger_count} Übergängen. "
        "Eine Warnung ist keine Schadens- oder Löschentscheidung."
    )


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
                "Verlaufsstatus",
                "Warnstatus",
                "Warnbegründung",
                "Trendgrenze erreicht",
                "Dateien",
                "Dateidifferenz",
                "Dateidifferenz Prozent",
                "Größe Byte",
                "Größendifferenz Byte",
                "Größendifferenz Prozent",
                "Warnschwelle Dateizahl Prozent",
                "Warnschwelle Größe Prozent",
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
                    point.traffic_label,
                    point.traffic_reason,
                    "ja" if point.threshold_triggered else "nein",
                    point.file_count,
                    "" if point.file_delta is None else point.file_delta,
                    "" if point.file_delta_percent is None else point.file_delta_percent,
                    point.size_bytes,
                    "" if point.size_delta_bytes is None else point.size_delta_bytes,
                    "" if point.size_delta_percent is None else point.size_delta_percent,
                    (
                        ""
                        if timeline.warn_file_growth_percent is None
                        else timeline.warn_file_growth_percent
                    ),
                    (
                        ""
                        if timeline.warn_size_growth_percent is None
                        else timeline.warn_size_growth_percent
                    ),
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
            tooltip = html.escape(point.traffic_reason, quote=True)
            rows.append(
                "<tr>"
                f"<td>#{point.session_id}</td>"
                f"<td>{html.escape(point.recorded_utc)}</td>"
                f"<td>{html.escape(point.scan_mode)}</td>"
                f"<td>{html.escape(point.status_label)}</td>"
                f"<td><span class=\"light {point.traffic_level}\" "
                f"title=\"{tooltip}\" aria-label=\"{html.escape(point.traffic_label)}: "
                f"{tooltip}\">● {html.escape(point.traffic_label)}</span>"
                f"<small>{tooltip}</small></td>"
                f"<td>{point.file_count}</td>"
                f"<td>{'–' if point.file_delta is None else f'{point.file_delta:+d}'}</td>"
                f"<td>{_percent(point.file_delta_percent)}</td>"
                f"<td>{_human_size(point.size_bytes)}</td>"
                f"<td>{_signed_size(point.size_delta_bytes)}</td>"
                f"<td>{_percent(point.size_delta_percent)}</td>"
                "</tr>"
            )
        truncation = (
            f"Es werden die neuesten {len(timeline.points)} von "
            f"{timeline.total_available_sessions} passenden Scans gezeigt."
            if timeline.truncated
            else f"Alle {len(timeline.points)} passenden Scans werden gezeigt."
        )
        charts = render_timeline_charts(timeline)
        threshold_summary = _threshold_summary(timeline)
        document = f"""<!doctype html>
<html lang=\"de\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>DATENBANKTOOL – Ordner-Zeitreihe</title>
<style>
:root{{color-scheme:light}}*{{box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;margin:0;background:#f6f7f9;color:#15171a;line-height:1.5}}
main{{max-width:1180px;margin:auto;padding:1.5rem}}
.hint,.threshold-summary{{padding:.8rem;border-radius:.35rem}}
.hint{{background:#e8f4ff;border-left:.35rem solid #176b87}}
.threshold-summary{{background:#fff8df;border-left:.35rem solid #8a6500;margin-top:1rem}}
.charts{{margin-top:2rem}}.chart-panel{{background:white;border:1px solid #c8ccd0;border-radius:.6rem;padding:1rem;margin:1rem 0}}
.chart-panel figcaption{{font-size:1.25rem;font-weight:750}}.chart-summary{{margin:.35rem 0 1rem}}
.timeline-chart{{display:block;width:100%;height:auto;min-height:18rem;color:#164f68;background:#fff;border:1px solid #d9dde1;border-radius:.35rem}}
.grid{{stroke:#d7dce0;stroke-width:1}}.axis{{stroke:#30363b;stroke-width:2}}
.data-line{{fill:none;stroke:currentColor;stroke-width:3;stroke-linejoin:round;stroke-linecap:round}}
.data-point{{fill:white;stroke:currentColor;stroke-width:3}}.data-point:focus{{outline:none;stroke-width:6}}
.warning-point{{fill:#fff1f1;stroke:#941919;stroke-width:5}}
.warning-label{{font-size:11px;font-weight:800;fill:#941919}}
.axis-label{{font-size:13px;fill:#343a40}}.axis-title{{font-size:15px;font-weight:700;fill:#202428}}
.value-label{{font-size:12px;font-weight:700;fill:#202428;paint-order:stroke;stroke:white;stroke-width:4px;stroke-linejoin:round}}
.table-wrap{{overflow-x:auto;margin-top:1.5rem}}table{{width:100%;border-collapse:collapse;background:white;min-width:980px}}
caption{{text-align:left;font-size:1.25rem;font-weight:750;padding:.5rem 0}}
th,td{{padding:.6rem;border:1px solid #c8ccd0;text-align:left;vertical-align:top}}
th{{background:#e9ecef;position:sticky;top:0}}.light{{font-weight:700}}td small{{display:block;margin-top:.25rem}}
.green{{color:#176b2c}}.yellow{{color:#6b4c00}}.red{{color:#941919}}
@media (max-width:640px){{main{{padding:.8rem}}.chart-panel{{padding:.55rem}}.timeline-chart{{min-height:14rem}}}}
@media (prefers-reduced-motion:reduce){{*{{scroll-behavior:auto!important}}}}
</style></head><body><main>
<h1>Ordner-Zeitreihe</h1>
<p>Stammordner: {html.escape(timeline.root)}<br>Ordner: {html.escape(timeline.folder)}<br>
Scans: #{timeline.first_session_id} bis #{timeline.last_session_id}</p>
<p class=\"hint\">Reine Auswertung gespeicherter Scans. {html.escape(truncation)}
Elternordner enthalten ihre Unterordner. Farben werden immer durch Klartext ergänzt.
Die Trendgrafiken benötigen weder Internet noch JavaScript.</p>
<p class=\"threshold-summary\"><strong>Trendgrenzen:</strong> {html.escape(threshold_summary)}</p>
{charts}
<div class=\"table-wrap\"><table><caption>Vollständige Zeitreihenwerte</caption><thead><tr>
<th scope=\"col\">Scan</th><th scope=\"col\">Zeitpunkt UTC</th><th scope=\"col\">Modus</th>
<th scope=\"col\">Verlauf</th><th scope=\"col\">Warnstatus und Begründung</th>
<th scope=\"col\">Dateien</th><th scope=\"col\">Δ Dateien</th><th scope=\"col\">Δ Dateien %</th>
<th scope=\"col\">Größe</th><th scope=\"col\">Δ Größe</th><th scope=\"col\">Δ Größe %</th>
</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
</main></body></html>
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
