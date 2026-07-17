# Task 4: Evidence runs and reviewed mappings

## Delivered

- Added immutable, organization-scoped evidence-run ingestion with canonical compact JSON and SHA-256 content hashes.
- Repeated identical envelopes return the existing run; an identical source-run identity with changed content returns a conflict.
- Stored one compact `GovernanceEvidence` artifact per run, linked to the run; only artifact references and summary data are stored, not raw outputs.
- Added explicit-control candidate mappings and authenticated accept/reject review history. Mapping review never updates a control assessment automatically.
- Added the four organization-scoped evidence-run and mapping routes, third-party assessor identity/independence validation, cross-organization denial, and workbook frequency parsing for `Every 3 months`, `Every 6 months`, and `Every 12 months`.
- Extended only the existing generic run, evidence, and mapping schema plus migration 009; no framework-specific tables or workflow engine were added.

## Verification

```text
cd apps/backend
uv run pytest tests/test_governance_evidence_runs.py -q --disable-warnings
# 7 passed

uv run pytest tests/test_governance_evidence_runs.py tests/test_governance_assurance_models.py tests/test_framework_catalog_service.py tests/test_governance_assurance_routes.py -q --disable-warnings
# 29 passed

cd ../..
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh
git diff --check
# all passed
```

## Concern

The focused suite emits pre-existing dependency deprecation warnings. No new failures were observed.
