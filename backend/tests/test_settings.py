from pathlib import Path

import pytest

from app.settings import SettingsError, load_settings

REQUIRED = {"APP_USERNAME": "admin", "APP_PASSWORD_HASH": "$2b$hash", "SECRET_KEY": "s3cret"}


def test_load_settings_lists_all_missing_required_vars():
    with pytest.raises(SettingsError) as exc:
        load_settings({})
    message = str(exc.value)
    for name in REQUIRED:
        assert name in message


def test_load_settings_applies_defaults():
    settings = load_settings(REQUIRED)
    assert settings.trust_proxy is False
    assert settings.cookie_secure is False
    assert settings.db_path == Path("data/app.sqlite")
    assert settings.llm_provider is None


def test_load_settings_parses_booleans():
    settings = load_settings({**REQUIRED, "TRUST_PROXY": "true", "COOKIE_SECURE": "TRUE"})
    assert settings.trust_proxy is True
    assert settings.cookie_secure is True
