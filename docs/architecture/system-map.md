# System Map

## Apps
- `apps/backend`: API and domain services.
- `apps/frontend`: product dashboard frontend.
- `apps/website`: Astro marketing site (`fairmind.xyz`).
- `apps/docs`: documentation application and canonical P0 source; hosted URL
  remains unverified for the alpha release.

## Backend Layers
- `src/api`: transport layer (routers, schemas, middleware).
- `src/application`: orchestration/use-cases.
- `src/domain`: business domain logic.
- `src/infrastructure`: DB and external adapters.
- `src/common`: shared cross-cutting primitives.

## Archive Policy
- Archived code lives in `apps/backend/archive` or root `archive/repo-legacy`.
- Active runtime modules must not import from archive paths.
