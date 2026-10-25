# CAGE Market Accessibility Tool: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A login-protected web tool that scores how accessible any country is for a company's remote services with the CAGE model (12 indicators → 4 dimensions → Accessibility %), with charts, a guarded AI explanation and a PDF report.

**Architecture:** Python FastAPI backend organised by feature module (auth, profile, sources, evidence, scoring, comparison, explanation, reports). A CLI collects evidence into SQLite; the API reads it and scores on request. A React + TypeScript frontend, also organised by feature, calls a same-origin `/api`. It is built in 8 vertical slices; each one ends with a usable feature merged into `main`.

**Tech Stack:** Python 3.12, uv, FastAPI, pydantic, httpx, PyYAML, bcrypt, itsdangerous, tzdata, fpdf2, matplotlib, pytest, pypdf, ruff · Vite, React, TypeScript, React Router, Tailwind CSS v4, shadcn/ui, Recharts, TanStack Query, Vitest, React Testing Library · GitHub Actions · Docker Compose, nginx, cloudflared.

**Spec:** `docs/specs/2026-10-25-cage-market-accessibility-design.md` (read it first; this plan argues from it).

## Global Constraints

- **Public repo:** never write the real company's name or any credential in a committed file. The real profile lives in `backend/config/company.yaml` / `company.md`, which are gitignored.
- **Scoring rules and their constants are exactly the spec's §3.1 table.** All scores are 0–100. A missing value is `None` / `"missing"`, never 0.
- **Dimension % = mean of available indicator scores. Accessibility % = mean of the 4 dimensions, or `null` with a reason if any dimension has 0 indicators.**
- Every `/api/*` route except `GET /api/health` and `POST /api/auth/login` requires a session (401 otherwise).
- Session cookie: name `session`, httpOnly, `SameSite=Lax`, `Secure` when `COOKIE_SECURE=true`, max age 8 h.
- Login throttle: 5 failures per client IP per 15 min → 429. Client IP comes from `CF-Connecting-IP` only when `TRUST_PROXY=true`.
- The LLM is provider-agnostic; no provider is named in code or docs until the team decides.
- The frontend only calls relative `/api/...`.
- No network access in tests. External HTTP is replaced by `httpx.MockTransport` with **recorded real responses**; the LLM by a fake.
- Conventional Commits with the module as scope. **Two commits per task:** the failing test as `test(scope): …` right after it fails for the right reason, then the implementation as `feat(scope): …` (each task's commit step names the `feat` message; the `test` message mirrors it). Add `refactor(scope): …` when needed. Never edit a test just to make it pass.
- Backend commands run from `backend/`; frontend commands run from `frontend/`.

## Review Focus

1. **The partner edits `manual_inputs.csv` in Spanish-locale Excel:** a UTF-8 BOM, `;` delimiter and decimal comma (`70,4`) must load the same as a plain CSV. → Task 3.1.
2. **World Bank unreachable during `collect`:** previously stored values must be kept, the other metrics still collected, and the failures reported. → Task 2.4.
3. **Session expires mid-use:** any 401 from a data query must send the user to the login page, not leave a broken screen. → Task 1.3.
4. **Non-Latin-1 characters in the PDF** (`–`, `≥`, `“ ”`, `ñ` in an explanation or country name) must render, not crash fpdf2. → Task 6.1.
5. **Lowercase or unknown country codes** (`/api/countries/col/scorecard`, `?iso3=col,xyz`): lowercase works; unknown gives 404 naming the code. → Tasks 2.5 and 4.1.

---

## How every slice runs (do this for each slice; not repeated below)

1. Start: `git switch main && git pull && git switch -c <branch>`.
2. Do the tasks in order. Each task ends green and committed.
3. Finish: update `README.md` (setup/usage for the new feature) and any `docs/` page the slice names. If behaviour differs from the spec, update the spec in the same branch (`docs(spec): …`).
4. Push the branch, open a PR to `main`, wait for CI to pass, merge with a **merge commit** and delete the branch. The GitHub CLI is optional: without it, open the PR from the link `git push` prints.
5. Manually check the slice's "Done when" line in the browser.

Before slice 0, the `docs/spec` PR (spec + this plan + `.gitignore`) must be merged.

---

## Slice 0 · `chore/walking-skeleton`

**Done when:** `uv run uvicorn app.main:app` and `npm run dev` show "API connected" in the browser, and CI is green on the PR.

### Task 0.1: Backend app with health endpoint

**Files:**
- Delete: `backend/main.py`
- Create: `backend/app/__init__.py`, `backend/app/main.py`, `backend/tests/__init__.py`, `backend/tests/test_health.py`
- Modify: `backend/pyproject.toml` (name `ai-market-intelligence-api`, description, deps)

**Interfaces:**
- Produces: `app.main.create_app() -> FastAPI`, module-level `app = create_app()`. Routers mount under `/api`.

- [ ] **Step 1:** Add dependencies: `uv add fastapi` and `uv add --dev pytest httpx ruff`. Add `[tool.pytest.ini_options] testpaths = ["tests"]` and `[tool.ruff] line-length = 100` to `pyproject.toml`.
- [ ] **Step 2: Write the failing test** `tests/test_health.py`

```python
from fastapi.testclient import TestClient
from app.main import create_app

def test_health_returns_ok():
    response = TestClient(create_app()).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 3:** Run `uv run pytest -v`. Expected: FAIL (`ModuleNotFoundError: app`).
- [ ] **Step 4:** Implement `create_app()` with `GET /api/health`.
- [ ] **Step 5:** Run `uv run pytest -v && uv run ruff check .`. Expected: 1 passed, no lint errors.
- [ ] **Step 6:** Commit: `feat(api): add app factory and health endpoint`.

### Task 0.2: Frontend scaffold showing API status

**Files:**
- Create: Vite React-TS project in `frontend/`; `frontend/src/lib/api.ts`, `frontend/src/features/health/ApiStatus.tsx`, `frontend/src/features/health/ApiStatus.test.tsx`, `frontend/src/test/setup.ts`
- Modify: `frontend/vite.config.ts`, `frontend/tsconfig.app.json`, `frontend/src/App.tsx`, `frontend/src/index.css`, `frontend/package.json`

**Interfaces:**
- Produces:
  - `ApiError extends Error { status: number; detail: string }`.
  - `apiFetch<T>(path: string, init?: RequestInit): Promise<T>`. It sends `credentials: "same-origin"` and JSON headers, throws `ApiError` on non-2xx (with `detail` from the body), and returns `undefined` for 204.
  - `getHealth(): Promise<{status: string}>` in `features/health/api.ts`.

- [ ] **Step 1:** Scaffold: `npm create vite@latest . -- --template react-ts` inside `frontend/`. Then:
  - `npm i @tanstack/react-query react-router`;
  - `npm i tailwindcss @tailwindcss/vite`;
  - `npm i -D @types/node vitest jsdom @testing-library/react @testing-library/user-event @testing-library/jest-dom`.
- [ ] **Step 2:** Configure:
  - the `@/*` alias in `tsconfig.app.json` and `vite.config.ts` (shadcn Vite guide);
  - the `tailwindcss()` plugin;
  - `@import "tailwindcss";` in `index.css`;
  - `server.proxy = { "/api": "http://localhost:8000" }`;
  - `test: { environment: "jsdom", setupFiles: "./src/test/setup.ts", globals: true }`. Import `defineConfig` from `vitest/config`.

  `setup.ts` imports `@testing-library/jest-dom/vitest`. Run `npx shadcn@latest init`, accepting the defaults. Add the script `"test": "vitest"`.
- [ ] **Step 3: Write the failing tests** `ApiStatus.test.tsx`. Mock `./api` with `vi.mock`. Wrap the component in a fresh `QueryClient` with `retry: false`.
  - `shows "API connected" when health returns ok`: `getHealth` resolves `{status: "ok"}` → `await screen.findByText("API connected")`.
  - `shows "API unreachable" when the request fails`: `getHealth` rejects → `findByText("API unreachable")`.
- [ ] **Step 4:** Run `npx vitest run src/features/health`. Expected: FAIL (module not found).
- [ ] **Step 5:** Implement `lib/api.ts`, `features/health/api.ts` and `ApiStatus` (`useQuery(["health"], getHealth)`). Render `<ApiStatus />` in `App.tsx` inside `QueryClientProvider`.
- [ ] **Step 6:** Run `npx vitest run && npm run lint && npm run build`. Expected: 2 passed, lint clean, build OK.
- [ ] **Step 7:** Commit: `feat(web): scaffold frontend with API status indicator`.

### Task 0.3: CI, line endings and docs

**Files:**
- Create: `.github/workflows/ci.yml`, `.gitattributes`, `docs/architecture.md`
- Modify: `README.md`

- [ ] **Step 1:** Write `.gitattributes` with `* text=auto eol=lf`, then run `git add --renormalize .`.
- [ ] **Step 2:** Write `ci.yml`. It triggers on `pull_request` and `push` to `main`, with two jobs:
  - `backend`: `astral-sh/setup-uv`, working dir `backend`, `uv sync --locked`, `uv run ruff check .`, `uv run pytest`.
  - `frontend`: `actions/setup-node` with Node 22 and an npm cache, working dir `frontend`, `npm ci`, `npm run lint`, `npx vitest run`, `npm run build`.
- [ ] **Step 3:** Write `README.md`: a project description (no company name), the stack, a quick start (backend `uv sync` + `uv run uvicorn app.main:app --reload`; frontend `npm i` + `npm run dev`) and how to run the tests.
- [ ] **Step 4:** Write `docs/architecture.md`: a Mermaid C4 context diagram (`C4Context`) and the module map from spec §4.
- [ ] **Step 5:** Push the branch and confirm both CI jobs pass on the PR.
- [ ] **Step 6:** Commit: `ci: run backend and frontend checks on pull requests` and `docs: add readme quick start and architecture overview`.

---

## Slice 1 · `feat/login`

**Done when:** opening the app shows a login page; correct credentials open the app; wrong ones show an error; logout returns to login; the sixth wrong attempt shows a lockout message.

### Task 1.1: Settings, password hashing, session tokens

**Files:**
- Create: `backend/app/settings.py`, `backend/app/auth/__init__.py`, `backend/app/auth/passwords.py`, `backend/app/auth/sessions.py`, `backend/app/cli.py`, `backend/.env.example`
- Test: `backend/tests/auth/test_passwords.py`, `backend/tests/auth/test_sessions.py`, `backend/tests/test_settings.py`

**Interfaces:**
- Produces:
  - `Settings` (frozen dataclass): `app_username: str`, `app_password_hash: str`, `secret_key: str`, `trust_proxy: bool`, `cookie_secure: bool`, `db_path: Path`, `config_dir: Path`, `data_dir: Path`, `llm_provider: str | None`, `llm_api_key: str | None`, `llm_model: str | None`.
  - `load_settings(env: Mapping[str, str] = os.environ) -> Settings`. Raises `SettingsError` naming every missing required var (`APP_USERNAME`, `APP_PASSWORD_HASH`, `SECRET_KEY`). Defaults: `TRUST_PROXY=false`, `COOKIE_SECURE=false`, `DB_PATH=data/app.sqlite`, `CONFIG_DIR=config`, `DATA_DIR=data`.
  - `app.deps.get_settings()`, cached and overridable in tests.
  - `hash_password(password: str) -> str` and `verify_password(password: str, hashed: str) -> bool` (bcrypt).
  - `SESSION_MAX_AGE = 8 * 3600`.
  - `create_token(username: str, secret: str, now: float) -> str` and `read_token(token: str, secret: str, now: float) -> str | None`. They use itsdangerous `URLSafeSerializer(secret, salt="session")` over `{"u": username, "iat": int(now)}`. `read_token` returns `None` for a bad signature, garbage input or `now - iat > SESSION_MAX_AGE`.

- [ ] **Step 1:** `uv add bcrypt itsdangerous`.
- [ ] **Step 2: Write the failing tests.**
  - `test_verify_password_accepts_correct_and_rejects_wrong`.
  - `test_token_roundtrip_returns_username` (`read_token(create_token("admin", "s", 1000), "s", 1000) == "admin"`).
  - `test_token_with_other_secret_is_rejected`.
  - `test_tampered_token_is_rejected` (flip one character).
  - `test_token_expires_after_8_hours` (valid at `1000 + 8*3600`, `None` at `1000 + 8*3600 + 1`).
  - `test_load_settings_lists_all_missing_required_vars` (empty env → the message contains all three names).
  - `test_load_settings_parses_booleans` (`"true"` → True).
- [ ] **Step 3:** Run `uv run pytest tests/auth tests/test_settings.py -v`. Expected: FAIL (imports).
- [ ] **Step 4:** Implement the four modules. Add `app/cli.py` with argparse subcommand `hash-password`, which prompts with `getpass` and prints `hash_password(...)`. Run it as `uv run python -m app.cli hash-password`.
- [ ] **Step 5:** Write `.env.example` with every variable from `Settings` and a comment on generating the hash and a `SECRET_KEY` (`python -c "import secrets;print(secrets.token_urlsafe(32))"`).
- [ ] **Step 6:** Run the tests. Expected: PASS.
- [ ] **Step 7:** Commit: `feat(auth): add settings, password hashing and signed session tokens`.

### Task 1.2: Login, logout, me, protection and throttle

**Files:**
- Create: `backend/app/auth/throttle.py`, `backend/app/auth/client_ip.py`, `backend/app/auth/routes.py`, `backend/app/deps.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/auth/test_throttle.py`, `backend/tests/auth/test_routes.py`, `backend/tests/conftest.py`

**Interfaces:**
- Consumes: Task 1.1.
- Produces:
  - `LoginThrottle(max_failures=5, window_seconds=900)` with `is_blocked(key: str, now: float) -> bool`, `record_failure(key: str, now: float) -> None` and `reset(key: str) -> None`. It is a sliding window over failure timestamps.
  - `client_ip(request: Request, trust_proxy: bool) -> str`.
  - `require_user(request: Request, settings = Depends(get_settings)) -> str`: a FastAPI dependency that raises 401 `{"detail": "Not authenticated"}`. All later routers use `dependencies=[Depends(require_user)]`.
  - Routes:
    - `POST /api/auth/login` takes body `LoginIn{username, password}`. It returns 204 and sets the cookie, 401 `"Invalid username or password"`, or 429 `"Too many failed attempts. Try again in 15 minutes."`.
    - `POST /api/auth/logout` returns 204 and deletes the cookie.
    - `GET /api/auth/me` returns `{username}`.
  - `conftest.py` fixtures:
    - `settings` (test values, `cookie_secure=False` because TestClient uses http, `db_path` in `tmp_path`);
    - `client` (`create_app()` with `get_settings` overridden; a fresh throttle per app);
    - `auth_client` (already logged in).
- Throttle state lives on `app.state.throttle`, created in `create_app()`.

- [ ] **Step 1: Write the failing tests.**
  - Throttle unit:
    - `test_blocks_after_five_failures_within_window`;
    - `test_failures_older_than_window_are_forgotten` (5 failures at t=0 → not blocked at t=901);
    - `test_reset_clears_failures`.
  - Routes:
    - `test_login_with_wrong_password_returns_401`;
    - `test_login_success_sets_httponly_session_cookie` (204; `set-cookie` contains `session=`, `HttpOnly`, `SameSite=lax`);
    - `test_protected_route_requires_session` (`GET /api/auth/me` without cookie → 401; with cookie → 200 `{"username": "admin"}`);
    - `test_tampered_cookie_returns_401`;
    - `test_sixth_failed_attempt_returns_429` (5×401, then the 6th, even with the correct password, → 429);
    - `test_trusted_proxy_throttles_each_cf_ip_separately` (`trust_proxy=True`: 5 failures with `CF-Connecting-IP: 1.1.1.1`, then a correct login with `CF-Connecting-IP: 2.2.2.2` → 204);
    - `test_untrusted_proxy_ignores_cf_header` (`trust_proxy=False`: failures with different CF headers share one bucket → 429 on the 6th);
    - `test_logout_clears_cookie`.
- [ ] **Step 2:** Run `uv run pytest tests/auth -v`. Expected: FAIL.
- [ ] **Step 3:** Implement the throttle, `client_ip` (CF header when trusted and present, else `request.client.host`), `require_user` (reads the `session` cookie → `read_token` with `time.time()`) and the routes. A successful login calls `throttle.reset(ip)`. A blocked IP gets 429 before the password check.
- [ ] **Step 4:** Run `uv run pytest -v`. Expected: all pass.
- [ ] **Step 5:** Commit: `feat(auth): add login, logout and session-protected routes with throttling`.

### Task 1.3: Login page, protected shell, logout, 401 handling

**Files:**
- Create: `frontend/src/features/auth/api.ts`, `LoginPage.tsx`, `AuthGate.tsx`, `AppShell.tsx`, `auth.test.tsx`; shadcn `button`, `input`, `label`, `card`
- Modify: `frontend/src/App.tsx`, `frontend/src/main.tsx`

**Interfaces:**
- Produces:
  - `login(username: string, password: string): Promise<void>`, `logout(): Promise<void>` and `getMe(): Promise<{username: string}>`.
  - Routes: `/login` → `LoginPage`. `/` → `AuthGate` → `AppShell` (header with app name, username, Logout, and an `<Outlet/>`).
  - `createQueryClient()` in `lib/queryClient.ts`. Its `QueryCache.onError` and `MutationCache.onError` set `["me"]` to `null` on `ApiError.status === 401`, so `AuthGate` redirects.

- [ ] **Step 1: Write the failing tests** (mock `./api`; render with `MemoryRouter` and the real `createQueryClient()`).
  - `wrong credentials show "Invalid username or password"` (`login` rejects `ApiError(401)`).
  - `429 shows the lockout message` (the text from Task 1.2).
  - `successful login navigates to the app shell` (then `getMe` resolves → `findByText("admin")`).
  - `visiting "/" without a session redirects to the login page` (`getMe` rejects 401 → `findByLabelText("Username")`).
  - `a 401 from any later query redirects to login`: render the shell (`getMe` resolves). Then a child test component's query rejects with `ApiError(401)` → the login form appears.
  - `logout returns to the login page`.
- [ ] **Step 2:** Run `npx vitest run src/features/auth`. Expected: FAIL.
- [ ] **Step 3:** Implement. `LoginPage` uses a shadcn `Card` form with labelled `Username` and `Password` inputs and a submit button. Move `ApiStatus` into the shell footer.
- [ ] **Step 4:** Run `npx vitest run && npm run lint`. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(auth-ui): add login page, protected shell and logout`.
- [ ] **Step 6:** In the README, document creating `.env` from `.env.example` and starting the backend with `uv run uvicorn app.main:app --reload --env-file .env`. Commit: `docs: explain local login setup`.

---

## Slice 2 · `feat/worldbank-scorecard`

**Done when:** after `uv run --env-file .env python -m app.cli collect --all`, picking Colombia shows A3, G2, E1, E2, E3 with raw value, score, source link and year.

Note: the company profile loader moves here from slice 3, because E1 needs the home country. Update spec §8 accordingly (`docs(spec): …`). The CLI runs as `python -m app.cli`; update the spec's command examples too.

### Task 2.1: Countries config and company profile

**Files:**
- Create: `backend/app/profile/__init__.py`, `countries.py`, `company.py`; `backend/config/countries.yaml`, `company.example.yaml`, `company.example.md`
- Test: `backend/tests/profile/test_countries.py`, `test_company.py`, fixtures under `backend/tests/profile/fixtures/`

**Interfaces:**
- Produces:
  - `Country(iso3: str, name: str, languages: list[str], business_timezone: str)`.
  - `load_countries(path: Path) -> dict[str, Country]`, keyed by upper-case iso3. Raises `ConfigError` for a missing field or a duplicate iso3.
  - `CompanyProfile(name, home_country, home_timezone, supported_languages: list[str], channels: list[str], description_md: str)`.
  - `load_profile(config_dir: Path) -> CompanyProfile`: `company.yaml` + `company.md` when present, else the `.example` files. Raises `ConfigError` naming missing fields.
  - `profile_hash(profile) -> str`: sha256 over the YAML fields + description.
  - `deps.get_countries()` and `deps.get_profile()`.
- `countries.yaml` starts with `COL` (Colombia, `[es]`, `America/Bogota`). The home country is not listed; it comes from the profile.
- The example profile is "Example Restaurant Marketing Co.", `USA`, `America/Los_Angeles`, `[en]`, `[sms, email]`, with a 3-sentence fictional description.

- [ ] **Step 1: Write the failing tests.**
  - `test_load_countries_keys_by_upper_iso3`.
  - `test_duplicate_iso3_raises_config_error`.
  - `test_example_profile_loads_when_no_real_profile`.
  - `test_real_profile_overrides_example` (tmp dir with both).
  - `test_profile_missing_home_country_names_the_field`.
  - `test_profile_hash_changes_when_description_changes`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** implement with PyYAML (`uv add pyyaml`). **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(profile): load countries config and company profile`.

### Task 2.2: Evidence model and SQLite store

**Files:**
- Create: `backend/app/evidence/__init__.py`, `models.py`, `store.py`
- Test: `backend/tests/evidence/test_store.py`

**Interfaces:**
- Produces:
  - `EvidenceRecord` (frozen dataclass): `country: str, metric: str, value: float | bool | str, unit: str, year: int | None, source_name: str, source_url: str, retrieved_at: str` (ISO 8601 UTC), `method: Literal["api", "manual", "computed"]`.
  - `EvidenceStore(db_path: Path)` creates its table on init: PK `(country, metric)`, `value` stored JSON-encoded. Methods: `upsert(records: Iterable[EvidenceRecord]) -> None`, `get_country(iso3: str) -> dict[str, EvidenceRecord]` and `countries_with_data() -> set[str]`.
  - `deps.get_store()`.

- [ ] **Step 1: Write the failing tests** (real SQLite in `tmp_path`).
  - `test_upsert_then_read_preserves_types` (float, bool, str survive the round trip).
  - `test_upsert_replaces_existing_metric`.
  - `test_get_country_unknown_returns_empty_dict`.
  - `test_countries_with_data`.
- [ ] **Step 2:** FAIL → **Step 3:** implement with stdlib `sqlite3` → **Step 4:** PASS.
- [ ] **Step 5:** Commit: `feat(evidence): add SQLite evidence store`.

### Task 2.3: World Bank client with recorded fixtures

**Files:**
- Create: `backend/app/sources/__init__.py`, `worldbank.py`; `backend/tests/fixtures/worldbank/*.json`; `backend/scripts/record_worldbank_fixtures.py`
- Test: `backend/tests/sources/test_worldbank.py`

**Interfaces:**
- Produces:
  - `WB_METRICS: dict[str, WBIndicator]`, where `WBIndicator(code: str, unit: str, source: int | None)`:
    - `regulatory_quality` → `GOV_WGI_RQ.EST`, `index`, source 3;
    - `internet_pct` → `IT.NET.USER.ZS`, `%`;
    - `gni_ppp_per_capita` → `NY.GNP.PCAP.PP.CD`, `USD`;
    - `urban_population` → `SP.URB.TOTL`, `people`;
    - `inflation_pct` → `FP.CPI.TOTL.ZG`, `%`.
  - `fetch_latest(client: httpx.Client, iso3: str, metric: str) -> EvidenceRecord | None`. It calls `GET https://api.worldbank.org/v2/country/{iso3}/indicator/{code}?format=json&mrnev=1` (+ `&source=3` when set). It returns `None` when the data array is null or empty, or when `value` is null. It raises `WorldBankError` when the body is a `message` error. `source_url` is the request URL.

- [ ] **Step 1:** Write `scripts/record_worldbank_fixtures.py`, which saves real responses for COL and USA × the 5 metrics, plus one real error response (an invalid code) and one real empty response (a country/indicator pair with no data). Run it once and commit the JSON files.
- [ ] **Step 2: Write the failing tests** (`httpx.MockTransport` serving the fixture by URL).
  - `test_parses_latest_value_and_year` (COL internet → `79.345…`, year 2024).
  - `test_wgi_request_includes_source_3` (assert on the captured request URL).
  - `test_empty_response_returns_none`.
  - `test_error_message_raises_worldbank_error`.
- [ ] **Step 3:** FAIL → **Step 4:** implement (`uv add httpx`; httpx moves from dev to main deps) → **Step 5:** PASS.
- [ ] **Step 6:** Commit: `feat(sources): add World Bank client with recorded fixtures`.

### Task 2.4: `collect` command

**Files:**
- Create: `backend/app/sources/collect.py`
- Modify: `backend/app/cli.py`
- Test: `backend/tests/sources/test_collect.py`

**Interfaces:**
- Consumes: 2.1–2.3.
- Produces:
  - `CollectReport(stored: list[str], failed: list[tuple[str, str]])`, holding `"COL:internet_pct"` keys and `(key, reason)` pairs.
  - `collect_country(iso3: str, *, client: httpx.Client, store: EvidenceStore, settings: Settings, profile: CompanyProfile, countries: dict[str, Country]) -> CollectReport`. Slice 2 uses only `client` and `store`; slice 3 uses the rest (data files, home timezone, Hofstede home row).
  - CLI `collect [--country ISO3 | --all]`. `--all` = every configured country + the profile's home country. It prints the report and exits with status 1 if anything failed.

- [ ] **Step 1: Write the failing tests.**
  - `test_collect_stores_all_five_metrics_for_colombia`.
  - `test_network_error_keeps_previous_value_and_reports_failure`. Pre-seed `COL:internet_pct = 70`. The transport raises `httpx.ConnectError` for that URL only. Expect: the stored value is still 70, the other 4 metrics are stored, and `failed` contains `COL:internet_pct`. **(Review Focus 2.)**
- [ ] **Step 2:** FAIL → **Step 3:** implement (catch `httpx.HTTPError` and `WorldBankError` per metric) → **Step 4:** PASS.
- [ ] **Step 5:** Commit: `feat(sources): add collect command for World Bank metrics`.

### Task 2.5: Scoring rules for World Bank indicators + scorecard API

**Files:**
- Create: `backend/app/scoring/__init__.py`, `rules.py`, `indicators.py`, `scorecard.py`, `routes.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/scoring/test_rules.py`, `test_scorecard.py`, `test_routes.py`

**Interfaces:**
- Produces:
  - Rules in `rules.py`. Each is pure, takes `None`-able inputs, returns `float | None` and clamps to 0–100:
    - `regulatory_quality(v)`;
    - `percentage(v)` (G2, G3);
    - `income_vs_home(country, home)`;
    - `market_size(urban_pop)`, with constant `MIN_URBAN_POPULATION = 10_000_000`;
    - `inflation(v)`.
  - `indicators.py`:
    - `IndicatorDef(id, dimension: Literal["C","A","G","E"], name, unit, score: Callable[[Inputs], float | None], raw_metric: str, metrics: tuple[str, ...], uses_home: bool)`;
    - `INDICATORS: list[IndicatorDef]` (this slice: A3, G2, E1, E2, E3, with the names from the spec table);
    - `Inputs(country: dict[str, EvidenceRecord], home: dict[str, EvidenceRecord], country_cfg: Country, profile: CompanyProfile)`.
  - `scorecard.py`:
    - pydantic `Source{name, url, year}`, `IndicatorResult{id, dimension, name, status: Literal["ok","missing"], score: float | None, raw: float | bool | str | None, unit, sources: list[Source]}` and `Scorecard{country: {iso3, name}, home: str, indicators: list[IndicatorResult]}`;
    - `build_scorecard(inputs: Inputs) -> Scorecard`.
  - Routes (protected):
    - `GET /api/countries` → `[{iso3, name, has_data}]`;
    - `GET /api/countries/{iso3}/scorecard` upper-cases `iso3`; returns 404 `"Unknown country: XYZ"` or 409 `"No data collected yet for Colombia"`.

- [ ] **Step 1: Write the failing tests.**
  - `test_rules.py` (parametrized; values from spec §3.1 and the proposal):
    - `regulatory_quality(-0.1973526) ≈ 46.05`, `(3.0) == 100`, `(None) is None`;
    - `percentage(79.345) ≈ 79.35`, `(120) == 100`;
    - `income_vs_home(22250, 89490) ≈ 24.86`, `(100000, 89490) == 100`, `(22250, None) is None`;
    - `market_size(42_090_207) == 100`, `(9_999_999) == 0`;
    - `inflation(5.14) ≈ 74.3`, `(25) == 0`, `(-1) == 100`.
  - `test_scorecard.py`:
    - `test_missing_metric_gives_missing_status_not_zero`;
    - `test_e1_lists_both_country_and_home_sources`.
  - `test_routes.py` (seeded store):
    - `test_scorecard_for_colombia_returns_five_indicators`;
    - `test_lowercase_iso3_works` (`/api/countries/col/scorecard` → 200) **(Review Focus 5)**;
    - `test_unknown_country_returns_404_naming_code`;
    - `test_country_without_data_returns_409`;
    - `test_scorecard_requires_session` (401).
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** run `uv run pytest -v`. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(scoring): score World Bank indicators and expose scorecard API`.

### Task 2.6: Scorecard page

**Files:**
- Create: `frontend/src/lib/types.ts`, `frontend/src/lib/format.ts` (+ `format.test.ts`), `frontend/src/features/scorecard/api.ts`, `ScorecardPage.tsx`, `CountryPicker.tsx`, `IndicatorTable.tsx`, `scorecard.test.tsx`; shadcn `select`, `table`, `badge`

**Interfaces:**
- Produces:
  - TS types mirroring the API in snake_case (`Scorecard`, `IndicatorResult`, `Source`, `CountrySummary`).
  - `formatRaw(value: number | boolean | string | null, unit: string): string`.
  - `getCountries()` and `getScorecard(iso3)`.
  - `ScorecardPage` at route `/`.

- [ ] **Step 1: Write the failing tests.**
  - `format.test.ts`:
    - `formatRaw(79.345, "%") === "79.3%"`;
    - `(22250, "USD") === "$22,250"`;
    - `(42090207, "people") === "42.1M"`;
    - `(true, "bool") === "Yes"`;
    - `(null, "%") === "n/a"`.
  - `scorecard.test.tsx`:
    - `choosing a country shows its indicators` (rows for "Regulatory quality" … with scores rounded to integers, e.g. "46");
    - `missing indicator shows n/a`;
    - `409 shows "No data collected yet for Colombia"`;
    - `source link points to the evidence URL`.
- [ ] **Step 2:** FAIL → **Step 3:** implement. The country choice lives in the URL as `?country=COL`, so it can be shared → **Step 4:** PASS.
- [ ] **Step 5:** Commit: `feat(scorecard-ui): pick a country and show World Bank indicators`.

---

## Slice 3 · `feat/full-cage-score`

**Done when:** Colombia shows all 12 indicators grouped by dimension, the 4 dimension %, Accessibility % (or the "not enough data" reason) and a radar chart. `docs/methodology.md` exists.

### Task 3.1: Manual inputs CSV loader

**Files:**
- Create: `backend/app/sources/manual.py`, `backend/data/manual_inputs.csv`
- Test: `backend/tests/sources/test_manual.py`, fixtures `tests/fixtures/manual/{valid.csv, excel_es.csv, bad_value.csv, duplicate.csv}`

**Interfaces:**
- Produces:
  - `MANUAL_METRICS`:
    - `english_band` (enum `very_high|high|moderate|low|very_low`, unit `band`);
    - `whatsapp_pct` (float 0–100, `%`);
    - `social_media_pct` (float 0–100, `%`);
    - `tax_treaty_with_home` (`yes|no` → bool);
    - `trade_agreement_with_home` (`yes|no` → bool).
  - CSV columns: `iso3,metric,value,year,source_name,source_url`.
  - `load_manual_inputs(path: Path) -> list[EvidenceRecord]` (`method="manual"`). Raises `ManualInputError(errors: list[str])` with one message per bad line, e.g. `"line 3: whatsapp_pct must be a number 0–100, got 'abc'"`.
- Seed `manual_inputs.csv` with the verified Colombia rows only: `tax_treaty_with_home=no` (PwC), `trade_agreement_with_home=yes` (USTR, 2012) and `social_media_pct=70.4` (DataReportal 2026). Other values stay missing until the partner adds them.

- [ ] **Step 1: Write the failing tests.**
  - `test_valid_file_loads_typed_values`.
  - `test_spanish_excel_export_loads_like_plain_csv`: a file with a UTF-8 BOM, `;` delimiter and `70,4` gives the same records as `valid.csv`. **(Review Focus 1.)**
  - `test_bad_value_reports_line_number`.
  - `test_duplicate_country_metric_is_an_error`.
  - `test_unknown_metric_is_an_error`.
- [ ] **Step 2:** FAIL → **Step 3:** implement. Open with `utf-8-sig`, detect the delimiter with `csv.Sniffer` limited to `,;`, and accept a decimal comma only when the delimiter is `;` → **Step 4:** PASS.
- [ ] **Step 5:** Commit: `feat(sources): load and validate manual inputs CSV`.

### Task 3.2: Hofstede distance and timezone overlap

**Files:**
- Create: `backend/app/sources/hofstede.py`, `backend/app/sources/timezone.py`, `backend/data/hofstede.csv`
- Test: `backend/tests/sources/test_hofstede.py`, `test_timezone.py`

**Interfaces:**
- Produces:
  - `load_hofstede(path) -> dict[str, dict[str, float | None]]`. The CSV columns are `iso3,pdi,idv,mas,uai,lto,ivr`; blank means missing.
  - `dimension_variances(data) -> dict[str, float]`: population variance per dimension, over countries that have it.
  - `kogut_singh(country: dict, home: dict, variances: dict) -> float | None`: the mean of `(c−h)²/V` over dimensions present in both; `None` if there are none.
  - `max_hour_difference(tz_a: str, tz_b: str, year: int) -> float`: the maximum absolute UTC-offset difference, in hours, sampled daily at 12:00 UTC.
- `collect_country` (Task 2.4) is extended. It also stores `kogut_singh` (`computed`, source "Hofstede Insights") and `max_hour_diff_home` (`computed`, source "IANA tz database"), and loads the manual CSV. Profile changes require re-running `collect` (documented).
- `hofstede.csv` holds the full Hofstede 6-D dataset with codes converted to ISO3; rows that aren't countries (e.g. regions) are dropped. Record the source URL and terms in `docs/methodology.md`.

- [ ] **Step 1:** `uv add tzdata` (Windows has no system tz database).
- [ ] **Step 2: Write the failing tests.**
  - `test_kogut_singh_hand_computed`: dataset A(pdi 40, idv 90), B(60, 30), C(80, 30); home = A → `kogut_singh(B) == 3.0`.
  - `test_kogut_singh_skips_dimensions_missing_on_either_side`.
  - `test_kogut_singh_none_when_no_common_dimension`.
  - `test_bogota_vs_los_angeles_is_3_hours` (2026).
  - `test_mexico_city_vs_los_angeles_is_2_hours`.
  - `test_madrid_vs_los_angeles_is_9_hours`.
  - `test_collect_stores_computed_metrics` (in `test_collect.py`).
- [ ] **Step 3:** FAIL → **Step 4:** implement → **Step 5:** PASS.
- [ ] **Step 6:** Commit: `feat(sources): compute Kogut-Singh distance and timezone overlap`.

### Task 3.3: Remaining rules, dimensions and Accessibility %

**Files:**
- Modify: `backend/app/scoring/rules.py`, `indicators.py`, `scorecard.py`
- Test: `backend/tests/scoring/test_rules.py`, `test_scorecard.py`, `test_routes.py`

**Interfaces:**
- Produces:
  - `language_barrier(country_languages, supported_languages, english_band) -> float | None`, using `ENGLISH_BAND_SCORES = {very_high:100, high:75, moderate:50, low:25, very_low:0}`.
  - `channel_fit(whatsapp_pct, channels) -> float | None`.
  - `cultural_distance(ks) -> float | None`, using `KS_SCORE_FACTOR = 25`.
  - `yes_no(v: bool | None) -> float | None`.
  - `hours_overlap(max_diff_hours) -> float | None`, using `WORKDAY_HOURS = 8`.
  - `INDICATORS` now holds all 12, in spec order.
  - `Dimension{id, name, score: float | None, available: int, total: int}`.
  - `Scorecard` gains `dimensions: list[Dimension]` (order C, A, G, E; names Cultural, Administrative, Geographic, Economic), `accessibility: float | None` and `accessibility_reason: str | None`.
  - `aggregate(results: list[IndicatorResult]) -> tuple[list[Dimension], float | None, str | None]`. The reason reads `"Not enough data: no indicators for Cultural"`, listing every empty dimension.

- [ ] **Step 1: Write the failing tests.**
  - Rules:
    - `language_barrier(["es"], ["en"], "low") == 25`, `(["es"], ["en","es"], None) == 100`, `(["es"], ["en"], None) is None`;
    - `channel_fit(92, ["sms","email"]) == 8`, `(None, ["sms","whatsapp"]) == 100`, `(None, ["sms"]) is None`;
    - `cultural_distance(3.0) == 25`, `(5.0) == 0`;
    - `yes_no(False) == 0`;
    - `hours_overlap(3) == 62.5`, `(9) == 0`.
  - Aggregation:
    - `test_colombia_preliminary_dimensions`: the proposal's 9 values give A ≈ 48.68, G ≈ 70.75, E ≈ 66.39, C `None` with `available == 0`; accessibility is `None` and the reason names Cultural;
    - `test_accessibility_is_mean_of_four_dimensions` (C 50, A 70, G 80, E 60 → 65);
    - `test_dimension_with_one_of_three_reports_available_1`.
  - Route: `test_scorecard_includes_dimensions_and_accessibility`.
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** PASS.
- [ ] **Step 5:** Commit: `feat(scoring): add cultural, administrative and geographic rules with aggregation`.

### Task 3.4: Full scorecard UI with radar

**Files:**
- Create: `frontend/src/features/scorecard/AccessibilitySummary.tsx`, `DimensionRadar.tsx`
- Modify: `IndicatorTable.tsx` (grouped by dimension), `ScorecardPage.tsx`, `scorecard.test.tsx`, `lib/types.ts`
- Create: `docs/methodology.md`

- [ ] **Step 1:** `npm i recharts`.
- [ ] **Step 2: Write the failing tests.**
  - `shows the accessibility percentage` (`accessibility: 61.04` → "61%").
  - `shows the not-enough-data reason when accessibility is null`.
  - `each dimension shows its available count` ("2/3 indicators").
  - `indicators are grouped under their dimension headings`.
- [ ] **Step 3:** FAIL → **Step 4:** implement. `DimensionRadar` is a Recharts `RadarChart` over the 4 dimensions; null dimensions plot as 0 with "no data" in the tooltip. A small table under it lists the values, so the chart is never the only way to read them → **Step 5:** PASS.
- [ ] **Step 6:** Write `docs/methodology.md` for non-developers: the CAGE theory, the 12 indicators with rules and sources, missing-data handling, the Hofstede source/terms, and when to re-run `collect`.
- [ ] **Step 7:** Commit: `feat(scorecard-ui): show dimensions, accessibility and radar` and `docs: add methodology guide`.

---

## Slice 4 · `feat/country-comparison`

**Done when:** on `/compare`, selecting Colombia, Mexico and Spain shows a ranking bar chart, a radar overlay and a values table.

### Task 4.1: Comparison API

**Files:**
- Create: `backend/app/comparison/__init__.py`, `routes.py`
- Modify: `backend/config/countries.yaml` (add MEX `America/Mexico_City`, ESP `Europe/Madrid`, CHL `America/Santiago`), `backend/app/main.py`
- Test: `backend/tests/comparison/test_routes.py`

**Interfaces:**
- Consumes: `build_scorecard`, `aggregate`.
- Produces: `GET /api/comparison?iso3=COL,MEX` → `{countries: [{iso3, name, has_data, accessibility, dimensions: {C, A, G, E}}]}`, sorted by accessibility descending with `null` last.

- [ ] **Step 1: Write the failing tests.**
  - `test_sorted_by_accessibility_with_nulls_last`.
  - `test_country_without_data_is_included_with_has_data_false` (not a 409).
  - `test_lowercase_codes_accepted`.
  - `test_unknown_code_returns_404_naming_it` (`?iso3=COL,XYZ` → `"Unknown country: XYZ"`). **(Review Focus 5.)**
  - `test_empty_selection_returns_422`.
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** PASS.
- [ ] **Step 5:** Commit: `feat(comparison): add multi-country comparison API`.

### Task 4.2: Comparison page

**Files:**
- Create: `frontend/src/features/comparison/api.ts`, `ComparisonPage.tsx`, `RankingChart.tsx`, `RadarOverlay.tsx`, `comparison.test.tsx`; shadcn `checkbox`
- Modify: `AppShell.tsx` (nav: Scorecard · Compare), `App.tsx` (route `/compare`)

- [ ] **Step 1: Write the failing tests.**
  - `selected countries appear in ranking order with percentages`.
  - `country without data shows "no data"`.
  - `radar overlays at most three countries and says so when more are selected` ("Radar shows the first 3 selected").
  - `selection is kept in the URL` (`?iso3=COL,MEX`).
- [ ] **Step 2:** FAIL → **Step 3:** implement.
  - `RankingChart` is a horizontal Recharts `BarChart` with direct value labels, in one colour.
  - `RadarOverlay` is capped at 3 series (categorical colours slots 1–3: `#2a78d6`, `#eb6834`, `#1baf7a`) with a legend.
  - A values table sits below both charts.
- [ ] **Step 4:** PASS.
- [ ] **Step 5:** Commit: `feat(comparison-ui): rank and compare selected countries`.

---

## Slice 5 · `feat/ai-explanation`

**Done when:** "Explain" on the Colombia scorecard shows an explanation (from the real provider once configured); a second click returns the cached one instantly; with no provider configured, the UI says so.

**Decision point before Task 5.3:** the team picks the LLM provider and model. Tasks 5.1–5.2 don't depend on it.

### Task 5.1: Prompt builder and numbers guard

**Files:**
- Create: `backend/app/explanation/__init__.py`, `prompt.py`, `guard.py`
- Test: `backend/tests/explanation/test_prompt.py`, `test_guard.py`

**Interfaces:**
- Produces:
  - `build_prompt(scorecard: Scorecard, profile: CompanyProfile) -> str`. It contains:
    - instructions: 120–180 words, plain language, name the weakest and strongest dimension, cite indicator IDs, end with one next step, and **use only numbers that appear in DATA**;
    - a `DATA:` JSON block holding only integer-rounded scores, dimension %, accessibility %, formatted raw values and years;
    - a `COMPANY:` block with `profile.description_md`.
  - `allowed_numbers(scorecard) -> set[float]`: every number in the DATA block.
  - `find_unsupported_numbers(text: str, allowed: set[float], tolerance: float = 0.5) -> list[str]`. It ignores digits that are part of indicator IDs (`C1`, `A3`) and accepts thousands separators and `%`.

- [ ] **Step 1: Write the failing tests.**
  - `test_prompt_data_block_contains_rounded_scores_and_ids` (A3 → 46; "A3" present).
  - `test_prompt_includes_company_description`.
  - `test_prompt_excludes_retrieval_timestamps_and_urls`.
  - `test_guard_accepts_numbers_from_payload` ("Administrative (49%)" when the dimension is 48.68).
  - `test_guard_flags_invented_number` ("a 20% withholding tax" → `["20%"]`).
  - `test_guard_ignores_indicator_ids` ("see A3 and G1" → `[]`).
  - `test_guard_accepts_thousands_separator` ("$22,250").
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** PASS.
- [ ] **Step 5:** Commit: `feat(explanation): build grounded prompt and numbers guard`.

### Task 5.2: Explanation service, cache and API

**Files:**
- Create: `backend/app/explanation/model.py`, `cache.py`, `service.py`, `routes.py`
- Test: `backend/tests/explanation/test_service.py`, `test_routes.py`

**Interfaces:**
- Produces:
  - `class ExplanationModel(Protocol): def generate(self, prompt: str) -> str`.
  - `get_model(settings) -> ExplanationModel` raises `ModelNotConfigured` when `llm_provider` is unset. `deps.get_explanation_model` is overridable.
  - `Explanation{iso3, text, flagged: bool, created_at}`.
  - `ExplanationCache(db_path)` creates table `explanations` with PK `(iso3, cache_key)` and has `get(iso3, key) -> Explanation | None` and `put(iso3, key, explanation)`.
  - `cache_key(scorecard, profile) -> str`: sha256 of the scorecard JSON + `profile_hash`.
  - `explain(scorecard, profile, *, model, cache) -> Explanation`:
    1. return the cached explanation on a hit;
    2. otherwise generate and run the guard;
    3. if the guard finds numbers, retry once with a line listing them;
    4. if they're still there, store with `flagged=True`.

    A model exception raises `ExplanationFailed`.
  - Routes:
    - `GET /api/countries/{iso3}/explanation` returns the explanation or 404 `"No explanation yet"`. It's keyed by the current data, so a data refresh makes it 404 again.
    - `POST` the same path: 200 `Explanation` · 503 `"AI is not configured"` · 502 `"The AI service failed"`. The 503 is new; add it to spec §4.3 (`docs(spec): …`).

- [ ] **Step 1: Write the failing tests** (a `FakeModel(responses: list[str | Exception])` that records prompts).
  - `test_cache_hit_does_not_call_model`.
  - `test_invented_number_triggers_one_retry_then_clean_result_is_not_flagged` (2 calls; the 2nd prompt mentions the rejected number).
  - `test_invented_number_twice_is_stored_flagged` (2 calls, `flagged=True`).
  - `test_changed_data_changes_cache_key`.
  - Routes:
    - `test_post_returns_explanation_and_get_returns_cached`;
    - `test_post_without_provider_returns_503`;
    - `test_model_error_returns_502`;
    - `test_explanation_requires_session`.
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** PASS.
- [ ] **Step 5:** Commit: `feat(explanation): generate, guard and cache explanations`.

### Task 5.3: Provider adapter (after the decision)

**Files:**
- Create: `backend/app/explanation/providers/<provider>.py`
- Modify: `backend/app/explanation/model.py` (`get_model` mapping), `.env.example`, README

- [ ] **Step 1:** Install the provider's official SDK. Implement `<Provider>Model(api_key, model).generate(prompt) -> str` with a 30 s timeout and a conservative token limit.
- [ ] **Step 2:** **No unit test for the network call** (it would only test a mock of the SDK). Verify manually: set the env vars, `POST` Colombia's explanation, and read the text.
- [ ] **Step 3:** Commit: `feat(explanation): add <provider> model adapter`.

### Task 5.4: Explanation panel

**Files:**
- Create: `frontend/src/features/explanation/api.ts`, `ExplanationPanel.tsx`, `explanation.test.tsx`; shadcn `alert`
- Modify: `ScorecardPage.tsx`

- [ ] **Step 1: Write the failing tests.**
  - `shows cached explanation on load` (`GET` resolves).
  - `explain button generates and shows text` (`GET` 404 → click "Explain" → text).
  - `flagged explanation shows a review warning` ("Some numbers could not be verified. Review before using.").
  - `503 shows "AI is not configured"`.
  - `502 shows a retry message` ("The AI service failed. Try again.").
- [ ] **Step 2:** FAIL → **Step 3:** implement (`useMutation`; the button is disabled while pending) → **Step 4:** PASS.
- [ ] **Step 5:** Commit: `feat(explanation-ui): add explain panel`.

---

## Slice 6 · `feat/pdf-report`

**Done when:** "Export PDF" on the scorecard downloads a one-country report; on `/compare` it downloads a report with the ranking page plus one section per country.

### Task 6.1: PDF builder

**Files:**
- Create: `backend/app/reports/__init__.py`, `charts.py`, `pdf.py`
- Test: `backend/tests/reports/test_pdf.py`

**Interfaces:**
- Consumes: `Scorecard`, `Explanation`, `CompanyProfile`.
- Produces:
  - `radar_png(series: list[tuple[str, list[Dimension]]]) -> bytes`, with 1 series per country section and up to 3 on the ranking page, and `ranking_png(rows: list[tuple[str, float | None]]) -> bytes`. They use matplotlib's Agg backend, with colours from Task 4.2.
  - `build_report(scorecards: list[Scorecard], explanations: dict[str, Explanation | None], profile: CompanyProfile, generated_at: datetime) -> bytes`. The font is **DejaVu Sans loaded from `matplotlib.get_data_path()/fonts/ttf/`** (regular + bold), so any Unicode renders.
  - Sections, per spec §4.2. A missing explanation prints "Explanation not generated yet."

- [ ] **Step 1:** `uv add fpdf2 matplotlib` and `uv add --dev pypdf`.
- [ ] **Step 2: Write the failing tests** (read the output with `pypdf.PdfReader`).
  - `test_single_country_report_contains_name_score_and_indicator_ids` ("Colombia", the formatted accessibility or its reason, all 12 IDs).
  - `test_multi_country_report_has_ranking_page_first` (page 2 text contains "Ranking" and every name).
  - `test_explanation_text_with_unicode_renders` (text containing `–`, `≥`, `“quoted”` and `Bogotá, Peñalolén` → no exception, and the text is extractable). **(Review Focus 4.)**
  - `test_missing_explanation_is_stated`.
- [ ] **Step 3:** FAIL → **Step 4:** implement → **Step 5:** PASS.
- [ ] **Step 6:** Commit: `feat(reports): build PDF report with charts`.

### Task 6.2: Report endpoint and export buttons

**Files:**
- Create: `backend/app/reports/routes.py`, `frontend/src/features/report/ExportPdfButton.tsx`, `report.test.tsx`
- Modify: `backend/app/main.py`, `ScorecardPage.tsx`, `ComparisonPage.tsx`
- Test: `backend/tests/reports/test_routes.py`

**Interfaces:**
- Produces:
  - `GET /api/reports/pdf?iso3=COL,MEX` → `application/pdf` with `Content-Disposition: attachment; filename="market-accessibility-COL-MEX-YYYY-MM-DD.pdf"`. It uses cached explanations only and never calls the model. Unknown codes → 404; no codes → 422.
  - `ExportPdfButton({ iso3: string[] })`: an `<a href={"/api/reports/pdf?iso3=" + codes} download>`. It's same-origin, so the cookie is sent.

- [ ] **Step 1: Write the failing tests.**
  - `test_pdf_endpoint_returns_pdf_with_attachment_header` (body starts with `%PDF`).
  - `test_pdf_endpoint_never_calls_the_model` (override `get_explanation_model` with a fake that fails if called).
  - `test_pdf_requires_session`.
  - Frontend: `export link targets the selected countries` (`href` ends with `iso3=COL,MEX`).
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** PASS.
- [ ] **Step 5:** Commit: `feat(reports): add PDF export endpoint and buttons`.

---

## Slice 7 · `feat/deploy`

**Done when:** the quick-tunnel URL serves the app over HTTPS, login works, data is present, and merging to `main` redeploys automatically. Infrastructure is verified with commands, not unit tests.

### Task 7.1: Containers and compose

**Files:**
- Create: `backend/Dockerfile`, `backend/.dockerignore`, `frontend/Dockerfile`, `frontend/nginx.conf`, `frontend/.dockerignore`, `deploy/docker-compose.yml`, `deploy/.env.example`, `deploy/scripts/tunnel-url.sh`, `deploy/scripts/backup.sh`, `docs/deploy.md`

**Interfaces:**
- Compose project `name: ami`, isolated from other stacks on the VPS. Services:
  - `api`: the backend image, with `DB_PATH=/data/app.sqlite`, `TRUST_PROXY=true`, `COOKIE_SECURE=true`, volume `app_data:/data` and `env_file: .env`.
  - `web`: a multi-stage Node build → `nginx:alpine`. `try_files $uri /index.html`; `location /api/` → `proxy_pass http://api:8000`.
  - `tunnel`: `cloudflare/cloudflared:latest`, with `command: tunnel --no-autoupdate --url http://web:80`.
- **No `ports:` on any service.**

- [ ] **Step 1:** Write the files.
  - The backend image is `python:3.12-slim` with uv and `uv sync --locked --no-dev`. Its CMD is `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Config, data CSVs and the real profile (if present on the server) are mounted read-only.
  - `tunnel-url.sh` runs `docker compose -p ami logs tunnel | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | tail -1`.
  - `backup.sh` uses Python's `sqlite3` backup API inside `api` to write `/data/backups/app-YYYYMMDD.sqlite` and keeps the last 14.
- [ ] **Step 2:** Verify locally: `docker compose -f deploy/docker-compose.yml up --build -d`, then `docker compose -p ami run --rm api python -m app.cli collect --all`.
  - The tunnel URL from `tunnel-url.sh` opens the login page.
  - `curl <url>/api/health` → `{"status":"ok"}`.
  - `docker compose -p ami ps` shows no published ports.
- [ ] **Step 3:** Commit: `build(deploy): add containers, compose and tunnel`.

### Task 7.2: Continuous deployment to the VPS

**Files:**
- Create: `.github/workflows/deploy.yml`
- Modify: `docs/deploy.md`, `README.md`

- [ ] **Step 1:** Write `deploy.yml`.
  - It triggers on `workflow_run` of CI, completed on `main` with a `success` conclusion.
  - The job SSHes with `appleboy/ssh-action`, using secrets `VPS_HOST`, `VPS_USER` and `VPS_SSH_KEY`.
  - On the server: `cd ~/ai-market-intelligence && git pull --ff-only && docker compose -f deploy/docker-compose.yml up -d --build api web`. **The `tunnel` service is never restarted, so the URL stays stable.**
- [ ] **Step 2:** In `docs/deploy.md`, document:
  - the one-time server setup (clone, `deploy/.env`, the real profile files, the first `collect`);
  - the nightly cron for `backup.sh`;
  - finding the URL;
  - switching to a named tunnel (`tunnel run --token $TUNNEL_TOKEN`) when a domain is bought.
- [ ] **Step 3:** Verify: merge a trivial docs change → the Action runs → `docker compose -p ami ps` shows new `api`/`web` containers and the same `tunnel` container ID → the URL still works.
- [ ] **Step 4:** Commit: `ci(deploy): deploy to VPS after CI passes on main`.

---

## After slice 7

Write `docs/plans/<date>-polishing-plan.md` with the team. Candidates:
- UX details;
- a README with screenshots and a demo GIF;
- more countries and the partner's completed manual data;
- a named tunnel with a domain;
- optional E2E tests;
- anything learned while building.
