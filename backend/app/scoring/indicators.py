"""The CAGE indicators: which evidence each one reads and which rule scores it."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from app.evidence.models import EvidenceRecord, EvidenceValue
from app.profile.company import CompanyProfile
from app.profile.countries import Country
from app.scoring import rules

DimensionId = Literal["C", "A", "G", "E"]


@dataclass(frozen=True)
class Inputs:
    country: dict[str, EvidenceRecord]
    home: dict[str, EvidenceRecord]
    country_cfg: Country
    profile: CompanyProfile

    def value(self, metric: str) -> EvidenceValue | None:
        record = self.country.get(metric)
        return None if record is None else record.value

    def home_value(self, metric: str) -> EvidenceValue | None:
        record = self.home.get(metric)
        return None if record is None else record.value


@dataclass(frozen=True)
class IndicatorDef:
    id: str
    dimension: DimensionId
    name: str
    unit: str
    score: Callable[[Inputs], float | None]
    raw_metric: str | None  # the value shown to the user as "raw"
    metrics: tuple[str, ...]  # evidence used, listed as sources
    uses_home: bool = False
    # Overrides the raw value when the score does not come from raw_metric (e.g. C1 when the
    # company already works in a local language).
    raw: Callable[[Inputs], EvidenceValue | None] | None = None


def _speaks_local_language(i: Inputs) -> bool:
    return bool(set(i.country_cfg.languages) & set(i.profile.supported_languages))


def _language_raw(i: Inputs) -> EvidenceValue | None:
    return "local_language_supported" if _speaks_local_language(i) else i.value("english_band")


def _channel_raw(i: Inputs) -> EvidenceValue | None:
    return "company_uses_whatsapp" if "whatsapp" in i.profile.channels else i.value("whatsapp_pct")


INDICATORS: list[IndicatorDef] = [
    IndicatorDef(
        "C1", "C", "Language barrier", "band",
        lambda i: rules.language_barrier(
            i.country_cfg.languages, i.profile.supported_languages, i.value("english_band")
        ),
        "english_band", ("english_band",), raw=_language_raw,
    ),
    IndicatorDef(
        "C2", "C", "Channel fit (SMS/email vs WhatsApp)", "%",
        lambda i: rules.channel_fit(i.value("whatsapp_pct"), i.profile.channels),
        "whatsapp_pct", ("whatsapp_pct",), raw=_channel_raw,
    ),
    IndicatorDef(
        "C3", "C", "Cultural distance (Hofstede)", "index",
        lambda i: rules.cultural_distance(i.value("kogut_singh")),
        "kogut_singh", ("kogut_singh",),
    ),
    IndicatorDef(
        "A1", "A", "Tax treaty with home country", "bool",
        lambda i: rules.yes_no(i.value("tax_treaty_with_home")),
        "tax_treaty_with_home", ("tax_treaty_with_home",),
    ),
    IndicatorDef(
        "A2", "A", "Trade agreement with home country", "bool",
        lambda i: rules.yes_no(i.value("trade_agreement_with_home")),
        "trade_agreement_with_home", ("trade_agreement_with_home",),
    ),
    IndicatorDef(
        "A3", "A", "Regulatory quality", "index",
        lambda i: rules.regulatory_quality(i.value("regulatory_quality")),
        "regulatory_quality", ("regulatory_quality",),
    ),
    IndicatorDef(
        "G1", "G", "Working-hours overlap with home", "hours",
        lambda i: rules.hours_overlap(i.value("max_hour_diff_home")),
        "max_hour_diff_home", ("max_hour_diff_home",),
    ),
    IndicatorDef(
        "G2", "G", "Internet users", "%",
        lambda i: rules.percentage(i.value("internet_pct")),
        "internet_pct", ("internet_pct",),
    ),
    IndicatorDef(
        "G3", "G", "Social media users", "%",
        lambda i: rules.percentage(i.value("social_media_pct")),
        "social_media_pct", ("social_media_pct",),
    ),
    IndicatorDef(
        "E1", "E", "Income per person (PPP) vs home", "USD",
        lambda i: rules.income_vs_home(
            i.value("gni_ppp_per_capita"), i.home_value("gni_ppp_per_capita")
        ),
        "gni_ppp_per_capita", ("gni_ppp_per_capita",), uses_home=True,
    ),
    IndicatorDef(
        "E2", "E", "Market size (urban population)", "people",
        lambda i: rules.market_size(i.value("urban_population")),
        "urban_population", ("urban_population",),
    ),
    IndicatorDef(
        "E3", "E", "Inflation", "%",
        lambda i: rules.inflation(i.value("inflation_pct")),
        "inflation_pct", ("inflation_pct",),
    ),
]
