from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth.passwords import hash_password
from app.deps import get_settings
from app.main import create_app
from app.settings import Settings

PASSWORD = "correct horse"
_PASSWORD_HASH = hash_password(PASSWORD, rounds=4)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        app_username="admin",
        app_password_hash=_PASSWORD_HASH,
        secret_key="test-secret",
        trust_proxy=False,
        cookie_secure=False,  # TestClient talks plain http, so Secure cookies would not be sent
        db_path=tmp_path / "app.sqlite",
        config_dir=Path("config"),
        data_dir=Path("data"),
        llm_provider=None,
        llm_api_key=None,
        llm_model=None,
    )


def make_client(settings: Settings) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return make_client(settings)


@pytest.fixture
def proxy_client(settings: Settings) -> TestClient:
    return make_client(replace(settings, trust_proxy=True))


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    response = client.post("/api/auth/login", json={"username": "admin", "password": PASSWORD})
    assert response.status_code == 204
    return client
