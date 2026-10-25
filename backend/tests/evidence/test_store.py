from app.evidence.models import EvidenceRecord
from app.evidence.store import EvidenceStore


def record(metric: str, value, country: str = "COL") -> EvidenceRecord:
    return EvidenceRecord(
        country=country,
        metric=metric,
        value=value,
        unit="%",
        year=2024,
        source_name="Test source",
        source_url="https://example.org",
        retrieved_at="2026-10-25T00:00:00+00:00",
        method="api",
    )


def test_upsert_then_read_preserves_types(tmp_path):
    store = EvidenceStore(tmp_path / "app.sqlite")
    store.upsert([record("internet_pct", 79.3), record("treaty", False), record("band", "low")])
    stored = store.get_country("COL")
    assert stored["internet_pct"] == record("internet_pct", 79.3)
    assert stored["treaty"].value is False
    assert stored["band"].value == "low"


def test_upsert_replaces_existing_metric(tmp_path):
    store = EvidenceStore(tmp_path / "app.sqlite")
    store.upsert([record("internet_pct", 70.0)])
    store.upsert([record("internet_pct", 79.3)])
    assert store.get_country("COL")["internet_pct"].value == 79.3


def test_get_country_unknown_returns_empty_dict(tmp_path):
    assert EvidenceStore(tmp_path / "app.sqlite").get_country("XYZ") == {}


def test_countries_with_data(tmp_path):
    store = EvidenceStore(tmp_path / "app.sqlite")
    store.upsert([record("internet_pct", 79.3), record("internet_pct", 94.7, country="USA")])
    assert store.countries_with_data() == {"COL", "USA"}


def test_store_creates_missing_parent_directory(tmp_path):
    store = EvidenceStore(tmp_path / "nested" / "app.sqlite")
    store.upsert([record("internet_pct", 79.3)])
    assert store.get_country("COL")
