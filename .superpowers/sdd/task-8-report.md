# Task 8 report: assurance summary, redirects, and integrated verification

## Outcome

Task 8 replaces the AI Governance overview's inferred evidence/compliance scoring with the organization-scoped readiness contract and consolidates Reports & Assurance around a version-pinned, evidence-led summary.

Implemented:

- company, AI-system, immutable framework version, catalog hash, and evidence-period scope;
- blocker-first Overview using `blockingFindings`, `missingEvidence`, and `staleEvidence` before readiness aggregates;
- explicit accepted, applicable, ready-for-review, partial, not-started, and not-applicable counts;
- Reports & Assurance evidence index with full content hashes and evaluation versions;
- unresolved-finding disclosure that distinguishes known counts from incomplete control detail;
- accepted/rejected mapping decision register with actor, time, and rationale;
- evaluation limitations and tenant-scoped evidence-run history;
- read-only auditor mode on the same `/reports` route, selected by permission or `mode=auditor`;
- builder navigation back to control assessment and evidence mapping review;
- preservation links to Evidence & Evaluations, Findings, and Remediation from Overview;
- legacy redirects for Audit Reports, Compliance, and Remediation Wizard bookmarks; and
- operator documentation for workbook import, activation, evidence ingestion, mapping review, claim boundaries, and validation.

No certification or automatic-compliance claim is rendered. Unknown or unavailable values remain explicit rather than becoming zero.

## TDD evidence

The Task 8 Playwright tests were added before production changes. The initial three-test run failed at the new Overview heading, new Reports heading, and auditor-mode label because those surfaces did not exist. After implementation, the focused tests and complete assurance journey passed.

## Verification

| Check | Result |
| --- | --- |
| `RATE_LIMIT_REQUESTS=10000 uv run pytest tests/test_governance_assurance_models.py tests/test_framework_catalog_service.py tests/test_governance_assurance_routes.py tests/test_governance_evidence_runs.py -q` | 49 passed |
| `bun test src/lib/api/hooks/useGovernanceAssurance.test.ts` | 6 passed |
| `./node_modules/.bin/tsc --noEmit --pretty false` | passed |
| `npx playwright test tests/governance-assurance.spec.ts --project=chromium --workers=1 --reporter=line` | 15 passed |
| `npm run build` | passed; 54 routes generated |
| `tooling/check_backend_layer_boundaries.sh` | passed |
| `tooling/check_no_archive_imports.sh` | passed |
| `git diff --check` | passed |

The first integrated backend run used the application's default `RATE_LIMIT_REQUESTS=100`. After 40 passing tests, nine later HTTP validation tests received HTTP 429 instead of their expected 422 because the test suite crossed the shared middleware budget. The fresh verification run raised only the test-process request allowance to 10,000 and all 49 focused tests passed. Production defaults and source files were not changed.

The build continues to report existing metadata viewport, workspace-root inference, Browserslist age, and missing optional Authentik public-configuration warnings. None fails compilation or static generation.

## Recorded baseline

The unrelated repository baseline remains `ModuleNotFoundError: No module named 'api.models'` during collection of `test_fairness_evidence_profile_route.py` in the backend package context. Task 8 does not touch that compatibility path. The focused assurance suite is the validated boundary for this work.
