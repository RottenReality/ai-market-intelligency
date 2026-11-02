import json

from app.analysis.schema import CountryAnalysisContent, parse_content, text_fields
from tests.analysis.fakes import country_content


def test_valid_content_parses():
    parsed = parse_content(json.dumps(country_content()), CountryAnalysisContent)
    assert parsed is not None
    assert parsed.dimensions.Administrative == "Administrative is the weakest at 23 [A1]."


def test_lists_are_trimmed_to_three():
    raw = json.dumps(country_content(barriers=["a", "b", "c", "d", "e"]))
    assert parse_content(raw, CountryAnalysisContent).barriers == ["a", "b", "c"]


def test_missing_dimension_key_is_invalid():
    content = country_content()
    del content["dimensions"]["Economic"]
    assert parse_content(json.dumps(content), CountryAnalysisContent) is None


def test_empty_list_is_invalid():
    raw = json.dumps(country_content(opportunities=[]))
    assert parse_content(raw, CountryAnalysisContent) is None


def test_blank_text_is_invalid():
    raw = json.dumps(country_content(recommendation="  "))
    assert parse_content(raw, CountryAnalysisContent) is None


def test_parse_strips_markdown_fence():
    raw = "```json\n" + json.dumps(country_content()) + "\n```"
    assert parse_content(raw, CountryAnalysisContent) is not None


def test_parse_returns_none_for_non_json():
    assert parse_content("Here is my analysis: Colombia is great.", CountryAnalysisContent) is None


def test_text_fields_lists_every_string():
    parsed = parse_content(json.dumps(country_content()), CountryAnalysisContent)
    fields = text_fields(parsed)
    assert "Colombia scores 49% overall [A1]." in fields
    assert "Large cities [E2]" in fields
    assert "Explore a local partner first, then a short pilot." in fields
    assert len(fields) == 1 + 4 + 2 + 2 + 1
