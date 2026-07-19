# Task 4: Original-shell Evaluation Runs workspace and icon language

## Delivered

- Replaced the shell-less legacy Test History route with an organization- and real-system-scoped Evaluation Runs workbench inside FairMind's original white, black, orange, and teal dashboard shell.
- Kept the singular legacy `/test` route exception segment-exact, added exactly one Evaluation Runs child under Assess, and corrected run-detail navigation to `/tests/{runId}`.
- Added shared `FramedIcon` and `FramedIdentity` primitives with 44px controls, accessible names, visible focus, reduced-motion handling, expanded/collapsed behavior, a centralized approved portrait URL, and a labelled initials fallback.
- Made synthetic fallback systems non-renderable and non-queryable. A missing real system now shows an explicit choose-system state and sends no evaluation request.
- Added the compact, locally validated plan form; plan activation; automatic preflight; truthful worker-blocked and external/imported evidence-link paths; separate loading, empty, server-error, and focused action-error states; and a locally scrollable recent-runs table.
- Kept technical execution status separate from governance verdict. The detail route shows distinct component and risk axes, exact evidence-run and Passport revision identifiers, `Not assessed` for absent axes, and `Awaiting evidence` instead of invented artifacts.
- Updated `DESIGN.md` with the functional icon, illustrated identity, evaluation-state, dense workbench, accessibility, and prohibited-style rules.
- Contained mobile overflow at the dashboard shell boundary while preserving horizontal table scrolling inside the bordered recent-runs surface.

## TDD evidence

The initial Playwright acceptance suite was written against the untouched legacy route and failed 9/9. Failures proved the old `/tests` route was shell-less, exposed the legacy page/schema, lacked workbench/preflight states, and did not satisfy the shared identity or responsive contracts.

A read-only completion review then identified three Important issues and no Critical issues. New tests produced a second RED checkpoint for the missing-organization gate and the absent search focus outline. The evaluation request spy was also moved ahead of scope dispatch so a request made with any incorrect organization or system ID can no longer false-pass the no-request assertion. All three review findings are resolved.

After implementation:

```text
cd apps/frontend
bun run test tests/evaluation-runs.spec.ts --project=chromium --reporter=line
# 10 passed

bun test src/lib/api/hooks/useEvaluationRuns.test.ts src/lib/api/hooks/useGovernanceAssurance.test.ts
# 28 passed, 0 failed

bunx tsc --noEmit --incremental false
# passed

bun run build
# passed with network access; 54/54 static pages generated

git diff --check
# passed

node /Users/adhi/.agents/skills/impeccable/scripts/detect.mjs --json <Task 4 UI files>
# []
```

The restricted-network build first failed only while fetching the repository's existing Raleway Google Font. The unchanged build passed when rerun with network access. Existing `metadataBase`, viewport-export, Authentik-configuration, and Browserslist-age messages remain baseline warnings.

## Visual evidence

- Desktop: `/tmp/fairmind-evaluation-runs-desktop.png` — 1440x1000 viewport capture at scroll top.
- Mobile: `/tmp/fairmind-evaluation-runs-mobile.png` — 390x844 viewport, full-page capture initiated at scroll top.
- Failure fallback proof: `/tmp/fairmind-evaluation-runs-fallback.png` — approved portrait request aborted and labelled initials fallback rendered.

## Follow-up

The approved profile portrait remains a single centralized remote fallback because no approved local source asset exists in this slice. Replace that constant with a local licensed asset when one is supplied; no route or shell duplicates the URL.

## Commit

`ab9ee17`
