from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.auth.routes import require_user
from app.scoring.indicators import INDICATORS
from app.scoring.routes import CountriesDep, ProfileDep, StoreDep, load_inputs, resolve_country
from app.scoring.scorecard import build_scorecard

router = APIRouter(tags=["comparison"], dependencies=[Depends(require_user)])


class ComparedCountry(BaseModel):
    iso3: str
    name: str
    has_data: bool
    accessibility: float | None
    dimensions: dict[str, float | None]
    # Countries are only comparable when similar data is available: show the coverage.
    indicators_available: int
    indicators_total: int


class Comparison(BaseModel):
    countries: list[ComparedCountry]


def parse_codes(raw: str) -> list[str]:
    codes = [code.strip().upper() for code in raw.split(",") if code.strip()]
    if not codes:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Select at least one country")
    return list(dict.fromkeys(codes))


@router.get("/comparison")
def compare(
    iso3: Annotated[str, Query(description="Comma-separated ISO3 codes, e.g. COL,MEX")],
    countries: CountriesDep,
    store: StoreDep,
    profile: ProfileDep,
) -> Comparison:
    compared = []
    for code in parse_codes(iso3):
        country = resolve_country(code, countries)
        inputs = load_inputs(country, store, profile)
        if inputs is None:
            compared.append(ComparedCountry(
                iso3=country.iso3, name=country.name, has_data=False, accessibility=None,
                dimensions={d: None for d in ("C", "A", "G", "E")},
                indicators_available=0, indicators_total=len(INDICATORS),
            ))
            continue
        card = build_scorecard(inputs)
        compared.append(ComparedCountry(
            iso3=country.iso3, name=country.name, has_data=True,
            accessibility=card.accessibility,
            dimensions={d.id: d.score for d in card.dimensions},
            indicators_available=sum(1 for i in card.indicators if i.status == "ok"),
            indicators_total=len(card.indicators),
        ))
    compared.sort(key=lambda c: (c.accessibility is None, -(c.accessibility or 0)))
    return Comparison(countries=compared)
