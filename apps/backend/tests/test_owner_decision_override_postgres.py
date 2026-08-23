"""Native PostgreSQL 14 service contract for audited owner decision overrides."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text

from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.services.governance_decision_service import GovernanceDecisionService
from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)
from tests.test_operational_freshness_postgres import (
    _admitted_graph,
    _decision_layers,
    _review,
)
from tests.test_owner_decision_override_integrity_013j import _install_owner_role
from tests.test_verified_evidence_admission_postgres import postgres_session_factory

MIGRATIONS = Path(__file__).parents[1] / "migrations"
OWNER_OPERATION = "evaluation-v2.governance-decision.owner-override"
OWNER_AUDIT_ACTION = "evaluation_v2.governance_decision.owner_override_created"
REJECTED_AUDIT_ACTION = "evaluation_v2.mutation.rejected"
OWNER_REASON = "Canonical owner is also the request and evidence actor."


@pytest.fixture(scope="module")
def owner_override_session_factory(postgres_session_factory):
    session = postgres_session_factory()
    try:
        schema = session.scalar(text("SELECT current_schema()"))
        assert isinstance(schema, str) and schema
        for migration in (
            "013g_operational_evidence_freshness.sql",
            "013h_idempotency_retention_integrity.sql",
            "013i_imported_evidence_delivery_integrity.sql",
            "013j_owner_decision_override_integrity.sql",
        ):
            session.execute(
                text(
                    "SELECT pg_catalog.set_config"
                    "('fairmind.migration_schema', :schema, false)"
                ),
                {"schema": schema},
            )
            session.execute(text((MIGRATIONS / migration).read_text(encoding="utf-8")))
        session.commit()
    finally:
        session.close()
    return postgres_session_factory


def _ready_owner_graph(factory):
    graph = _admitted_graph(factory)
    _review(factory, graph, reviewer_id="independent-reviewer")
    session = factory()
    try:
        _install_owner_role(session, graph, graph.scenario.actor_id)
        session.commit()
    finally:
        session.close()
    return graph


def _install_independent_owner(factory, graph) -> str:
    actor_id = str(uuid.uuid4())
    session = factory()
    try:
        session.execute(
            text(
                "INSERT INTO users "
                "(id, email, username, password_hash, role, permissions) "
                "VALUES (:id, :email, :username, "
                "'test-only-invalid-password-hash', 'admin', '[]'::jsonb)"
            ),
            {
                "id": actor_id,
                "email": f"{actor_id}@example.test",
                "username": actor_id,
            },
        )
        session.execute(
            text(
                "INSERT INTO org_members (id, org_id, user_id, role, status) "
                "VALUES (:id, :org_id, :user_id, 'owner', 'active')"
            ),
            {
                "id": str(uuid.uuid4()),
                "org_id": graph.scenario.org_id,
                "user_id": actor_id,
            },
        )
        _install_owner_role(session, graph, actor_id)
        session.commit()
    finally:
        session.close()
    return actor_id


def _decide_owner(
    session,
    graph,
    *,
    key: str,
    reason: str = OWNER_REASON,
    actor_id: str | None = None,
):
    actor_id = actor_id or graph.scenario.actor_id
    return GovernanceDecisionService(
        SqlAlchemyEvaluationWorkbenchUnitOfWork(session)
    ).decide_owner_override(
        scope=graph.decision_scope,
        actor_id=actor_id,
        idempotency_key=key,
        expected_verdict_version=0,
        overall_verdict="conditional",
        layer_verdicts=_decision_layers(graph),
        rationale="Evidence supports a conditional verdict.",
        owner_override_reason=reason,
    )


def _owner_rows(session, graph, *, actor_id: str | None = None):
    actor_id = actor_id or graph.scenario.actor_id
    decisions = (
        session.execute(
            text(
                "SELECT id, owner_override_reason FROM governance_evaluation_decisions "
                "WHERE org_id=:org_id AND run_id=:run_id"
            ),
            {"org_id": graph.scenario.org_id, "run_id": graph.scenario.run_id},
        )
        .mappings()
        .all()
    )
    idempotency = (
        session.execute(
            text(
                "SELECT status, response_status, response_body_json "
                "FROM governance_idempotency_records "
                "WHERE org_id=:org_id AND actor_id=:actor_id AND operation=:operation"
            ),
            {
                "org_id": graph.scenario.org_id,
                "actor_id": actor_id,
                "operation": OWNER_OPERATION,
            },
        )
        .mappings()
        .all()
    )
    audits = (
        session.execute(
            text(
                "SELECT outcome, details_json FROM governance_evaluation_audit_events "
                "WHERE org_id=:org_id AND action=:action"
            ),
            {"org_id": graph.scenario.org_id, "action": OWNER_AUDIT_ACTION},
        )
        .mappings()
        .all()
    )
    return decisions, idempotency, audits


def _rejected_rows(session, graph, *, actor_id: str):
    decisions = session.execute(
        text(
            "SELECT id FROM governance_evaluation_decisions "
            "WHERE org_id=:org_id AND run_id=:run_id"
        ),
        {"org_id": graph.scenario.org_id, "run_id": graph.scenario.run_id},
    ).all()
    idempotency = (
        session.execute(
            text(
                "SELECT status, response_status, response_body_json "
                "FROM governance_idempotency_records "
                "WHERE org_id=:org_id AND actor_id=:actor_id AND operation=:operation"
            ),
            {
                "org_id": graph.scenario.org_id,
                "actor_id": actor_id,
                "operation": OWNER_OPERATION,
            },
        )
        .mappings()
        .all()
    )
    audits = (
        session.execute(
            text(
                "SELECT outcome, details_json FROM governance_evaluation_audit_events "
                "WHERE org_id=:org_id AND actor_id=:actor_id AND action=:action"
            ),
            {
                "org_id": graph.scenario.org_id,
                "actor_id": actor_id,
                "action": REJECTED_AUDIT_ACTION,
            },
        )
        .mappings()
        .all()
    )
    return decisions, idempotency, audits


class _FailBeforeAuditUnitOfWork(SqlAlchemyEvaluationWorkbenchUnitOfWork):
    def _append_audit(self, **_kwargs):
        raise RuntimeError("injected owner override audit failure")


def test_owner_override_success_replay_and_conflict_use_one_audited_uow(
    owner_override_session_factory,
) -> None:
    factory = owner_override_session_factory
    graph = _ready_owner_graph(factory)
    session = factory()
    try:
        result = _decide_owner(session, graph, key="native-owner-override")
        assert result.status == 201
        assert result.body["ownerOverrideApplied"] is True
        assert "ownerOverrideReason" not in result.body

        decisions, idempotency, audits = _owner_rows(session, graph)
        assert len(decisions) == len(idempotency) == len(audits) == 1
        assert decisions[0]["owner_override_reason"] == OWNER_REASON
        assert idempotency[0]["status"] == "completed"
        assert idempotency[0]["response_status"] == 201
        assert OWNER_REASON not in idempotency[0]["response_body_json"]

        details = json.loads(audits[0]["details_json"])
        domain = details["_fairmindEvaluationSuccessBinding"]["domainDetails"]
        relationships = [
            {
                "relationshipType": "evidence_submitter",
                "actorId": graph.scenario.actor_id,
                "resourceType": "evidence_admission",
                "resourceIds": [graph.admission_id],
            },
            {
                "relationshipType": "run_requester",
                "actorId": graph.scenario.actor_id,
                "resourceType": "evaluation_run",
                "resourceIds": [graph.scenario.run_id],
            },
        ]
        assert audits[0]["outcome"] == "success"
        assert domain["waivedRelationships"] == relationships
        assert domain["waivedRelationshipsHash"] == canonical_sha256(relationships)
        assert domain["ownerOverrideReasonHash"] == canonical_sha256(
            {"ownerOverrideReason": OWNER_REASON}
        )
        assert OWNER_REASON not in canonical_json(result.body)
        assert OWNER_REASON not in audits[0]["details_json"]

        replay = _decide_owner(session, graph, key="native-owner-override")
        assert replay.replayed is True
        assert canonical_json(replay.body) == canonical_json(result.body)
        replay_rows = _owner_rows(session, graph)
        assert tuple(map(len, replay_rows)) == (1, 1, 1)

        with pytest.raises(EvaluationWorkbenchError) as caught:
            _decide_owner(
                session,
                graph,
                key="native-owner-override",
                reason="A changed reason must conflict with the original request.",
            )
        assert caught.value.code == "idempotency_conflict"
    finally:
        session.close()


def test_owner_override_rolls_back_decision_claim_and_retries_after_audit_failure(
    owner_override_session_factory,
) -> None:
    factory = owner_override_session_factory
    graph = _ready_owner_graph(factory)
    session = factory()
    try:
        service = GovernanceDecisionService(_FailBeforeAuditUnitOfWork(session))
        with pytest.raises(EvaluationWorkbenchError) as caught:
            service.decide_owner_override(
                scope=graph.decision_scope,
                actor_id=graph.scenario.actor_id,
                idempotency_key="native-owner-override-rollback",
                expected_verdict_version=0,
                overall_verdict="conditional",
                layer_verdicts=_decision_layers(graph),
                rationale="Evidence supports a conditional verdict.",
                owner_override_reason=OWNER_REASON,
            )
        assert caught.value.code == "evaluation_persistence_failed"
        assert tuple(map(len, _owner_rows(session, graph))) == (0, 0, 0)

        retry = _decide_owner(
            session,
            graph,
            key="native-owner-override-rollback",
        )
        assert retry.status == 201
        assert retry.body["ownerOverrideApplied"] is True
        assert tuple(map(len, _owner_rows(session, graph))) == (1, 1, 1)
    finally:
        session.close()


@pytest.mark.parametrize(
    ("case", "expected_code", "expected_status"),
    (
        ("authority-false", "evaluation_separation_override_forbidden", 403),
        ("override-not-required", "governance_decision_override_not_required", 409),
    ),
)
def test_owner_override_expected_rejections_are_audited_and_replayable(
    owner_override_session_factory,
    case: str,
    expected_code: str,
    expected_status: int,
) -> None:
    factory = owner_override_session_factory
    graph = _admitted_graph(factory)
    _review(factory, graph, reviewer_id="independent-reviewer")
    actor_id = graph.scenario.actor_id
    if case == "override-not-required":
        actor_id = _install_independent_owner(factory, graph)

    session = factory()
    key = f"native-owner-override-{case}"
    try:
        with pytest.raises(EvaluationWorkbenchError) as first:
            _decide_owner(session, graph, key=key, actor_id=actor_id)
        assert first.value.code == expected_code
        assert first.value.status_code == expected_status
        first_detail = first.value.detail()

        decisions, idempotency, audits = _rejected_rows(
            session,
            graph,
            actor_id=actor_id,
        )
        assert len(decisions) == 0
        assert len(idempotency) == len(audits) == 1
        assert idempotency[0]["status"] == "completed"
        assert idempotency[0]["response_status"] == expected_status
        assert audits[0]["outcome"] == "rejected"
        assert json.loads(audits[0]["details_json"])["errorCode"] == expected_code
        assert OWNER_REASON not in canonical_json(first_detail)
        assert OWNER_REASON not in idempotency[0]["response_body_json"]
        assert OWNER_REASON not in audits[0]["details_json"]

        with pytest.raises(EvaluationWorkbenchError) as replay:
            _decide_owner(session, graph, key=key, actor_id=actor_id)
        assert replay.value.detail() == first_detail
        assert tuple(
            map(
                len,
                _rejected_rows(session, graph, actor_id=actor_id),
            )
        ) == (0, 1, 1)

        with pytest.raises(EvaluationWorkbenchError) as conflict:
            _decide_owner(
                session,
                graph,
                key=key,
                actor_id=actor_id,
                reason="A changed reason must conflict with the rejected request.",
            )
        assert conflict.value.code == "idempotency_conflict"
    finally:
        session.close()
