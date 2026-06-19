# Low-Risk Cleanup Pass 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the smallest confirmed bloat from the audit without touching active dashboard, backend runtime, or user-modified files.

**Architecture:** This is a deletion-first cleanup. It removes unused demo routes, unused dependencies, and seed scripts that the repository already marks deprecated. It avoids risky backend service consolidation, database manager changes, docs deletion, and symlink import cleanup.

**Tech Stack:** Next.js frontend with npm lockfile, FastAPI backend scripts, shell checks with `rg`, `npm`, and Python compile checks.

---

## File Structure

- Delete: `apps/frontend/src/app/ai-demo/page.tsx`
- Delete: `apps/frontend/src/app/api/chat/route.ts`
- Delete: `apps/frontend/src/app/test/page.tsx`
- Modify: `apps/frontend/package.json`
- Modify: `apps/frontend/package-lock.json`
- Delete: `apps/backend/scripts/seed_models.py`
- Delete: `apps/backend/scripts/seed_models_simple.py`
- Delete: `apps/backend/scripts/seed_models_realistic.py`
- Delete: `apps/backend/scripts/seed_models_api.py`
- Modify: `apps/backend/scripts/SEEDING.md`
- Modify: `apps/frontend/scripts/verify-all.sh`
- Modify: `apps/frontend/tests/README.md`

Do not touch existing dirty files: `.gitignore`, `AGENTS.md`, or `research/RESEARCH_SUBMISSION_STRATEGY.md`.

### Task 1: Remove Unlinked Frontend Demo Routes

**Files:**
- Delete: `apps/frontend/src/app/ai-demo/page.tsx`
- Delete: `apps/frontend/src/app/api/chat/route.ts`
- Delete: `apps/frontend/src/app/test/page.tsx`

- [ ] **Step 1: Confirm routes are unlinked**

Run:

```bash
rg -n "ai-demo|/api/chat|src/app/test|href=[{]?['\"]/(ai-demo|test)" apps/frontend/src apps/frontend/tests apps/frontend/scripts -g '*.{ts,tsx}'
```

Expected: matches only inside the files being deleted, or no matches for navigation/tests.

- [ ] **Step 2: Delete the demo route files**

Run:

```bash
rm apps/frontend/src/app/ai-demo/page.tsx apps/frontend/src/app/api/chat/route.ts apps/frontend/src/app/test/page.tsx
```

- [ ] **Step 3: Confirm no imports reference deleted route code**

Run:

```bash
rg -n "@tanstack/ai|@tanstack/ai-openai|@tanstack/ai-react|useChat|fetchServerSentEvents|/api/chat" apps/frontend/src -g '*.{ts,tsx}'
```

Expected: no output.

- [ ] **Step 4: Check route tree**

Run:

```bash
test ! -e apps/frontend/src/app/ai-demo/page.tsx
test ! -e apps/frontend/src/app/api/chat/route.ts
test ! -e apps/frontend/src/app/test/page.tsx
```

Expected: exit 0.

### Task 2: Remove Unused Frontend Dependencies

**Files:**
- Modify: `apps/frontend/package.json`
- Modify: `apps/frontend/package-lock.json`

- [ ] **Step 1: Verify packages are unused outside manifests**

Run:

```bash
rg -n "@tanstack/ai|@tanstack/ai-openai|@tanstack/ai-react|@hugeicons|@alcyone-labs/zod-to-json-schema|zod-to-json-schema|@mantine/hooks|from ['\"]glob|require\\(['\"]glob" apps/frontend/src apps/frontend/scripts apps/frontend/tests -g '*.{ts,tsx,js,jsx}'
```

Expected: no output after Task 1.

- [ ] **Step 2: Remove unused packages with npm**

Run:

```bash
cd apps/frontend && npm uninstall @tanstack/ai @tanstack/ai-openai @tanstack/ai-react @hugeicons/core-free-icons @hugeicons/react @alcyone-labs/zod-to-json-schema zod-to-json-schema @mantine/hooks glob
```

- [ ] **Step 3: Confirm manifests no longer list packages**

Run:

```bash
rg -n "@tanstack/ai|@tanstack/ai-openai|@tanstack/ai-react|@hugeicons|@alcyone-labs/zod-to-json-schema|zod-to-json-schema|@mantine/hooks|\"glob\"" apps/frontend/package.json apps/frontend/package-lock.json
```

Expected: no output.

- [ ] **Step 4: Run frontend build**

Run:

```bash
cd apps/frontend && npm run build
```

Expected: build exits 0.

### Task 3: Remove Deprecated Backend Seed Scripts

**Files:**
- Delete: `apps/backend/scripts/seed_models.py`
- Delete: `apps/backend/scripts/seed_models_simple.py`
- Delete: `apps/backend/scripts/seed_models_realistic.py`
- Delete: `apps/backend/scripts/seed_models_api.py`
- Modify: `apps/backend/scripts/SEEDING.md`
- Modify: `apps/frontend/scripts/verify-all.sh`
- Modify: `apps/frontend/tests/README.md`

- [ ] **Step 1: Confirm only deprecation docs reference removed scripts**

Run:

```bash
rg -n "seed_models\\.py|seed_models_simple\\.py|seed_models_realistic\\.py|seed_models_api\\.py" apps/backend docs tests tooling -g '*'
```

Expected: references are limited to `apps/backend/scripts/SEEDING.md`, `apps/frontend/scripts/verify-all.sh`, `apps/frontend/tests/README.md`, and the scripts themselves.

- [ ] **Step 2: Delete deprecated scripts**

Run:

```bash
rm apps/backend/scripts/seed_models.py apps/backend/scripts/seed_models_simple.py apps/backend/scripts/seed_models_realistic.py apps/backend/scripts/seed_models_api.py
```

- [ ] **Step 3: Update seeding docs**

Edit `apps/backend/scripts/SEEDING.md` so it names `seed_database.py` as the supported path and says the old `seed_models*` scripts were removed. Also update `apps/frontend/scripts/verify-all.sh` and `apps/frontend/tests/README.md` so setup instructions use `seed_database.py`.

Use this replacement for the deprecated section:

```markdown
## Removed Legacy Scripts

The older `seed_models*` scripts were removed. Use `seed_database.py` for full demo data seeding.
```

- [ ] **Step 4: Verify no remaining references to deleted scripts**

Run:

```bash
rg -n "seed_models\\.py|seed_models_simple\\.py|seed_models_realistic\\.py|seed_models_api\\.py" apps/backend docs tests tooling -g '*'
```

Expected: only `apps/backend/scripts/SEEDING.md` mentions removed legacy scripts by pattern, or no output if the doc uses `seed_models*`.

- [ ] **Step 5: Compile remaining backend scripts**

Run:

```bash
cd apps/backend && python3 -m compileall -q scripts
```

Expected: exit 0.

### Task 4: Final Verification

**Files:**
- No file changes.

- [ ] **Step 1: Check worktree changes are scoped**

Run:

```bash
git status --short
```

Expected: only the planned frontend/backend files plus pre-existing `.gitignore`, `AGENTS.md`, and `research/RESEARCH_SUBMISSION_STRATEGY.md`.

- [ ] **Step 2: Check deleted names are gone**

Run:

```bash
test ! -e apps/frontend/src/app/ai-demo/page.tsx
test ! -e apps/frontend/src/app/api/chat/route.ts
test ! -e apps/frontend/src/app/test/page.tsx
test ! -e apps/backend/scripts/seed_models.py
test ! -e apps/backend/scripts/seed_models_simple.py
test ! -e apps/backend/scripts/seed_models_realistic.py
test ! -e apps/backend/scripts/seed_models_api.py
```

Expected: exit 0.

- [ ] **Step 3: Summarize line and dependency reduction**

Run:

```bash
git diff --stat
```

Expected: diff stat shows deletions from the planned files and package manifest updates.

## Self-Review

Spec coverage: Covers the first low-risk Ponytail cleanup pass: unused frontend demo routes, unused frontend dependencies, and explicitly deprecated backend seed scripts.

Placeholder scan: No TBD/TODO placeholders. Each task has exact files and commands.

Type consistency: No new runtime types or APIs are introduced.
