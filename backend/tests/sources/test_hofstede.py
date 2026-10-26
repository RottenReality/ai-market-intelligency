from pathlib import Path

import pytest

from app.sources.hofstede import dimension_variances, kogut_singh, load_hofstede

# Hand-computed example. Population variances: pdi = 800/3, idv = 800.
# KS(B vs A) = ((60-40)^2 / (800/3) + (30-90)^2 / 800) / 2 = (1.5 + 4.5) / 2 = 3.0
DATASET = {
    "A": {"pdi": 40.0, "idv": 90.0},
    "B": {"pdi": 60.0, "idv": 30.0},
    "C": {"pdi": 80.0, "idv": 30.0},
}


def test_dimension_variances_are_population_variances():
    variances = dimension_variances(DATASET)
    assert variances["pdi"] == pytest.approx(800 / 3)
    assert variances["idv"] == pytest.approx(800)


def test_kogut_singh_hand_computed():
    variances = dimension_variances(DATASET)
    assert kogut_singh(DATASET["B"], DATASET["A"], variances) == pytest.approx(3.0)


def test_kogut_singh_skips_dimensions_missing_on_either_side():
    variances = dimension_variances(DATASET)
    country = {"pdi": 60.0, "idv": None}
    assert kogut_singh(country, DATASET["A"], variances) == pytest.approx(1.5)


def test_kogut_singh_none_when_no_common_dimension():
    assert kogut_singh({"pdi": None}, {"pdi": 40.0}, {"pdi": 10.0}) is None


def test_load_hofstede_reads_repository_file_with_blanks_as_none():
    data = load_hofstede(Path("data/hofstede.csv"))
    assert data["COL"] == {"pdi": 67, "idv": 13, "mas": 64, "uai": 80, "lto": 13, "ivr": 83}
    assert data["ALB"]["pdi"] is None  # Albania only has LTO and IVR scores
    assert data["ALB"]["lto"] == 61
