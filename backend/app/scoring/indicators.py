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


INDICATORS: list[IndicatorDef] = [
    IndicatorDef(
        "A3", "A", "Regulatory quality", "index",
        lambda i: rules.regulatory_quality(i.value("regulatory_quality")),
        "regulatory_quality", ("regulatory_quality",),
    ),
    IndicatorDef(
        "G2", "G", "Internet users", "%",
        lambda i: rules.percentage(i.value("internet_pct")),
        "internet_pct", ("internet_pct",),
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
