from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.providers import ModelOption, available_models
from app.auth.routes import require_user
from app.deps import get_settings
from app.settings import Settings

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(require_user)])


@router.get("/providers")
def list_models(settings: Annotated[Settings, Depends(get_settings)]) -> list[ModelOption]:
    """The AI options for the selector (one per Groq model)."""
    return available_models(settings)
