#!/usr/bin/env sh
# Consistent SQLite backup into the data volume (/data/backups), keeping the last 14.
# Run nightly from cron, e.g.:
#   0 3 * * * cd ~/ai-market-intelligence && sh deploy/scripts/backup.sh >> ~/ami-backup.log 2>&1
set -e
docker compose -p ami exec -T api python - <<'PY'
import sqlite3
from datetime import date
from pathlib import Path

backups = Path("/data/backups")
backups.mkdir(exist_ok=True)
target = backups / f"app-{date.today():%Y%m%d}.sqlite"
with sqlite3.connect("/data/app.sqlite") as source, sqlite3.connect(target) as copy:
    source.backup(copy)
for old in sorted(backups.glob("app-*.sqlite"))[:-14]:
    old.unlink()
print(f"backup written: {target}")
PY
