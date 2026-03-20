# Pilot Go-Live Checklist

## Environment
- [ ] Neon `DATABASE_URL` set and tested
- [ ] Backend `.venv` available and dependencies installed
- [ ] Frontend, docs, website environment variables configured

## Data & Model Readiness
- [ ] Runtime schema migrated (`migrate_neon_runtime_tables.py`)
- [ ] Meaningful seed loaded (`seed_demo_data.py`)
- [ ] Real model artifact onboarded (`onboard_real_model.py`)
- [ ] Baseline eval completed (`run_baseline_model_eval.py`)

## Verification
- [ ] Pilot readiness report is green:
  - `/Users/adhi/axonome/fairmind/apps/backend/docs/pilot_readiness_report.json`
  - `overall_ok = true`
- [ ] Backend tests pass (`python -m pytest -q`)
- [ ] Frontend build passes (`apps/frontend`)
- [ ] Docs build passes (`apps/docs`)
- [ ] Website build passes (`apps/website`)

## UX/Content
- [ ] Dashboard loads with seeded model/dataset/activity
- [ ] `/alerts` and `/settings` routes work
- [ ] Docs available at `/docs` with navigation/search
- [ ] Website/docs cross-links correct (`fairmind.xyz` ↔ `docs.fairmind.xyz`)

## Operational
- [ ] Pilot runbook shared with stakeholder team
- [ ] Known limitations documented
- [ ] Incident owner and support channel assigned
- [ ] Backup/rollback plan agreed
