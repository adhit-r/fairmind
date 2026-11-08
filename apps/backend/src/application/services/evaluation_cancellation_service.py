"""Authorized, idempotent cancellation of an evaluation run or one suite job."""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime

from src.application.evaluation_workbench_contracts import assurance_request_hash
from src.application.ports.evaluation_cancellation import (
    CancellationScope,
    EvaluationCancellationRepository,
    PersistCancellationCommand,
)
from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    EvaluationWorkbenchUnitOfWork,
    FrozenJsonObject,
    MutationCommand,
    MutationOutcome,
    MutationResult,
)
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    validate_idempotency_key,
    validate_public_safe_string,
)

_OPERATION = "evaluation-v2.run.cancel"
_AUDIT_ACTION = "evaluation_v2.worker.cancellation_requested"
_FINALIZED_AUDIT_ACTION = "evaluation_v2.worker.cancellation_finalized"
_AUDIT_SCHEMA = "evaluation-v2.cancellation-request/v1"


def _invalid() -> EvaluationWorkbenchError:
    return EvaluationWorkbenchError(
        "evaluation_cancellation_request_invalid",
        "The cancellation request is invalid.",
        status_code=422,
    )


def _validated_body(payload: Mapping[str, object]) -> tuple[str, str | None, str]:
    if not isinstance(payload, Mapping) or not set(payload) <= {
        "scopeKind",
        "suiteExecutionId",
        "reason",
    }:
        raise _invalid()
    scope_kind = payload.get("scopeKind")
    suite_execution_id = payload.get("suiteExecutionId")
    reason = payload.get("reason")
    if (
        scope_kind not in {"run", "suite"}
        or (scope_kind == "run") != (suite_execution_id is None)
        or (suite_execution_id is not None and not isinstance(suite_execution_id, str))
        or not isinstance(reason, str)
        or reason != reason.strip()
        or not 1 <= len(reason) <= 2000
        or len(reason.encode("utf-8")) > 2000
    ):
        raise _invalid()
    return scope_kind, suite_execution_id, reason


class EvaluationRunCancellationService:
    """Append one cancellation request and terminalize every affected active job."""

    def __init__(
        self,
        unit_of_work: EvaluationWorkbenchUnitOfWork,
        repository: EvaluationCancellationRepository,
        *,
        uuid_factory: Callable[[], object] = uuid.uuid4,
    ) -> None:
        self.unit_of_work = unit_of_work
        self._repository = repository
        self._uuid_factory = uuid_factory

    def request_cancellation(
        self,
        *,
        scope: CancellationScope,
        actor_id: str,
        idempotency_key: str,
        payload: Mapping[str, object],
    ) -> MutationResult:
        try:
            for value in (
                scope.organization_id,
                scope.workspace_id,
                scope.system_id,
                scope.run_id,
                actor_id,
            ):
                if not isinstance(value, str) or not value:
                    raise _invalid()
                validate_public_safe_string(value)
            validated_key = validate_idempotency_key(idempotency_key)
            scope_kind, suite_execution_id, reason = _validated_body(payload)
            if suite_execution_id is not None:
                validate_public_safe_string(suite_execution_id)
        except (AssuranceContractValidationError, TypeError, UnicodeError) as error:
            raise _invalid() from error
        command = MutationCommand(
            organization_id=scope.organization_id,
            actor_id=actor_id,
            operation=_OPERATION,
            idempotency_key=validated_key,
            request_hash=assurance_request_hash(
                method="POST",
                operation=_OPERATION,
                scope={
                    "organizationId": scope.organization_id,
                    "workspaceId": scope.workspace_id,
                    "systemId": scope.system_id,
                    "runId": scope.run_id,
                },
                body={
                    "scopeKind": scope_kind,
                    "suiteExecutionId": suite_execution_id,
                    "reason": reason,
                },
            ),
        )

        def cancel(_mutation_now: datetime) -> MutationOutcome:
            del _mutation_now
            record = self._repository.request_cancellation(
                PersistCancellationCommand(
                    scope=scope,
                    scope_kind=scope_kind,
                    suite_execution_id=suite_execution_id,
                    actor_id=actor_id,
                    cancellation_id=str(uuid.UUID(str(self._uuid_factory()))),
                    reason=reason,
                )
            )
            body = {
                "cancellationId": record.cancellation_id,
                "runId": scope.run_id,
                "scopeKind": record.scope_kind,
                "suiteExecutionId": record.suite_execution_id,
                "requestedBy": record.requested_by,
                "requestedAt": record.requested_at.isoformat(),
                "runTechnicalStatus": record.run_technical_status,
                "suiteExecutions": [
                    {"id": suite_id, "technicalStatus": status}
                    for suite_id, status in record.suite_statuses
                ],
            }
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(body),
                status=201,
                resource_type="evaluation_cancellation",
                resource_id=record.cancellation_id,
                audit_action=(
                    _FINALIZED_AUDIT_ACTION if record.finalized_existing else _AUDIT_ACTION
                ),
                audit_details=FrozenJsonObject.from_mapping(
                    {
                        "schemaVersion": _AUDIT_SCHEMA,
                        "runId": scope.run_id,
                        "cancellationId": record.cancellation_id,
                        "scopeKind": record.scope_kind,
                        "suiteExecutionId": record.suite_execution_id,
                        "reasonHash": hashlib.sha256(reason.encode("utf-8")).hexdigest(),
                        "cancelledAttemptIds": list(record.cancelled_attempt_ids),
                        "runTechnicalStatus": record.run_technical_status,
                    }
                ),
            )

        return self.unit_of_work.mutate(command, cancel)


__all__ = ["EvaluationRunCancellationService"]
