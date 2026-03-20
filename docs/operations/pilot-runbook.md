# FairMind Pilot Runbook

## Purpose
Run a production-like pilot for AI compliance workflows using Neon and a real model artifact.

## Prerequisites
- Backend venv exists: `apps/backend/.venv`
- Neon `DATABASE_URL` configured
- Optional real model file (if omitted, script trains one sample model)

## One-Command Bootstrap
From repo root:

```bash
cd apps/backend
export DATABASE_URL='postgresql://...'
./scripts/pilot_bootstrap.sh
```

Optional overrides:
- `REAL_MODEL_FILE=/abs/path/to/model.pkl`
- `REAL_MODEL_NAME='Company Credit Model v2'`
- `REAL_MODEL_TYPE=classification`
- `REAL_MODEL_VERSION=2.0.0`
- `OWNER_EMAIL=you@company.com`

## Outputs
- Onboarded real model ID (printed by script)
- Readiness report: `/Users/adhi/axonome/fairmind/apps/backend/docs/pilot_readiness_report.json`

## Local App Startup
Backend:
```bash
cd apps/backend
export DATABASE_URL='postgresql://...'
.venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd apps/frontend
npm run dev
```

Docs:
```bash
cd apps/docs
npm run dev
```

Website:
```bash
cd apps/website
npm run dev
```

## Pilot Demo Happy Path
1. Open dashboard and confirm models/datasets are populated.
2. Open the onboarded model detail and verify metadata/audit trail.
3. Review bias and compliance records for baseline evaluation.
4. Review governance policy/workflow/evidence entries.
5. Export/share compliance summary and next actions.

## Troubleshooting
- `DATABASE_URL is required`: export valid Neon URL first.
- Missing model artifact: ensure `REAL_MODEL_FILE` path exists.
- `User not found`: seed script creates `adhi@axonome.xyz`; use that as owner or seed your user.
- Readiness fails: inspect `/Users/adhi/axonome/fairmind/apps/backend/docs/pilot_readiness_report.json`.
