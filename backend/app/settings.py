import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

# backend/.env, found from this file so it works from any working directory.
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
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
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"


def _flag(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes"}


def environment(
    env_file: Path | None = None, base: Mapping[str, str] | None = None
) -> dict[str, str]:
    """Values from backend/.env (when it exists) overlaid by the real environment, which wins."""
    path = env_file or ENV_FILE
    from_file = dotenv_values(path) if path.is_file() else {}
    values = {key: value for key, value in from_file.items() if value is not None}
    values.update(os.environ if base is None else base)
    return values


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    if env is None:
        env = environment()
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
        gemini_api_key=env.get("GEMINI_API_KEY") or None,
        gemini_model=env.get("GEMINI_MODEL") or "gemini-3.8-flash",
        groq_api_key=env.get("GROQ_API_KEY") or None,
        groq_model=env.get("GROQ_MODEL") or "openai/gpt-oss-120b",
    )
