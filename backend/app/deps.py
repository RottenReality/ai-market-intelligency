"""Shared FastAPI dependencies. Tests override these through ``app.dependency_overrides``."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.evidence.store import EvidenceStore
from app.explanation.cache import ExplanationCache
from app.explanation.model import ExplanationModel, ModelNotConfigured, get_model
from app.profile.company import CompanyProfile, load_profile
from app.profile.countries import Country, load_countries
from app.settings import Settings, load_settings


@lru_cache
def get_settings() -> Settings:
    return load_settings()


def get_countries(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, Country]:
    return load_countries(settings.config_dir / "countries.yaml")


def get_profile(settings: Annotated[Settings, Depends(get_settings)]) -> CompanyProfile:
    return load_profile(settings.config_dir)


def get_store(settings: Annotated[Settings, Depends(get_settings)]) -> EvidenceStore:
    return EvidenceStore(settings.db_path)


def get_explanation_cache(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ExplanationCache:
    return ExplanationCache(settings.db_path)


def get_explanation_model(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ExplanationModel | None:
    """The configured LLM, or None when no provider is set (the API then answers 503)."""
    try:
        return get_model(settings)
    except ModelNotConfigured:
        return None
