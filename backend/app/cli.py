"""Command-line entry point: ``uv run python -m app.cli <command>``."""

import argparse
import getpass

from app.auth.passwords import hash_password


def _hash_password(_: argparse.Namespace) -> int:
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Repeat password: "):
        print("Passwords do not match.")
        return 1
    print(hash_password(password))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("hash-password", help="print a bcrypt hash for APP_PASSWORD_HASH").set_defaults(
        handler=_hash_password
    )
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
