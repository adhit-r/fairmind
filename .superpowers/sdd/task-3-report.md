# Task 3 Report: Organization-scoped framework workflow

## Delivered

- Mounted `api.routes.governance_assurance` at `/api/v1/ai-governance`.
- Added organization-scoped framework, version, control, assignment, assessment, readiness, workspace, and system routes.
- Bound every route to an active `org_members` record for the authenticated user.
- Limited imports to owner/admin; allowed mutations for owner/admin or the existing `model:write` organization-role permission.
- Scoped system, assignment, and assessment lookups by `org_id` and created assignments plus active-control assessments in one transaction.
- Added transparent readiness counts only; no compliance score or certification language.
- Added scoped workspace/system creation so new records receive the path organization ID.

`apps/backend/api/routes` is a symlink to `../src/api/routers`, so the new router is stored at `apps/backend/src/api/routers/governance_assurance.py` and resolves as `api.routes.governance_assurance`.

## TDD evidence

The initial focused route suite failed before the router was mounted (405 on the planned route). The final suite exercises the real app with overridden active-user and database dependencies, active membership, import denial, permission-based mutation, assignment idempotency, active-control initialization, cross-org assignment/assessment denial, and count-only readiness.

## Verification

```text
cd apps/backend && uv run pytest tests/test_governance_assurance_routes.py -q
6 passed

cd apps/backend && uv run pytest tests/test_governance_assurance_models.py tests/test_framework_catalog_service.py -q
13 passed

tooling/check_backend_layer_boundaries.sh
Backend layer boundary checks passed.

tooling/check_no_archive_imports.sh
No archive import violations found.
```

## Concern

The existing repository emits unrelated Pydantic/SQLAlchemy deprecation warnings and has an ambiguous `User.organizations` mapper. The route tests deliberately use Core table inserts and a shared in-memory SQLite connection so authorization remains real without loading that unrelated mapper.

## Review remediation

- Workbook imports now use a savepoint when membership authorization has already opened the request transaction, then commit the successful catalog persistence atomically.
- `workbookPath` is constrained to a relative `.xlsx` file below `GOVERNANCE_FRAMEWORK_IMPORT_ROOT` (or the secure temp-data default), with resolved-path containment, regular-file, and 50 MiB checks. The successful import test uses a production-shaped workbook and the explicit `GOVERNANCE_FRAMEWORK_IMPORT_STRICT=false` test seam.
- Assignments with no active controls are persisted successfully and report zero for every readiness count. Failed assessment insertion rolls back the assignment.
- Readiness now derives missing and stale evidence from accepted `GovernanceControlEvidence` mappings and evidence-run timestamps, using the control frequency; assessment status remains a separate workflow count.

```text
cd apps/backend && uv run pytest tests/test_governance_assurance_routes.py tests/test_governance_assurance_models.py tests/test_framework_catalog_service.py -q
22 passed
```
