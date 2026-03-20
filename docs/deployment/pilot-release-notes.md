# FairMind Pilot Release Notes

## Release Date
- March 13, 2026

## Scope
- Backend stabilization for Neon-backed pilot
- Real model onboarding and baseline evaluation workflow
- Frontend/docs/website reliability fixes for pilot demos
- Pilot operations documentation and go-live checks

## Major Additions
- One-command pilot bootstrap:
  - `/Users/adhi/axonome/fairmind/apps/backend/scripts/pilot_bootstrap.sh`
- Real model flow:
  - `/Users/adhi/axonome/fairmind/apps/backend/scripts/create_sample_real_model.py`
  - `/Users/adhi/axonome/fairmind/apps/backend/scripts/onboard_real_model.py`
  - `/Users/adhi/axonome/fairmind/apps/backend/scripts/run_baseline_model_eval.py`
- Pilot readiness automation:
  - `/Users/adhi/axonome/fairmind/apps/backend/scripts/pilot_readiness_check.py`
  - Output: `/Users/adhi/axonome/fairmind/apps/backend/docs/pilot_readiness_report.json`
- Neon migration audit:
  - `/Users/adhi/axonome/fairmind/apps/backend/scripts/verify_neon_migration.py`

## Product/UX Fixes Included
- Alerts route added and wired in dashboard navigation.
- Settings API route added (`/api/v1/settings/`) and integrated.
- Dashboard fallback logic hardened to avoid hard error screens.
- Collapsed sidebar now shows top-level routes consistently.
- Settings “About” content refocused to product workflow.
- Docs app now has `/docs` index, search, and per-page routing.

## Deployment Notes
- Website build issue from sitemap integration was neutralized for pilot stability.
- Backend default pytest profile now runs deterministic non-e2e checks.
- Pilot seed data is meaningful and linked across models/datasets/bias/compliance/governance/audit.

## Known Limitations
- Some optional advanced routers may skip if heavy ML deps are missing (e.g., `torch`).
- This release prioritizes pilot operability and verification over deep architecture cleanup.

## Acceptance Snapshot
- Bootstrap completed successfully on Neon.
- Readiness report passed with `overall_ok=true`.
