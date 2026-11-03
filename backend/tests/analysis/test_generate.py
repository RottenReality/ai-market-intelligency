import pytest

from app.analysis.generate import AnalysisUnreadable, generate_structured
from app.analysis.guard import numbers_in
from app.analysis.prompt import country_data_block
from app.analysis.schema import CountryAnalysisContent
from tests.analysis.fakes import FakeModel, country_content
from tests.analysis.fixtures import colombia_scorecard

ALLOWED = numbers_in(country_data_block(colombia_scorecard()))
INVENTED = country_content(executive_summary="Clients withhold a 20% tax [A1].")


def run(model):
    return generate_structured(model, "PROMPT", ALLOWED, CountryAnalysisContent)


def test_clean_first_answer_uses_one_call():
    model = FakeModel([country_content()])
    content, flagged, _ = run(model)
    assert flagged is False
    assert content.executive_summary == "Colombia scores 49% overall [A1]."
    assert len(model.prompts) == 1


def test_malformed_then_valid_uses_two_calls():
    model = FakeModel(["not json", country_content()])
    _content, flagged, _ = run(model)
    assert (flagged, len(model.prompts)) == (False, 2)
    assert "JSON" in model.prompts[1]


def test_malformed_twice_raises_unreadable():
    with pytest.raises(AnalysisUnreadable):
        run(FakeModel(["not json", "still not json"]))


def test_unsupported_numbers_retry_then_clean_is_not_flagged():
    model = FakeModel([INVENTED, country_content()])
    _content, flagged, _ = run(model)
    assert (flagged, len(model.prompts)) == (False, 2)
    assert "20%" in model.prompts[1]


def test_unsupported_numbers_twice_is_flagged():
    model = FakeModel([INVENTED, INVENTED])
    _content, flagged, _ = run(model)
    assert (flagged, len(model.prompts)) == (True, 2)


def test_unsupported_then_malformed_keeps_first_answer_flagged():
    content, flagged, _ = run(FakeModel([INVENTED, "broken"]))
    assert flagged is True
    assert content.executive_summary == "Clients withhold a 20% tax [A1]."


def test_guard_checks_every_field():
    hidden = country_content(barriers=["No tax treaty [A1]", "A 20% withholding [A1]"])
    _, flagged, _ = run(FakeModel([hidden, hidden]))
    assert flagged is True


PREFERS = country_content(barriers=["Most internet users prefer WhatsApp [C2]", "No treaty [A1]"])


def test_preference_wording_is_retried_with_a_note():
    model = FakeModel([PREFERS, country_content()])
    _content, flagged, overstated = run(model)
    assert (flagged, overstated, len(model.prompts)) == (False, False, 2)
    assert "Most internet users prefer WhatsApp [C2]" in model.prompts[1]
    assert 'write "use", not "prefer"' in model.prompts[1]


def test_preference_wording_twice_is_marked():
    _content, flagged, overstated = run(FakeModel([PREFERS, PREFERS]))
    assert (flagged, overstated) == (False, True)


def test_numbers_and_wording_are_fixed_in_the_same_retry():
    both = country_content(executive_summary="Clients withhold a 20% tax [A1].",
                           barriers=["Users prefer WhatsApp [C2]"])
    model = FakeModel([both, country_content()])
    assert run(model)[1:] == (False, False)
    assert "20%" in model.prompts[1] and "prefer WhatsApp" in model.prompts[1]


def test_limit_reached_on_the_retry_keeps_the_first_answer_marked():
    from app.ai.providers import AIProviderError

    limit = AIProviderError(429, "limit")
    content, flagged, overstated = run(FakeModel([PREFERS, limit]))
    assert (flagged, overstated) == (False, True)
    assert content.barriers[0] == "Most internet users prefer WhatsApp [C2]"
    assert run(FakeModel([INVENTED, limit]))[1:] == (True, False)


def test_limit_reached_with_no_readable_answer_is_still_an_error():
    from app.ai.providers import AIProviderError

    with pytest.raises(AIProviderError):
        run(FakeModel(["not json", AIProviderError(429, "limit")]))
