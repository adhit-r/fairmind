"""Independently link one already-verified Evidence Passport V2 admission."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timezone

from src.application.evaluation_workbench_contracts import (
    EVIDENCE_RESULTS_BY_TECHNICAL_STATUS,
    TERMINAL_TECHNICAL_STATUSES,
    aggregate_run_result_axes,
    assurance_request_hash,
)
from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    JsonValue,
    MutationCommand,
    MutationOutcome,
    MutationResult,
    SuiteExecutionRecord,
)
from src.application.ports.evidence_link import (
    EvidenceLinkScope,
    EvidenceLinkUnitOfWork,
    PersistVerifiedEvidenceLinkCommand,
    UuidFactory,
    VerifiedEvidenceLinkAuthorityRecord,
    VerifiedEvidenceLinkRecord,
)
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    validate_idempotency_key,
    validate_public_safe_string,
)

_OPERATION = "evaluation-v2.evidence.verified-link"
_AUDIT_SCHEMA = "evaluation-v2.verified-evidence-link/v1"


def _error(
    code: str,
    message: str,
    *,
    status_code: int = 409,
) -> EvaluationWorkbenchError:
    return EvaluationWorkbenchError(code, message, status_code=status_code)


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise _error(
            "verified_evidence_link_integrity_conflict",
            "The verified evidence link authority is invalid.",
        )
    return value.astimezone(timezone.utc)


def _timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        return _utc(value)
    if not isinstance(value, str):
        raise _error(
            "verified_evidence_link_integrity_conflict",
            "The verified evidence link authority is invalid.",
        )
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return _utc(datetime.fromisoformat(normalized))
    except ValueError:
        raise _error(
            "verified_evidence_link_integrity_conflict",
            "The verified evidence link authority is invalid.",
        ) from None


def _optional_timestamp(value: object) -> datetime | None:
    return None if value is None else _timestamp(value)


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise _error(
            "verified_evidence_link_integrity_conflict",
            "The verified evidence link authority is invalid.",
        )
    return value


def _frozen_array(value: object) -> tuple[JsonValue, ...]:
    if not isinstance(value, (list, tuple)):
        raise _error(
            "verified_evidence_link_integrity_conflict",
            "The verified evidence link authority is invalid.",
        )
    frozen = FrozenJsonObject.from_mapping({"items": value})["items"]
    if not isinstance(frozen, tuple):
        raise _error(
            "verified_evidence_link_integrity_conflict",
            "The verified evidence link authority is invalid.",
        )
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


def _selected_suite(
    authority: VerifiedEvidenceLinkAuthorityRecord,
) -> SuiteExecutionRecord:
    matches = [
        execution
        for execution in authority.run.suite_executions
        if execution.id == authority.scope.suite_execution_id
    ]
    if len(matches) != 1:
        raise _error(
            "verified_evidence_link_integrity_conflict",
            "The verified evidence link authority is invalid.",
        )
    return matches[0]


def _verify_unlinked_suite(
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
            "verified_evidence_link_occupied",
            "The suite execution already has an evidence link.",
        )
    if evidence_result_status not in EVIDENCE_RESULTS_BY_TECHNICAL_STATUS.get(
        technical_status,
        (),
    ):
        raise _error(
            "verified_evidence_link_integrity_conflict",
            "The stored evaluator result is invalid.",
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
                "verified_evidence_link_projection_conflict",
                "The stored result no longer matches the suite execution.",
            )
        return started_at, completed_at
    if execution.technical_status not in {
        "awaiting_evidence",
        "queued",
        "leased",
        "running",
    } or (execution.technical_status in {"queued", "leased"} and technical_status == "succeeded"):
        raise _error(
            "verified_evidence_link_projection_conflict",
            "The suite execution cannot transition to the stored result.",
        )
    return started_at, completed_at


def _assert_safe_record(
    record: VerifiedEvidenceLinkRecord,
    command: PersistVerifiedEvidenceLinkCommand,
) -> None:
    authority = command.authority
    expected = (
        command.scope.organization_id,
        authority.run.workspace_id,
        command.scope.system_id,
        command.scope.run_id,
        command.scope.suite_execution_id,
        command.scope.admission_id,
        authority.evidence_run_id,
        command.scope.passport_revision_id,
        command.suite_evidence_link_id,
        command.technical_status,
        command.evidence_result_status,
        "verified",
        "pending",
        "current",
        command.run_technical_status,
        command.run_evidence_outcome,
        authority.run.overall_verdict,
        authority.run.verdict_version,
        command.actor_id,
        command.linked_at,
    )
    actual = (
        record.organization_id,
        record.workspace_id,
        record.system_id,
        record.run_id,
        record.suite_execution_id,
        record.admission_id,
        record.evidence_run_id,
        record.passport_revision_id,
        record.suite_evidence_link_id,
        record.technical_status,
        record.evidence_result_status,
        record.admission_status,
        record.review_status,
        record.freshness_status,
        record.run_technical_status,
        record.run_evidence_outcome,
        record.overall_verdict,
        record.verdict_version,
        record.linked_by,
        record.linked_at,
    )
    if actual != expected:
        raise _error(
            "verified_evidence_link_integrity_conflict",
            "The verified evidence link failed its relational integrity checks.",
        )


class VerifiedEvidenceLinkService:
    """Revalidate and link one exact stored verified admission."""

    def __init__(
        self,
        unit_of_work: EvidenceLinkUnitOfWork,
        *,
        uuid_factory: UuidFactory = uuid.uuid4,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._repository = unit_of_work.repository
        self._uuid_factory = uuid_factory

    def link_verified_evidence(
        self,
        *,
        scope: EvidenceLinkScope,
        actor_id: str,
        idempotency_key: str,
    ) -> MutationResult:
        if not isinstance(scope, EvidenceLinkScope):
            raise _error(
                "verified_evidence_link_request_invalid",
                "The verified evidence link request is invalid.",
                status_code=422,
            )
        try:
            for value in (
                scope.organization_id,
                scope.system_id,
                scope.run_id,
                scope.suite_execution_id,
                scope.admission_id,
                scope.passport_revision_id,
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
                "verified_evidence_link_request_invalid",
                "The verified evidence link request is invalid.",
                status_code=422,
            ) from error

        request_scope = {
            "organizationId": scope.organization_id,
            "systemId": scope.system_id,
            "runId": scope.run_id,
            "suiteExecutionId": scope.suite_execution_id,
            "admissionId": scope.admission_id,
            "passportRevisionId": scope.passport_revision_id,
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
                body={"contractVersion": "2.0.0"},
            ),
        )

        def link(mutation_now: datetime) -> MutationOutcome:
            linked_at = _utc(mutation_now)
            authority = self._repository.load_verified_evidence_link_authority_for_update(
                scope=scope
            )
            if authority is None:
                raise _error(
                    "verified_evidence_link_not_found",
                    "The verified evidence submission was not found.",
                    status_code=404,
                )
            if (
                authority.scope != scope
                or authority.run.id != scope.run_id
                or authority.run.organization_id != scope.organization_id
                or authority.run.system_id != scope.system_id
                or authority.admission_status != "verified"
                or authority.freshness_status != "current"
                or _utc(authority.verified_at) > linked_at
                or linked_at >= _utc(authority.effective_expires_at)
            ):
                raise _error(
                    "verified_evidence_link_ineligible",
                    "The verified evidence submission is not eligible for linking.",
                )
            passport = authority.passport_snapshot.to_dict()
            result = _mapping(passport.get("result"))
            technical_status = result.get("technicalStatus")
            evidence_result_status = result.get("evidenceResultStatus")
            if not isinstance(technical_status, str) or not isinstance(
                evidence_result_status,
                str,
            ):
                raise _error(
                    "verified_evidence_link_integrity_conflict",
                    "The stored evaluator result is invalid.",
                )
            summary = _mapping(result.get("summary"))
            limitations = _frozen_array(passport.get("limitations"))
            current = _selected_suite(authority)
            existing_started_at, existing_completed_at = _verify_unlinked_suite(
                current,
                technical_status=technical_status,
                evidence_result_status=evidence_result_status,
            )
            was_terminal = current.technical_status in TERMINAL_TECHNICAL_STATUSES
            suite_started_at = (
                existing_started_at if existing_started_at is not None else linked_at
            )
            suite_completed_at = existing_completed_at if was_terminal else linked_at

            run = authority.run
            raw_current_axes = aggregate_run_result_axes(run.suite_executions)
            linked_current_axes = aggregate_run_result_axes(
                run.suite_executions,
                require_linked_evidence=True,
            )
            current_parent_axes = (run.technical_status, run.evidence_outcome)
            if current_parent_axes not in {raw_current_axes, linked_current_axes}:
                raise _error(
                    "verified_evidence_link_projection_conflict",
                    "The evaluation run changed before evidence could be linked.",
                )
            projected = replace(
                current,
                technical_status=technical_status,
                evidence_result_status=evidence_result_status,
                admission_status="verified",
                review_status="pending",
                freshness_status="current",
                evidence_run_id=authority.evidence_run_id,
                passport_revision_id=scope.passport_revision_id,
                linked_by=actor_id,
                linked_at=linked_at.isoformat(),
                result_summary=FrozenJsonObject.from_mapping(summary),
                limitations=limitations,
                started_at=suite_started_at.isoformat(),
                completed_at=suite_completed_at.isoformat(),
                updated_at=linked_at.isoformat(),
            )
            projected_siblings = tuple(
                projected if sibling.id == current.id else sibling
                for sibling in run.suite_executions
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
                        _optional_timestamp(sibling.started_at)
                        or _timestamp(sibling.created_at)
                        for sibling in projected_siblings
                    ),
                    default=linked_at,
                )
            if resulting_terminal and run_completed_at is None:
                run_completed_at = max(
                    (
                        _optional_timestamp(sibling.completed_at) or linked_at
                        for sibling in projected_siblings
                    ),
                    default=linked_at,
                )
            if not resulting_terminal:
                run_completed_at = None

            persist_command = PersistVerifiedEvidenceLinkCommand(
                scope=scope,
                actor_id=actor_id,
                suite_evidence_link_id=_safe_uuid(self._uuid_factory),
                authority=authority,
                technical_status=technical_status,
                evidence_result_status=evidence_result_status,
                result_summary=FrozenJsonObject.from_mapping(summary),
                limitations=limitations,
                suite_started_at=suite_started_at,
                suite_completed_at=suite_completed_at,
                run_technical_status=run_technical_status,
                run_evidence_outcome=run_evidence_outcome,
                run_started_at=run_started_at,
                run_completed_at=run_completed_at,
                linked_at=linked_at,
            )
            record = self._repository.persist_verified_evidence_link(persist_command)
            _assert_safe_record(record, persist_command)
            body = {
                "admissionId": record.admission_id,
                "evidenceRunId": record.evidence_run_id,
                "passportRevisionId": record.passport_revision_id,
                "suiteEvidenceLinkId": record.suite_evidence_link_id,
                "runId": record.run_id,
                "suiteExecutionId": record.suite_execution_id,
                "technicalStatus": record.technical_status,
                "evidenceResultStatus": record.evidence_result_status,
                "admissionStatus": record.admission_status,
                "reviewStatus": record.review_status,
                "freshnessStatus": record.freshness_status,
                "runTechnicalStatus": record.run_technical_status,
                "runEvidenceOutcome": record.run_evidence_outcome,
                "overallVerdict": record.overall_verdict,
                "verdictVersion": record.verdict_version,
                "linkedBy": record.linked_by,
                "linkedAt": record.linked_at.isoformat(),
            }
            audit_details = {
                "schemaVersion": _AUDIT_SCHEMA,
                "runId": record.run_id,
                "suiteExecutionId": record.suite_execution_id,
                "admissionId": record.admission_id,
                "evidenceRunId": record.evidence_run_id,
                "passportRevisionId": record.passport_revision_id,
                "suiteEvidenceLinkId": record.suite_evidence_link_id,
                "submittedBy": authority.submitted_by,
                "linkedBy": record.linked_by,
                "linkedAt": record.linked_at.isoformat(),
                "technicalStatus": record.technical_status,
                "evidenceResultStatus": record.evidence_result_status,
                "runTechnicalStatus": record.run_technical_status,
                "runEvidenceOutcome": record.run_evidence_outcome,
                "evaluatorRegistrationId": authority.evaluator_registration_id,
                "evaluatorRegistrationBindingHash": (
                    authority.evaluator_registration_binding_hash
                ),
            }
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(body),
                status=201,
                resource_type="evidence_link",
                resource_id=record.suite_evidence_link_id,
                audit_action="evaluation_v2.evidence.verified_linked",
                audit_details=FrozenJsonObject.from_mapping(audit_details),
            )

        return self._unit_of_work.mutate(command, link)


__all__ = ["VerifiedEvidenceLinkService"]
