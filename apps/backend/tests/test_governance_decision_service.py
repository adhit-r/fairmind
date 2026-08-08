"""Governance decisions are immutable CAS mutations over server-owned evidence."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
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
    "modalities": {"predictive_model": "conditional"},
    "components": {},
    "riskDimensions": {"fairness": "conditional"},
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
        evidence_set=EVIDENCE_SET,
        evidence_set_hash=EVIDENCE_SET_HASH,
    )


@dataclass
class _FakeRepository:
    authority: GovernanceDecisionAuthorityRecord

    def __post_init__(self) -> None:
        self.persisted: list[object] = []

    def read_fresh_utc_now(self) -> datetime:
        return NOW

    def load_governance_decision_authority_for_update(self, *, scope):
        return self.authority if scope == self.authority.scope else None

    def persist_governance_decision(self, command):
        self.persisted.append(command)
        return GovernanceDecisionRecord.create(
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
            decided_at=command.decided_at,
        )


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
    }
    persisted = repository.persisted[0]
    assert persisted.expected_verdict_version == 0
    assert persisted.next_verdict_version == 1
    assert persisted.authority.evidence_set.to_dict() == EVIDENCE_SET
    assert persisted.owner_override_reason is None


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
