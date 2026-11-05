"""Transactional persistence tests for four-eyes verified-evidence review."""

from __future__ import annotations

from dataclasses import replace

import pytest
from sqlalchemy import func, select

from database.governance_models import GovernanceEvidenceReview
from src.application.ports.evidence_review import EvidenceReviewScope
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchRepository,
)
from tests.test_evaluation_workbench_repository import (  # noqa: F401  (fixture re-export)
    ORG,
    OTHER_ORG,
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
    field: str,
    value: str,
) -> None:
    session, _factory = repository_fixture
    scope = _admitted_scope(session)
    mutated_scope = replace(scope, **{field: value})

    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    assert repository.load_evidence_review_authority_for_update(scope=mutated_scope) is None
    assert session.scalar(select(func.count()).select_from(GovernanceEvidenceReview.__table__)) == 0


def test_review_rejects_admission_and_passport_cross_pairs_without_a_review_row(
    repository_fixture,
) -> None:
    session, _factory = repository_fixture
    first_scope = _admitted_scope(session, run_key="review-cross-pair-first")
    second_scope = _admitted_scope(
        session,
        seed_authority=False,
        run_key="review-cross-pair-second",
    )
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)

    for name, mutated_scope in (
        ("admission", replace(first_scope, admission_id=second_scope.admission_id)),
        (
            "passport",
            replace(first_scope, passport_revision_id=second_scope.passport_revision_id),
        ),
    ):
        assert repository.load_evidence_review_authority_for_update(scope=mutated_scope) is None

    assert session.scalar(select(func.count()).select_from(GovernanceEvidenceReview.__table__)) == 0
