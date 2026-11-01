"""Prompts for the AI analysis. The model only sees rounded scores, formatted values and
years (never URLs or timestamps), so every number it may use is listed in the DATA block."""

import json

from app.profile.company import CompanyProfile
from app.scoring.display import format_raw
from app.scoring.scorecard import DIMENSION_NAMES, Scorecard

RULES = """Rules:
- Use digits only for numbers that appear in DATA. Write timeframes and quantities in words
  (for example "a short pilot", "within the first months"), never as digits.
- Do not add facts, figures or percentages from memory.
- Cite the indicators behind each statement with their IDs in brackets, e.g. [A1].
- Indicators with "score": null have no data: say so instead of guessing.
- Answer with a single JSON object and nothing else."""

COUNTRY_INSTRUCTIONS = """You are a market-entry analyst writing for business readers. Using the
CAGE distance framework (Cultural, Administrative, Geographic, Economic), explain how accessible
{country} is for the company described below, which sells its services remotely from {home}.

Return JSON with exactly these keys:
- "executive_summary": 60-100 words. Overall market accessibility, the decisive strengths and
  barriers, and what it means for the company.
- "dimensions": an object with keys "Cultural", "Administrative", "Geographic", "Economic";
  40-80 words each explaining why that dimension scored as it did.
- "barriers": 2-3 short items, the main obstacles to entering.
- "opportunities": 2-3 short items, the main advantages to build on.
- "recommendation": 50-100 words with a recommendation and concrete next steps."""


def _rounded(score: float | None) -> int | None:
    return None if score is None else int(score + 0.5)


def country_data(scorecard: Scorecard) -> dict:
    return {
        "country": scorecard.country.name,
        "home_country": scorecard.home,
        "market_accessibility": _rounded(scorecard.accessibility),
        "not_calculated_because": scorecard.accessibility_reason,
        "dimensions": {
            d.name: {"score": _rounded(d.score), "indicators_with_data": f"{d.available}/{d.total}"}
            for d in scorecard.dimensions
        },
        "indicators": [
            {
                "id": i.id,
                "name": i.name,
                "dimension": DIMENSION_NAMES[i.dimension],
                "score": _rounded(i.score),
                "value": "no data" if i.score is None else format_raw(i.raw, i.unit),
                "year": max((s.year for s in i.sources if s.year), default=None),
            }
            for i in scorecard.indicators
        ],
    }


def country_data_block(scorecard: Scorecard) -> str:
    return json.dumps(country_data(scorecard), indent=1, ensure_ascii=False)


def country_prompt(scorecard: Scorecard, profile: CompanyProfile) -> str:
    instructions = COUNTRY_INSTRUCTIONS.format(
        country=scorecard.country.name, home=scorecard.home
    )
    return (
        f"{instructions}\n\n{RULES}\n\nCOMPANY:\n{profile.description_md}\n\n"
        f"DATA:\n{country_data_block(scorecard)}\n"
    )
