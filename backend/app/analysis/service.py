import hashlib
from datetime import UTC, datetime

from pydantic import BaseModel

from app.ai.providers import PROVIDER_LABELS, RETIRED_LABELS, TextModel
from app.analysis.generate import generate_structured
from app.analysis.guard import numbers_in
from app.analysis.prompt import (
    comparison_data_block,
    comparison_prompt,
    country_data_block,
    country_prompt,
)
from app.analysis.schema import ComparisonInsightContent, CountryAnalysisContent, RankingText
from app.analysis.store import AnalysisStore, StoredAnalysis
from app.profile.company import CompanyProfile, profile_hash
from app.scoring.scorecard import Scorecard


class CountryAnalysis(BaseModel):
    iso3: str
    provider: str
    provider_label: str
    model: str
    created_at: str
    flagged: bool
    overstated: bool = False  # wording guard: a share of users still called a preference
    outdated: bool
    content: CountryAnalysisContent


def analysis_key(payload_json: str, profile: CompanyProfile) -> str:
    return hashlib.sha256((payload_json + profile_hash(profile)).encode()).hexdigest()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _label(provider: str) -> str:
    return {**RETIRED_LABELS, **PROVIDER_LABELS}.get(provider, provider)


def _to_country_analysis(stored: StoredAnalysis, current_key: str) -> CountryAnalysis:
    return CountryAnalysis(
        iso3=stored.subject,
        provider=stored.provider,
        provider_label=_label(stored.provider),
        model=stored.model,
        created_at=stored.created_at,
        flagged=stored.flagged,
        overstated=stored.overstated,
        outdated=stored.cache_key != current_key,
        content=CountryAnalysisContent.model_validate(stored.content),
    )


def generate_country_analysis(
    scorecard: Scorecard, profile: CompanyProfile, model: TextModel, store: AnalysisStore
) -> CountryAnalysis:
    """Always ask the AI (the user chose a provider) and replace the saved analysis."""
    key = analysis_key(scorecard.model_dump_json(), profile)
    allowed = numbers_in(country_data_block(scorecard))
    content, flagged, overstated = generate_structured(
        model, country_prompt(scorecard, profile), allowed, CountryAnalysisContent
    )
    stored = StoredAnalysis(
        kind="country", subject=scorecard.country.iso3, cache_key=key, provider=model.provider,
        model=model.model, content=content.model_dump(), flagged=flagged,
        overstated=overstated, created_at=_now(),
    )
    store.put(stored)
    return _to_country_analysis(stored, key)


def get_country_analysis(
    scorecard: Scorecard, profile: CompanyProfile, store: AnalysisStore
) -> CountryAnalysis | None:
    stored = store.get("country", scorecard.country.iso3)
    if stored is None:
        return None
    return _to_country_analysis(stored, analysis_key(scorecard.model_dump_json(), profile))


class RankedExplanation(BaseModel):
    iso3: str
    name: str
    accessibility: float | None
    rank: int
    explanation: str


class ComparisonInsight(BaseModel):
    countries: list[str]
    provider: str
    provider_label: str
    model: str
    created_at: str
    flagged: bool
    overstated: bool = False  # wording guard: a share of users still called a preference
    outdated: bool
    summary: str
    ranking: list[RankedExplanation]
    key_differences: list[str]


def comparison_subject(codes: list[str]) -> str:
    return ",".join(sorted(codes))


def _comparison_key(scorecards: list[Scorecard], profile: CompanyProfile) -> str:
    ordered = sorted(scorecards, key=lambda c: c.country.iso3)
    return analysis_key("".join(c.model_dump_json() for c in ordered), profile)


def order_ranking(
    scorecards: list[Scorecard], entries: list[RankingText]
) -> list[RankedExplanation]:
    """Rank order always comes from the real scores; the AI's text is matched by country."""
    texts: dict[str, str] = {}
    for entry in entries:
        texts.setdefault(entry.iso3.upper(), entry.explanation)
    ordered = sorted(scorecards, key=lambda c: (c.accessibility is None, -(c.accessibility or 0)))
    return [
        RankedExplanation(
            iso3=card.country.iso3,
            name=card.country.name,
            accessibility=card.accessibility,
            rank=position,
            explanation=texts.get(card.country.iso3, "No explanation provided"),
        )
        for position, card in enumerate(ordered, start=1)
    ]


def _to_insight(
    stored: StoredAnalysis, scorecards: list[Scorecard], current_key: str
) -> ComparisonInsight:
    content = ComparisonInsightContent.model_validate(stored.content)
    return ComparisonInsight(
        countries=stored.subject.split(","),
        provider=stored.provider,
        provider_label=_label(stored.provider),
        model=stored.model,
        created_at=stored.created_at,
        flagged=stored.flagged,
        overstated=stored.overstated,
        outdated=stored.cache_key != current_key,
        summary=content.summary,
        ranking=order_ranking(scorecards, content.ranking),
        key_differences=content.key_differences,
    )


def generate_comparison_insight(
    scorecards: list[Scorecard], profile: CompanyProfile, model: TextModel, store: AnalysisStore
) -> ComparisonInsight:
    key = _comparison_key(scorecards, profile)
    allowed = numbers_in(comparison_data_block(scorecards))
    content, flagged, overstated = generate_structured(
        model, comparison_prompt(scorecards, profile), allowed, ComparisonInsightContent
    )
    stored = StoredAnalysis(
        kind="comparison", subject=comparison_subject([c.country.iso3 for c in scorecards]),
        cache_key=key, provider=model.provider, model=model.model,
        content=content.model_dump(), flagged=flagged,
        overstated=overstated, created_at=_now(),
    )
    store.put(stored)
    return _to_insight(stored, scorecards, key)


def get_comparison_insight(
    scorecards: list[Scorecard], profile: CompanyProfile, store: AnalysisStore
) -> ComparisonInsight | None:
    stored = store.get("comparison", comparison_subject([c.country.iso3 for c in scorecards]))
    if stored is None:
        return None
    return _to_insight(stored, scorecards, _comparison_key(scorecards, profile))
