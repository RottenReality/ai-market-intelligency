from dataclasses import replace
from pathlib import Path

import pytest

from app.explanation.cache import ExplanationCache
from app.explanation.service import ExplanationFailed, cache_key, explain
from app.profile.company import load_profile
from tests.explanation.fakes import CLEAN, INVENTED, FakeModel
from tests.explanation.test_prompt import colombia_scorecard

PROFILE = load_profile(Path("config"))


@pytest.fixture
def cache(tmp_path) -> ExplanationCache:
    return ExplanationCache(tmp_path / "app.sqlite")


def test_clean_explanation_is_stored_and_not_flagged(cache):
    model = FakeModel([CLEAN])
    result = explain(colombia_scorecard(), PROFILE, model=model, cache=cache)
    assert result.text == CLEAN
    assert result.flagged is False
    assert result.iso3 == "COL"
    assert len(model.prompts) == 1
    assert cache.get("COL", cache_key(colombia_scorecard(), PROFILE)) == result


def test_cache_hit_does_not_call_model(cache):
    first = explain(colombia_scorecard(), PROFILE, model=FakeModel([CLEAN]), cache=cache)
    model = FakeModel([])
    assert explain(colombia_scorecard(), PROFILE, model=model, cache=cache) == first
    assert model.prompts == []


def test_invented_number_triggers_one_retry_then_clean_result_is_not_flagged(cache):
    model = FakeModel([INVENTED, CLEAN])
    result = explain(colombia_scorecard(), PROFILE, model=model, cache=cache)
    assert len(model.prompts) == 2
    assert "20%" in model.prompts[1]
    assert result.text == CLEAN
    assert result.flagged is False


def test_invented_number_twice_is_stored_flagged(cache):
    model = FakeModel([INVENTED, INVENTED])
    result = explain(colombia_scorecard(), PROFILE, model=model, cache=cache)
    assert len(model.prompts) == 2
    assert result.flagged is True
    assert result.text == INVENTED


def test_model_error_raises_explanation_failed(cache):
    with pytest.raises(ExplanationFailed):
        explain(colombia_scorecard(), PROFILE, model=FakeModel([TimeoutError("slow")]), cache=cache)


def test_changed_data_changes_cache_key():
    card = colombia_scorecard()
    changed = card.model_copy(update={"accessibility": 99.0})
    assert cache_key(card, PROFILE) != cache_key(changed, PROFILE)


def test_changed_profile_changes_cache_key():
    other = replace(PROFILE, description_md="A different company.")
    assert cache_key(colombia_scorecard(), PROFILE) != cache_key(colombia_scorecard(), other)


def test_guard_bug_is_not_reported_as_an_ai_failure(cache, monkeypatch):
    from app.explanation import service

    def broken_guard(*_args, **_kwargs):
        raise ValueError("guard bug")

    monkeypatch.setattr(service, "find_unsupported_numbers", broken_guard)
    with pytest.raises(ValueError, match="guard bug"):
        explain(colombia_scorecard(), PROFILE, model=FakeModel([CLEAN]), cache=cache)
