"""Build evidence for scoring tests from the real Colombia/USA values used in the proposal."""

from app.evidence.models import EvidenceRecord, EvidenceValue

COLOMBIA = {
    "regulatory_quality": -0.1973526,
    "internet_pct": 79.34543299,
    "gni_ppp_per_capita": 22250.0,
    "urban_population": 42090207.0,
    "inflation_pct": 5.14,
}
USA = {"gni_ppp_per_capita": 89490.0}


def evidence(country: str, values: dict[str, EvidenceValue]) -> dict[str, EvidenceRecord]:
    return {
        metric: EvidenceRecord(country, metric, value, "-", 2025, "World Bank",
                               f"https://example.org/{country}/{metric}",
                               "2026-10-25T00:00:00+00:00", "api")
        for metric, value in values.items()
    }
