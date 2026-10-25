"""Record real World Bank API responses used as test fixtures.

Run from backend/:  uv run python -m scripts.record_worldbank_fixtures
Re-run only when the API format changes; tests never touch the network.
"""

import json
from pathlib import Path

import httpx2

from app.sources.worldbank import WB_METRICS, indicator_url

OUT = Path("tests/fixtures/worldbank")

CASES = [(iso3, metric) for iso3 in ("COL", "USA") for metric in WB_METRICS]
EXTRA = {
    # A real "no data" answer: Channel Islands have no internet-users series.
    "CHI_IT.NET.USER.ZS": indicator_url("CHI", "IT.NET.USER.ZS", None),
    # A real error answer: an indicator code that does not exist.
    "COL_NOT.A.CODE": indicator_url("COL", "NOT.A.CODE", None),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    targets = {f"{iso3}_{WB_METRICS[m].code}": indicator_url(iso3, WB_METRICS[m].code,
                                                             WB_METRICS[m].source)
               for iso3, m in CASES}
    targets.update(EXTRA)
    with httpx2.Client(timeout=30) as client:
        for name, url in targets.items():
            body = client.get(url).json()
            (OUT / f"{name}.json").write_text(json.dumps(body, indent=1), encoding="utf-8")
            print("saved", name)


if __name__ == "__main__":
    main()
