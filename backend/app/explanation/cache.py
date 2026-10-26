import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

from pydantic import BaseModel

_SCHEMA = """
CREATE TABLE IF NOT EXISTS explanations (
    iso3       TEXT NOT NULL,
    cache_key  TEXT NOT NULL,
    text       TEXT NOT NULL,
    flagged    INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (iso3, cache_key)
)
"""


class Explanation(BaseModel):
    iso3: str
    text: str
    flagged: bool
    created_at: str


class ExplanationCache:
    """Explanations keyed by country + a hash of the data and profile they were written from."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(_SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            yield conn

    def get(self, iso3: str, key: str) -> Explanation | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT text, flagged, created_at FROM explanations "
                "WHERE iso3 = ? AND cache_key = ?",
                (iso3, key),
            ).fetchone()
        if row is None:
            return None
        return Explanation(iso3=iso3, text=row[0], flagged=bool(row[1]), created_at=row[2])

    def put(self, key: str, explanation: Explanation) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO explanations VALUES (?, ?, ?, ?, ?)",
                (explanation.iso3, key, explanation.text, int(explanation.flagged),
                 explanation.created_at),
            )
