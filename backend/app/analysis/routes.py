from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.ai.providers import AIProviderError, TextModel
from app.analysis.generate import AnalysisUnreadable
from app.analysis.service import (
    ComparisonInsight,
    CountryAnalysis,
    generate_comparison_insight,
    generate_country_analysis,
    get_comparison_insight,
    get_country_analysis,
)
from app.analysis.store import AnalysisStore
from app.auth.routes import require_user
from app.comparison.routes import parse_codes
from app.deps import get_ai_models, get_analysis_store
from app.evidence.store import EvidenceStore
from app.profile.company import CompanyProfile
from app.profile.countries import Country
from app.scoring.routes import CountriesDep, ProfileDep, StoreDep, load_inputs, resolve_country
from app.scoring.scorecard import Scorecard, build_scorecard

router = APIRouter(tags=["analysis"], dependencies=[Depends(require_user)])

AnalysisStoreDep = Annotated[AnalysisStore, Depends(get_analysis_store)]
ModelsDep = Annotated[dict[str, TextModel], Depends(get_ai_models)]


class GenerateRequest(BaseModel):
    provider: str


def load_scorecard(
    iso3: str, countries: dict[str, Country], store: EvidenceStore, profile: CompanyProfile
) -> Scorecard:
    country = resolve_country(iso3, countries)
    inputs = load_inputs(country, store, profile)
    if inputs is None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"No data collected yet for {country.name}")
    return build_scorecard(inputs)


def pick_model(models: dict[str, TextModel], provider: str) -> TextModel:
    if not models:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "AI is not configured")
    model = models.get(provider)
    if model is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This AI is not configured")
    return model


def ai_errors(error: Exception) -> HTTPException:
    if isinstance(error, AIProviderError):
        return HTTPException(error.status_code, error.detail)
    return HTTPException(
        status.HTTP_502_BAD_GATEWAY, "The AI returned an unreadable answer. Try again."
    )


@router.get("/countries/{iso3}/analysis")
def get_analysis(
    iso3: str, countries: CountriesDep, store: StoreDep, profile: ProfileDep,
    analyses: AnalysisStoreDep,
) -> CountryAnalysis:
    scorecard = load_scorecard(iso3, countries, store, profile)
    analysis = get_country_analysis(scorecard, profile, analyses)
    if analysis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No AI analysis yet")
    return analysis


@router.post("/countries/{iso3}/analysis")
def create_analysis(
    iso3: str, body: GenerateRequest, countries: CountriesDep, store: StoreDep,
    profile: ProfileDep, analyses: AnalysisStoreDep, models: ModelsDep,
) -> CountryAnalysis:
    scorecard = load_scorecard(iso3, countries, store, profile)
    model = pick_model(models, body.provider)
    try:
        return generate_country_analysis(scorecard, profile, model, analyses)
    except (AIProviderError, AnalysisUnreadable) as error:
        raise ai_errors(error) from error


class InsightRequest(BaseModel):
    iso3: list[str]
    provider: str


def scorecards_with_data(
    codes: list[str], countries: dict[str, Country], store: EvidenceStore, profile: CompanyProfile
) -> list[Scorecard]:
    """Scorecards of the selected countries that have data (unknown codes are a 404)."""
    cards = []
    for code in dict.fromkeys(c.strip().upper() for c in codes if c.strip()):
        inputs = load_inputs(resolve_country(code, countries), store, profile)
        if inputs is not None:
            cards.append(build_scorecard(inputs))
    if len(cards) < 2:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Select at least two countries with data"
        )
    return cards


@router.get("/comparison/insight")
def get_insight(
    iso3: Annotated[str, Query(description="Comma-separated ISO3 codes, e.g. COL,MEX")],
    countries: CountriesDep, store: StoreDep, profile: ProfileDep, analyses: AnalysisStoreDep,
) -> ComparisonInsight:
    cards = scorecards_with_data(parse_codes(iso3), countries, store, profile)
    insight = get_comparison_insight(cards, profile, analyses)
    if insight is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No comparison insight yet")
    return insight


@router.post("/comparison/insight")
def create_insight(
    body: InsightRequest, countries: CountriesDep, store: StoreDep, profile: ProfileDep,
    analyses: AnalysisStoreDep, models: ModelsDep,
) -> ComparisonInsight:
    cards = scorecards_with_data(body.iso3, countries, store, profile)
    model = pick_model(models, body.provider)
    try:
        return generate_comparison_insight(cards, profile, model, analyses)
    except (AIProviderError, AnalysisUnreadable) as error:
        raise ai_errors(error) from error
