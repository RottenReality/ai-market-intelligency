from dataclasses import replace
from pathlib import Path

import pytest

from app.sources.manual import ManualInputError, load_manual_inputs

FIXTURES = Path(__file__).parent.parent / "fixtures" / "manual"


def comparable(records):
    return sorted((replace(r, retrieved_at="") for r in records), key=lambda r: r.metric)


def test_valid_file_loads_typed_values():
    records = {r.metric: r for r in load_manual_inputs(FIXTURES / "valid.csv")}
    assert records["social_media_pct"].value == 70.4
    assert records["social_media_pct"].unit == "%"
    assert records["tax_treaty_with_home"].value is False
    assert records["tax_treaty_with_home"].country == "COL"
    assert records["trade_agreement_with_home"].value is True
    assert records["english_band"].value == "low"
    assert records["english_band"].year == 2025
    assert {r.method for r in records.values()} == {"manual"}
    assert records["english_band"].source_url == "https://www.ef.com/epi"


def test_spanish_excel_export_loads_like_plain_csv():
    # UTF-8 BOM, ";" delimiter, decimal comma and CRLF line endings, as Excel saves it
    # on a Spanish-locale computer.
    plain = load_manual_inputs(FIXTURES / "valid.csv")
    excel = load_manual_inputs(FIXTURES / "excel_es.csv")
    assert comparable(excel) == comparable(plain)


def test_bad_value_reports_line_number():
    with pytest.raises(ManualInputError) as exc:
        load_manual_inputs(FIXTURES / "bad_value.csv")
    assert exc.value.errors == ["line 3: whatsapp_pct must be a number 0-100, got 'abc'"]


def test_duplicate_country_metric_is_an_error():
    with pytest.raises(ManualInputError) as exc:
        load_manual_inputs(FIXTURES / "duplicate.csv")
    assert exc.value.errors == ["line 3: duplicate COL social_media_pct (first on line 2)"]


def test_unknown_metric_is_an_error():
    with pytest.raises(ManualInputError) as exc:
        load_manual_inputs(FIXTURES / "unknown_metric.csv")
    assert "unknown metric 'coffee_per_capita'" in exc.value.errors[0]


def test_repository_manual_inputs_load():
    records = load_manual_inputs(Path("data/manual_inputs.csv"))
    assert any(r.country == "COL" and r.metric == "tax_treaty_with_home" for r in records)
