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


class Dimension(BaseModel):
    id: DimensionId
    name: str
    score: float | None
    available: int
    total: int


class Scorecard(BaseModel):
    country: CountryRef
    home: str
    indicators: list[IndicatorResult]
    dimensions: list[Dimension]
    accessibility: float | None
    accessibility_reason: str | None


DIMENSION_NAMES: dict[DimensionId, str] = {
    "C": "Cultural", "A": "Administrative", "G": "Geographic", "E": "Economic",
}


def _source(record: EvidenceRecord) -> Source:
    return Source(name=record.source_name, url=record.source_url, year=record.year)


def _evaluate(definition: IndicatorDef, inputs: Inputs) -> IndicatorResult:
    score = definition.score(inputs)
    records = [inputs.country[m] for m in definition.metrics if m in inputs.country]
    if definition.uses_home:
        records += [inputs.home[m] for m in definition.metrics if m in inputs.home]
    if definition.raw is not None:
        raw = definition.raw(inputs)
    else:
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


def aggregate(
    results: list[IndicatorResult],
) -> tuple[list[Dimension], float | None, str | None]:
    """Dimension % = mean of available scores; Accessibility % = mean of the 4 dimensions,
    only when every dimension has at least one indicator."""
    dimensions = []
    for dim_id, name in DIMENSION_NAMES.items():
        members = [r for r in results if r.dimension == dim_id]
        scores = [r.score for r in members if r.score is not None]
        dimensions.append(
            Dimension(
                id=dim_id, name=name, score=sum(scores) / len(scores) if scores else None,
                available=len(scores), total=len(members),
            )
        )
    empty = [d.name for d in dimensions if d.score is None]
    if empty:
        return dimensions, None, "Not enough data: no indicators for " + ", ".join(empty)
    return dimensions, sum(d.score for d in dimensions) / len(dimensions), None


def build_scorecard(inputs: Inputs) -> Scorecard:
    indicators = [_evaluate(definition, inputs) for definition in INDICATORS]
    dimensions, accessibility, reason = aggregate(indicators)
    return Scorecard(
        country=CountryRef(iso3=inputs.country_cfg.iso3, name=inputs.country_cfg.name),
        home=inputs.profile.home_country,
        indicators=indicators,
        dimensions=dimensions,
        accessibility=accessibility,
        accessibility_reason=reason,
    )
