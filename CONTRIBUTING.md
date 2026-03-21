# Contributing to FairMind

Thanks for your interest in contributing to FairMind! This guide will get you up and running.

## Prerequisites

- **Python 3.11+** and [uv](https://docs.astral.sh/uv/getting-started/installation/) (backend)
- **Node.js 20+** and npm (frontend)
- **PostgreSQL** (local or [Neon](https://neon.tech) free tier)
- **Git**

## Getting Started

### 1. Fork and clone

```bash
git clone https://github.com/<your-username>/fairmind.git
cd fairmind
```

### 2. Backend setup

```bash
cd apps/backend
cp .env.example .env
# Edit .env — set DATABASE_URL to your Postgres connection string
# For local dev, most other defaults are fine

uv sync
uv run fastapi dev api/main.py
```

Backend runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### 3. Frontend setup

```bash
cd apps/frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:1111`.

### 4. Verify it works

- Open `http://localhost:1111` — you should see the dashboard
- Open `http://localhost:8000/docs` — you should see the Swagger UI

## Finding Something to Work On

- Browse [good first issues](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- Check [help wanted](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) for more substantial tasks
- Comment on the issue to let us know you're working on it

## Making Changes

### Branch naming

```
feature/short-description
fix/short-description
```

### Code style

- **Backend**: Follow existing patterns in `apps/backend/src/`. Domain-driven design with routers, services, and domain models.
- **Frontend**: Follow existing patterns in `apps/frontend/src/`. Next.js App Router, Tailwind CSS, neobrutalist design system.
- No mock data, no hardcoded IDs, no placeholder content in production code.

### Running tests

```bash
# Backend
cd apps/backend
uv run pytest

# Frontend
cd apps/frontend
npm run test
```

## Submitting a PR

1. Create a feature branch from `main`
2. Make your changes
3. Run tests and make sure they pass
4. Push your branch and open a PR against `main`
5. Describe what you changed and why in the PR description
6. Link the related issue

## Project Structure

```
apps/
  backend/     → FastAPI backend (Python)
  frontend/    → Next.js dashboard (TypeScript)
  website/     → Marketing site (Astro)
  ml/          → ML models and utilities
docs/          → Documentation
```

## Questions?

Open an issue or comment on an existing one. We're happy to help you get started.
