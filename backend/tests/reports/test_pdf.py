from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.explanation.cache import Explanation
from app.profile.company import load_profile
from app.profile.countries import Country
from app.reports.pdf import build_report
from app.scoring.indicators import Inputs
from app.scoring.scorecard import build_scorecard
from tests.explanation.test_prompt import FULL, colombia_scorecard
from tests.scoring.evidence_factory import USA, evidence

PROFILE = load_profile(Path("config"))
GENERATED = datetime(2026, 10, 25, 12, 0, tzinfo=UTC)


def mexico_scorecard():
    values = {**FULL, "max_hour_diff_home": 2.0, "tax_treaty_with_home": True}
    country = Country("MEX", "Mexico", ["es"], "America/Mexico_City")
    return build_scorecard(Inputs(evidence("MEX", values), evidence("USA", USA), country, PROFILE))


def pages_text(pdf: bytes) -> list[str]:
    return [page.extract_text() for page in PdfReader(BytesIO(pdf)).pages]


def explanation(text: str, flagged: bool = False) -> Explanation:
    return Explanation(iso3="COL", text=text, flagged=flagged, created_at="2026-10-25T10:00:00+00:00")


def test_single_country_report_contains_name_score_and_indicator_ids():
    pdf = build_report([colombia_scorecard()], {}, PROFILE, GENERATED)
    assert pdf.startswith(b"%PDF")
    text = "\n".join(pages_text(pdf))
    assert "Colombia" in text
    assert "Market accessibility: 49%" in text
    for indicator_id in ("C1", "C2", "C3", "A1", "A2", "A3", "G1", "G2", "G3", "E1", "E2", "E3"):
        assert indicator_id in text
    assert PROFILE.name in text
    assert "2026-10-25" in text


def test_multi_country_report_has_ranking_page_after_cover():
    pdf = build_report([mexico_scorecard(), colombia_scorecard()], {}, PROFILE, GENERATED)
    ranking_page = pages_text(pdf)[1]
    assert "Ranking" in ranking_page
    assert ranking_page.index("Mexico") < ranking_page.index("Colombia")


def test_explanation_text_with_unicode_renders():
    text = "Colombia – accessible ≥ “quoted” — Bogotá, Peñalolén, 49%."
    pdf = build_report([colombia_scorecard()], {"COL": explanation(text)}, PROFILE, GENERATED)
    assert "Peñalolén" in "\n".join(pages_text(pdf))


def test_missing_explanation_is_stated():
    pdf = build_report([colombia_scorecard()], {"COL": None}, PROFILE, GENERATED)
    assert "Explanation not generated yet." in "\n".join(pages_text(pdf))


def test_flagged_explanation_is_marked_for_review():
    pdf = build_report(
        [colombia_scorecard()], {"COL": explanation("Some text.", flagged=True)}, PROFILE, GENERATED
    )
    assert "could not be verified" in "\n".join(pages_text(pdf))
