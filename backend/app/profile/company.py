import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from app.profile.countries import require_fields

PROFILE_FIELDS = ("name", "home_country", "home_timezone", "supported_languages", "channels")


@dataclass(frozen=True)
class CompanyProfile:
    name: str
    home_country: str
    home_timezone: str
    supported_languages: list[str]
    channels: list[str]
    description_md: str


def load_profile(config_dir: Path) -> CompanyProfile:
    """Load the private profile (company.yaml/.md) if present, else the committed example."""
    stem = "company" if (config_dir / "company.yaml").exists() else "company.example"
    yaml_path = config_dir / f"{stem}.yaml"
    md_path = config_dir / f"{stem}.md"
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    require_fields(data, PROFILE_FIELDS, yaml_path.name)
    return CompanyProfile(
        name=str(data["name"]),
        home_country=str(data["home_country"]).upper(),
        home_timezone=str(data["home_timezone"]),
        supported_languages=[str(lang) for lang in data["supported_languages"]],
        channels=[str(channel).lower() for channel in data["channels"]],
        description_md=md_path.read_text(encoding="utf-8").strip() if md_path.exists() else "",
    )


def profile_hash(profile: CompanyProfile) -> str:
    return hashlib.sha256(json.dumps(asdict(profile), sort_keys=True).encode()).hexdigest()
