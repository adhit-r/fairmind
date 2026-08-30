"""Append one normal governance decision through an exact run-version CAS."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Mapping

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationCommand,
    MutationOutcome,
    MutationResult,
)
from src.application.ports.governance_decision import (
    GovernanceDecisionAuthorityRecord,
    GovernanceDecisionRecord,
    GovernanceDecisionScope,
    GovernanceDecisionUnitOfWork,
    PersistGovernanceDecisionCommand,
    UuidFactory,
)
from src.application.evaluation_workbench_contracts import assurance_request_hash
from src.application import evidence_freshness as freshness
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    canonical_sha256,
    validate_owner_override_reason,
    validate_idempotency_key,
    validate_public_safe_string,
)

_OPERATION = "evaluation-v2.governance-decision.create"
_OWNER_OVERRIDE_OPERATION = "evaluation-v2.governance-decision.owner-override"
_AUDIT_SCHEMA = "evaluation-v2.governance-decision/v2"
_OWNER_OVERRIDE_AUDIT_ACTION = (
    "evaluation_v2.governance_decision.owner_override_created"
)
_CONTRACT_VERSION = "2.0.0"
_LAYER_SCHEMA_VERSION = "1.0.0"
_LAYER_AXES = frozenset({"suites", "modalities", "components", "riskDimensions"})
_VERDICTS = frozenset({"approved", "conditional", "review", "blocked", "insufficient"})
_LOWER_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


def _error(code: str, message: str, *, status_code: int = 409) -> EvaluationWorkbenchError:
    return EvaluationWorkbenchError(code, message, status_code=status_code)


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise _error(
            "governance_decision_chronology_invalid",
            "The governance-decision chronology is invalid.",
        )
    return value.astimezone(timezone.utc)


def _safe_uuid(factory: UuidFactory) -> str:
    value = str(factory())
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError) as error:
        raise RuntimeError("The server UUID factory returned an invalid identity.") from error
    if str(parsed) != value:
        raise RuntimeError("The server UUID factory returned a non-canonical identity.")
    return value


def _safe_string(value: object, *, code: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise _error(code, "The governance-decision request is invalid.", status_code=422)
    try:
        validate_public_safe_string(value)
    except AssuranceContractValidationError as error:
        raise _error(
            code, "The governance-decision request is invalid.", status_code=422
        ) from error
    return value.strip()


def _safe_owner_override_reason(value: object) -> str:
    if not isinstance(value, str):
        raise _error(
            "governance_decision_request_invalid",
            "The governance-decision request is invalid.",
            status_code=422,
        )
    try:
        validate_owner_override_reason(value)
    except AssuranceContractValidationError as error:
        raise _error(
            "governance_decision_request_invalid",
            "The governance-decision request is invalid.",
            status_code=422,
        ) from error
    return value.strip()


def _validate_scope(scope: GovernanceDecisionScope) -> None:
    if not isinstance(scope, GovernanceDecisionScope):
        raise _error(
            "governance_decision_scope_invalid",
            "The governance-decision scope is invalid.",
            status_code=422,
        )
    for value in (
        scope.organization_id,
        scope.workspace_id,
        scope.system_id,
        scope.run_id,
    ):
        _safe_string(value, code="governance_decision_scope_invalid", maximum=128)


def _validated_layers(value: object) -> FrozenJsonObject:
    if not isinstance(value, Mapping) or set(value) != _LAYER_AXES:
        raise _error(
            "governance_decision_request_invalid",
            "The governance-decision request is invalid.",
            status_code=422,
        )
    normalized: dict[str, object] = {}
    total = 0
    for axis in ("suites", "modalities", "components", "riskDimensions"):
        entries = value[axis]
        if not isinstance(entries, Mapping):
            raise _error(
                "governance_decision_request_invalid",
                "The governance-decision request is invalid.",
                status_code=422,
            )
        axis_values: dict[str, str] = {}
        for key, verdict in entries.items():
            if not isinstance(key, str) or len(key) > 160 or verdict not in _VERDICTS:
                raise _error(
                    "governance_decision_request_invalid",
                    "The governance-decision request is invalid.",
                    status_code=422,
                )
            _safe_string(key, code="governance_decision_request_invalid", maximum=160)
            axis_values[key] = verdict
            total += 1
        normalized[axis] = axis_values
    if not normalized["suites"] or total > 256:
        raise _error(
            "governance_decision_request_invalid",
            "The governance-decision request is invalid.",
            status_code=422,
        )
    if any(normalized[axis] for axis in ("modalities", "components", "riskDimensions")):
        raise _error(
            "governance_decision_layer_axis_unsupported",
            "Non-suite governance claims require registered capability-pack authority.",
            status_code=422,
        )
    return FrozenJsonObject.from_mapping(normalized)


def _assert_authority(
    *,
    authority: GovernanceDecisionAuthorityRecord,
    scope: GovernanceDecisionScope,
    actor_id: str,
    expected_verdict_version: int,
    layers: FrozenJsonObject,
    require_independent_actor: bool,
) -> None:
    if authority.scope != scope or authority.run_contract_version != _CONTRACT_VERSION:
        raise _error(
            "governance_decision_integrity_conflict",
            "The locked governance-decision authority is inconsistent.",
        )
    if authority.technical_status != "succeeded":
        raise _error(
            "governance_decision_run_not_succeeded",
            "A governance decision requires a succeeded evaluation run.",
        )
    freshness.require_common_evaluated_at(
        authority.operational_freshness
    )
    if len(authority.operational_freshness) != len(authority.suite_execution_ids):
        raise _error(
            "governance_decision_integrity_conflict",
            "The locked governance-decision authority is inconsistent.",
        )
    for classification in authority.operational_freshness:
        freshness.require_decision_eligible(
            classification,
            expected_recorded_status="current",
            error_code="governance_decision_evidence_not_ready",
            error_message="Every suite requires current, accepted, verified evidence.",
        )
    if authority.current_verdict_version != expected_verdict_version:
        raise _error(
            "governance_decision_version_conflict",
            "The governance verdict version is stale.",
        )
    if require_independent_actor and (
        actor_id == authority.requested_by
        or actor_id in authority.evidence_submitters
        or actor_id in authority.evidence_linkers
    ):
        raise _error(
            "governance_decision_separation_required",
            "The decider must be independent from the run requester, evidence submitters, "
            "and evidence linkers.",
        )
    layer_suites = layers.to_dict()["suites"]
    if not isinstance(layer_suites, dict) or set(layer_suites) != set(
        authority.suite_execution_ids
    ):
        raise _error(
            "governance_decision_suite_scope_conflict",
            "The layered verdicts do not match the current run graph.",
        )
    if (
        not authority.suite_execution_ids
        or not _LOWER_HEX_64.fullmatch(authority.envelope_hash)
        or not _LOWER_HEX_64.fullmatch(authority.evidence_set_hash)
        or canonical_sha256(authority.evidence_set.to_dict()) != authority.evidence_set_hash
    ):
        raise _error(
            "governance_decision_integrity_conflict",
            "The locked governance-decision authority is inconsistent.",
        )


def _waived_relationships(
    authority: GovernanceDecisionAuthorityRecord,
    actor_id: str,
) -> list[dict[str, object]]:
    if (
        len(authority.admission_ids) != len(authority.admission_submitters)
        or len(authority.admission_ids) != len(authority.admission_linkers)
    ):
        raise _error(
            "governance_decision_integrity_conflict",
            "The locked governance-decision authority is inconsistent.",
        )
    relationships: list[dict[str, object]] = []
    admission_ids = sorted(
        {
            admission_id
            for admission_id, submitted_by in zip(
                authority.admission_ids,
                authority.admission_submitters,
                strict=True,
            )
            if submitted_by == actor_id
        }
    )
    if admission_ids:
        relationships.append(
            {
                "relationshipType": "evidence_submitter",
                "actorId": actor_id,
                "resourceType": "evidence_admission",
                "resourceIds": admission_ids,
            }
        )
    linked_admission_ids = sorted(
        {
            admission_id
            for admission_id, linked_by in zip(
                authority.admission_ids,
                authority.admission_linkers,
                strict=True,
            )
            if linked_by == actor_id
        }
    )
    if linked_admission_ids:
        relationships.append(
            {
                "relationshipType": "evidence_linker",
                "actorId": actor_id,
                "resourceType": "evidence_admission",
                "resourceIds": linked_admission_ids,
            }
        )
    if authority.requested_by == actor_id:
        relationships.append(
            {
                "relationshipType": "run_requester",
                "actorId": actor_id,
                "resourceType": "evaluation_run",
                "resourceIds": [authority.scope.run_id],
            }
        )
    return sorted(
        relationships,
        key=lambda item: (str(item["relationshipType"]), str(item["actorId"])),
    )


def _suite_freshness(record: GovernanceDecisionRecord) -> list[dict[str, object]]:
    return [
        {
            "suiteExecutionId": suite_execution_id,
            "recordedFreshnessStatus": classification.recorded_freshness_status,
            "effectiveFreshnessStatus": classification.effective_freshness_status,
            "freshnessEffectiveAt": _utc(classification.effective_at).isoformat(),
            "expiringAt": (
                None
                if classification.expiring_at is None
                else _utc(classification.expiring_at).isoformat()
            ),
            "freshnessReasonCodes": list(classification.reason_codes),
            "decisionEvidenceEligibleAtDecision": classification.decision_eligible is True,
        }
        for suite_execution_id, classification in zip(
            record.suite_execution_ids,
            record.operational_freshness,
            strict=True,
        )
    ]


def _body(record: GovernanceDecisionRecord) -> dict[str, object]:
    evaluated_at = freshness.require_common_evaluated_at(
        record.operational_freshness
    )
    if evaluated_at is None or len(record.operational_freshness) == 0:
        raise _error(
            "governance_decision_integrity_conflict",
            "The persisted governance-decision projection is inconsistent.",
        )
    return {
        "decisionId": record.decision_id,
        "runId": record.scope.run_id,
        "contractVersion": record.run_contract_version,
        "verdictVersion": record.verdict_version,
        "overallVerdict": record.overall_verdict,
        "layerVerdictsSchemaVersion": _LAYER_SCHEMA_VERSION,
        "layerVerdicts": record.layer_verdicts.to_dict(),
        "rationale": record.rationale,
        "decidedBy": record.decided_by,
        "evidenceSetHash": record.evidence_set_hash,
        "decidedAt": _utc(record.decided_at).isoformat(),
        "freshnessContractVersion": "1.0.0",
        "freshnessEvaluatedAt": evaluated_at.isoformat(),
        "decisionEvidenceEligibleAtDecision": all(
            classification.decision_eligible is True
            for classification in record.operational_freshness
        ),
        "suiteFreshness": _suite_freshness(record),
    }


def _assert_record(
    record: GovernanceDecisionRecord,
    command: PersistGovernanceDecisionCommand,
) -> None:
    expected = (
        command.decision_id,
        command.scope,
        command.authority.run_contract_version,
        command.authority.envelope_id,
        command.authority.envelope_hash,
        command.next_verdict_version,
        command.overall_verdict,
        command.layer_verdicts,
        command.rationale,
        command.actor_id,
        command.authority.evidence_set_hash,
        command.owner_override_reason,
        command.authority.suite_execution_ids,
    )
    actual = (
        record.decision_id,
        record.scope,
        record.run_contract_version,
        record.envelope_id,
        record.envelope_hash,
        record.verdict_version,
        record.overall_verdict,
        record.layer_verdicts,
        record.rationale,
        record.decided_by,
        record.evidence_set_hash,
        record.owner_override_reason,
        record.suite_execution_ids,
    )
    if actual != expected:
        raise _error(
            "governance_decision_integrity_conflict",
            "The persisted governance-decision projection is inconsistent.",
        )
    decided_at = _utc(record.decided_at)
    classified_at = freshness.require_common_evaluated_at(
        record.operational_freshness
    )
    if (
        classified_at != decided_at
        or len(record.operational_freshness)
        != len(command.authority.suite_execution_ids)
    ):
        raise _error(
            "governance_decision_integrity_conflict",
            "The persisted governance-decision projection is inconsistent.",
        )
    for classification in record.operational_freshness:
        freshness.require_decision_eligible(
            classification,
            expected_recorded_status="current",
            error_code="governance_decision_evidence_not_ready",
            error_message="Every suite requires current, accepted, verified evidence.",
        )


class GovernanceDecisionService:
    """Create normal governance decisions and authorized owner overrides."""

    def __init__(
        self,
        unit_of_work: GovernanceDecisionUnitOfWork,
        *,
        uuid_factory: UuidFactory = uuid.uuid4,
    ) -> None:
        self.unit_of_work = unit_of_work
        self.repository = unit_of_work.repository
        self._uuid_factory = uuid_factory

    def decide(
        self,
        *,
        scope: GovernanceDecisionScope,
        actor_id: str,
        idempotency_key: str,
        expected_verdict_version: int,
        overall_verdict: str,
        layer_verdicts: Mapping[str, object],
        rationale: str,
    ) -> MutationResult:
        return self._decide(
            scope=scope,
            actor_id=actor_id,
            idempotency_key=idempotency_key,
            expected_verdict_version=expected_verdict_version,
            overall_verdict=overall_verdict,
            layer_verdicts=layer_verdicts,
            rationale=rationale,
            owner_override_reason=None,
        )

    def decide_owner_override(
        self,
        *,
        scope: GovernanceDecisionScope,
        actor_id: str,
        idempotency_key: str,
        expected_verdict_version: int,
        overall_verdict: str,
        layer_verdicts: Mapping[str, object],
        rationale: str,
        owner_override_reason: str,
    ) -> MutationResult:
        reason = _safe_owner_override_reason(owner_override_reason)
        return self._decide(
            scope=scope,
            actor_id=actor_id,
            idempotency_key=idempotency_key,
            expected_verdict_version=expected_verdict_version,
            overall_verdict=overall_verdict,
            layer_verdicts=layer_verdicts,
            rationale=rationale,
            owner_override_reason=reason,
        )

    def _decide(
        self,
        *,
        scope: GovernanceDecisionScope,
        actor_id: str,
        idempotency_key: str,
        expected_verdict_version: int,
        overall_verdict: str,
        layer_verdicts: Mapping[str, object],
        rationale: str,
        owner_override_reason: str | None,
    ) -> MutationResult:
        _validate_scope(scope)
        actor = _safe_string(actor_id, code="governance_decision_actor_invalid", maximum=128)
        if (
            isinstance(expected_verdict_version, bool)
            or not isinstance(expected_verdict_version, int)
            or expected_verdict_version < 0
            or overall_verdict not in _VERDICTS
        ):
            raise _error(
                "governance_decision_request_invalid",
                "The governance-decision request is invalid.",
                status_code=422,
            )
        safe_rationale = _safe_string(
            rationale,
            code="governance_decision_request_invalid",
            maximum=4000,
        )
        layers = _validated_layers(layer_verdicts)
        try:
            key = validate_idempotency_key(idempotency_key)
        except AssuranceContractValidationError as error:
            raise _error(
                "invalid_idempotency_key",
                "The Idempotency-Key is invalid.",
                status_code=422,
            ) from error

        operation = (
            _OWNER_OVERRIDE_OPERATION
            if owner_override_reason is not None
            else _OPERATION
        )
        request_body: dict[str, object] = {
            "expectedVerdictVersion": expected_verdict_version,
            "overallVerdict": overall_verdict,
            "layerVerdicts": layers.to_dict(),
            "rationale": safe_rationale,
        }
        if owner_override_reason is not None:
            request_body["ownerOverrideReason"] = owner_override_reason

        mutation = MutationCommand(
            organization_id=scope.organization_id,
            actor_id=actor,
            operation=operation,
            idempotency_key=key,
            request_hash=assurance_request_hash(
                method="POST",
                operation=operation,
                scope={
                    "organizationId": scope.organization_id,
                    "workspaceId": scope.workspace_id,
                    "systemId": scope.system_id,
                    "runId": scope.run_id,
                },
                body=request_body,
            ),
        )

        def persist(_mutation_now: datetime) -> MutationOutcome:
            if owner_override_reason is not None and not (
                self.repository.authorize_owner_decision_override_for_update(
                    organization_id=scope.organization_id,
                    actor_id=actor,
                )
            ):
                raise _error(
                    "evaluation_separation_override_forbidden",
                    "Owner decision override authority is not available.",
                    status_code=403,
                )
            authority = self.repository.load_governance_decision_authority_for_update(scope=scope)
            if authority is None:
                raise _error(
                    "governance_decision_scope_not_found",
                    "The evaluation run was not found in this scope.",
                    status_code=404,
                )
            _assert_authority(
                authority=authority,
                scope=scope,
                actor_id=actor,
                expected_verdict_version=expected_verdict_version,
                layers=layers,
                require_independent_actor=owner_override_reason is None,
            )
            waived_relationships = (
                _waived_relationships(authority, actor)
                if owner_override_reason is not None
                else []
            )
            if owner_override_reason is not None and not waived_relationships:
                raise _error(
                    "governance_decision_override_not_required",
                    "The canonical owner has no decision-separation conflict to override.",
                )
            advisory_evaluated_at = freshness.require_common_evaluated_at(
                authority.operational_freshness
            )
            if advisory_evaluated_at is None:
                raise _error(
                    "governance_decision_integrity_conflict",
                    "The locked governance-decision authority is inconsistent.",
                )
            command = PersistGovernanceDecisionCommand(
                scope=scope,
                authority=authority,
                decision_id=_safe_uuid(self._uuid_factory),
                actor_id=actor,
                expected_verdict_version=expected_verdict_version,
                next_verdict_version=expected_verdict_version + 1,
                overall_verdict=overall_verdict,
                layer_verdicts=layers,
                rationale=safe_rationale,
                owner_override_reason=owner_override_reason,
                decided_at=advisory_evaluated_at,
            )
            record = self.repository.persist_governance_decision(command)
            _assert_record(record, command)
            body = _body(record)
            if owner_override_reason is not None:
                body["ownerOverrideApplied"] = True
            audit_details: dict[str, object] = {
                "schemaVersion": _AUDIT_SCHEMA,
                "runId": scope.run_id,
                "verdictVersion": record.verdict_version,
                "overallVerdict": record.overall_verdict,
                "evidenceSetHash": record.evidence_set_hash,
                "rationaleHash": canonical_sha256({"rationale": safe_rationale}),
                "ownerOverride": owner_override_reason is not None,
                "freshnessContractVersion": "1.0.0",
                "freshnessEvaluatedAt": _utc(record.decided_at).isoformat(),
                "suiteFreshness": body["suiteFreshness"],
                "freshnessReasonCodesHash": canonical_sha256(
                    [
                        list(classification.reason_codes)
                        for classification in record.operational_freshness
                    ]
                ),
                "decisionEvidenceEligibleAtDecision": body[
                    "decisionEvidenceEligibleAtDecision"
                ],
            }
            if owner_override_reason is not None:
                audit_details.update(
                    {
                        "ownerActorId": actor,
                        "waivedRelationships": waived_relationships,
                        "waivedRelationshipsHash": canonical_sha256(waived_relationships),
                        "ownerOverrideReasonHash": canonical_sha256(
                            {"ownerOverrideReason": owner_override_reason}
                        ),
                    }
                )
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(body),
                status=201,
                resource_type="evaluation_governance_decision",
                resource_id=record.decision_id,
                audit_action=(
                    _OWNER_OVERRIDE_AUDIT_ACTION
                    if owner_override_reason is not None
                    else "evaluation_v2.governance_decision.created"
                ),
                audit_details=FrozenJsonObject.from_mapping(audit_details),
            )

        return self.unit_of_work.mutate(mutation, persist)


__all__ = ["GovernanceDecisionService"]
