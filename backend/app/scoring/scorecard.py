from typing import Literal

from pydantic import BaseModel

from app.evidence.models import EvidenceRecord
from app.scoring.indicators import INDICATORS, DimensionId, IndicatorDef, Inputs


class Source(BaseModel):
    name: str
    url: str
    year: int | None


class IndicatorResult(BaseModel):
    id: str
    dimension: DimensionId
    name: str
    status: Literal["ok", "missing"]
    score: float | None
    raw: float | bool | str | None
    unit: str
    sources: list[Source]


class CountryRef(BaseModel):
    iso3: str
    name: str


class Scorecard(BaseModel):
    country: CountryRef
    home: str
    indicators: list[IndicatorResult]


def _source(record: EvidenceRecord) -> Source:
    return Source(name=record.source_name, url=record.source_url, year=record.year)


def _evaluate(definition: IndicatorDef, inputs: Inputs) -> IndicatorResult:
    score = definition.score(inputs)
    records = [inputs.country[m] for m in definition.metrics if m in inputs.country]
    if definition.uses_home:
        records += [inputs.home[m] for m in definition.metrics if m in inputs.home]
    raw = inputs.value(definition.raw_metric) if definition.raw_metric else None
    return IndicatorResult(
        id=definition.id,
        dimension=definition.dimension,
        name=definition.name,
        status="missing" if score is None else "ok",
        score=score,
        raw=None if score is None else raw,
        unit=definition.unit,
        sources=[_source(r) for r in records],
    )


def build_scorecard(inputs: Inputs) -> Scorecard:
    return Scorecard(
        country=CountryRef(iso3=inputs.country_cfg.iso3, name=inputs.country_cfg.name),
        home=inputs.profile.home_country,
        indicators=[_evaluate(definition, inputs) for definition in INDICATORS],
    )
