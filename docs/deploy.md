# Deployment (VPS + Cloudflare Tunnel)

The app runs as its own Docker Compose project, **`ami`**, isolated from anything else on the server. It has three containers and **publishes no host ports**:

| Service | Image | Role |
|---|---|---|
| `api` | `backend/Dockerfile` | FastAPI. SQLite lives on the named volume `app_data` (`/data/app.sqlite`). |
| `web` | `frontend/Dockerfile` | nginx: serves the React build and forwards `/api` to `api` (same origin, so the login cookie works). |
| `tunnel` | `cloudflare/cloudflared` | Public HTTPS address. Cloudflare terminates TLS and the tunnel reaches `web` inside the Docker network. |

Production settings are fixed in `deploy/docker-compose.yml`:
- `TRUST_PROXY=true`: the login throttle reads the visitor IP from `CF-Connecting-IP`.
- `COOKIE_SECURE=true`.

## One-time server setup

Requirements: Docker with the Compose plugin and git.

```bash
git clone https://github.com/RottenReality/ai-market-intelligency.git ~/ai-market-intelligence
cd ~/ai-market-intelligence

# 1. Secrets (never committed)
cp deploy/.env.example deploy/.env
docker compose -f deploy/docker-compose.yml build api
docker compose -f deploy/docker-compose.yml run --rm api python -m app.cli hash-password
#    paste the hash into APP_PASSWORD_HASH (keep the single quotes)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # → SECRET_KEY
nano deploy/.env

# 2. Optional: the real company profile (gitignored), copied before building
#    backend/config/company.yaml and backend/config/company.md

# 3. Start and collect data
docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml run --rm api python -m app.cli collect --all

# 4. Public address
sh deploy/scripts/tunnel-url.sh
```

Check that nothing is exposed on the host: `docker compose -p ami ps` must show no `0.0.0.0:` port mappings.

## Updating

Merging into `main` deploys automatically once continuous deployment is enabled (see below). To deploy by hand:

```bash
cd ~/ai-market-intelligence
git pull --ff-only
docker compose -f deploy/docker-compose.yml up -d --build api web
```

Only `api` and `web` are rebuilt. **The `tunnel` container is left alone, so the quick-tunnel address does not change.**

## Refreshing the data

After editing `backend/data/manual_inputs.csv` (then deploy), adding a country, or changing the company profile:

```bash
docker compose -f deploy/docker-compose.yml run --rm api python -m app.cli collect --all
```

## Backups

`deploy/scripts/backup.sh` makes a consistent copy of the database in `/data/backups` and keeps the last 14. Add it to cron on the server:

```bash
crontab -e
0 3 * * * cd ~/ai-market-intelligence && sh deploy/scripts/backup.sh >> ~/ami-backup.log 2>&1
```

## Continuous deployment (GitHub Actions)

`.github/workflows/deploy.yml` runs after CI succeeds on `main` and deploys over SSH. It stays off until you enable it in the GitHub repository settings:

1. Create an SSH key pair for deployments and add the public key to the server user's `~/.ssh/authorized_keys`.
2. **Settings → Secrets and variables → Actions → Secrets:** add `VPS_HOST`, `VPS_USER` and `VPS_SSH_KEY` (the private key). Add `VPS_APP_DIR` if the app isn't in `~/ai-market-intelligence`.
3. **Settings → Secrets and variables → Actions → Variables:** add `DEPLOY_ENABLED` = `true`.

## Quick tunnel vs named tunnel

| | Quick tunnel (default) | Named tunnel |
|---|---|---|
| Address | Random `https://….trycloudflare.com` | Your own, e.g. `https://market.example.com` |
| Changes when | The `tunnel` container restarts (server reboot, Docker update) | Never |
| Needs | Nothing | A domain on Cloudflare (free plan) |
| Good for | Development and testing | Sharing with the company or the thesis jury |

To switch to a named tunnel:
1. In Cloudflare Zero Trust, go to **Networks → Tunnels → Create a tunnel** (type Cloudflared) and copy the token.
2. Add a public hostname pointing to `http://web:80`.
3. Put `TUNNEL_TOKEN=...` in `deploy/.env`.
4. In `deploy/docker-compose.yml`, replace the tunnel `command` with `tunnel --no-autoupdate run --token ${TUNNEL_TOKEN}`.
5. Run `docker compose -f deploy/docker-compose.yml up -d tunnel`.
