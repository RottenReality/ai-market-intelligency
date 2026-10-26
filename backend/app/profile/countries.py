from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Country:
    iso3: str
    name: str
    languages: list[str]
    business_timezone: str


COUNTRY_FIELDS = ("iso3", "name", "languages", "business_timezone")


def require_fields(entry: dict[str, Any], fields: tuple[str, ...], where: str) -> None:
    missing = [field for field in fields if entry.get(field) in (None, "", [])]
    if missing:
        raise ConfigError(f"{where}: missing field(s) {', '.join(missing)}")


def load_countries(path: Path) -> dict[str, Country]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    countries: dict[str, Country] = {}
    for index, entry in enumerate(data.get("countries", []), start=1):
        require_fields(entry, COUNTRY_FIELDS, f"{path.name} entry {index}")
        iso3 = str(entry["iso3"]).upper()
        if iso3 in countries:
            raise ConfigError(f"{path.name}: duplicate country {iso3}")
        countries[iso3] = Country(
            iso3=iso3,
            name=str(entry["name"]),
            languages=[str(lang) for lang in entry["languages"]],
            business_timezone=str(entry["business_timezone"]),
        )
    return countries
