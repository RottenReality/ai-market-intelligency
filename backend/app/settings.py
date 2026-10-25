import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

REQUIRED_VARS = ("APP_USERNAME", "APP_PASSWORD_HASH", "SECRET_KEY")


class SettingsError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    app_username: str
    app_password_hash: str
    secret_key: str
    trust_proxy: bool
    cookie_secure: bool
    db_path: Path
    config_dir: Path
    data_dir: Path
    llm_provider: str | None
    llm_api_key: str | None
    llm_model: str | None


def _flag(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes"}


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    missing = [name for name in REQUIRED_VARS if not env.get(name)]
    if missing:
        raise SettingsError(
            "Missing required environment variables: " + ", ".join(missing)
            + ". Copy backend/.env.example to backend/.env and fill them in."
        )
    return Settings(
        app_username=env["APP_USERNAME"],
        app_password_hash=env["APP_PASSWORD_HASH"],
        secret_key=env["SECRET_KEY"],
        trust_proxy=_flag(env.get("TRUST_PROXY")),
        cookie_secure=_flag(env.get("COOKIE_SECURE")),
        db_path=Path(env.get("DB_PATH", "data/app.sqlite")),
        config_dir=Path(env.get("CONFIG_DIR", "config")),
        data_dir=Path(env.get("DATA_DIR", "data")),
        llm_provider=env.get("LLM_PROVIDER") or None,
        llm_api_key=env.get("LLM_API_KEY") or None,
        llm_model=env.get("LLM_MODEL") or None,
    )
