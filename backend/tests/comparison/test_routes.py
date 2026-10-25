from app.evidence.store import EvidenceStore
from tests.scoring.evidence_factory import COLOMBIA, USA, evidence

FULL = {**COLOMBIA, "kogut_singh": 2.5, "max_hour_diff_home": 3.0, "tax_treaty_with_home": False}


def seed(settings, country: str, values: dict) -> None:
    EvidenceStore(settings.db_path).upsert(evidence(country, values).values())


def seed_all(settings) -> None:
    seed(settings, "USA", USA)
    seed(settings, "COL", FULL)
    # Mexico: same as Colombia but closer in time (2 h) and with a tax treaty -> ranks higher.
    seed(settings, "MEX", {**FULL, "max_hour_diff_home": 2.0, "tax_treaty_with_home": True})
    # Spain: World Bank data only -> no Cultural indicator -> accessibility is null.
    seed(settings, "ESP", COLOMBIA)


def test_sorted_by_accessibility_with_nulls_last(auth_client, settings):
    seed_all(settings)
    response = auth_client.get("/api/comparison", params={"iso3": "ESP,COL,MEX"})
    assert response.status_code == 200
    countries = response.json()["countries"]
    assert [c["iso3"] for c in countries] == ["MEX", "COL", "ESP"]
    assert countries[0]["accessibility"] > countries[1]["accessibility"]
    assert countries[2]["accessibility"] is None
    assert set(countries[0]["dimensions"]) == {"C", "A", "G", "E"}
    assert countries[0]["name"] == "Mexico"


def test_country_without_data_is_included_with_has_data_false(auth_client, settings):
    seed_all(settings)
    countries = auth_client.get("/api/comparison", params={"iso3": "COL,CHL"}).json()["countries"]
    chile = next(c for c in countries if c["iso3"] == "CHL")
    assert chile["has_data"] is False
    assert chile["accessibility"] is None
    assert chile["dimensions"] == {"C": None, "A": None, "G": None, "E": None}


def test_lowercase_codes_and_spaces_accepted(auth_client, settings):
    seed_all(settings)
    response = auth_client.get("/api/comparison", params={"iso3": "col, mex"})
    assert response.status_code == 200
    assert {c["iso3"] for c in response.json()["countries"]} == {"COL", "MEX"}


def test_unknown_code_returns_404_naming_it(auth_client):
    response = auth_client.get("/api/comparison", params={"iso3": "COL,XYZ"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown country: XYZ"}


def test_empty_selection_returns_422(auth_client):
    assert auth_client.get("/api/comparison", params={"iso3": ""}).status_code == 422
    assert auth_client.get("/api/comparison").status_code == 422


def test_duplicates_are_listed_once(auth_client, settings):
    seed_all(settings)
    countries = auth_client.get("/api/comparison", params={"iso3": "COL,COL"}).json()["countries"]
    assert [c["iso3"] for c in countries] == ["COL"]


def test_comparison_requires_session(client):
    assert client.get("/api/comparison", params={"iso3": "COL"}).status_code == 401


def test_each_country_reports_how_many_indicators_had_data(auth_client, settings):
    seed_all(settings)
    countries = auth_client.get("/api/comparison", params={"iso3": "COL,ESP,CHL"}).json()["countries"]
    by_code = {c["iso3"]: c for c in countries}
    # COL: 5 World Bank + C3 + G1 + A1 = 8 of 12. ESP: World Bank only = 5. CHL: nothing.
    assert (by_code["COL"]["indicators_available"], by_code["COL"]["indicators_total"]) == (8, 12)
    assert by_code["ESP"]["indicators_available"] == 5
    assert (by_code["CHL"]["indicators_available"], by_code["CHL"]["indicators_total"]) == (0, 12)
