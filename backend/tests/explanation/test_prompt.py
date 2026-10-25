import json
from pathlib import Path

from app.explanation.prompt import build_prompt, data_block
from app.profile.company import load_profile
from app.profile.countries import Country
from app.scoring.indicators import Inputs
from app.scoring.scorecard import build_scorecard
from tests.scoring.evidence_factory import COLOMBIA, USA, evidence

FULL = {**COLOMBIA, "kogut_singh": 2.5, "max_hour_diff_home": 3.0, "tax_treaty_with_home": False}


def colombia_scorecard():
    profile = load_profile(Path("config"))
    country = Country("COL", "Colombia", ["es"], "America/Bogota")
    return build_scorecard(Inputs(evidence("COL", FULL), evidence("USA", USA), country, profile))


def test_data_block_contains_rounded_scores_and_ids():
    data = json.loads(data_block(colombia_scorecard()))
    a3 = next(i for i in data["indicators"] if i["id"] == "A3")
    assert a3 == {
        "id": "A3", "name": "Regulatory quality", "dimension": "Administrative",
        "score": 46, "value": "-0.20", "year": 2025,
    }
    assert data["country"] == "Colombia"
    assert data["home_country"] == "USA"
    assert data["dimensions"]["Administrative"] == {"score": 23, "indicators_with_data": "2/3"}


def test_missing_indicators_are_marked_not_scored():
    data = json.loads(data_block(colombia_scorecard()))
    c1 = next(i for i in data["indicators"] if i["id"] == "C1")
    assert c1["score"] is None
    assert c1["value"] == "no data"


def test_prompt_includes_company_description_and_data():
    profile = load_profile(Path("config"))
    prompt = build_prompt(colombia_scorecard(), profile)
    assert profile.description_md in prompt
    assert data_block(colombia_scorecard()) in prompt
    assert "Use only numbers that appear in DATA" in prompt


def test_prompt_excludes_retrieval_timestamps_and_urls():
    prompt = build_prompt(colombia_scorecard(), load_profile(Path("config")))
    assert "http" not in prompt
    assert "2026-10-25T" not in prompt
