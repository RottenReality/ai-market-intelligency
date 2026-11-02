"""Shared test data: a Colombia scorecard with at least one indicator per CAGE dimension."""

from pathlib import Path

from app.profile.company import load_profile
from app.profile.countries import Country
from app.scoring.indicators import Inputs
from app.scoring.scorecard import Scorecard, build_scorecard
from tests.scoring.evidence_factory import COLOMBIA, USA, evidence

PROFILE = load_profile(Path("config"))
FULL = {**COLOMBIA, "kogut_singh": 2.5, "max_hour_diff_home": 3.0, "tax_treaty_with_home": False}


def scorecard_for(iso3: str, name: str, values: dict, tz: str = "America/Bogota") -> Scorecard:
    country = Country(iso3, name, ["es"], tz)
    return build_scorecard(Inputs(evidence(iso3, values), evidence("USA", USA), country, PROFILE))


def colombia_scorecard() -> Scorecard:
    # accessibility 49, Administrative 23, Cultural 38, Geographic 71, Economic 66
    return scorecard_for("COL", "Colombia", FULL)
