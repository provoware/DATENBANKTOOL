from __future__ import annotations

import unicodedata

_PORTABILITY_RISK_CHARS = frozenset('<>:"\\|?*')


def filename_warnings(name: str) -> list[str]:
    """Return non-destructive filename diagnostics."""
    warnings: list[str] = []
    if not name:
        return ["empty-name"]
    if name in {".", ".."}:
        warnings.append("reserved-path-segment")
    if name != name.strip():
        warnings.append("leading-or-trailing-whitespace")
    if name.startswith("-"):
        warnings.append("leading-dash-shell-risk")
    if any(ord(character) < 32 or ord(character) == 127 for character in name):
        warnings.append("control-character")
    if any(character in _PORTABILITY_RISK_CHARS for character in name):
        warnings.append("cross-platform-risk-character")
    if "\n" in name or "\r" in name:
        warnings.append("line-break")
    if "  " in name:
        warnings.append("repeated-space")
    if unicodedata.normalize("NFC", name) != name:
        warnings.append("unicode-not-nfc")
    if len(name.encode("utf-8")) > 255:
        warnings.append("name-over-255-bytes")
    return warnings
