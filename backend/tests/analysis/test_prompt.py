import json

from app.analysis.prompt import country_data_block, country_prompt
from tests.analysis.fixtures import PROFILE, colombia_scorecard


def test_country_data_block_has_rounded_scores():
    data = json.loads(country_data_block(colombia_scorecard()))
    a3 = next(i for i in data["indicators"] if i["id"] == "A3")
    assert a3 == {
        "id": "A3", "name": "Regulatory quality", "dimension": "Administrative",
        "score": 46, "value": "-0.20", "year": 2025,
        "meaning": "The World Bank rates Colombia's regulatory quality at -0.20, on a scale from "
                   "-2.5 (weak) to 2.5 (strong).",
    }
    missing = next(i for i in data["indicators"] if i["id"] == "C1")
    assert (missing["value"], "meaning" in missing) == ("no data", False)
    assert data["market_accessibility"] == 49
    assert data["dimensions"]["Administrative"] == {"score": 23, "indicators_with_data": "2/3"}


def test_country_prompt_contains_data_description_shape_and_digit_rule():
    prompt = country_prompt(colombia_scorecard(), PROFILE)
    assert country_data_block(colombia_scorecard()) in prompt
    assert PROFILE.description_md in prompt
    assert "Use digits only for numbers that appear in DATA" in prompt
    assert "exactly as DATA shows it (52, never fifty-two)" in prompt
    assert "Every score goes from 0 to 100: higher means easier for the company" in prompt
    assert "Describe each value as its \"meaning\" says" in prompt
    for key in ("executive_summary", "dimensions", "barriers", "opportunities", "recommendation"):
        assert key in prompt


def test_prompt_excludes_urls_and_timestamps():
    prompt = country_prompt(colombia_scorecard(), PROFILE)
    assert "http" not in prompt
    assert "T00:00:00" not in prompt
