"""Native PostgreSQL 14 service contract for audited owner decision overrides."""

from __future__ import annotations

import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest
from sqlalchemy import text

from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.services.governance_decision_service import GovernanceDecisionService
from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256
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
    _insert_raw_review,
    _install_owner_role,
)
from tests.test_verified_evidence_admission_postgres import postgres_session_factory

MIGRATIONS = Path(__file__).parents[1] / "migrations"
OWNER_OPERATION = "evaluation-v2.governance-decision.owner-override"
OWNER_AUDIT_ACTION = "evaluation_v2.governance_decision.owner_override_created"
REJECTED_AUDIT_ACTION = "evaluation_v2.mutation.rejected"
OWNER_REASON = "Canonical owner is also the request and evidence actor."


@pytest.fixture(scope="module")
def owner_override_session_factory():
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


def _set_application_name(session, name: str) -> None:
    session.execute(
        text("SELECT pg_catalog.set_config('application_name', :name, false)"),
        {"name": name},
    )


def _wait_for_postgres_lock(factory, application_name: str) -> None:
    observer = factory()
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            waiting = observer.scalar(
                text(
                    "SELECT wait_event_type='Lock' FROM pg_catalog.pg_stat_activity "
                    "WHERE application_name=:application_name"
                ),
                {"application_name": application_name},
            )
            observer.rollback()
            if waiting is True:
                return
        raise AssertionError(f"{application_name} did not reach a PostgreSQL lock wait")
    finally:
        observer.close()


class _EventRepository(SqlAlchemyEvaluationWorkbenchRepository):
    def __init__(
        self,
        session,
        *,
        authorize_reached: Event | None = None,
        authority_reached: Event | None = None,
        release: Event,
    ) -> None:
        super().__init__(session)
        self.authorize_reached = authorize_reached
        self.authority_reached = authority_reached
        self.release = release

    def authorize_owner_decision_override_for_update(self, **kwargs) -> bool:
        authorized = super().authorize_owner_decision_override_for_update(**kwargs)
        if self.authorize_reached is not None:
            self.authorize_reached.set()
            assert self.release.wait(timeout=10)
        return authorized

    def load_governance_decision_authority_for_update(self, **kwargs):
        authority = super().load_governance_decision_authority_for_update(**kwargs)
        if self.authority_reached is not None:
            self.authority_reached.set()
            assert self.release.wait(timeout=10)
        return authority


class _EventOrgLockUnitOfWork(SqlAlchemyEvaluationWorkbenchUnitOfWork):
    def __init__(self, session, *, locked: Event, release: Event) -> None:
        super().__init__(session)
        self.locked = locked
        self.release = release

    def _lock_org(self, org_id: str) -> None:
        super()._lock_org(org_id)
        self.locked.set()
        assert self.release.wait(timeout=10)


def _owner_worker(
    factory,
    graph,
    *,
    key: str,
    application_name: str | None = None,
    repository_factory=None,
    start: Event | None = None,
    ready: Event | None = None,
):
    if ready is not None:
        ready.set()
    if start is not None:
        assert start.wait(timeout=10)
    session = factory()
    try:
        if application_name is not None:
            _set_application_name(session, application_name)
        repository = repository_factory(session) if repository_factory else None
        unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(
            session,
            repository=repository,
        )
        return GovernanceDecisionService(unit_of_work).decide_owner_override(
            scope=graph.decision_scope,
            actor_id=graph.scenario.actor_id,
            idempotency_key=key,
            expected_verdict_version=0,
            overall_verdict="conditional",
            layer_verdicts=_decision_layers(graph),
            rationale="Evidence supports a conditional verdict.",
            owner_override_reason=OWNER_REASON,
        )
    finally:
        session.close()


@pytest.mark.asyncio
async def test_owner_override_http_rejects_every_scope_substitution_before_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fastapi import HTTPException
    from src.api.routers import evaluation_workbench as router
    from src.application.services.governance_assurance_service import OrgMembership

    first = {
        "organizationId": "org-a",
        "workspaceId": "workspace-a",
        "systemId": "system-a",
        "id": "run-a",
        "contractVersion": "2.0.0",
    }
    second = {
        "organizationId": "org-b",
        "workspaceId": "workspace-b",
        "systemId": "system-b",
        "id": "run-b",
        "contractVersion": "2.0.0",
    }

    class Runs:
        def get_run(self, *, run_id: str, **_kwargs):
            return {"run-a": first, "run-b": second}.get(run_id)

    class Decisions:
        calls: list[dict[str, object]] = []

        def decide_owner_override(self, **kwargs):
            self.calls.append(kwargs)
            raise AssertionError("scope rejection must precede service invocation")

    monkeypatch.setattr(router, "_run_service", lambda _db: Runs())
    membership = OrgMembership(
        org_id="org-a",
        user_id="owner-a",
        role="owner",
        permissions=("evaluation:decision",),
    )
    service = Decisions()
    substitutions = (
        ("org-b", "workspace-a", "system-a", "run-a"),
        ("org-a", "workspace-b", "system-a", "run-a"),
        ("org-a", "workspace-a", "system-b", "run-a"),
        ("org-a", "workspace-a", "system-a", "run-b"),
        ("org-a", "workspace-b", "system-b", "run-b"),
    )
    for org_id, workspace_id, system_id, run_id in substitutions:
        with pytest.raises(HTTPException) as rejected:
            await router.create_owner_decision_override(
                org_id=org_id,
                workspace_id=workspace_id,
                system_id=system_id,
                run_id=run_id,
                request=None,
                idempotency_key=f"scope-{uuid.uuid4()}",
                membership=membership,
                db=object(),
                decision_service=service,
            )
        assert rejected.value.status_code == 404
        assert rejected.value.detail["code"] == "decision_scope_not_found"
    assert service.calls == []


@pytest.mark.parametrize(
    ("table", "statement", "column"),
    (
        (
            "organization",
            "UPDATE organizations SET is_active=false WHERE id=:org_id",
            "is_active",
        ),
        (
            "member",
            "UPDATE org_members SET status='inactive' "
            "WHERE org_id=:org_id AND user_id=:actor_id",
            "status",
        ),
        (
            "role",
            "UPDATE org_roles SET is_system_role=false "
            "WHERE org_id=:org_id AND name='owner'",
            "is_system_role",
        ),
    ),
)
def test_owner_override_locks_each_authority_row_until_commit(
    owner_override_session_factory,
    table: str,
    statement: str,
    column: str,
) -> None:
    factory = owner_override_session_factory
    graph = _ready_owner_graph(factory)
    authority_locked = Event()
    release_override = Event()
    writer_started = Event()
    application_name = f"owner-authority-writer-{uuid.uuid4()}"

    def repository(session):
        return _EventRepository(
            session,
            authorize_reached=authority_locked,
            release=release_override,
        )

    def write_authority() -> None:
        session = factory()
        try:
            _set_application_name(session, application_name)
            writer_started.set()
            session.execute(
                text(statement),
                {
                    "org_id": graph.scenario.org_id,
                    "actor_id": graph.scenario.actor_id,
                },
            )
            session.commit()
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        override = pool.submit(
            _owner_worker,
            factory,
            graph,
            key=f"authority-lock-{table}-{uuid.uuid4()}",
            repository_factory=repository,
        )
        assert authority_locked.wait(timeout=10)
        writer = pool.submit(write_authority)
        assert writer_started.wait(timeout=10)
        _wait_for_postgres_lock(factory, application_name)
        assert not writer.done()
        release_override.set()
        assert override.result(timeout=30).status == 201
        writer.result(timeout=30)

    session = factory()
    try:
        table_name = {
            "organization": "organizations",
            "member": "org_members",
            "role": "org_roles",
        }[table]
        predicate = {
            "organization": "id=:org_id",
            "member": "org_id=:org_id AND user_id=:actor_id",
            "role": "org_id=:org_id AND name='owner'",
        }[table]
        value = session.scalar(
            text(f"SELECT {column} FROM {table_name} WHERE {predicate}"),
            {"org_id": graph.scenario.org_id, "actor_id": graph.scenario.actor_id},
        )
        assert value in (False, "inactive")
        assert tuple(map(len, _owner_rows(session, graph))) == (1, 1, 1)
    finally:
        session.close()


def test_owner_override_reloads_authority_after_writer_commits_first(
    owner_override_session_factory,
) -> None:
    factory = owner_override_session_factory
    graph = _ready_owner_graph(factory)
    writer_updated = Event()
    release_writer = Event()
    application_name = f"owner-blocked-after-writer-{uuid.uuid4()}"

    def write_authority() -> None:
        session = factory()
        try:
            session.execute(
                text("UPDATE organizations SET is_active=false WHERE id=:org_id"),
                {"org_id": graph.scenario.org_id},
            )
            writer_updated.set()
            assert release_writer.wait(timeout=10)
            session.commit()
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        writer = pool.submit(write_authority)
        assert writer_updated.wait(timeout=10)
        override = pool.submit(
            _owner_worker,
            factory,
            graph,
            key=f"authority-writer-first-{uuid.uuid4()}",
            application_name=application_name,
        )
        _wait_for_postgres_lock(factory, application_name)
        release_writer.set()
        writer.result(timeout=30)
        with pytest.raises(EvaluationWorkbenchError) as rejected:
            override.result(timeout=30)
        assert rejected.value.code == "evaluation_separation_override_forbidden"

    session = factory()
    try:
        decisions, idempotency, success = _owner_rows(session, graph)
        assert decisions == []
        assert len(idempotency) == 1 and idempotency[0]["status"] == "completed"
        assert success == []
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_audit_events "
                "WHERE org_id=:org_id AND outcome='rejected' AND action=:action"
            ),
            {"org_id": graph.scenario.org_id, "action": REJECTED_AUDIT_ACTION},
        ) == 1
    finally:
        session.close()


def test_normal_decision_and_override_share_one_verdict_cas(
    owner_override_session_factory,
) -> None:
    factory = owner_override_session_factory
    graph = _ready_owner_graph(factory)
    org_locked = Event()
    release_normal = Event()
    application_name = f"owner-cas-loser-{uuid.uuid4()}"

    def decide_normal():
        session = factory()
        try:
            unit_of_work = _EventOrgLockUnitOfWork(
                session,
                locked=org_locked,
                release=release_normal,
            )
            return GovernanceDecisionService(unit_of_work).decide(
                scope=graph.decision_scope,
                actor_id=f"independent-decider-{uuid.uuid4()}",
                idempotency_key=f"normal-cas-{uuid.uuid4()}",
                expected_verdict_version=0,
                overall_verdict="conditional",
                layer_verdicts=_decision_layers(graph),
                rationale="Independent evidence supports a conditional verdict.",
            )
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        normal = pool.submit(decide_normal)
        assert org_locked.wait(timeout=10)
        override = pool.submit(
            _owner_worker,
            factory,
            graph,
            key=f"override-cas-{uuid.uuid4()}",
            application_name=application_name,
        )
        _wait_for_postgres_lock(factory, application_name)
        release_normal.set()
        assert normal.result(timeout=30).body["verdictVersion"] == 1
        with pytest.raises(EvaluationWorkbenchError) as stale:
            override.result(timeout=30)
        assert stale.value.code == "governance_decision_version_conflict"

    session = factory()
    try:
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_decisions "
                "WHERE run_id=:run_id AND verdict_version=1"
            ),
            {"run_id": graph.scenario.run_id},
        ) == 1
        assert session.scalar(
            text(
                "SELECT verdict_version FROM governance_evaluation_runs "
                "WHERE id=:run_id"
            ),
            {"run_id": graph.scenario.run_id},
        ) == 1
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_audit_events "
                "WHERE org_id=:org_id AND outcome='success' "
                "AND resource_type='evaluation_governance_decision'"
            ),
            {"org_id": graph.scenario.org_id},
        ) == 1
    finally:
        session.close()


@pytest.mark.parametrize("ordering", ("decision-first", "review-first"))
def test_review_insert_and_override_serialize_on_the_run_lock(
    owner_override_session_factory,
    ordering: str,
) -> None:
    from sqlalchemy.exc import DBAPIError

    factory = owner_override_session_factory
    graph = _ready_owner_graph(factory)
    review_reached = Event()
    release_review = Event()
    decision_reached = Event()
    release_decision = Event()
    review_application_name = f"owner-review-race-review-{uuid.uuid4()}"
    decision_application_name = f"owner-review-race-decision-{uuid.uuid4()}"

    def insert_review(*, pause_after_insert: bool) -> None:
        session = factory()
        try:
            _set_application_name(session, review_application_name)
            _insert_raw_review(
                session,
                graph,
                reviewer_sql="'second-independent-reviewer'",
                review_version=2,
            )
            review_reached.set()
            if pause_after_insert:
                assert release_review.wait(timeout=10)
            session.commit()
        finally:
            session.close()

    def repository(session):
        return _EventRepository(
            session,
            authority_reached=decision_reached,
            release=release_decision,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        if ordering == "decision-first":
            decision = pool.submit(
                _owner_worker,
                factory,
                graph,
                key=f"review-race-decision-first-{uuid.uuid4()}",
                repository_factory=repository,
            )
            assert decision_reached.wait(timeout=10)
            review = pool.submit(insert_review, pause_after_insert=False)
            _wait_for_postgres_lock(factory, review_application_name)
            release_decision.set()
            assert decision.result(timeout=30).status == 201
            with pytest.raises(DBAPIError, match="reviews are frozen"):
                review.result(timeout=30)
        else:
            review = pool.submit(insert_review, pause_after_insert=True)
            assert review_reached.wait(timeout=10)
            decision = pool.submit(
                _owner_worker,
                factory,
                graph,
                key=f"review-race-review-first-{uuid.uuid4()}",
                application_name=decision_application_name,
            )
            _wait_for_postgres_lock(factory, decision_application_name)
            release_review.set()
            review.result(timeout=30)
            assert decision.result(timeout=30).status == 201

    session = factory()
    try:
        review_versions = session.scalars(
            text(
                "SELECT review_version FROM governance_evidence_reviews "
                "WHERE admission_id=:admission_id ORDER BY review_version"
            ),
            {"admission_id": graph.admission_id},
        ).all()
        assert review_versions == ([1] if ordering == "decision-first" else [1, 2])
        assert session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_decisions "
                "WHERE run_id=:run_id"
            ),
            {"run_id": graph.scenario.run_id},
        ) == 1
    finally:
        session.close()


def test_twenty_identical_owner_overrides_produce_one_commit_and_nineteen_replays(
    owner_override_session_factory,
) -> None:
    factory = owner_override_session_factory
    graph = _ready_owner_graph(factory)
    start = Event()
    ready = [Event() for _ in range(20)]
    key = f"owner-twenty-replays-{uuid.uuid4()}"
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = [
            pool.submit(
                _owner_worker,
                factory,
                graph,
                key=key,
                start=start,
                ready=ready[index],
            )
            for index in range(20)
        ]
        assert all(event.wait(timeout=10) for event in ready)
        start.set()
        results = [future.result(timeout=60) for future in futures]

    assert sum(result.replayed is False for result in results) == 1
    assert sum(result.replayed is True for result in results) == 19
    assert len({canonical_json(result.body) for result in results}) == 1
    session = factory()
    try:
        decisions, idempotency, audits = _owner_rows(session, graph)
        assert len(decisions) == len(idempotency) == len(audits) == 1
        assert idempotency[0]["status"] == "completed"
    finally:
        session.close()
