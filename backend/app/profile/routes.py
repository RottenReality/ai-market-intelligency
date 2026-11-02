from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.routes import require_user
from app.deps import get_profile_store, get_settings
from app.profile.company import CompanyProfile, load_profile
from app.profile.store import (
    CHANNEL_OPTIONS,
    LANGUAGE_OPTIONS,
    ProfileEdits,
    ProfileStore,
    effective_profile,
)
from app.settings import Settings

router = APIRouter(prefix="/profile", tags=["profile"], dependencies=[Depends(require_user)])

SettingsDep = Annotated[Settings, Depends(get_settings)]
ProfileStoreDep = Annotated[ProfileStore, Depends(get_profile_store)]


class ProfileOptions(BaseModel):
    languages: list[str]
    channels: list[str]


class ProfileOut(BaseModel):
    name: str
    description: str
    supported_languages: list[str]
    channels: list[str]
    home_country: str
    home_timezone: str
    source: Literal["saved", "file"]
    options: ProfileOptions


def _out(profile: CompanyProfile, source: Literal["saved", "file"]) -> ProfileOut:
    return ProfileOut(
        name=profile.name,
        description=profile.description_md,
        supported_languages=profile.supported_languages,
        channels=profile.channels,
        home_country=profile.home_country,
        home_timezone=profile.home_timezone,
        source=source,
        options=ProfileOptions(languages=list(LANGUAGE_OPTIONS), channels=list(CHANNEL_OPTIONS)),
    )


@router.get("")
def get_company_profile(settings: SettingsDep, store: ProfileStoreDep) -> ProfileOut:
    edits = store.get()
    profile = effective_profile(load_profile(settings.config_dir), edits)
    return _out(profile, "saved" if edits else "file")


@router.put("")
def save_company_profile(
    edits: ProfileEdits, settings: SettingsDep, store: ProfileStoreDep
) -> ProfileOut:
    store.save(edits)
    return _out(effective_profile(load_profile(settings.config_dir), edits), "saved")


@router.delete("")
def reset_company_profile(settings: SettingsDep, store: ProfileStoreDep) -> ProfileOut:
    store.clear()
    return _out(load_profile(settings.config_dir), "file")
