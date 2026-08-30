# P0 documentation pass overview

This is a constrained release-documentation pass for FairMind's P0 trustworthy
control plane, not a full repository documentation ingest. The repository is a
multi-app project with a FastAPI backend, a Next.js dashboard, and a separate
Next.js documentation app. The canonical P0 HTTP boundary is mounted from
`apps/backend/api/main.py:L381-L500`; content is written to
`apps/docs/content/docs`.

Relevant local commands:

- Backend: `cd apps/backend && uv run python -m uvicorn api.main:app --reload --port 8000`
- Dashboard: `cd apps/frontend && npm run dev`
- Docs: `cd apps/docs && npm run dev`

Evidence sources: `README.md:L37-L89`, `apps/backend/pyproject.toml`,
`apps/frontend/package.json`, and `apps/docs/package.json`.
