import httpx2
import pytest

from app.sources.worldbank import WorldBankError, fetch_latest
from tests.sources.worldbank_fixtures import fixture_client, fixture_handler


def test_parses_latest_value_and_year():
    record = fetch_latest(fixture_client(), "COL", "internet_pct")
    assert record is not None
    assert record.country == "COL"
    assert record.metric == "internet_pct"
    assert record.value == pytest.approx(79.345, abs=0.001)
    assert record.year == 2024
    assert record.unit == "%"
    assert record.method == "api"
    assert record.source_name == "World Bank"
    assert "IT.NET.USER.ZS" in record.source_url


def test_wgi_request_includes_source_3():
    seen: list[httpx2.Request] = []

    def spy(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return fixture_handler(request)

    record = fetch_latest(fixture_client(spy), "COL", "regulatory_quality")
    assert seen[0].url.params["source"] == "3"
    assert seen[0].url.params["mrnev"] == "1"
    assert record is not None and record.value == pytest.approx(-0.197, abs=0.001)


def test_empty_response_returns_none():
    client = fixture_client()
    # CHI has no internet-users series: the API answers [meta, null].
    assert fetch_latest(client, "CHI", "internet_pct") is None


def test_error_message_raises_worldbank_error(monkeypatch):
    from app.sources import worldbank

    monkeypatch.setitem(worldbank.WB_METRICS, "broken", worldbank.WBIndicator("NOT.A.CODE", "%"))
    with pytest.raises(WorldBankError, match="NOT.A.CODE"):
        fetch_latest(fixture_client(), "COL", "broken")


def test_lowercase_country_is_normalised():
    record = fetch_latest(fixture_client(), "col", "internet_pct")
    assert record is not None and record.country == "COL"
