# Backend Service Ownership Audit

Generated on 2026-03-05T10:57:15Z

## Duplicate Service Names (application vs domain)

| Service file | Application path | Domain path(s) |
|---|---|---|
| `dataset_service.py` | `apps/backend/src/application/services/dataset_service.py` | `apps/backend/src/domain/dataset/services/dataset_service.py` |

## Recommendation

- Keep API-facing orchestration in `application/services`.
- Keep pure business logic in `domain/*/services`.
- For duplicate names, convert one side to an adapter wrapper or archive after import trace confirms no runtime usage.
