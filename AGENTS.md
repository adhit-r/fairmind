# Codex Onboarding

## Repository Shape

FairMind is a multi-app AI governance and bias detection platform.

- `apps/backend`: FastAPI backend. Active layered code lives mainly under `apps/backend/src`; older compatibility modules also exist at `apps/backend/api`, `apps/backend/config`, `apps/backend/services`, and `apps/backend/fairness_library`.
- `apps/frontend`: Next.js product dashboard on port `1111`.
- `apps/website`: Astro marketing site.
- `apps/docs`: Next/Fumadocs documentation site on port `3333`.
- `apps/ml`: Python ML pipelines and visualizations.
- `docs`: Architecture, operations, deployment, API, RBAC, and regulatory docs.
- `tooling`: Repository guard scripts for architecture boundaries and archive imports.
- `archive`, `apps/backend/archive`, and `_external`: Do not treat these as active runtime code unless the task explicitly asks for legacy or vendored files.

## Non-Negotiable UI Rules

- Do not use emoji.
- Do not use purple gradients.
- Do not produce generic AI-looking UI. Preserve the existing direct, professional neobrutalist direction.
- Frontend UI should use strong borders, hard shadows, high contrast, and the established teal/orange/black/white language already documented in `CLAUDE.md`.
- Keep product screens task-focused. Avoid marketing hero treatment inside dashboard workflows.

## Backend Conventions

- Preferred backend entrypoint: `apps/backend/api/main.py`.
- Local backend command from `apps/backend`:
  ```bash
  uv run python -m uvicorn api.main:app --reload --port 8000
  ```
- Backend package metadata and pytest config are in `apps/backend/pyproject.toml`.
- Respect the intended dependency direction:
  `api -> application -> domain -> infrastructure`; `common` may be shared.
- Domain services must not import FastAPI or API-layer modules.
- Runtime code must not import from archive directories.
- Use env-based configuration. Do not commit secrets from `.env`, `.env.production`, local databases, logs, coverage, or generated artifacts.

## Frontend Conventions

- Product dashboard: work in `apps/frontend/src`.
- Dashboard scripts from `apps/frontend`:
  ```bash
  npm run dev
  npm run build
  npm run test
  ```
- `npm run dev` serves the dashboard on `http://localhost:1111`.
- Playwright config currently starts the dev server with `bun run dev`; if using `npm run test`, make sure Bun is available or adjust the command deliberately as part of the task.
- API URL is typically configured with `NEXT_PUBLIC_API_URL=http://localhost:8000`.
- Reuse existing components under `apps/frontend/src/components` and existing route patterns under `apps/frontend/src/app/(dashboard)`.

## Website And Docs

- Marketing site commands from `apps/website`:
  ```bash
  npm run dev
  npm run build
  npm run preview
  ```
- Docs site commands from `apps/docs`:
  ```bash
  npm run dev
  npm run build
  npm run start
  ```
- Keep website, docs, and product-dashboard styling decisions scoped to the app being changed.

## Validation

Use the narrowest useful checks for the files touched.

- Backend unit tests from `apps/backend`:
  ```bash
  uv run pytest
  ```
- Root Python tests:
  ```bash
  python3 -m pytest tests
  ```
- Frontend E2E tests from `apps/frontend`:
  ```bash
  npm run test
  ```
- Boundary checks from repo root:
  ```bash
  tooling/check_backend_layer_boundaries.sh
  tooling/check_no_archive_imports.sh
  ```
- For frontend changes, run a local browser check at desktop and mobile widths when practical.

## Working Notes

- Prefer `rg` for search.
- Read the nearby README/docs, but verify commands against package metadata because some docs are older than the current app state.
- Keep edits scoped. This repository contains generated output, coverage, local virtualenvs, and old build artifacts; do not churn them.
- Before git operations, check status and preserve user changes.

<!-- graft:start -->
## Graft — repo context graph

This repo is indexed in `graft/`: small linked markdown nodes that explain each
system and carry exact file:line spans, kept in sync with the code through git.

For ANY task here — understanding how something works, finding where code lives,
or scoping a change — get context from the graph before grepping or opening
source files. Re-ask freely (it's cheap) and reuse literal identifiers you
already have (symbol, error string, file name) as the query. New to this repo?
Run `graft map` first — a token-budgeted orientation (dir clusters, hubs,
hotspots), no LLM, no key.

- Run `graft ask "<your question>" --source` → ranked nodes with the relevant
  code spans inlined (each hit's ≤8-line crux by default; `--full` for whole
  definitions when the crux isn't enough). Match the tool to the task shape:
  for understanding or editing, the top node IS the answer — cite its
  `covers:` file:line spans and edit straight from `--source`. For
  exhaustive tasks ("every occurrence / every caller of this pattern"), ranked
  results are top-N, not complete — run `graft grep "<literal>"` instead
  (exhaustive over indexed files, grouped by enclosing symbol), falling back
  to raw `grep -rn` only for unindexed files.
- `graft skeleton <file>` → every definition's signature + span, ~10× cheaper
  than reading the file; use it to skim an API surface.
- `graft callers <symbol>` gives precomputed, exact edges — who calls this.
  Add `--direction out` for what it calls, or `--depth N` to walk
  transitively for the full blast radius. For structural questions, skip
  ranking and use this directly.
- Or browse: `graft/INDEX.md` lists every node; follow the links.
- Monorepos and folders of multiple repos rank fairly across sub-projects —
  hits carry `[scope/]` labels naming which one they're from. Narrow with
  `graft ask "<task>" --in <scope>/` once you know where you're working.

If a returned span is truncated ("+N more lines"), open the file at that exact
range before finalizing. Only open source files when a node genuinely lacks a
needed detail, and then at the exact file:line the node points to — never
re-read whole files.

After big code changes, refresh the graph with `graft build` (deterministic,
no API key, $0).
<!-- graft:end -->
