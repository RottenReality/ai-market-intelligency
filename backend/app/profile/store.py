"""Company profile edits made in the app, stored in SQLite (never in files or git).

The edits override the editable fields of the file profile; the home country and home time
zone always come from the file because changing them needs new reference data.
"""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, field_validator

from app.profile.company import CompanyProfile

LANGUAGE_OPTIONS = ("en", "es", "pt", "fr", "de", "it")
CHANNEL_OPTIONS = ("sms", "email", "whatsapp")
MAX_NAME = 120
MAX_DESCRIPTION = 4000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS company_profile (
    id                  INTEGER PRIMARY KEY CHECK (id = 1),
    name                TEXT NOT NULL,
    description         TEXT NOT NULL,
    supported_languages TEXT NOT NULL,
    channels            TEXT NOT NULL,
    updated_at          TEXT NOT NULL
)
"""


def _choices(values: list[str], allowed: tuple[str, ...], field: str) -> list[str]:
    cleaned = list(dict.fromkeys(v.strip().lower() for v in values))
    if not cleaned:
        raise ValueError(f"choose at least one {field}")
    unknown = [v for v in cleaned if v not in allowed]
    if unknown:
        raise ValueError(f"unknown {field}: {', '.join(unknown)}")
    return cleaned


class ProfileEdits(BaseModel):
    name: str
    description: str
    supported_languages: list[str]
    channels: list[str]

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > MAX_NAME:
            raise ValueError(f"name must be 1-{MAX_NAME} characters")
        return value

    @field_validator("description")
    @classmethod
    def _description(cls, value: str) -> str:
        if len(value) > MAX_DESCRIPTION:
            raise ValueError(f"description must be at most {MAX_DESCRIPTION} characters")
        return value

    @field_validator("supported_languages")
    @classmethod
    def _languages(cls, value: list[str]) -> list[str]:
        return _choices(value, LANGUAGE_OPTIONS, "language")

    @field_validator("channels")
    @classmethod
    def _channels(cls, value: list[str]) -> list[str]:
        return _choices(value, CHANNEL_OPTIONS, "channel")


class ProfileStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(_SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            yield conn

    def get(self) -> ProfileEdits | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT name, description, supported_languages, channels "
                "FROM company_profile WHERE id = 1"
            ).fetchone()
        if row is None:
            return None
        name, description, languages, channels = row
        return ProfileEdits(
            name=name,
            description=description,
            supported_languages=json.loads(languages),
            channels=json.loads(channels),
        )

    def save(self, edits: ProfileEdits) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO company_profile VALUES (1, ?, ?, ?, ?, ?)",
                (edits.name, edits.description, json.dumps(edits.supported_languages),
                 json.dumps(edits.channels), datetime.now(UTC).isoformat(timespec="seconds")),
            )

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM company_profile")


def effective_profile(file_profile: CompanyProfile, edits: ProfileEdits | None) -> CompanyProfile:
    if edits is None:
        return file_profile
    return replace(
        file_profile,
        name=edits.name,
        description_md=edits.description,
        supported_languages=edits.supported_languages,
        channels=edits.channels,
    )
