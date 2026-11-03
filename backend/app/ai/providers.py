"""Free AI models on Groq, called through its OpenAI-compatible chat API.

The app offers every model listed in GROQ_MODELS. Groq's free limits are counted per model, so
when one model is saturated the error message suggests the other.
"""

from dataclasses import dataclass
from typing import Protocol

import httpx2

from app.settings import Settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
PROVIDER_LABELS = {"groq": "Groq"}
# Providers no longer offered, so analyses saved with them still show a proper name.
RETIRED_LABELS = {"gemini": "Gemini"}
MODEL_LABELS = {"openai/gpt-oss-120b": "GPT-OSS 120B", "qwen/qwen3.8-27b": "Qwen 3.8 27B"}
# GPT-OSS reasons before answering; a short think keeps the JSON answer from being cut off.
EXTRA_BODY = {"openai/gpt-oss-120b": {"reasoning_effort": "low"}}
REQUEST_TIMEOUT_SECONDS = 60
SERVICE_FAILED = "The AI service failed. Try again."


@dataclass(frozen=True)
class ModelOption:
    id: str
    label: str
    model: str


class TextModel(Protocol):
    provider: str
    model: str

    def complete_json(self, prompt: str) -> str: ...


class AIProviderError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def model_label(model: str) -> str:
    return MODEL_LABELS.get(model, model)


def available_models(settings: Settings) -> list[ModelOption]:
    if not settings.groq_api_key:
        return []
    return [ModelOption(m, f"Groq · {model_label(m)}", m) for m in settings.groq_models]


class OpenAICompatibleModel:
    provider = "groq"

    def __init__(
        self, model: str, api_key: str, client: httpx2.Client, alternative: str | None = None
    ) -> None:
        self.model = model
        self.alternative = alternative
        self._api_key = api_key
        self._client = client

    def _or_other(self, sentence: str, comma: str = ", or") -> str:
        if self.alternative is None:
            return f"{sentence}."
        return f"{sentence}{comma} use {model_label(self.alternative)}."

    def complete_json(self, prompt: str) -> str:
        """The model's answer text; "" when Groq rejected its own JSON (the caller retries)."""
        name = model_label(self.model)
        try:
            response = self._client.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3,
                    **EXTRA_BODY.get(self.model, {}),
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except httpx2.TimeoutException as error:
            raise AIProviderError(
                504, self._or_other(f"{name} took too long to answer. Try again", " or")
            ) from error
        except httpx2.HTTPError as error:
            raise AIProviderError(502, SERVICE_FAILED) from error
        if response.status_code == 429:  # Groq's free limits are per minute (and per day)
            raise AIProviderError(429, self._or_other(
                f"Groq's free limit for {name} was reached. Wait a minute and try again"
            ))
        if response.status_code in (401, 403):
            raise AIProviderError(502, "The Groq API key was rejected")
        if response.status_code == 503:
            raise AIProviderError(
                503, self._or_other("Groq is busy right now. Try again in a few minutes", " or")
            )
        if response.status_code == 400 and _error_code(response) == "json_validate_failed":
            return ""
        if response.status_code >= 400:
            raise AIProviderError(502, SERVICE_FAILED)
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise AIProviderError(502, SERVICE_FAILED) from error


def _error_code(response: httpx2.Response) -> str | None:
    try:
        return response.json()["error"]["code"]
    except (ValueError, KeyError, TypeError):
        return None


def build_models(settings: Settings, client: httpx2.Client) -> dict[str, TextModel]:
    if not settings.groq_api_key:
        return {}
    names = list(settings.groq_models)
    return {
        name: OpenAICompatibleModel(
            name, settings.groq_api_key, client,
            alternative=next((other for other in names if other != name), None),
        )
        for name in names
    }
