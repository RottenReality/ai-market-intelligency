"""Each indicator's short value and plain-language meaning (shown in the app, the PDF and to the AI)."""

from dataclasses import replace

import pytest

from app.profile.countries import Country
from app.scoring.indicators import Inputs
from app.scoring.wording import describe
from tests.analysis.fixtures import PROFILE
from tests.scoring.evidence_factory import USA, evidence

VALUES = {
    "english_band": "low",
    "whatsapp_pct": 92.1,
    "kogut_singh": 2.52,
    "tax_treaty_with_home": False,
    "trade_agreement_with_home": True,
    "regulatory_quality": -0.1973526,
    "max_hour_diff_home": 3.0,
    "internet_pct": 79.34543299,
    "social_media_pct": 70.4,
    "gni_ppp_per_capita": 22250.0,
    "urban_population": 42090207.0,
    "inflation_pct": 5.14,
}


def inputs(profile=PROFILE, **overrides) -> Inputs:
    country = Country("COL", "Colombia", ["es"], "America/Bogota")
    return Inputs(evidence("COL", {**VALUES, **overrides}), evidence("USA", USA), country, profile)


@pytest.mark.parametrize(("indicator", "display", "meaning"), [
    ("C1", "English: Low",
     "Colombia's main business language is Spanish, which the company does not work in. "
     "English proficiency there is Low (EF English Proficiency Index), so the language barrier "
     "is high."),
    ("C2", "92.1% use WhatsApp",
     "92.1% of internet users in Colombia say they use WhatsApp. The company reaches customers "
     "only by SMS and email, so its channels fit less where WhatsApp is this common. This shows "
     "how common WhatsApp is, not that people stopped using SMS or email."),
    ("C3", "2.52",
     "Cultural distance between Colombia and the USA (Kogut-Singh index on Hofstede's "
     "dimensions) is 2.52, where 0 means the same culture and 4 or more means very distant."),
    ("A1", "No", "There is no income tax treaty between Colombia and the USA."),
    ("A2", "Yes", "There is a trade agreement in force between Colombia and the USA."),
    ("A3", "-0.20",
     "The World Bank rates Colombia's regulatory quality at -0.20, on a scale from -2.5 (weak) "
     "to 2.5 (strong)."),
    ("G1", "3 h difference",
     "Colombia's working day is up to 3 h apart from the company's time zone "
     "(America/Los_Angeles), so 5 of 8 working hours overlap."),
    ("G2", "79.3%", "79.3% of the population of Colombia uses the internet."),
    ("G3", "70.4%", "Social media user identities in Colombia equal 70.4% of the population."),
    ("E1", "$22,250",
     "Income per person in Colombia (GNI per capita, PPP) is $22,250, which is 25% of the USA's "
     "$89,490."),
    ("E2", "42.1M",
     "42.1M people live in cities in Colombia. The score counts 10M or more as a large market."),
    ("E3", "5.1%",
     "Consumer prices in Colombia rose 5.1% in a year. Each point of inflation lowers the score "
     "by 5."),
])
def test_value_and_meaning(indicator, display, meaning):
    assert describe(indicator, inputs()) == (display, meaning)


def test_language_barrier_follows_the_english_band():
    assert describe("C1", inputs(english_band="very_high"))[1].endswith(
        "English proficiency there is Very high (EF English Proficiency Index), so the language "
        "barrier is low."
    )
    assert describe("C1", inputs(english_band="moderate"))[1].endswith("barrier is moderate.")


def test_company_working_in_the_local_language():
    spanish = replace(PROFILE, supported_languages=["en", "es"])
    assert describe("C1", inputs(spanish)) == (
        "Local language",
        "The company works in Spanish, a main business language of Colombia, so there is no "
        "language barrier.",
    )


def test_company_using_whatsapp():
    whatsapp = replace(PROFILE, channels=["sms", "whatsapp"])
    assert describe("C2", inputs(whatsapp)) == (
        "Company uses WhatsApp",
        "The company already reaches customers on WhatsApp, so its channels fit local habits.",
    )


def test_opposite_cases_read_correctly():
    assert describe("A1", inputs(tax_treaty_with_home=True))[1] == (
        "There is an income tax treaty between Colombia and the USA."
    )
    assert describe("A2", inputs(trade_agreement_with_home=False))[1] == (
        "There is no trade agreement in force between Colombia and the USA."
    )
    assert describe("G1", inputs(max_hour_diff_home=9.0)) == (
        "9 h difference",
        "Colombia's working day is up to 9 h apart from the company's time zone "
        "(America/Los_Angeles), so 0 of 8 working hours overlap.",
    )
