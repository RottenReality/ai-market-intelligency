import httpx2

from app.evidence.models import EvidenceRecord
from app.evidence.store import EvidenceStore
from app.sources.collect import collect_country
from app.sources.worldbank import WB_METRICS
from tests.sources.worldbank_fixtures import fixture_client, fixture_handler


def test_collect_stores_all_five_metrics_for_colombia(settings):
    store = EvidenceStore(settings.db_path)
    report = collect_country("COL", client=fixture_client(), store=store)
    assert report.failed == []
    assert sorted(report.stored) == sorted(f"COL:{m}" for m in WB_METRICS)
    assert set(store.get_country("COL")) == set(WB_METRICS)


def test_network_error_keeps_previous_value_and_reports_failure(settings):
    store = EvidenceStore(settings.db_path)
    previous = EvidenceRecord("COL", "internet_pct", 70.0, "%", 2020, "World Bank",
                              "https://old", "2025-01-01T00:00:00+00:00", "api")
    store.upsert([previous])

    def flaky(request: httpx2.Request) -> httpx2.Response:
        if "IT.NET.USER.ZS" in request.url.path:
            raise httpx2.ConnectError("World Bank unreachable", request=request)
        return fixture_handler(request)

    report = collect_country("COL", client=fixture_client(flaky), store=store)

    stored = store.get_country("COL")
    assert stored["internet_pct"] == previous
    assert len(stored) == len(WB_METRICS)
    assert [key for key, _ in report.failed] == ["COL:internet_pct"]
    assert "unreachable" in report.failed[0][1]


def test_country_without_data_is_reported_as_missing_not_failed(settings):
    store = EvidenceStore(settings.db_path)
    report = collect_country("CHI", client=fixture_client(), store=store)
    assert "CHI:internet_pct" in report.missing
    assert "CHI:internet_pct" not in [key for key, _ in report.failed]


def test_collect_stores_computed_and_manual_metrics(settings):
    from pathlib import Path

    from app.profile.company import load_profile
    from app.profile.countries import load_countries

    store = EvidenceStore(settings.db_path)
    report = collect_country(
        "COL",
        client=fixture_client(),
        store=store,
        settings=settings,
        profile=load_profile(Path("config")),
        countries=load_countries(Path("config/countries.yaml")),
    )
    stored = store.get_country("COL")
    assert report.failed == []
    assert stored["max_hour_diff_home"].value == 3
    assert stored["max_hour_diff_home"].method == "computed"
    assert stored["kogut_singh"].method == "computed"
    assert stored["kogut_singh"].value > 0
    assert stored["tax_treaty_with_home"].value is False
    assert stored["tax_treaty_with_home"].method == "manual"


def test_invalid_manual_file_is_reported_as_failure(settings, tmp_path):
    from dataclasses import replace
    from pathlib import Path

    from app.profile.company import load_profile
    from app.profile.countries import load_countries

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "manual_inputs.csv").write_text(
        "iso3,metric,value,year,source_name,source_url\nCOL,whatsapp_pct,lots,2025,x,https://x\n",
        encoding="utf-8",
    )
    (data_dir / "hofstede.csv").write_text(Path("data/hofstede.csv").read_text(), encoding="utf-8")
    report = collect_country(
        "COL",
        client=fixture_client(),
        store=EvidenceStore(settings.db_path),
        settings=replace(settings, data_dir=data_dir),
        profile=load_profile(Path("config")),
        countries=load_countries(Path("config/countries.yaml")),
    )
    assert report.failed[0][0] == "COL:manual_inputs"
    assert "whatsapp_pct must be a number 0-100" in report.failed[0][1]
