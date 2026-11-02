# AI Market Intelligence: CAGE Market Accessibility

A web tool that estimates **how accessible a foreign country is** for a company that sells its services remotely. It applies Pankaj Ghemawat's **CAGE distance framework** (Cultural, Administrative, Geographic, Economic): 12 indicators → 4 dimension scores → one Market Accessibility %. Results come with charts, an AI-written analysis and a PDF report.

The model is country-agnostic: adding a country is a config change, not a code change.

> Design: [original spec](docs/specs/2026-10-25-cage-market-accessibility-design.md) and [AI analysis & company profile spec](docs/specs/2026-11-01-ai-analysis-and-company-profile-design.md).

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
- **AI analysis (free):** on the scorecard, choose **Gemini** or **Groq** and click *Generate* for a written analysis: executive summary, why each CAGE dimension scored as it did, main barriers and opportunities, and a recommendation with next steps. The AI only sees the numbers on screen and the company description; every number in its answer is checked against the data (one retry, then the analysis is flagged for review). One analysis is saved per country and marked *outdated* when the data or the company profile changes.
  - Free API keys: [Google AI Studio](https://aistudio.google.com/apikey) (`GEMINI_API_KEY`, default model `gemini-3.8-flash`) and [Groq](https://console.groq.com/keys) (`GROQ_API_KEY`, default model `openai/gpt-oss-120b`). Only providers with a key appear in the menu. Note: Google may use free-tier Gemini inputs to improve its products; prefer Groq if the company description is confidential.
- **Comparison insight:** on *Compare*, *Generate* asks the chosen AI why the selected countries (those with data, at least two) rank as they do: a summary, one explanation per country and the key differences. The ranking order always comes from the real scores; the AI gets each country's rank and point gaps so it can cite them correctly.
- **Company profile:** the *Company* page edits the company's name, description, languages and channels. Languages and channels feed C1 and C2, so scores update as soon as you save; the description is background for the AI. Edits are stored in the app's database (never in git); *Reset* goes back to the file profile. The home country and time zone stay in `backend/config/company.yaml` because changing them needs a new `collect`.
- **Compare:** select several countries to see a ranking, an overlaid CAGE radar (top 3) and a values table. A "Data" column shows how many indicators each country has, because missing indicators are left out of the averages.

- **PDF report:** *Export PDF* on the scorecard or the comparison downloads a report with a cover; for several countries, a comparison page (ranking chart and table, a countries × dimensions heat map, the top-3 radar and the saved comparison insight); one page per country (accessibility % and rank, radar, AI executive summary, dimension bars marked with the best compared country, an indicator heat map, the AI sections on each dimension, barriers, opportunities and next steps, and the indicator table with sources); and a methodology note. AI text sits in light-blue boxes with the provider, model and date. Exporting never calls the AI: it uses saved analyses only, and the button notes how many countries have none yet.

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

## Deployment

The app runs on a VPS with Docker Compose behind a Cloudflare Tunnel (no open ports, HTTPS from Cloudflare), and redeploys automatically after CI passes on `main`. See [docs/deploy.md](docs/deploy.md).

## Documentation

- [Methodology](docs/methodology.md): the 12 CAGE indicators, scoring rules and data sources, for non-developers
- [Architecture](docs/architecture.md)
- [Deployment](docs/deploy.md)
- [Design spec](docs/specs/2026-10-25-cage-market-accessibility-design.md)
- [Implementation plan](docs/plans/2026-10-25-implementation-plan.md)
