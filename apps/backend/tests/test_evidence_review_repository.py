"""Transactional persistence tests for four-eyes verified-evidence review."""

from __future__ import annotations

from dataclasses import replace

import pytest
from sqlalchemy import func, select

from database.governance_models import (
    GovernanceEvaluationAuditEvent,
    GovernanceEvaluationDecision,
    GovernanceEvaluationRun,
    GovernanceEvaluationRunSuiteExecution,
    GovernanceEvidenceReview,
)
from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.ports.evidence_review import EvidenceReviewScope
from src.application.services.verified_evidence_review_service import (
    VerifiedEvidenceReviewService,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchRepository,
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)
from tests.test_evaluation_workbench_repository import (
    ORG,
    OTHER_ORG,
    USER,
    _create_active_plan_and_run,
    _service,
    repository_fixture,
)
from tests.test_evidence_admission_repository import _admission_command, _seed_signing_authority


def _admitted_scope(
    session,
    *,
    seed_authority: bool = True,
    run_key: str = "integrity-run",
) -> EvidenceReviewScope:
    _plan, run = _create_active_plan_and_run(_service(session), run_key=run_key)
    if seed_authority:
        _seed_signing_authority(session)
    admission = _admission_command(session, run)
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    repository.persist_verified_passport_v2(admission)
    repository.force_evidence_admission_constraints()
    session.commit()
    return EvidenceReviewScope(
        organization_id=ORG,
        workspace_id="workspace-a",
        system_id="system-a",
        run_id=admission.scope.run_id,
        suite_execution_id=admission.scope.suite_execution_id,
        admission_id=admission.admission_id,
        passport_revision_id=admission.passport_revision_id,
    )


def _review_service(session) -> VerifiedEvidenceReviewService:
    return VerifiedEvidenceReviewService(SqlAlchemyEvaluationWorkbenchUnitOfWork(session))


def test_sqlite_repository_rejects_review_freshness_authority(
    repository_fixture,
) -> None:
    session, _factory = repository_fixture
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)

    with pytest.raises(EvaluationWorkbenchError) as caught:
        repository.load_evidence_review_authority_for_update(
            scope=EvidenceReviewScope(
                organization_id=ORG,
                workspace_id="workspace-a",
                system_id="system-a",
                run_id="run-a",
                suite_execution_id="suite-a",
                admission_id="admission-a",
                passport_revision_id="revision-a",
            )
        )

    assert caught.value.code == "operational_freshness_postgresql_required"


class _ProjectionFailingRepository:
    """Test double that simulates a CAS miss after the review insert is attempted."""

    def __init__(self, delegate: SqlAlchemyEvaluationWorkbenchRepository) -> None:
        self._delegate = delegate

    def read_fresh_utc_now(self):
        return self._delegate.read_fresh_utc_now()

    def load_evidence_review_authority_for_update(self, *, scope):
        return self._delegate.load_evidence_review_authority_for_update(scope=scope)

    def persist_evidence_review(self, command):
        return self._delegate.persist_evidence_review(
            replace(
                command,
                authority=replace(command.authority, linked_by="linker-mismatch"),
            )
        )


class _ProjectionFailingUnitOfWork:
    def __init__(self, session) -> None:
        delegate = SqlAlchemyEvaluationWorkbenchRepository(session)
        self.repository = _ProjectionFailingRepository(delegate)
        self._delegate = SqlAlchemyEvaluationWorkbenchUnitOfWork(
            session,
            repository=delegate,
        )

    def mutate(self, command, callback):
        return self._delegate.mutate(command, callback)


def test_sqlite_review_mutation_fails_closed_replays_rejection_and_writes_no_review(
    repository_fixture,
) -> None:
    session, _factory = repository_fixture
    scope = _admitted_scope(session)
    service = _review_service(session)

    for _attempt in range(2):
        with pytest.raises(EvaluationWorkbenchError) as unavailable:
            service.review_verified_evidence(
                scope=scope,
                actor_id="independent-reviewer-a",
                idempotency_key="review-replay-a",
                decision="accepted",
                rationale="Independent evidence review completed.",
                expected_review_version=0,
            )
        assert unavailable.value.code == "operational_freshness_postgresql_required"

    with pytest.raises(EvaluationWorkbenchError) as conflict:
        service.review_verified_evidence(
            scope=scope,
            actor_id="independent-reviewer-a",
            idempotency_key="review-replay-a",
            decision="accepted",
            rationale="A different rationale must conflict.",
            expected_review_version=0,
        )
    assert conflict.value.code == "idempotency_conflict"

    assert session.scalar(select(func.count()).select_from(GovernanceEvidenceReview.__table__)) == 0
    suite = (
        session.execute(
            select(GovernanceEvaluationRunSuiteExecution.__table__).where(
                GovernanceEvaluationRunSuiteExecution.id == scope.suite_execution_id
            )
        )
        .mappings()
        .one()
    )
    assert suite["review_status"] == "pending"
    assert (
        session.scalar(select(func.count()).select_from(GovernanceEvaluationDecision.__table__))
        == 0
    )
    assert (
        session.scalar(
            select(func.count())
            .select_from(GovernanceEvaluationAuditEvent.__table__)
            .where(GovernanceEvaluationAuditEvent.action == "evaluation_v2.evidence.reviewed")
        )
        == 0
    )
    assert (
        session.scalar(
            select(func.count())
            .select_from(GovernanceEvaluationAuditEvent.__table__)
            .where(
                GovernanceEvaluationAuditEvent.action == "evaluation_v2.mutation.rejected",
                GovernanceEvaluationAuditEvent.outcome == "rejected",
            )
        )
        == 2
    )


def test_sqlite_rejects_before_four_eyes_and_scope_loader_remains_tenant_exact(
    repository_fixture,
    monkeypatch,
) -> None:
    session, _factory = repository_fixture
    scope = _admitted_scope(session)
    service = _review_service(session)

    with pytest.raises(EvaluationWorkbenchError) as submitter:
        service.review_verified_evidence(
            scope=scope,
            actor_id=USER,
            idempotency_key="review-submitter-a",
            decision="rejected",
            rationale="Independent evidence review completed.",
            expected_review_version=0,
        )
    assert submitter.value.code == "operational_freshness_postgresql_required"

    wrong_scope = EvidenceReviewScope(
        organization_id=scope.organization_id,
        workspace_id="workspace-wrong",
        system_id=scope.system_id,
        run_id=scope.run_id,
        suite_execution_id=scope.suite_execution_id,
        admission_id=scope.admission_id,
        passport_revision_id=scope.passport_revision_id,
    )
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    monkeypatch.setattr(repository, "_require_postgres_freshness_authority", lambda: None)
    assert repository.load_evidence_review_authority_for_update(scope=wrong_scope) is None
    assert session.scalar(select(func.count()).select_from(GovernanceEvidenceReview.__table__)) == 0


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("organization_id", OTHER_ORG),
        ("workspace_id", "workspace-wrong"),
        ("system_id", "system-wrong"),
        ("run_id", "run-wrong"),
        ("suite_execution_id", "suite-execution-wrong"),
        ("admission_id", "admission-wrong"),
        ("passport_revision_id", "passport-revision-wrong"),
    ),
    ids=(
        "organization",
        "workspace",
        "system",
        "run",
        "suite-execution",
        "admission",
        "passport-revision",
    ),
)
def test_review_rejects_every_mutated_scope_identity_without_a_review_row(
    repository_fixture,
    monkeypatch,
    field: str,
    value: str,
) -> None:
    session, _factory = repository_fixture
    scope = _admitted_scope(session)
    mutated_scope = replace(scope, **{field: value})

    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    monkeypatch.setattr(repository, "_require_postgres_freshness_authority", lambda: None)
    assert repository.load_evidence_review_authority_for_update(scope=mutated_scope) is None
    assert session.scalar(select(func.count()).select_from(GovernanceEvidenceReview.__table__)) == 0


def test_review_rejects_admission_and_passport_cross_pairs_without_a_review_row(
    repository_fixture,
    monkeypatch,
) -> None:
    session, _factory = repository_fixture
    first_scope = _admitted_scope(session, run_key="review-cross-pair-first")
    second_scope = _admitted_scope(
        session,
        seed_authority=False,
        run_key="review-cross-pair-second",
    )
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    monkeypatch.setattr(repository, "_require_postgres_freshness_authority", lambda: None)

    for name, mutated_scope in (
        ("admission", replace(first_scope, admission_id=second_scope.admission_id)),
        (
            "passport",
            replace(first_scope, passport_revision_id=second_scope.passport_revision_id),
        ),
    ):
        assert repository.load_evidence_review_authority_for_update(scope=mutated_scope) is None

    assert session.scalar(select(func.count()).select_from(GovernanceEvidenceReview.__table__)) == 0


def test_sqlite_never_reaches_projection_cas_and_records_only_rejection_audit(
    repository_fixture,
) -> None:
    session, _factory = repository_fixture
    scope = _admitted_scope(session)
    service = VerifiedEvidenceReviewService(_ProjectionFailingUnitOfWork(session))

    with pytest.raises(EvaluationWorkbenchError) as failed:
        service.review_verified_evidence(
            scope=scope,
            actor_id="independent-reviewer-a",
            idempotency_key="review-projection-failure",
            decision="accepted",
            rationale="Independent evidence review completed.",
            expected_review_version=0,
        )

    assert failed.value.code == "operational_freshness_postgresql_required"
    assert session.scalar(select(func.count()).select_from(GovernanceEvidenceReview.__table__)) == 0
    suite = (
        session.execute(
            select(GovernanceEvaluationRunSuiteExecution.__table__).where(
                GovernanceEvaluationRunSuiteExecution.id == scope.suite_execution_id
            )
        )
        .mappings()
        .one()
    )
    assert suite["review_status"] == "pending"
    assert (
        session.scalar(
            select(func.count())
            .select_from(GovernanceEvaluationAuditEvent.__table__)
            .where(GovernanceEvaluationAuditEvent.action == "evaluation_v2.evidence.reviewed")
        )
        == 0
    )
    assert (
        session.scalar(
            select(func.count())
            .select_from(GovernanceEvaluationAuditEvent.__table__)
            .where(
                GovernanceEvaluationAuditEvent.action == "evaluation_v2.mutation.rejected",
                GovernanceEvaluationAuditEvent.outcome == "rejected",
            )
        )
        == 1
    )
