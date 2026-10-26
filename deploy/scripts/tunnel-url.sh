#!/usr/bin/env sh
# Print the current public address of the quick tunnel.
docker compose -p ami logs tunnel 2>&1 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | tail -1
