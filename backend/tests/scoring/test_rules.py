import pytest

from app.scoring import rules


@pytest.mark.parametrize(
    ("value", "expected"),
    [(-0.1973526, 46.05), (3.0, 100.0), (-3.0, 0.0), (0.0, 50.0)],
)
def test_regulatory_quality(value, expected):
    assert rules.regulatory_quality(value) == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize(("value", "expected"), [(79.345, 79.345), (120.0, 100.0), (-1.0, 0.0)])
def test_percentage(value, expected):
    assert rules.percentage(value) == pytest.approx(expected)


def test_income_vs_home():
    assert rules.income_vs_home(22250, 89490) == pytest.approx(24.86, abs=0.01)
    assert rules.income_vs_home(100000, 89490) == 100.0
    assert rules.income_vs_home(22250, None) is None
    assert rules.income_vs_home(22250, 0) is None


def test_market_size_threshold():
    assert rules.MIN_URBAN_POPULATION == 10_000_000
    assert rules.market_size(42_090_207) == 100.0
    assert rules.market_size(10_000_000) == 100.0
    assert rules.market_size(9_999_999) == 0.0


@pytest.mark.parametrize(("value", "expected"), [(5.14, 74.3), (0.0, 100.0), (25.0, 0.0), (-1.0, 100.0)])
def test_inflation(value, expected):
    assert rules.inflation(value) == pytest.approx(expected)


@pytest.mark.parametrize(
    "rule", [rules.regulatory_quality, rules.percentage, rules.market_size, rules.inflation]
)
def test_missing_input_gives_none(rule):
    assert rule(None) is None
