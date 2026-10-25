"""World Bank Indicators API v2 client: latest non-empty value per country and indicator."""

from dataclasses import dataclass
from datetime import UTC, datetime

import httpx2

from app.evidence.models import EvidenceRecord

BASE_URL = "https://api.worldbank.org/v2"


@dataclass(frozen=True)
class WBIndicator:
    code: str
    unit: str
    source: int | None = None  # some series (e.g. WGI) live in a non-default source


WB_METRICS: dict[str, WBIndicator] = {
    "regulatory_quality": WBIndicator("GOV_WGI_RQ.EST", "index", source=3),
    "internet_pct": WBIndicator("IT.NET.USER.ZS", "%"),
    "gni_ppp_per_capita": WBIndicator("NY.GNP.PCAP.PP.CD", "USD"),
    "urban_population": WBIndicator("SP.URB.TOTL", "people"),
    "inflation_pct": WBIndicator("FP.CPI.TOTL.ZG", "%"),
}


class WorldBankError(RuntimeError):
    pass


def indicator_url(iso3: str, code: str, source: int | None) -> str:
    url = f"{BASE_URL}/country/{iso3}/indicator/{code}?format=json&mrnev=1"
    return f"{url}&source={source}" if source else url


def fetch_latest(client: httpx2.Client, iso3: str, metric: str) -> EvidenceRecord | None:
    """Return the most recent non-empty value, or None when the World Bank has no data."""
    iso3 = iso3.upper()
    indicator = WB_METRICS[metric]
    url = indicator_url(iso3, indicator.code, indicator.source)
    response = client.get(url, timeout=30)
    response.raise_for_status()
    body = response.json()

    if isinstance(body, list) and body and isinstance(body[0], dict) and "message" in body[0]:
        details = "; ".join(m.get("value", "") for m in body[0]["message"])
        raise WorldBankError(f"World Bank rejected {indicator.code} for {iso3}: {details}")
    if not isinstance(body, list) or len(body) < 2 or not body[1]:
        return None
    row = body[1][0]
    if row.get("value") is None:
        return None
    return EvidenceRecord(
        country=iso3,
        metric=metric,
        value=float(row["value"]),
        unit=indicator.unit,
        year=int(row["date"]) if str(row.get("date", "")).isdigit() else None,
        source_name="World Bank",
        source_url=url,
        retrieved_at=datetime.now(UTC).isoformat(timespec="seconds"),
        method="api",
    )
