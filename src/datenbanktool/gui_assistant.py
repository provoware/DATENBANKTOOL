from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Severity = Literal["info", "success", "warning", "error"]


@dataclass(frozen=True)
class AssistantMessage:
    title: str
    body: str
    severity: Severity
    next_action: str | None = None


@dataclass(frozen=True)
class AuditEntry:
    sequence: int
    action: str
    reason: str
    effect: str
    reversible: bool


class AssistantTimeline:
    """Deterministic explanatory layer for GUI feedback and audit previews."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def explain_scan(self, *, files: int, warnings: int, errors: int) -> AssistantMessage:
        if errors:
            return AssistantMessage(
                "Scan mit Problemen abgeschlossen",
                f"{files:,} Dateien wurden erfasst. {errors} Lesefehler wurden protokolliert; "
                "betroffene Elemente bleiben unangetastet.",
                "warning",
                "Fehlerliste prüfen",
            )
        if warnings:
            return AssistantMessage(
                "Analyse abgeschlossen",
                f"{files:,} Dateien wurden sicher gelesen. {warnings} Hinweise brauchen eventuell "
                "deine Aufmerksamkeit, bevor ein Workflow vorgeschlagen wird.",
                "info",
                "Hinweise prüfen",
            )
        return AssistantMessage(
            "Analyse abgeschlossen",
            f"{files:,} Dateien wurden ohne gemeldete Fehler rein lesend ausgewertet.",
            "success",
            "Workflow auswählen",
        )

    def explain_action(self, *, action: str, reason: str, effect: str, reversible: bool) -> AuditEntry:
        entry = AuditEntry(
            sequence=len(self._entries) + 1,
            action=action,
            reason=reason,
            effect=effect,
            reversible=reversible,
        )
        self._entries.append(entry)
        return entry

    def entries(self) -> tuple[AuditEntry, ...]:
        return tuple(self._entries)

    def next_steps(self, *, has_index: bool, has_selection: bool, test_passed: bool) -> tuple[str, ...]:
        if not has_index:
            return ("Index rein lesend auswählen", "Bestand analysieren", "Ergebnis prüfen")
        if not has_selection:
            return ("Preset oder Filter wählen", "Vorschau erzeugen", "Auswahl prüfen")
        if not test_passed:
            return ("Testlauf starten", "Warnungen prüfen", "Vorschlag anpassen")
        return ("Testbericht prüfen", "Freigabe bewusst erteilen", "Ausführung überwachen")
