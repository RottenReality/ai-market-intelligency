"""Hofstede 6-D culture scores and the Kogut-Singh cultural distance index.

KS_j = (1/n) * sum_i ((I_ij - I_ih)^2 / V_i), over the n dimensions both countries have,
where V_i is the variance of dimension i across all countries in the dataset
(Kogut & Singh, 1988).
"""

import csv
from pathlib import Path
from statistics import pvariance

DIMENSIONS = ("pdi", "idv", "mas", "uai", "lto", "ivr")
HOFSTEDE_SOURCE_URL = "https://geerthofstede.com/research-and-vsm/dimension-data-matrix/"

Scores = dict[str, float | None]


def load_hofstede(path: Path) -> dict[str, Scores]:
    rows = csv.DictReader(path.read_text(encoding="utf-8").splitlines())
    return {
        row["iso3"]: {dim: float(row[dim]) if row[dim] else None for dim in DIMENSIONS}
        for row in rows
    }


def dimension_variances(data: dict[str, Scores]) -> dict[str, float]:
    variances = {}
    for dim in {d for scores in data.values() for d in scores}:
        values = [scores[dim] for scores in data.values() if scores.get(dim) is not None]
        if len(values) >= 2:
            variances[dim] = pvariance(values)
    return variances


def kogut_singh(country: Scores, home: Scores, variances: dict[str, float]) -> float | None:
    terms = [
        (country[dim] - home[dim]) ** 2 / variances[dim]
        for dim in variances
        if country.get(dim) is not None and home.get(dim) is not None and variances[dim] > 0
    ]
    return sum(terms) / len(terms) if terms else None
