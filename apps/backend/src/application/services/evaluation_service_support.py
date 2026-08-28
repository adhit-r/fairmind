"""Shared non-business mechanics for independent Assurance V2 services."""

from __future__ import annotations

from typing import Mapping

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    MutationCommand,
)
from src.application.evaluation_workbench_contracts import (
    _translate,
    assurance_request_hash,
)
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    validate_idempotency_key,
)


class EvaluationServiceSupport:
    """Own one supplied UoW and preserve command hashing across split services."""

    def __init__(self, unit_of_work: object) -> None:
        self.unit_of_work = unit_of_work
        self.repository = unit_of_work.repository

    def _command(
        self,
        *,
        org_id: str,
        actor_id: str,
        operation: str,
        idempotency_key: str,
        scope: Mapping[str, object],
        body: object,
    ) -> MutationCommand:
        try:
            key = validate_idempotency_key(idempotency_key)
        except AssuranceContractValidationError as error:
            raise _translate(error) from error
        return MutationCommand(
            organization_id=org_id,
            actor_id=actor_id,
            operation=operation,
            idempotency_key=key,
            request_hash=assurance_request_hash(
                method="POST",
                operation=operation,
                scope=scope,
                body=body,
            ),
        )


__all__ = ["EvaluationServiceSupport"]
