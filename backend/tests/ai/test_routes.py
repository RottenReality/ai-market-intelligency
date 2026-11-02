from dataclasses import replace

from app.deps import get_settings


def test_providers_route_lists_configured_models(auth_client, settings):
    assert auth_client.get("/api/ai/providers").json() == []
    configured = replace(settings, groq_api_key="q")
    auth_client.app.dependency_overrides[get_settings] = lambda: configured
    assert auth_client.get("/api/ai/providers").json() == [
        {"id": "groq", "label": "Groq", "model": "openai/gpt-oss-120b"}
    ]


def test_providers_route_requires_session(client):
    assert client.get("/api/ai/providers").status_code == 401
