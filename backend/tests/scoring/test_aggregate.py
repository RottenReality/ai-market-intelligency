import pytest

from app.scoring.scorecard import IndicatorResult, aggregate


def result(indicator_id: str, score: float | None) -> IndicatorResult:
    return IndicatorResult(
        id=indicator_id, dimension=indicator_id[0], name=indicator_id,
        status="missing" if score is None else "ok", score=score, raw=None, unit="-", sources=[],
    )


# The preliminary Colombia values from the proposal (Cultural not collected yet).
COLOMBIA_PRELIMINARY = [
    result("C1", None), result("C2", None), result("C3", None),
    result("A1", 0), result("A2", 100), result("A3", 46.0529),
    result("G1", 62.5), result("G2", 79.345), result("G3", 70.4),
    result("E1", 24.863), result("E2", 100), result("E3", 74.3),
]


def test_colombia_preliminary_dimensions():
    dimensions, accessibility, reason = aggregate(COLOMBIA_PRELIMINARY)
    by_id = {d.id: d for d in dimensions}
    assert [d.id for d in dimensions] == ["C", "A", "G", "E"]
    assert [d.name for d in dimensions] == ["Cultural", "Administrative", "Geographic", "Economic"]
    assert by_id["A"].score == pytest.approx(48.68, abs=0.01)
    assert by_id["G"].score == pytest.approx(70.75, abs=0.01)
    assert by_id["E"].score == pytest.approx(66.39, abs=0.01)
    assert by_id["C"].score is None
    assert by_id["C"].available == 0 and by_id["C"].total == 3
    assert accessibility is None
    assert reason == "Not enough data: no indicators for Cultural"


def test_accessibility_is_mean_of_four_dimensions():
    results = [
        result("C1", 50), result("A1", 70), result("G1", 80), result("E1", 60),
    ]
    _, accessibility, reason = aggregate(results)
    assert accessibility == pytest.approx(65)
    assert reason is None


def test_dimension_with_one_of_three_reports_available_1():
    results = [result("C1", 40), result("C2", None), result("C3", None)]
    dimensions, _, _ = aggregate(results)
    cultural = dimensions[0]
    assert cultural.score == 40
    assert cultural.available == 1


def test_reason_lists_every_empty_dimension():
    _, accessibility, reason = aggregate([result("A1", 10), result("G1", 20)])
    assert accessibility is None
    assert reason == "Not enough data: no indicators for Cultural, Economic"
