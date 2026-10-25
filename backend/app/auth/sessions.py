from itsdangerous import BadSignature, URLSafeSerializer

SESSION_MAX_AGE = 8 * 3600
_SALT = "session"


def create_token(username: str, secret: str, now: float) -> str:
    return URLSafeSerializer(secret, salt=_SALT).dumps({"u": username, "iat": int(now)})


def read_token(token: str, secret: str, now: float) -> str | None:
    try:
        payload = URLSafeSerializer(secret, salt=_SALT).loads(token)
    except BadSignature:
        return None
    if not isinstance(payload, dict):
        return None
    username, issued_at = payload.get("u"), payload.get("iat")
    if not isinstance(username, str) or not isinstance(issued_at, int):
        return None
    if now - issued_at > SESSION_MAX_AGE:
        return None
    return username
