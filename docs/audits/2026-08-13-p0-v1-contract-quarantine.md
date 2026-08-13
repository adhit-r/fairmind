# P0 legacy contract quarantine release evidence

Date: 2026-08-13

## Closed roadmap row

Existing evaluation plans and runs are retained as assurance contract `1.0.0`
records without invented target, suite, plan-hash, trust-policy, lifecycle, or
execution-envelope bindings. They remain readable for historical use. When
Assurance V2 is enabled, the legacy API rejects plan creation, activation, run
preparation, and Passport linking with `contract_upgrade_required`; preflight
directs the user to clone the record into a bound v2 plan.

## Evidence

- Migration 013 defaults pre-existing plans and runs to `1.0.0` and leaves all
  v2-only identity fields null.
- The upgrade regression starts at the migration 012 schema, inserts a real
  legacy plan and run, applies the SQLite 013 migration, verifies the original
  records are unchanged, and proves that target, suite, and trust-policy
  catalogs remain empty.
- The route regression proves legacy lists, detail, and preflight remain
  readable while four mutation paths fail without creating an audit event or
  database record.
- Contract foreign keys require each run to retain the same contract version
  as its parent plan. Existing records are not upgraded in place to v2.

Focused verification command:

```bash
uv run pytest -q \
  tests/test_evaluation_assurance_v2_models.py::test_migration_013_marks_existing_records_v1_without_fabricating_bindings \
  tests/test_evaluation_assurance_v2_models.py::test_legacy_plan_and_run_default_to_v1_contract \
  tests/test_evaluation_runs.py::test_v1_mutations_are_quarantined_when_assurance_v2_is_enabled
```

Result: `3 passed`.

Broader verification:

```text
242 passed, 2 skipped in the combined P0 integration slice.
Repository-wide backend: 2,132 passed; 27 inherited failures and 57 inherited
setup errors remain, matching the established legacy failure floor.
23 Playwright governance-assurance tests passed.
Frontend typecheck and production build passed.
Backend layer boundary checks passed.
No archive import violations found.
git diff --check passed.
```

The combined slice used a disposable local PostgreSQL 14 instance for the
environmental migration and integrity checks. The two skips are unrelated
environment-gated checks. The legacy-contract regression itself remains
SQLite migration-parity and application-route evidence; no native PostgreSQL
proof is inferred for that row.

## Claim boundary

This is SQLite migration-parity and application-route evidence for legacy
contract quarantine. It does not claim a native PostgreSQL run of that legacy
upgrade path, deployment, worker execution, automatic enforcement, or
production readiness.
