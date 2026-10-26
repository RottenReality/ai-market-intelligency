from pathlib import Path

import pytest

from app.profile.countries import ConfigError, load_countries


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "countries.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_load_countries_keys_by_upper_iso3(tmp_path):
    path = write(
        tmp_path,
        "countries:\n"
        "  - {iso3: col, name: Colombia, languages: [es], business_timezone: America/Bogota}\n",
    )
    countries = load_countries(path)
    assert list(countries) == ["COL"]
    assert countries["COL"].name == "Colombia"
    assert countries["COL"].languages == ["es"]
    assert countries["COL"].business_timezone == "America/Bogota"


def test_duplicate_iso3_raises_config_error(tmp_path):
    entry = "  - {iso3: COL, name: Colombia, languages: [es], business_timezone: America/Bogota}\n"
    path = write(tmp_path, "countries:\n" + entry + entry)
    with pytest.raises(ConfigError, match="COL"):
        load_countries(path)


def test_missing_field_names_the_field(tmp_path):
    path = write(tmp_path, "countries:\n  - {iso3: COL, name: Colombia, languages: [es]}\n")
    with pytest.raises(ConfigError, match="business_timezone"):
        load_countries(path)


def test_repository_countries_config_loads():
    countries = load_countries(Path("config/countries.yaml"))
    assert "COL" in countries
