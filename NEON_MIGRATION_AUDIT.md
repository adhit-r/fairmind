# Neon Migration Audit (Supabase Removal)

Date: 2026-03-05
Scope: Runtime backend + frontend dependency surface

## Summary

Supabase has been removed from active runtime paths in backend services touched during this pass and from frontend dependencies.

What is now true:
- Backend runtime no longer imports Supabase SDK directly in key storage services.
- Core API routes no longer call `supabase_service` in metrics/dataset creation paths.
- Supabase-specific health/config hooks removed from runtime settings path.
- Frontend `@supabase/supabase-js` dependency removed; dead client file removed.

What remains:
- Supabase references still exist in docs/scripts/legacy tooling and a compatibility shim file name (`supabase_client.py`) used by legacy repository code paths.
- Legacy scripts under `apps/backend/scripts/*supabase*` still reference Supabase semantics and should be deprecated/replaced.

## Changes Applied

### Backend runtime
- Updated `apps/backend/api/routes/core.py`
  - Replaced metrics summary Supabase call with DB queries.
  - Replaced dataset create Supabase call with DB insert.
- Updated `apps/backend/services/dataset_storage.py`
  - Removed Supabase SDK import and Supabase branches.
  - Local filesystem storage only.
- Updated `apps/backend/services/bias_test_results.py`
  - Removed Supabase SDK import and Supabase branches.
  - Local filesystem storage only.
- Replaced `apps/backend/supabase_client.py`
  - Converted to compatibility shim (no Supabase SDK import, always disconnected fallback).
- Updated `apps/backend/services/health.py`
  - Removed Supabase health check branch.
- Updated `apps/backend/core/middleware/auth.py`
  - Removed Supabase config coupling from middleware init.
- Updated `apps/backend/config/settings.py`
  - Removed `supabase_url` and `supabase_service_role_key` settings fields.
- Updated `apps/backend/shared/constants.py`
  - Removed `ServiceName.SUPABASE`.
- Updated `apps/backend/health/checker.py`
  - Removed Supabase external-service branch.

### Dependency manifests
- Updated `apps/backend/pyproject.toml`
  - Removed `supabase` dependency.
  - Removed `supabase.*` mypy override.
- Updated `apps/backend/requirements.txt`
  - Removed `supabase`, `supabase-auth`, `supabase-functions` pinned entries.

### Frontend
- Updated `apps/frontend/package.json`
  - Removed `@supabase/supabase-js`.
- Updated `apps/frontend/bun.lock`
- Deleted `apps/frontend/src/lib/supabase/client.ts`

## Remaining Supabase References (non-runtime / legacy)

- Docs/config text:
  - `apps/backend/config/env.example`
  - `apps/backend/SETUP.md`
  - `apps/backend/services/DATASET_STORAGE_README.md`
  - `docs/deployment/DEPLOYMENT_GUIDE_2025.md`
- Legacy scripts:
  - `apps/backend/scripts/seed_datasets.py` (direct Supabase SDK import)
  - `apps/backend/scripts/setup_supabase_storage.py`
  - `apps/backend/scripts/migrate_to_supabase.py`
  - `apps/backend/scripts/test_supabase_storage.py`
  - `apps/backend/scripts/quick_start_supabase.py`
  - `apps/backend/scripts/check_supabase_via_client.py`
- Legacy repository path still named by convention:
  - `apps/backend/api/repositories/ai_bom_repository.py` imports `supabase_client` shim.

## Neon-first Operational Guidance

Use only:
- `DATABASE_URL=postgresql://<neon-connection-string>`
- optional local storage paths (`DATASET_STORAGE_PATH`, model local storage)

Do not set:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

## Recommended Next Steps

1. Rename compatibility file to neutral naming:
   - `supabase_client.py` -> `storage_adapter.py`
   - update imports in `model_storage_service.py`, `ai_bom_repository.py`, scripts.
2. Remove or archive Supabase-specific scripts into `scripts/legacy/`.
3. Update `env.example` and setup docs to Neon-first examples.
4. Replace AI BOM repository fallback with proper SQLAlchemy implementation so shim is no longer needed.
5. Regenerate backend lock/requirements cleanly from pyproject (if this repo depends on lock sync policy).

