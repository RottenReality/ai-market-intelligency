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
