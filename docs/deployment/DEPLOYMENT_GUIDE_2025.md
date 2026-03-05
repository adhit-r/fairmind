# Deployment Guide 2025 (Neon-first)

## Overview

This guide describes the current deployment approach for FairMind using:
- Neon (PostgreSQL) for relational data
- Local artifact storage by default
- Optional external object storage via adapter pattern

## 1. Backend Environment

Set in `apps/backend/.env`:

```bash
DATABASE_URL=postgresql://<user>:<password>@<neon-host>/<db>?sslmode=require
SECRET_KEY=<strong-random-secret>
JWT_SECRET=<strong-random-secret>
```

## 2. Install Dependencies

```bash
cd apps/backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 3. Run Migrations / Table Setup

Use your standard migration or table-init workflow.

## 4. Start Services

Backend:

```bash
cd apps/backend
python main.py
```

Website/docs:

```bash
cd apps/website
bun install
bun run build
```

## 5. Operational Checks

- API health endpoints return healthy.
- DB connectivity succeeds against Neon.
- File storage paths are writable.
- Core user flows (model registration, governance checks, reporting) are functional.

## Legacy Note

The old provider-specific deployment guide is archived at:
`docs/deployment/archive/DEPLOYMENT_GUIDE_2025_LEGACY_PROVIDER.md`.
