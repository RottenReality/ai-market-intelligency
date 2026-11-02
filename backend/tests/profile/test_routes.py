from app.evidence.store import EvidenceStore
from tests.scoring.evidence_factory import COLOMBIA, USA, evidence

EDITS = {
    "name": "Real Co.",
    "description": "We run SMS campaigns for restaurants.",
    "supported_languages": ["en", "es"],
    "channels": ["sms", "email"],
}


def test_get_profile_from_file_by_default(auth_client):
    body = auth_client.get("/api/profile").json()
    assert body["source"] == "file"
    assert body["name"] == "Example Restaurant Marketing Co."
    assert body["home_country"] == "USA"
    assert body["home_timezone"] == "America/Los_Angeles"
    assert body["options"] == {
        "languages": ["en", "es", "pt", "fr", "de", "it"],
        "channels": ["sms", "email", "whatsapp"],
    }


def test_put_saves_and_returns_saved_source(auth_client):
    response = auth_client.put("/api/profile", json=EDITS)
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "saved"
    assert body["name"] == "Real Co."
    assert body["description"] == EDITS["description"]
    assert auth_client.get("/api/profile").json()["supported_languages"] == ["en", "es"]


def test_put_invalid_returns_422_with_field(auth_client):
    response = auth_client.put("/api/profile", json={**EDITS, "channels": ["fax"]})
    assert response.status_code == 422
    assert "channels" in str(response.json()["detail"])


def test_saving_spanish_changes_colombia_c1_immediately(auth_client, settings):
    EvidenceStore(settings.db_path).upsert(
        [*evidence("COL", {**COLOMBIA, "english_band": "low"}).values(),
         *evidence("USA", USA).values()]
    )

    def c1():
        card = auth_client.get("/api/countries/COL/scorecard").json()
        return next(i for i in card["indicators"] if i["id"] == "C1")["score"]

    assert c1() == 25
    auth_client.put("/api/profile", json=EDITS)
    assert c1() == 100


def test_delete_resets_to_file(auth_client):
    auth_client.put("/api/profile", json=EDITS)
    response = auth_client.delete("/api/profile")
    assert response.status_code == 200
    assert response.json()["source"] == "file"
    assert auth_client.get("/api/profile").json()["name"] == "Example Restaurant Marketing Co."


def test_profile_requires_session(client):
    assert client.get("/api/profile").status_code == 401
    assert client.put("/api/profile", json=EDITS).status_code == 401
    assert client.delete("/api/profile").status_code == 401
