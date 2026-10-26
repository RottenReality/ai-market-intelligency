"""PDF report: cover, optional ranking page, one section per country, methodology note."""

from datetime import datetime
from io import BytesIO
from pathlib import Path

import matplotlib
from fpdf import FPDF
from fpdf.fonts import FontFace

from app.explanation.cache import Explanation
from app.profile.company import CompanyProfile
from app.reports.charts import radar_png, ranking_png
from app.scoring.display import format_raw, format_score
from app.scoring.scorecard import Scorecard

# DejaVu Sans ships with matplotlib and covers any text an explanation may contain
# (dashes, curly quotes, accents); the PDF core fonts only cover Latin-1.
_FONTS = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
FONT = "DejaVu"
BLUE = (31, 95, 173)
MUTED = (82, 81, 78)
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


def _accessibility_line(card: Scorecard) -> str:
    if card.accessibility is None:
        return f"Market accessibility: not calculated. {card.accessibility_reason}"
    return f"Market accessibility: {format_score(card.accessibility)}%"


def _cover(pdf: FPDF, cards: list[Scorecard], profile: CompanyProfile, generated: datetime) -> None:
    pdf.add_page()
    pdf.ln(50)
    _heading(pdf, "CAGE Market Accessibility Report", size=24)
    _paragraph(pdf, f"Prepared for {profile.name} (home country: {profile.home_country})", 12)
    _paragraph(pdf, "Countries: " + ", ".join(c.country.name for c in cards), 12)
    _paragraph(pdf, f"Generated on {generated:%Y-%m-%d}", 11, MUTED)


def _ranking(pdf: FPDF, cards: list[Scorecard]) -> None:
    ranked = sorted(cards, key=lambda c: (c.accessibility is None, -(c.accessibility or 0)))
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
    with_score = [c for c in ranked if c.accessibility is not None][:MAX_RADAR_SERIES]
    if with_score:
        pdf.ln(4)
        _heading(pdf, "CAGE profile (top 3)", size=12)
        series = [(c.country.name, c.dimensions) for c in with_score]
        pdf.image(BytesIO(radar_png(series)), w=110)


def _country(pdf: FPDF, card: Scorecard, explanation: Explanation | None) -> None:
    pdf.add_page()
    _heading(pdf, card.country.name, size=18)
    _paragraph(pdf, _accessibility_line(card), 13)

    pdf.image(BytesIO(radar_png([(card.country.name, card.dimensions)])), w=90)
    pdf.set_font(FONT, "", 9)
    with pdf.table(col_widths=(50, 25, 35), width=110, headings_style=HEADER,
                   text_align="LEFT") as table:
        table.row(["Dimension", "Score", "Indicators"])
        for d in card.dimensions:
            table.row([d.name, format_score(d.score), f"{d.available}/{d.total}"])
    pdf.ln(4)

    _heading(pdf, "Indicators", size=12)
    pdf.set_font(FONT, "", 8)
    with pdf.table(col_widths=(10, 52, 22, 14, 76), headings_style=HEADER,
                   text_align="LEFT") as table:
        table.row(["ID", "Indicator", "Value", "Score", "Source"])
        for i in card.indicators:
            source = "; ".join(f"{s.name} ({s.year})" if s.year else s.name for s in i.sources)
            table.row([i.id, i.name, format_raw(i.raw, i.unit), format_score(i.score),
                       source or "-"])
    pdf.ln(4)

    _heading(pdf, "AI explanation", size=12)
    if explanation is None:
        _paragraph(pdf, "Explanation not generated yet.", 10, MUTED)
        return
    if explanation.flagged:
        _paragraph(pdf, "Note: some numbers in this explanation could not be verified against "
                        "the data. Review before using.", 9, (180, 83, 9))
    _paragraph(pdf, explanation.text, 10)
    _paragraph(pdf, f"AI-generated on {explanation.created_at[:10]} from the scores above.", 8,
               MUTED)


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
    explanations: dict[str, Explanation | None],
    profile: CompanyProfile,
    generated_at: datetime,
) -> bytes:
    pdf = _new_pdf()
    _cover(pdf, scorecards, profile, generated_at)
    if len(scorecards) > 1:
        _ranking(pdf, scorecards)
    for card in scorecards:
        _country(pdf, card, explanations.get(card.country.iso3))
    _methodology(pdf)
    return bytes(pdf.output())
