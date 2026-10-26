"""Human-readable formatting of raw values and scores (mirrors frontend/src/lib/format.ts)."""

from app.evidence.models import EvidenceValue

MISSING = "n/a"


def format_raw(value: EvidenceValue | None, unit: str) -> str:
    if value is None:
        return MISSING
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, str):
        text = value.replace("_", " ")
        return text[:1].upper() + text[1:]
    if unit == "%":
        return f"{value:.1f}%"
    if unit == "USD":
        return f"${value:,.0f}"
    if unit == "people":
        return f"{value / 1_000_000:.1f}M" if value >= 1_000_000 else f"{value:,.0f}"
    if unit == "index":
        return f"{value:.2f}"
    if unit == "hours":
        return f"{value:g} h"
    return f"{round(value, 2):g}"


def format_score(score: float | None) -> str:
    # Round half up like JavaScript's Math.round (Python's round() rounds half to even).
    return MISSING if score is None else str(int(score + 0.5) if score >= 0 else round(score))
