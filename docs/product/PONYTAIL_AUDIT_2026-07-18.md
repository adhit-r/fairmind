# FairMind Ponytail Audit — 18 July 2026

## Purpose and boundary

This audit identifies deletion and simplification candidates that can reduce FairMind's maintenance surface without weakening the selected Evidence Workbench recovery. It is a structural reachability and dependency audit. It does not conclude that any candidate is incorrect, insecure, slow, or low quality. A zero-inbound module may still be loaded dynamically, imported from an external package context, used by a script, or retained for a supported compatibility path.

The user requested autonomous execution, but this document deliberately separates evidence gathering from deletion. The current and sibling assurance worktrees are dirty and divergent. No cleanup batch should be applied to either dirty worktree. Cleanup begins only in the isolated recovery worktree and only after the assurance route, evaluator adapters, tests, scripts, and both Python import contexts define an explicit live closure.

## Executive result

The conservative reduction opportunity is approximately 25,000 source lines and 34 direct dependencies. That number is an upper bound conditioned on per-batch reference checks, builds, tests, runtime route discovery, migration checks, and package-root/repository-root import checks.

The largest candidates are unreachable service slabs, not visual components. Deleting them before the assurance integration would be unsafe because the target adapters may reuse a small portion of the current evaluator code. The correct order is dependency manifests, zero-inbound leaves, inactive infrastructure, legacy services, then application/domain service batches. Compatibility symlinks are last.

## Ranked findings

| Rank | Candidate surface | Audit signal | Estimated reduction | Decision |
| --- | --- | --- | --- | --- |
| 1 | Unreachable or test-only service modules | 40 modules: 18 application modules, 9 legacy modules, and 13 domain modules have no inbound production closure in the current static graph | 20,730 lines: 14,897 application, 2,980 legacy, 2,853 domain | Quarantine until the evaluator registry and assurance router are integrated. Delete in small path-specific batches against an explicit import/router/test manifest. |
| 2 | `apps/backend/fairness_library/` | Approximately 2,579 lines appear unused by the active runtime except `india_regulatory_frameworks` | About 2,579 lines, less the retained India mapping | Preserve `india_regulatory_frameworks` and any transitive resources. Delete the remainder only after package-root and repository-root import scans plus focused India tests. |
| 3 | Duplicate middleware | Approximately 1,440 lines duplicate or bypass the preferred authentication, organization, validation, and error-handling paths | About 1,440 lines | Establish the mounted middleware chain from `apps/backend/api/main.py`, then remove one inactive family at a time with auth and cross-organization negative tests. |
| 4 | Zero-inbound frontend modules | 20 modules have no static inbound import from active source or tests | About 1,348 lines | Safest source deletion lane after checking Next.js route conventions, dynamic imports, barrel exports, Playwright selectors, and build output. |
| 5 | Orphan compliance surfaces | Overlapping compliance routes and components are outside the selected six-task information architecture | About 895 lines in the first confirmed orphan set | Redirect only after the canonical `/compliance-dashboard` flow reaches parity; then remove page-specific code and endpoint constants. |
| 6 | Custom dependency-injection and interface scaffolding | Approximately 510 lines add abstraction without a demonstrated second implementation in the active closure | About 510 lines | Inline only after the assurance integration settles the application ports. Keep the evidence-ingestion port because it has multiple evaluator adapters. |
| 7 | Unused registry | A 298-line registry has no active consumer in the mounted route closure | 298 lines | Remove after confirming no plugin, CLI, migration, or dynamic import loads it. Do not replace it with a new generic registry. |
| 8 | Old health implementation | A 215-line health path is outside the preferred entrypoint and current health contract | 215 lines | Retain one minimal readiness/liveness implementation and remove the inactive path after deployment and pilot scripts are updated. |
| 9 | Dependency manifests | Static import audit found 15 ML, 13 frontend, and 6 backend direct-dependency candidates | 34 direct dependencies plus lockfile transitive reductions | Remove one ecosystem batch at a time and regenerate only its managed lockfile. A static absence is insufficient without build, test, CLI, and optional-feature checks. |
| 10 | Catch-all `OPTIONS` handling | Approximately 30 lines duplicate framework CORS behaviour | About 30 lines | Remove only after browser preflight tests confirm configured CORS middleware covers required origins, headers, methods, and credentials. |
| 11 | Unused settings | 22 settings have no active read in the current static closure | Configuration surface, not material line count | Remove only after scanning deployment manifests, env templates, scripts, and `os.getenv`/dynamic access. Document any renamed setting. |
| 12 | Thin adapters | Two adapters total about 16 lines and add no transformation or isolation | 16 lines | Inline at the call site after the canonical evidence adapter interface is fixed. |
| 13 | Compatibility symlink namespaces | Six namespaces support mixed repository-root and package-root imports | Indirect reduction and lower import ambiguity | Last operation only. Validate both execution contexts and update all scripts, tests, package declarations, and deployment commands first. |

## Protected recovery closure

The following areas are protected from deletion until their replacement has passed acceptance tests:

- `apps/backend/src/domain/environmental/`
- `apps/backend/src/application/services/environmental_service.py`
- `apps/backend/src/api/routers/environmental.py`
- `apps/backend/src/api/routers/approvals.py`
- `apps/backend/src/infrastructure/db/database/governance_models.py`
- `apps/backend/tests/test_environmental*.py`
- `apps/frontend/src/app/(dashboard)/ai-governance/`
- `apps/frontend/src/lib/api/hooks/useAIGovernance.ts`
- The assurance-worktree implementations of `governance_assurance.py`, `framework_catalog_service.py`, `governance_assurance_service.py`, its `009_governance_assurance.sql` source migration renumbered to `011_governance_assurance.sql` during integration, and their focused tests
- The substantive statistical evaluators selected by the Sprint 1 tabular or LLM adapter
- `apps/backend/fairness_library/india_regulatory_frameworks` until India compliance imports and tests prove it can move or be removed

Generated output, archives, vendored code, virtual environments, and caches are excluded from the source-line reduction estimate. They may be governed by separate repository hygiene rules, but their presence does not justify deleting active source.

## Safe cleanup sequence

### Gate 0 — establish a reproducible recovery baseline

1. Record `git status --short`, branch name, HEAD, and `git diff --stat` for the current and assurance worktrees.
2. Create a separate `codex/fairmind-evidence-recovery` worktree from the agreed integration base.
3. Integrate the assurance commit line and the three post-merge-base FairMind-E commits without carrying uncommitted files implicitly.
4. Run the focused assurance, environmental, authorization, frontend, and architecture checks before any deletion.
5. Generate a machine-readable live-closure manifest covering mounted routers, imports, scripts, tests, dynamic import strings, Next.js routes, migrations, and packaging entrypoints. Commit that manifest with the integration change so later deletions can be reviewed against a stable baseline.

Baseline commands:

```bash
git status --short
git branch --show-current
git rev-parse HEAD
tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh
cd apps/backend && uv run pytest tests/test_environmental*.py -q
cd ../frontend && npm run build
```

Expected evidence: recorded dirty-state snapshots, a clean isolated recovery worktree, green architecture guards, green selected backend tests, and a successful frontend production build. Existing unrelated baseline failures remain named rather than being suppressed.

### Gate 1 — dependency manifest batches

Process ML, frontend, and backend manifests separately. For each candidate package:

1. Search imports, `require`, dynamic import strings, CLI invocations, plugin declarations, build configuration, tests, notebooks, and deployment scripts.
2. Remove the package using the ecosystem package manager so the lockfile remains consistent.
3. Run that application's build and test gates.
4. Revert only the candidate removal if the gate fails; do not weaken a test to preserve the deletion.

Required gates:

```bash
cd apps/frontend && npm run build && npm run test
cd ../website && npm run build
cd ../docs && npm run build
cd ../backend && uv run pytest
cd ../ml && python3 -m compileall -q .
```

The ML command is a syntax gate only. Any package used by a documented ML pipeline, notebook, optional evaluator, or CLI remains until that workflow has a focused execution test.

### Gate 2 — zero-inbound frontend leaves

Delete the 20 frontend candidates in batches grouped by route or feature, not as one large change.

For every batch:

1. Confirm no import, barrel export, `next/dynamic`, string route, test selector, navigation entry, or API endpoint constant references the files.
2. Confirm the files are not `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `route.ts`, or other filesystem-routed Next.js modules unless the route is intentionally redirected.
3. Run TypeScript, relevant component tests, Playwright coverage for affected routes, and the production build.

```bash
cd apps/frontend
./node_modules/.bin/tsc --noEmit --pretty false
npm run test
npm run build
```

Expected evidence: no unresolved imports, no lost route, no changed selected organization/system context, and a green build.

### Gate 3 — inactive registry, health, middleware, and catch-all preflight

Sequence these as four independent changes:

1. Remove the unused registry after runtime import tracing shows no loader.
2. Consolidate health checks onto the mounted `api.main:app` implementation and update deployment probes.
3. Remove duplicate middleware only after documenting the exact mounted order and adding cross-organization/authentication negative tests.
4. Remove catch-all `OPTIONS` handling only after browser preflight tests pass through configured CORS middleware.

Required evidence includes the generated OpenAPI route list before and after, unchanged intended route count, green `/health` and readiness probes, denied unauthenticated access, denied cross-organization IDs, and successful browser preflights.

### Gate 4 — fairness-library and legacy service batches

1. Preserve the India regulatory mapping closure.
2. Split legacy service candidates by owning router or script.
3. Remove only modules with no live router, CLI, migration, background job, test, documentation contract, or evaluator-adapter dependency.
4. Run package-root and repository-root imports after each batch.

```bash
python3 -c "import apps.backend.api.main"
cd apps/backend && uv run python -c "import api.main"
cd ../.. && tooling/check_backend_layer_boundaries.sh
tooling/check_no_archive_imports.sh
```

Expected evidence: both import contexts succeed, mounted routes remain intentional, and India/framework tests remain green.

### Gate 5 — application and domain service slabs

The 31 application/domain candidates account for most of the potential reduction and carry the highest reuse risk. Process them only after evaluator adapters are selected.

For each batch, attach a deletion manifest containing:

- Exact file paths and line count.
- Static inbound references.
- Dynamic-string and registry references.
- Owning router and whether it is mounted.
- Tests that import or exercise the module.
- Replacement adapter or explicit removed capability.
- Validation commands and results.

Batch boundaries follow capabilities: tabular fairness, LLM evaluation, multimodal metadata, compliance context, reporting, provenance, and miscellaneous legacy services. A batch that removes a user-visible capability also removes or redirects its navigation, endpoint constants, docs, and claims in the same change.

### Gate 6 — route consolidation and orphan surfaces

After the six-task Evidence Workbench passes browser parity:

- Redirect `/audit-reports` to `/reports?view=builder`.
- Redirect `/compliance` and `/compliance/dashboard` to `/compliance-dashboard`.
- Redirect guided remediation bookmarks to `/remediation?mode=guided` while the flow remains supported.
- Remove orphan page implementations, duplicate hooks, endpoint constants, and report/compliance components only after redirect tests pass.

The redirect period lasts at least one released recovery version. Server logs or product analytics determine whether external bookmarks still require compatibility.

### Gate 7 — dependency-injection scaffolding, thin adapters, settings, and symlinks

Simplify custom interfaces only when one concrete implementation remains and the interface is not the evidence-ingestion or artifact-storage boundary. Remove unused settings only after deployment-manifest and dynamic-access scans. Retire compatibility symlinks last, after:

- `apps/backend/pyproject.toml` declares one supported package layout.
- Local, test, worker, migration, and deployment commands use the same import root.
- Repository-root and package-root compatibility tests have been replaced by one documented supported context plus an explicit transition check.
- No external plugin or integration contract depends on the old namespaces.

## Batch stop conditions

Stop a cleanup batch and retain the candidate when any of these occurs:

- A dynamic loader, migration, CLI, background job, framework importer, or package entrypoint references it.
- Its removal changes an evaluator from `validated` to a weaker capability state without an approved product change.
- An authorization, cross-organization, environmental approval, evidence-hash, mapping-review, report-manifest, build, or browser test fails.
- The deletion requires a speculative replacement abstraction.
- The same batch mixes assurance integration with unrelated cleanup, making regression attribution ambiguous.

## Verification ledger

Each cleanup change records:

| Evidence | Required content |
| --- | --- |
| Scope | Exact deleted and modified paths; pre-existing dirty files excluded |
| Reachability | Static references, dynamic strings, mounted route closure, scripts, tests, migrations, and package entrypoints |
| Product effect | Removed, redirected, or unchanged user-visible capability and its claim wording |
| Validation | Exact commands, exit status, focused test counts, build results, and named baseline failures |
| Reduction | Source lines and direct/transitive dependencies removed from the managed manifests |
| Rollback | The single change or commit that restores the batch without reverting assurance work |

The reduction total is reported only from committed deletion batches that pass their gates. The approximate 25,000-line and 34-dependency opportunity must not be presented as achieved before that evidence exists.
