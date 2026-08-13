"""Fail-closed four-eyes review of one verified Evidence Passport V2."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationCommand,
    MutationOutcome,
    MutationResult,
)
from src.application.ports.evidence_review import (
    EvidenceReviewAuthorityRecord,
    EvidenceReviewScope,
    EvidenceReviewUnitOfWork,
    PersistEvidenceReviewCommand,
    ReviewedEvidenceRecord,
    UuidFactory,
)
from src.application.evaluation_workbench_contracts import assurance_request_hash
from src.application import evidence_freshness as freshness
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    canonical_sha256,
    validate_idempotency_key,
    validate_public_safe_string,
)

_OPERATION = "evaluation-v2.evidence.review"
_AUDIT_SCHEMA = "evaluation-v2.verified-evidence-review/v2"
_DECISIONS = frozenset({"accepted", "rejected"})


def _error(code: str, message: str, *, status_code: int = 409) -> EvaluationWorkbenchError:
    return EvaluationWorkbenchError(code, message, status_code=status_code)


def _utc(value: datetime, *, code: str = "evidence_review_chronology_invalid") -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise _error(code, "The evidence-review chronology is invalid.")
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _utc(value).isoformat()


def _safe_uuid(factory: UuidFactory) -> str:
    value = str(factory())
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError) as error:
        raise RuntimeError("The server UUID factory returned an invalid identity.") from error
    if str(parsed) != value:
        raise RuntimeError("The server UUID factory returned a non-canonical identity.")
    return value


def _validate_string(value: object, *, code: str) -> str:
    if not isinstance(value, str):
        raise _error(code, "The evidence-review request is invalid.", status_code=422)
    try:
        validate_public_safe_string(value)
    except AssuranceContractValidationError as error:
        raise _error(code, "The evidence-review request is invalid.", status_code=422) from error
    return value


def _validate_scope(scope: EvidenceReviewScope) -> None:
    for value in (
        scope.organization_id,
        scope.workspace_id,
        scope.system_id,
        scope.run_id,
        scope.suite_execution_id,
        scope.admission_id,
        scope.passport_revision_id,
    ):
        _validate_string(value, code="evidence_review_scope_invalid")


def _validate_request(
    *,
    decision: object,
    rationale: object,
    expected_review_version: object,
    idempotency_key: str,
) -> tuple[str, str, int, str]:
    if not isinstance(decision, str) or decision not in _DECISIONS:
        raise _error(
            "evidence_review_decision_invalid", "The review decision is invalid.", status_code=422
        )
    safe_rationale = _validate_string(rationale, code="evidence_review_rationale_invalid")
    if isinstance(expected_review_version, bool) or not isinstance(expected_review_version, int):
        raise _error(
            "evidence_review_version_invalid", "The review version is invalid.", status_code=422
        )
    if expected_review_version < 0:
        raise _error(
            "evidence_review_version_invalid", "The review version is invalid.", status_code=422
        )
    try:
        key = validate_idempotency_key(idempotency_key)
    except AssuranceContractValidationError as error:
        raise _error(
            "invalid_idempotency_key", "The Idempotency-Key is invalid.", status_code=422
        ) from error
    return decision, safe_rationale, expected_review_version, key


def _assert_authority(
    *,
    authority: EvidenceReviewAuthorityRecord,
    scope: EvidenceReviewScope,
    actor_id: str,
    expected_review_version: int,
    now: datetime,
) -> None:
    if authority.scope != scope or authority.admission_contract_version != "2.0.0":
        raise _error(
            "evidence_review_integrity_conflict",
            "The locked evidence-review authority is inconsistent.",
        )
    if authority.admission_status != "verified":
        raise _error(
            "evidence_review_admission_not_verified",
            "Only verified evidence can be reviewed.",
        )
    freshness.require_review_eligible(
        authority.operational_freshness,
        expected_recorded_status=authority.freshness_status,
        error_code="evidence_review_evidence_not_current",
        error_message="Only current or expiring evidence can be reviewed.",
    )
    if _utc(authority.operational_freshness.evaluated_at) != now:
        raise _error(
            "evidence_review_integrity_conflict",
            "The locked evidence-review authority is inconsistent.",
        )
    if authority.review_status != "pending" or authority.current_review_version != 0:
        raise _error(
            "evidence_review_not_pending",
            "The evidence review is no longer pending.",
        )
    if authority.current_review_version != expected_review_version:
        raise _error(
            "evidence_review_version_conflict",
            "The evidence review version is stale.",
        )
    if authority.governance_decision_exists:
        raise _error(
            "evidence_review_frozen",
            "Evidence reviews are frozen after a governance decision.",
        )
    if actor_id in {
        authority.submitted_by,
        authority.linked_by,
        authority.run_requested_by,
    }:
        raise _error(
            "evidence_review_separation_required",
            "The reviewer must be independent from submission, linking, and run request.",
        )
    effective_expires_at = _utc(authority.effective_expires_at)
    key_valid_from = _utc(authority.key_valid_from)
    key_valid_until = _utc(authority.key_valid_until)
    key_revoked_at = None if authority.key_revoked_at is None else _utc(authority.key_revoked_at)
    if effective_expires_at <= now:
        raise _error(
            "evidence_review_evidence_expired",
            "Expired evidence cannot be reviewed.",
        )
    if authority.trust_policy_status != "active":
        raise _error(
            "evidence_review_trust_policy_inactive",
            "The evidence trust policy is no longer active.",
        )
    if authority.issuer_status != "active":
        raise _error(
            "evidence_review_issuer_inactive",
            "The evidence issuer is no longer active.",
        )
    if key_revoked_at is not None and key_revoked_at <= now:
        raise _error(
            "evidence_review_signing_key_revoked",
            "The evidence signing key has been revoked.",
        )
    if not key_valid_from <= now < key_valid_until:
        raise _error(
            "evidence_review_signing_key_inactive",
            "The evidence signing key is not currently valid.",
        )


def _body(record: ReviewedEvidenceRecord) -> dict[str, object]:
    result = {
        "reviewId": record.review_id,
        "admissionId": record.admission_id,
        "passportRevisionId": record.passport_revision_id,
        "runId": record.run_id,
        "suiteExecutionId": record.suite_execution_id,
        "decision": record.decision,
        "rationale": record.rationale,
        "reviewVersion": record.review_version,
        "reviewedBy": record.reviewed_by,
        "reviewedAt": _iso(record.reviewed_at),
        "admissionStatus": record.admission_status,
        "reviewStatus": record.review_status,
        "freshnessStatus": record.freshness_status,
        "technicalStatus": record.technical_status,
        "evidenceResultStatus": record.evidence_result_status,
        "runTechnicalStatus": record.run_technical_status,
        "runEvidenceOutcome": record.run_evidence_outcome,
    }
    result.update(
        freshness.public_projection(
            record.operational_freshness,
            expected_recorded_status=record.freshness_status,
        )
    )
    result["decisionEvidenceEligibleAtReview"] = (
        record.operational_freshness.decision_eligible is True
    )
    return result


def _assert_record(
    record: ReviewedEvidenceRecord,
    command: PersistEvidenceReviewCommand,
) -> None:
    authority = command.authority
    expected = (
        command.review_id,
        command.scope.organization_id,
        command.scope.workspace_id,
        command.scope.system_id,
        command.scope.run_id,
        command.scope.suite_execution_id,
        command.scope.admission_id,
        command.scope.passport_revision_id,
        authority.evidence_run_id,
        command.decision,
        command.rationale,
        command.next_review_version,
        command.actor_id,
        "verified",
        command.decision,
        authority.freshness_status,
        authority.technical_status,
        authority.evidence_result_status,
        authority.run_technical_status,
        authority.run_evidence_outcome,
    )
    actual = (
        record.review_id,
        record.organization_id,
        record.workspace_id,
        record.system_id,
        record.run_id,
        record.suite_execution_id,
        record.admission_id,
        record.passport_revision_id,
        record.evidence_run_id,
        record.decision,
        record.rationale,
        record.review_version,
        record.reviewed_by,
        record.admission_status,
        record.review_status,
        record.freshness_status,
        record.technical_status,
        record.evidence_result_status,
        record.run_technical_status,
        record.run_evidence_outcome,
    )
    if actual != expected:
        raise _error(
            "evidence_review_integrity_conflict",
            "The evidence-review projection is inconsistent.",
        )
    reviewed_at = _utc(record.reviewed_at)
    freshness.require_review_eligible(
        record.operational_freshness,
        expected_recorded_status=record.freshness_status,
        error_code="evidence_review_evidence_not_current",
        error_message="Only current or expiring evidence can be reviewed.",
    )
    if _utc(record.operational_freshness.evaluated_at) != reviewed_at:
        raise _error(
            "evidence_review_integrity_conflict",
            "The persisted evidence-review projection is inconsistent.",
        )


class VerifiedEvidenceReviewService:
    """Creates an append-only evidence review, never a governance decision."""

    def __init__(
        self,
        unit_of_work: EvidenceReviewUnitOfWork,
        *,
        uuid_factory: UuidFactory = uuid.uuid4,
    ) -> None:
        self.unit_of_work = unit_of_work
        self.repository = unit_of_work.repository
        self._uuid_factory = uuid_factory

    def review_verified_evidence(
        self,
        *,
        scope: EvidenceReviewScope,
        actor_id: str,
        idempotency_key: str,
        decision: str,
        rationale: str,
        expected_review_version: int,
    ) -> MutationResult:
        _validate_scope(scope)
        safe_actor_id = _validate_string(actor_id, code="evidence_review_actor_invalid")
        decision, rationale, expected_review_version, key = _validate_request(
            decision=decision,
            rationale=rationale,
            expected_review_version=expected_review_version,
            idempotency_key=idempotency_key,
        )
        command = MutationCommand(
            organization_id=scope.organization_id,
            actor_id=safe_actor_id,
            operation=_OPERATION,
            idempotency_key=key,
            request_hash=assurance_request_hash(
                method="POST",
                operation=_OPERATION,
                scope={
                    "organizationId": scope.organization_id,
                    "workspaceId": scope.workspace_id,
                    "systemId": scope.system_id,
                    "runId": scope.run_id,
                    "suiteExecutionId": scope.suite_execution_id,
                    "admissionId": scope.admission_id,
                    "passportRevisionId": scope.passport_revision_id,
                },
                body={
                    "decision": decision,
                    "rationale": rationale,
                    "expectedReviewVersion": expected_review_version,
                },
            ),
        )

        def review(_mutation_now: datetime) -> MutationOutcome:
            authority = self.repository.load_evidence_review_authority_for_update(scope=scope)
            if authority is None:
                raise _error(
                    "evidence_review_scope_not_found",
                    "The evidence admission was not found in this scope.",
                    status_code=404,
                )
            advisory_evaluated_at = _utc(authority.operational_freshness.evaluated_at)
            _assert_authority(
                authority=authority,
                scope=scope,
                actor_id=safe_actor_id,
                expected_review_version=expected_review_version,
                now=advisory_evaluated_at,
            )
            persistence = PersistEvidenceReviewCommand(
                scope=scope,
                authority=authority,
                review_id=_safe_uuid(self._uuid_factory),
                actor_id=safe_actor_id,
                decision=decision,
                rationale=rationale,
                expected_review_version=expected_review_version,
                next_review_version=expected_review_version + 1,
                reviewed_at=advisory_evaluated_at,
            )
            record = self.repository.persist_evidence_review(persistence)
            _assert_record(record, persistence)
            body = _body(record)
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(body),
                status=201,
                resource_type="evaluation_evidence_review",
                resource_id=record.review_id,
                audit_action="evaluation_v2.evidence.reviewed",
                audit_details=FrozenJsonObject.from_mapping(
                    {
                        "schemaVersion": _AUDIT_SCHEMA,
                        "runId": scope.run_id,
                        "suiteExecutionId": scope.suite_execution_id,
                        "admissionId": scope.admission_id,
                        "passportRevisionId": scope.passport_revision_id,
                        "evidenceRunId": authority.evidence_run_id,
                        "decision": decision,
                        "reviewVersion": persistence.next_review_version,
                        "rationaleHash": canonical_sha256({"rationale": rationale}),
                        "admissionStatus": "verified",
                        "reviewStatus": decision,
                        "recordedFreshnessStatus": record.freshness_status,
                        "effectiveFreshnessStatus": (
                            record.operational_freshness.effective_freshness_status
                        ),
                        "freshnessContractVersion": (
                            record.operational_freshness.freshness_contract_version
                        ),
                        "freshnessEvaluatedAt": _iso(
                            record.operational_freshness.evaluated_at
                        ),
                        "freshnessEffectiveAt": _iso(
                            record.operational_freshness.effective_at
                        ),
                        "expiringAt": (
                            None
                            if record.operational_freshness.expiring_at is None
                            else _iso(record.operational_freshness.expiring_at)
                        ),
                        "freshnessReasonCodesHash": canonical_sha256(
                            list(record.operational_freshness.reason_codes)
                        ),
                        "decisionEvidenceEligibleAtReview": (
                            record.operational_freshness.decision_eligible is True
                        ),
                        "technicalStatus": authority.technical_status,
                        "evidenceResultStatus": authority.evidence_result_status,
                    }
                ),
            )

        return self.unit_of_work.mutate(command, review)
