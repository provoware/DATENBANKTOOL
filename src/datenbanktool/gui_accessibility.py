from __future__ import annotations

from dataclasses import dataclass

from datenbanktool.gui_model import NEON_ARCHIVE_THEME


@dataclass(frozen=True)
class AccessibilityProfile:
    scale_percent: int = 100
    minimum_target_px: int = 32
    keyboard_navigation: bool = True
    reduced_motion: bool = True

    def scaled(self, percent: int) -> "AccessibilityProfile":
        if percent < 80 or percent > 200:
            raise ValueError("Skalierung muss zwischen 80 und 200 Prozent liegen")
        return AccessibilityProfile(
            scale_percent=percent,
            minimum_target_px=self.minimum_target_px,
            keyboard_navigation=self.keyboard_navigation,
            reduced_motion=self.reduced_motion,
        )


KEYBOARD_ACTIONS = (
    ("Ctrl+F", "Suche fokussieren"),
    ("Ctrl+L", "Dateiliste fokussieren"),
    ("Ctrl+P", "Schnellmodi öffnen"),
    ("Ctrl+T", "Testlabor öffnen"),
    ("Ctrl+Z", "Undo-Status anzeigen"),
    ("F1", "Kontexthilfe öffnen"),
    ("Escape", "Dialog oder Vorschau schließen"),
)


def _rgb(value: str) -> tuple[float, float, float]:
    if len(value) != 7 or not value.startswith("#"):
        raise ValueError(f"Ungültige Farbe: {value}")
    return tuple(int(value[index:index + 2], 16) / 255.0 for index in (1, 3, 5))  # type: ignore[return-value]


def _linear(channel: float) -> float:
    if channel <= 0.03928:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    red, green, blue = _rgb(color)
    return 0.2126 * _linear(red) + 0.7152 * _linear(green) + 0.0722 * _linear(blue)


def contrast_ratio(foreground: str, background: str) -> float:
    first = relative_luminance(foreground)
    second = relative_luminance(background)
    lighter = max(first, second)
    darker = min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def default_contrast_checks() -> dict[str, float]:
    theme = NEON_ARCHIVE_THEME
    return {
        "text/background": contrast_ratio(theme.text, theme.background),
        "text/panel": contrast_ratio(theme.text, theme.panel),
        "accent/background": contrast_ratio(theme.accent, theme.background),
        "success/background": contrast_ratio(theme.success, theme.background),
    }


def accessibility_gate_passed() -> bool:
    checks = default_contrast_checks()
    return (
        checks["text/background"] >= 7.0
        and checks["text/panel"] >= 7.0
        and checks["accent/background"] >= 4.5
        and checks["success/background"] >= 4.5
        and len(KEYBOARD_ACTIONS) >= 6
    )
