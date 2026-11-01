from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.analysis.routes import AnalysisStoreDep, load_scorecard
from app.analysis.service import get_country_analysis
from app.auth.routes import require_user
from app.comparison.routes import parse_codes
from app.reports.pdf import build_report
from app.scoring.routes import CountriesDep, ProfileDep, StoreDep

router = APIRouter(tags=["reports"], dependencies=[Depends(require_user)])


@router.get("/reports/pdf", response_class=Response)
def pdf_report(
    iso3: Annotated[str, Query(description="Comma-separated ISO3 codes, e.g. COL,MEX")],
    countries: CountriesDep,
    store: StoreDep,
    profile: ProfileDep,
    analyses: AnalysisStoreDep,
) -> Response:
    """Build the PDF from stored data and saved analyses only: it never calls the AI."""
    scorecards = [load_scorecard(code, countries, store, profile) for code in parse_codes(iso3)]
    explanations = {
        card.country.iso3: get_country_analysis(card, profile, analyses)
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
