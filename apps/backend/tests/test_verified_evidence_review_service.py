"""Four-eyes review is distinct from evidence admission and governance decisions."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationOutcome,
    MutationResult,
)
from src.application.ports.evidence_review import (
    EvidenceReviewAuthorityRecord,
    EvidenceReviewScope,
    ReviewedEvidenceRecord,
)
from src.application.services.verified_evidence_review_service import (
    VerifiedEvidenceReviewService,
)
from src.domain.assurance.evaluation_v2 import canonical_sha256

UTC = timezone.utc
NOW = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)
SCOPE = EvidenceReviewScope(
    organization_id="org-a",
    workspace_id="workspace-a",
    system_id="system-a",
    run_id="run-a",
    suite_execution_id="suite-execution-a",
    admission_id="admission-a",
    passport_revision_id="passport-revision-a",
)


def _authority(**changes: object) -> EvidenceReviewAuthorityRecord:
    values: dict[str, object] = {
        "scope": SCOPE,
        "evidence_run_id": "evidence-run-a",
        "admission_contract_version": "2.0.0",
        "admission_status": "verified",
        "freshness_status": "current",
        "review_status": "pending",
        "current_review_version": 0,
        "submitted_by": "submitter-a",
        "linked_by": "linker-a",
        "run_requested_by": "requester-a",
        "effective_expires_at": NOW + timedelta(hours=1),
        "trust_policy_status": "active",
        "issuer_status": "active",
        "key_valid_from": NOW - timedelta(hours=1),
        "key_valid_until": NOW + timedelta(hours=1),
        "key_revoked_at": None,
        "technical_status": "succeeded",
        "evidence_result_status": "failed",
        "run_technical_status": "succeeded",
        "run_evidence_outcome": "failed",
        "governance_decision_exists": False,
    }
    values.update(changes)
    return EvidenceReviewAuthorityRecord(**values)


@dataclass
class _FakeRepository:
    authority: EvidenceReviewAuthorityRecord

    def __post_init__(self) -> None:
        self.persisted: list[object] = []

    def read_fresh_utc_now(self) -> datetime:
        return NOW

    def load_evidence_review_authority_for_update(self, *, scope: EvidenceReviewScope):
        return self.authority if scope == self.authority.scope else None

    def persist_evidence_review(self, command):
        self.persisted.append(command)
        return ReviewedEvidenceRecord(
            review_id=command.review_id,
            organization_id=command.scope.organization_id,
            workspace_id=command.scope.workspace_id,
            system_id=command.scope.system_id,
            run_id=command.scope.run_id,
            suite_execution_id=command.scope.suite_execution_id,
            admission_id=command.scope.admission_id,
            passport_revision_id=command.scope.passport_revision_id,
            evidence_run_id=command.authority.evidence_run_id,
            decision=command.decision,
            rationale=command.rationale,
            review_version=command.next_review_version,
            reviewed_by=command.actor_id,
            reviewed_at=command.reviewed_at,
            admission_status="verified",
            review_status=command.decision,
            freshness_status="current",
            technical_status=command.authority.technical_status,
            evidence_result_status=command.authority.evidence_result_status,
            run_technical_status=command.authority.run_technical_status,
            run_evidence_outcome=command.authority.run_evidence_outcome,
        )


@dataclass
class _FakeUnitOfWork:
    repository: _FakeRepository

    def __post_init__(self) -> None:
        self.command = None
        self.outcome = None

    def mutate(self, command, callback):
        self.command = command
        self.outcome = callback(NOW)
        return MutationResult.create(body=self.outcome.body.to_dict(), status=self.outcome.status)


def _service(*, authority: EvidenceReviewAuthorityRecord | None = None):
    repository = _FakeRepository(authority or _authority())
    unit_of_work = _FakeUnitOfWork(repository)
    return (
        VerifiedEvidenceReviewService(unit_of_work, uuid_factory=uuid.uuid4),
        unit_of_work,
        repository,
    )


@pytest.mark.parametrize("decision", ("accepted", "rejected"))
def test_review_persists_an_independent_transition_without_a_governance_verdict(
    decision: str,
) -> None:
    service, unit_of_work, repository = _service()

    result = service.review_verified_evidence(
        scope=SCOPE,
        actor_id="reviewer-a",
        idempotency_key=f"review-{decision}",
        decision=decision,
        rationale="Independent evidence review completed.",
        expected_review_version=0,
    )

    assert result.status == 201
    assert result.body == {
        "reviewId": repository.persisted[0].review_id,
        "admissionId": SCOPE.admission_id,
        "passportRevisionId": SCOPE.passport_revision_id,
        "runId": SCOPE.run_id,
        "suiteExecutionId": SCOPE.suite_execution_id,
        "decision": decision,
        "rationale": "Independent evidence review completed.",
        "reviewVersion": 1,
        "reviewedBy": "reviewer-a",
        "reviewedAt": NOW.isoformat(),
        "admissionStatus": "verified",
        "reviewStatus": decision,
        "freshnessStatus": "current",
        "technicalStatus": "succeeded",
        "evidenceResultStatus": "failed",
        "runTechnicalStatus": "succeeded",
        "runEvidenceOutcome": "failed",
    }
    assert "overallVerdict" not in result.body
    assert "verdictVersion" not in result.body
    assert unit_of_work.command.operation == "evaluation-v2.evidence.review"
    assert unit_of_work.command.request_hash == canonical_sha256(
        {
            "method": "POST",
            "operation": "evaluation-v2.evidence.review",
            "scope": {
                "organizationId": "org-a",
                "workspaceId": "workspace-a",
                "systemId": "system-a",
                "runId": "run-a",
                "suiteExecutionId": "suite-execution-a",
                "admissionId": "admission-a",
                "passportRevisionId": "passport-revision-a",
            },
            "body": {
                "decision": decision,
                "rationale": "Independent evidence review completed.",
                "expectedReviewVersion": 0,
            },
        }
    )
    assert unit_of_work.outcome == MutationOutcome(
        body=FrozenJsonObject.from_mapping(result.body),
        status=201,
        resource_type="evaluation_evidence_review",
        resource_id=repository.persisted[0].review_id,
        audit_action="evaluation_v2.evidence.reviewed",
        audit_details=FrozenJsonObject.from_mapping(
            {
                "schemaVersion": "evaluation-v2.verified-evidence-review/v1",
                "runId": "run-a",
                "suiteExecutionId": "suite-execution-a",
                "admissionId": "admission-a",
                "passportRevisionId": "passport-revision-a",
                "evidenceRunId": "evidence-run-a",
                "decision": decision,
                "reviewVersion": 1,
                "rationaleHash": canonical_sha256(
                    {"rationale": "Independent evidence review completed."}
                ),
                "admissionStatus": "verified",
                "reviewStatus": decision,
                "freshnessStatus": "current",
                "technicalStatus": "succeeded",
                "evidenceResultStatus": "failed",
            }
        ),
    )


@pytest.mark.parametrize("actor_id", ("submitter-a", "linker-a", "requester-a"))
def test_review_rejects_submitter_linker_and_run_requester(actor_id: str) -> None:
    service, _unit_of_work, repository = _service()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.review_verified_evidence(
            scope=SCOPE,
            actor_id=actor_id,
            idempotency_key=f"separation-{actor_id}",
            decision="accepted",
            rationale="Independent evidence review completed.",
            expected_review_version=0,
        )

    assert caught.value.code == "evidence_review_separation_required"
    assert caught.value.status_code == 409
    assert repository.persisted == []


@pytest.mark.parametrize(
    ("authority", "expected_review_version", "expected_code"),
    (
        (_authority(admission_status="unverified"), 0, "evidence_review_admission_not_verified"),
        (_authority(freshness_status="stale"), 0, "evidence_review_evidence_not_current"),
        (
            _authority(review_status="accepted", current_review_version=1),
            1,
            "evidence_review_not_pending",
        ),
        (_authority(current_review_version=0), 1, "evidence_review_version_conflict"),
        (_authority(governance_decision_exists=True), 0, "evidence_review_frozen"),
        (_authority(effective_expires_at=NOW), 0, "evidence_review_evidence_expired"),
        (_authority(trust_policy_status="superseded"), 0, "evidence_review_trust_policy_inactive"),
        (_authority(issuer_status="revoked"), 0, "evidence_review_issuer_inactive"),
        (
            _authority(key_revoked_at=NOW - timedelta(seconds=1)),
            0,
            "evidence_review_signing_key_revoked",
        ),
        (_authority(key_valid_until=NOW), 0, "evidence_review_signing_key_inactive"),
    ),
)
def test_review_rejects_noncurrent_or_stale_compare_and_swap_state(
    authority: EvidenceReviewAuthorityRecord,
    expected_review_version: int,
    expected_code: str,
) -> None:
    service, _unit_of_work, repository = _service(authority=authority)

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.review_verified_evidence(
            scope=SCOPE,
            actor_id="reviewer-a",
            idempotency_key=f"state-{expected_code}",
            decision="accepted",
            rationale="Independent evidence review completed.",
            expected_review_version=expected_review_version,
        )

    assert caught.value.code == expected_code
    assert repository.persisted == []
