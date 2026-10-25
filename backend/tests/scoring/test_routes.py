from app.evidence.store import EvidenceStore
from tests.scoring.evidence_factory import COLOMBIA, USA, evidence


def seed(settings):
    store = EvidenceStore(settings.db_path)
    store.upsert([*evidence("COL", COLOMBIA).values(), *evidence("USA", USA).values()])


def test_countries_lists_configured_countries_with_data_flag(auth_client, settings):
    assert auth_client.get("/api/countries").json() == [
        {"iso3": "COL", "name": "Colombia", "has_data": False}
    ]
    seed(settings)
    assert auth_client.get("/api/countries").json()[0]["has_data"] is True


def test_scorecard_for_colombia_returns_five_indicators(auth_client, settings):
    seed(settings)
    response = auth_client.get("/api/countries/COL/scorecard")
    assert response.status_code == 200
    body = response.json()
    assert body["country"] == {"iso3": "COL", "name": "Colombia"}
    assert [i["id"] for i in body["indicators"]] == ["A3", "G2", "E1", "E2", "E3"]
    assert body["indicators"][0]["sources"][0]["name"] == "World Bank"


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
