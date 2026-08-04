from __future__ import annotations

import html

from datenbanktool.core.folder_timeline import FolderTimeline

_WIDTH = 960
_HEIGHT = 360
_LEFT = 88
_RIGHT = 28
_TOP = 42
_BOTTOM = 72
_PLOT_WIDTH = _WIDTH - _LEFT - _RIGHT
_PLOT_HEIGHT = _HEIGHT - _TOP - _BOTTOM


def _human_size(size_bytes: int) -> str:
    value = float(abs(size_bytes))
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{int(value)} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{abs(size_bytes)} B"


def _bounds(values: list[int]) -> tuple[float, float]:
    low = float(min(values))
    high = float(max(values))
    if low == high:
        padding = max(1.0, abs(high) * 0.1)
        low = max(0.0, low - padding)
        high += padding
    return low, high


def _label_indexes(count: int) -> set[int]:
    if count <= 12:
        return set(range(count))
    return {round(step * (count - 1) / 5) for step in range(6)}


def _metric_value(metric: str, value: int) -> str:
    return _human_size(value) if metric == "size" else str(value)


def _chart(
    timeline: FolderTimeline,
    *,
    metric: str,
    heading: str,
    description: str,
) -> str:
    values = [
        point.size_bytes if metric == "size" else point.file_count
        for point in timeline.points
    ]
    low, high = _bounds(values)
    count = len(values)
    x_step = _PLOT_WIDTH / max(1, count - 1)

    def x_position(index: int) -> float:
        return _LEFT + index * x_step

    def y_position(value: int | float) -> float:
        ratio = (float(value) - low) / (high - low)
        return _TOP + _PLOT_HEIGHT - ratio * _PLOT_HEIGHT

    tick_lines: list[str] = []
    for index in range(5):
        value = low + (high - low) * index / 4
        y = y_position(value)
        label = _metric_value(metric, round(value))
        tick_lines.append(
            f'<line class="grid" x1="{_LEFT}" y1="{y:.2f}" '
            f'x2="{_LEFT + _PLOT_WIDTH}" y2="{y:.2f}" />'
            f'<text class="axis-label" x="{_LEFT - 10}" y="{y + 4:.2f}" '
            f'text-anchor="end">{html.escape(label)}</text>'
        )

    labels = _label_indexes(count)
    x_labels: list[str] = []
    points: list[str] = []
    coordinates: list[str] = []
    for index, point in enumerate(timeline.points):
        value = values[index]
        x = x_position(index)
        y = y_position(value)
        coordinates.append(f"{x:.2f},{y:.2f}")
        value_text = _metric_value(metric, value)
        accessible = html.escape(
            f"Scan #{point.session_id}, {point.recorded_utc}: {value_text}",
            quote=True,
        )
        points.append(
            f'<circle class="data-point" cx="{x:.2f}" cy="{y:.2f}" r="5" '
            f'tabindex="0" role="img" aria-label="{accessible}">'
            f'<title>{accessible}</title></circle>'
        )
        if index in labels:
            x_labels.append(
                f'<text class="axis-label" x="{x:.2f}" y="{_HEIGHT - 38}" '
                f'text-anchor="middle">#{point.session_id}</text>'
            )
            value_y = max(_TOP + 14, y - 11)
            points.append(
                f'<text class="value-label" x="{x:.2f}" y="{value_y:.2f}" '
                f'text-anchor="middle">{html.escape(value_text)}</text>'
            )

    identifier = "size-chart" if metric == "size" else "files-chart"
    minimum = _metric_value(metric, min(values))
    maximum = _metric_value(metric, max(values))
    net_value = values[-1] - values[0]
    net = _metric_value(metric, abs(net_value))
    net_text = "unverändert" if net_value == 0 else (
        f"um {net} gestiegen" if net_value > 0 else f"um {net} gesunken"
    )
    summary = (
        f"{description} Minimum {minimum}, Maximum {maximum}; vom ersten bis zum "
        f"letzten angezeigten Scan {net_text}. Die vollständigen Werte stehen in "
        "der Tabelle unter den Diagrammen."
    )
    return f"""
<figure class="chart-panel">
<figcaption>{html.escape(heading)}</figcaption>
<p class="chart-summary">{html.escape(summary)}</p>
<svg class="timeline-chart" viewBox="0 0 {_WIDTH} {_HEIGHT}" role="img"
 aria-labelledby="{identifier}-title {identifier}-description">
<title id="{identifier}-title">{html.escape(heading)}</title>
<desc id="{identifier}-description">{html.escape(summary)}</desc>
<line class="axis" x1="{_LEFT}" y1="{_TOP}" x2="{_LEFT}" y2="{_TOP + _PLOT_HEIGHT}" />
<line class="axis" x1="{_LEFT}" y1="{_TOP + _PLOT_HEIGHT}" x2="{_LEFT + _PLOT_WIDTH}" y2="{_TOP + _PLOT_HEIGHT}" />
{''.join(tick_lines)}
<polyline class="data-line" points="{' '.join(coordinates)}" />
{''.join(points)}
{''.join(x_labels)}
<text class="axis-title" x="{_LEFT + _PLOT_WIDTH / 2:.2f}" y="{_HEIGHT - 10}" text-anchor="middle">Scan-ID</text>
</svg>
</figure>
"""


def render_timeline_charts(timeline: FolderTimeline) -> str:
    """Return two script-free, accessible, fully local SVG charts."""
    return (
        '<section class="charts" aria-labelledby="trend-heading">'
        '<h2 id="trend-heading">Trendgrafiken</h2>'
        '<p>Beide Diagramme sind textlich beschriftet. Jeder Datenpunkt besitzt eine '
        'Tastaturmarke und eine genaue zugängliche Beschreibung.</p>'
        + _chart(
            timeline,
            metric="size",
            heading="Größenverlauf",
            description="Entwicklung des rekursiven Speicherbedarfs.",
        )
        + _chart(
            timeline,
            metric="files",
            heading="Dateizahlverlauf",
            description="Entwicklung der rekursiven Dateizahl.",
        )
        + "</section>"
    )
