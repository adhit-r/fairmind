# Ponytail Cleanup Pass 3

## Goal

Finish the remaining Ponytail audit cleanup items with deletion-first, evidence-backed changes:

- backend service slab cleanup
- docs/archive removal
- remaining unreferenced backend scripts
- website screenshot bank cleanup
- backend symlink compatibility layer cleanup

## Guardrails

- Do not touch user-owned dirty files: `.gitignore`, `AGENTS.md`, `research/RESEARCH_SUBMISSION_STRATEGY.md`.
- Workers must not commit, stage, or revert unrelated edits.
- Delete only when references are absent or trivially replaced.
- For compatibility-layer and service-slab work, prefer `BLOCKED` over speculative rewrites.
- Main thread owns final integration, validation, staging, and commit.

## Parallel Lanes

1. Docs archive removal
   - Scope: `docs/archive/**`.
   - Verify active references before deletion.
   - Delete `docs/archive` only if references are internal or stale.

2. Backend scripts cleanup
   - Scope: unreferenced `apps/backend/scripts/*` files only.
   - Recheck references per script.
   - Preserve active seed, migration, onboarding, pilot, and readiness scripts.

3. Website screenshot bank cleanup
   - Scope: `apps/website/screenshots/**`, `apps/website/public/screenshots/**`, and only the page references needed to keep the build working.
   - Keep only assets referenced by active website source.
   - Remove generated `dist` screenshots from source cleanup if they are untracked build output.

4. Backend symlink compatibility cleanup
   - Scope: root/backend compatibility shims and symlinks.
   - First map live imports.
   - Delete only inert leftovers such as empty files; report live symlink dependencies as blocked.

5. Backend service slab cleanup
   - Scope: candidate service files under `apps/backend/src/application/services`.
   - First map imports, dynamic strings, tests, and docs.
   - Delete only confirmed zero-reference service modules.

## Validation

- `git diff --check`
- Backend compile check when backend files change: `cd apps/backend && python3 -m compileall -q api scripts src`
- Website build when website assets/source change: `cd apps/website && npm run build`
- Reference scans for every deletion lane.
