from pathlib import Path

import pytest
from pydantic import ValidationError

from app.profile.company import load_profile
from app.profile.store import ProfileEdits, ProfileStore, effective_profile

VALID = {
    "name": "Real Co.",
    "description": "Restaurant marketing.",
    "supported_languages": ["en"],
    "channels": ["sms"],
}


def test_save_then_get_round_trips_unicode_and_newlines(tmp_path):
    store = ProfileStore(tmp_path / "app.sqlite")
    text = 'Restaurantes en Bogotá – "premium"\nSegunda línea'
    edits = ProfileEdits(**{**VALID, "description": text})
    store.save(edits)
    assert store.get() == edits
    assert store.get().description == text


def test_get_without_edits_returns_none(tmp_path):
    assert ProfileStore(tmp_path / "app.sqlite").get() is None


def test_clear_removes_edits(tmp_path):
    store = ProfileStore(tmp_path / "app.sqlite")
    store.save(ProfileEdits(**VALID))
    store.clear()
    assert store.get() is None


def test_effective_profile_keeps_home_fields_from_file():
    file_profile = load_profile(Path("config"))
    edits = ProfileEdits(**{**VALID, "supported_languages": ["en", "es"], "channels": ["whatsapp"]})
    effective = effective_profile(file_profile, edits)
    assert effective.name == "Real Co."
    assert effective.description_md == "Restaurant marketing."
    assert effective.supported_languages == ["en", "es"]
    assert effective.channels == ["whatsapp"]
    assert effective.home_country == file_profile.home_country
    assert effective.home_timezone == file_profile.home_timezone


def test_effective_profile_without_edits_is_the_file_profile():
    file_profile = load_profile(Path("config"))
    assert effective_profile(file_profile, None) == file_profile


@pytest.mark.parametrize(
    "change",
    [
        {"name": "   "},
        {"name": "x" * 121},
        {"description": "x" * 4001},
        {"supported_languages": []},
        {"supported_languages": ["xx"]},
        {"channels": []},
        {"channels": ["fax"]},
    ],
)
def test_invalid_edits_are_rejected(change):
    with pytest.raises(ValidationError):
        ProfileEdits(**{**VALID, **change})


def test_edits_are_normalised():
    edits = ProfileEdits(**{**VALID, "name": "  Real Co.  ", "supported_languages": ["es", "es", "en"]})
    assert edits.name == "Real Co."
    assert edits.supported_languages == ["es", "en"]
