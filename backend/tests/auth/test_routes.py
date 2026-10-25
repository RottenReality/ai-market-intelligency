from tests.conftest import PASSWORD

LOCKOUT = "Too many failed attempts. Try again in 15 minutes."


def login(client, password, headers=None):
    return client.post(
        "/api/auth/login", json={"username": "admin", "password": password}, headers=headers or {}
    )


def test_login_with_wrong_password_returns_401(client):
    response = login(client, "wrong")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}


def test_login_with_wrong_username_returns_401(client):
    response = client.post("/api/auth/login", json={"username": "root", "password": PASSWORD})
    assert response.status_code == 401


def test_login_success_sets_httponly_session_cookie(client):
    response = login(client, PASSWORD)
    assert response.status_code == 204
    cookie = response.headers["set-cookie"]
    assert "session=" in cookie
    assert "HttpOnly" in cookie
    assert "samesite=lax" in cookie.lower()
    assert "Max-Age=28800" in cookie


def test_protected_route_requires_session(client):
    assert client.get("/api/auth/me").status_code == 401
    login(client, PASSWORD)
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json() == {"username": "admin"}


def test_tampered_cookie_returns_401(client):
    client.cookies.set("session", "forged.value")
    assert client.get("/api/auth/me").status_code == 401


def test_sixth_failed_attempt_returns_429(client):
    for _ in range(5):
        assert login(client, "wrong").status_code == 401
    response = login(client, PASSWORD)
    assert response.status_code == 429
    assert response.json() == {"detail": LOCKOUT}


def test_trusted_proxy_throttles_each_cf_ip_separately(proxy_client):
    for _ in range(5):
        login(proxy_client, "wrong", headers={"CF-Connecting-IP": "1.1.1.1"})
    assert login(proxy_client, "wrong", headers={"CF-Connecting-IP": "1.1.1.1"}).status_code == 429
    assert login(proxy_client, PASSWORD, headers={"CF-Connecting-IP": "2.2.2.2"}).status_code == 204


def test_untrusted_proxy_ignores_cf_header(client):
    for n in range(5):
        login(client, "wrong", headers={"CF-Connecting-IP": f"10.0.0.{n}"})
    response = login(client, PASSWORD, headers={"CF-Connecting-IP": "10.0.0.99"})
    assert response.status_code == 429


def test_successful_login_resets_failures(client):
    for _ in range(4):
        login(client, "wrong")
    assert login(client, PASSWORD).status_code == 204
    for _ in range(4):
        login(client, "wrong")
    assert login(client, PASSWORD).status_code == 204


def test_logout_clears_cookie(auth_client):
    response = auth_client.post("/api/auth/logout")
    assert response.status_code == 204
    assert auth_client.get("/api/auth/me").status_code == 401


def test_health_stays_public(client):
    assert client.get("/api/health").status_code == 200


def test_non_ascii_username_is_rejected_not_crashed(client):
    response = client.post("/api/auth/login", json={"username": "andrés", "password": PASSWORD})
    assert response.status_code == 401
