# ADR-0001: Split Website and Docs

## Decision
Use separate apps and domains:
- `apps/website` on `fairmind.xyz`
- `apps/docs` with `docs.fairmind.xyz` reserved as the intended target

The domain target is an architectural decision, not deployment evidence. The
P0 alpha links the committed docs source until DNS and hosting are verified.

## Rationale
Improves deploy independence, ownership clarity, and docs pipeline evolution.
