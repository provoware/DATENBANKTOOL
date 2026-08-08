from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeTokens:
    background: str
    panel: str
    panel_alt: str
    border: str
    text: str
    muted: str
    accent: str
    accent_soft: str
    success: str
    warning: str
    danger: str


NEON_ARCHIVE_THEME = ThemeTokens(
    background="#050b0e",
    panel="#071419",
    panel_alt="#0a1b20",
    border="#0b7f6a",
    text="#e8fff8",
    muted="#8db8ad",
    accent="#00f0b5",
    accent_soft="#0bb98e",
    success="#19d66b",
    warning="#ffb000",
    danger="#ff4d4d",
)

NAVIGATION = (
    "Analyse & Inventur",
    "Schnellmodi & Presets",
    "Duplikate & Umbenennen",
    "Listen & Ergebnisse",
    "Testsystem & Prüfläufe",
    "Transparenz & Monitor",
    "Einstellungen",
    "Protokolle",
)

WORKSPACE_TABS = (
    "Duplikate",
    "Umbenennen",
    "Groß & Alt",
    "Leere Dateien",
    "Unbekannte",
    "Ausnahmen",
)

SUMMARY_CARDS = (
    ("Exakte Duplikate", "3.421", "12,67 TB"),
    ("Ähnliche Dateien", "12.842", "4,12 TB"),
    ("Leere Dateien", "218", "2,12 GB"),
    ("Große Dateien", "1.245", "7,45 TB"),
    ("Vorschau & Auswahl", "2.863", "ausgewählt"),
)

SAFETY_STATES = (
    "Nur lesender Zugriff aktiv",
    "Testlauf zuerst empfohlen",
    "Papierkorb aktiv",
    "Undo & Rollback verfügbar",
    "Protokollierung 100%",
)

NEXT_STEPS = (
    "Vorschau aktualisieren",
    "Auswahl prüfen",
    "Testlauf starten",
    "Ergebnisse prüfen",
    "Sichere Simulation starten",
)


def gui_contract() -> dict[str, object]:
    """Return the stable visual/interaction contract without importing a GUI toolkit."""
    return {
        "theme": NEON_ARCHIVE_THEME,
        "navigation": NAVIGATION,
        "tabs": WORKSPACE_TABS,
        "summary_cards": SUMMARY_CARDS,
        "safety_states": SAFETY_STATES,
        "next_steps": NEXT_STEPS,
        "layout": (
            "left_navigation",
            "project_header",
            "summary_and_workload",
            "detail_list_workspace",
            "assistant_sidebar",
            "persistent_status_strip",
        ),
    }
