from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.routes import require_user
from app.deps import get_countries, get_profile, get_store
from app.evidence.store import EvidenceStore
from app.profile.company import CompanyProfile
from app.profile.countries import Country
from app.scoring.indicators import Inputs
from app.scoring.scorecard import Scorecard, build_scorecard

router = APIRouter(tags=["scorecard"], dependencies=[Depends(require_user)])

CountriesDep = Annotated[dict[str, Country], Depends(get_countries)]
StoreDep = Annotated[EvidenceStore, Depends(get_store)]
ProfileDep = Annotated[CompanyProfile, Depends(get_profile)]


class CountrySummary(BaseModel):
    iso3: str
    name: str
    has_data: bool


def resolve_country(iso3: str, countries: dict[str, Country]) -> Country:
    code = iso3.strip().upper()
    country = countries.get(code)
    if country is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown country: {code}")
    return country


def load_inputs(country: Country, store: EvidenceStore, profile: CompanyProfile) -> Inputs | None:
    evidence = store.get_country(country.iso3)
    if not evidence:
        return None
    return Inputs(evidence, store.get_country(profile.home_country), country, profile)


@router.get("/countries")
def list_countries(countries: CountriesDep, store: StoreDep) -> list[CountrySummary]:
    with_data = store.countries_with_data()
    return [
        CountrySummary(iso3=c.iso3, name=c.name, has_data=c.iso3 in with_data)
        for c in countries.values()
    ]


@router.get("/countries/{iso3}/scorecard")
def get_scorecard(
    iso3: str, countries: CountriesDep, store: StoreDep, profile: ProfileDep
) -> Scorecard:
    country = resolve_country(iso3, countries)
    inputs = load_inputs(country, store, profile)
    if inputs is None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"No data collected yet for {country.name}")
    return build_scorecard(inputs)
