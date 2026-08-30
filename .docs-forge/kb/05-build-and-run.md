# Build, run, and verification notes

## Toolchain

- Backend: Python 3.11 or later with `uv`
  (`apps/backend/pyproject.toml`, `README.md:L67-L85`).
- Dashboard and docs: Node.js 20 or later
  (`apps/frontend/package.json`, `apps/docs/package.json`, `README.md:L69-L74`).
- Public website: Node.js 22.12 or later
  (`apps/website/package.json`, `README.md:L69-L74`).
- Frontend scoped unit tests: Bun (`README.md:L69-L74`).

## Local services

```bash
cd apps/backend
uv run python -m uvicorn api.main:app --reload --port 8000
```

```bash
cd apps/frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

```bash
cd apps/docs
npm run dev
```

The development ports are backend `8000`, dashboard `1111`, and documentation
site `3333` (`README.md:L76-L108`). These commands do not enable the default-off
Assurance V2 gates or prove production readiness.

## Documentation validation

From `apps/docs`:

```bash
npm run validate
npm run typecheck
npm run build
```

The validator checks the nine canonical P0 pages, their frontmatter, internal
links, unsupported API examples, and automatic compliance language
(`apps/docs/scripts/validate-docs.mjs:L1-L52`). The build verifies the custom
Next.js documentation application, not a hosted deployment.

## Backend and frontend release checks

The committed release workflow is the authoritative CI recipe for the alpha.
Representative local checks and the native PostgreSQL boundary are summarized
in `README.md:L113-L140` and `docs/releases/v2.1.0-alpha.1.md`. A focused green
test does not replace review of default-off gates, PostgreSQL integrity,
security checks, or the required pull-request approvals.

## Activation boundary

This documentation pass intentionally provides no public recipe for enabling
Assurance V2. Activation requires an approved environment, migration state,
tenant and trust bootstrap, explicit permission assignment, and a recorded
release decision. The open environment/bootstrap question is retained in
`.docs-forge/kb/99-open-questions.md`.
