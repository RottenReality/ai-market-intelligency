"""Load the hand-curated inputs (data/manual_inputs.csv) that no API provides.

The file is edited by non-developers, often in Excel. Spanish-locale Excel saves CSV with a
UTF-8 BOM, ";" as delimiter and "," as decimal separator, so all of that is accepted.
"""

import csv
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.evidence.models import EvidenceRecord, EvidenceValue

COLUMNS = ("iso3", "metric", "value", "year", "source_name", "source_url")
ENGLISH_BANDS = ("very_high", "high", "moderate", "low", "very_low")


class ManualInputError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class ManualMetric:
    unit: str
    parse: Callable[[str, bool], EvidenceValue]  # (text, decimal_comma) -> value
    expected: str  # human description used in error messages


def _percentage(text: str, decimal_comma: bool) -> float:
    value = float(text.replace(",", ".") if decimal_comma else text)
    if not 0 <= value <= 100:
        raise ValueError
    return value


def _yes_no(text: str, _: bool) -> bool:
    answer = text.strip().lower()
    if answer not in ("yes", "no"):
        raise ValueError
    return answer == "yes"


def _band(text: str, _: bool) -> str:
    band = text.strip().lower().replace(" ", "_")
    if band not in ENGLISH_BANDS:
        raise ValueError
    return band


MANUAL_METRICS: dict[str, ManualMetric] = {
    "english_band": ManualMetric("band", _band, "one of " + ", ".join(ENGLISH_BANDS)),
    "whatsapp_pct": ManualMetric("%", _percentage, "a number 0-100"),
    "social_media_pct": ManualMetric("%", _percentage, "a number 0-100"),
    "tax_treaty_with_home": ManualMetric("bool", _yes_no, "yes or no"),
    "trade_agreement_with_home": ManualMetric("bool", _yes_no, "yes or no"),
}


def _read_rows(path: Path) -> tuple[list[dict[str, str]], bool]:
    text = path.read_text(encoding="utf-8-sig")
    delimiter = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;").delimiter
    rows = list(csv.DictReader(text.splitlines(), delimiter=delimiter))
    return rows, delimiter == ";"


def load_manual_inputs(path: Path) -> list[EvidenceRecord]:
    rows, decimal_comma = _read_rows(path)
    retrieved_at = datetime.now(UTC).isoformat(timespec="seconds")
    errors: list[str] = []
    seen: dict[tuple[str, str], int] = {}
    records: list[EvidenceRecord] = []

    for line, row in enumerate(rows, start=2):  # line 1 is the header
        if missing := [c for c in COLUMNS if c not in row]:
            raise ManualInputError([f"{path.name}: missing column(s) {', '.join(missing)}"])
        iso3, metric = row["iso3"].strip().upper(), row["metric"].strip()
        definition = MANUAL_METRICS.get(metric)
        if definition is None:
            errors.append(f"line {line}: unknown metric '{metric}'")
            continue
        try:
            value = definition.parse(row["value"].strip(), decimal_comma)
        except ValueError:
            errors.append(
                f"line {line}: {metric} must be {definition.expected}, got '{row['value']}'"
            )
            continue
        if (iso3, metric) in seen:
            errors.append(
                f"line {line}: duplicate {iso3} {metric} (first on line {seen[iso3, metric]})"
            )
            continue
        seen[iso3, metric] = line
        year = row["year"].strip()
        records.append(
            EvidenceRecord(
                country=iso3,
                metric=metric,
                value=value,
                unit=definition.unit,
                year=int(year) if year.isdigit() else None,
                source_name=row["source_name"].strip(),
                source_url=row["source_url"].strip(),
                retrieved_at=retrieved_at,
                method="manual",
            )
        )
    if errors:
        raise ManualInputError(errors)
    return records
