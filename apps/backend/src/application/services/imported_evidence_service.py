"""Atomic admission of explicitly unverified imported evidence reports.

Imported reports are intentionally not Evidence Passport V2 documents.  They
are persisted as claimed, human-review-only material and never obtain a
verification receipt, signer identity, or decision-evidence authority.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from src.application.evaluation_workbench_contracts import (
    EVIDENCE_RESULTS_BY_TECHNICAL_STATUS,
    TERMINAL_TECHNICAL_STATUSES,
    aggregate_run_result_axes,
    assurance_request_hash,
    verify_run_record_binding,
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
from src.application.ports.evidence_admission import EvidenceAdmissionScope
from src.application.ports.imported_evidence import (
    ImportedEvidenceAuthorityRecord,
    ImportedEvidenceRecord,
    ImportedEvidenceUnitOfWork,
    PersistUnverifiedImportedEvidenceCommand,
    UuidFactory,
)
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    canonical_sha256,
    reject_sensitive_keys,
    require_canonical_size,
    validate_idempotency_key,
    validate_public_safe_string,
    validate_public_safe_values,
)


_OPERATION = "evaluation-v2.evidence.unverified-import"
_AUDIT_SCHEMA = "evaluation-v2.unverified-evidence-import/v1"
_CHECKED_BY = "fairmind/imported-evidence-service"
_REPORT_ID = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_.:-]{0,94}[A-Za-z0-9])?$")
_LOWER_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_MAX_RESULT_SUMMARY_BYTES = 64 * 1024
_MAX_ARTIFACT_REFS = 50
_MAX_ARTIFACT_BYTES = 32 * 1024
_MAX_LIMITATIONS = 64
_MAX_LIMITATIONS_BYTES = 8 * 1024
_MAX_LIMITATION_BYTES = 512
_MAX_ARTIFACT_IDENTIFIER_BYTES = 96
_MAX_ARTIFACT_ROLE_BYTES = 48
_MAX_MEDIA_TYPE_BYTES = 128
_EXPECTED_PAYLOAD_KEYS = frozenset(
    {
        "reportId",
        "reportContentHash",
        "capturedAt",
        "claimedTechnicalStatus",
        "claimedEvidenceResultStatus",
        "claimedResultSummary",
        "artifactRefs",
        "limitations",
    }
)
_EXPECTED_ARTIFACT_KEYS = frozenset(
    {"artifactId", "role", "sha256", "mediaType", "sizeBytes"}
)


def _error(
    code: str,
    message: str,
    *,
    status_code: int = 409,
) -> EvaluationWorkbenchError:
    return EvaluationWorkbenchError(code, message, status_code=status_code)


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


def _utc(value: datetime, *, code: str = "imported_evidence_chronology_invalid") -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise _error(code, "The imported evidence chronology is invalid.")
    return value.astimezone(timezone.utc)


def _stored_timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        return _utc(value)
    if not isinstance(value, str):
        raise _error("imported_evidence_authority_invalid", "The locked import authority is invalid.")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return _utc(datetime.fromisoformat(normalized), code="imported_evidence_authority_invalid")
    except ValueError:
        raise _error(
            "imported_evidence_authority_invalid",
            "The locked import authority is invalid.",
        ) from None


def _optional_stored_timestamp(value: object) -> datetime | None:
    return None if value is None else _stored_timestamp(value)


def _canonical_utc_input(value: object) -> datetime:
    if not isinstance(value, str):
        raise _error(
            "imported_evidence_chronology_invalid",
            "The imported evidence chronology is invalid.",
            status_code=422,
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise _error(
            "imported_evidence_chronology_invalid",
            "The imported evidence chronology is invalid.",
            status_code=422,
        ) from None
    if parsed.tzinfo is None:
        raise _error(
            "imported_evidence_chronology_invalid",
            "The imported evidence chronology is invalid.",
            status_code=422,
        )
    normalized = parsed.astimezone(timezone.utc)
    if value != normalized.isoformat():
        raise _error(
            "imported_evidence_chronology_invalid",
            "The imported evidence chronology is invalid.",
            status_code=422,
        )
    return normalized


def _safe_string(value: object, *, code: str, maximum_bytes: int) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > maximum_bytes:
        raise _error(code, "The imported evidence request is invalid.", status_code=422)
    try:
        validate_public_safe_string(value)
    except (AssuranceContractValidationError, UnicodeError) as error:
        raise _error(code, "The imported evidence request is invalid.", status_code=422) from error
    return value


def _safe_json(
    value: object,
    *,
    code: str,
    maximum_bytes: int,
    validate_values: bool = True,
) -> None:
    try:
        reject_sensitive_keys(value)
        if validate_values:
            validate_public_safe_values(value)
        require_canonical_size(
            value,
            maximum_bytes=maximum_bytes,
            code=code,
            message="Imported evidence exceeds the bounded assurance contract.",
        )
    except (AssuranceContractValidationError, TypeError, UnicodeError, ValueError) as error:
        raise _error(code, "The imported evidence request is invalid.", status_code=422) from error


def _frozen_array(value: object, *, code: str) -> tuple[JsonValue, ...]:
    if not isinstance(value, (list, tuple)):
        raise _error(code, "The imported evidence request is invalid.", status_code=422)
    try:
        frozen = FrozenJsonObject.from_mapping({"items": value})["items"]
    except (TypeError, UnicodeError) as error:
        raise _error(code, "The imported evidence request is invalid.", status_code=422) from error
    if not isinstance(frozen, tuple):
        raise _error(code, "The imported evidence request is invalid.", status_code=422)
    return frozen


def _validate_artifact_refs(value: object) -> tuple[JsonValue, ...]:
    if not isinstance(value, (list, tuple)) or len(value) > _MAX_ARTIFACT_REFS:
        raise _error(
            "imported_evidence_artifacts_invalid",
            "The imported evidence request is invalid.",
            status_code=422,
        )
    normalized: list[dict[str, object]] = []
    artifact_ids: set[str] = set()
    for item in value:
        if not isinstance(item, Mapping) or set(item) != _EXPECTED_ARTIFACT_KEYS:
            raise _error(
                "imported_evidence_artifacts_invalid",
                "The imported evidence request is invalid.",
                status_code=422,
            )
        artifact_id = _safe_string(
            item.get("artifactId"),
            code="imported_evidence_artifacts_invalid",
            maximum_bytes=_MAX_ARTIFACT_IDENTIFIER_BYTES,
        )
        role = _safe_string(
            item.get("role"),
            code="imported_evidence_artifacts_invalid",
            maximum_bytes=_MAX_ARTIFACT_ROLE_BYTES,
        )
        media_type = _safe_string(
            item.get("mediaType"),
            code="imported_evidence_artifacts_invalid",
            maximum_bytes=_MAX_MEDIA_TYPE_BYTES,
        )
        sha256 = item.get("sha256")
        size_bytes = item.get("sizeBytes")
        if (
            not isinstance(sha256, str)
            or _LOWER_HEX64.fullmatch(sha256) is None
            or isinstance(size_bytes, bool)
            or not isinstance(size_bytes, int)
            or not 0 <= size_bytes < 2**53
        ):
            raise _error(
                "imported_evidence_artifacts_invalid",
                "The imported evidence request is invalid.",
                status_code=422,
            )
        if artifact_id in artifact_ids:
            raise _error(
                "imported_evidence_artifacts_invalid",
                "The imported evidence request is invalid.",
                status_code=422,
            )
        artifact_ids.add(artifact_id)
        normalized.append(
            {
                "artifactId": artifact_id,
                "role": role,
                "sha256": sha256,
                "mediaType": media_type,
                "sizeBytes": size_bytes,
            }
        )
    _safe_json(
        normalized,
        code="imported_evidence_artifacts_invalid",
        maximum_bytes=_MAX_ARTIFACT_BYTES,
        validate_values=False,
    )
    return _frozen_array(normalized, code="imported_evidence_artifacts_invalid")


def _validate_limitations(value: object) -> tuple[JsonValue, ...]:
    if not isinstance(value, (list, tuple)) or len(value) > _MAX_LIMITATIONS:
        raise _error(
            "imported_evidence_limitations_invalid",
            "The imported evidence request is invalid.",
            status_code=422,
        )
    normalized = [
        _safe_string(
            item,
            code="imported_evidence_limitations_invalid",
            maximum_bytes=_MAX_LIMITATION_BYTES,
        )
        for item in value
    ]
    _safe_json(
        normalized,
        code="imported_evidence_limitations_invalid",
        maximum_bytes=_MAX_LIMITATIONS_BYTES,
    )
    return _frozen_array(normalized, code="imported_evidence_limitations_invalid")


def _validate_payload(value: object) -> FrozenJsonObject:
    if not isinstance(value, Mapping) or set(value) != _EXPECTED_PAYLOAD_KEYS:
        raise _error(
            "imported_evidence_payload_invalid",
            "The imported evidence request is invalid.",
            status_code=422,
        )
    report_id = _safe_string(
        value.get("reportId"),
        code="imported_evidence_report_id_invalid",
        maximum_bytes=96,
    )
    if _REPORT_ID.fullmatch(report_id) is None:
        raise _error(
            "imported_evidence_report_id_invalid",
            "The imported evidence request is invalid.",
            status_code=422,
        )
    content_hash = value.get("reportContentHash")
    if not isinstance(content_hash, str) or _LOWER_HEX64.fullmatch(content_hash) is None:
        raise _error(
            "imported_evidence_content_hash_invalid",
            "The imported evidence request is invalid.",
            status_code=422,
        )
    captured_at = _canonical_utc_input(value.get("capturedAt"))
    technical_status = value.get("claimedTechnicalStatus")
    evidence_result_status = value.get("claimedEvidenceResultStatus")
    if (
        not isinstance(technical_status, str)
        or not isinstance(evidence_result_status, str)
        or technical_status not in TERMINAL_TECHNICAL_STATUSES
        or evidence_result_status
        not in EVIDENCE_RESULTS_BY_TECHNICAL_STATUS.get(technical_status, ())
    ):
        raise _error(
            "imported_evidence_result_invalid",
            "The claimed result axes are inconsistent.",
            status_code=422,
        )
    summary = value.get("claimedResultSummary")
    if not isinstance(summary, Mapping):
        raise _error(
            "imported_evidence_summary_invalid",
            "The imported evidence request is invalid.",
            status_code=422,
        )
    summary_copy = dict(summary)
    _safe_json(
        summary_copy,
        code="imported_evidence_summary_invalid",
        maximum_bytes=_MAX_RESULT_SUMMARY_BYTES,
    )
    try:
        frozen_summary = FrozenJsonObject.from_mapping(summary_copy)
    except (TypeError, UnicodeError) as error:
        raise _error(
            "imported_evidence_summary_invalid",
            "The imported evidence request is invalid.",
            status_code=422,
        ) from error
    artifact_refs = _validate_artifact_refs(value.get("artifactRefs"))
    limitations = _validate_limitations(value.get("limitations"))
    if evidence_result_status == "passed_with_limitations" and not limitations:
        raise _error(
            "imported_evidence_result_invalid",
            "The claimed result axes are inconsistent.",
            status_code=422,
        )
    if technical_status != "succeeded" and not summary_copy:
        raise _error(
            "imported_evidence_result_invalid",
            "The claimed result axes are inconsistent.",
            status_code=422,
        )
    return FrozenJsonObject.from_mapping(
        {
            "reportId": report_id,
            "reportContentHash": content_hash,
            "capturedAt": captured_at.isoformat(),
            "claimedTechnicalStatus": technical_status,
            "claimedEvidenceResultStatus": evidence_result_status,
            "claimedResultSummary": frozen_summary.to_dict(),
            "artifactRefs": artifact_refs,
            "limitations": limitations,
        }
    )


def _validate_request(
    *,
    scope: EvidenceAdmissionScope,
    actor_id: object,
    idempotency_key: object,
    payload: object,
) -> tuple[str, FrozenJsonObject]:
    if not isinstance(scope, EvidenceAdmissionScope):
        raise _error(
            "imported_evidence_scope_invalid",
            "The imported evidence scope is invalid.",
            status_code=422,
        )
    try:
        for identifier in (
            scope.organization_id,
            scope.system_id,
            scope.run_id,
            scope.suite_execution_id,
            actor_id,
        ):
            if not isinstance(identifier, str) or not identifier:
                raise AssuranceContractValidationError("invalid_identifier", "Identifier is invalid.")
            validate_public_safe_string(identifier)
        key = validate_idempotency_key(idempotency_key)
    except (AssuranceContractValidationError, TypeError, UnicodeError) as error:
        raise _error(
            "imported_evidence_request_invalid",
            "The imported evidence request is invalid.",
            status_code=422,
        ) from error
    return key, _validate_payload(payload)


def _selected_suite(
    authority: ImportedEvidenceAuthorityRecord,
) -> tuple[SuiteExecutionRecord, object]:
    matches = [
        execution
        for execution in authority.run.suite_executions
        if execution.id == authority.scope.suite_execution_id
    ]
    if len(matches) != 1:
        raise _error(
            "imported_evidence_authority_invalid",
            "The locked import authority is inconsistent.",
        )
    execution = matches[0]
    selections = [
        selection
        for selection in authority.plan_graph.suites
        if selection.ordinal == execution.ordinal and selection.suite.id == execution.suite_version_id
    ]
    if len(selections) != 1:
        raise _error(
            "imported_evidence_authority_invalid",
            "The locked import authority is inconsistent.",
        )
    return execution, selections[0].suite


def _validate_authority(
    authority: ImportedEvidenceAuthorityRecord,
    *,
    scope: EvidenceAdmissionScope,
    database_now: datetime,
) -> None:
    graph = authority.plan_graph
    run = authority.run
    if (
        authority.scope != scope
        or graph.scope.organization_id != scope.organization_id
        or graph.scope.system_id != scope.system_id
        or run.organization_id != scope.organization_id
        or run.system_id != scope.system_id
        or run.workspace_id != graph.scope.workspace_id
        or run.id != scope.run_id
        or sum(execution.id == scope.suite_execution_id for execution in run.suite_executions) != 1
    ):
        raise _error(
            "imported_evidence_scope_mismatch",
            "The locked import authority has the wrong scope.",
        )
    try:
        verify_run_record_binding(run, graph)
    except EvaluationWorkbenchError:
        raise
    except Exception as error:
        raise _error(
            "imported_evidence_authority_invalid",
            "The locked import authority is inconsistent.",
        ) from error
    if (
        graph.plan.status != "active"
        or graph.target.status != "active"
        or graph.trust_policy.status != "active"
        or any(selection.suite.status != "active" for selection in graph.suites)
    ):
        raise _error(
            "imported_evidence_authority_inactive",
            "The bound plan, target, trust policy, or suite is inactive.",
        )
    if graph.plan.delivery_mode != "imported_report":
        raise _error(
            "imported_evidence_delivery_mode_invalid",
            "The bound plan does not accept imported reports.",
        )
    if (
        not isinstance(authority.maximum_evidence_age_seconds, int)
        or isinstance(authority.maximum_evidence_age_seconds, bool)
        or authority.maximum_evidence_age_seconds <= 0
        or authority.unsigned_import_policy != "manual_review"
    ):
        raise _error(
            "imported_evidence_trust_policy_invalid",
            "The active trust policy does not allow unverified imported evidence.",
        )
    _selected_suite(authority)
    _utc(database_now)


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
            "imported_evidence_result_invalid",
            "The claimed result axes are inconsistent.",
            status_code=422,
        )
    started_at = _optional_stored_timestamp(execution.started_at)
    completed_at = _optional_stored_timestamp(execution.completed_at)
    if execution.technical_status in TERMINAL_TECHNICAL_STATUSES:
        if (
            execution.technical_status != technical_status
            or execution.evidence_result_status != evidence_result_status
            or completed_at is None
        ):
            raise _error(
                "suite_execution_result_conflict",
                "The claimed result does not match the terminal suite execution.",
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
            "The suite execution cannot transition to the claimed result.",
        )
    return started_at, completed_at


def _assert_record(
    record: ImportedEvidenceRecord,
    command: PersistUnverifiedImportedEvidenceCommand,
) -> None:
    expected = (
        command.scope.organization_id,
        command.authority.run.workspace_id,
        command.scope.system_id,
        command.scope.run_id,
        command.scope.suite_execution_id,
        command.evidence_run_id,
        command.passport_revision_id,
        command.admission_id,
        command.nonce_claim_id,
        command.suite_evidence_link_id,
        command.report_content_hash,
        command.import_snapshot_hash,
        command.technical_status,
        command.evidence_result_status,
        "unverified",
        "pending",
        "current",
        command.run_technical_status,
        command.run_evidence_outcome,
        command.authority.run.overall_verdict,
        command.authority.run.verdict_version,
        command.effective_expires_at,
        command.imported_at,
    )
    actual = (
        record.organization_id,
        record.workspace_id,
        record.system_id,
        record.run_id,
        record.suite_execution_id,
        record.evidence_run_id,
        record.passport_revision_id,
        record.admission_id,
        record.nonce_claim_id,
        record.suite_evidence_link_id,
        record.report_content_hash,
        record.import_snapshot_hash,
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
        record.imported_at,
    )
    if actual != expected:
        raise _error(
            "imported_evidence_integrity_conflict",
            "The imported evidence graph failed its relational integrity checks.",
        )


class ImportedEvidenceService:
    """Persist one bounded unsigned report as explicitly unverified material."""

    def __init__(
        self,
        unit_of_work: ImportedEvidenceUnitOfWork,
        *,
        uuid_factory: UuidFactory = uuid.uuid4,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._repository = unit_of_work.repository
        self._uuid_factory = uuid_factory

    def import_unverified_report(
        self,
        *,
        scope: EvidenceAdmissionScope,
        actor_id: str,
        idempotency_key: str,
        payload: Mapping[str, object],
    ) -> MutationResult:
        key, normalized = _validate_request(
            scope=scope,
            actor_id=actor_id,
            idempotency_key=idempotency_key,
            payload=payload,
        )
        request_scope = {
            "organizationId": scope.organization_id,
            "systemId": scope.system_id,
            "runId": scope.run_id,
            "suiteExecutionId": scope.suite_execution_id,
        }
        command = MutationCommand(
            organization_id=scope.organization_id,
            actor_id=actor_id,
            operation=_OPERATION,
            idempotency_key=key,
            request_hash=assurance_request_hash(
                method="POST",
                operation=_OPERATION,
                scope=request_scope,
                body=normalized.to_dict(),
            ),
        )

        def persist(_mutation_now: datetime) -> MutationOutcome:
            del _mutation_now
            authority = self._repository.load_imported_evidence_authority_for_update(scope=scope)
            if authority is None:
                raise _error(
                    "imported_evidence_authority_not_found",
                    "The bound imported-evidence authority was not found.",
                    status_code=404,
                )
            imported_at = _utc(self._repository.read_fresh_utc_now())
            _validate_authority(authority, scope=scope, database_now=imported_at)
            return self._persist(
                scope=scope,
                actor_id=actor_id,
                authority=authority,
                payload=normalized,
                imported_at=imported_at,
            )

        return self._unit_of_work.mutate(command, persist)

    def _persist(
        self,
        *,
        scope: EvidenceAdmissionScope,
        actor_id: str,
        authority: ImportedEvidenceAuthorityRecord,
        payload: FrozenJsonObject,
        imported_at: datetime,
    ) -> MutationOutcome:
        run = authority.run
        current, suite = _selected_suite(authority)
        payload_data = payload.to_dict()
        report_id = payload_data["reportId"]
        report_content_hash = payload_data["reportContentHash"]
        captured_at = _canonical_utc_input(payload_data["capturedAt"])
        technical_status = payload_data["claimedTechnicalStatus"]
        evidence_result_status = payload_data["claimedEvidenceResultStatus"]
        summary_value = payload_data["claimedResultSummary"]
        if not isinstance(report_id, str) or not isinstance(report_content_hash, str):
            raise _error("imported_evidence_integrity_conflict", "The imported evidence graph is invalid.")
        if not isinstance(technical_status, str) or not isinstance(evidence_result_status, str):
            raise _error("imported_evidence_integrity_conflict", "The imported evidence graph is invalid.")
        if not isinstance(summary_value, Mapping):
            raise _error("imported_evidence_integrity_conflict", "The imported evidence graph is invalid.")
        artifact_refs = _frozen_array(payload_data["artifactRefs"], code="imported_evidence_integrity_conflict")
        limitations = _frozen_array(payload_data["limitations"], code="imported_evidence_integrity_conflict")
        requested_at = _stored_timestamp(run.envelope.to_dict().get("requestedAt"))
        effective_expires_at = captured_at + timedelta(
            seconds=authority.maximum_evidence_age_seconds
        )
        if not requested_at <= captured_at <= imported_at:
            raise _error(
                "imported_evidence_chronology_invalid",
                "The imported evidence chronology is invalid.",
            )
        if imported_at >= effective_expires_at:
            raise _error(
                "imported_evidence_expired",
                "The imported evidence is no longer current.",
            )
        if imported_at <= max(_stored_timestamp(run.updated_at), _stored_timestamp(current.updated_at)):
            raise _error(
                "imported_evidence_clock_invalid",
                "The trusted database clock does not follow the locked run state.",
            )
        existing_started_at, existing_completed_at = _verify_current_suite(
            current,
            technical_status=technical_status,
            evidence_result_status=evidence_result_status,
        )
        was_terminal = current.technical_status in TERMINAL_TECHNICAL_STATUSES
        suite_started_at = existing_started_at if existing_started_at is not None else imported_at
        suite_completed_at = existing_completed_at if was_terminal else imported_at

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
            passport_id,
            admission_id,
            nonce_claim_id,
            suite_evidence_link_id,
        ) = _graph_ids(self._uuid_factory)
        projected = replace(
            current,
            technical_status=technical_status,
            evidence_result_status=evidence_result_status,
            admission_status="unverified",
            review_status="pending",
            freshness_status="current",
            evidence_run_id=evidence_run_id,
            passport_revision_id=passport_revision_id,
            linked_by=actor_id,
            linked_at=imported_at.isoformat(),
            result_summary=FrozenJsonObject.from_mapping(dict(summary_value)),
            limitations=limitations,
            started_at=suite_started_at.isoformat(),
            completed_at=suite_completed_at.isoformat(),
            updated_at=imported_at.isoformat(),
        )
        projected_siblings = tuple(
            projected if sibling.id == current.id else sibling for sibling in run.suite_executions
        )
        if current_parent_axes == raw_current_axes and raw_current_axes != linked_current_axes:
            run_technical_status, run_evidence_outcome = aggregate_run_result_axes(projected_siblings)
        else:
            run_technical_status, run_evidence_outcome = aggregate_run_result_axes(
                projected_siblings,
                require_linked_evidence=True,
            )
        resulting_terminal = run_technical_status in TERMINAL_TECHNICAL_STATUSES
        run_started_at = _optional_stored_timestamp(run.started_at)
        run_completed_at = _optional_stored_timestamp(run.completed_at)
        if run_started_at is None and resulting_terminal:
            run_started_at = min(
                (
                    _optional_stored_timestamp(sibling.started_at)
                    or _stored_timestamp(sibling.created_at)
                    for sibling in projected_siblings
                ),
                default=imported_at,
            )
        if resulting_terminal and run_completed_at is None:
            run_completed_at = max(
                (
                    _optional_stored_timestamp(sibling.completed_at) or imported_at
                    for sibling in projected_siblings
                ),
                default=imported_at,
            )
        if not resulting_terminal:
            run_completed_at = None

        snapshot = {
            "schemaVersion": "1.0.0",
            "sourceType": "imported_report",
            "resultAuthority": "claimed",
            "humanReviewOnly": True,
            "decisionEvidenceEligible": False,
            "organizationId": scope.organization_id,
            "workspaceId": run.workspace_id,
            "systemId": scope.system_id,
            "runId": scope.run_id,
            "envelope": {
                "id": run.envelope_id,
                "hash": run.envelope_hash,
                "nonce": run.envelope_nonce,
            },
            "plan": {
                "id": authority.plan_graph.plan.id,
                "contentHash": authority.plan_graph.plan.plan_content_hash,
                "deliveryMode": authority.plan_graph.plan.delivery_mode,
            },
            "target": {
                "id": authority.plan_graph.target.id,
                "subjectDigest": authority.plan_graph.target.subject_digest,
                "manifestDigest": authority.plan_graph.target.manifest_digest,
            },
            "suite": {
                "executionId": scope.suite_execution_id,
                "versionId": suite.id,
                "ownerScope": current.owner_scope,
                "ordinal": current.ordinal,
                "adapterName": suite.adapter_name,
                "adapterVersion": suite.adapter_version,
                "resultContractVersion": suite.result_contract_version,
            },
            "trustPolicy": {
                "id": authority.plan_graph.trust_policy.id,
                "hash": authority.plan_graph.trust_policy.policy_hash,
                "maximumEvidenceAgeSeconds": authority.maximum_evidence_age_seconds,
                "unsignedImportPolicy": authority.unsigned_import_policy,
            },
            "report": {
                "id": report_id,
                "contentHash": report_content_hash,
                "capturedAt": captured_at.isoformat(),
                "effectiveExpiresAt": effective_expires_at.isoformat(),
                "claimedTechnicalStatus": technical_status,
                "claimedEvidenceResultStatus": evidence_result_status,
                "claimedResultSummary": dict(summary_value),
                "artifactRefs": payload_data["artifactRefs"],
                "limitations": payload_data["limitations"],
            },
        }
        _safe_json(
            snapshot,
            code="imported_evidence_snapshot_invalid",
            maximum_bytes=_MAX_RESULT_SUMMARY_BYTES + _MAX_ARTIFACT_BYTES + _MAX_LIMITATIONS_BYTES + 32 * 1024,
            validate_values=False,
        )
        import_snapshot = FrozenJsonObject.from_mapping(snapshot)
        import_snapshot_hash = canonical_sha256(import_snapshot.to_dict())
        persist_command = PersistUnverifiedImportedEvidenceCommand(
            scope=scope,
            actor_id=actor_id,
            evidence_run_id=evidence_run_id,
            passport_revision_id=passport_revision_id,
            passport_id=passport_id,
            admission_id=admission_id,
            nonce_claim_id=nonce_claim_id,
            suite_evidence_link_id=suite_evidence_link_id,
            authority=authority,
            report_id=report_id,
            report_content_hash=report_content_hash,
            import_snapshot=import_snapshot,
            import_snapshot_hash=import_snapshot_hash,
            technical_status=technical_status,
            evidence_result_status=evidence_result_status,
            result_summary=FrozenJsonObject.from_mapping(dict(summary_value)),
            artifact_refs=artifact_refs,
            limitations=limitations,
            captured_at=captured_at,
            effective_expires_at=effective_expires_at,
            imported_at=imported_at,
            evidence_created_at=imported_at,
            revision_created_at=imported_at,
            suite_started_at=suite_started_at,
            suite_completed_at=suite_completed_at,
            run_technical_status=run_technical_status,
            run_evidence_outcome=run_evidence_outcome,
            run_started_at=run_started_at,
            run_completed_at=run_completed_at,
        )
        record = self._repository.persist_unverified_imported_evidence(persist_command)
        self._repository.force_evidence_admission_constraints()
        _assert_record(record, persist_command)
        body = {
            "admissionId": record.admission_id,
            "evidenceRunId": record.evidence_run_id,
            "passportRevisionId": record.passport_revision_id,
            "nonceClaimId": record.nonce_claim_id,
            "suiteEvidenceLinkId": record.suite_evidence_link_id,
            "runId": record.run_id,
            "suiteExecutionId": record.suite_execution_id,
            "reportContentHash": record.report_content_hash,
            "importSnapshotHash": record.import_snapshot_hash,
            "resultAuthority": "claimed",
            "humanReviewOnly": True,
            "decisionEvidenceEligible": False,
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
            "importedAt": record.imported_at.isoformat(),
        }
        audit_details = {
            "schemaVersion": _AUDIT_SCHEMA,
            "runId": record.run_id,
            "suiteExecutionId": record.suite_execution_id,
            "admissionId": record.admission_id,
            "evidenceRunId": record.evidence_run_id,
            "passportRevisionId": record.passport_revision_id,
            "nonceClaimId": record.nonce_claim_id,
            "suiteEvidenceLinkId": record.suite_evidence_link_id,
            "reportContentHash": record.report_content_hash,
            "importSnapshotHash": record.import_snapshot_hash,
            "resultAuthority": "claimed",
            "humanReviewOnly": True,
            "decisionEvidenceEligible": False,
            "technicalStatus": record.technical_status,
            "evidenceResultStatus": record.evidence_result_status,
            "admissionStatus": record.admission_status,
            "reviewStatus": record.review_status,
            "freshnessStatus": record.freshness_status,
            "runTechnicalStatus": record.run_technical_status,
            "runEvidenceOutcome": record.run_evidence_outcome,
        }
        return MutationOutcome(
            body=FrozenJsonObject.from_mapping(body),
            status=201,
            resource_type="evidence_admission",
            resource_id=record.admission_id,
            audit_action="evaluation_v2.evidence.unverified_imported",
            audit_details=FrozenJsonObject.from_mapping(audit_details),
        )


__all__ = ["ImportedEvidenceService"]
