from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.ai.routes import router as ai_router
from app.analysis.routes import router as analysis_router
from app.auth.routes import router as auth_router
from app.auth.throttle import LoginThrottle
from app.comparison.routes import router as comparison_router
from app.deps import get_settings
from app.profile.routes import router as profile_router
from app.reports.routes import router as reports_router
from app.scoring.routes import router as scoring_router


@asynccontextmanager
async def _check_settings(app: FastAPI) -> AsyncIterator[None]:
    """Fail at startup with a clear message instead of a 500 on every request."""
    app.dependency_overrides.get(get_settings, get_settings)()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="CAGE Market Accessibility API", lifespan=_check_settings)
    app.state.throttle = LoginThrottle()
    api = APIRouter(prefix="/api")

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    api.include_router(auth_router)
    api.include_router(scoring_router)
    api.include_router(comparison_router)
    api.include_router(analysis_router)
    api.include_router(reports_router)
    api.include_router(profile_router)
    api.include_router(ai_router)
    app.include_router(api)
    return app


app = create_app()
