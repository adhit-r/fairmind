"""Atomic, evidence-grade admission of one verified Evidence Passport V2."""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Mapping
from dataclasses import replace
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
    EvidenceAdmissionScope,
    EvidenceAdmissionUnitOfWork,
    PersistVerifiedPassportV2Command,
    TrustedEvidenceAdmissionContext,
    UuidFactory,
    VerifiedPassportV2Record,
)
from src.application.services.evaluation_workbench_service import (
    EVIDENCE_RESULTS_BY_TECHNICAL_STATUS,
    TERMINAL_TECHNICAL_STATUSES,
    aggregate_run_result_axes,
    assurance_request_hash,
)
from src.application.services.evidence_authenticity_service import (
    AuthenticityCandidate,
    EvidenceAuthenticityError,
    EvidenceAuthenticityService,
)
from src.application.services.evaluator_registry import (
    EvaluatorRegistration,
    EvaluatorRegistry,
    EvaluatorRegistryError,
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

_OPERATION = "evaluation-v2.evidence.verified-admit"
_AUDIT_SCHEMA = "evaluation-v2.verified-evidence-admission/v1"
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


def _optional_timestamp(value: object) -> datetime | None:
    return None if value is None else _timestamp(value)


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


def _graph_ids(factory: UuidFactory) -> tuple[str, str, str, str, str, str]:
    values = tuple(_safe_uuid(factory) for _ in range(6))
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
    evaluator_registry: EvaluatorRegistry,
) -> EvaluatorRegistration:
    try:
        registration = evaluator_registry.validate_binding(
            evaluator_id=evaluator["evaluatorId"],
            source_type=evaluator["sourceType"],
            adapter_name=evaluator["adapterName"],
            adapter_version=evaluator["adapterVersion"],
            result_contract_version=evaluator["resultContractVersion"],
        )
    except EvaluatorRegistryError as error:
        mapped_code = {
            "evaluator_unregistered": "evidence_evaluator_unregistered",
            "evaluator_inactive": "evidence_evaluator_inactive",
            "evaluator_source_not_allowed": "evidence_evaluator_source_untrusted",
        }.get(error.code, "evidence_evaluator_binding_mismatch")
        raise _error(
            mapped_code,
            "The signed evaluator is not authorized by the server catalog.",
            status_code=409,
        ) from None
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


def _verify_current_suite(
    execution: SuiteExecutionRecord,
    *,
    technical_status: str,
    evidence_result_status: str,
) -> tuple[datetime | None, datetime | None]:
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
    if evidence_result_status not in EVIDENCE_RESULTS_BY_TECHNICAL_STATUS.get(
        technical_status,
        (),
    ):
        raise _error(
            "suite_execution_result_invalid",
            "The evaluator result axes are inconsistent.",
            status_code=422,
        )
    started_at = _optional_timestamp(execution.started_at)
    completed_at = _optional_timestamp(execution.completed_at)
    if execution.technical_status in TERMINAL_TECHNICAL_STATUSES:
        if (
            execution.technical_status != technical_status
            or execution.evidence_result_status != evidence_result_status
            or completed_at is None
        ):
            raise _error(
                "suite_execution_result_conflict",
                "The signed result does not match the terminal suite execution.",
            )
        return started_at, completed_at
    if execution.technical_status not in {
        "awaiting_evidence",
        "queued",
        "leased",
        "running",
    } or (execution.technical_status in {"queued", "leased"} and technical_status == "succeeded"):
        raise _error(
            "suite_execution_transition_invalid",
            "The suite execution cannot transition to the signed result.",
        )
    return started_at, completed_at


def _assert_safe_record(
    record: VerifiedPassportV2Record,
    command: PersistVerifiedPassportV2Command,
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
        command.suite_evidence_link_id,
        command.authority.run.envelope_hash,
        command.passport_content_hash,
        command.technical_status,
        command.evidence_result_status,
        "verified",
        "pending",
        "current",
        command.run_technical_status,
        command.run_evidence_outcome,
        command.authority.run.overall_verdict,
        command.authority.run.verdict_version,
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
        record.suite_evidence_link_id,
        record.envelope_hash,
        record.passport_content_hash,
        record.technical_status,
        record.evidence_result_status,
        record.admission_status,
        record.review_status,
        record.freshness_status,
        record.run_technical_status,
        record.run_evidence_outcome,
        record.overall_verdict,
        record.verdict_version,
        record.effective_expires_at,
        record.verified_at,
    )
    if actual != expected:
        raise _error(
            "evidence_admission_integrity_conflict",
            "The verified evidence graph failed its relational integrity checks.",
        )


class VerifiedEvidenceAdmissionService:
    """Verify authenticity, re-resolve authority, then admit one exact graph."""

    def __init__(
        self,
        unit_of_work: EvidenceAdmissionUnitOfWork,
        authenticity_service: EvidenceAuthenticityService,
        evaluator_registry: EvaluatorRegistry,
        *,
        uuid_factory: UuidFactory = uuid.uuid4,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._repository = unit_of_work.repository
        self._authenticity = authenticity_service
        self._evaluator_registry = evaluator_registry
        self._resolver = TrustedEvidenceAdmissionResolver(self._repository)
        self._uuid_factory = uuid_factory

    def admit_verified_passport_v2(
        self,
        *,
        scope: EvidenceAdmissionScope,
        actor_id: str,
        idempotency_key: str,
        raw_passport: bytes,
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
            operation=_OPERATION,
            idempotency_key=validated_key,
            request_hash=assurance_request_hash(
                method="POST",
                operation=_OPERATION,
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
            initial_registration = _verify_evaluator_binding(
                initial,
                evaluator,
                self._evaluator_registry,
            )
            verified = self._resolver.resolve(
                scope=scope,
                issuer_key=issuer_key,
                signer_key_id=signer_key_id,
            )
            _verify_stable_authority(initial, verified)
            verified_registration = _verify_evaluator_binding(
                verified,
                evaluator,
                self._evaluator_registry,
            )
            if initial_registration != verified_registration:
                raise _error(
                    "evidence_evaluator_registry_changed",
                    "The server evaluator catalog changed during verification.",
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
        evaluator_registration: EvaluatorRegistration,
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
        existing_started_at, existing_completed_at = _verify_current_suite(
            current,
            technical_status=technical_status,
            evidence_result_status=evidence_result_status,
        )
        was_terminal = current.technical_status in TERMINAL_TECHNICAL_STATUSES
        suite_started_at = existing_started_at if existing_started_at is not None else verified_at
        suite_completed_at = existing_completed_at if was_terminal else verified_at

        raw_current_axes = aggregate_run_result_axes(run.suite_executions)
        linked_current_axes = aggregate_run_result_axes(
            run.suite_executions,
            require_linked_evidence=True,
        )
        current_parent_axes = (run.technical_status, run.evidence_outcome)
        if current_parent_axes not in {raw_current_axes, linked_current_axes}:
            raise _error(
                "run_projection_conflict",
                "The evaluation run changed before evidence could be linked.",
            )

        (
            evidence_run_id,
            passport_revision_id,
            verification_receipt_id,
            admission_id,
            nonce_claim_id,
            suite_evidence_link_id,
        ) = _graph_ids(self._uuid_factory)
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
        projected = replace(
            current,
            technical_status=technical_status,
            evidence_result_status=evidence_result_status,
            admission_status="verified",
            review_status="pending",
            freshness_status="current",
            evidence_run_id=evidence_run_id,
            passport_revision_id=passport_revision_id,
            linked_by=actor_id,
            linked_at=verified_at.isoformat(),
            result_summary=FrozenJsonObject.from_mapping(summary),
            limitations=limitations,
            started_at=suite_started_at.isoformat(),
            completed_at=suite_completed_at.isoformat(),
            updated_at=verified_at.isoformat(),
        )
        projected_siblings = tuple(
            projected if sibling.id == current.id else sibling for sibling in run.suite_executions
        )
        if current_parent_axes == raw_current_axes and raw_current_axes != linked_current_axes:
            run_technical_status, run_evidence_outcome = aggregate_run_result_axes(
                projected_siblings
            )
        else:
            run_technical_status, run_evidence_outcome = aggregate_run_result_axes(
                projected_siblings,
                require_linked_evidence=True,
            )
        resulting_terminal = run_technical_status in TERMINAL_TECHNICAL_STATUSES
        run_started_at = _optional_timestamp(run.started_at)
        run_completed_at = _optional_timestamp(run.completed_at)
        if run_started_at is None and resulting_terminal:
            run_started_at = min(
                (
                    _optional_timestamp(sibling.started_at) or _timestamp(sibling.created_at)
                    for sibling in projected_siblings
                ),
                default=verified_at,
            )
        if resulting_terminal and run_completed_at is None:
            run_completed_at = max(
                (
                    _optional_timestamp(sibling.completed_at) or verified_at
                    for sibling in projected_siblings
                ),
                default=verified_at,
            )
        if not resulting_terminal:
            run_completed_at = None

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
        persist_command = PersistVerifiedPassportV2Command(
            scope=scope,
            actor_id=actor_id,
            evidence_run_id=evidence_run_id,
            passport_revision_id=passport_revision_id,
            verification_receipt_id=verification_receipt_id,
            admission_id=admission_id,
            nonce_claim_id=nonce_claim_id,
            suite_evidence_link_id=suite_evidence_link_id,
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
            suite_started_at=suite_started_at,
            suite_completed_at=suite_completed_at,
            run_technical_status=run_technical_status,
            run_evidence_outcome=run_evidence_outcome,
            run_started_at=run_started_at,
            run_completed_at=run_completed_at,
        )
        record = self._repository.persist_verified_passport_v2(persist_command)
        self._repository.force_evidence_admission_constraints()
        _assert_safe_record(record, persist_command)
        body = {
            "admissionId": record.admission_id,
            "evidenceRunId": record.evidence_run_id,
            "passportRevisionId": record.passport_revision_id,
            "verificationReceiptId": record.verification_receipt_id,
            "nonceClaimId": record.nonce_claim_id,
            "suiteEvidenceLinkId": record.suite_evidence_link_id,
            "runId": record.run_id,
            "suiteExecutionId": record.suite_execution_id,
            "envelopeHash": record.envelope_hash,
            "passportContentHash": record.passport_content_hash,
            "technicalStatus": record.technical_status,
            "evidenceResultStatus": record.evidence_result_status,
            "admissionStatus": record.admission_status,
            "reviewStatus": record.review_status,
            "freshnessStatus": record.freshness_status,
            "runTechnicalStatus": record.run_technical_status,
            "runEvidenceOutcome": record.run_evidence_outcome,
            "overallVerdict": record.overall_verdict,
            "verdictVersion": record.verdict_version,
            "effectiveExpiresAt": record.effective_expires_at.isoformat(),
            "verifiedAt": record.verified_at.isoformat(),
        }
        audit_details = {
            "schemaVersion": _AUDIT_SCHEMA,
            "runId": record.run_id,
            "suiteExecutionId": record.suite_execution_id,
            "admissionId": record.admission_id,
            "evidenceRunId": record.evidence_run_id,
            "passportRevisionId": record.passport_revision_id,
            "verificationReceiptId": record.verification_receipt_id,
            "nonceClaimId": record.nonce_claim_id,
            "suiteEvidenceLinkId": record.suite_evidence_link_id,
            "envelopeHash": record.envelope_hash,
            "passportContentHash": record.passport_content_hash,
            "technicalStatus": record.technical_status,
            "evidenceResultStatus": record.evidence_result_status,
            "admissionStatus": record.admission_status,
            "reviewStatus": record.review_status,
            "freshnessStatus": record.freshness_status,
            "runTechnicalStatus": record.run_technical_status,
            "runEvidenceOutcome": record.run_evidence_outcome,
            "evaluatorRegistryHash": self._evaluator_registry.catalog_hash,
            "evaluatorRegistrationHash": canonical_sha256(evaluator_registration.to_dict()),
        }
        return MutationOutcome(
            body=FrozenJsonObject.from_mapping(body),
            status=201,
            resource_type="evidence_admission",
            resource_id=record.admission_id,
            audit_action="evaluation_v2.evidence.verified_admitted",
            audit_details=FrozenJsonObject.from_mapping(audit_details),
        )


__all__ = ["VerifiedEvidenceAdmissionService"]
