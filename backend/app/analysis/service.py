import hashlib
from datetime import UTC, datetime

from pydantic import BaseModel

from app.ai.providers import PROVIDER_LABELS, TextModel
from app.analysis.generate import generate_structured
from app.analysis.guard import numbers_in
from app.analysis.prompt import country_data_block, country_prompt
from app.analysis.schema import CountryAnalysisContent
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
    outdated: bool
    content: CountryAnalysisContent


def analysis_key(payload_json: str, profile: CompanyProfile) -> str:
    return hashlib.sha256((payload_json + profile_hash(profile)).encode()).hexdigest()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _label(provider: str) -> str:
    return PROVIDER_LABELS.get(provider, provider)  # type: ignore[call-overload]


def _to_country_analysis(stored: StoredAnalysis, current_key: str) -> CountryAnalysis:
    return CountryAnalysis(
        iso3=stored.subject,
        provider=stored.provider,
        provider_label=_label(stored.provider),
        model=stored.model,
        created_at=stored.created_at,
        flagged=stored.flagged,
        outdated=stored.cache_key != current_key,
        content=CountryAnalysisContent.model_validate(stored.content),
    )


def generate_country_analysis(
    scorecard: Scorecard, profile: CompanyProfile, model: TextModel, store: AnalysisStore
) -> CountryAnalysis:
    """Always ask the AI (the user chose a provider) and replace the saved analysis."""
    key = analysis_key(scorecard.model_dump_json(), profile)
    allowed = numbers_in(country_data_block(scorecard))
    content, flagged = generate_structured(
        model, country_prompt(scorecard, profile), allowed, CountryAnalysisContent
    )
    stored = StoredAnalysis(
        kind="country", subject=scorecard.country.iso3, cache_key=key, provider=model.provider,
        model=model.model, content=content.model_dump(), flagged=flagged, created_at=_now(),
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
