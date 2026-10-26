"""Static charts for the PDF report (matplotlib, rendered to PNG in memory)."""

from io import BytesIO

import matplotlib

matplotlib.use("Agg")  # no display needed on servers

import matplotlib.pyplot as plt
import numpy as np

from app.scoring.scorecard import Dimension

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
