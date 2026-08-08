from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class ProgressSnapshot:
    phase: str
    current: int
    total: int | None
    elapsed_seconds: float
    rate_per_second: float | None
    message: str

    @property
    def percent(self) -> float | None:
        if self.total is None or self.total <= 0:
            return None
        return max(0.0, min(100.0, (self.current / self.total) * 100.0))

    @property
    def remaining_seconds(self) -> float | None:
        if self.total is None or self.rate_per_second is None or self.rate_per_second <= 0:
            return None
        remaining = max(0, self.total - self.current)
        return remaining / self.rate_per_second


@dataclass(frozen=True)
class TransparencyReport:
    title: str
    mode: str
    source: str
    planned_actions: int
    protected_items: int
    warnings: int
    errors: int
    reversible: bool
    notes: tuple[str, ...]


def human_duration(seconds: float | None) -> str:
    if seconds is None:
        return "noch nicht berechenbar"
    if seconds < 0:
        raise ValueError("Dauer darf nicht negativ sein")
    rounded = int(round(seconds))
    duration = timedelta(seconds=rounded)
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if days:
        return f"{days} T {hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def build_transparency_report(
    *,
    source: str,
    planned_actions: int,
    protected_items: int,
    warnings: int,
    errors: int,
) -> TransparencyReport:
    if min(planned_actions, protected_items, warnings, errors) < 0:
        raise ValueError("Berichtszähler dürfen nicht negativ sein")
    notes = (
        "Originaldaten werden durch die GUI-Planung nicht automatisch verändert.",
        "Änderungen benötigen eine getrennte, ausdrückliche Freigabe.",
        "Geschützte oder fehlerhafte Elemente werden sichtbar ausgewiesen.",
        "Jeder ausgeführte Fachschritt muss separat protokollierbar bleiben.",
    )
    return TransparencyReport(
        title="Sicherheits- und Wirkungsbericht",
        mode="Vorschau / Testlauf",
        source=source,
        planned_actions=planned_actions,
        protected_items=protected_items,
        warnings=warnings,
        errors=errors,
        reversible=True,
        notes=notes,
    )
