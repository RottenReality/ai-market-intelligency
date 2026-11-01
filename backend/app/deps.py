"""Shared FastAPI dependencies. Tests override these through ``app.dependency_overrides``."""

from functools import lru_cache
from typing import Annotated

import httpx2
from fastapi import Depends

from app.ai.providers import ProviderId, TextModel, build_models
from app.analysis.store import AnalysisStore
from app.evidence.store import EvidenceStore
from app.profile.company import CompanyProfile, load_profile
from app.profile.countries import Country, load_countries
from app.profile.store import ProfileStore, effective_profile
from app.settings import Settings, load_settings


@lru_cache
def get_settings() -> Settings:
    return load_settings()


def get_countries(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, Country]:
    return load_countries(settings.config_dir / "countries.yaml")


def get_profile_store(settings: Annotated[Settings, Depends(get_settings)]) -> ProfileStore:
    return ProfileStore(settings.db_path)


def get_profile(settings: Annotated[Settings, Depends(get_settings)]) -> CompanyProfile:
    """The effective profile: the file profile with any edits saved in the app applied."""
    return effective_profile(load_profile(settings.config_dir), ProfileStore(settings.db_path).get())


def get_store(settings: Annotated[Settings, Depends(get_settings)]) -> EvidenceStore:
    return EvidenceStore(settings.db_path)


def get_analysis_store(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnalysisStore:
    return AnalysisStore(settings.db_path)


@lru_cache
def get_http_client() -> httpx2.Client:
    return httpx2.Client()


def get_ai_models(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[ProviderId, TextModel]:
    """The AI providers that have an API key configured (tests override this with fakes)."""
    return build_models(settings, get_http_client())
