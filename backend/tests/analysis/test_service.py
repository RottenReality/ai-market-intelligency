from dataclasses import replace

import pytest

from app.analysis.service import generate_country_analysis, get_country_analysis
from app.analysis.store import AnalysisStore
from tests.analysis.fakes import FakeModel, country_content
from tests.analysis.fixtures import FULL, PROFILE, colombia_scorecard, scorecard_for


@pytest.fixture
def store(tmp_path) -> AnalysisStore:
    return AnalysisStore(tmp_path / "app.sqlite")


def test_generate_saves_provider_model_and_content(store):
    model = FakeModel([country_content()], provider="groq", model="openai/gpt-oss-120b")
    result = generate_country_analysis(colombia_scorecard(), PROFILE, model, store)
    assert (result.iso3, result.provider, result.provider_label) == ("COL", "groq", "Groq")
    assert result.model == "openai/gpt-oss-120b"
    assert result.flagged is False and result.outdated is False
    assert result.content.executive_summary == "Colombia scores 49% overall [A1]."
    assert get_country_analysis(colombia_scorecard(), PROFILE, store) == result


def test_regenerating_with_other_provider_replaces(store):
    generate_country_analysis(colombia_scorecard(), PROFILE, FakeModel([country_content()]), store)
    groq = FakeModel([country_content()], provider="groq")
    generate_country_analysis(colombia_scorecard(), PROFILE, groq, store)
    assert get_country_analysis(colombia_scorecard(), PROFILE, store).provider == "groq"


def test_get_without_analysis_returns_none(store):
    assert get_country_analysis(colombia_scorecard(), PROFILE, store) is None


def test_outdated_after_data_change(store):
    generate_country_analysis(colombia_scorecard(), PROFILE, FakeModel([country_content()]), store)
    changed = scorecard_for("COL", "Colombia", {**FULL, "inflation_pct": 9.0})
    assert get_country_analysis(changed, PROFILE, store).outdated is True


def test_outdated_after_profile_change(store):
    generate_country_analysis(colombia_scorecard(), PROFILE, FakeModel([country_content()]), store)
    edited = replace(PROFILE, description_md="A different company.")
    result = get_country_analysis(colombia_scorecard(), edited, store)
    assert result is not None
    assert result.outdated is True


def test_not_outdated_when_nothing_changed(store):
    generate_country_analysis(colombia_scorecard(), PROFILE, FakeModel([country_content()]), store)
    assert get_country_analysis(colombia_scorecard(), PROFILE, store).outdated is False


def test_analysis_saved_with_gemini_keeps_its_label(store):
    old = FakeModel([country_content()], provider="gemini", model="gemini-3.8-flash")
    generate_country_analysis(colombia_scorecard(), PROFILE, old, store)
    saved = get_country_analysis(colombia_scorecard(), PROFILE, store)
    assert (saved.provider, saved.provider_label) == ("gemini", "Gemini")
