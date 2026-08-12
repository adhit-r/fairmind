# P0 cyber hardening evidence

**Date:** 2026-08-13

**Reviewed range:** `148eb0a9cc457fe917b566a66e8c9460556e3ef3..e5e37cbbb1b581478b4838fdc808c1438cc0ac55`

**Hardening branch:** `adhit/p0-cyber-hardening`

## Evidence recovery

The first diff scan, `59a51a76-0370-4f18-a7e0-0ffd3142336d`, stopped during report finalization because the range launcher did not populate the required `scan.target.snapshotDigest`. Its review receipts and validation artifacts were preserved; it was not retried or represented as complete.

The exact binary Git diff was then applied to the index of a detached worktree at the base revision. Git confirmed that the staged tree matched the reviewed head commit, and the same snapshot implementation produced:

`codex-security-snapshot/v1:sha256:954bbbdb76b2d7f187e379ddbe61d76777fa0510d1cff0cb921513703554f51a`

Replacement scan `0c973128-6841-4ed0-96be-00d60f1debcb` completed and sealed with all 62 runtime-source review receipts closed. The recovery changed no finding, validation, or attack-path conclusion.

## Validated finding

The scan reported one High-confidence, High-severity finding: the default application mounted legacy AI-BOM CRUD without authenticated tenant scope (`CWE-306`). Unauthenticated create and list requests returned HTTP 200 through the real FastAPI application in local development and production configurations with disposable persistence. No live deployment, public ingress, or customer data was accessed.

## Remediation

- Removed the legacy AI-BOM router from default application composition and OpenAPI/product claims.
- Added a router-wide fail-closed dependency so direct mounting returns 404 before any service method runs.
- Replaced prefix-based JWT public-path matching with exact method/path rules and segment-aware development route families.
- Required the Assurance V2 master gate together with each admission, review, and decision child gate.
- Removed dashboard AI-BOM endpoint constants, hooks, retry behavior, and write actions; `/ai-bom` now renders an explicit unavailable state.
- Corrected README, website, comparison, request-access, product-analysis, and paper-draft capability claims.
- Applied the authoritative evaluator-catalog migration to the SQLite verifier fixture and asserted the exact receipt-trigger set.

## Verification receipt

- P0 backend assurance/auth regression: **1,395 passed, 242 skipped**. The skips are PostgreSQL or environment-gated tests; no live PostgreSQL result is claimed.
- Focused final security review: **257 passed**, with no remaining security/control defect in the reviewed diff.
- Migration integrity: **55 passed, 11 skipped**.
- Frontend TypeScript: passed.
- Frontend production build: passed.
- Website production build: passed.
- Desktop and mobile AI-BOM browser checks: HTTP 200, no page errors, no overflow, and zero legacy AI-BOM API requests.
- Desktop and mobile request-access browser checks: HTTP 200, no page errors, no overflow, and no purple/gradient classes.
- Backend dependency-layer boundary check: passed.
- Archive-import guard: passed.
- Python compilation and `git diff --check`: passed.

## Remaining claim boundary

This evidence establishes local source, test, build, and browser behavior only. It does not establish deployed-image parity, reverse-proxy policy, live PostgreSQL behavior, production tenant isolation, or release readiness. AI-BOM remains unavailable until a tenant-scoped replacement passes its independent release gates.
