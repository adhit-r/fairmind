# Task 6 Report: Frameworks & Controls Workbench

## Outcome

Replaced the legacy score-oriented dashboard at `/compliance-dashboard` with a system-scoped governance workbench for version activation, control filtering, inline evidence trace, and assessment updates.

The workbench uses the existing Organization and AI-system contexts plus the Task 5 governance assurance hooks. UI language is limited to readiness and review state.

## Implemented

- Framework family and immutable version selection.
- Authorized AIUC-1 April, 2026 activation for the currently selected AI system.
- Exact first-run guidance: `Activate a framework version for this AI system`.
- Readiness summary strip with transparent counts rather than an unexplained score.
- Dense control table showing framework ID, requirement, obligation, application, owner, assessment state, accepted evidence count, latest evaluation, freshness, and open findings when provided by the assurance payload.
- Mandatory-control, missing-accepted-evidence, and text filters.
- Inline A006.1 trace with parent requirement, mapping rationale, evidence timeline, and owner/applicability/state updates.
- Keyboard activation, expansion, filtering, and native form controls with visible focus states.
- Mobile stacked records that preserve labels and keep the trace inline.
- Skeleton loading, catalog-empty, filtered-empty, error, and retry states.
- A minimal `useAuth` callback-stability repair required to stop `AuthGuard` from repeatedly remounting authenticated dashboard pages during Playwright runs.

## TDD Evidence

The focused Playwright spec was written first and observed failing three tests against the legacy page. The failures were caused by the missing workbench and missing accessible controls. After implementation, the same route-mocked tests cover:

1. Keyboard selection and activation of AIUC-1 April, 2026.
2. Mandatory and missing-evidence filtering.
3. A006.1 inline trace expansion.
4. Owner, applicability, and assessment-state updates.
5. Readiness-only language.
6. Loading, empty, recoverable error, desktop, and mobile behavior.

## Validation

- `cd apps/frontend && npx tsc --noEmit`
- `cd apps/frontend && npx playwright test tests/governance-assurance.spec.ts --project=chromium --workers=1 --reporter=line`
- `cd apps/frontend && npm run build`
- `git diff --check`
- Desktop and 390 px mobile screenshots inspected from the route-mocked journey.

## Integration Note

The frontend accepts enriched assessment fields for obligation, application, evidence counts, evaluation freshness, findings, parent requirement, rationale, and trace items. The current base backend assignment-control route returns the core assessment fields only. Missing enriched fields degrade explicitly to `Not specified`, `Not run`, `Missing`, or zero rather than inventing assurance data. A backend response enrichment can replace those fallbacks without changing this workbench.
