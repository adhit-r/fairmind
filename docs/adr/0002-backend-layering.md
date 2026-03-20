# ADR-0002: Backend Layering

## Decision
Adopt explicit backend layers under `apps/backend/src`:
- api, application, domain, infrastructure, common.

## Rationale
Reduces coupling and duplicate service ownership.
