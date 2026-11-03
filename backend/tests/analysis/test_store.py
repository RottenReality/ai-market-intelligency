import sqlite3

from app.analysis.store import AnalysisStore, StoredAnalysis


def stored(subject="COL", provider="groq", key="k1") -> StoredAnalysis:
    return StoredAnalysis(
        kind="country", subject=subject, cache_key=key, provider=provider, model="m",
        content={"executive_summary": "x"}, flagged=False, created_at="2026-11-01T10:00:00+00:00",
    )


def test_put_then_get(tmp_path):
    store = AnalysisStore(tmp_path / "app.sqlite")
    store.put(stored())
    assert store.get("country", "COL") == stored()
    assert store.get("comparison", "COL") is None


def test_put_replaces_previous_subject(tmp_path):
    store = AnalysisStore(tmp_path / "app.sqlite")
    store.put(stored(provider="groq"))
    store.put(stored(provider="groq", key="k2"))
    latest = store.get("country", "COL")
    assert (latest.provider, latest.cache_key) == ("groq", "k2")


def test_old_explanations_table_is_dropped(tmp_path):
    db = tmp_path / "app.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE explanations (iso3 TEXT)")
    AnalysisStore(db)
    with sqlite3.connect(db) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master")}
    assert "explanations" not in tables
    assert "analyses" in tables


def test_wording_mark_is_saved(tmp_path):
    store = AnalysisStore(tmp_path / "app.sqlite")
    store.put(stored().model_copy(update={"overstated": True}))
    assert store.get("country", "COL").overstated is True


def test_database_from_before_the_wording_mark_still_works(tmp_path):
    db = tmp_path / "app.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TABLE analyses (kind TEXT NOT NULL, subject TEXT NOT NULL, cache_key TEXT "
            "NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, content TEXT NOT NULL, "
            "flagged INTEGER NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY (kind, subject))"
        )
        conn.execute("INSERT INTO analyses VALUES ('country', 'COL', 'k1', 'groq', 'm', "
                     "'{\"executive_summary\": \"x\"}', 0, '2026-11-01T10:00:00+00:00')")
    store = AnalysisStore(db)
    assert store.get("country", "COL") == stored()
    store.put(stored(subject="MEX").model_copy(update={"overstated": True}))
    assert store.get("country", "MEX").overstated is True
