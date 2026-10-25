"""Shared FastAPI dependencies. Tests override these through ``app.dependency_overrides``."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

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
