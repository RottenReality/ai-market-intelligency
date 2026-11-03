from dataclasses import replace

from app.deps import get_settings


def test_providers_route_lists_configured_models(auth_client, settings):
    assert auth_client.get("/api/ai/providers").json() == []
    configured = replace(settings, groq_api_key="q")
    auth_client.app.dependency_overrides[get_settings] = lambda: configured
    assert auth_client.get("/api/ai/providers").json() == [
        {"id": "openai/gpt-oss-120b", "label": "Groq · GPT-OSS 120B", "model": "openai/gpt-oss-120b"},
        {"id": "qwen/qwen3.8-27b", "label": "Groq · Qwen 3.8 27B", "model": "qwen/qwen3.8-27b"},
    ]


def test_providers_route_requires_session(client):
    assert client.get("/api/ai/providers").status_code == 401
