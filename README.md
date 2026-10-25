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

```bash
# Backend (http://localhost:8000)
cd backend
uv sync
uv run uvicorn app.main:app --reload

# Frontend (http://localhost:5173), in another terminal
cd frontend
npm install
npm run dev
```

The frontend proxies `/api` to the backend, so open http://localhost:5173.

## Tests

```bash
cd backend && uv run pytest && uv run ruff check .
cd frontend && npx vitest run && npm run lint
```

## Documentation

- [Architecture](docs/architecture.md)
- [Design spec](docs/specs/2026-10-25-cage-market-accessibility-design.md)
- [Implementation plan](docs/plans/2026-10-25-implementation-plan.md)
