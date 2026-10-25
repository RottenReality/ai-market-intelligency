import pytest

from app.profile.company import load_profile
from app.profile.countries import Country
from app.scoring.indicators import Inputs
from app.scoring.scorecard import build_scorecard
from tests.scoring.evidence_factory import COLOMBIA, USA, evidence

COL = Country("COL", "Colombia", ["es"], "America/Bogota")


def inputs(country_values=COLOMBIA, home_values=USA) -> Inputs:
    from pathlib import Path

    return Inputs(
        country=evidence("COL", country_values),
        home=evidence("USA", home_values),
        country_cfg=COL,
        profile=load_profile(Path("config")),
    )


def by_id(scorecard):
    return {indicator.id: indicator for indicator in scorecard.indicators}


def test_scorecard_scores_colombia_world_bank_indicators():
    card = build_scorecard(inputs())
    indicators = by_id(card)
    assert card.country.iso3 == "COL" and card.home == "USA"
    assert indicators["A3"].score == pytest.approx(46.05, abs=0.01)
    assert indicators["G2"].score == pytest.approx(79.35, abs=0.01)
    assert indicators["E1"].score == pytest.approx(24.86, abs=0.01)
    assert indicators["E2"].score == 100.0
    assert indicators["E3"].score == pytest.approx(74.3)
    assert indicators["G2"].raw == pytest.approx(79.345, abs=0.001)


def test_missing_metric_gives_missing_status_not_zero():
    values = {k: v for k, v in COLOMBIA.items() if k != "inflation_pct"}
    e3 = by_id(build_scorecard(inputs(country_values=values)))["E3"]
    assert e3.status == "missing"
    assert e3.score is None
    assert e3.raw is None


def test_e1_lists_both_country_and_home_sources():
    e1 = by_id(build_scorecard(inputs()))["E1"]
    urls = [source.url for source in e1.sources]
    assert urls == [
        "https://example.org/COL/gni_ppp_per_capita",
        "https://example.org/USA/gni_ppp_per_capita",
    ]


def test_e1_is_missing_when_home_value_is_missing():
    e1 = by_id(build_scorecard(inputs(home_values={})))["E1"]
    assert e1.status == "missing"
