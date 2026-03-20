# Layer Boundaries

## Allowed Dependency Direction
- `api -> application -> domain -> infrastructure`
- `common` may be imported by any layer.

## Disallowed
- `domain` importing `fastapi` or transport types.
- `api` directly executing ad-hoc SQL when repository/adapters exist.
- any imports from `archive/**` into runtime code.
