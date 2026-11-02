import pytest

from app.reports.charts import (
    SCORE_BANDS,
    band_color,
    comparison_heatmap_png,
    dimension_bars_png,
    indicator_heatmap_png,
)
from tests.analysis.fixtures import FULL, colombia_scorecard, scorecard_for
from tests.scoring.evidence_factory import COLOMBIA

PNG = b"\x89PNG"


@pytest.mark.parametrize(
    ("score", "band"),
    [(0, "barrier"), (39.9, "barrier"), (40, "middle"), (69.9, "middle"), (70, "strength"),
     (100, "strength"), (None, "missing")],
)
def test_band_color_boundaries(score, band):
    assert band_color(score) == SCORE_BANDS[band]


def test_score_band_colours():
    assert SCORE_BANDS == {
        "barrier": "#f4a29b", "middle": "#f6d58a", "strength": "#8fd1a6", "missing": "#d9d9d9",
    }


def test_indicator_heatmap_is_png_with_and_without_missing_values():
    assert indicator_heatmap_png(colombia_scorecard().indicators).startswith(PNG)
    sparse = scorecard_for("COL", "Colombia", COLOMBIA)  # cultural indicators missing
    assert indicator_heatmap_png(sparse.indicators).startswith(PNG)


def test_dimension_bars_with_and_without_best():
    dims = colombia_scorecard().dimensions
    assert dimension_bars_png(dims, None).startswith(PNG)
    best = {"Cultural": ("Spain", 61.0), "Administrative": ("Chile", 88.0)}
    assert dimension_bars_png(dims, best).startswith(PNG)


def test_comparison_heatmap_is_png():
    cards = [colombia_scorecard(), scorecard_for("MEX", "Mexico", FULL)]
    assert comparison_heatmap_png(cards).startswith(PNG)
