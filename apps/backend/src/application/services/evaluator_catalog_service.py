"""Idempotent, auditable evaluator-registration catalog orchestration.

This is a default-off application contract. It is not wired into an HTTP route
or evidence admission composition, so no registration produced by this module
can authorize submitted evidence until the persistent control-plane release is
installed and independently reviewed.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Callable

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationCommand,
    MutationOutcome,
    MutationResult,
)
from src.application.ports.evaluator_catalog import (
    EvaluatorCatalogRecord,
    EvaluatorCatalogUnitOfWork,
)
from src.application.services.evaluator_registration import (
    EvaluatorIdentityBinding,
    EvaluatorRegistrationCeremony,
    EvaluatorRegistrationCeremonyError,
)
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    canonical_sha256,
    validate_idempotency_key,
    validate_public_safe_string,
)


_SUBMIT_OPERATION = "evaluation-v2.evaluator-catalog.submit"
_APPROVE_OPERATION = "evaluation-v2.evaluator-catalog.approve"
_REJECT_OPERATION = "evaluation-v2.evaluator-catalog.reject"
_REVOKE_OPERATION = "evaluation-v2.evaluator-catalog.revoke"
_AUDIT_SCHEMA = "evaluation-v2.evaluator-catalog/v1"
_TRANSITION_AUDIT_ACTIONS = {
    "approve": "evaluation_v2.evaluator_catalog.approved",
    "reject": "evaluation_v2.evaluator_catalog.rejected",
    "revoke": "evaluation_v2.evaluator_catalog.revoked",
}


class EvaluatorCatalogError(EvaluationWorkbenchError):
    """Stable, public error for catalog lifecycle operations."""

    def __init__(self, code: str, message: str, *, status_code: int = 409) -> None:
        super().__init__(code, message, status_code=status_code)


def _error(code: str, message: str, *, status_code: int = 409) -> EvaluatorCatalogError:
    return EvaluatorCatalogError(code, message, status_code=status_code)


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise RuntimeError("The mutation clock is invalid.")
    return value.astimezone(timezone.utc)


def _safe_uuid(factory: Callable[[], object]) -> str:
    value = str(factory())
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError) as error:
        raise RuntimeError("The server UUID factory returned an invalid identity.") from error
    if str(parsed) != value:
        raise RuntimeError("The server UUID factory returned a non-canonical identity.")
    return value


def evaluator_binding_projection(binding: EvaluatorIdentityBinding) -> dict[str, str]:
    """Return the exact immutable tuple that is approved and later admitted."""

    return {
        "evaluatorId": binding.evaluator_id,
        "sourceType": binding.source_type,
        "adapterName": binding.adapter_name,
        "adapterVersion": binding.adapter_version,
        "resultContractVersion": binding.result_contract_version,
        "issuerId": binding.issuer_id,
        "signingKeyId": binding.key_id,
    }


def evaluator_binding_hash(binding: EvaluatorIdentityBinding) -> str:
    return canonical_sha256(evaluator_binding_projection(binding))


def _record_view(record: EvaluatorCatalogRecord) -> dict[str, object]:
    registration = record.registration
    binding = evaluator_binding_projection(registration.binding)
    return {
        "id": registration.registration_id,
        "organizationId": record.organization_id,
        **binding,
        "bindingHash": record.binding_hash,
        "status": registration.status,
        "submittedBy": registration.submitted_by,
        "submittedAt": registration.submitted_at.isoformat(),
        "reviewedBy": registration.reviewed_by,
        "reviewedAt": (
            None if registration.reviewed_at is None else registration.reviewed_at.isoformat()
        ),
        "reviewRationale": registration.review_rationale,
        "revokedBy": registration.revoked_by,
        "revokedAt": (
            None if registration.revoked_at is None else registration.revoked_at.isoformat()
        ),
        "revocationRationale": registration.revocation_rationale,
    }


def _audit_details(record: EvaluatorCatalogRecord, *, prior_status: str | None) -> FrozenJsonObject:
    details: dict[str, object] = {
        "schemaVersion": _AUDIT_SCHEMA,
        "registrationId": record.registration_id,
        "bindingHash": record.binding_hash,
        "status": record.status,
    }
    if prior_status is not None:
        details["priorStatus"] = prior_status
    return FrozenJsonObject.from_mapping(details)


class EvaluatorCatalogService:
    """Apply the ceremony only through idempotent, tenant-bound mutations."""

    def __init__(
        self,
        unit_of_work: EvaluatorCatalogUnitOfWork,
        *,
        uuid_factory: Callable[[], object] = uuid.uuid4,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._repository = unit_of_work.repository
        self._uuid_factory = uuid_factory

    @staticmethod
    def _validate_identifiers(*values: str) -> None:
        try:
            for value in values:
                if not isinstance(value, str) or not value:
                    raise AssuranceContractValidationError(
                        "invalid_identifier", "Identifier is invalid."
                    )
                validate_public_safe_string(value)
        except (AssuranceContractValidationError, TypeError, UnicodeError) as error:
            raise _error(
                "evaluator_registration_request_invalid",
                "The evaluator registration request is invalid.",
                status_code=422,
            ) from error

    @staticmethod
    def _validated_key(value: str) -> str:
        try:
            return validate_idempotency_key(value)
        except (AssuranceContractValidationError, TypeError, UnicodeError) as error:
            raise _error(
                "evaluator_registration_request_invalid",
                "The evaluator registration request is invalid.",
                status_code=422,
            ) from error

    @staticmethod
    def _request_hash(
        *,
        operation: str,
        organization_id: str,
        body: dict[str, object],
    ) -> str:
        return canonical_sha256(
            {
                "method": "POST",
                "operation": operation,
                "scope": {"organizationId": organization_id},
                "body": body,
            }
        )

    @staticmethod
    def _translate_ceremony(error: EvaluatorRegistrationCeremonyError) -> EvaluatorCatalogError:
        return _error(error.code, error.message, status_code=409)

    def submit(
        self,
        *,
        organization_id: str,
        actor_id: str,
        idempotency_key: str,
        binding: EvaluatorIdentityBinding,
    ) -> MutationResult:
        self._validate_identifiers(organization_id, actor_id)
        if not isinstance(binding, EvaluatorIdentityBinding):
            raise _error(
                "evaluator_registration_request_invalid",
                "The evaluator registration request is invalid.",
                status_code=422,
            )
        validated_key = self._validated_key(idempotency_key)
        binding_projection = evaluator_binding_projection(binding)
        command = MutationCommand(
            organization_id=organization_id,
            actor_id=actor_id,
            operation=_SUBMIT_OPERATION,
            idempotency_key=validated_key,
            request_hash=self._request_hash(
                operation=_SUBMIT_OPERATION,
                organization_id=organization_id,
                body={"binding": binding_projection},
            ),
        )

        def persist(now: datetime) -> MutationOutcome:
            now = _utc(now)
            if self._repository.find_by_binding(
                organization_id=organization_id,
                binding=binding,
            ) is not None:
                raise _error(
                    "evaluator_registration_exists",
                    "An evaluator registration already exists for this exact binding.",
                )
            if not self._repository.signing_authority_is_live(
                organization_id=organization_id,
                issuer_id=binding.issuer_id,
                key_id=binding.key_id,
                at=now,
                lock=True,
            ):
                raise _error(
                    "evaluator_registration_signing_authority_untrusted",
                    "The evaluator issuer and signing key are not live in this organization.",
                )
            try:
                ceremony_record = EvaluatorRegistrationCeremony.submit(
                    registration_id=_safe_uuid(self._uuid_factory),
                    binding=binding,
                    submitted_by=actor_id,
                    submitted_at=now,
                )
            except EvaluatorRegistrationCeremonyError as error:
                raise self._translate_ceremony(error) from None
            record = EvaluatorCatalogRecord(
                organization_id=organization_id,
                registration=ceremony_record,
                binding_hash=evaluator_binding_hash(binding),
            )
            persisted = self._repository.insert_registration(record)
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_record_view(persisted)),
                status=201,
                resource_type="evaluator_registration",
                resource_id=persisted.registration_id,
                audit_action="evaluation_v2.evaluator_catalog.submitted",
                audit_details=_audit_details(persisted, prior_status=None),
            )

        return self._unit_of_work.mutate(command, persist)

    def _transition(
        self,
        *,
        operation: str,
        action: str,
        organization_id: str,
        registration_id: str,
        actor_id: str,
        idempotency_key: str,
        rationale: str,
    ) -> MutationResult:
        self._validate_identifiers(organization_id, registration_id, actor_id)
        validated_key = self._validated_key(idempotency_key)
        if not isinstance(rationale, str):
            raise _error(
                "evaluator_registration_request_invalid",
                "The evaluator registration request is invalid.",
                status_code=422,
            )
        command = MutationCommand(
            organization_id=organization_id,
            actor_id=actor_id,
            operation=operation,
            idempotency_key=validated_key,
            request_hash=self._request_hash(
                operation=operation,
                organization_id=organization_id,
                body={"registrationId": registration_id, "rationale": rationale.strip()},
            ),
        )

        def persist(now: datetime) -> MutationOutcome:
            now = _utc(now)
            current = self._repository.get_registration(
                organization_id=organization_id,
                registration_id=registration_id,
                lock=True,
            )
            if current is None:
                raise _error(
                    "evaluator_registration_not_found",
                    "The evaluator registration was not found in this organization.",
                    status_code=404,
                )
            prior_status = current.status
            try:
                if action == "approve":
                    if not self._repository.signing_authority_is_live(
                        organization_id=organization_id,
                        issuer_id=current.binding.issuer_id,
                        key_id=current.binding.key_id,
                        at=now,
                        lock=True,
                    ):
                        raise _error(
                            "evaluator_registration_signing_authority_untrusted",
                            "The evaluator issuer and signing key are not live in this organization.",
                        )
                    transitioned = EvaluatorRegistrationCeremony.approve(
                        current.registration,
                        approved_by=actor_id,
                        approved_at=now,
                        rationale=rationale,
                    )
                    expected_status = "pending"
                elif action == "reject":
                    transitioned = EvaluatorRegistrationCeremony.reject(
                        current.registration,
                        rejected_by=actor_id,
                        rejected_at=now,
                        rationale=rationale,
                    )
                    expected_status = "pending"
                elif action == "revoke":
                    transitioned = EvaluatorRegistrationCeremony.revoke(
                        current.registration,
                        revoked_by=actor_id,
                        revoked_at=now,
                        rationale=rationale,
                    )
                    expected_status = "approved"
                else:
                    raise RuntimeError("Unknown evaluator catalog transition.")
            except EvaluatorRegistrationCeremonyError as error:
                raise self._translate_ceremony(error) from None
            replacement = EvaluatorCatalogRecord(
                organization_id=current.organization_id,
                registration=transitioned,
                binding_hash=current.binding_hash,
            )
            persisted = self._repository.replace_registration(
                replacement,
                expected_status=expected_status,
            )
            if persisted is None:
                raise _error(
                    "evaluator_registration_transition_conflict",
                    "The evaluator registration changed before it could be decided.",
                )
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_record_view(persisted)),
                status=200,
                resource_type="evaluator_registration",
                resource_id=persisted.registration_id,
                audit_action=_TRANSITION_AUDIT_ACTIONS[action],
                audit_details=_audit_details(persisted, prior_status=prior_status),
            )

        return self._unit_of_work.mutate(command, persist)

    def approve(
        self,
        *,
        organization_id: str,
        registration_id: str,
        actor_id: str,
        idempotency_key: str,
        rationale: str,
    ) -> MutationResult:
        return self._transition(
            operation=_APPROVE_OPERATION,
            action="approve",
            organization_id=organization_id,
            registration_id=registration_id,
            actor_id=actor_id,
            idempotency_key=idempotency_key,
            rationale=rationale,
        )

    def reject(
        self,
        *,
        organization_id: str,
        registration_id: str,
        actor_id: str,
        idempotency_key: str,
        rationale: str,
    ) -> MutationResult:
        return self._transition(
            operation=_REJECT_OPERATION,
            action="reject",
            organization_id=organization_id,
            registration_id=registration_id,
            actor_id=actor_id,
            idempotency_key=idempotency_key,
            rationale=rationale,
        )

    def revoke(
        self,
        *,
        organization_id: str,
        registration_id: str,
        actor_id: str,
        idempotency_key: str,
        rationale: str,
    ) -> MutationResult:
        return self._transition(
            operation=_REVOKE_OPERATION,
            action="revoke",
            organization_id=organization_id,
            registration_id=registration_id,
            actor_id=actor_id,
            idempotency_key=idempotency_key,
            rationale=rationale,
        )

    def get(self, *, organization_id: str, registration_id: str) -> dict[str, object] | None:
        self._validate_identifiers(organization_id, registration_id)
        record = self._repository.get_registration(
            organization_id=organization_id,
            registration_id=registration_id,
            lock=False,
        )
        return None if record is None else _record_view(record)

    def list(self, *, organization_id: str) -> list[dict[str, object]]:
        self._validate_identifiers(organization_id)
        return [
            _record_view(record)
            for record in self._repository.list_registrations(organization_id=organization_id)
        ]


__all__ = [
    "EvaluatorCatalogError",
    "EvaluatorCatalogService",
    "evaluator_binding_hash",
    "evaluator_binding_projection",
]
