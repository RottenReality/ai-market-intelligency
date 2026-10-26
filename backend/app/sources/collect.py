"""Collect raw evidence for a country and store it. Failures never erase stored values."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx2

from app.evidence.models import EvidenceRecord
from app.evidence.store import EvidenceStore
from app.profile.company import CompanyProfile
from app.profile.countries import Country
from app.settings import Settings
from app.sources.hofstede import (
    HOFSTEDE_SOURCE_URL,
    dimension_variances,
    kogut_singh,
    load_hofstede,
)
from app.sources.manual import ManualInputError, load_manual_inputs
from app.sources.timezone import max_hour_difference
from app.sources.worldbank import WB_METRICS, WorldBankError, fetch_latest

IANA_URL = "https://www.iana.org/time-zones"


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
    if settings is not None and profile is not None and countries is not None:
        records += _manual(iso3, settings, report)
        if iso3 != profile.home_country and iso3 in countries:
            records += _computed(iso3, settings, profile, countries[iso3], report)
    store.upsert(records)
    return report


def _now() -> datetime:
    return datetime.now(UTC)


def _manual(iso3: str, settings: Settings, report: CollectReport) -> list[EvidenceRecord]:
    path = settings.data_dir / "manual_inputs.csv"
    if not path.exists():
        return []
    try:
        records = [r for r in load_manual_inputs(path) if r.country == iso3]
    except ManualInputError as error:
        report.failed.append((f"{iso3}:manual_inputs", "; ".join(error.errors)))
        return []
    report.stored += [f"{iso3}:{r.metric}" for r in records]
    return records


def _computed(
    iso3: str, settings: Settings, profile: CompanyProfile, country: Country,
    report: CollectReport,
) -> list[EvidenceRecord]:
    now = _now()
    stamp = now.isoformat(timespec="seconds")
    records = [
        EvidenceRecord(
            iso3, "max_hour_diff_home",
            max_hour_difference(country.business_timezone, profile.home_timezone, now.year),
            "hours", now.year, f"IANA time zone database ({country.business_timezone} vs "
            f"{profile.home_timezone})", IANA_URL, stamp, "computed",
        )
    ]
    report.stored.append(f"{iso3}:max_hour_diff_home")

    hofstede = load_hofstede(settings.data_dir / "hofstede.csv")
    distance = None
    if iso3 in hofstede and profile.home_country in hofstede:
        distance = kogut_singh(
            hofstede[iso3], hofstede[profile.home_country], dimension_variances(hofstede)
        )
    if distance is None:
        report.missing.append(f"{iso3}:kogut_singh")
    else:
        records.append(
            EvidenceRecord(
                iso3, "kogut_singh", distance, "index", 2015,
                f"Hofstede 6-D scores, Kogut-Singh vs {profile.home_country}",
                HOFSTEDE_SOURCE_URL, stamp, "computed",
            )
        )
        report.stored.append(f"{iso3}:kogut_singh")
    return records
