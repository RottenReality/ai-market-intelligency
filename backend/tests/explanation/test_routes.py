from app.deps import get_explanation_model
from app.evidence.store import EvidenceStore
from tests.explanation.fakes import CLEAN, FakeModel
from tests.explanation.test_prompt import FULL
from tests.scoring.evidence_factory import USA, evidence

URL = "/api/countries/COL/explanation"


def seed(settings):
    EvidenceStore(settings.db_path).upsert([*evidence("COL", FULL).values(),
                                            *evidence("USA", USA).values()])


def use_model(client, model):
    client.app.dependency_overrides[get_explanation_model] = lambda: model


def test_get_without_explanation_returns_404(auth_client, settings):
    seed(settings)
    response = auth_client.get(URL)
    assert response.status_code == 404
    assert response.json() == {"detail": "No explanation yet"}


def test_post_returns_explanation_and_get_returns_cached(auth_client, settings):
    seed(settings)
    use_model(auth_client, FakeModel([CLEAN]))
    created = auth_client.post(URL)
    assert created.status_code == 200
    assert created.json()["text"] == CLEAN
    assert created.json()["flagged"] is False
    assert auth_client.get(URL).json() == created.json()


def test_post_without_provider_returns_503(auth_client, settings):
    seed(settings)  # settings fixture has no LLM provider configured
    response = auth_client.post(URL)
    assert response.status_code == 503
    assert response.json() == {"detail": "AI is not configured"}


def test_model_error_returns_502(auth_client, settings):
    seed(settings)
    use_model(auth_client, FakeModel([ConnectionError("down")]))
    response = auth_client.post(URL)
    assert response.status_code == 502
    assert response.json() == {"detail": "The AI service failed"}


def test_unknown_country_returns_404(auth_client):
    assert auth_client.post("/api/countries/XYZ/explanation").status_code == 404


def test_explanation_requires_session(client):
    assert client.get(URL).status_code == 401
    assert client.post(URL).status_code == 401
