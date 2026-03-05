# Reorg Move Ledger

Tracks structural moves during repository cleanup.

| Date | Source | Destination | Reason |
|---|---|---|---|
| 2026-03-05 | `apps/website/src/pages/docs` | `apps/website/archive/docs-pages` | Website must be marketing-only. |
| 2026-03-05 | `apps/website/src/content/docs` | `apps/docs/content/docs` | Canonical docs moved to docs app. |
| 2026-03-05 | `apps/website/fumadocs.config.ts` | `apps/docs/archive/legacy-fumadocs.config.ts.txt` | Legacy Fumadocs config preserved as reference; docs app now uses Next app router scaffold. |
| 2026-03-05 | `apps/backend/_legacy_backup` | `apps/backend/archive/legacy_backup` | Legacy backup should not be runtime-importable. |
| 2026-03-05 | `apps/backend/legacy_supabase_sql` | `archive/repo-legacy/supabase-legacy/sql/backend_legacy_supabase_sql` | Supabase SQL archived after Neon migration. |
| 2026-03-05 | `apps/backend/scripts/legacy_supabase` | `archive/repo-legacy/supabase-legacy/scripts/backend_legacy_supabase_scripts` | Supabase scripts archived. |
| 2026-03-05 | `legacy_supabase` / `supabase` | `archive/repo-legacy/supabase-legacy/root/*` | Root-level Supabase artifacts archived. |
| 2026-03-05 | `apps/backend/domain/bias/services/bias_bench` | `apps/backend/archive/bias_bench_duplicate/bias_bench` | Keep one canonical bias_bench tree. |
| 2026-03-05 | `apps/backend/src/domain/*/routes` | `apps/backend/archive/domain-routes-legacy/*/routes` | Duplicate domain route trees archived; runtime uses explicit API router registration. |
| 2026-03-05 | `apps/backend/src/domain/bias_detection/services/bias_detection_service.py` | `apps/backend/archive/duplicate-services/domain-bias_detection/bias_detection_service.py` | Duplicate bias-detection ownership removed; application service is runtime canonical. |
| 2026-03-05 | `apps/backend/src/domain/compliance/services/india_compliance_service.py` | `apps/backend/archive/duplicate-services/domain-compliance/india_compliance_service.py` | Duplicate India compliance ownership removed; application service is runtime canonical. |
| 2026-03-05 | `apps/backend/src/application/services/bias_detection_service.py` | `apps/backend/archive/duplicate-services/application-bias_detection/bias_detection_service.py` | Legacy unused implementation archived after import-trace verification. |
