from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.routes import require_user
from app.deps import get_explanation_cache, get_explanation_model
from app.evidence.store import EvidenceStore
from app.explanation.cache import Explanation, ExplanationCache
from app.explanation.model import ExplanationModel
from app.explanation.service import ExplanationFailed, cache_key, explain
from app.profile.company import CompanyProfile
from app.profile.countries import Country
from app.scoring.routes import CountriesDep, ProfileDep, StoreDep, load_inputs, resolve_country
from app.scoring.scorecard import Scorecard, build_scorecard

router = APIRouter(tags=["explanation"], dependencies=[Depends(require_user)])

CacheDep = Annotated[ExplanationCache, Depends(get_explanation_cache)]
ModelDep = Annotated[ExplanationModel | None, Depends(get_explanation_model)]


def load_scorecard(
    iso3: str, countries: dict[str, Country], store: EvidenceStore, profile: CompanyProfile
) -> Scorecard:
    country = resolve_country(iso3, countries)
    inputs = load_inputs(country, store, profile)
    if inputs is None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"No data collected yet for {country.name}")
    return build_scorecard(inputs)


@router.get("/countries/{iso3}/explanation")
def get_explanation(
    iso3: str, countries: CountriesDep, store: StoreDep, profile: ProfileDep, cache: CacheDep
) -> Explanation:
    scorecard = load_scorecard(iso3, countries, store, profile)
    explanation = cache.get(scorecard.country.iso3, cache_key(scorecard, profile))
    if explanation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No explanation yet")
    return explanation


@router.post("/countries/{iso3}/explanation")
def create_explanation(
    iso3: str,
    countries: CountriesDep,
    store: StoreDep,
    profile: ProfileDep,
    cache: CacheDep,
    model: ModelDep,
) -> Explanation:
    scorecard = load_scorecard(iso3, countries, store, profile)
    if model is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "AI is not configured")
    try:
        return explain(scorecard, profile, model=model, cache=cache)
    except ExplanationFailed as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "The AI service failed") from error
