"""Shared FastAPI dependencies. Tests override these through ``app.dependency_overrides``."""

from functools import lru_cache

from app.settings import Settings, load_settings


@lru_cache
def get_settings() -> Settings:
    return load_settings()
