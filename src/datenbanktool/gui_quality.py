from __future__ import annotations

from dataclasses import dataclass

from datenbanktool.gui_model import NEON_ARCHIVE_THEME, gui_contract
from datenbanktool.gui_presets import validate_presets


@dataclass(frozen=True)
class QualityFinding:
    code: str
    passed: bool
    detail: str


def _hex_color(value: str) -> bool:
    return len(value) == 7 and value.startswith("#") and all(
        char in "0123456789abcdefABCDEF" for char in value[1:]
    )


def run_gui_quality_gate() -> tuple[QualityFinding, ...]:
    contract = gui_contract()
    theme = NEON_ARCHIVE_THEME
    findings: list[QualityFinding] = []

    required_layout = {
        "left_navigation",
        "project_header",
        "summary_and_workload",
        "detail_list_workspace",
        "assistant_sidebar",
        "persistent_status_strip",
    }
    actual_layout = set(contract["layout"])
    findings.append(QualityFinding(
        "layout-required-zones",
        required_layout <= actual_layout,
        "Alle verbindlichen Layoutzonen müssen vorhanden sein.",
    ))

    colors = (
        theme.background, theme.panel, theme.panel_alt, theme.border,
        theme.text, theme.muted, theme.accent, theme.accent_soft,
        theme.success, theme.warning, theme.danger,
    )
    findings.append(QualityFinding(
        "theme-valid-colors",
        all(_hex_color(value) for value in colors),
        "Design-Tokens müssen explizite hexadezimale Farben sein.",
    ))
    findings.append(QualityFinding(
        "theme-distinct-action-colors",
        len({theme.success, theme.warning, theme.danger}) == 3,
        "Erfolg, Warnung und Fehler brauchen unterscheidbare Signalfarben.",
    ))

    safety = tuple(str(item).casefold() for item in contract["safety_states"])
    for token in ("nur les", "testlauf", "papierkorb", "rollback", "protokoll"):
        findings.append(QualityFinding(
            f"safety-{token.replace(' ', '-')}",
            any(token in item for item in safety),
            f"Sicherheitszustand '{token}' muss im sichtbaren Vertrag vorkommen.",
        ))

    preset_problems = validate_presets()
    findings.append(QualityFinding(
        "presets-safe",
        not preset_problems,
        "Kein Standard-Preset darf destruktiv oder unvollständig sein."
        if not preset_problems else "; ".join(preset_problems),
    ))

    findings.append(QualityFinding(
        "minimum-workspace-tabs",
        len(tuple(contract["tabs"])) >= 6,
        "Der Detailworkspace benötigt ausreichend klar getrennte Arbeitsansichten.",
    ))
    findings.append(QualityFinding(
        "assistant-next-steps",
        len(tuple(contract["next_steps"])) >= 3,
        "Die Führung muss jederzeit mehrere nachvollziehbare nächste Schritte anbieten.",
    ))
    return tuple(findings)


def quality_gate_passed() -> bool:
    return all(finding.passed for finding in run_gui_quality_gate())
