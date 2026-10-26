"""httpx2 MockTransport that serves recorded World Bank responses by URL."""

import json
from pathlib import Path

import httpx2

FIXTURES = Path(__file__).parent.parent / "fixtures" / "worldbank"


def fixture_handler(request: httpx2.Request) -> httpx2.Response:
    # /v2/country/{iso3}/indicator/{code}
    parts = request.url.path.strip("/").split("/")
    iso3, code = parts[2], parts[4]
    path = FIXTURES / f"{iso3}_{code}.json"
    if not path.exists():
        return httpx2.Response(404, json={"error": f"no fixture for {iso3} {code}"})
    return httpx2.Response(200, json=json.loads(path.read_text(encoding="utf-8")))


def fixture_client(handler=fixture_handler) -> httpx2.Client:
    return httpx2.Client(transport=httpx2.MockTransport(handler))
