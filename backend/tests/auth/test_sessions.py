from app.auth.sessions import SESSION_MAX_AGE, create_token, read_token


def test_token_roundtrip_returns_username():
    token = create_token("admin", "secret", now=1000)
    assert read_token(token, "secret", now=1000) == "admin"


def test_token_with_other_secret_is_rejected():
    token = create_token("admin", "secret", now=1000)
    assert read_token(token, "other-secret", now=1000) is None


def test_tampered_token_is_rejected():
    token = create_token("admin", "secret", now=1000)
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    assert read_token(tampered, "secret", now=1000) is None


def test_garbage_token_is_rejected():
    assert read_token("not even a token", "secret", now=1000) is None


def test_token_expires_after_8_hours():
    token = create_token("admin", "secret", now=1000)
    assert SESSION_MAX_AGE == 8 * 3600
    assert read_token(token, "secret", now=1000 + SESSION_MAX_AGE) == "admin"
    assert read_token(token, "secret", now=1000 + SESSION_MAX_AGE + 1) is None
