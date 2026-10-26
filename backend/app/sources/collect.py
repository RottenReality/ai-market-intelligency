"""Collect raw evidence for a country and store it. Failures never erase stored values."""

from dataclasses import dataclass, field

import httpx2

from app.evidence.store import EvidenceStore
from app.profile.company import CompanyProfile
from app.profile.countries import Country
from app.settings import Settings
from app.sources.worldbank import WB_METRICS, WorldBankError, fetch_latest


@dataclass
class CollectReport:
    stored: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)  # the source has no data for this metric
    failed: list[tuple[str, str]] = field(default_factory=list)  # (key, reason)

    def merge(self, other: "CollectReport") -> None:
        self.stored += other.stored
        self.missing += other.missing
        self.failed += other.failed


def collect_country(
    iso3: str,
    *,
    client: httpx2.Client,
    store: EvidenceStore,
    settings: Settings | None = None,
    profile: CompanyProfile | None = None,
    countries: dict[str, Country] | None = None,
) -> CollectReport:
    iso3 = iso3.upper()
    report = CollectReport()
    records = []
    for metric in WB_METRICS:
        key = f"{iso3}:{metric}"
        try:
            record = fetch_latest(client, iso3, metric)
        except (httpx2.HTTPError, WorldBankError) as error:
            report.failed.append((key, str(error)))
            continue
        if record is None:
            report.missing.append(key)
        else:
            records.append(record)
            report.stored.append(key)
    store.upsert(records)
    return report
