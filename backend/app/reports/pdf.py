"""PDF report: cover, comparison page (several countries), one section per country,
methodology note. AI text comes from saved analyses only."""

import struct
from datetime import datetime
from io import BytesIO
from pathlib import Path

import matplotlib
from fpdf import FPDF
from fpdf.fonts import FontFace

from app.analysis.service import ComparisonInsight, CountryAnalysis
from app.profile.company import CompanyProfile
from app.reports.charts import (
    comparison_heatmap_png,
    dimension_bars_png,
    indicator_heatmap_png,
    radar_png,
    ranking_png,
)
from app.scoring.display import format_raw, format_score
from app.scoring.scorecard import Scorecard

# DejaVu Sans ships with matplotlib and covers any text an explanation may contain
# (dashes, curly quotes, accents); the PDF core fonts only cover Latin-1.
_FONTS = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
FONT = "DejaVu"
BLUE = (31, 95, 173)
MUTED = (82, 81, 78)
AMBER = (180, 83, 9)
AI_FILL = (238, 244, 252)  # #eef4fc: light blue marks AI-written text
HEADER = FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=BLUE)
MAX_RADAR_SERIES = 3

METHODOLOGY = (
    "Market accessibility is measured with Ghemawat's CAGE distance framework: Cultural, "
    "Administrative, Geographic and Economic distance from the company's home country. Each of "
    "the 12 indicators is scored from 0 (very hard) to 100 (very accessible). A dimension is the "
    "average of its available indicators, and market accessibility is the average of the four "
    "dimensions with equal weights. Missing indicators are left out of the averages, never "
    "counted as zero."
)


class _Report(FPDF):
    def footer(self) -> None:
        self.set_y(-12)
        self.set_font(FONT, size=8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, f"CAGE Market Accessibility Report · page {self.page_no()}", align="R")


def _new_pdf() -> _Report:
    pdf = _Report(format="A4")
    pdf.add_font(FONT, "", str(_FONTS / "DejaVuSans.ttf"))
    pdf.add_font(FONT, "B", str(_FONTS / "DejaVuSans-Bold.ttf"))
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(auto=True, margin=18)
    return pdf


def _heading(pdf: FPDF, text: str, size: int = 15) -> None:
    pdf.set_font(FONT, "B", size)
    pdf.set_text_color(*BLUE)
    pdf.multi_cell(0, size * 0.55, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def _paragraph(pdf: FPDF, text: str, size: int = 10, color=(0, 0, 0)) -> None:
    pdf.set_font(FONT, "", size)
    pdf.set_text_color(*color)
    pdf.multi_cell(0, size * 0.5, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def _keep_space(pdf: FPDF, height: float) -> None:
    """Start a new page unless `height` mm still fit, so headings never end up orphaned."""
    if pdf.get_y() + height > pdf.page_break_trigger:
        pdf.add_page()


def _figure(pdf: FPDF, title: str | None, png: bytes, width: float) -> None:
    """Optional heading plus chart, moved to the next page together if they do not fit."""
    px_w, px_h = struct.unpack(">II", png[16:24])  # PNG IHDR width and height
    _keep_space(pdf, width * px_h / px_w + (12 if title else 2))
    if title:
        _heading(pdf, title, size=12)
    pdf.image(BytesIO(png), w=width)


def _ranked(cards: list[Scorecard]) -> list[Scorecard]:
    return sorted(cards, key=lambda c: (c.accessibility is None, -(c.accessibility or 0)))


def _ranks(cards: list[Scorecard]) -> dict[str, int]:
    """Rank among the countries in this report that have a score (best = 1)."""
    scored = [c for c in _ranked(cards) if c.accessibility is not None]
    return {c.country.iso3: rank for rank, c in enumerate(scored, start=1)}


def _best_per_dimension(cards: list[Scorecard]) -> dict[str, tuple[str, float]]:
    best: dict[str, tuple[str, float]] = {}
    for card in cards:
        for d in card.dimensions:
            if d.score is not None and (d.name not in best or d.score > best[d.name][1]):
                best[d.name] = (card.country.name, d.score)
    return best


def _accessibility_line(card: Scorecard, rank: int | None, total: int) -> str:
    if card.accessibility is None:
        return f"Market accessibility: not calculated. {card.accessibility_reason}"
    line = f"Market accessibility: {format_score(card.accessibility)}%"
    return line if rank is None or total < 2 else f"{line} · rank {rank} of {total}"


def _percent(score: float | None) -> str:
    return "not calculated" if score is None else f"{format_score(score)}%"


def _cover(pdf: FPDF, cards: list[Scorecard], profile: CompanyProfile, generated: datetime) -> None:
    pdf.add_page()
    pdf.ln(50)
    _heading(pdf, "CAGE Market Accessibility Report", size=24)
    _paragraph(pdf, f"Prepared for {profile.name} (home country: {profile.home_country})", 12)
    _paragraph(pdf, "Countries: " + ", ".join(c.country.name for c in cards), 12)
    _paragraph(pdf, f"Generated on {generated:%Y-%m-%d}", 11, MUTED)


def _ai_box(pdf: FPDF, title: str, lines: list[str]) -> None:
    """A light-blue block of AI-written text; it flows across pages when long."""
    _keep_space(pdf, 30)
    pdf.set_fill_color(*AI_FILL)
    pdf.set_font(FONT, "B", 11)
    pdf.set_text_color(*BLUE)
    pdf.multi_cell(0, 6, title, fill=True, padding=(3, 4, 1, 4), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(FONT, "", 10)
    for i, line in enumerate(lines):
        bottom = 3 if i == len(lines) - 1 else 1
        pdf.multi_cell(0, 5, line, fill=True, padding=(1, 4, bottom, 4), align="L",
                       new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)


def _attribution(pdf: FPDF, meta: CountryAnalysis | ComparisonInsight) -> None:
    _paragraph(pdf, f"AI analysis written by {meta.provider_label} ({meta.model}) on "
                    f"{meta.created_at[:10]}. Numbers checked against the data.", 8, MUTED)
    if meta.flagged:
        _paragraph(pdf, "Some numbers could not be verified; review before use.", 9, AMBER)
    if meta.outdated:
        _paragraph(pdf, "Written before the latest data or company change.", 9, AMBER)


def _comparison(pdf: FPDF, cards: list[Scorecard], insight: ComparisonInsight | None) -> None:
    ranked = _ranked(cards)
    pdf.add_page()
    _heading(pdf, "Ranking")
    pdf.image(BytesIO(ranking_png([(c.country.name, c.accessibility) for c in ranked])), w=150)
    pdf.ln(2)
    pdf.set_font(FONT, "", 9)
    with pdf.table(col_widths=(7, 30, 25, 20, 29, 24, 21), headings_style=HEADER,
                   text_align="LEFT") as table:
        table.row(["#", "Country", "Accessibility", "Cultural", "Administrative", "Geographic",
                   "Economic"])
        for rank, card in enumerate(ranked, start=1):
            access = "-" if card.accessibility is None else f"{format_score(card.accessibility)}%"
            table.row([str(rank), card.country.name, access,
                       *(format_score(d.score) for d in card.dimensions)])
    pdf.ln(4)
    _figure(pdf, "Scores by dimension", comparison_heatmap_png(cards), 165)
    with_score = [c for c in ranked if c.accessibility is not None][:MAX_RADAR_SERIES]
    if with_score:
        pdf.ln(4)
        series = [(c.country.name, c.dimensions) for c in with_score]
        _figure(pdf, "CAGE profile (top 3)", radar_png(series), 110)
    if insight is None:
        return
    pdf.ln(4)
    _keep_space(pdf, 40)
    _heading(pdf, "Comparison insight", size=12)
    _ai_box(pdf, "Summary", [insight.summary])
    _ai_box(pdf, "Why they rank this way", [
        f"{entry.rank}. {entry.name} ({_percent(entry.accessibility)}): {entry.explanation}"
        for entry in insight.ranking
    ])
    _ai_box(pdf, "Key differences", [f"• {item}" for item in insight.key_differences])
    _attribution(pdf, insight)


def _country(
    pdf: FPDF, card: Scorecard, analysis: CountryAnalysis | None, rank: int | None, total: int,
    best: dict[str, tuple[str, float]] | None,
) -> None:
    pdf.add_page()
    _heading(pdf, card.country.name, size=18)
    _paragraph(pdf, _accessibility_line(card, rank, total), 13)
    pdf.image(BytesIO(radar_png([(card.country.name, card.dimensions)])), w=85)
    pdf.ln(2)

    if analysis is None:
        _paragraph(pdf, "AI analysis not generated yet", 10, MUTED)
    else:
        _ai_box(pdf, "Executive summary", [analysis.content.executive_summary])

    _figure(pdf, "Dimension scores", dimension_bars_png(card.dimensions, best), 150)
    pdf.ln(2)
    _figure(pdf, "Indicator heat map", indicator_heatmap_png(card.indicators), 120)
    _paragraph(pdf, "Red: barrier (below 40) · amber: 40 to 69 · green: strength (70 and above) "
                    "· grey: no data.", 8, MUTED)

    if analysis is not None:
        content = analysis.content
        dims = content.dimensions
        _ai_box(pdf, "Why each dimension scored this way", [
            f"Cultural: {dims.Cultural}", f"Administrative: {dims.Administrative}",
            f"Geographic: {dims.Geographic}", f"Economic: {dims.Economic}",
        ])
        _ai_box(pdf, "Barriers", [f"• {item}" for item in content.barriers])
        _ai_box(pdf, "Opportunities", [f"• {item}" for item in content.opportunities])
        _ai_box(pdf, "Recommendation and next steps", [content.recommendation])
        _attribution(pdf, analysis)
    pdf.ln(2)

    _keep_space(pdf, 40)
    _heading(pdf, "Indicators", size=12)
    pdf.set_font(FONT, "", 8)
    with pdf.table(col_widths=(10, 52, 22, 14, 76), headings_style=HEADER,
                   text_align="LEFT") as table:
        table.row(["ID", "Indicator", "Value", "Score", "Source"])
        for i in card.indicators:
            source = "; ".join(f"{s.name} ({s.year})" if s.year else s.name for s in i.sources)
            table.row([i.id, i.name, format_raw(i.raw, i.unit), format_score(i.score),
                       source or "-"])


def _methodology(pdf: FPDF) -> None:
    pdf.add_page()
    _heading(pdf, "Methodology")
    _paragraph(pdf, METHODOLOGY)
    _paragraph(pdf, "Sources: World Bank Indicators API and Worldwide Governance Indicators; "
                    "PwC Worldwide Tax Summaries; USTR; DataReportal; EF English Proficiency "
                    "Index; Hofstede 6-D dimension data (Kogut-Singh index); IANA time zone "
                    "database. Each indicator above lists its exact source and year.", 9, MUTED)


def build_report(
    scorecards: list[Scorecard],
    analyses: dict[str, CountryAnalysis | None],
    insight: ComparisonInsight | None,
    profile: CompanyProfile,
    generated_at: datetime,
) -> bytes:
    pdf = _new_pdf()
    _cover(pdf, scorecards, profile, generated_at)
    several = len(scorecards) > 1
    if several:
        _comparison(pdf, scorecards, insight)
    ranks = _ranks(scorecards)
    best = _best_per_dimension(scorecards) if several else None
    for card in scorecards:
        _country(pdf, card, analyses.get(card.country.iso3), ranks.get(card.country.iso3),
                 len(scorecards), best)
    _methodology(pdf)
    return bytes(pdf.output())
