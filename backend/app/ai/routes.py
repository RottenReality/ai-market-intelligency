from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.providers import ProviderInfo, available_providers
from app.auth.routes import require_user
from app.deps import get_settings
from app.settings import Settings

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(require_user)])


@router.get("/providers")
def list_providers(settings: Annotated[Settings, Depends(get_settings)]) -> list[ProviderInfo]:
    return available_providers(settings)
