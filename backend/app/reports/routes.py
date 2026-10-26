from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.auth.routes import require_user
from app.comparison.routes import parse_codes
from app.explanation.routes import CacheDep, load_scorecard
from app.explanation.service import cache_key
from app.reports.pdf import build_report
from app.scoring.routes import CountriesDep, ProfileDep, StoreDep

router = APIRouter(tags=["reports"], dependencies=[Depends(require_user)])


@router.get("/reports/pdf", response_class=Response)
def pdf_report(
    iso3: Annotated[str, Query(description="Comma-separated ISO3 codes, e.g. COL,MEX")],
    countries: CountriesDep,
    store: StoreDep,
    profile: ProfileDep,
    cache: CacheDep,
) -> Response:
    """Build the PDF from stored data and saved explanations only: it never calls the LLM."""
    scorecards = [load_scorecard(code, countries, store, profile) for code in parse_codes(iso3)]
    explanations = {
        card.country.iso3: cache.get(card.country.iso3, cache_key(card, profile))
        for card in scorecards
    }
    now = datetime.now(UTC)
    codes = "-".join(card.country.iso3 for card in scorecards)
    return Response(
        content=build_report(scorecards, explanations, profile, now),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="market-accessibility-{codes}-'
            f'{now:%Y-%m-%d}.pdf"'
        },
    )
