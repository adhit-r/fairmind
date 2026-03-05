# Backend Service Ownership Map

## Purpose
Define one canonical owner per capability to prevent duplicate implementations across layers.

## Canonical Ownership (Current)

| Capability | Canonical runtime owner | Notes |
|---|---|---|
| Dataset lifecycle | `apps/backend/src/domain/dataset/services/dataset_service.py` | `application/services/dataset_service.py` is a thin adapter for API contract compatibility. |
| Monitoring metrics/config | `apps/backend/src/domain/monitoring/services/monitoring_service.py` | API router imports domain service directly. |
| Alerts/rules | `apps/backend/src/domain/monitoring/services/alert_service.py` | API router imports domain service directly. |
| India compliance workflows | `apps/backend/src/application/services/india_compliance_service.py` | Domain duplicate archived; app service remains canonical pending deeper redesign. |
| India bias detection | `apps/backend/src/application/services/india_bias_detection_service.py` | Used directly by India compliance API router. |
| LLM bias detection | `apps/backend/src/application/services/llm_bias_detection_service.py` | Canonical runtime implementation. |
| Multimodal bias detection | `apps/backend/src/application/services/multimodal_bias_detection_service.py` | Domain variant exists for legacy/internal patterns; not API canonical. |

## Archived Duplicates

- `apps/backend/archive/duplicate-services/application-bias_detection/bias_detection_service.py`
- `apps/backend/archive/duplicate-services/domain-bias_detection/bias_detection_service.py`
- `apps/backend/archive/duplicate-services/domain-compliance/india_compliance_service.py`

## Rules Going Forward

1. API routers import from `application/services` only.
2. `application/services` may orchestrate and adapt contracts.
3. `domain/*/services` contains reusable business logic and no web framework dependencies.
4. New overlapping service names require explicit owner decision and ledger entry.
