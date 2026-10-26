import hmac
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from app.auth.client_ip import client_ip
from app.auth.passwords import verify_password
from app.auth.sessions import SESSION_MAX_AGE, create_token, read_token
from app.deps import get_settings
from app.settings import Settings

COOKIE_NAME = "session"
SettingsDep = Annotated[Settings, Depends(get_settings)]

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str
    password: str


def require_user(request: Request, settings: SettingsDep) -> str:
    token = request.cookies.get(COOKIE_NAME)
    username = read_token(token, settings.secret_key, now=time.time()) if token else None
    if username is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return username


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
def login(body: LoginIn, request: Request, response: Response, settings: SettingsDep) -> None:
    throttle = request.app.state.throttle
    ip = client_ip(request, settings.trust_proxy)
    now = time.time()
    if throttle.is_blocked(ip, now):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many failed attempts. Try again in 15 minutes."
        )
    username_ok = hmac.compare_digest(body.username.encode(), settings.app_username.encode())
    password_ok = verify_password(body.password, settings.app_password_hash)
    if not (username_ok and password_ok):
        throttle.record_failure(ip, now)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    throttle.reset(ip)
    response.set_cookie(
        COOKIE_NAME,
        create_token(settings.app_username, settings.secret_key, now=now),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_user)])
def logout(response: Response, settings: SettingsDep) -> None:
    response.delete_cookie(
        COOKIE_NAME, path="/", httponly=True, samesite="lax", secure=settings.cookie_secure
    )


@router.get("/me")
def me(username: Annotated[str, Depends(require_user)]) -> dict[str, str]:
    return {"username": username}
