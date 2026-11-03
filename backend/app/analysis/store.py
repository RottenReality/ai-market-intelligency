"""Saved AI analyses: one per subject (a country, or a set of compared countries)."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

Kind = Literal["country", "comparison"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    kind       TEXT NOT NULL,
    subject    TEXT NOT NULL,
    cache_key  TEXT NOT NULL,
    provider   TEXT NOT NULL,
    model      TEXT NOT NULL,
    content    TEXT NOT NULL,
    flagged    INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    overstated INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (kind, subject)
)
"""


class StoredAnalysis(BaseModel):
    kind: Kind
    subject: str
    cache_key: str  # hash of the data + profile it was written from; differs => outdated
    provider: str
    model: str
    content: dict
    flagged: bool
    created_at: str
    overstated: bool = False  # wording guard: a share of users still called a preference


class AnalysisStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("DROP TABLE IF EXISTS explanations")  # replaced by this table
            conn.execute(_SCHEMA)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(analyses)")}
            if "overstated" not in columns:  # databases created before the wording guard
                conn.execute(
                    "ALTER TABLE analyses ADD COLUMN overstated INTEGER NOT NULL DEFAULT 0"
                )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            yield conn

    def get(self, kind: Kind, subject: str) -> StoredAnalysis | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT cache_key, provider, model, content, flagged, created_at, overstated "
                "FROM analyses WHERE kind = ? AND subject = ?",
                (kind, subject),
            ).fetchone()
        if row is None:
            return None
        cache_key, provider, model, content, flagged, created_at, overstated = row
        return StoredAnalysis(
            kind=kind, subject=subject, cache_key=cache_key, provider=provider, model=model,
            content=json.loads(content), flagged=bool(flagged), created_at=created_at,
            overstated=bool(overstated),
        )

    def put(self, analysis: StoredAnalysis) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO analyses (kind, subject, cache_key, provider, model, "
                "content, flagged, created_at, overstated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (analysis.kind, analysis.subject, analysis.cache_key, analysis.provider,
                 analysis.model, json.dumps(analysis.content, ensure_ascii=False),
                 int(analysis.flagged), analysis.created_at, int(analysis.overstated)),
            )
