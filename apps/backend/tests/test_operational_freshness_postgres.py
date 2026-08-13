"""Native PostgreSQL 14 integration tests for operational evidence freshness.

The verified-admission suite owns the authoritative signed Passport V2 fixture.
This module installs 013g once on that exact migrated schema, then exercises the
classifier and application repositories against complete relational evidence.
"""

from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from threading import Event
from typing import Any

import pytest
from sqlalchemy import text

from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.ports.evidence_review import EvidenceReviewScope
from src.application.ports.governance_decision import GovernanceDecisionScope
from src.application.services.governance_decision_service import GovernanceDecisionService
from src.application.services.verified_evidence_review_service import (
    VerifiedEvidenceReviewService,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchRepository,
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)
from tests.test_verified_evidence_admission_postgres import (
    _admit,
    _scope,
    _seed_scenario,
    _signed_passport,
    postgres_session_factory,
)


MIGRATION_013G = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "013g_operational_evidence_freshness.sql"
)


@pytest.fixture(scope="module")
def operational_freshness_session_factory(postgres_session_factory):
    """Install 013g once in the existing verified-admission schema."""

    session = postgres_session_factory()
    try:
        schema = session.scalar(text("SELECT current_schema()"))
        assert isinstance(schema, str) and schema
        session.execute(
            text(
                "SELECT pg_catalog.set_config"
                "('fairmind.migration_schema', :schema, false)"
            ),
            {"schema": schema},
        )
        session.execute(text(MIGRATION_013G.read_text(encoding="utf-8")))
        session.commit()
    finally:
        session.close()
    return postgres_session_factory


@dataclass(frozen=True)
class AdmittedGraph:
    scenario: Any
    admission_id: str
    passport_revision_id: str
    suite_execution_id: str

    @property
    def review_scope(self) -> EvidenceReviewScope:
        return EvidenceReviewScope(
            organization_id=self.scenario.org_id,
            workspace_id=self.scenario.workspace_id,
            system_id=self.scenario.system_id,
            run_id=self.scenario.run_id,
            suite_execution_id=self.suite_execution_id,
            admission_id=self.admission_id,
            passport_revision_id=self.passport_revision_id,
        )

    @property
    def decision_scope(self) -> GovernanceDecisionScope:
        return GovernanceDecisionScope(
            organization_id=self.scenario.org_id,
            workspace_id=self.scenario.workspace_id,
            system_id=self.scenario.system_id,
            run_id=self.scenario.run_id,
        )


def _admitted_graph(factory) -> AdmittedGraph:
    scenario = _seed_scenario(factory, suite_count=1)
    _payload, raw = _signed_passport(scenario)
    admission_session = factory()
    try:
        result = _admit(
            admission_session,
            scenario,
            raw=raw,
            idempotency_key=f"freshness-admit-{uuid.uuid4()}",
            scope=_scope(scenario),
        )
        assert result.status == 201
    finally:
        admission_session.close()

    suite_execution_id = str(scenario.suite_executions[0]["id"])
    read_session = factory()
    try:
        row = (
            read_session.execute(
                text(
                    "SELECT id, passport_revision_id "
                    "FROM governance_evidence_admissions "
                    "WHERE org_id = :org_id AND workspace_id = :workspace_id "
                    "AND system_id = :system_id AND run_id = :run_id "
                    "AND suite_execution_id = :suite_execution_id"
                ),
                {
                    "org_id": scenario.org_id,
                    "workspace_id": scenario.workspace_id,
                    "system_id": scenario.system_id,
                    "run_id": scenario.run_id,
                    "suite_execution_id": suite_execution_id,
                },
            )
            .mappings()
            .one()
        )
    finally:
        read_session.close()
    return AdmittedGraph(
        scenario=scenario,
        admission_id=str(row["id"]),
        passport_revision_id=str(row["passport_revision_id"]),
        suite_execution_id=suite_execution_id,
    )


def _classify(session, graph: AdmittedGraph) -> dict[str, object]:
    return dict(
        session.execute(
            text(
                "SELECT * FROM fairmind_classify_evidence_freshness_013g("
                ":org_id, :workspace_id, :system_id, :run_id, "
                ":suite_execution_id, :admission_id, NULL)"
            ),
            {
                "org_id": graph.scenario.org_id,
                "workspace_id": graph.scenario.workspace_id,
                "system_id": graph.scenario.system_id,
                "run_id": graph.scenario.run_id,
                "suite_execution_id": graph.suite_execution_id,
                "admission_id": graph.admission_id,
            },
        )
        .mappings()
        .one()
    )


def _review(factory, graph: AdmittedGraph, *, reviewer_id: str) -> dict[str, object]:
    session = factory()
    try:
        result = VerifiedEvidenceReviewService(
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session)
        ).review_verified_evidence(
            scope=graph.review_scope,
            actor_id=reviewer_id,
            idempotency_key=f"freshness-review-{uuid.uuid4()}",
            decision="accepted",
            rationale="Independent PostgreSQL freshness review accepted the evidence.",
            expected_review_version=0,
        )
        assert result.status == 201
        return dict(result.body)
    finally:
        session.close()


def _decision_layers(graph: AdmittedGraph) -> dict[str, dict[str, str]]:
    return {
        "suites": {graph.suite_execution_id: "conditional"},
        "modalities": {},
        "components": {},
        "riskDimensions": {},
    }


def _decide(factory, graph: AdmittedGraph, *, decider_id: str) -> dict[str, object]:
    session = factory()
    try:
        result = GovernanceDecisionService(
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session)
        ).decide(
            scope=graph.decision_scope,
            actor_id=decider_id,
            idempotency_key=f"freshness-decision-{uuid.uuid4()}",
            expected_verdict_version=0,
            overall_verdict="conditional",
            layer_verdicts=_decision_layers(graph),
            rationale="Current accepted evidence supports a conditional governance verdict.",
        )
        assert result.status == 201
        return dict(result.body)
    finally:
        session.close()


def _revoke_registration(
    session,
    graph: AdmittedGraph,
    *,
    started: Event | None = None,
    updated: Event | None = None,
    release: Event | None = None,
) -> None:
    if started is not None:
        started.set()
    session.execute(
        text(
            "UPDATE governance_evaluator_registrations "
            "SET status = 'revoked', revoked_by = 'freshness-revoker-a', "
            "revoked_at = '2000-01-01T00:00:00+00:00', "
            "revocation_rationale = 'Native freshness race invalidated this evaluator.' "
            "WHERE id = :registration_id AND org_id = :org_id"
        ),
        {
            "registration_id": graph.scenario.evaluator_registration_id,
            "org_id": graph.scenario.org_id,
        },
    )
    if updated is not None:
        updated.set()
    if release is not None and not release.wait(timeout=30):
        raise RuntimeError("revocation release timed out")
    session.commit()


class _SignallingUnitOfWork(SqlAlchemyEvaluationWorkbenchUnitOfWork):
    """Expose actual PostgreSQL advisory-lock acquisition to the race test."""

    def __init__(self, session, *, lock_started: Event, lock_acquired: Event) -> None:
        super().__init__(session)
        self._lock_started_event = lock_started
        self._lock_acquired_event = lock_acquired

    def _lock_org(self, org_id: str) -> None:
        self._lock_started_event.set()
        super()._lock_org(org_id)
        self._lock_acquired_event.set()


class _BlockingDecisionRepository(SqlAlchemyEvaluationWorkbenchRepository):
    """Hold the real decision authority while the common org lock is owned."""

    def __init__(self, session, *, authority_loaded: Event, release: Event) -> None:
        super().__init__(session)
        self._authority_loaded_event = authority_loaded
        self._release_event = release

    def load_governance_decision_authority_for_update(self, *, scope):
        authority = super().load_governance_decision_authority_for_update(scope=scope)
        self._authority_loaded_event.set()
        if not self._release_event.wait(timeout=30):
            raise RuntimeError("decision authority release timed out")
        return authority


class _CallerTimeEvidenceReviewRepository(SqlAlchemyEvaluationWorkbenchRepository):
    """Submit an adversarial caller time while preserving real persistence."""

    caller_time = datetime(2000, 1, 1, tzinfo=timezone.utc)

    def persist_evidence_review(self, command):
        return super().persist_evidence_review(
            replace(command, reviewed_at=self.caller_time)
        )


def test_verified_linked_evidence_is_current_but_not_decision_eligible_before_review(
    operational_freshness_session_factory,
) -> None:
    """Catches a classifier that launders an unreviewed admission into a verdict."""

    factory = operational_freshness_session_factory
    graph = _admitted_graph(factory)
    session = factory()
    try:
        row = _classify(session, graph)
    finally:
        session.close()

    assert row["classification_status"] == "ok"
    assert row["freshness_contract_version"] == "1.0.0"
    assert row["recorded_freshness_status"] == "current"
    assert row["effective_freshness_status"] == "current"
    assert row["effective_at"] <= row["evaluated_at"] < row["expiring_at"]
    assert json.loads(str(row["reason_codes_json"])) == []
    assert row["decision_eligible"] is False
    assert row["evaluated_at"].tzinfo is not None
    assert row["evaluated_at"].astimezone(timezone.utc).utcoffset().total_seconds() == 0


def test_current_accepted_evidence_reaches_one_governance_decision(
    operational_freshness_session_factory,
) -> None:
    """Catches a decision adapter that cannot consume the DB-owned freshness gate."""

    factory = operational_freshness_session_factory
    graph = _admitted_graph(factory)
    reviewer_id = "independent-reviewer-a"
    decider_id = "independent-decider-a"

    review = _review(factory, graph, reviewer_id=reviewer_id)
    assert review["reviewStatus"] == "accepted"
    assert review["freshnessStatus"] == "current"
    assert review["recordedFreshnessStatus"] == "current"
    assert review["decisionEvidenceEligibleAtReview"] is True

    decision = _decide(factory, graph, decider_id=decider_id)
    assert decision["verdictVersion"] == 1
    assert decision["overallVerdict"] == "conditional"
    assert decision["decisionEvidenceEligibleAtDecision"] is True
    assert len(decision["suiteFreshness"]) == 1
    suite_freshness = decision["suiteFreshness"][0]
    assert suite_freshness["suiteExecutionId"] == graph.suite_execution_id
    assert suite_freshness["recordedFreshnessStatus"] == "current"
    assert suite_freshness["effectiveFreshnessStatus"] == "current"
    assert suite_freshness["freshnessReasonCodes"] == []
    assert suite_freshness["decisionEvidenceEligibleAtDecision"] is True
    assert datetime.fromisoformat(suite_freshness["freshnessEffectiveAt"]).tzinfo is not None
    assert datetime.fromisoformat(suite_freshness["expiringAt"]).tzinfo is not None

    persisted = factory()
    try:
        row = (
            persisted.execute(
                text(
                    "SELECT verdict_version, overall_verdict, decided_by, decided_at "
                    "FROM governance_evaluation_decisions "
                    "WHERE org_id = :org_id AND run_id = :run_id"
                ),
                {"org_id": graph.scenario.org_id, "run_id": graph.scenario.run_id},
            )
            .mappings()
            .one()
        )
    finally:
        persisted.close()
    assert row["verdict_version"] == 1
    assert row["overall_verdict"] == "conditional"
    assert row["decided_by"] == decider_id
    assert datetime.fromisoformat(str(row["decided_at"])).tzinfo is not None


def test_review_insert_returning_uses_database_time_not_caller_time(
    operational_freshness_session_factory,
) -> None:
    """Catches the review adapter trusting an application-supplied chronology."""

    factory = operational_freshness_session_factory
    graph = _admitted_graph(factory)
    session = factory()
    try:
        repository = _CallerTimeEvidenceReviewRepository(session)
        result = VerifiedEvidenceReviewService(
            SqlAlchemyEvaluationWorkbenchUnitOfWork(
                session,
                repository=repository,
            )
        ).review_verified_evidence(
            scope=graph.review_scope,
            actor_id="independent-reviewer-clock-a",
            idempotency_key=f"freshness-review-clock-{uuid.uuid4()}",
            decision="accepted",
            rationale="PostgreSQL must replace the caller supplied review time.",
            expected_review_version=0,
        )
        persisted_reviewed_at = session.scalar(
            text(
                "SELECT reviewed_at FROM governance_evidence_reviews "
                "WHERE org_id = :org_id AND admission_id = :admission_id"
            ),
            {"org_id": graph.scenario.org_id, "admission_id": graph.admission_id},
        )
    finally:
        session.close()

    assert result.status == 201
    assert result.body["reviewedAt"] != repository.caller_time.isoformat()
    assert result.body["reviewedAt"] == persisted_reviewed_at
    assert result.body["freshnessEvaluatedAt"] == result.body["reviewedAt"]
    assert result.body["decisionEvidenceEligibleAtReview"] is True


def test_committed_registration_revocation_denies_a_new_governance_decision(
    operational_freshness_session_factory,
) -> None:
    """Catches the decision service relying on historical acceptance after revocation."""

    factory = operational_freshness_session_factory
    graph = _admitted_graph(factory)
    _review(factory, graph, reviewer_id="independent-reviewer-revoked-decision")
    revoke_session = factory()
    try:
        _revoke_registration(revoke_session, graph)
    finally:
        revoke_session.close()

    decision_session = factory()
    try:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            GovernanceDecisionService(
                SqlAlchemyEvaluationWorkbenchUnitOfWork(decision_session)
            ).decide(
                scope=graph.decision_scope,
                actor_id="independent-decider-after-revocation",
                idempotency_key=f"freshness-revoked-decision-{uuid.uuid4()}",
                expected_verdict_version=0,
                overall_verdict="conditional",
                layer_verdicts=_decision_layers(graph),
                rationale="Revoked evaluator evidence must not support a new verdict.",
            )
        decision_count = decision_session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_decisions "
                "WHERE org_id = :org_id AND run_id = :run_id"
            ),
            {"org_id": graph.scenario.org_id, "run_id": graph.scenario.run_id},
        )
    finally:
        decision_session.close()

    assert caught.value.code == "governance_decision_evidence_not_ready"
    assert caught.value.status_code == 409
    assert decision_count == 0


def test_registration_revocation_lock_wins_before_review_and_review_fails_closed(
    operational_freshness_session_factory,
) -> None:
    """Catches a review that reads pre-revocation authority after waiting on its lock."""

    factory = operational_freshness_session_factory
    graph = _admitted_graph(factory)
    revocation_updated = Event()
    release_revocation = Event()
    review_lock_started = Event()
    review_lock_acquired = Event()

    def revoke_first() -> None:
        session = factory()
        try:
            _revoke_registration(
                session,
                graph,
                updated=revocation_updated,
                release=release_revocation,
            )
        finally:
            session.close()

    def review_second() -> tuple[str, int]:
        session = factory()
        try:
            service = VerifiedEvidenceReviewService(
                _SignallingUnitOfWork(
                    session,
                    lock_started=review_lock_started,
                    lock_acquired=review_lock_acquired,
                )
            )
            try:
                service.review_verified_evidence(
                    scope=graph.review_scope,
                    actor_id="independent-reviewer-race-a",
                    idempotency_key=f"freshness-review-race-{uuid.uuid4()}",
                    decision="accepted",
                    rationale="Revoked evaluator evidence must not be accepted.",
                    expected_review_version=0,
                )
            except EvaluationWorkbenchError as error:
                return error.code, error.status_code
            raise AssertionError("review unexpectedly accepted revoked evaluator evidence")
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        revoke_future = executor.submit(revoke_first)
        assert revocation_updated.wait(timeout=30)
        review_future = executor.submit(review_second)
        assert review_lock_started.wait(timeout=30)
        assert not review_lock_acquired.wait(timeout=0.25)
        release_revocation.set()
        revoke_future.result(timeout=30)
        outcome = review_future.result(timeout=30)

    assert outcome == ("evidence_review_evidence_not_current", 409)
    session = factory()
    try:
        row = _classify(session, graph)
        review_count = session.scalar(
            text(
                "SELECT count(*) FROM governance_evidence_reviews "
                "WHERE org_id = :org_id AND admission_id = :admission_id"
            ),
            {"org_id": graph.scenario.org_id, "admission_id": graph.admission_id},
        )
    finally:
        session.close()
    assert row["classification_status"] == "ok"
    assert row["effective_freshness_status"] == "stale"
    assert json.loads(str(row["reason_codes_json"])) == [
        "evaluator_registration_revoked"
    ]
    assert row["decision_eligible"] is False
    assert review_count == 0


def test_decision_lock_wins_then_revocation_invalidates_only_live_eligibility(
    operational_freshness_session_factory,
) -> None:
    """Catches revocation bypassing the decision's organization-wide lock."""

    factory = operational_freshness_session_factory
    graph = _admitted_graph(factory)
    _review(factory, graph, reviewer_id="independent-reviewer-race-b")
    authority_loaded = Event()
    release_decision = Event()
    revocation_started = Event()
    revocation_updated = Event()
    revocation_committed = Event()

    def decide_first() -> dict[str, object]:
        session = factory()
        try:
            repository = _BlockingDecisionRepository(
                session,
                authority_loaded=authority_loaded,
                release=release_decision,
            )
            result = GovernanceDecisionService(
                SqlAlchemyEvaluationWorkbenchUnitOfWork(
                    session,
                    repository=repository,
                )
            ).decide(
                scope=graph.decision_scope,
                actor_id="independent-decider-race-b",
                idempotency_key=f"freshness-decision-race-{uuid.uuid4()}",
                expected_verdict_version=0,
                overall_verdict="conditional",
                layer_verdicts=_decision_layers(graph),
                rationale="Decision owns the organization lock before revocation.",
            )
            return dict(result.body)
        finally:
            session.close()

    def revoke_second() -> None:
        session = factory()
        try:
            _revoke_registration(
                session,
                graph,
                started=revocation_started,
                updated=revocation_updated,
            )
            revocation_committed.set()
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        decision_future = executor.submit(decide_first)
        assert authority_loaded.wait(timeout=30)
        revocation_future = executor.submit(revoke_second)
        assert revocation_started.wait(timeout=30)
        assert not revocation_updated.wait(timeout=0.25)
        assert not revocation_committed.is_set()
        release_decision.set()
        decision = decision_future.result(timeout=30)
        revocation_future.result(timeout=30)

    assert decision["verdictVersion"] == 1
    assert decision["decisionEvidenceEligibleAtDecision"] is True
    assert revocation_updated.is_set()
    assert revocation_committed.is_set()

    session = factory()
    try:
        row = _classify(session, graph)
        persisted_verdict = session.execute(
            text(
                "SELECT verdict_version, overall_verdict "
                "FROM governance_evaluation_decisions "
                "WHERE org_id = :org_id AND run_id = :run_id"
            ),
            {"org_id": graph.scenario.org_id, "run_id": graph.scenario.run_id},
        ).one()
    finally:
        session.close()
    assert row["classification_status"] == "ok"
    assert row["effective_freshness_status"] == "stale"
    assert json.loads(str(row["reason_codes_json"])) == [
        "evaluator_registration_revoked"
    ]
    assert row["decision_eligible"] is False
    assert persisted_verdict == (1, "conditional")
