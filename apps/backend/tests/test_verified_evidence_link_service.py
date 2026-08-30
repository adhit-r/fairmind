"""Independent verified-evidence linking is one exact audited mutation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationResult,
    SuiteExecutionRecord,
)
from src.application.ports.evidence_link import EvidenceLinkScope
from src.application.services.verified_evidence_link_service import (
    VerifiedEvidenceLinkService,
)

UTC = timezone.utc
REQUESTED_AT = datetime(2026, 8, 8, 8, 0, tzinfo=UTC)
LINKED_AT = REQUESTED_AT + timedelta(minutes=5)
SCOPE = EvidenceLinkScope(
    organization_id="org-a",
    system_id="system-a",
    run_id="run-a",
    suite_execution_id="suite-execution-a",
    admission_id="admission-a",
    passport_revision_id="passport-revision-a",
)


def _execution() -> SuiteExecutionRecord:
    return SuiteExecutionRecord(
        id=SCOPE.suite_execution_id,
        suite_version_id="suite-version-a",
        owner_scope="org-a",
        ordinal=0,
        technical_status="awaiting_evidence",
        evidence_result_status="pending",
        admission_status="pending",
        review_status="pending",
        freshness_status="current",
        evidence_run_id=None,
        passport_revision_id=None,
        linked_by=None,
        linked_at=None,
        result_summary=None,
        limitations=None,
        failure_code=None,
        failure_message=None,
        started_at=None,
        completed_at=None,
        created_at=REQUESTED_AT.isoformat(),
        updated_at=(REQUESTED_AT + timedelta(minutes=1)).isoformat(),
    )


def _authority(*, expires_at: datetime | None = None):
    execution = _execution()
    run = SimpleNamespace(
        id=SCOPE.run_id,
        organization_id=SCOPE.organization_id,
        workspace_id="workspace-a",
        system_id=SCOPE.system_id,
        technical_status="awaiting_evidence",
        evidence_outcome="pending",
        overall_verdict="insufficient",
        verdict_version=0,
        suite_executions=(execution,),
        started_at=None,
        completed_at=None,
        created_at=REQUESTED_AT.isoformat(),
        updated_at=(REQUESTED_AT + timedelta(minutes=1)).isoformat(),
    )
    return SimpleNamespace(
        scope=SCOPE,
        run=run,
        evidence_run_id="evidence-run-a",
        verification_receipt_id="receipt-a",
        nonce_claim_id="nonce-claim-a",
        passport_content_hash="a" * 64,
        passport_snapshot=FrozenJsonObject.from_mapping(
            {
                "result": {
                    "technicalStatus": "succeeded",
                    "evidenceResultStatus": "failed",
                    "summary": {"caseCount": 20},
                },
                "limitations": ["One provider feature is unavailable."],
            }
        ),
        admission_status="verified",
        freshness_status="current",
        submitted_by="submitter-a",
        effective_expires_at=expires_at or REQUESTED_AT + timedelta(hours=1),
        verified_at=REQUESTED_AT + timedelta(minutes=4),
        evaluator_registration_id="registration-a",
        evaluator_registration_binding_hash="b" * 64,
    )


class SequentialUuidFactory:
    def __init__(self) -> None:
        self.value = 100

    def __call__(self):
        self.value += 1
        return UUID(int=self.value)


class FakeRepository:
    def __init__(self, authority) -> None:
        self.authority = authority
        self.loaded = []
        self.persisted = []

    def load_verified_evidence_link_authority_for_update(self, *, scope):
        self.loaded.append(scope)
        return self.authority

    def persist_verified_evidence_link(self, command):
        self.persisted.append(command)
        authority = command.authority
        return SimpleNamespace(
            organization_id=command.scope.organization_id,
            workspace_id=authority.run.workspace_id,
            system_id=command.scope.system_id,
            run_id=command.scope.run_id,
            suite_execution_id=command.scope.suite_execution_id,
            admission_id=command.scope.admission_id,
            evidence_run_id=authority.evidence_run_id,
            passport_revision_id=command.scope.passport_revision_id,
            suite_evidence_link_id=command.suite_evidence_link_id,
            technical_status=command.technical_status,
            evidence_result_status=command.evidence_result_status,
            admission_status="verified",
            review_status="pending",
            freshness_status="current",
            run_technical_status=command.run_technical_status,
            run_evidence_outcome=command.run_evidence_outcome,
            overall_verdict=authority.run.overall_verdict,
            verdict_version=authority.run.verdict_version,
            linked_by=command.actor_id,
            linked_at=command.linked_at,
        )


class FakeUnitOfWork:
    def __init__(self, repository: FakeRepository) -> None:
        self.repository = repository
        self.command = None
        self.outcome = None
        self.rejections = []

    def mutate(self, command, callback):
        self.command = command
        try:
            self.outcome = callback(LINKED_AT)
        except EvaluationWorkbenchError as error:
            self.rejections.append(error)
            raise
        return MutationResult.create(
            body=self.outcome.body.to_dict(),
            status=self.outcome.status,
        )


def _service(authority=None):
    repository = FakeRepository(_authority() if authority is None else authority)
    unit_of_work = FakeUnitOfWork(repository)
    service = VerifiedEvidenceLinkService(
        unit_of_work,
        uuid_factory=SequentialUuidFactory(),
    )
    return service, unit_of_work, repository


def test_link_projects_only_the_exact_persisted_verified_submission() -> None:
    service, unit_of_work, repository = _service()

    result = service.link_verified_evidence(
        scope=SCOPE,
        actor_id="linker-a",
        idempotency_key="link-key-a",
    )

    assert result.status == 201
    assert result.body == {
        "admissionId": SCOPE.admission_id,
        "evidenceRunId": "evidence-run-a",
        "passportRevisionId": SCOPE.passport_revision_id,
        "suiteEvidenceLinkId": str(UUID(int=101)),
        "runId": SCOPE.run_id,
        "suiteExecutionId": SCOPE.suite_execution_id,
        "technicalStatus": "succeeded",
        "evidenceResultStatus": "failed",
        "admissionStatus": "verified",
        "reviewStatus": "pending",
        "freshnessStatus": "current",
        "runTechnicalStatus": "succeeded",
        "runEvidenceOutcome": "failed",
        "overallVerdict": "insufficient",
        "verdictVersion": 0,
        "linkedBy": "linker-a",
        "linkedAt": LINKED_AT.isoformat(),
    }
    assert repository.loaded == [SCOPE]
    command = repository.persisted[0]
    assert command.result_summary.to_dict() == {"caseCount": 20}
    assert command.limitations == ("One provider feature is unavailable.",)
    assert command.suite_started_at == LINKED_AT
    assert command.suite_completed_at == LINKED_AT
    assert unit_of_work.command.operation == "evaluation-v2.evidence.verified-link"
    assert unit_of_work.outcome.audit_action == "evaluation_v2.evidence.verified_linked"
    assert unit_of_work.outcome.audit_details.to_dict()["submittedBy"] == "submitter-a"
    assert unit_of_work.outcome.audit_details.to_dict()["linkedBy"] == "linker-a"


def test_link_fails_closed_when_exact_submission_is_missing() -> None:
    service, unit_of_work, repository = _service(authority=False)
    repository.authority = None

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.link_verified_evidence(
            scope=SCOPE,
            actor_id="linker-a",
            idempotency_key="link-missing-a",
        )

    assert caught.value.code == "verified_evidence_link_not_found"
    assert caught.value.status_code == 404
    assert repository.persisted == []
    assert unit_of_work.rejections == [caught.value]


def test_link_rechecks_expiry_at_database_mutation_time() -> None:
    service, unit_of_work, repository = _service(
        authority=_authority(expires_at=LINKED_AT),
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.link_verified_evidence(
            scope=SCOPE,
            actor_id="linker-a",
            idempotency_key="link-expired-a",
        )

    assert caught.value.code == "verified_evidence_link_ineligible"
    assert repository.persisted == []
    assert unit_of_work.rejections == [caught.value]
