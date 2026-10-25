# CAGE Market Accessibility Tool: Design Spec

- **Status:** draft v3 for review · 2026-10-25
- **Living document:** a feature branch may update this spec when it learns something. The change is committed with `docs(spec): …`.
- **Public repo rule:** no client or company names, credentials or private data in the repo. Company-specific settings live in gitignored files (see §3.3).

## 1. Purpose

A web tool that tells a **service company** (the pilot is a US restaurant-marketing company) **how accessible a foreign country is** for selling its services remotely. It uses Ghemawat's **CAGE** framework: 12 indicators → 4 dimension percentages → 1 Market Accessibility %. Results come with charts, a short AI-written explanation and a **PDF report**. Colombia is the pilot country. **Any country** can be added through config alone, with no code changes.

**Users:** a few people sharing **one generic login**.

## 2. Non-goals

Multiple users or roles · sign-up / password reset · editing the company profile in the UI · city-level analysis · custom weights in the UI · scheduled data refresh · E2E browser tests · UI translations.

## 3. The model

### 3.1 Indicators and scoring rules (all scores 0–100)

"Home" = the company's home country and time zone from the profile (pilot: USA, `America/Los_Angeles`).

| ID | Indicator | Raw input | Rule → score | Source |
|---|---|---|---|---|
| C1 | Language barrier | country languages, profile `supported_languages`, EF EPI band | any country language supported → 100; else band Very high 100 · High 75 · Moderate 50 · Low 25 · Very low 0 | config + manual |
| C2 | Channel fit (company channels vs WhatsApp) | % internet users on WhatsApp | if profile `channels` includes `whatsapp` → 100; else `100 − value` | manual (DataReportal) |
| C3 | Cultural distance from home | Hofstede 6-D scores | Kogut–Singh index `KS` vs home → `max(0, 100 − 25·KS)` | manual (Hofstede CSV) |
| A1 | Tax treaty with home | bool | yes 100 / no 0 | manual (PwC) |
| A2 | Trade agreement with home | bool | yes 100 / no 0 | manual (USTR) |
| A3 | Regulatory quality | WGI estimate (−2.5…2.5) | `(v + 2.5) / 5 · 100`, clamped | World Bank `GOV_WGI_RQ.EST` (source 3) |
| G1 | Working-hours overlap with home | country business timezone (IANA) | `(8 − maxDiffHours) / 8 · 100`, clamped. maxDiff = largest offset difference vs the home timezone over the year | computed |
| G2 | Internet users % | % | value (clamped) | World Bank `IT.NET.USER.ZS` |
| G3 | Social media users % | % | value (clamped) | manual (DataReportal) |
| E1 | Income PPP vs home | GNI per capita PPP | `min(100, country / home · 100)` | World Bank `NY.GNP.PCAP.PP.CD` |
| E2 | Market size | urban population | ≥ 10,000,000 → 100 else 0 | World Bank `SP.URB.TOTL` |
| E3 | Inflation | annual % | `100 − 5·v`, clamped (0% → 100, ≥20% → 0; deflation counts as 100) | World Bank `FP.CPI.TOTL.ZG` |

- **Dimension %** = mean of the dimension's **available** indicator scores. Each dimension also reports `available/3`.
- **Accessibility %** = mean of the four dimensions (equal 25% weights). It is computed only when all four dimensions have ≥ 1 indicator; otherwise it is `null` with the reason.
- **Missing value** = indicator `status: "missing"`. It is never treated as 0.
- Rules live in **one Python module** with one pure function per indicator. Thresholds come from a constants block, so the thesis can cite them.

### 3.2 Evidence (every number is traceable)

Each raw value is stored as: `country, indicator_id, value, unit, year, source_name, source_url, retrieved_at, method (api|manual|computed)`.

### 3.3 Company profile

| File | Committed? | Content |
|---|---|---|
| `backend/config/company.example.yaml` | yes | `name`, `home_country` (ISO3), `home_timezone`, `supported_languages`, `channels` (e.g. `[sms, email]`) for a fictional company |
| `backend/config/company.example.md` | yes | Short fictional description of the company and its services |
| `backend/config/company.yaml` / `company.md` | **no (gitignored)** | The real profile. Loaded instead of the example when present. |

- The YAML settings feed the scoring rules above. The Markdown is **only** context for the AI explanation; it never affects a score.
- Changing the profile changes the scores, so the profile's content is part of the explanation cache key.

## 4. Architecture

```
frontend/  React + TS (Vite)  ──/api (same origin via proxy)──►  backend/  FastAPI
  features/auth                               app/auth        (login, session cookie, throttle)
  features/scorecard                          app/profile     (company profile + countries.yaml)
  features/comparison                         app/sources     (World Bank client, manual CSV, timezone)
  features/explanation                        app/evidence    (SQLite store)
  features/report                             app/scoring     (pure rules → dimension/total)
                                              app/explanation (LLM port + numbers guard + cache)
                                              app/reports     (PDF builder)
                                              app/cli.py      (collect, hash-password)
```

- **Organised by module (feature), not by layer.** Each backend module owns its models, logic, routes and tests.
- **Data flow:** `uv run python -m app.cli collect --country ISO3|--all` fetches World Bank data, loads `data/manual_inputs.csv`, computes G1 and **writes evidence to SQLite**. The **API only reads** evidence and computes scores on request. Explanations are generated **on demand** (a UI button) and cached in SQLite, keyed by country + evidence hash + profile hash.
- **Countries:** `backend/config/countries.yaml` (iso3, name, languages, business_timezone). The home country is always collected, because it's the reference.
- **Same origin:** the frontend always calls relative `/api/...`. Vite's dev proxy (local) and nginx (production) forward to FastAPI, so the session cookie is first-party.
- **LLM:** a provider-agnostic port `ExplanationModel.generate(prompt) -> str`. One adapter is picked once the provider is decided (`LLM_PROVIDER` env var). Tests use a fake. The prompt contains only the scorecard payload + `company.md`.
- **Numbers guard:** every number in the generated text must match a number in the scorecard payload (after rounding). Otherwise the explanation is rejected, retried once, then returned with `flagged: true`.

### 4.1 Authentication

- One user. `APP_USERNAME`, `APP_PASSWORD_HASH` (bcrypt) and `SECRET_KEY` come from environment variables, and `.env.example` documents them. `uv run python -m app.cli hash-password` prints a hash.
- `POST /api/auth/login` verifies the credentials and sets cookie `session`: an itsdangerous-signed token that is httpOnly, `SameSite=Lax`, `Secure` in production and valid for 8 h.
- Every `/api/*` route except `/api/health` and `/api/auth/login` requires a valid session (401 otherwise).
- **Throttle:** 5 failed logins per client IP per 15 min → 429. In-memory is enough for a single instance.
  - **Client IP:** behind the Cloudflare Tunnel every request arrives from the proxy. The client IP is read from `CF-Connecting-IP`, but only when `TRUST_PROXY=true`. Otherwise `request.client.host` is used. Without this, one attacker could lock out every user.
- **CSRF:** this is enough at this scale: same-origin requests, SameSite=Lax, and state-changing routes accept only `application/json` bodies.
- **Frontend:** a login page; a protected app shell that redirects to login on 401; a logout button.

### 4.2 PDF report

- `GET /api/reports/pdf?iso3=COL,MEX,ESP` → `application/pdf`, built with **fpdf2**. Charts are rendered by **matplotlib** to PNG in memory.
- **Contents:**
  - Cover (company name, date, countries).
  - If more than one country: the ranking bar chart + radar overlay.
  - Per country: Accessibility %, dimension bars, indicator table (raw value, score, source, year) and the cached AI explanation (or "not generated").
  - Methodology note and source list.
- The PDF never triggers an LLM call; it only uses cached explanations.
- **Frontend:** an "Export PDF" button on the scorecard (one country) and on the comparison (selected countries).

### 4.3 API (v1)

| Method | Path | Auth | Returns |
|---|---|---|---|
| GET | `/api/health` | no | `{status: "ok"}` |
| POST | `/api/auth/login` | no | 204 + cookie · 401 · 429 |
| POST | `/api/auth/logout` | yes | 204, cookie cleared |
| GET | `/api/auth/me` | yes | `{username}` |
| GET | `/api/countries` | yes | configured countries (iso3, name, has_data) |
| GET | `/api/countries/{iso3}/scorecard` | yes | indicators (raw, score, status, evidence) + dimensions + accessibility |
| GET | `/api/comparison?iso3=COL,MEX` | yes | scorecard summaries for ranking/radar |
| GET | `/api/countries/{iso3}/explanation` | yes | cached explanation or 404 |
| POST | `/api/countries/{iso3}/explanation` | yes | generate (or return cached) explanation |
| GET | `/api/reports/pdf?iso3=…` | yes | PDF file |

Errors use FastAPI's default `{"detail": …}`: 404 for an unknown country, 409 for "no data collected yet" and 502 for a failed LLM call.

## 5. Tech stack

- **Backend:** Python 3.12, uv, FastAPI, pydantic, httpx2 (maintained httpx successor), PyYAML, bcrypt, itsdangerous, fpdf2, matplotlib, stdlib `sqlite3` + `zoneinfo`. Tests with pytest (+ pypdf to read PDFs in tests). Lint with ruff.
- **Frontend:** Vite + React + TypeScript, React Router, Tailwind CSS + shadcn/ui, Recharts, TanStack Query. Tests with Vitest + React Testing Library.
- **CI:** GitHub Actions runs backend and frontend tests and lint on every PR.
- **Hosting (last slice): the team's own VPS** (Ubuntu 24.04, Docker), in its own Docker Compose project, isolated from other apps on the server:
  - `api`: FastAPI (uvicorn). SQLite lives on a named volume, so data and cached explanations survive restarts.
  - `web`: nginx serves the built React app and proxies `/api` to `api`.
  - `tunnel`: our own `cloudflared` container, which provides HTTPS. **No host ports are published.** Two modes, one line apart in the compose file:
    - **Quick tunnel (start):** `tunnel --url http://web:80` gives a random `trycloudflare.com` address that changes when the tunnel container restarts. Deploys restart only `api`/`web`, never `tunnel`. `scripts/tunnel-url.sh` prints the current address from the logs.
    - **Named tunnel (before sharing with the company or the jury):** `tunnel run --token $TUNNEL_TOKEN` with a cheap domain on Cloudflare, for a stable address like `market.<domain>`.
  - Secrets (`APP_PASSWORD_HASH`, `SECRET_KEY`, LLM key, tunnel token if named) live in a `.env` on the server only.
  - Data is refreshed manually with `docker compose run --rm api collect --all`. A nightly cron copies the SQLite file to a backup folder.
  - **CD:** GitHub Actions on merge to `main` builds the images and deploys over SSH (`docker compose pull && up -d`).

## 6. Testing strategy (necessary, not exhaustive)

| What | How | Why |
|---|---|---|
| Scoring rules | Table-driven unit tests per rule, including boundaries (0, clamp, missing) and the real Colombia values from the proposal | Core of the thesis. Wrong numbers mean a wrong conclusion. |
| Dimension/total aggregation | Unit tests: averages, missing indicators, `null` total | Easy to get subtly wrong |
| Company profile | Example loads; real file overrides it; invalid profile fails with a clear message | Scores depend on it |
| World Bank client | `httpx.MockTransport` fed with **recorded real responses** (saved JSON). Covers parsing, missing values, latest-year choice | No network in tests, but realistic data |
| Manual CSV loader | Small fixture CSVs: valid rows, a bad row, a duplicate | The partner edits this file by hand |
| G1 timezone | Real `zoneinfo` for Bogotá, Mexico City, Madrid | DST logic is a classic bug source |
| Evidence store | Real SQLite in a temp file: write → read → upsert | Cheap and catches SQL errors |
| Auth | TestClient: wrong password 401; correct → cookie → protected route 200; tampered/expired cookie 401; 6th failed attempt 429; with `TRUST_PROXY` two different `CF-Connecting-IP` values are throttled separately; logout clears | Security must actually work |
| API | TestClient against a seeded temp DB: status codes + payload shape | Contract between modules |
| Explanation | Fake model: prompt contains only payload numbers + profile text; guard rejects an invented number; cache hit avoids a 2nd call | Tests our logic, not the LLM |
| PDF | Generate for a seeded country, read it with pypdf: country name, Accessibility % and indicator scores appear; multi-country includes the ranking page | Checks the content, not just "a file came back" |
| Frontend | Vitest + RTL with the API module mocked: login error and success, 401 redirects to login, picker loads a scorecard, missing data shows "n/a", the explain button shows text/error, the export button requests the right URL | User-visible behaviour only |

**Not tested:** styling, shadcn internals, Recharts/matplotlib rendering details, PDF layout, the LLM's prose, config file contents.

**Rules:** write the failing test first. A test must fail for the right reason before the code is written. No tests that only assert mocks were called. No tests modified just to pass.

## 7. Workflow

- **Branches:** `main` is always green. One branch per slice: `feat/<slice>` (also `fix/…`, `docs/…`, `chore/…`).
- **Commits:** Conventional Commits with the module as scope, e.g. `test(scoring): cover E3 inflation clamp`, `feat(scoring): add inflation rule`, `feat(auth): throttle failed logins`. The TDD rhythm is visible in history: `test:` then `feat:`, plus `refactor:` when needed.
- **Merge:** open a PR per slice on GitHub. Merge with a **merge commit** once CI passes, then delete the branch.
- **Definition of done per slice:**
  - Tests are green locally and in CI.
  - The feature works in the browser.
  - The **README is updated** (setup, usage, the new feature).
  - **Docs are updated** (`docs/`) and the spec is updated if behaviour changed.
- **Docs layout:**
  - `README.md`: what it is, screenshots, quick start, env vars.
  - `docs/specs/`: this spec.
  - `docs/plans/`: implementation plans.
  - `docs/architecture.md`: C4 diagrams in Mermaid + the module map.
  - `docs/methodology.md`: the 12 indicators and rules, written for non-developers.

## 8. Slices (vertical, each one usable)

| # | Branch | User-visible result |
|---|---|---|
| 0 | `chore/walking-skeleton` | React page shows "API connected"; CI runs both suites; README quick start |
| 1 | `feat/login` | Login page; app reachable only after login; logout |
| 2 | `feat/worldbank-scorecard` | Company profile loader (E1 needs the home country) + pick a country → its 5 World Bank indicators with raw value, score and source |
| 3 | `feat/full-cage-score` | All 12 indicators (profile settings used by C1, C2, G1), 4 dimension %, Accessibility %, radar chart |
| 4 | `feat/country-comparison` | Select several countries → ranking bar chart + overlaid radar |
| 5 | `feat/ai-explanation` | "Explain" button → guarded, cached AI explanation per country |
| 6 | `feat/pdf-report` | "Export PDF" for one country or a comparison |
| 7 | `feat/deploy` | Public HTTPS URL through Cloudflare Tunnel (login-protected), auto-deploy on merge |

A separate **polishing plan** follows after slice 7.

## 9. Open items

- LLM provider (needed at slice 5).
- VPS: RAM is confirmed (≈2.5 GB available; the app needs ≈300 MB). Decide when to buy a domain for the named tunnel (slice 7 or polishing).
- Hofstede variances for Kogut–Singh: compute from the full Hofstede dataset (CSV in `data/`), confirm the academic-use terms (slice 3).
- WhatsApp % and social-media % per country come from manual DataReportal collection by the partner (slice 3).
- Comparison countries (suggested: MEX, ESP, CHL) (slice 4).
