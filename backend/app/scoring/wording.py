"""Plain-language wording for each indicator: a short value for tables and a one-sentence
meaning that says what the number is, its scale and its direction. The app, the PDF and the AI
all read the same text, so nobody has to guess what a bare "Low" or "3 h" means."""

from collections.abc import Callable

from app.scoring import rules
from app.scoring.display import format_raw
from app.scoring.indicators import Inputs

LANGUAGE_NAMES = {
    "en": "English", "es": "Spanish", "pt": "Portuguese", "fr": "French", "de": "German",
    "it": "Italian",
}
# How hard English-only service is, given the country's English level (EF EPI band).
BARRIER_BY_BAND = {
    "very_high": "low", "high": "low", "moderate": "moderate", "low": "high", "very_low": "high",
}
CHANNEL_NAMES = {"sms": "SMS", "email": "email", "whatsapp": "WhatsApp"}

Wording = tuple[str, str]


# Home countries read better with an article ("the USA"); others are shown by their code.
HOME_NAMES = {"USA": "the USA", "GBR": "the UK"}


def _home(i: Inputs) -> str:
    return HOME_NAMES.get(i.profile.home_country, i.profile.home_country)


def _language(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)


def _and(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _c1(i: Inputs) -> Wording:
    country = i.country_cfg.name
    shared = [c for c in i.country_cfg.languages if c in i.profile.supported_languages]
    if shared:
        return ("Local language",
                (f"The company works in {_language(shared[0])}, a main business language of "
                f"{country}, so there is no language barrier."))
    band = str(i.value("english_band"))
    local = _and([_language(c) for c in i.country_cfg.languages])
    return (f"English: {format_raw(band, 'band')}",
            (f"{country}'s main business language is {local}, which the company does not work "
            f"in. English proficiency there is {format_raw(band, 'band')} (EF English Proficiency "
            f"Index), so the language barrier is {BARRIER_BY_BAND.get(band, 'unclear')}."))


def _c2(i: Inputs) -> Wording:
    if "whatsapp" in i.profile.channels:
        return ("Company uses WhatsApp",
                ("The company already reaches customers on WhatsApp, so its channels fit local "
                "habits."))
    pct = format_raw(i.value("whatsapp_pct"), "%")
    channels = _and([CHANNEL_NAMES.get(c, c) for c in i.profile.channels])
    return (f"{pct} use WhatsApp",
            (f"{pct} of internet users in {i.country_cfg.name} say they use WhatsApp. The company "
            f"reaches customers only by {channels}, so its channels fit less where WhatsApp is "
            "this common. This shows how common WhatsApp is, not that people stopped using SMS "
            "or email."))


def _c3(i: Inputs) -> Wording:
    value = format_raw(i.value("kogut_singh"), "index")
    return (value,
            (f"Cultural distance between {i.country_cfg.name} and {_home(i)} "
            f"(Kogut-Singh index on Hofstede's dimensions) is {value}, where 0 means the same "
            "culture and 4 or more means very distant."))


def _agreement(metric: str, article: str, kind: str) -> Callable[[Inputs], Wording]:
    def wording(i: Inputs) -> Wording:
        exists = bool(i.value(metric))
        subject = f"{article} {kind}" if exists else f"no {kind}"
        return (format_raw(exists, "bool"),
                f"There is {subject} between {i.country_cfg.name} and {_home(i)}.")
    return wording


def _a3(i: Inputs) -> Wording:
    value = format_raw(i.value("regulatory_quality"), "index")
    low, high = rules.WGI_RANGE
    return (value,
            (f"The World Bank rates {i.country_cfg.name}'s regulatory quality at {value}, on a "
            f"scale from {low:g} (weak) to {high:g} (strong)."))


def _g1(i: Inputs) -> Wording:
    difference = float(i.value("max_hour_diff_home"))  # type: ignore[arg-type]
    overlap = max(0.0, rules.WORKDAY_HOURS - difference)
    return (f"{difference:g} h difference",
            (f"{i.country_cfg.name}'s working day is up to {difference:g} h apart from the "
            f"company's time zone ({i.profile.home_timezone}), so {overlap:g} of "
            f"{rules.WORKDAY_HOURS} working hours overlap."))


def _g2(i: Inputs) -> Wording:
    pct = format_raw(i.value("internet_pct"), "%")
    return pct, f"{pct} of the population of {i.country_cfg.name} uses the internet."


def _g3(i: Inputs) -> Wording:
    pct = format_raw(i.value("social_media_pct"), "%")
    return pct, f"Social media user identities in {i.country_cfg.name} equal {pct} of the population."


def _e1(i: Inputs) -> Wording:
    country, home = i.value("gni_ppp_per_capita"), i.home_value("gni_ppp_per_capita")
    value = format_raw(country, "USD")
    share = rules.income_vs_home(country, home)  # type: ignore[arg-type]
    return (value,
            (f"Income per person in {i.country_cfg.name} (GNI per capita, PPP) is {value}, which "
            f"is {round(share or 0)}% of {_home(i)}'s {format_raw(home, 'USD')}."))


def _e2(i: Inputs) -> Wording:
    value = format_raw(i.value("urban_population"), "people")
    threshold = f"{rules.MIN_URBAN_POPULATION / 1_000_000:g}M"
    return (value,
            (f"{value} people live in cities in {i.country_cfg.name}. The score counts "
            f"{threshold} or more as a large market."))


def _e3(i: Inputs) -> Wording:
    pct = format_raw(i.value("inflation_pct"), "%")
    return (pct,
            (f"Consumer prices in {i.country_cfg.name} rose {pct} in a year. Each point of "
            f"inflation lowers the score by {rules.INFLATION_PENALTY_PER_POINT}."))


WORDING: dict[str, Callable[[Inputs], Wording]] = {
    "C1": _c1, "C2": _c2, "C3": _c3,
    "A1": _agreement("tax_treaty_with_home", "an", "income tax treaty"),
    "A2": _agreement("trade_agreement_with_home", "a", "trade agreement in force"),
    "A3": _a3, "G1": _g1, "G2": _g2, "G3": _g3, "E1": _e1, "E2": _e2, "E3": _e3,
}


def describe(indicator_id: str, inputs: Inputs) -> Wording:
    """(short value, meaning) for an indicator that has data."""
    return WORDING[indicator_id](inputs)
