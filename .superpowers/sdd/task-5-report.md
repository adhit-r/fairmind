# Task 5 Report: Frontend assurance contract and navigation

## Delivered

- Added organization-scoped governance assurance endpoint builders.
- Added typed catalog, framework-version, assignment, assessment/readiness, evidence-run, and reviewed-mapping hooks.
- Normalized snake_case and camelCase API payloads at the contract boundary.
- Added mapping review payload support with `reviewVersion` for optimistic concurrency.
- Consolidated `Govern & Prove` to Overview, AI Systems, Frameworks & Controls, Evidence & Evaluations, Findings, and Reports & Assurance.
- Kept the existing Assess tools unchanged and made nested governance routes retain their active sidebar state.

## Validation

- `bun test src/lib/api/hooks/useGovernanceAssurance.test.ts` passes, 4 tests.
- `./node_modules/.bin/tsc --noEmit --pretty false` passes.
- `npm run build` passes.

## Existing build notices

- Next.js reports the existing multi-lockfile workspace-root warning.
- The build reports existing Browserslist, Authentik configuration, and metadata viewport warnings. No dependency or unrelated configuration changes were made.

## Review follow-up

- Corrected the framework-import contract to the backend import-result payload.
- Added the distinct raw control-assessment update-result contract and refreshed joined controls after mutation.
- Preserved an explicit `owner: null` update while continuing to ignore null status and applicability values.
- Stabilized assurance refresh and mutation callbacks with their individual refresh dependencies.
- Added focused frontend contract coverage and a backend regression test for owner clearing.
