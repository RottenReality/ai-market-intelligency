import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from app.evidence.models import EvidenceRecord

_SCHEMA = """
CREATE TABLE IF NOT EXISTS evidence (
    country      TEXT NOT NULL,
    metric       TEXT NOT NULL,
    value        TEXT NOT NULL,  -- JSON-encoded so floats, booleans and strings survive
    unit         TEXT NOT NULL,
    year         INTEGER,
    source_name  TEXT NOT NULL,
    source_url   TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    method       TEXT NOT NULL,
    PRIMARY KEY (country, metric)
)
"""
_COLUMNS = "country, metric, value, unit, year, source_name, source_url, retrieved_at, method"


class EvidenceStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def upsert(self, records: Iterable[EvidenceRecord]) -> None:
        rows = [
            (r.country, r.metric, json.dumps(r.value), r.unit, r.year, r.source_name,
             r.source_url, r.retrieved_at, r.method)
            for r in records
        ]
        with self._connect() as conn:
            conn.executemany(
                f"INSERT OR REPLACE INTO evidence ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )

    def get_country(self, iso3: str) -> dict[str, EvidenceRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM evidence WHERE country = ?", (iso3,)
            ).fetchall()
        records = (
            EvidenceRecord(country, metric, json.loads(value), unit, year, source_name,
                           source_url, retrieved_at, method)
            for country, metric, value, unit, year, source_name, source_url, retrieved_at, method
            in rows
        )
        return {r.metric: r for r in records}

    def countries_with_data(self) -> set[str]:
        with self._connect() as conn:
            return {row[0] for row in conn.execute("SELECT DISTINCT country FROM evidence")}
