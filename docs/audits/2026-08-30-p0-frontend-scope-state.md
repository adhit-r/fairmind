# P0 frontend scope-state evidence

Date: 2026-08-30

## Result

Evaluation state now uses one collision-safe key over organization, workspace,
system, plan, and run identifiers. The `/tests` workbench is keyed by its exact
organization/system scope, so selected plans, plan-form input, preflight state,
action banners, busy state, and the local controller cannot survive a scope
change. Preflight state adds the selected plan identifier and renders a masked
loading state until that exact plan's request settles.

Legacy and Assurance V2 detail pages bind the complete payload/loading/error
tuple to the current run scope. A route, organization, workspace, or system
change therefore masks prior detail data and failures during the render before
effects run. The V2 retry path writes only while its originating scope remains
current and ignores the controller's stale-result signal.

## TDD evidence

The new browser test first failed because the successful old-system action
banner remained visible after `system-2` and its plan became active. The new
scope-key unit failed first because the production helper did not exist. After
the implementation:

```text
CI=1 bunx playwright test tests/evaluation-runs.spec.ts \
  --project=chromium --workers=1 --retries=0 --reporter=line
16 passed

bun test src
105 passed, 0 failed

bun run typecheck
passed

bun run build
compiled, typechecked, and generated 54/54 pages
```

The production build retained existing warnings for metadata viewport exports,
`metadataBase`, stale Browserslist data, inferred workspace root, and absent
local Authentik configuration. None was introduced by this slice.

## Claim boundary

This closes only frontend state keying and synchronous prior-scope masking. It
does not claim that legacy parsed API records are bound to the requested
organization/system/plan/run; that response-validation work remains the next
open checklist row. It also does not establish production SSO, deployment, or
release readiness.
