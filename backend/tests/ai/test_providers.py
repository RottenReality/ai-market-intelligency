import json
from dataclasses import replace

import httpx2
import pytest

from app.ai.providers import (
    GROQ_URL,
    AIProviderError,
    OpenAICompatibleModel,
    available_models,
    build_models,
    model_label,
)

GPT, QWEN = "openai/gpt-oss-120b", "qwen/qwen3.8-27b"


def ok_reply(content: str = '{"a": 1}') -> httpx2.Response:
    return httpx2.Response(200, json={"choices": [{"message": {"content": content}}]})


def model_with(handler, model=GPT, alternative=None) -> OpenAICompatibleModel:
    client = httpx2.Client(transport=httpx2.MockTransport(handler))
    return OpenAICompatibleModel(model, "k", client, alternative=alternative)


def sent(model=GPT) -> tuple[httpx2.Request, dict]:
    seen: list[httpx2.Request] = []

    def handler(request):
        seen.append(request)
        return ok_reply()

    model_with(handler, model).complete_json("hello")
    return seen[0], json.loads(seen[0].content)


def failure(response: httpx2.Response | Exception, model=GPT, alternative=QWEN) -> AIProviderError:
    def handler(request):
        if isinstance(response, Exception):
            raise response
        return response

    with pytest.raises(AIProviderError) as exc:
        model_with(handler, model, alternative).complete_json("p")
    return exc.value


def test_two_groq_models_by_default_and_none_without_key(settings):
    assert available_models(settings) == []
    options = available_models(replace(settings, groq_api_key="q"))
    assert [(o.id, o.label, o.model) for o in options] == [
        (GPT, "Groq · GPT-OSS 120B", GPT),
        (QWEN, "Groq · Qwen 3.8 27B", QWEN),
    ]


def test_models_come_from_settings_and_unknown_names_are_shown_as_is(settings):
    options = available_models(replace(settings, groq_api_key="q", groq_models=("llama-x",)))
    assert [(o.id, o.label) for o in options] == [("llama-x", "Groq · llama-x")]


def test_each_model_suggests_the_other(settings):
    models = build_models(replace(settings, groq_api_key="q"), httpx2.Client())
    assert set(models) == {GPT, QWEN}
    assert models[GPT].provider == "groq" and models[GPT].model == GPT
    assert models[GPT].alternative == QWEN and models[QWEN].alternative == GPT


def test_model_label():
    assert model_label(GPT) == "GPT-OSS 120B"
    assert model_label("something/else") == "something/else"


def test_request_shape():
    request, body = sent()
    assert str(request.url) == GROQ_URL == "https://api.groq.com/openai/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer k"
    assert body["model"] == GPT
    assert body["messages"] == [{"role": "user", "content": "hello"}]
    assert body["response_format"] == {"type": "json_object"}
    assert request.extensions["timeout"]["read"] == 60


def test_gpt_oss_thinks_briefly_so_its_answer_is_not_cut_off():
    assert sent(GPT)[1]["reasoning_effort"] == "low"
    assert "reasoning_effort" not in sent(QWEN)[1]


def test_returns_message_content():
    assert model_with(lambda r: ok_reply('{"x": 2}')).complete_json("p") == '{"x": 2}'


def test_rejected_json_counts_as_an_unreadable_answer():
    # Groq refuses its own invalid or cut-off JSON with 400 json_validate_failed; an empty answer
    # makes the analysis retry once instead of failing at once.
    reply = httpx2.Response(400, json={"error": {"code": "json_validate_failed"}})
    assert model_with(lambda r: reply).complete_json("p") == ""


def test_rate_limit_says_wait_a_minute_and_suggests_the_other_model():
    error = failure(httpx2.Response(429))
    assert (error.status_code, error.detail) == (
        429, "Groq's free limit for GPT-OSS 120B was reached. "
        "Wait a minute and try again, or use Qwen 3.8 27B.",
    )


def test_rate_limit_without_alternative():
    error = failure(httpx2.Response(429), alternative=None)
    assert error.detail == "Groq's free limit for GPT-OSS 120B was reached. Wait a minute and try again."


@pytest.mark.parametrize("status", [401, 403])
def test_rejected_key(status):
    error = failure(httpx2.Response(status))
    assert (error.status_code, error.detail) == (502, "The Groq API key was rejected")


def test_timeout_says_it_took_too_long_and_suggests_the_other_model():
    error = failure(httpx2.ReadTimeout("slow"))
    assert (error.status_code, error.detail) == (
        504, "GPT-OSS 120B took too long to answer. Try again or use Qwen 3.8 27B."
    )


def test_busy_service_says_so():
    error = failure(httpx2.Response(503, json={"error": {}}))
    assert (error.status_code, error.detail) == (
        503, "Groq is busy right now. Try again in a few minutes or use Qwen 3.8 27B."
    )


@pytest.mark.parametrize("response", [
    httpx2.Response(500),
    httpx2.Response(400, json={"error": {"code": "context_length_exceeded"}}),
    httpx2.Response(200, json={"unexpected": True}),
    httpx2.ConnectError("down"),
])
def test_other_failures_map_to_service_failed(response):
    error = failure(response)
    assert (error.status_code, error.detail) == (502, "The AI service failed. Try again.")
