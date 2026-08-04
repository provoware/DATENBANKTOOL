from __future__ import annotations


class InputParseError(ValueError):
    """Raised when a guided home input value cannot be parsed."""


def parse_optional_integer(
    value: str,
    *,
    minimum: int,
    maximum: int | None = None,
    default: int | None = None,
) -> int | None:
    if not value:
        return default
    try:
        number = int(value)
    except ValueError as error:
        raise InputParseError("Bitte eine ganze Zahl eingeben.") from error
    if number < minimum or (maximum is not None and number > maximum):
        range_text = (
            f"zwischen {minimum} und {maximum}"
            if maximum is not None
            else f"ab {minimum}"
        )
        raise InputParseError(f"Bitte eine Zahl {range_text} eingeben.")
    return number


def parse_optional_percent(
    value: str,
    *,
    minimum: float,
    maximum: float,
) -> float | None:
    if not value:
        return None
    try:
        number = float(value.replace(",", "."))
    except ValueError as error:
        raise InputParseError("Bitte eine Zahl eingeben.") from error
    if number != number or number in {float("inf"), float("-inf")}:
        raise InputParseError("Bitte eine endliche Zahl eingeben.")
    if not minimum <= number <= maximum:
        raise InputParseError(
            f"Bitte eine Zahl zwischen {minimum:g} und {maximum:g} eingeben."
        )
    return number


def parse_report_format(value: str) -> str:
    aliases = {
        "": "none",
        "kein": "none",
        "keiner": "none",
        "ohne": "none",
        "none": "none",
        "json": "json",
        "csv": "csv",
        "html": "html",
    }
    try:
        return aliases[value.casefold()]
    except KeyError as error:
        raise InputParseError("Bitte kein, json, csv oder html eingeben.") from error
