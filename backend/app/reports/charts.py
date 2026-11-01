"""Static charts for the PDF report (matplotlib, rendered to PNG in memory)."""

from io import BytesIO

import matplotlib

matplotlib.use("Agg")  # no display needed on servers

import matplotlib.pyplot as plt
import numpy as np

from app.scoring.scorecard import Dimension, IndicatorResult, Scorecard

SERIES_COLORS = ("#2a78d6", "#eb6834", "#1baf7a")  # same palette as the web app
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"


def _png(fig) -> bytes:
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buffer.getvalue()


def radar_png(series: list[tuple[str, list[Dimension]]]) -> bytes:
    """One polygon per country (max 3), dimensions in C, A, G, E order; missing = 0."""
    names = [d.name for d in series[0][1]]
    angles = np.linspace(0, 2 * np.pi, len(names), endpoint=False).tolist()
    fig = plt.figure(figsize=(4.2, 3.6))
    ax = plt.subplot(111, polar=True)
    ax.set_theta_offset(np.pi / 2)  # first dimension (Cultural) at the top, like the web app
    ax.set_theta_direction(-1)  # clockwise
    for (label, dimensions), color in zip(series, SERIES_COLORS, strict=False):
        values = [d.score or 0 for d in dimensions]
        ax.plot(angles + angles[:1], values + values[:1], color=color, lw=2, label=label)
        ax.fill(angles + angles[:1], values + values[:1], color=color, alpha=0.12)
    ax.set_xticks(angles)
    ax.set_xticklabels(names, fontsize=9, color=INK)
    ax.tick_params(axis="x", pad=8)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels([])
    ax.grid(color=GRID)
    ax.spines["polar"].set_color(GRID)
    if len(series) > 1:
        ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.12), frameon=False, fontsize=8)
    return _png(fig)


def ranking_png(rows: list[tuple[str, float | None]]) -> bytes:
    """Horizontal bars, best first. Countries without a score are listed as 'no score'."""
    labels = [name for name, _ in rows]
    values = [value or 0 for _, value in rows]
    fig, ax = plt.subplots(figsize=(6, 0.5 * len(rows) + 0.8))
    y = np.arange(len(rows))[::-1]
    ax.barh(y, values, color=SERIES_COLORS[0], height=0.55)
    for yi, (_, value) in zip(y, rows, strict=True):
        text = "no score" if value is None else f"{round(value)}%"
        ax.text((value or 0) + 1.5, yi, text, va="center", fontsize=9, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9, color=INK)
    ax.set_xlim(0, 100)
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0, colors=MUTED)
    return _png(fig)


# Score bands for the heat maps. The score is always printed on the cell, so colour is never
# the only way to read it.
SCORE_BANDS = {
    "barrier": "#f4a29b",  # below 40
    "middle": "#f6d58a",  # 40-69
    "strength": "#8fd1a6",  # 70 and above
    "missing": "#d9d9d9",
}
DIMENSION_ORDER = ("C", "A", "G", "E")
DIMENSION_LABELS = {"C": "Cultural", "A": "Administrative", "G": "Geographic", "E": "Economic"}


def band_color(score: float | None) -> str:
    if score is None:
        return SCORE_BANDS["missing"]
    if score < 40:
        return SCORE_BANDS["barrier"]
    if score < 70:
        return SCORE_BANDS["middle"]
    return SCORE_BANDS["strength"]


def _cell(ax, x: float, y: float, color: str, lines: list[str]) -> None:
    ax.add_patch(plt.Rectangle((x, y), 0.94, 0.88, color=color, ec="white", lw=1.5))
    ax.text(x + 0.47, y + 0.44, "\n".join(lines), ha="center", va="center", fontsize=9,
            color=INK, linespacing=1.3)


def _score_text(score: float | None) -> str:
    return "n/a" if score is None else str(int(score + 0.5))


def indicator_heatmap_png(indicators: list[IndicatorResult]) -> bytes:
    """4 rows (C, A, G, E) x 3 indicators, each cell showing its ID and score."""
    rows = {dim: [i for i in indicators if i.dimension == dim] for dim in DIMENSION_ORDER}
    columns = max((len(items) for items in rows.values()), default=1)
    fig, ax = plt.subplots(figsize=(1.25 * columns + 1.6, 3.0))
    for r, dim in enumerate(DIMENSION_ORDER):
        y = len(DIMENSION_ORDER) - 1 - r
        ax.text(-0.08, y + 0.44, DIMENSION_LABELS[dim], ha="right", va="center", fontsize=9,
                color=INK)
        for c, indicator in enumerate(rows[dim]):
            _cell(ax, c, y, band_color(indicator.score),
                  [indicator.id, _score_text(indicator.score)])
    ax.set_xlim(-1.6, columns)
    ax.set_ylim(0, len(DIMENSION_ORDER))
    ax.axis("off")
    return _png(fig)


def dimension_bars_png(
    dimensions: list[Dimension], best: dict[str, tuple[str, float]] | None
) -> bytes:
    """One bar per dimension with its score; optionally 'best: <country> <score>' beside it."""
    fig, ax = plt.subplots(figsize=(6.2, 2.4))
    y = np.arange(len(dimensions))[::-1]
    values = [d.score or 0 for d in dimensions]
    ax.barh(y, values, color=SERIES_COLORS[0], height=0.55)
    for yi, dim in zip(y, dimensions, strict=True):
        label = _score_text(dim.score)
        if best and dim.name in best:
            name, score = best[dim.name]
            label += f"   (best: {name} {_score_text(score)})"
        ax.text((dim.score or 0) + 1.5, yi, label, va="center", fontsize=9, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([d.name for d in dimensions], fontsize=9, color=INK)
    ax.set_xlim(0, 135 if best else 110)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0, colors=MUTED)
    return _png(fig)


def comparison_heatmap_png(scorecards: list[Scorecard]) -> bytes:
    """Countries (rows, best first) x dimensions plus the overall score, values printed."""
    ordered = sorted(scorecards, key=lambda c: (c.accessibility is None, -(c.accessibility or 0)))
    headers = [*(DIMENSION_LABELS[d] for d in DIMENSION_ORDER), "Accessibility"]
    fig, ax = plt.subplots(figsize=(7.2, 0.55 * len(ordered) + 0.9))
    for r, card in enumerate(ordered):
        y = len(ordered) - 1 - r
        ax.text(-0.08, y + 0.44, card.country.name, ha="right", va="center", fontsize=9,
                color=INK)
        scores = {d.id: d.score for d in card.dimensions}
        for c, dim in enumerate(DIMENSION_ORDER):
            _cell(ax, c, y, band_color(scores.get(dim)), [_score_text(scores.get(dim))])
        _cell(ax, len(DIMENSION_ORDER), y, band_color(card.accessibility),
              [_score_text(card.accessibility) + ("" if card.accessibility is None else "%")])
    for c, header in enumerate(headers):
        ax.text(c + 0.47, len(ordered) + 0.15, header, ha="center", va="bottom", fontsize=8.5,
                color=MUTED)
    ax.set_xlim(-1.4, len(headers))
    ax.set_ylim(0, len(ordered) + 0.7)
    ax.axis("off")
    return _png(fig)
