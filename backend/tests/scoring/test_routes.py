from pathlib import Path

from app.evidence.store import EvidenceStore
from app.profile.countries import load_countries
from tests.scoring.evidence_factory import COLOMBIA, USA, evidence


def seed(settings):
    store = EvidenceStore(settings.db_path)
    store.upsert([*evidence("COL", COLOMBIA).values(), *evidence("USA", USA).values()])


def test_countries_lists_configured_countries_with_data_flag(auth_client, settings):
    countries = auth_client.get("/api/countries").json()
    assert countries[0] == {"iso3": "COL", "name": "Colombia", "has_data": False}
    assert [c["iso3"] for c in countries] == list(load_countries(Path("config/countries.yaml")))
    seed(settings)
    assert auth_client.get("/api/countries").json()[0]["has_data"] is True


def test_scorecard_for_colombia_returns_all_twelve_indicators(auth_client, settings):
    seed(settings)
    response = auth_client.get("/api/countries/COL/scorecard")
    assert response.status_code == 200
    body = response.json()
    assert body["country"] == {"iso3": "COL", "name": "Colombia"}
    assert [i["id"] for i in body["indicators"]] == [
        "C1", "C2", "C3", "A1", "A2", "A3", "G1", "G2", "G3", "E1", "E2", "E3",
    ]
    a3 = next(i for i in body["indicators"] if i["id"] == "A3")
    assert a3["sources"][0]["name"] == "World Bank"


def test_scorecard_includes_dimensions_and_accessibility(auth_client, settings):
    seed(settings)
    body = auth_client.get("/api/countries/COL/scorecard").json()
    assert [d["id"] for d in body["dimensions"]] == ["C", "A", "G", "E"]
    # Only World Bank evidence is seeded: Cultural has no indicators.
    assert body["accessibility"] is None
    assert body["accessibility_reason"] == "Not enough data: no indicators for Cultural"


def test_lowercase_iso3_works(auth_client, settings):
    seed(settings)
    assert auth_client.get("/api/countries/col/scorecard").status_code == 200


def test_unknown_country_returns_404_naming_code(auth_client):
    response = auth_client.get("/api/countries/XYZ/scorecard")
    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown country: XYZ"}


def test_country_without_data_returns_409(auth_client):
    response = auth_client.get("/api/countries/COL/scorecard")
    assert response.status_code == 409
    assert response.json() == {"detail": "No data collected yet for Colombia"}


def test_scorecard_requires_session(client):
    assert client.get("/api/countries/COL/scorecard").status_code == 401
    assert client.get("/api/countries").status_code == 401
