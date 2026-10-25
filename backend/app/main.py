from fastapi import APIRouter, FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="CAGE Market Accessibility API")
    api = APIRouter(prefix="/api")

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api)
    return app


app = create_app()
