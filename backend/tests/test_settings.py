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
    assert settings.gemini_api_key is None
    assert settings.groq_api_key is None
    assert settings.gemini_model == "gemini-3.8-flash"
    assert settings.groq_model == "openai/gpt-oss-120b"


def test_load_settings_parses_booleans():
    settings = load_settings({**REQUIRED, "TRUST_PROXY": "true", "COOKIE_SECURE": "TRUE"})
    assert settings.trust_proxy is True
    assert settings.cookie_secure is True


def test_load_settings_reads_ai_keys_and_models():
    settings = load_settings(
        {**REQUIRED, "GEMINI_API_KEY": "g-key", "GROQ_API_KEY": "q-key", "GROQ_MODEL": "llama-3.3-70b-versatile"}
    )
    assert settings.gemini_api_key == "g-key"
    assert settings.groq_api_key == "q-key"
    assert settings.groq_model == "llama-3.3-70b-versatile"
