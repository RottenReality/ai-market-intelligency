"""Provider-agnostic LLM port. Adapters live in app/explanation/providers/."""

from typing import Protocol

from app.settings import Settings


class ExplanationModel(Protocol):
    def generate(self, prompt: str) -> str: ...


class ModelNotConfigured(RuntimeError):
    pass


def get_model(settings: Settings) -> ExplanationModel:
    if not settings.llm_provider:
        raise ModelNotConfigured("LLM_PROVIDER is not set")
    raise ModelNotConfigured(f"Unknown LLM provider: {settings.llm_provider}")
