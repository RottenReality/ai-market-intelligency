from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import settings as app_settings
from app.deps import get_settings
from app.main import create_app
from app.settings import SettingsError, environment, load_settings

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
    assert settings.groq_api_key is None
    assert settings.groq_models == ("openai/gpt-oss-120b", "qwen/qwen3.8-27b")


def test_load_settings_parses_booleans():
    settings = load_settings({**REQUIRED, "TRUST_PROXY": "true", "COOKIE_SECURE": "TRUE"})
    assert settings.trust_proxy is True
    assert settings.cookie_secure is True


def test_load_settings_reads_ai_keys_and_models():
    settings = load_settings(
        {**REQUIRED, "GROQ_API_KEY": "q-key", "GROQ_MODELS": " llama-a , ,llama-b "}
    )
    assert settings.groq_api_key == "q-key"
    assert settings.groq_models == ("llama-a", "llama-b")


def write_env(path: Path, values: dict[str, str]) -> Path:
    path.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    return path


def test_env_file_is_read_without_env_file_flag(tmp_path):
    env_file = write_env(tmp_path / ".env", {**REQUIRED, "GROQ_API_KEY": "gsk_file"})
    settings = load_settings(environment(env_file, base={}))
    assert settings.app_username == "admin"
    assert settings.groq_api_key == "gsk_file"


def test_real_environment_wins_over_env_file(tmp_path):
    env_file = write_env(tmp_path / ".env", {**REQUIRED, "APP_USERNAME": "from-file"})
    settings = load_settings(environment(env_file, base={"APP_USERNAME": "from-env"}))
    assert settings.app_username == "from-env"


def test_missing_env_file_uses_the_real_environment(tmp_path):
    settings = load_settings(environment(tmp_path / "nope.env", base=REQUIRED))
    assert settings.secret_key == "s3cret"


def test_app_refuses_to_start_without_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(app_settings, "ENV_FILE", tmp_path / "missing.env")
    for name in REQUIRED:
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()  # a cached earlier result would hide the missing settings
    with pytest.raises(SettingsError, match="APP_PASSWORD_HASH"), TestClient(create_app()):
        pass
    get_settings.cache_clear()
