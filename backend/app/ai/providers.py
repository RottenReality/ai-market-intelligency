"""Free AI providers (Gemini and Groq) called through their OpenAI-compatible chat API."""

from dataclasses import dataclass
from typing import Literal, Protocol

import httpx2

from app.settings import Settings

ProviderId = Literal["gemini", "groq"]

PROVIDER_LABELS: dict[ProviderId, str] = {"gemini": "Gemini", "groq": "Groq"}
PROVIDER_URLS: dict[ProviderId, str] = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
}
REQUEST_TIMEOUT_SECONDS: dict[ProviderId, int] = {"gemini": 60, "groq": 30}
# Gemini "thinks" before answering; a short think keeps a comparison well inside its time limit.
EXTRA_BODY: dict[ProviderId, dict[str, str]] = {"gemini": {"reasoning_effort": "low"}, "groq": {}}
SERVICE_FAILED = "The AI service failed. Try again."


@dataclass(frozen=True)
class ProviderInfo:
    id: ProviderId
    label: str
    model: str


class TextModel(Protocol):
    provider: ProviderId
    model: str

    def _timeout_message(self) -> str:
        message = f"{PROVIDER_LABELS[self.provider]} took too long to answer."
        if self._alternative:
            return f"{message} Try again or use {PROVIDER_LABELS[self._alternative]}."
        return f"{message} Try again."

    def _busy_message(self) -> str:
        message = f"{PROVIDER_LABELS[self.provider]} is busy right now."
        if self._alternative:
            return f"{message} Try again in a few minutes or use {PROVIDER_LABELS[self._alternative]}."
        return f"{message} Try again in a few minutes."

    def complete_json(self, prompt: str) -> str: ...


class AIProviderError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _configured(settings: Settings) -> list[tuple[ProviderId, str, str]]:
    """(id, api key, model) for every provider that has a key, Gemini first."""
    candidates: list[tuple[ProviderId, str | None, str]] = [
        ("gemini", settings.gemini_api_key, settings.gemini_model),
        ("groq", settings.groq_api_key, settings.groq_model),
    ]
    return [(pid, key, model) for pid, key, model in candidates if key]


def available_providers(settings: Settings) -> list[ProviderInfo]:
    return [ProviderInfo(pid, PROVIDER_LABELS[pid], model) for pid, _, model in _configured(settings)]


class OpenAICompatibleModel:
    def __init__(
        self,
        provider: ProviderId,
        model: str,
        api_key: str,
        client: httpx2.Client,
        alternative: ProviderId | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self._api_key = api_key
        self._client = client
        self._alternative = alternative

    def _quota_message(self) -> str:
        message = f"The free quota for {PROVIDER_LABELS[self.provider]} is used up for now."
        if self._alternative:
            return f"{message} Try again later or use {PROVIDER_LABELS[self._alternative]}."
        return f"{message} Try again later."

    def _timeout_message(self) -> str:
        message = f"{PROVIDER_LABELS[self.provider]} took too long to answer."
        if self._alternative:
            return f"{message} Try again or use {PROVIDER_LABELS[self._alternative]}."
        return f"{message} Try again."

    def _busy_message(self) -> str:
        message = f"{PROVIDER_LABELS[self.provider]} is busy right now."
        if self._alternative:
            return f"{message} Try again in a few minutes or use {PROVIDER_LABELS[self._alternative]}."
        return f"{message} Try again in a few minutes."

    def complete_json(self, prompt: str) -> str:
        try:
            response = self._client.post(
                PROVIDER_URLS[self.provider],
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3,
                    **EXTRA_BODY[self.provider],
                },
                timeout=REQUEST_TIMEOUT_SECONDS[self.provider],
            )
        except httpx2.TimeoutException as error:
            raise AIProviderError(504, self._timeout_message()) from error
        except httpx2.HTTPError as error:
            raise AIProviderError(502, SERVICE_FAILED) from error
        if response.status_code == 429:
            raise AIProviderError(429, self._quota_message())
        if response.status_code in (401, 403):
            raise AIProviderError(
                502, f"The {PROVIDER_LABELS[self.provider]} API key was rejected"
            )
        if response.status_code == 503:  # free models are often overloaded for a few minutes
            raise AIProviderError(503, self._busy_message())
        if response.status_code >= 400:
            raise AIProviderError(502, SERVICE_FAILED)
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise AIProviderError(502, SERVICE_FAILED) from error


def build_models(settings: Settings, client: httpx2.Client) -> dict[ProviderId, TextModel]:
    configured = _configured(settings)
    ids = [pid for pid, _, _ in configured]
    models: dict[ProviderId, TextModel] = {}
    for pid, key, model in configured:
        alternative = next((other for other in ids if other != pid), None)
        models[pid] = OpenAICompatibleModel(pid, model, key, client, alternative=alternative)
    return models
