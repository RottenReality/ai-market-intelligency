from pathlib import Path

import pytest

from app.profile.company import load_profile, profile_hash
from app.profile.countries import ConfigError

EXAMPLE_YAML = """name: Example Co.
home_country: usa
home_timezone: America/Los_Angeles
supported_languages: [en]
channels: [sms, email]
"""


def make_dir(tmp_path: Path, *, example=EXAMPLE_YAML, real=None, real_md=None) -> Path:
    (tmp_path / "company.example.yaml").write_text(example, encoding="utf-8")
    (tmp_path / "company.example.md").write_text("Example description.", encoding="utf-8")
    if real is not None:
        (tmp_path / "company.yaml").write_text(real, encoding="utf-8")
    if real_md is not None:
        (tmp_path / "company.md").write_text(real_md, encoding="utf-8")
    return tmp_path


def test_example_profile_loads_when_no_real_profile(tmp_path):
    profile = load_profile(make_dir(tmp_path))
    assert profile.name == "Example Co."
    assert profile.home_country == "USA"
    assert profile.supported_languages == ["en"]
    assert profile.channels == ["sms", "email"]
    assert profile.description_md == "Example description."


def test_real_profile_overrides_example(tmp_path):
    real = EXAMPLE_YAML.replace("Example Co.", "Real Co.")
    profile = load_profile(make_dir(tmp_path, real=real, real_md="Real description."))
    assert profile.name == "Real Co."
    assert profile.description_md == "Real description."


def test_profile_missing_home_country_names_the_field(tmp_path):
    broken = EXAMPLE_YAML.replace("home_country: usa\n", "")
    with pytest.raises(ConfigError, match="home_country"):
        load_profile(make_dir(tmp_path, example=broken))


def test_profile_hash_changes_when_description_changes(tmp_path):
    first = profile_hash(load_profile(make_dir(tmp_path, real=EXAMPLE_YAML, real_md="One.")))
    second = profile_hash(load_profile(make_dir(tmp_path, real=EXAMPLE_YAML, real_md="Two.")))
    assert first != second


def test_repository_example_profile_loads():
    profile = load_profile(Path("config"))
    assert profile.home_country == "USA"
