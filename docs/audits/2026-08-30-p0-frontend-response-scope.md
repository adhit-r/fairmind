# P0 frontend response-scope evidence

Date: 2026-08-30

## Result

The legacy Evaluation Runs controller now treats runtime schema validation as
necessary but insufficient. Every parsed plan or run is checked against the
organization and system in the request before it can be returned or published.
Initial list loads reject the entire affected segment; post-commit targeted
refreshes keep the last known-good segment and expose the mismatch as an error.
The strict plan and run schemas also require the backend's canonical
`contractVersion: "1.0.0"`, so these guards operate on the real versioned wire
contract rather than an incomplete mock-only shape.

Direct responses additionally bind to the identifier named by the request:
plan activation and preflight bind to the requested plan, run creation binds to
the requested plan, and run detail and Passport linking bind to the requested
run. A successful Passport-link response must also confirm the exact evidence
run and Passport revision that were submitted before the UI treats the link as
committed.

`selected_org_id` remains only a persisted UI preference. `OrgContext` accepts
it only when it matches an organization returned by the current-user API. The
API client neither reads that key nor appends it to request paths or query
strings; its existing unit contract proves that caller-supplied route authority
is preserved unchanged.

## TDD evidence

Each response boundary was introduced through a RED-to-GREEN cycle. Before the
guards, schema-valid foreign plan/run lists were published, wrong run details
and preflights resolved successfully, mutation responses for different
plans/runs were accepted, and mismatched Passport acknowledgements triggered a
follow-up refresh. The new tests failed on those observable results before the
shared scope and identifier guards were added.

The exact security review then exposed a pre-existing contract-fixture gap:
backend plan/run serializers emit `contractVersion`, while the strict frontend
schemas and mocks omitted it. A public-controller tracer test using a
wire-shaped fixture failed before both schemas were pinned to `1.0.0`; a
negative contract test prevents either schema from accepting another version,
and the shared unit and Playwright fixtures mirror the canonical contract.

Final verification:

```text
bun test src/lib/api/hooks/useEvaluationRuns.test.ts
37 passed, 0 failed

bun test src
120 passed, 0 failed

bun run typecheck
passed

CI=1 bunx playwright test tests/evaluation-runs.spec.ts \
  --project=chromium --workers=1 --retries=0 --reporter=line
16 passed

bun run build
compiled, typechecked, and generated 54/54 pages
```

The production build retained existing warnings for metadata viewport exports,
`metadataBase`, stale Browserslist data, inferred workspace root, and absent
local Authentik configuration. None was introduced by this slice.

## Review and claim boundary

Independent standards review found no violation or code smell. Spec review
requested direct foreign-scope coverage for every public response path; one
compact table-driven controller test now covers activation, run creation, run
detail, and Passport linking in addition to the list and create-plan cases.

The legacy route contract supplies organization and system identifiers, not a
workspace identifier, so this slice does not invent workspace authority or
claim to validate it. Assurance V2 retains its separate workspace-bound
contract. This checkpoint does not establish production SSO, deployment, or
release readiness.
