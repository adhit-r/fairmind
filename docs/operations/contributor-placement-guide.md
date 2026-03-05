# Contributor Placement Guide

## Where new code goes
- New endpoints: `apps/backend/src/api/routers`
- Request/response schemas: `apps/backend/src/api/schemas`
- Orchestration logic: `apps/backend/src/application/services`
- Business logic: `apps/backend/src/domain/*`
- DB/external connectors: `apps/backend/src/infrastructure/*`
- Docs content: `apps/docs/content`
- Marketing pages: `apps/website/src/pages`

## Anti-patterns
- Adding new runtime code under any `archive/` path.
- Duplicating service implementations across layers.
