# Ponytail Cleanup Pass 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the next safest over-engineered and stale repository surfaces after the first Ponytail cleanup pass.

**Architecture:** This is deletion-first cleanup. It removes content and dependencies that active code does not read, updates stale docs/script references, and removes a wrapper entrypoint now superseded by `api.main:app`.

**Tech Stack:** Next.js docs app, Next.js frontend test docs/scripts, FastAPI backend, npm lockfiles, shell reference checks.

---

## File Structure

- Delete: `apps/docs/content/legacy-root-docs/`
- Modify: `apps/docs/package.json`
- Modify: `apps/docs/package-lock.json`
- Modify: `README.md`
- Modify: `apps/frontend/scripts/verify-all.sh`
- Modify: `apps/frontend/tests/README.md`
- Modify: `docs/deployment/DEPLOYMENT_GUIDE_2025.md`
- Modify: `docs/TESTING_GUIDE.md`
- Modify: `apps/backend/SETUP.md`
- Delete: `apps/backend/main.py`

Do not touch existing user files: `.gitignore`, `AGENTS.md`, or `research/RESEARCH_SUBMISSION_STRATEGY.md`.

### Task 1: Delete Unrendered Legacy Docs Content

**Files:**
- Delete: `apps/docs/content/legacy-root-docs/`

- [ ] **Step 1: Confirm docs app reads only active docs**

Run:

```bash
rg -n "legacy-root-docs|content/legacy|DOCS_ROOT|DOC_ITEMS" apps/docs/src apps/docs/content apps/docs/package.json
```

Expected: `src/lib/docs.ts` points `DOCS_ROOT` to `content/docs`; no runtime code imports `legacy-root-docs`.

- [ ] **Step 2: Delete legacy docs content**

Run:

```bash
rm -rf apps/docs/content/legacy-root-docs
```

- [ ] **Step 3: Verify legacy docs content is gone**

Run:

```bash
test ! -e apps/docs/content/legacy-root-docs
```

Expected: exit 0.

### Task 2: Remove Unused Fumadocs Dependencies

**Files:**
- Modify: `apps/docs/package.json`
- Modify: `apps/docs/package-lock.json`

- [ ] **Step 1: Confirm Fumadocs is unused outside manifests**

Run:

```bash
rg -n "fumadocs" apps/docs -g '!node_modules/**' -g '!.next/**' -g '!package-lock.json' -g '!package.json'
```

Expected: no output.

- [ ] **Step 2: Uninstall unused docs dependencies**

Run:

```bash
cd apps/docs && npm uninstall fumadocs-ui fumadocs-mdx
```

- [ ] **Step 3: Verify manifests no longer list Fumadocs**

Run:

```bash
rg -n "fumadocs-ui|fumadocs-mdx" apps/docs/package.json apps/docs/package-lock.json
```

Expected: no output.

- [ ] **Step 4: Build docs app**

Run:

```bash
cd apps/docs && npm run build
```

Expected: exit 0.

### Task 3: Replace Stale Frontend-New References

**Files:**
- Modify: `README.md`
- Modify: `apps/frontend/scripts/verify-all.sh`
- Modify: `apps/frontend/tests/README.md`

- [ ] **Step 1: Confirm `apps/frontend-new` is absent**

Run:

```bash
test ! -d apps/frontend-new
rg -n "frontend-new" README.md apps/frontend/scripts/verify-all.sh apps/frontend/tests/README.md
```

Expected: first command exits 0; references are limited to the three listed files.

- [ ] **Step 2: Replace stale path text**

Edit the three files so `apps/frontend-new` becomes `apps/frontend`, and nearby `cd ../frontend-new` becomes `cd ../frontend`.

- [ ] **Step 3: Verify stale references are gone**

Run:

```bash
rg -n "frontend-new" README.md apps/frontend/scripts/verify-all.sh apps/frontend/tests/README.md
bash -n apps/frontend/scripts/verify-all.sh
```

Expected: first command has no output; shell syntax exits 0.

### Task 4: Remove Backend Main Wrapper

**Files:**
- Delete: `apps/backend/main.py`
- Modify: `docs/deployment/DEPLOYMENT_GUIDE_2025.md`
- Modify: `docs/TESTING_GUIDE.md`
- Modify: `apps/backend/SETUP.md`

- [ ] **Step 1: Confirm active entrypoint is `api.main:app`**

Run:

```bash
rg -n "python main\\.py|apps/backend/main\\.py|main:app|api\\.main:app" README.md docs apps/backend apps/frontend -g '!node_modules/**' -g '!.next/**' -g '!archive/**'
```

Expected: deployment scripts and Docker use `api.main:app`; remaining `python main.py` references are docs only.

- [ ] **Step 2: Delete wrapper and update docs**

Run:

```bash
rm apps/backend/main.py
```

Edit docs so `python main.py` instructions become:

```bash
uv run python -m uvicorn api.main:app --reload --port 8000
```

- [ ] **Step 3: Verify wrapper references are gone**

Run:

```bash
test ! -e apps/backend/main.py
rg -n "python main\\.py|apps/backend/main\\.py|main:app" README.md docs apps/backend apps/frontend -g '!node_modules/**' -g '!.next/**' -g '!archive/**'
```

Expected: no `python main.py` or `apps/backend/main.py`; `api.main:app` references may remain.

### Task 5: Final Verification

**Files:**
- No new file changes.

- [ ] **Step 1: Run build and syntax checks**

Run:

```bash
cd apps/docs && npm run build
cd ../frontend && npm run build
cd ../backend && python3 -m compileall -q api scripts src
```

Expected: all commands exit 0.

- [ ] **Step 2: Check staged cleanup scope**

Run:

```bash
git status --short
git diff --check
git diff --stat
```

Expected: planned files plus pre-existing `.gitignore`, `AGENTS.md`, and `research/RESEARCH_SUBMISSION_STRATEGY.md`.

## Self-Review

Spec coverage: Covers the low-risk follow-up Ponytail cuts from the audit: unrendered docs content, unused docs dependencies, stale frontend path text, and the backend wrapper entrypoint.

Placeholder scan: No TODO/TBD placeholders.

Type consistency: No new runtime APIs or types are introduced.
