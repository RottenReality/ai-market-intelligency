"""Numbers guard: every number in an AI explanation must come from the scorecard data."""

import re

# A number not glued to a letter or another number (so "A3" or "G1" are not numbers),
# with optional thousands separators, decimals and a trailing percent sign.
_NUMBER = re.compile(r"(?<![A-Za-z\d.,])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?")


def _value(token: str) -> float:
    return float(token.rstrip("%").replace(",", ""))


def numbers_in(text: str) -> set[float]:
    return {_value(match.group(0)) for match in _NUMBER.finditer(text)}


def find_unsupported_numbers(text: str, allowed: set[float], tolerance: float = 0.5) -> list[str]:
    return [
        match.group(0)
        for match in _NUMBER.finditer(text)
        if not any(abs(_value(match.group(0)) - number) <= tolerance for number in allowed)
    ]


# Wording guard: a share of people who use something (C2: WhatsApp) is not a preference.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_PREFERENCE = re.compile(
    r"\b(?:prefer|prefers|preferred|preference|preferences|favou?r|favou?rs|favou?red)\b", re.IGNORECASE
)
_USAGE_TOPIC = re.compile(r"whatsapp", re.IGNORECASE)


def find_overstatements(text: str) -> list[str]:
    """Sentences that turn the share of WhatsApp users into a preference."""
    return [
        sentence.strip()
        for sentence in _SENTENCE_END.split(text)
        if _USAGE_TOPIC.search(sentence) and _PREFERENCE.search(sentence)
    ]
