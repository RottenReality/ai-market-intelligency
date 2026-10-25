from fastapi import APIRouter, FastAPI

from app.auth.routes import router as auth_router
from app.auth.throttle import LoginThrottle


def create_app() -> FastAPI:
    app = FastAPI(title="CAGE Market Accessibility API")
    app.state.throttle = LoginThrottle()
    api = APIRouter(prefix="/api")

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    api.include_router(auth_router)
    app.include_router(api)
    return app


app = create_app()
