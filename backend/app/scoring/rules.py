"""CAGE scoring rules: pure functions, one per indicator, every result clamped to 0-100.

A missing input always gives ``None`` ("missing"), never 0. The constants below are the
thresholds cited in the methodology (spec section 3.1).
"""

MIN_URBAN_POPULATION = 10_000_000  # E2: urban population needed to count as a large market
INFLATION_PENALTY_PER_POINT = 5  # E3: 0% -> 100, 20% -> 0
WGI_RANGE = (-2.5, 2.5)  # A3: World Bank governance estimate range


def clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def regulatory_quality(estimate: float | None) -> float | None:
    if estimate is None:
        return None
    low, high = WGI_RANGE
    return clamp((estimate - low) / (high - low) * 100)


def percentage(value: float | None) -> float | None:
    return None if value is None else clamp(value)


def income_vs_home(country: float | None, home: float | None) -> float | None:
    if country is None or not home:
        return None
    return clamp(country / home * 100)


def market_size(urban_population: float | None) -> float | None:
    if urban_population is None:
        return None
    return 100.0 if urban_population >= MIN_URBAN_POPULATION else 0.0


def inflation(annual_pct: float | None) -> float | None:
    if annual_pct is None:
        return None
    return clamp(100 - INFLATION_PENALTY_PER_POINT * annual_pct)


ENGLISH_BAND_SCORES = {"very_high": 100, "high": 75, "moderate": 50, "low": 25, "very_low": 0}
KS_SCORE_FACTOR = 25  # C3: Kogut-Singh 0 -> 100, 4 or more -> 0
WORKDAY_HOURS = 8  # G1: length of the working day used for the overlap


def language_barrier(
    country_languages: list[str], supported_languages: list[str], english_band: str | None
) -> float | None:
    """C1: 100 if the company works in a local language; otherwise the English level."""
    if set(country_languages) & set(supported_languages):
        return 100.0
    if english_band is None:
        return None
    return float(ENGLISH_BAND_SCORES[english_band])


def channel_fit(whatsapp_pct: float | None, channels: list[str]) -> float | None:
    """C2: how much SMS/email still matter where WhatsApp dominates messaging."""
    if "whatsapp" in channels:
        return 100.0
    return None if whatsapp_pct is None else clamp(100 - whatsapp_pct)


def cultural_distance(kogut_singh: float | None) -> float | None:
    return None if kogut_singh is None else clamp(100 - KS_SCORE_FACTOR * kogut_singh)


def yes_no(value: bool | None) -> float | None:
    return None if value is None else (100.0 if value else 0.0)


def hours_overlap(max_diff_hours: float | None) -> float | None:
    if max_diff_hours is None:
        return None
    return clamp((WORKDAY_HOURS - max_diff_hours) / WORKDAY_HOURS * 100)
