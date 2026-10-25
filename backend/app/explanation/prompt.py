"""Build the LLM prompt. The model only sees rounded scores, formatted values and years,
never URLs or timestamps, so every number it may use is listed in the DATA block."""

import json

from app.profile.company import CompanyProfile
from app.scoring.display import format_raw
from app.scoring.scorecard import DIMENSION_NAMES, Scorecard

INSTRUCTIONS = """You are a market-entry analyst. Using the CAGE distance framework, explain how
accessible {country} is for the company described below, which sells its services remotely
from {home}.

Write 120-180 words of plain English for business readers:
- Start with the overall market accessibility (or say why it could not be calculated).
- Name the weakest and the strongest CAGE dimension and explain why, citing indicator IDs
  in brackets, e.g. [A1].
- Mention any dimension with missing indicators.
- End with one concrete next step for the company.

Use only numbers that appear in DATA. Do not add facts, figures or percentages from memory.
Indicators with "score": null have no data: say so instead of guessing."""


def _rounded(score: float | None) -> int | None:
    return None if score is None else int(score + 0.5)


def data_block(scorecard: Scorecard) -> str:
    data = {
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
    return json.dumps(data, indent=1, ensure_ascii=False)


def build_prompt(scorecard: Scorecard, profile: CompanyProfile) -> str:
    instructions = INSTRUCTIONS.format(country=scorecard.country.name, home=scorecard.home)
    return (
        f"{instructions}\n\nCOMPANY:\n{profile.description_md}\n\n"
        f"DATA:\n{data_block(scorecard)}\n"
    )
