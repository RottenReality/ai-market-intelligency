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
    content, flagged = run(model)
    assert flagged is False
    assert content.executive_summary == "Colombia scores 49% overall [A1]."
    assert len(model.prompts) == 1


def test_malformed_then_valid_uses_two_calls():
    model = FakeModel(["not json", country_content()])
    content, flagged = run(model)
    assert (flagged, len(model.prompts)) == (False, 2)
    assert "JSON" in model.prompts[1]


def test_malformed_twice_raises_unreadable():
    with pytest.raises(AnalysisUnreadable):
        run(FakeModel(["not json", "still not json"]))


def test_unsupported_numbers_retry_then_clean_is_not_flagged():
    model = FakeModel([INVENTED, country_content()])
    content, flagged = run(model)
    assert (flagged, len(model.prompts)) == (False, 2)
    assert "20%" in model.prompts[1]


def test_unsupported_numbers_twice_is_flagged():
    model = FakeModel([INVENTED, INVENTED])
    content, flagged = run(model)
    assert (flagged, len(model.prompts)) == (True, 2)


def test_unsupported_then_malformed_keeps_first_answer_flagged():
    content, flagged = run(FakeModel([INVENTED, "broken"]))
    assert flagged is True
    assert content.executive_summary == "Clients withhold a 20% tax [A1]."


def test_guard_checks_every_field():
    hidden = country_content(barriers=["No tax treaty [A1]", "A 20% withholding [A1]"])
    _, flagged = run(FakeModel([hidden, hidden]))
    assert flagged is True
