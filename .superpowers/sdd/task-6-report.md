# Task 6 Report: Frameworks & Controls Workbench

## Outcome

Replaced the legacy score-oriented dashboard at `/compliance-dashboard` with a system-scoped governance workbench for version activation, control filtering, inline evidence trace, and assessment updates.

The workbench uses the existing Organization and AI-system contexts plus the Task 5 governance assurance hooks. UI language is limited to readiness and review state.

## Implemented

- Framework family and immutable version selection.
- Authorized AIUC-1 April, 2026 activation for the currently selected AI system.
- Exact first-run guidance: `Activate a framework version for this AI system`.
- Readiness summary strip with transparent counts rather than an unexplained score.
- Readiness counts remain skeletons or explicit unknowns until the scoped summary request resolves; unresolved data is never rendered as zero.
- Dense control table showing framework ID, requirement, obligation, application, owner, assessment state, accepted evidence count, latest evaluation, freshness, and open findings when provided by the assurance payload.
- Backend enrichment from persisted control definitions, evidence mappings, evidence runs, and evidence artifacts; fields without a schema link, including control-specific findings, remain explicitly unknown.
- Mandatory-control, missing-accepted-evidence, and text filters.
- Inline A006.1 trace with parent requirement, mapping rationale, evidence timeline, and owner/applicability/state updates.
- Organization owner/admin and `model:write` authorization for activation and assessment mutations, with an inspection-only trace for read-only roles.
- The existing organization bootstrap route now supplies effective custom-role permissions from `org_roles`; owner/admin authorization remains role-based.
- Scope-keyed request state and stale-response suppression so changing AI systems clears the prior assignment before the next fetch resolves.
- Persisted AI-system selection precedence over the initialized fallback system.
- Keyboard activation, expansion, filtering, and native form controls with visible focus states.
- Mobile stacked records that preserve labels and keep the trace inline.
- Skeleton loading, catalog-empty, filtered-empty, error, and retry states.
- A minimal `useAuth` callback-stability repair required to stop `AuthGuard` from repeatedly remounting authenticated dashboard pages during Playwright runs.

## TDD Evidence

The focused Playwright spec was written first and observed failing three tests against the legacy page. Review regressions were also observed red before the backend enrichment and stored-system selection fixes. After implementation, the route-mocked tests cover:

1. Keyboard selection and activation of AIUC-1 April, 2026.
2. Mandatory and missing-evidence filtering.
3. A006.1 inline trace expansion.
4. Owner, applicability, and assessment-state updates.
5. Readiness-only language.
6. Loading, empty, recoverable error, desktop, and mobile behavior.
7. A delayed two-system switch with no stale controls or stale assessment mutation.
8. Dynamic framework names plus admin, read-only, and `model:write` access modes.
9. Delayed readiness resolution without provisional zero counts.

The backend route regression seeds a real accepted evidence mapping and asserts the full enriched A006.1 response. An organization-list contract test asserts effective custom-role permissions and owner role preservation through the real bootstrap route. A focused system-selection test asserts that a valid persisted selection wins over the initialized fallback.

## Validation

- `cd apps/frontend && npx tsc --noEmit`
- `cd apps/backend && uv run pytest tests/test_governance_assurance_routes.py -q` — 11 passed
- `cd apps/backend && uv run pytest tests/test_organization_list_contract.py -q` — 1 passed
- `cd apps/frontend && bun test src/components/workflow/SystemContext.test.ts` — 2 passed
- `cd apps/frontend && npx playwright test tests/governance-assurance.spec.ts --reporter=line` — 7 passed
- `cd apps/frontend && npm run build`
- `tooling/check_backend_layer_boundaries.sh`
- `tooling/check_no_archive_imports.sh`
- `git diff --check`
- Desktop and 390 px mobile screenshots inspected from the route-mocked journey.

## Data Truthfulness

The assignment-control route now returns explicit nullable fields for definition metadata, evidence counts, latest evaluation provenance, freshness, parent requirement, rationale, and evidence trace. The frontend preserves those nullable values and renders unknowns as `Not specified`, `Not evaluated`, or `Not linked`; filters only match known mandatory or known zero-evidence values. It does not convert unknown evidence or findings into zero.
