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


COMPARISON_INSTRUCTIONS = """You are a market-entry analyst writing for business readers. Using the
CAGE distance framework, compare how accessible these countries are for the company described
below, which sells its services remotely from {home}. The ranking is already calculated in DATA:
explain it, do not change it.

Return JSON with exactly these keys:
- "summary": 80-130 words on what separates the countries and what it means for the company.
- "ranking": one entry per country, {{"iso3": "<code>", "explanation": "<one or two sentences
  on why it ranks where it does>"}}.
- "key_differences": 2-4 short items naming the differences that matter most."""


def _ranked(values: dict[str, int | None]) -> dict[str, tuple[int, int | None]]:
    """(rank, points behind the leader) per key; missing values rank last with no gap."""
    order = sorted(values, key=lambda k: (values[k] is None, -(values[k] or 0)))
    leader = values[order[0]] if order else None
    return {
        key: (position, None if values[key] is None or leader is None else leader - values[key])
        for position, key in enumerate(order, start=1)
    }


def comparison_data(scorecards: list[Scorecard]) -> dict:
    overall = _ranked({c.country.iso3: _rounded(c.accessibility) for c in scorecards})
    dimension_ranks = {
        name: _ranked({
            c.country.iso3: _rounded(next(d.score for d in c.dimensions if d.name == name))
            for c in scorecards
        })
        for name in DIMENSION_NAMES.values()
    }
    countries = []
    for card in sorted(scorecards, key=lambda c: overall[c.country.iso3][0]):
        code = card.country.iso3
        rank, gap = overall[code]
        countries.append({
            "iso3": code,
            "name": card.country.name,
            "market_accessibility": _rounded(card.accessibility),
            "rank": rank,
            "points_behind_leader": gap,
            "dimensions": {
                d.name: {
                    "score": _rounded(d.score),
                    "rank": dimension_ranks[d.name][code][0],
                    "points_behind_leader": dimension_ranks[d.name][code][1],
                }
                for d in card.dimensions
            },
            "indicator_scores": {i.id: _rounded(i.score) for i in card.indicators},
        })
    return {"home_country": scorecards[0].home if scorecards else None, "countries": countries}


def comparison_data_block(scorecards: list[Scorecard]) -> str:
    return json.dumps(comparison_data(scorecards), indent=1, ensure_ascii=False)


def comparison_prompt(scorecards: list[Scorecard], profile: CompanyProfile) -> str:
    instructions = COMPARISON_INSTRUCTIONS.format(home=scorecards[0].home)
    return (
        f"{instructions}\n\n{RULES}\n\nCOMPANY:\n{profile.description_md}\n\n"
        f"DATA:\n{comparison_data_block(scorecards)}\n"
    )
