import json
from dataclasses import replace

import httpx2
import pytest

from app.ai.providers import (
    PROVIDER_URLS,
    AIProviderError,
    OpenAICompatibleModel,
    available_providers,
)


def ok_reply(content: str = '{"a": 1}') -> httpx2.Response:
    return httpx2.Response(200, json={"choices": [{"message": {"content": content}}]})


def model_with(handler, provider="gemini", alternative=None) -> OpenAICompatibleModel:
    client = httpx2.Client(transport=httpx2.MockTransport(handler))
    return OpenAICompatibleModel(provider, "test-model", "k", client, alternative=alternative)


def test_available_providers_depend_on_keys(settings):
    assert available_providers(settings) == []
    only_gemini = available_providers(replace(settings, gemini_api_key="g"))
    assert [(p.id, p.label, p.model) for p in only_gemini] == [("gemini", "Gemini", "gemini-3.8-flash")]
    both = available_providers(replace(settings, gemini_api_key="g", groq_api_key="q"))
    assert [p.id for p in both] == ["gemini", "groq"]
    assert both[1].model == "openai/gpt-oss-120b"


@pytest.mark.parametrize("provider", ["gemini", "groq"])
def test_request_shape(provider):
    seen: list[httpx2.Request] = []

    def handler(request):
        seen.append(request)
        return ok_reply()

    model_with(handler, provider).complete_json("hello")
    request = seen[0]
    assert str(request.url) == PROVIDER_URLS[provider]
    assert request.headers["authorization"] == "Bearer k"
    body = json.loads(request.content)
    assert body["model"] == "test-model"
    assert body["messages"] == [{"role": "user", "content": "hello"}]
    assert body["response_format"] == {"type": "json_object"}


def test_provider_urls():
    assert PROVIDER_URLS == {
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "groq": "https://api.groq.com/openai/v1/chat/completions",
    }


def test_returns_message_content():
    assert model_with(lambda r: ok_reply('{"x": "y"}')).complete_json("p") == '{"x": "y"}'


def test_429_names_provider_and_suggests_alternative():
    model = model_with(lambda r: httpx2.Response(429), "gemini", alternative="groq")
    with pytest.raises(AIProviderError) as exc:
        model.complete_json("p")
    assert exc.value.status_code == 429
    assert exc.value.detail == (
        "The free quota for Gemini is used up for now. Try again later or use Groq."
    )


def test_429_without_alternative():
    model = model_with(lambda r: httpx2.Response(429), "groq")
    with pytest.raises(AIProviderError) as exc:
        model.complete_json("p")
    assert exc.value.detail == "The free quota for Groq is used up for now. Try again later."


@pytest.mark.parametrize("status", [401, 403])
def test_rejected_key(status):
    with pytest.raises(AIProviderError) as exc:
        model_with(lambda r: httpx2.Response(status), "groq").complete_json("p")
    assert (exc.value.status_code, exc.value.detail) == (502, "The Groq API key was rejected")


def test_timeout_maps_to_service_failed():
    def handler(request):
        raise httpx2.ReadTimeout("slow", request=request)

    with pytest.raises(AIProviderError) as exc:
        model_with(handler).complete_json("p")
    assert (exc.value.status_code, exc.value.detail) == (502, "The AI service failed. Try again.")


def test_server_error_maps_to_service_failed():
    with pytest.raises(AIProviderError) as exc:
        model_with(lambda r: httpx2.Response(500)).complete_json("p")
    assert exc.value.detail == "The AI service failed. Try again."


def test_unexpected_body_maps_to_service_failed():
    with pytest.raises(AIProviderError) as exc:
        model_with(lambda r: httpx2.Response(200, json={"nope": True})).complete_json("p")
    assert exc.value.status_code == 502
