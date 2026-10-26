"""Command-line entry point: ``uv run python -m app.cli <command>``."""

import argparse
import getpass

import httpx2

from app.auth.passwords import hash_password
from app.evidence.store import EvidenceStore
from app.profile.company import load_profile
from app.profile.countries import load_countries
from app.settings import load_settings
from app.sources.collect import CollectReport, collect_country


def _hash_password(_: argparse.Namespace) -> int:
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Repeat password: "):
        print("Passwords do not match.")
        return 1
    print(hash_password(password))
    return 0


def _collect(args: argparse.Namespace) -> int:
    settings = load_settings()
    profile = load_profile(settings.config_dir)
    countries = load_countries(settings.config_dir / "countries.yaml")
    if args.all:
        targets = [*countries, profile.home_country]
    else:
        targets = [args.country.upper()]
        if targets[0] not in countries and targets[0] != profile.home_country:
            print(f"Unknown country {targets[0]}: add it to config/countries.yaml first.")
            return 2
    store = EvidenceStore(settings.db_path)
    report = CollectReport()
    with httpx2.Client() as client:
        for iso3 in dict.fromkeys(targets):
            report.merge(collect_country(iso3, client=client, store=store, settings=settings,
                                         profile=profile, countries=countries))
    print(f"Stored {len(report.stored)} values in {settings.db_path}.")
    for key in report.missing:
        print(f"  no data at source: {key}")
    for key, reason in report.failed:
        print(f"  FAILED {key}: {reason}")
    return 1 if report.failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("hash-password", help="print a bcrypt hash for APP_PASSWORD_HASH").set_defaults(
        handler=_hash_password
    )
    collect = commands.add_parser("collect", help="fetch and store evidence for countries")
    target = collect.add_mutually_exclusive_group(required=True)
    target.add_argument("--country", help="ISO3 code, e.g. COL")
    target.add_argument("--all", action="store_true", help="all configured countries + home")
    collect.set_defaults(handler=_collect)
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
