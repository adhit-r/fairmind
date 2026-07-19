# Task 3 Report: Typed frontend Evaluation Runs client

## Delivered behavior

- Added the seven organization-and-system-scoped endpoint builders for evaluation plans, activation, preflight, plan run preparation, run lists, run details, and exact Evidence Passport revision linking.
- Added exact TypeScript transport unions and strict raw camelCase Zod 4 schemas for plans, preflight results, runs, partial component verdicts, and partial risk-dimension verdicts. Unknown values, extra snake_case fields, and unsupported verdict keys are rejected at runtime.
- Added a dependency-free generation-token controller used directly by `useEvaluationRuns`. It performs no request without both scope IDs, clears missing scope to a non-loading empty state, loads plan and run lists together, and prevents stale scope/list/detail results from replacing current state.
- Added exact plan, activation, preflight, run preparation, detail, and Passport-link mutations. Successful plan mutations refresh only plans; successful run mutations refresh only runs; preflight/detail do not refresh; failed mutations never create optimistic run state.
- Added named `StaleEvaluationResultError` behavior for superseded detail requests, including superseded requests that later fail rather than return a valid payload.
- Extended `ApiResponse` backward-compatibly: `error` remains an optional string and `apiError` optionally preserves HTTP status, stable workflow code, detail, and next action. A strict Zod envelope accepts only the ten documented Task 2 workflow codes; unknown codes, missing or malformed `nextAction`, and extra fields fall back to a non-actionable string error while retaining HTTP status.
- Hardened overlapping full and mutation-targeted refreshes. Targeted plan/run completion reaches a terminal loading state, older full-refresh data cannot overwrite the affected list, and still-current data for the unaffected list is retained.
- Kept committed POST results truthful when only the follow-up list GET fails. The mutation resolves with its server DTO, the existing list is left unchanged without optimistic insertion, and the refresh error remains in controller state; a scope change during refresh still rejects with `StaleEvaluationResultError`.
- Converted rejected superseded detail promises to `StaleEvaluationResultError` while preserving the original rejection for the current detail request.
- Tightened offline classification to `navigator.onLine === false`, so Bun or browsers with an undefined `onLine` value preserve the real HTTP classification.
- Added no packages and did not touch Task 4 UI or backend files.

## TDD evidence

- Initial RED command: `cd apps/frontend && bun test src/lib/api/hooks/useEvaluationRuns.test.ts`
- Initial RED result: exit 1; zero tests passed because `./useEvaluationRuns` did not exist (`Cannot find module`).
- HTTP-status hardening RED: the focused suite had 12 passes and one failure because a structured HTTP 422 response was incorrectly classified with status 0.
- Stale-detail hardening RED: the focused suite had 12 passes and one failure because a superseded failed request returned `EvaluationApiRequestError` instead of `StaleEvaluationResultError`.
- Independent-review RED command: `cd apps/frontend && bun test src/lib/api/hooks/useEvaluationRuns.test.ts`
- Independent-review RED result: 14 passed and six failed, reproducing stranded loading during targeted/full overlap, false mutation failure after committed POSTs, raw rejected stale detail promises, stale scope rejection loss, and permissive malformed workflow-code forwarding.
- Focused GREEN command: `cd apps/frontend && bun test src/lib/api/hooks/useEvaluationRuns.test.ts`
- Focused GREEN result after review remediation: 20 passed, zero failed, exit 0.
- Regression command: `cd apps/frontend && bun test src/lib/api/hooks/useGovernanceAssurance.test.ts src/lib/api/hooks/useEvaluationRuns.test.ts`
- Regression GREEN result after review remediation: 28 passed, zero failed, exit 0.
- Type check: `cd apps/frontend && bunx tsc --noEmit --incremental false`: passed, exit 0.
- `git diff --check`: passed before commit.

## Files changed

- `apps/frontend/src/lib/api/endpoints.ts`
- `apps/frontend/src/lib/api/api-client.ts`
- `apps/frontend/src/lib/api/hooks/useEvaluationRuns.ts`
- `apps/frontend/src/lib/api/hooks/useEvaluationRuns.test.ts`
- `apps/frontend/src/lib/api/hooks/index.ts`

## Commits

- Initial commit SHA: `c21ae0296c07e447bd67eac6f47355f13854039b`
- Initial message: `feat(evaluations): add typed evaluation runs client`
- Review-fix commit SHA: `ebb438f63627a79d1695a3f846fd3874fa54bd9a`
- Review-fix message: `fix(evaluations): harden client concurrency contracts`

## Concerns

- The hook is unit-tested through the same dependency-free controller it delegates to because this frontend has no DOM hook-renderer dependency and Task 3 forbids adding one. Task 4's Playwright acceptance tests remain the live React integration proof.
- The existing API client still appends the selected `org_id` query parameter to GET requests under `/api/v1/`; the new paths are already organization-scoped, but this legacy behavior was deliberately left unchanged and the authoritative organization remains in the path.
