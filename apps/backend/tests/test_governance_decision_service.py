"""Governance decisions are immutable CAS mutations over server-owned evidence."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    MutationResult,
)
from src.application.ports.governance_decision import (
    GovernanceDecisionAuthorityRecord,
    GovernanceDecisionRecord,
    GovernanceDecisionScope,
)
from src.application.ports.evidence_freshness import EvidenceFreshnessClassification
from src.application.services.governance_decision_service import GovernanceDecisionService

UTC = timezone.utc
NOW = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)
DECISION_ID = UUID("11111111-1111-4111-8111-111111111111")
HASH_A = "a" * 64
HASH_B = "b" * 64
EVIDENCE_SET_HASH = "f7294527727d1c756664b89154efac6a18413586d048622629b9e23e149b29cc"
SCOPE = GovernanceDecisionScope(
    organization_id="org-a",
    workspace_id="workspace-a",
    system_id="system-a",
    run_id="run-a",
)
LAYERS = {
    "suites": {"suite-execution-a": "conditional"},
    "modalities": {},
    "components": {},
    "riskDimensions": {},
}
EVIDENCE_SET = {
    "target": {
        "manifestDigest": HASH_B,
        "subjectDigest": HASH_A,
        "targetVersionId": "target-a",
    },
    "suites": [
        {
            "admissionId": "admission-a",
            "evidenceContentHash": HASH_B,
            "evidenceRunId": "evidence-run-a",
            "linkId": "link-a",
            "nonceClaimId": "claim-a",
            "passportContentHash": HASH_A,
            "passportRevisionId": "passport-revision-a",
            "reviewId": "review-a",
            "reviewVersion": 1,
            "suiteExecutionId": "suite-execution-a",
            "suiteManifestDigest": HASH_A,
            "suiteRunnerImageDigest": None,
            "suiteVersionId": "suite-a",
        }
    ],
}


def _authority() -> GovernanceDecisionAuthorityRecord:
    return GovernanceDecisionAuthorityRecord.create(
        scope=SCOPE,
        run_contract_version="2.0.0",
        envelope_id="envelope-a",
        envelope_hash=HASH_A,
        technical_status="succeeded",
        current_verdict_version=0,
        current_overall_verdict="review",
        current_layer_verdicts={
            "suites": {"suite-execution-a": "review"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        requested_by="requester-a",
        evidence_submitters=("submitter-a",),
        suite_execution_ids=("suite-execution-a",),
        admission_ids=("admission-a",),
        evidence_set=EVIDENCE_SET,
        evidence_set_hash=EVIDENCE_SET_HASH,
        operational_freshness=(
            EvidenceFreshnessClassification(
                classification_status="ok",
                freshness_contract_version="1.0.0",
                recorded_freshness_status="current",
                effective_freshness_status="current",
                evaluated_at=NOW,
                effective_at=NOW,
                expiring_at=NOW + timedelta(hours=1),
                reason_codes=(),
                decision_eligible=True,
            ),
        ),
    )


@dataclass
class _FakeRepository:
    authority: GovernanceDecisionAuthorityRecord
    owner_authorized: bool = False

    def __post_init__(self) -> None:
        self.persisted: list[object] = []
        self.owner_authorization_calls: list[tuple[str, str]] = []

    def read_fresh_utc_now(self) -> datetime:
        return NOW

    def load_governance_decision_authority_for_update(self, *, scope):
        return self.authority if scope == self.authority.scope else None

    def authorize_owner_decision_override_for_update(
        self, *, organization_id: str, actor_id: str
    ) -> bool:
        self.owner_authorization_calls.append((organization_id, actor_id))
        return self.owner_authorized

    def persist_governance_decision(self, command):
        self.persisted.append(command)
        decided_at = getattr(self, "returned_decided_at", command.decided_at)
        operational_freshness = getattr(
            self,
            "returned_operational_freshness",
            command.authority.operational_freshness,
        )
        record = GovernanceDecisionRecord.create(
            decision_id=command.decision_id,
            scope=command.scope,
            run_contract_version=command.authority.run_contract_version,
            envelope_id=command.authority.envelope_id,
            envelope_hash=command.authority.envelope_hash,
            verdict_version=command.next_verdict_version,
            overall_verdict=command.overall_verdict,
            layer_verdicts=command.layer_verdicts.to_dict(),
            rationale=command.rationale,
            decided_by=command.actor_id,
            evidence_set_hash=command.authority.evidence_set_hash,
            decided_at=decided_at,
            suite_execution_ids=command.authority.suite_execution_ids,
            operational_freshness=operational_freshness,
        )
        if command.owner_override_reason is None:
            return record
        return replace(record, owner_override_reason=command.owner_override_reason)


@dataclass
class _FakeUnitOfWork:
    repository: _FakeRepository

    def mutate(self, command, callback):
        self.command = command
        self.outcome = callback(NOW)
        return MutationResult.create(body=self.outcome.body.to_dict(), status=self.outcome.status)


def test_decision_appends_server_bound_record_and_advances_expected_version() -> None:
    repository = _FakeRepository(_authority())
    unit_of_work = _FakeUnitOfWork(repository)
    service = GovernanceDecisionService(unit_of_work, uuid_factory=lambda: DECISION_ID)

    result = service.decide(
        scope=SCOPE,
        actor_id="decider-a",
        idempotency_key="decision-key",
        expected_verdict_version=0,
        overall_verdict="conditional",
        layer_verdicts=LAYERS,
        rationale="Current reviewed evidence supports conditional approval.",
    )

    assert result.status == 201
    assert result.body == {
        "decisionId": str(DECISION_ID),
        "runId": "run-a",
        "contractVersion": "2.0.0",
        "verdictVersion": 1,
        "overallVerdict": "conditional",
        "layerVerdictsSchemaVersion": "1.0.0",
        "layerVerdicts": LAYERS,
        "rationale": "Current reviewed evidence supports conditional approval.",
        "decidedBy": "decider-a",
        "evidenceSetHash": EVIDENCE_SET_HASH,
        "decidedAt": NOW.isoformat(),
        "freshnessContractVersion": "1.0.0",
        "freshnessEvaluatedAt": NOW.isoformat(),
        "decisionEvidenceEligibleAtDecision": True,
        "suiteFreshness": [
            {
                "suiteExecutionId": "suite-execution-a",
                "recordedFreshnessStatus": "current",
                "effectiveFreshnessStatus": "current",
                "freshnessEffectiveAt": NOW.isoformat(),
                "expiringAt": (NOW + timedelta(hours=1)).isoformat(),
                "freshnessReasonCodes": [],
                "decisionEvidenceEligibleAtDecision": True,
            }
        ],
    }
    persisted = repository.persisted[0]
    assert persisted.expected_verdict_version == 0
    assert persisted.next_verdict_version == 1
    assert persisted.authority.evidence_set.to_dict() == EVIDENCE_SET
    assert persisted.owner_override_reason is None
    assert "ownerOverrideApplied" not in result.body
    assert unit_of_work.command.operation == "evaluation-v2.governance-decision.create"
    assert unit_of_work.outcome.audit_action == "evaluation_v2.governance_decision.created"
    assert repository.owner_authorization_calls == []


def test_owner_override_records_exact_waived_relationships_without_raw_reason() -> None:
    repository = _FakeRepository(
        replace(
            _authority(),
            requested_by="owner-a",
            evidence_submitters=("owner-a",),
            admission_submitters=("owner-a",),
        ),
        owner_authorized=True,
    )
    unit_of_work = _FakeUnitOfWork(repository)
    service = GovernanceDecisionService(unit_of_work, uuid_factory=lambda: DECISION_ID)

    result = service.decide_owner_override(
        scope=SCOPE,
        actor_id="owner-a",
        idempotency_key="owner-override-key",
        expected_verdict_version=0,
        overall_verdict="conditional",
        layer_verdicts=LAYERS,
        rationale="Current evidence supports a conditional verdict.",
        owner_override_reason="No independent decision owner is available.",
    )

    assert result.status == 201
    assert result.body["ownerOverrideApplied"] is True
    assert "ownerOverrideReason" not in result.body
    assert unit_of_work.command.operation == (
        "evaluation-v2.governance-decision.owner-override"
    )
    assert unit_of_work.outcome.audit_action == (
        "evaluation_v2.governance_decision.owner_override_created"
    )
    details = unit_of_work.outcome.audit_details.to_dict()
    assert details["waivedRelationships"] == [
        {
            "relationshipType": "evidence_submitter",
            "actorId": "owner-a",
            "resourceType": "evidence_admission",
            "resourceIds": ["admission-a"],
        },
        {
            "relationshipType": "run_requester",
            "actorId": "owner-a",
            "resourceType": "evaluation_run",
            "resourceIds": ["run-a"],
        },
    ]
    assert "No independent decision owner" not in repr(details)
    assert repository.persisted[0].owner_override_reason == (
        "No independent decision owner is available."
    )


@pytest.mark.parametrize(
    ("owner_authorized", "actor_id", "expected_code"),
    (
        (False, "owner-a", "evaluation_separation_override_forbidden"),
        (True, "independent-owner", "governance_decision_override_not_required"),
    ),
)
def test_owner_override_requires_canonical_authority_and_a_real_conflict(
    owner_authorized: bool,
    actor_id: str,
    expected_code: str,
) -> None:
    authority = _authority()
    if owner_authorized:
        authority = replace(authority, admission_submitters=("submitter-a",))
    repository = _FakeRepository(authority, owner_authorized=owner_authorized)
    service = GovernanceDecisionService(
        _FakeUnitOfWork(repository), uuid_factory=lambda: DECISION_ID
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.decide_owner_override(
            scope=SCOPE,
            actor_id=actor_id,
            idempotency_key=f"owner-override-{expected_code}",
            expected_verdict_version=0,
            overall_verdict="conditional",
            layer_verdicts=LAYERS,
            rationale="Evidence remains authoritative.",
            owner_override_reason="Documented ownership conflict.",
        )

    assert caught.value.code == expected_code
    assert repository.persisted == []


def test_owner_override_fails_closed_without_aligned_admission_provenance() -> None:
    repository = _FakeRepository(
        replace(
            _authority(),
            requested_by="owner-a",
            evidence_submitters=("owner-a",),
        ),
        owner_authorized=True,
    )
    service = GovernanceDecisionService(
        _FakeUnitOfWork(repository), uuid_factory=lambda: DECISION_ID
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.decide_owner_override(
            scope=SCOPE,
            actor_id="owner-a",
            idempotency_key="owner-override-missing-admission-provenance",
            expected_verdict_version=0,
            overall_verdict="conditional",
            layer_verdicts=LAYERS,
            rationale="Evidence remains authoritative.",
            owner_override_reason="Documented ownership conflict.",
        )

    assert caught.value.code == "governance_decision_integrity_conflict"
    assert repository.persisted == []


def test_decision_rejects_classifier_result_from_a_different_database_instant() -> None:
    repository = _FakeRepository(_authority())
    repository.returned_decided_at = NOW
    repository.returned_operational_freshness = (
        replace(
            _authority().operational_freshness[0],
            evaluated_at=NOW.replace(microsecond=1),
        ),
    )
    service = GovernanceDecisionService(
        _FakeUnitOfWork(repository), uuid_factory=lambda: DECISION_ID
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.decide(
            scope=SCOPE,
            actor_id="decider-a",
            idempotency_key="decision-wrong-evaluated-at",
            expected_verdict_version=0,
            overall_verdict="conditional",
            layer_verdicts=LAYERS,
            rationale="Must share the database-owned decision instant.",
        )

    assert caught.value.code == "governance_decision_integrity_conflict"
    assert len(repository.persisted) == 1


@pytest.mark.parametrize(
    ("axis", "claim"),
    (
        ("modalities", {"video": "approved"}),
        ("components", {"tool-router": "conditional"}),
        ("riskDimensions", {"safety": "approved"}),
    ),
)
def test_decision_rejects_non_suite_claims_without_registered_pack_authority(
    axis: str,
    claim: dict[str, str],
) -> None:
    repository = _FakeRepository(_authority())
    service = GovernanceDecisionService(
        _FakeUnitOfWork(repository),
        uuid_factory=lambda: DECISION_ID,
    )
    layers = {
        "suites": {"suite-execution-a": "conditional"},
        "modalities": {},
        "components": {},
        "riskDimensions": {},
    }
    layers[axis] = claim

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.decide(
            scope=SCOPE,
            actor_id="decider-a",
            idempotency_key=f"decision-unsupported-{axis}",
            expected_verdict_version=0,
            overall_verdict="conditional",
            layer_verdicts=layers,
            rationale="Only evidence-bound suite claims are currently supported.",
        )

    assert caught.value.code == "governance_decision_layer_axis_unsupported"
    assert repository.persisted == []


@pytest.mark.parametrize(
    ("authority", "actor_id", "expected_version", "layers", "expected_code"),
    (
        (
            _authority(),
            "requester-a",
            0,
            LAYERS,
            "governance_decision_separation_required",
        ),
        (
            _authority(),
            "submitter-a",
            0,
            LAYERS,
            "governance_decision_separation_required",
        ),
        (
            replace(_authority(), current_verdict_version=1),
            "decider-a",
            0,
            LAYERS,
            "governance_decision_version_conflict",
        ),
        (
            _authority(),
            "decider-a",
            0,
            {
                **LAYERS,
                "suites": {"caller-invented-suite": "conditional"},
            },
            "governance_decision_suite_scope_conflict",
        ),
    ),
)
def test_decision_rejects_non_independent_stale_or_noncanonical_authority(
    authority,
    actor_id: str,
    expected_version: int,
    layers: dict[str, object],
    expected_code: str,
) -> None:
    repository = _FakeRepository(authority)
    service = GovernanceDecisionService(
        _FakeUnitOfWork(repository),
        uuid_factory=lambda: DECISION_ID,
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.decide(
            scope=SCOPE,
            actor_id=actor_id,
            idempotency_key=f"decision-{expected_code}",
            expected_verdict_version=expected_version,
            overall_verdict="conditional",
            layer_verdicts=layers,
            rationale="Decision must remain bound to current independent authority.",
        )

    assert caught.value.code == expected_code
    assert repository.persisted == []
