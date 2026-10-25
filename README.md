# AI Market Intelligence: CAGE Market Accessibility

A web tool that estimates **how accessible a foreign country is** for a company that sells its services remotely. It applies Pankaj Ghemawat's **CAGE distance framework** (Cultural, Administrative, Geographic, Economic): 12 indicators → 4 dimension scores → one Market Accessibility %. Results come with charts, an AI-written explanation and a PDF report.

The model is country-agnostic: adding a country is a config change, not a code change.

> Status: in development. See the [design spec](docs/specs/2026-10-25-cage-market-accessibility-design.md) and the [implementation plan](docs/plans/2026-10-25-implementation-plan.md).

## Stack

- **Backend:** Python 3.12, [uv](https://docs.astral.sh/uv/), FastAPI, SQLite
- **Frontend:** React + TypeScript (Vite), Tailwind CSS, shadcn/ui, TanStack Query
- **CI:** GitHub Actions (lint, tests, build)

## Quick start

Requirements: Python 3.12 with `uv`, and Node.js 24.

First create the backend configuration (it is gitignored):

```bash
cd backend
cp .env.example .env
uv run python -m app.cli hash-password            # paste the output into APP_PASSWORD_HASH
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"   # paste into SECRET_KEY
```

Then run both apps:

```bash
# Backend (http://localhost:8000)
cd backend
uv sync
uv run uvicorn app.main:app --reload --env-file .env

# Frontend (http://localhost:5173), in another terminal
cd frontend
npm install
npm run dev
```

Collect data before opening the app (World Bank indicators for every country in `backend/config/countries.yaml` plus the home country from the company profile):

```bash
cd backend
uv run --env-file .env python -m app.cli collect --all
```

The frontend proxies `/api` to the backend, so open http://localhost:5173 and sign in with `APP_USERNAME` and the password you hashed.

## Features

- **Scorecard:** pick a country to see its Market Accessibility %, the four CAGE dimensions (radar chart) and all 12 indicators with raw values, scores and sources.
- **AI explanation:** on the scorecard, *Explain* asks an LLM for a short summary written only from the numbers on screen. Every number in the answer is checked against the data; if one can't be verified, the AI gets one retry, and if it still fails the explanation is marked for review. Explanations are saved and reused until the data or the company profile changes. The LLM provider is configured with `LLM_PROVIDER`, `LLM_API_KEY` and `LLM_MODEL`. Without them, the button reports that AI is not configured.
- **Compare:** select several countries to see a ranking, an overlaid CAGE radar (top 3) and a values table. A "Data" column shows how many indicators each country has, because missing indicators are left out of the averages.

- **PDF report:** *Export PDF* on the scorecard or the comparison downloads a report with a cover, the ranking (for several countries), each country's dimensions, indicators with sources and the saved AI explanation, plus a methodology note. Exporting never calls the AI.

## Configuration

- `backend/config/countries.yaml`: target countries (ISO3 code, name, main languages, business timezone). Adding a country = adding one line, then running `collect`.
- `backend/config/company.example.yaml` / `.md`: a fictional company profile (home country, home timezone, supported languages, channels, description). Put the real profile in `company.yaml` / `company.md`: they are gitignored and loaded instead of the example.

## Login

There is one generic user, configured through environment variables (see `backend/.env.example`). Sessions use a signed, httpOnly cookie valid for 8 hours. After 5 failed attempts from the same IP, login is locked for 15 minutes.

## Tests

```bash
cd backend && uv run pytest && uv run ruff check .
cd frontend && npx vitest run && npm run lint
```

## Documentation

- [Methodology](docs/methodology.md): the 12 CAGE indicators, scoring rules and data sources, for non-developers
- [Architecture](docs/architecture.md)
- [Design spec](docs/specs/2026-10-25-cage-market-accessibility-design.md)
- [Implementation plan](docs/plans/2026-10-25-implementation-plan.md)
