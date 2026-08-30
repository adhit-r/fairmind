"""Native PostgreSQL 14 contract for named separation-override grants."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.services.governance_decision_service import GovernanceDecisionService
from src.domain.assurance.evaluation_v2 import canonical_json
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchRepository,
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)
from tests.test_operational_freshness_postgres import (
    _admitted_graph,
    _decision_layers,
    _review,
)
from tests.test_owner_decision_override_integrity_013j import (
    _assert_schema_dropped,
    _install_owner_role,
)
from tests.test_verified_evidence_admission_postgres import postgres_session_factory

MIGRATIONS = Path(__file__).parents[1] / "migrations"
REASON = "No independent decision owner is available for this exact run."


@pytest.fixture(scope="module")
def delegated_override_session_factory():
    chain = postgres_session_factory.__wrapped__()
    factory = next(chain)
    session = factory()
    schema = ""
    try:
        schema = session.scalar(text("SELECT current_schema()"))
        assert isinstance(schema, str) and schema
        for migration in (
            "013g_operational_evidence_freshness.sql",
            "013h_idempotency_retention_integrity.sql",
            "013i_imported_evidence_delivery_integrity.sql",
            "013j_owner_decision_override_integrity.sql",
            "013k_verified_evidence_link_integrity.sql",
            "013l_delegated_separation_override_grant_integrity.sql",
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
    try:
        yield factory
    finally:
        try:
            next(chain)
        except StopIteration:
            pass
        _assert_schema_dropped(schema)


def _ready_delegated_graph(factory):
    graph = _admitted_graph(factory)
    _review(factory, graph, reviewer_id="independent-reviewer")
    owner_id = str(uuid.uuid4())
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
                "id": owner_id,
                "email": f"{owner_id}@example.test",
                "username": owner_id,
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
                "user_id": owner_id,
            },
        )
        session.execute(
            text(
                "UPDATE org_members SET role='delegated-decider', status='active' "
                "WHERE org_id=:org_id AND user_id=:actor_id"
            ),
            {
                "org_id": graph.scenario.org_id,
                "actor_id": graph.scenario.actor_id,
            },
        )
        session.execute(
            text("DELETE FROM org_roles WHERE org_id=:org_id"),
            {"org_id": graph.scenario.org_id},
        )
        _install_owner_role(session, graph, owner_id)
        session.execute(
            text(
                "INSERT INTO org_roles "
                "(id, org_id, name, permissions, is_system_role) "
                "VALUES (:id, :org_id, 'delegated-decider', "
                "'[\"evaluation:decision\"]'::jsonb, true)"
            ),
            {"id": str(uuid.uuid4()), "org_id": graph.scenario.org_id},
        )
        session.commit()
    finally:
        session.close()
    return graph, owner_id, graph.scenario.actor_id


def _grant(factory, graph, owner_id: str):
    session = factory()
    try:
        return GovernanceDecisionService(
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session)
        ).create_separation_override_grant(
            scope=graph.decision_scope,
            actor_id=owner_id,
            idempotency_key=f"delegated-grant-{uuid.uuid4()}",
            grantee_actor_id=graph.scenario.actor_id,
            expected_verdict_version=0,
            reason=REASON,
        )
    finally:
        session.close()


def _decide(factory, graph, actor_id: str, grant_id: str, *, version: int = 0):
    session = factory()
    try:
        return GovernanceDecisionService(
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session)
        ).decide_delegated_override(
            scope=graph.decision_scope,
            actor_id=actor_id,
            idempotency_key=f"delegated-decision-{uuid.uuid4()}",
            grant_id=grant_id,
            expected_verdict_version=version,
            overall_verdict="conditional",
            layer_verdicts=_decision_layers(graph),
            rationale="Current evidence supports a conditional verdict.",
        )
    finally:
        session.close()


def test_named_exact_run_grant_creates_one_decision_receipt(
    delegated_override_session_factory,
) -> None:
    factory = delegated_override_session_factory
    graph, owner_id, delegate_id = _ready_delegated_graph(factory)

    grant = _grant(factory, graph, owner_id)
    assert grant.status == 201
    assert "separationOverrideReason" not in grant.body
    decision = _decide(factory, graph, delegate_id, grant.body["grantId"])
    assert decision.status == 201
    assert decision.body["separationOverrideApplied"] is True
    assert decision.body["separationOverrideGrantId"] == grant.body["grantId"]

    with pytest.raises(EvaluationWorkbenchError) as reused:
        _decide(factory, graph, delegate_id, grant.body["grantId"], version=1)
    assert reused.value.code == "evaluation_separation_override_grant_forbidden"

    session = factory()
    try:
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_decisions "
                "WHERE separation_override_grant_id=:grant_id"
            ),
            {"grant_id": grant.body["grantId"]},
        ) == 1
    finally:
        session.close()


def test_exact_run_grant_rejects_every_actor_except_the_named_grantee(
    delegated_override_session_factory,
) -> None:
    factory = delegated_override_session_factory
    graph, owner_id, _delegate_id = _ready_delegated_graph(factory)
    grant = _grant(factory, graph, owner_id)

    with pytest.raises(EvaluationWorkbenchError) as denied:
        _decide(factory, graph, owner_id, grant.body["grantId"])

    assert denied.value.status_code == 403
    assert denied.value.code == "evaluation_separation_override_grant_forbidden"


def test_exact_run_grant_fails_closed_when_grantee_loses_decision_permission(
    delegated_override_session_factory,
) -> None:
    factory = delegated_override_session_factory
    graph, owner_id, delegate_id = _ready_delegated_graph(factory)
    grant = _grant(factory, graph, owner_id)
    session = factory()
    try:
        session.execute(
            text(
                "UPDATE org_roles SET permissions='[]'::jsonb "
                "WHERE org_id=:org_id AND name='delegated-decider'"
            ),
            {"org_id": graph.scenario.org_id},
        )
        session.commit()
    finally:
        session.close()

    with pytest.raises(EvaluationWorkbenchError) as denied:
        _decide(factory, graph, delegate_id, grant.body["grantId"])

    assert denied.value.status_code == 403
    assert denied.value.code == "evaluation_separation_override_grant_forbidden"


def test_raw_grant_without_atomic_audit_binding_rolls_back(
    delegated_override_session_factory,
) -> None:
    factory = delegated_override_session_factory
    graph, owner_id, delegate_id = _ready_delegated_graph(factory)
    grant_id = str(uuid.uuid4())
    session = factory()
    try:
        authority = SqlAlchemyEvaluationWorkbenchRepository(
            session
        ).load_governance_decision_authority_for_update(scope=graph.decision_scope)
        assert authority is not None
        with pytest.raises(DBAPIError, match="separation override grant audit binding failed"):
            session.execute(
                text(
                    "INSERT INTO governance_separation_override_grants "
                    "(id, org_id, workspace_id, system_id, run_id, "
                    "run_contract_version, envelope_id, envelope_hash, "
                    "evidence_set_json, evidence_set_hash, expected_verdict_version, "
                    "granted_by, grantee_actor_id, reason, granted_at, expires_at) "
                    "VALUES (:id, :org_id, :workspace_id, :system_id, :run_id, "
                    ":contract_version, :envelope_id, :envelope_hash, "
                    ":evidence_set_json, :evidence_set_hash, 0, :granted_by, "
                    ":grantee_actor_id, :reason, :granted_at, :expires_at)"
                ),
                {
                    "id": grant_id,
                    "org_id": graph.scenario.org_id,
                    "workspace_id": graph.scenario.workspace_id,
                    "system_id": graph.scenario.system_id,
                    "run_id": graph.scenario.run_id,
                    "contract_version": authority.run_contract_version,
                    "envelope_id": authority.envelope_id,
                    "envelope_hash": authority.envelope_hash,
                    "evidence_set_json": canonical_json(authority.evidence_set.to_dict()),
                    "evidence_set_hash": authority.evidence_set_hash,
                    "granted_by": owner_id,
                    "grantee_actor_id": delegate_id,
                    "reason": REASON,
                    "granted_at": "2000-01-01T00:00:00.000000+00:00",
                    "expires_at": "2000-01-01T00:30:00.000000+00:00",
                },
            )
            session.commit()
        session.rollback()
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_separation_override_grants "
                "WHERE id=:grant_id"
            ),
            {"grant_id": grant_id},
        ) == 0
    finally:
        session.close()
