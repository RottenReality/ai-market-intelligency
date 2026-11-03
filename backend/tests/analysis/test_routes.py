from app.ai.providers import AIProviderError
from app.deps import get_ai_models
from app.evidence.store import EvidenceStore
from tests.analysis.fakes import FakeModel, country_content
from tests.analysis.fixtures import FULL
from tests.scoring.evidence_factory import USA, evidence

URL = "/api/countries/COL/analysis"


def seed(settings):
    EvidenceStore(settings.db_path).upsert(
        [*evidence("COL", FULL).values(), *evidence("USA", USA).values()]
    )


def use_models(client, **models):
    client.app.dependency_overrides[get_ai_models] = lambda: models


def test_post_then_get(auth_client, settings):
    seed(settings)
    use_models(auth_client, gpt=FakeModel([country_content()]))
    created = auth_client.post(URL, json={"provider": "gpt"})
    assert created.status_code == 200
    body = created.json()
    assert body["provider_label"] == "Groq"
    assert body["content"]["barriers"] == ["No tax treaty [A1]", "Cultural distance [C3]"]
    assert auth_client.get(URL).json() == body


def test_get_without_analysis_404(auth_client, settings):
    seed(settings)
    response = auth_client.get(URL)
    assert response.status_code == 404
    assert response.json() == {"detail": "No AI analysis yet"}


def test_unknown_provider_400(auth_client, settings):
    seed(settings)
    use_models(auth_client, gpt=FakeModel([]))
    response = auth_client.post(URL, json={"provider": "groq"})
    assert response.status_code == 400
    assert response.json() == {"detail": "This AI is not configured"}


def test_no_providers_503(auth_client, settings):
    seed(settings)
    use_models(auth_client)
    response = auth_client.post(URL, json={"provider": "gpt"})
    assert response.status_code == 503
    assert response.json() == {"detail": "AI is not configured"}


def test_quota_error_passes_429_and_message(auth_client, settings):
    seed(settings)
    message = "Groq's free limit for GPT-OSS 120B was reached. Wait a minute and try again, or use Qwen 3.8 27B."
    use_models(auth_client, gpt=FakeModel([AIProviderError(429, message)]))
    response = auth_client.post(URL, json={"provider": "gpt"})
    assert response.status_code == 429
    assert response.json() == {"detail": message}


def test_unreadable_502(auth_client, settings):
    seed(settings)
    use_models(auth_client, gpt=FakeModel(["nope", "still nope"]))
    response = auth_client.post(URL, json={"provider": "gpt"})
    assert response.status_code == 502
    assert response.json() == {"detail": "The AI returned an unreadable answer. Try again."}


def test_unknown_country_404_and_no_data_409(auth_client, settings):
    use_models(auth_client, gpt=FakeModel([]))
    assert auth_client.post("/api/countries/XYZ/analysis", json={"provider": "gpt"}).status_code == 404
    assert auth_client.post(URL, json={"provider": "gpt"}).status_code == 409


def test_analysis_requires_session(client):
    assert client.get(URL).status_code == 401
    assert client.post(URL, json={"provider": "gpt"}).status_code == 401
