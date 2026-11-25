# Contributing to FairMind

Thanks for your interest in FairMind. This guide gets you from a fresh clone to an open pull request.

## Prerequisites

- **Python 3.11+** and [uv](https://docs.astral.sh/uv/getting-started/installation/) (backend)
- **Node.js 20+** and npm (frontend)
- **Git**

PostgreSQL is optional. The backend uses a local SQLite file unless you set `DATABASE_URL`.

## Getting started

### 1. Fork and clone

Fork the repository on GitHub, then:

```bash
git clone https://github.com/<your-username>/fairmind.git
cd fairmind
git remote add upstream https://github.com/adhit-r/fairmind.git
```

### 2. Backend

```bash
cd apps/backend
cp config/env.example .env
uv sync
uv run uvicorn api.main:app --reload --port 8000
```

The defaults in `.env` work for local development. The first start takes about a minute while it creates the SQLite tables. To use PostgreSQL instead, set `DATABASE_URL` in `.env` to your connection string.

### 3. Frontend

In a second terminal:

```bash
cd apps/frontend
echo "BACKEND_INTERNAL_URL=http://localhost:8000" > .env.local
npm install
npm run dev
```

`BACKEND_INTERNAL_URL` tells the frontend's API proxy where your local backend is. Without it, API calls go to the hosted backend address and fail.

### 4. Check it works

- http://localhost:8000/docs shows the API docs.
- http://localhost:1111 shows the sign-in page. Create an account on the register page and sign in.

If a step fails, open an issue with the command and the error. Fixing setup problems is a useful first contribution.

## Finding something to work on

- [Good first issues](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) are small and come with pointers to the files involved.
- [Help wanted](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) issues are larger.
- Comment on an issue before you start so others know it is taken. If you stop working on it, say so in a comment so someone else can pick it up.
- For a new idea, open a [Discussion](https://github.com/adhit-r/fairmind/discussions) or a feature request first, so we can agree on the approach before you write code.

## Making changes

### Branches

Branch from an up-to-date `main`:

```bash
git fetch upstream
git checkout -b fix/short-description upstream/main
```

Use `feature/`, `fix/`, `docs/` or `task/` as the prefix.

### Code style

- **Backend** (`apps/backend/`): FastAPI with a domain-driven layout of routes, services and domain models. Follow the patterns of nearby code.
- **Frontend** (`apps/frontend/`): Next.js App Router with Tailwind CSS. New pages use the lifecycle-shell design described in [CLAUDE.md](CLAUDE.md); `/dashboard`, `/integrations` and `/onboard` are good reference pages.
- No mock data, hardcoded IDs or placeholder content in production code. Everything the UI shows comes from a real API, or is labelled "Coming soon".
- No emoji in code, docs, commit messages or templates.

### Tests

```bash
# Backend
cd apps/backend
uv run pytest

# Frontend (Playwright; run `npx playwright install` once first)
cd apps/frontend
npm run test
```

Add or update tests for behaviour you change.

## Opening a pull request

1. Push your branch to your fork and open a pull request against `main`.
2. Fill in the pull request template: what changed, why, and how you tested it.
3. Link the issue it closes, for example `Closes #123`.
4. Keep the pull request focused on one change. Smaller pull requests get reviewed faster.

A maintainer reviews every pull request before it is merged.

## Project structure

```
apps/
  backend/     FastAPI backend (Python)
  frontend/    Next.js dashboard (TypeScript)
  docs/        Documentation site
  website/     Marketing site (Astro)
  ml/          ML models and utilities
docs/          Architecture notes, ADRs, audits and plans
```

## Questions

Ask in [GitHub Discussions](https://github.com/adhit-r/fairmind/discussions) or comment on the issue you are working on.

On your first pull request, a bot asks you to accept the [Contributor License Agreement](CLA.md) by posting a comment; you keep the copyright in your work. Your contributions are distributed under the licenses in [LICENSING.md](LICENSING.md): Apache-2.0 for `apps/sdk`, `apps/cli` and `apps/mcp`, AGPL-3.0 for everything else. Please also follow the [Code of Conduct](CODE_OF_CONDUCT.md).
