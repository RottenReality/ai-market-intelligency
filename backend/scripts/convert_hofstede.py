"""Convert the original Hofstede 6-D file to data/hofstede.csv with ISO3 codes.

Source: https://geerthofstede.com/research-and-vsm/dimension-data-matrix/ (Cultures and
Organizations, 3rd ed., 2010). "Researchers can use them without asking for permission.
Those who are considering commercial use should contact us."

Run from backend/:  uv run --with pycountry python -m scripts.convert_hofstede
Regions and sub-national groups (e.g. "Arab countries", "Belgium French") are dropped.
"""

import csv
from pathlib import Path

import pycountry

SOURCE = Path("data/raw/hofstede-6-dimensions-2015-08-16.csv")
TARGET = Path("data/hofstede.csv")
DIMENSIONS = {"pdi": "pdi", "idv": "idv", "mas": "mas", "uai": "uai", "ltowvs": "lto", "ivr": "ivr"}

NOT_COUNTRIES = {"AFE", "AFW", "ARA", "BEF", "BEN", "CAF", "GEE", "SAW", "SWF", "SWG"}
NAME_OVERRIDES = {
    "Bosnia": "BIH", "Czech Rep": "CZE", "Dominican Rep": "DOM", "Great Britain": "GBR",
    "Iran": "IRN", "Korea South": "KOR", "Kyrgyz Rep": "KGZ", "Macedonia Rep": "MKD",
    "Moldova": "MDA", "Russia": "RUS", "Slovak Rep": "SVK", "Taiwan": "TWN", "Tanzania": "TZA",
    "Turkey": "TUR", "U.S.A.": "USA", "Venezuela": "VEN", "Vietnam": "VNM",
}


def iso3_for(name: str) -> str:
    if name in NAME_OVERRIDES:
        return NAME_OVERRIDES[name]
    return pycountry.countries.lookup(name).alpha_3


def main() -> None:
    rows = list(csv.DictReader(SOURCE.read_text(encoding="utf-8").splitlines(), delimiter=";"))
    out = []
    for row in rows:
        if row["ctr"] in NOT_COUNTRIES:
            continue
        values = {new: ("" if row[old] == "#NULL!" else row[old]) for old, new in DIMENSIONS.items()}
        out.append({"iso3": iso3_for(row["country"]), "country": row["country"], **values})
    codes = [r["iso3"] for r in out]
    assert len(codes) == len(set(codes)), "duplicate ISO3 codes after conversion"
    with TARGET.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["iso3", "country", *DIMENSIONS.values()])
        writer.writeheader()
        writer.writerows(sorted(out, key=lambda r: r["iso3"]))
    print(f"wrote {len(out)} countries to {TARGET}")


if __name__ == "__main__":
    main()
