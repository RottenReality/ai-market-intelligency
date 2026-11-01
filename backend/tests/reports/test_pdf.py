from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.analysis.schema import CountryAnalysisContent
from app.analysis.service import ComparisonInsight, CountryAnalysis, RankedExplanation
from app.profile.company import load_profile
from app.profile.countries import Country
from app.reports.pdf import build_report
from app.scoring.indicators import Inputs
from app.scoring.scorecard import build_scorecard
from tests.analysis.fakes import country_content
from tests.analysis.fixtures import FULL, colombia_scorecard, scorecard_for
from tests.scoring.evidence_factory import USA, evidence

PROFILE = load_profile(Path("config"))
GENERATED = datetime(2026, 10, 25, 12, 0, tzinfo=UTC)
ATTRIBUTION = (
    "AI analysis written by Groq (openai/gpt-oss-120b) on 2026-11-01. "
    "Numbers checked against the data."
)


def mexico_scorecard():
    values = {**FULL, "max_hour_diff_home": 2.0, "tax_treaty_with_home": True}
    country = Country("MEX", "Mexico", ["es"], "America/Mexico_City")
    return build_scorecard(Inputs(evidence("MEX", values), evidence("USA", USA), country, PROFILE))


def pages_text(pdf: bytes) -> list[str]:
    return [page.extract_text() for page in PdfReader(BytesIO(pdf)).pages]


def all_text(pdf: bytes) -> str:
    # pypdf may break long lines; join with spaces so phrases can be matched across wraps.
    return " ".join(" ".join(pages_text(pdf)).split())


def analysis(flagged: bool = False, outdated: bool = False, **content) -> CountryAnalysis:
    return CountryAnalysis(
        iso3="COL", provider="groq", provider_label="Groq", model="openai/gpt-oss-120b",
        created_at="2026-11-01T10:00:00+00:00", flagged=flagged, outdated=outdated,
        content=CountryAnalysisContent.model_validate(country_content(**content)),
    )


def insight() -> ComparisonInsight:
    return ComparisonInsight(
        countries=["COL", "MEX"], provider="gemini", provider_label="Gemini",
        model="gemini-3.8-flash", created_at="2026-11-01T10:00:00+00:00", flagged=False,
        outdated=False, summary="Mexico leads thanks to its tax treaty [A1].",
        ranking=[
            RankedExplanation(iso3="MEX", name="Mexico", accessibility=60.0, rank=1,
                              explanation="MEXICO-TEXT has a tax treaty [A1]."),
            RankedExplanation(iso3="COL", name="Colombia", accessibility=49.0, rank=2,
                              explanation="COLOMBIA-TEXT lacks one [A1]."),
        ],
        key_differences=["Tax treaty [A1]"],
    )


def test_single_country_report_contains_name_score_and_indicator_ids():
    pdf = build_report([colombia_scorecard()], {}, None, PROFILE, GENERATED)
    assert pdf.startswith(b"%PDF")
    text = all_text(pdf)
    assert "Colombia" in text
    assert "Market accessibility: 49%" in text
    for indicator_id in ("C1", "C2", "C3", "A1", "A2", "A3", "G1", "G2", "G3", "E1", "E2", "E3"):
        assert indicator_id in text
    assert PROFILE.name in text
    assert "2026-10-25" in text


def test_multi_country_report_has_ranking_page_after_cover():
    pdf = build_report([mexico_scorecard(), colombia_scorecard()], {}, None, PROFILE, GENERATED)
    ranking_page = pages_text(pdf)[1]
    assert "Ranking" in ranking_page
    assert ranking_page.index("Mexico") < ranking_page.index("Colombia")


def test_country_page_has_ai_sections_and_attribution():
    pdf = build_report([colombia_scorecard()], {"COL": analysis()}, None, PROFILE, GENERATED)
    text = all_text(pdf)
    for heading in ("Executive summary", "Why each dimension scored this way", "Barriers",
                    "Opportunities", "Recommendation"):
        assert heading in text
    assert "Colombia scores 49% overall [A1]." in text
    assert "Administrative is the weakest at 23 [A1]." in text
    assert "Explore a local partner first, then a short pilot." in text
    assert ATTRIBUTION in text


def test_missing_analysis_says_not_generated():
    pdf = build_report([colombia_scorecard()], {"COL": None}, None, PROFILE, GENERATED)
    text = all_text(pdf)
    assert "AI analysis not generated yet" in text
    assert "Executive summary" not in text


def test_flagged_and_outdated_notes():
    pdf = build_report([colombia_scorecard()], {"COL": analysis(flagged=True, outdated=True)},
                       None, PROFILE, GENERATED)
    text = all_text(pdf)
    assert "Some numbers could not be verified; review before use." in text
    assert "Written before the latest data or company change." in text
    plain = build_report([colombia_scorecard()], {"COL": analysis()}, None, PROFILE, GENERATED)
    assert "could not be verified" not in all_text(plain)
    assert "Written before" not in all_text(plain)


def test_rank_shown_only_for_several_countries():
    cards = [
        colombia_scorecard(),
        mexico_scorecard(),
        scorecard_for("ESP", "Spain", FULL, "Europe/Madrid"),
        scorecard_for("CHL", "Chile", FULL, "America/Santiago"),
    ]
    text = all_text(build_report(cards, {}, None, PROFILE, GENERATED))
    assert "rank 4 of 4" in text or "rank 3 of 4" in text
    assert "rank 1 of 4" in text
    single = all_text(build_report([colombia_scorecard()], {}, None, PROFILE, GENERATED))
    assert "rank" not in single.lower().replace("ranking", "")


def test_comparison_page_includes_insight_in_real_order():
    pdf = build_report([colombia_scorecard(), mexico_scorecard()], {}, insight(), PROFILE,
                       GENERATED)
    comparison_page = " ".join(pages_text(pdf)[1].split())
    assert "Mexico leads thanks to its tax treaty [A1]." in comparison_page \
        or "Mexico leads thanks to its tax treaty [A1]." in all_text(pdf)
    text = all_text(pdf)
    assert text.index("MEXICO-TEXT") < text.index("COLOMBIA-TEXT")
    assert "Tax treaty [A1]" in text
    assert "AI analysis written by Gemini (gemini-3.8-flash) on 2026-11-01." in text


def test_unicode_text_renders():
    summary = "Colombia – accessible ≥ “quoted” — Bogotá, Peñalolén, 49%."
    pdf = build_report([colombia_scorecard()], {"COL": analysis(executive_summary=summary)},
                       None, PROFILE, GENERATED)
    assert "Peñalolén" in all_text(pdf)


def test_long_ai_text_flows_across_pages():
    long = ("Bogotá y Medellín concentran la demanda; la expansión requiere paciencia. " * 20)[:1500]
    dims = {name: f"{name}: {long}" for name in
            ("Cultural", "Administrative", "Geographic", "Economic")}
    heavy = analysis(executive_summary=long, dimensions=dims, recommendation=long,
                     barriers=[long[:400]] * 3, opportunities=[long[:400]] * 3)
    short_pdf = build_report([colombia_scorecard()], {"COL": analysis()}, None, PROFILE,
                             GENERATED)
    long_pdf = build_report([colombia_scorecard()], {"COL": heavy}, None, PROFILE, GENERATED)
    assert len(pages_text(long_pdf)) > len(pages_text(short_pdf))
    text = all_text(long_pdf)
    assert "Economic: Bogotá y Medellín" in text
    assert text.count("expansión") >= 20
