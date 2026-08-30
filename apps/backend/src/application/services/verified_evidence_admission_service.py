"""Atomic, evidence-grade admission of one verified Evidence Passport V2."""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    JsonValue,
    MutationCommand,
    MutationOutcome,
    MutationResult,
    SuiteExecutionRecord,
)
from src.application.ports.evidence_admission import (
    ApprovedEvaluatorRegistration,
    EvidenceAdmissionScope,
    EvidenceAdmissionUnitOfWork,
    PersistVerifiedPassportV2SubmissionCommand,
    TrustedEvidenceAdmissionContext,
    UuidFactory,
    VerifiedPassportV2SubmissionRecord,
)
from src.application.evaluation_workbench_contracts import (
    EVIDENCE_RESULTS_BY_TECHNICAL_STATUS,
    assurance_request_hash,
)
from src.application.services.evidence_authenticity_service import (
    AuthenticityCandidate,
    EvidenceAuthenticityError,
    EvidenceAuthenticityService,
)
from src.application.evaluator_catalog_contracts import (
    evaluator_binding_hash,
)
from src.application.evaluator_registration import (
    EvaluatorIdentityBinding,
    EvaluatorRegistrationCeremonyError,
)
from src.application.services.trusted_evidence_admission_resolver import (
    TrustedEvidenceAdmissionResolver,
)
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    canonical_sha256,
    validate_idempotency_key,
    validate_public_safe_string,
)
from src.domain.assurance.evidence_passport_v2 import (
    EvidencePassportV2ValidationError,
    parse_evidence_passport_v2,
)

_SUBMISSION_OPERATION = "evaluation-v2.evidence.verified-submit"
_SUBMISSION_AUDIT_SCHEMA = "evaluation-v2.verified-evidence-submission/v1"
_EVALUATOR_KEYS = (
    "issuerId",
    "evaluatorId",
    "sourceType",
    "adapterName",
    "adapterVersion",
    "resultContractVersion",
)


def _error(
    code: str,
    message: str,
    *,
    status_code: int = 409,
) -> EvaluationWorkbenchError:
    return EvaluationWorkbenchError(code, message, status_code=status_code)


def _utc(value: datetime, *, code: str = "evidence_chronology_invalid") -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise _error(code, "The evidence chronology is invalid.")
    return value.astimezone(timezone.utc)


def _timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        return _utc(value)
    if not isinstance(value, str):
        raise _error("evidence_chronology_invalid", "The evidence chronology is invalid.")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return _utc(datetime.fromisoformat(normalized))
    except ValueError:
        raise _error(
            "evidence_chronology_invalid",
            "The evidence chronology is invalid.",
        ) from None


def _mapping(value: object, *, code: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise _error(code, "The verified evidence projection is invalid.", status_code=422)
    return value


def _frozen_array(value: object, *, code: str) -> tuple[JsonValue, ...]:
    if not isinstance(value, (list, tuple)):
        raise _error(code, "The verified evidence projection is invalid.", status_code=422)
    frozen = FrozenJsonObject.from_mapping({"items": value})["items"]
    if not isinstance(frozen, tuple):
        raise _error(code, "The verified evidence projection is invalid.", status_code=422)
    return frozen


def _safe_uuid(factory: UuidFactory) -> str:
    value = str(factory())
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError) as error:
        raise RuntimeError("The server UUID factory returned an invalid identity.") from error
    if str(parsed) != value:
        raise RuntimeError("The server UUID factory returned a non-canonical identity.")
    return value


def _submission_graph_ids(factory: UuidFactory) -> tuple[str, str, str, str, str]:
    values = tuple(_safe_uuid(factory) for _ in range(5))
    if len(set(values)) != len(values):
        raise RuntimeError("The server UUID factory returned duplicate identities.")
    return values  # type: ignore[return-value]


def _selected_suite(
    context: TrustedEvidenceAdmissionContext,
) -> tuple[SuiteExecutionRecord, object]:
    scope = context.authority.scope
    matches = [
        execution
        for execution in context.authority.run.suite_executions
        if execution.id == scope.suite_execution_id
    ]
    if len(matches) != 1:
        raise _error(
            "evidence_admission_authority_invalid",
            "The locked evidence-admission authority is inconsistent.",
        )
    execution = matches[0]
    selections = [
        selection
        for selection in context.authority.plan_graph.suites
        if selection.ordinal == execution.ordinal
        and selection.suite.id == execution.suite_version_id
    ]
    if len(selections) != 1:
        raise _error(
            "evidence_admission_authority_invalid",
            "The locked evidence-admission authority is inconsistent.",
        )
    return execution, selections[0].suite


def _evaluator_projection(passport: Mapping[str, object]) -> dict[str, object]:
    evaluator = _mapping(
        passport.get("evaluator"),
        code="evidence_evaluator_binding_mismatch",
    )
    if any(not isinstance(evaluator.get(key), str) for key in _EVALUATOR_KEYS):
        raise _error(
            "evidence_evaluator_binding_mismatch",
            "The signed evaluator does not match the locked suite authority.",
        )
    return {key: evaluator[key] for key in _EVALUATOR_KEYS}


def _verify_evaluator_binding(
    context: TrustedEvidenceAdmissionContext,
    evaluator: Mapping[str, object],
) -> None:
    _, suite = _selected_suite(context)
    expected = {
        "issuerId": context.authority.issuer_key,
        "sourceType": context.authority.issuer_type,
        "adapterName": suite.adapter_name,
        "adapterVersion": suite.adapter_version,
        "resultContractVersion": suite.result_contract_version,
    }
    if context.authority.plan_graph.plan.delivery_mode != context.authority.issuer_type or any(
        evaluator.get(key) != value for key, value in expected.items()
    ):
        raise _error(
            "evidence_evaluator_binding_mismatch",
            "The signed evaluator does not match the locked suite authority.",
        )


def _resolve_approved_evaluator_registration(
    *,
    context: TrustedEvidenceAdmissionContext,
    evaluator: Mapping[str, object],
    signer_key_id: str,
    repository: object,
) -> ApprovedEvaluatorRegistration:
    """Lock the durable approval that authorizes this exact receipt binding."""

    values = {
        "evaluator_id": evaluator["evaluatorId"],
        "source_type": evaluator["sourceType"],
        "adapter_name": evaluator["adapterName"],
        "adapter_version": evaluator["adapterVersion"],
        "result_contract_version": evaluator["resultContractVersion"],
        "issuer_id": evaluator["issuerId"],
    }
    if any(not isinstance(value, str) for value in values.values()):
        raise _error(
            "evidence_evaluator_binding_mismatch",
            "The signed evaluator does not match the locked suite authority.",
        )
    try:
        binding = EvaluatorIdentityBinding(
            evaluator_id=values["evaluator_id"],
            source_type=values["source_type"],
            adapter_name=values["adapter_name"],
            adapter_version=values["adapter_version"],
            result_contract_version=values["result_contract_version"],
            issuer_id=values["issuer_id"],
            key_id=signer_key_id,
        )
    except EvaluatorRegistrationCeremonyError:
        raise _error(
            "evidence_evaluator_binding_mismatch",
            "The signed evaluator does not match the locked suite authority.",
        ) from None

    resolver = getattr(repository, "load_approved_evaluator_registration_for_update", None)
    if not callable(resolver):
        raise _error(
            "evidence_evaluator_registration_unavailable",
            "Persistent evaluator registration is unavailable for evidence admission.",
        )
    registration = resolver(
        scope=context.authority.scope,
        authority=context.authority,
        evaluator_id=binding.evaluator_id,
        source_type=binding.source_type,
        adapter_name=binding.adapter_name,
        adapter_version=binding.adapter_version,
        result_contract_version=binding.result_contract_version,
        issuer_id=binding.issuer_id,
        signing_key_id=binding.key_id,
        verified_at=context.database_now,
    )
    if registration is None:
        raise _error(
            "evidence_evaluator_unregistered",
            "The signed evaluator has no approved persistent registration.",
        )
    expected = (
        binding.evaluator_id,
        binding.source_type,
        binding.adapter_name,
        binding.adapter_version,
        binding.result_contract_version,
        binding.issuer_id,
        binding.key_id,
        evaluator_binding_hash(binding),
    )
    observed = (
        registration.evaluator_id,
        registration.source_type,
        registration.adapter_name,
        registration.adapter_version,
        registration.result_contract_version,
        registration.issuer_id,
        registration.signing_key_id,
        registration.binding_hash,
    )
    if (
        not isinstance(registration.registration_id, str)
        or not registration.registration_id
        or observed != expected
    ):
        raise _error(
            "evidence_admission_integrity_conflict",
            "The approved evaluator registration failed integrity checks.",
        )
    return registration


def _verify_stable_authority(
    initial: TrustedEvidenceAdmissionContext,
    verified: TrustedEvidenceAdmissionContext,
) -> None:
    if (
        initial.authority_hash != verified.authority_hash
        or initial.expected_binding != verified.expected_binding
        or initial.trusted_key != verified.trusted_key
    ):
        raise _error(
            "evidence_admission_authority_changed",
            "The evidence-admission authority changed during verification.",
        )
    if _utc(verified.database_now) < _utc(initial.database_now):
        raise _error(
            "evidence_admission_clock_invalid",
            "The trusted database clock moved backwards during verification.",
        )


def _verify_unlinked_suite(execution: SuiteExecutionRecord) -> None:
    if (
        any(
            value is not None
            for value in (
                execution.evidence_run_id,
                execution.passport_revision_id,
                execution.linked_by,
                execution.linked_at,
            )
        )
        or execution.admission_status != "pending"
        or execution.review_status != "pending"
        or execution.freshness_status != "current"
        or execution.result_summary is not None
        or execution.limitations is not None
    ):
        raise _error(
            "evidence_admission_occupied",
            "The suite execution or evidence identity is already occupied.",
        )


def _assert_safe_submission_record(
    record: VerifiedPassportV2SubmissionRecord,
    command: PersistVerifiedPassportV2SubmissionCommand,
) -> None:
    expected = (
        command.scope.organization_id,
        command.authority.run.workspace_id,
        command.scope.system_id,
        command.scope.run_id,
        command.scope.suite_execution_id,
        command.evidence_run_id,
        command.passport_revision_id,
        command.verification_receipt_id,
        command.admission_id,
        command.nonce_claim_id,
        command.authority.run.envelope_hash,
        command.passport_content_hash,
        command.technical_status,
        command.evidence_result_status,
        "verified",
        "current",
        command.effective_expires_at,
        command.verified_at,
    )
    actual = (
        record.organization_id,
        record.workspace_id,
        record.system_id,
        record.run_id,
        record.suite_execution_id,
        record.evidence_run_id,
        record.passport_revision_id,
        record.verification_receipt_id,
        record.admission_id,
        record.nonce_claim_id,
        record.envelope_hash,
        record.passport_content_hash,
        record.technical_status,
        record.evidence_result_status,
        record.admission_status,
        record.freshness_status,
        record.effective_expires_at,
        record.verified_at,
    )
    if actual != expected:
        raise _error(
            "evidence_admission_integrity_conflict",
            "The verified evidence submission failed its relational integrity checks.",
        )


class VerifiedEvidenceAdmissionService:
    """Verify authenticity and persist one exact unlinked evidence submission."""

    def __init__(
        self,
        unit_of_work: EvidenceAdmissionUnitOfWork,
        authenticity_service: EvidenceAuthenticityService,
        *,
        uuid_factory: UuidFactory = uuid.uuid4,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._repository = unit_of_work.repository
        self._authenticity = authenticity_service
        self._resolver = TrustedEvidenceAdmissionResolver(self._repository)
        self._uuid_factory = uuid_factory

    def submit_verified_passport_v2(
        self,
        *,
        scope: EvidenceAdmissionScope,
        actor_id: str,
        idempotency_key: str,
        raw_passport: bytes,
    ) -> MutationResult:
        """Verify and persist a nonce-claimed admission without linking it."""

        return self._mutate_verified_passport_v2(
            scope=scope,
            actor_id=actor_id,
            idempotency_key=idempotency_key,
            raw_passport=raw_passport,
            operation=_SUBMISSION_OPERATION,
        )

    def _mutate_verified_passport_v2(
        self,
        *,
        scope: EvidenceAdmissionScope,
        actor_id: str,
        idempotency_key: str,
        raw_passport: bytes,
        operation: str,
    ) -> MutationResult:
        if not isinstance(scope, EvidenceAdmissionScope):
            raise _error(
                "evidence_admission_scope_invalid",
                "The evidence-admission scope is invalid.",
                status_code=422,
            )
        try:
            for value in (
                scope.organization_id,
                scope.system_id,
                scope.run_id,
                scope.suite_execution_id,
                actor_id,
            ):
                if not isinstance(value, str) or not value:
                    raise AssuranceContractValidationError(
                        "invalid_identifier",
                        "Identifier is invalid.",
                    )
                validate_public_safe_string(value)
            validated_key = validate_idempotency_key(idempotency_key)
        except (AssuranceContractValidationError, TypeError, UnicodeError) as error:
            raise _error(
                "evidence_admission_request_invalid",
                "The evidence-admission request is invalid.",
                status_code=422,
            ) from error
        if not isinstance(raw_passport, (bytes, bytearray, memoryview)):
            raise _error(
                "evidence_passport_invalid",
                "The Evidence Passport is invalid.",
                status_code=422,
            )
        raw = bytes(raw_passport)
        request_scope = {
            "organizationId": scope.organization_id,
            "systemId": scope.system_id,
            "runId": scope.run_id,
            "suiteExecutionId": scope.suite_execution_id,
        }
        request_body = {
            "contractVersion": "2.0.0",
            "rawPassport": {
                "sha256": hashlib.sha256(raw).hexdigest(),
                "byteLength": len(raw),
            },
        }
        command = MutationCommand(
            organization_id=scope.organization_id,
            actor_id=actor_id,
            operation=operation,
            idempotency_key=validated_key,
            request_hash=assurance_request_hash(
                method="POST",
                operation=operation,
                scope=request_scope,
                body=request_body,
            ),
        )

        def admit(_mutation_now: datetime) -> MutationOutcome:
            del _mutation_now
            try:
                passport = parse_evidence_passport_v2(raw)
            except EvidencePassportV2ValidationError:
                raise _error(
                    "evidence_passport_invalid",
                    "The Evidence Passport is invalid.",
                    status_code=422,
                ) from None
            signature = _mapping(
                passport.get("signature"),
                code="evidence_passport_invalid",
            )
            issuer_key = signature.get("issuerId")
            signer_key_id = signature.get("keyId")
            if not isinstance(issuer_key, str) or not isinstance(signer_key_id, str):
                raise _error(
                    "evidence_passport_invalid",
                    "The Evidence Passport is invalid.",
                    status_code=422,
                )

            initial = self._resolver.resolve(
                scope=scope,
                issuer_key=issuer_key,
                signer_key_id=signer_key_id,
            )
            try:
                candidate = self._authenticity.assess(
                    passport,
                    initial.expected_binding,
                    initial.trusted_key,
                    initial.database_now,
                )
            except EvidenceAuthenticityError:
                raise _error(
                    "evidence_authenticity_failed",
                    "The Evidence Passport authenticity checks failed.",
                    status_code=422,
                ) from None
            if candidate.issuer_id != issuer_key or candidate.key_id != signer_key_id:
                raise _error(
                    "evidence_authenticity_failed",
                    "The Evidence Passport authenticity checks failed.",
                    status_code=422,
                )

            evaluator = _evaluator_projection(passport)
            _verify_evaluator_binding(initial, evaluator)
            verified = self._resolver.resolve(
                scope=scope,
                issuer_key=issuer_key,
                signer_key_id=signer_key_id,
            )
            _verify_stable_authority(initial, verified)
            _verify_evaluator_binding(verified, evaluator)
            verified_registration = _resolve_approved_evaluator_registration(
                context=verified,
                evaluator=evaluator,
                signer_key_id=signer_key_id,
                repository=self._repository,
            )
            return self._persist_verified(
                scope=scope,
                actor_id=actor_id,
                passport=passport,
                candidate=candidate,
                evaluator=evaluator,
                initial=initial,
                verified=verified,
                evaluator_registration=verified_registration,
            )

        return self._unit_of_work.mutate(command, admit)

    def _persist_verified(
        self,
        *,
        scope: EvidenceAdmissionScope,
        actor_id: str,
        passport: Mapping[str, object],
        candidate: AuthenticityCandidate,
        evaluator: Mapping[str, object],
        initial: TrustedEvidenceAdmissionContext,
        verified: TrustedEvidenceAdmissionContext,
        evaluator_registration: ApprovedEvaluatorRegistration,
    ) -> MutationOutcome:
        authority = verified.authority
        run = authority.run
        current, _suite = _selected_suite(verified)
        verified_at = _utc(verified.database_now)
        requested_at = _timestamp(run.envelope.to_dict().get("requestedAt"))
        captured_at = _utc(candidate.captured_at)
        signed_at = _utc(candidate.signed_at)
        passport_expires_at = _utc(candidate.expires_at)
        key_valid_until = _utc(authority.key_valid_until)
        effective_expires_at = min(
            passport_expires_at,
            captured_at + timedelta(seconds=authority.maximum_evidence_age_seconds),
            key_valid_until,
        )
        if not requested_at <= captured_at <= signed_at <= verified_at:
            raise _error(
                "evidence_chronology_invalid",
                "The evidence chronology is invalid.",
            )
        if verified_at >= effective_expires_at:
            raise _error(
                "evidence_expired",
                "The Evidence Passport is no longer current.",
            )
        if verified_at <= max(_timestamp(run.updated_at), _timestamp(current.updated_at)):
            raise _error(
                "evidence_admission_clock_invalid",
                "The trusted database clock does not follow the locked run state.",
            )

        result = _mapping(
            candidate.normalized_result,
            code="suite_execution_result_invalid",
        )
        technical_status = result.get("technicalStatus")
        evidence_result_status = result.get("evidenceResultStatus")
        if not isinstance(technical_status, str) or not isinstance(
            evidence_result_status,
            str,
        ):
            raise _error(
                "suite_execution_result_invalid",
                "The evaluator result axes are inconsistent.",
                status_code=422,
            )
        if evidence_result_status not in EVIDENCE_RESULTS_BY_TECHNICAL_STATUS.get(
            technical_status,
            (),
        ):
            raise _error(
                "suite_execution_result_invalid",
                "The evaluator result axes are inconsistent.",
                status_code=422,
            )
        _verify_unlinked_suite(current)

        (
            evidence_run_id,
            passport_revision_id,
            verification_receipt_id,
            admission_id,
            nonce_claim_id,
        ) = _submission_graph_ids(self._uuid_factory)
        summary = _mapping(
            result.get("summary"),
            code="suite_execution_result_invalid",
        )
        limitations = _frozen_array(
            passport.get("limitations"),
            code="evidence_passport_invalid",
        )
        artifact_refs = _frozen_array(
            passport.get("artifacts"),
            code="evidence_passport_invalid",
        )

        execution_binding = _mapping(
            passport.get("executionBinding"),
            code="evidence_passport_invalid",
        )
        if candidate.execution_binding_hash != canonical_sha256(execution_binding):
            raise _error(
                "evidence_authenticity_failed",
                "The Evidence Passport authenticity checks failed.",
                status_code=422,
            )
        if candidate.evaluator_projection_hash != canonical_sha256(evaluator):
            raise _error(
                "evidence_authenticity_failed",
                "The Evidence Passport authenticity checks failed.",
                status_code=422,
            )
        passport_id = passport.get("passportId")
        passport_revision = passport.get("passportRevision")
        if not isinstance(passport_id, str) or passport_revision != 1:
            raise _error(
                "evidence_passport_invalid",
                "The Evidence Passport is invalid.",
                status_code=422,
            )
        submission_command = PersistVerifiedPassportV2SubmissionCommand(
            scope=scope,
            actor_id=actor_id,
            evidence_run_id=evidence_run_id,
            passport_revision_id=passport_revision_id,
            verification_receipt_id=verification_receipt_id,
            admission_id=admission_id,
            nonce_claim_id=nonce_claim_id,
            authority=authority,
            initial_authority_hash=initial.authority_hash,
            verified_authority_hash=verified.authority_hash,
            passport=FrozenJsonObject.from_mapping(passport),
            passport_id=passport_id,
            passport_revision=passport_revision,
            passport_content_hash=candidate.content_hash,
            passport_snapshot_hash=candidate.passport_snapshot_hash,
            signature_input_hash=candidate.signature_input_hash,
            execution_binding=FrozenJsonObject.from_mapping(execution_binding),
            execution_binding_hash=candidate.execution_binding_hash,
            evaluator_projection=FrozenJsonObject.from_mapping(evaluator),
            evaluator_projection_hash=candidate.evaluator_projection_hash,
            evaluator_registration_id=evaluator_registration.registration_id,
            evaluator_registration_binding_hash=evaluator_registration.binding_hash,
            public_key_fingerprint=candidate.public_key_fingerprint,
            verifier_contract=candidate.verifier_contract,
            verifier_version=candidate.verifier_version,
            technical_status=technical_status,
            evidence_result_status=evidence_result_status,
            result_summary=FrozenJsonObject.from_mapping(summary),
            artifact_refs=artifact_refs,
            limitations=limitations,
            captured_at=captured_at,
            signed_at=signed_at,
            effective_expires_at=effective_expires_at,
            verified_at=verified_at,
            evidence_id=None,
            previous_revision_hash=None,
            evidence_created_at=verified_at,
            revision_created_at=verified_at,
        )
        record = self._repository.persist_verified_passport_v2_submission(
            submission_command
        )
        self._repository.force_evidence_admission_constraints()
        _assert_safe_submission_record(record, submission_command)
        body = {
            "admissionId": record.admission_id,
            "evidenceRunId": record.evidence_run_id,
            "passportRevisionId": record.passport_revision_id,
            "verificationReceiptId": record.verification_receipt_id,
            "nonceClaimId": record.nonce_claim_id,
            "runId": record.run_id,
            "suiteExecutionId": record.suite_execution_id,
            "envelopeHash": record.envelope_hash,
            "passportContentHash": record.passport_content_hash,
            "technicalStatus": record.technical_status,
            "evidenceResultStatus": record.evidence_result_status,
            "admissionStatus": record.admission_status,
            "freshnessStatus": record.freshness_status,
            "linkStatus": "pending",
            "effectiveExpiresAt": record.effective_expires_at.isoformat(),
            "verifiedAt": record.verified_at.isoformat(),
        }
        audit_details = {
            "schemaVersion": _SUBMISSION_AUDIT_SCHEMA,
            "runId": record.run_id,
            "suiteExecutionId": record.suite_execution_id,
            "admissionId": record.admission_id,
            "evidenceRunId": record.evidence_run_id,
            "passportRevisionId": record.passport_revision_id,
            "verificationReceiptId": record.verification_receipt_id,
            "nonceClaimId": record.nonce_claim_id,
            "envelopeHash": record.envelope_hash,
            "passportContentHash": record.passport_content_hash,
            "technicalStatus": record.technical_status,
            "evidenceResultStatus": record.evidence_result_status,
            "admissionStatus": record.admission_status,
            "freshnessStatus": record.freshness_status,
            "linkStatus": "pending",
            "evaluatorRegistrationId": evaluator_registration.registration_id,
            "evaluatorRegistrationBindingHash": evaluator_registration.binding_hash,
        }
        return MutationOutcome(
            body=FrozenJsonObject.from_mapping(body),
            status=201,
            resource_type="evidence_admission",
            resource_id=record.admission_id,
            audit_action="evaluation_v2.evidence.verified_submitted",
            audit_details=FrozenJsonObject.from_mapping(audit_details),
        )


__all__ = ["VerifiedEvidenceAdmissionService"]
