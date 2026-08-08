"""Organization-scoped Evaluation Plan and Evaluation Run API tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from config.auth import TokenData, TokenType, UserRole, get_current_active_user
from config.settings import settings
from database.connection import Base, get_db
from database.governance_models import (
    GovernanceAISystem,
    GovernanceEvaluationPlan,
    GovernanceEvaluationRun,
    GovernanceEvidencePassportRevision,
    GovernanceEvidenceRun,
    GovernanceWorkspace,
)
from database.models import Organization, OrganizationAuditLog, OrganizationMember, User
from src.application.services.evaluation_runs_service import (
    EvaluationRunsService,
    EvaluationWorkflowError,
)


ORG_A = str(uuid.uuid4())
ORG_B = str(uuid.uuid4())
USER_A = str(uuid.uuid4())
USER_B = str(uuid.uuid4())
VIEWER = str(uuid.uuid4())
BASE = "/api/v1/ai-governance/organizations"


def _token(user_id: str) -> TokenData:
    now = datetime.now(timezone.utc)
    return TokenData(
        user_id=user_id,
        email=f"{user_id}@example.test",
        role=UserRole.ANALYST,
        token_type=TokenType.ACCESS,
        iat=now,
        exp=now,
    )


def _seed_org(session, org_id: str, user_id: str, *, role: str = "admin") -> None:
    user_uuid = uuid.UUID(user_id)
    if session.execute(
        select(User.__table__.c.id).where(User.__table__.c.id == user_uuid)
    ).scalar_one_or_none() is None:
        session.execute(
            User.__table__.insert().values(
                id=user_uuid,
                email=f"{user_id}@example.test",
                username=user_id,
            )
        )
    session.execute(
        Organization.__table__.insert().values(
            id=uuid.UUID(org_id),
            name=org_id,
            slug=org_id,
            owner_id=user_uuid,
        )
    )
    session.execute(
        OrganizationMember.__table__.insert().values(
            id=uuid.uuid4(),
            org_id=uuid.UUID(org_id),
            user_id=user_uuid,
            role=role,
            status="active",
        )
    )


def _seed_member(session, org_id: str, user_id: str, *, role: str) -> None:
    user_uuid = uuid.UUID(user_id)
    session.execute(
        User.__table__.insert().values(
            id=user_uuid,
            email=f"{user_id}@example.test",
            username=user_id,
        )
    )
    session.execute(
        OrganizationMember.__table__.insert().values(
            id=uuid.uuid4(),
            org_id=uuid.UUID(org_id),
            user_id=user_uuid,
            role=role,
            status="active",
        )
    )


def _seed_system(
    session,
    *,
    org_id: str,
    workspace_id: str,
    system_id: str,
) -> None:
    session.execute(
        GovernanceWorkspace.__table__.insert().values(
            id=workspace_id,
            org_id=org_id,
            name=workspace_id,
        )
    )
    session.execute(
        GovernanceAISystem.__table__.insert().values(
            id=system_id,
            workspace_id=workspace_id,
            org_id=org_id,
            name=system_id,
        )
    )


@pytest.fixture
def evaluation_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys = ON")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    active_user = {"value": _token(USER_A)}
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    _seed_org(session, ORG_B, USER_B)
    _seed_member(session, ORG_A, VIEWER, role="viewer")
    _seed_system(session, org_id=ORG_A, workspace_id="workspace-a", system_id="system-a")
    _seed_system(session, org_id=ORG_B, workspace_id="workspace-b", system_id="system-b")
    session.commit()
    session.close()

    def override_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    async def override_user():
        return active_user["value"]

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_active_user] = override_user
    try:
        with TestClient(app) as client:
            yield client, session_factory, active_user
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def _plan_payload(**overrides) -> dict:
    payload = {
        "name": "Release assurance",
        "targetKind": "predictive_model",
        "lifecyclePhases": ["pre_deploy"],
        "executionDepth": "hybrid",
        "enforcementMode": "human_approval",
        "deliveryMode": "external_provider",
        "suiteRefs": ["fairmind/bias@2026.07"],
    }
    payload.update(overrides)
    return payload


def _plans_url(org_id: str = ORG_A, system_id: str = "system-a") -> str:
    return f"{BASE}/{org_id}/systems/{system_id}/evaluation-plans"


def _create_plan(client: TestClient, **overrides) -> dict:
    response = client.post(_plans_url(), json=_plan_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def _activate(client: TestClient, plan_id: str):
    return client.post(f"{_plans_url()}/{plan_id}/activate")


def _create_run(client: TestClient, plan_id: str, *, trigger: str = "manual"):
    return client.post(f"{_plans_url()}/{plan_id}/runs", json={"trigger": trigger})


def _audit_actions(session_factory) -> list[str]:
    session = session_factory()
    try:
        return list(
            session.execute(
                select(OrganizationAuditLog.__table__.c.action).order_by(
                    OrganizationAuditLog.__table__.c.created_at
                )
            ).scalars()
        )
    finally:
        session.close()


def _workflow_detail(message: str, next_action: str) -> dict:
    return {
        "detail": {
            "code": "passport_scope_mismatch",
            "message": message,
            "nextAction": next_action,
        }
    }


def test_v1_mutations_are_quarantined_when_assurance_v2_is_enabled(
    evaluation_client,
) -> None:
    client, session_factory, _ = evaluation_client
    plan = _create_plan(client)
    assert plan["contractVersion"] == "1.0.0"
    assert _activate(client, plan["id"]).status_code == 200
    run_response = _create_run(client, plan["id"])
    assert run_response.status_code == 201, run_response.text
    run = run_response.json()
    assert run["contractVersion"] == "1.0.0"

    session = session_factory()
    try:
        before = {
            "plans": len(
                session.execute(
                    select(GovernanceEvaluationPlan.__table__.c.id)
                ).all()
            ),
            "runs": len(
                session.execute(
                    select(GovernanceEvaluationRun.__table__.c.id)
                ).all()
            ),
            "audits": len(
                session.execute(select(OrganizationAuditLog.__table__.c.id)).all()
            ),
        }
    finally:
        session.close()

    expected = {
        "detail": {
            "code": "contract_upgrade_required",
            "message": (
                "Legacy evaluation mutations are disabled while Assurance V2 "
                "is enabled."
            ),
            "nextAction": (
                "Clone legacy records into a bound v2 plan and use the "
                "evaluation-v2 workflow."
            ),
        }
    }
    original = settings.assurance_v2_enabled
    try:
        settings.assurance_v2_enabled = True
        responses = (
            client.post(_plans_url(), json=_plan_payload(name="Blocked legacy plan")),
            _activate(client, plan["id"]),
            _create_run(client, plan["id"]),
            client.post(
                f"{BASE}/{ORG_A}/systems/system-a/evaluation-runs/{run['id']}"
                "/evidence-passport-link",
                json={
                    "evidenceRunId": "blocked-evidence",
                    "passportRevisionId": "blocked-passport-revision",
                },
            ),
        )
        for response in responses:
            assert response.status_code == 409
            assert response.json() == expected

        plans = client.get(_plans_url())
        assert plans.status_code == 200
        assert [item["id"] for item in plans.json()] == [plan["id"]]
        assert plans.json()[0]["contractVersion"] == "1.0.0"
        assert plans.json()[0]["status"] == "active"
        preflight = client.get(f"{_plans_url()}/{plan['id']}/preflight")
        assert preflight.status_code == 200
        assert preflight.json() == {
            "planId": plan["id"],
            "canPrepareRun": False,
            "fairmindExecutionAvailable": False,
            "code": "contract_upgrade_required",
            "message": (
                "This legacy assurance-contract v1 plan cannot prepare a new run "
                "while Assurance V2 is enabled."
            ),
            "nextAction": (
                "Clone legacy records into a bound v2 plan and use the "
                "evaluation-v2 workflow."
            ),
        }
        assert (
            client.get(
                f"{BASE}/{ORG_A}/systems/system-a/evaluation-runs"
            ).status_code
            == 200
        )
        assert (
            client.get(
                f"{BASE}/{ORG_A}/systems/system-a/evaluation-runs/{run['id']}"
            ).status_code
            == 200
        )
    finally:
        settings.assurance_v2_enabled = original

    session = session_factory()
    try:
        after = {
            "plans": len(
                session.execute(
                    select(GovernanceEvaluationPlan.__table__.c.id)
                ).all()
            ),
            "runs": len(
                session.execute(
                    select(GovernanceEvaluationRun.__table__.c.id)
                ).all()
            ),
            "audits": len(
                session.execute(select(OrganizationAuditLog.__table__.c.id)).all()
            ),
        }
    finally:
        session.close()
    assert after == before


def _passport_snapshot(
    *,
    org_id: str = ORG_A,
    workspace_id: str = "workspace-a",
    system_id: str = "system-a",
    target_kind: str = "model",
    suite_name: str = "fairmind/bias",
    suite_version: str = "2026.07",
    capability_state: str = "validated",
    result_status: str = "passed",
    error_code: str | None = None,
    error_message: str | None = None,
) -> dict:
    """Canonical Passport 1.0 fields consumed by the exact-link contract."""
    result = {
        "status": result_status,
        "summary": f"Bounded {result_status} result.",
        "metrics": [],
        "startedAt": "2026-07-18T00:00:00Z",
        "endedAt": "2026-07-18T00:05:00Z",
    }
    if error_code is not None:
        result["errorCode"] = error_code
    if error_message is not None:
        result["errorMessage"] = error_message
    artifacts = []
    if result_status in {"error", "unavailable"}:
        artifacts.append(
            {
                "artifactId": "artifact-log",
                "role": "log",
                "uri": "https://evidence.example.test/evaluation.log",
                "sha256": "6" * 64,
                "mediaType": "text/plain",
                "containsSensitiveData": False,
            }
        )
    return {
        "schemaVersion": "1.0.0",
        "passportId": str(uuid.uuid4()),
        "passportRevision": 1,
        "claimBoundary": "supporting_evidence_only",
        "organizationId": org_id,
        "workspaceId": workspace_id,
        "aiSystem": {
            "systemId": system_id,
            "name": "System supplied name",
            "kind": target_kind,
            "version": "2026.07",
            "identityHash": "1" * 64,
            "ownerId": "owner-001",
        },
        "evaluation": {
            "sourceType": "fairmind_evaluation",
            "sourceIdentifier": "fairmind-bias-suite",
            "runId": str(uuid.uuid4()),
            "capabilityState": capability_state,
            "assuranceSource": "fairmind_internal",
            "evaluator": {"name": "FairMind evaluator", "version": "2.0.0"},
            "suite": {
                "name": suite_name,
                "version": suite_version,
                "trigger": "release_gate",
            },
            "subject": {"kind": target_kind, "subjectId": "subject-001"},
            "scope": {"intendedUse": "Bounded synthetic evaluation."},
            "configurationHash": "5" * 64,
            "thresholds": [],
            "result": result,
            "runContentHash": "2" * 64,
            "capturedAt": "2026-07-18T00:05:00Z",
            "limitations": ["Synthetic test set only."],
        },
        "artifacts": artifacts,
        "frameworkMappings": [],
        "review": {"status": "pending", "reviewVersion": 0},
        "findings": [],
        "remediation": [],
        "freshness": {
            "status": "current",
            "policy": "Re-evaluate on material change.",
            "assessedAt": "2026-07-18T00:05:00Z",
            "staleReasons": [],
            "invalidationKeys": ["system_version"],
        },
        "lineage": {"predecessorPassportIds": [], "retestOfPassportIds": []},
        "createdAt": "2026-07-18T00:05:00Z",
        "canonicalContentHash": "3" * 64,
    }


def _seed_passport(
    session_factory,
    *,
    evidence_run_id: str,
    revision_id: str,
    snapshot: dict,
    org_id: str = ORG_A,
    workspace_id: str = "workspace-a",
    system_id: str = "system-a",
    snapshot_json_override: str | None = None,
) -> str:
    session = session_factory()
    snapshot_json = snapshot_json_override or json.dumps(
        snapshot, sort_keys=True, separators=(",", ":")
    )
    try:
        session.execute(
            GovernanceEvidenceRun.__table__.insert().values(
                id=evidence_run_id,
                org_id=org_id,
                workspace_id=workspace_id,
                system_id=system_id,
                source_type="fairmind_evaluation",
                source_identifier="fairmind-bias-suite",
                run_id=snapshot["evaluation"]["runId"],
                content_hash="4" * 64,
                passport_id=snapshot["passportId"],
                schema_version=snapshot["schemaVersion"],
                capability_state=snapshot["evaluation"]["capabilityState"],
                assurance_source="fairmind_internal",
                result=snapshot["evaluation"]["result"]["status"],
                provenance_json="{}",
                artifact_refs_json="[]",
                limitations_json='["Synthetic test set only."]',
            )
        )
        session.execute(
            GovernanceEvidencePassportRevision.__table__.insert().values(
                id=revision_id,
                org_id=org_id,
                system_id=system_id,
                evidence_run_id=evidence_run_id,
                passport_id=snapshot["passportId"],
                passport_revision=1,
                previous_revision_hash=None,
                canonical_content_hash=snapshot["canonicalContentHash"],
                snapshot_json=snapshot_json,
                created_by=USER_A,
            )
        )
        session.commit()
        return snapshot_json
    finally:
        session.close()


def test_reads_are_membership_and_system_scoped_and_mutations_require_permission(
    evaluation_client,
) -> None:
    client, _, active_user = evaluation_client

    assert client.get(_plans_url()).status_code == 200
    assert client.get(_plans_url()).json() == []
    active_user["value"] = _token(USER_B)
    assert client.get(_plans_url()).status_code == 403
    active_user["value"] = _token(VIEWER)
    assert client.get(_plans_url()).status_code == 200
    assert client.post(_plans_url(), json=_plan_payload()).status_code == 403
    active_user["value"] = _token(USER_A)
    assert client.get(_plans_url(system_id="missing-system")).status_code == 404


@pytest.mark.parametrize(
    ("method", "path", "body", "expected"),
    [
        (
            "get",
            _plans_url(system_id="missing-system"),
            None,
            _workflow_detail(
                "AI system not found in this organization scope.",
                "Select an AI system in the current organization and workspace.",
            ),
        ),
        (
            "post",
            f"{_plans_url()}/{uuid.uuid4()}/activate",
            None,
            _workflow_detail(
                "Evaluation plan not found in this AI system scope.",
                "Refresh the plan list and select an available plan.",
            ),
        ),
        (
            "get",
            f"{_plans_url()}/{uuid.uuid4()}/preflight",
            None,
            _workflow_detail(
                "Evaluation plan not found in this AI system scope.",
                "Refresh the plan list and select an available plan.",
            ),
        ),
        (
            "get",
            f"{BASE}/{ORG_A}/systems/missing-system/evaluation-runs",
            None,
            _workflow_detail(
                "AI system not found in this organization scope.",
                "Select an AI system in the current organization and workspace.",
            ),
        ),
        (
            "get",
            f"{BASE}/{ORG_A}/systems/system-a/evaluation-runs/{uuid.uuid4()}",
            None,
            _workflow_detail(
                "Evaluation run not found in this AI system scope.",
                "Refresh the run list and select an available run.",
            ),
        ),
        (
            "post",
            (
                f"{BASE}/{ORG_A}/systems/system-a/evaluation-runs/{uuid.uuid4()}"
                "/evidence-passport-link"
            ),
            {"evidenceRunId": "missing-evidence", "passportRevisionId": "missing-revision"},
            _workflow_detail(
                "Evaluation run not found in this AI system scope.",
                "Refresh the run list and select an available run.",
            ),
        ),
    ],
)
def test_all_evaluation_404_paths_return_exact_workflow_envelope(
    evaluation_client, method, path, body, expected
) -> None:
    client, _, _ = evaluation_client

    response = client.request(method, path, json=body)

    assert response.status_code == 404
    assert response.json() == expected


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("name", "   "),
        ("name", "x" * 121),
        ("targetKind", "model"),
        ("lifecyclePhases", []),
        ("lifecyclePhases", ["pre_deploy", "pre_deploy"]),
        ("lifecyclePhases", ["pre_deploy", "realtime", "post_deploy", "extra"]),
        ("lifecyclePhases", ["deployment"]),
        ("executionDepth", "batch"),
        ("enforcementMode", "rubber_stamp"),
        ("deliveryMode", "internal_magic"),
        ("suiteRefs", []),
        ("suiteRefs", ["fairmind/bias@1", "fairmind/bias@1"]),
        ("suiteRefs", [f"namespace/suite-{index}@1" for index in range(33)]),
        ("suiteRefs", ["Display Name@latest"]),
        ("suiteRefs", ["fairmind/bias@"]),
        ("suiteRefs", ["fairmind/" + "a" * 150 + "@2026.07"]),
    ],
)
def test_plan_creation_rejects_invalid_contract_fields(evaluation_client, field, value) -> None:
    client, session_factory, _ = evaluation_client

    response = client.post(_plans_url(), json=_plan_payload(**{field: value}))

    assert response.status_code == 422, response.text
    session = session_factory()
    try:
        assert session.execute(select(GovernanceEvaluationPlan.__table__.c.id)).all() == []
    finally:
        session.close()


def test_plan_creation_is_camel_case_scoped_and_audited(evaluation_client) -> None:
    client, session_factory, _ = evaluation_client

    response = client.post(_plans_url(), json=_plan_payload())

    assert response.status_code == 201, response.text
    plan = response.json()
    assert plan == {
        **plan,
        "orgId": ORG_A,
        "workspaceId": "workspace-a",
        "systemId": "system-a",
        "targetKind": "predictive_model",
        "lifecyclePhases": ["pre_deploy"],
        "executionDepth": "hybrid",
        "enforcementMode": "human_approval",
        "deliveryMode": "external_provider",
        "suiteRefs": ["fairmind/bias@2026.07"],
        "status": "draft",
    }
    assert "target_kind" not in plan
    uuid.UUID(plan["id"])
    assert _audit_actions(session_factory) == ["evaluation_plan.created"]
    assert client.post(_plans_url(org_id=ORG_A, system_id="system-b"), json=_plan_payload()).status_code == 404


def test_plan_creation_rolls_back_when_audit_write_fails(evaluation_client, monkeypatch) -> None:
    client, session_factory, _ = evaluation_client

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("injected audit failure")

    monkeypatch.setattr(EvaluationRunsService, "_write_audit", fail_audit)
    response = client.post(_plans_url(), json=_plan_payload())

    assert response.status_code == 500, response.text
    assert response.json()["detail"]["code"] == "evaluation_persistence_failed"
    session = session_factory()
    try:
        assert session.execute(select(GovernanceEvaluationPlan.__table__.c.id)).all() == []
        assert session.execute(select(OrganizationAuditLog.__table__.c.id)).all() == []
    finally:
        session.close()


def test_plan_creation_rolls_back_when_response_read_fails(
    evaluation_client, monkeypatch
) -> None:
    client, session_factory, _ = evaluation_client

    def fail_response_read(*_args, **_kwargs):
        raise RuntimeError("injected response read failure")

    monkeypatch.setattr(EvaluationRunsService, "_plan_row", fail_response_read)
    response = client.post(_plans_url(), json=_plan_payload())

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "evaluation_persistence_failed"
    session = session_factory()
    try:
        assert session.execute(select(GovernanceEvaluationPlan.__table__.c.id)).all() == []
        assert session.execute(select(OrganizationAuditLog.__table__.c.id)).all() == []
    finally:
        session.close()


def test_activation_is_scoped_idempotent_and_does_not_retire_other_plans(evaluation_client) -> None:
    client, session_factory, _ = evaluation_client
    first = _create_plan(client)
    second = _create_plan(
        client,
        name="Agent assurance",
        targetKind="agent",
        suiteRefs=["fairmind/agent-safety@1.0"],
    )

    activated = _activate(client, first["id"])
    replay = _activate(client, first["id"])
    other = _activate(client, second["id"])

    assert activated.status_code == replay.status_code == other.status_code == 200
    assert activated.json()["status"] == replay.json()["status"] == "active"
    listed = client.get(_plans_url()).json()
    assert {plan["id"]: plan["status"] for plan in listed} == {
        first["id"]: "active",
        second["id"]: "active",
    }
    assert _audit_actions(session_factory).count("evaluation_plan.activated") == 2
    assert _activate(client, str(uuid.uuid4())).status_code == 404

    session = session_factory()
    try:
        session.execute(
            update(GovernanceEvaluationPlan.__table__)
            .where(GovernanceEvaluationPlan.__table__.c.id == second["id"])
            .values(status="archived")
        )
        session.commit()
    finally:
        session.close()
    archived = _activate(client, second["id"])
    assert archived.status_code == 409
    assert archived.json()["detail"]["code"] == "plan_archived"


def test_activation_rolls_back_when_audit_write_fails(evaluation_client, monkeypatch) -> None:
    client, session_factory, _ = evaluation_client
    plan = _create_plan(client)

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("injected audit failure")

    monkeypatch.setattr(EvaluationRunsService, "_write_audit", fail_audit)
    response = _activate(client, plan["id"])

    assert response.status_code == 500
    session = session_factory()
    try:
        status_value = session.execute(
            select(GovernanceEvaluationPlan.__table__.c.status).where(
                GovernanceEvaluationPlan.__table__.c.id == plan["id"]
            )
        ).scalar_one()
        assert status_value == "draft"
    finally:
        session.close()


def test_activation_rolls_back_when_response_read_fails(
    evaluation_client, monkeypatch
) -> None:
    client, session_factory, _ = evaluation_client
    plan = _create_plan(client)
    original_plan_row = EvaluationRunsService._plan_row
    read_count = 0

    def fail_second_plan_read(self, **kwargs):
        nonlocal read_count
        read_count += 1
        if read_count == 2:
            raise RuntimeError("injected response read failure")
        return original_plan_row(self, **kwargs)

    monkeypatch.setattr(EvaluationRunsService, "_plan_row", fail_second_plan_read)
    response = _activate(client, plan["id"])

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "evaluation_persistence_failed"
    session = session_factory()
    try:
        assert session.execute(
            select(GovernanceEvaluationPlan.__table__.c.status).where(
                GovernanceEvaluationPlan.__table__.c.id == plan["id"]
            )
        ).scalar_one() == "draft"
        assert _audit_actions(session_factory) == ["evaluation_plan.created"]
    finally:
        session.close()


@pytest.mark.parametrize("delivery_mode", ["external_provider", "imported_report"])
def test_preflight_and_run_preparation_are_honest_and_audited(
    evaluation_client, delivery_mode
) -> None:
    client, session_factory, _ = evaluation_client
    plan = _create_plan(client, deliveryMode=delivery_mode)
    assert _activate(client, plan["id"]).status_code == 200

    preflight = client.get(f"{_plans_url()}/{plan['id']}/preflight")
    created = _create_run(client, plan["id"], trigger="release_gate")

    assert preflight.status_code == 200
    assert preflight.json() == {
        "planId": plan["id"],
        "canPrepareRun": True,
        "fairmindExecutionAvailable": False,
        "code": "evidence_link_required",
        "message": "This plan requires evidence from its configured delivery source.",
        "nextAction": "Prepare the run, then link an exact Evidence Passport revision.",
    }
    assert created.status_code == 201, created.text
    run = created.json()
    assert run["technicalStatus"] == "awaiting_evidence"
    assert run["overallVerdict"] == "insufficient"
    assert run["layerVerdicts"] == {}
    assert run["trigger"] == "release_gate"
    assert _audit_actions(session_factory)[-1] == "evaluation_run.prepared"


@pytest.mark.parametrize("delivery_mode", ["external_provider", "imported_report"])
@pytest.mark.parametrize(
    ("plan_status", "message", "next_action"),
    [
        (
            "draft",
            "This evaluation plan is still a draft and cannot prepare runs.",
            "Activate the plan before preparing a run.",
        ),
        (
            "archived",
            "This evaluation plan is archived and cannot prepare runs.",
            "Create and activate a new versioned plan before preparing a run.",
        ),
    ],
)
def test_preflight_blocks_inactive_external_and_imported_plans(
    evaluation_client, delivery_mode, plan_status, message, next_action
) -> None:
    client, session_factory, _ = evaluation_client
    plan = _create_plan(client, deliveryMode=delivery_mode)
    if plan_status == "archived":
        session = session_factory()
        try:
            session.execute(
                update(GovernanceEvaluationPlan.__table__)
                .where(GovernanceEvaluationPlan.__table__.c.id == plan["id"])
                .values(status="archived")
            )
            session.commit()
        finally:
            session.close()

    response = client.get(f"{_plans_url()}/{plan['id']}/preflight")

    assert response.status_code == 200
    assert response.json() == {
        "planId": plan["id"],
        "canPrepareRun": False,
        "fairmindExecutionAvailable": False,
        "code": "evidence_link_required",
        "message": message,
        "nextAction": next_action,
    }


def test_unavailable_worker_cannot_create_run(evaluation_client) -> None:
    client, session_factory, _ = evaluation_client
    plan = _create_plan(client, deliveryMode="fairmind_worker")
    assert _activate(client, plan["id"]).status_code == 200

    preflight = client.get(f"{_plans_url()}/{plan['id']}/preflight")
    response = _create_run(client, plan["id"])

    assert preflight.status_code == 200
    assert preflight.json()["canPrepareRun"] is False
    assert preflight.json()["fairmindExecutionAvailable"] is False
    assert preflight.json()["code"] == "executor_unavailable"
    assert preflight.json()["nextAction"]
    assert response.status_code == 409
    assert response.json() == {
        "detail": {
            "code": "executor_unavailable",
            "message": "No FairMind worker is installed for this plan.",
            "nextAction": "Select an external provider or imported report, or install a compatible worker.",
        }
    }
    session = session_factory()
    try:
        assert session.execute(select(GovernanceEvaluationRun.__table__.c.id)).all() == []
    finally:
        session.close()


def test_inactive_plan_cannot_prepare_run_and_run_reads_do_not_leak(evaluation_client) -> None:
    client, _, active_user = evaluation_client
    plan = _create_plan(client)
    inactive = _create_run(client, plan["id"])
    assert inactive.status_code == 409
    assert inactive.json()["detail"]["code"] == "plan_inactive"
    assert _activate(client, plan["id"]).status_code == 200
    run = _create_run(client, plan["id"]).json()

    active_user["value"] = _token(USER_B)
    assert client.get(f"{BASE}/{ORG_B}/systems/system-b/evaluation-runs").json() == []
    assert client.get(f"{BASE}/{ORG_B}/systems/system-b/evaluation-runs/{run['id']}").status_code == 404
    active_user["value"] = _token(USER_A)
    listed = client.get(f"{BASE}/{ORG_A}/systems/system-a/evaluation-runs")
    detail = client.get(f"{BASE}/{ORG_A}/systems/system-a/evaluation-runs/{run['id']}")
    assert listed.status_code == detail.status_code == 200
    assert listed.json() == [detail.json()]


def test_run_preparation_rolls_back_when_audit_write_fails(evaluation_client, monkeypatch) -> None:
    client, session_factory, _ = evaluation_client
    plan = _create_plan(client)
    assert _activate(client, plan["id"]).status_code == 200

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("injected audit failure")

    monkeypatch.setattr(EvaluationRunsService, "_write_audit", fail_audit)
    response = _create_run(client, plan["id"])

    assert response.status_code == 500
    session = session_factory()
    try:
        assert session.execute(select(GovernanceEvaluationRun.__table__.c.id)).all() == []
    finally:
        session.close()


def test_run_preparation_rolls_back_when_response_read_fails(
    evaluation_client, monkeypatch
) -> None:
    client, session_factory, _ = evaluation_client
    plan = _create_plan(client)
    assert _activate(client, plan["id"]).status_code == 200

    def fail_response_read(*_args, **_kwargs):
        raise RuntimeError("injected response read failure")

    monkeypatch.setattr(EvaluationRunsService, "_run_row", fail_response_read)
    response = _create_run(client, plan["id"])

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "evaluation_persistence_failed"
    session = session_factory()
    try:
        assert session.execute(select(GovernanceEvaluationRun.__table__.c.id)).all() == []
        assert "evaluation_run.prepared" not in _audit_actions(session_factory)
    finally:
        session.close()


def _prepared_run(client: TestClient, **plan_overrides) -> tuple[dict, dict]:
    plan = _create_plan(client, **plan_overrides)
    assert _activate(client, plan["id"]).status_code == 200
    response = _create_run(client, plan["id"])
    assert response.status_code == 201, response.text
    return plan, response.json()


def _link(client: TestClient, run_id: str, evidence_run_id: str, revision_id: str):
    return client.post(
        f"{BASE}/{ORG_A}/systems/system-a/evaluation-runs/{run_id}/evidence-passport-link",
        json={"evidenceRunId": evidence_run_id, "passportRevisionId": revision_id},
    )


def test_passport_projection_includes_capability_result_and_diagnostics() -> None:
    snapshot = _passport_snapshot(
        result_status="error",
        error_code="provider_timeout",
        error_message="Provider timed out.",
    )

    projection = EvaluationRunsService._passport_projection(json.dumps(snapshot))

    assert projection == {
        "schemaVersion": "1.0.0",
        "targetKind": "model",
        "suiteRef": "fairmind/bias@2026.07",
        "capabilityState": "validated",
        "resultStatus": "error",
        "resultSummary": "Bounded error result.",
        "errorCode": "provider_timeout",
        "errorMessage": "Provider timed out.",
        "startedAt": "2026-07-18T00:00:00Z",
        "endedAt": "2026-07-18T00:05:00Z",
    }


def test_exact_passport_link_succeeds_idempotently_and_preserves_revision(evaluation_client) -> None:
    client, session_factory, _ = evaluation_client
    _, run = _prepared_run(client)
    snapshot = _passport_snapshot()
    original_json = _seed_passport(
        session_factory,
        evidence_run_id="evidence-a",
        revision_id="revision-a",
        snapshot=snapshot,
    )

    linked = _link(client, run["id"], "evidence-a", "revision-a")
    replay = _link(client, run["id"], "evidence-a", "revision-a")

    assert linked.status_code == replay.status_code == 200
    assert linked.json() == replay.json()
    result = linked.json()
    assert result["technicalStatus"] == "succeeded"
    assert result["overallVerdict"] == "review"
    assert result["layerVerdicts"] == {}
    assert result["linkedEvidenceRunId"] == "evidence-a"
    assert result["linkedPassportRevisionId"] == "revision-a"
    assert result["linkedBy"] == USER_A
    assert result["linkedAt"]
    assert result["startedAt"] == "2026-07-18T00:00:00Z"
    assert result["completedAt"] == "2026-07-18T00:05:00Z"
    assert _audit_actions(session_factory).count("evaluation_run.passport_linked") == 1
    session = session_factory()
    try:
        assert session.execute(
            select(GovernanceEvidencePassportRevision.__table__.c.snapshot_json).where(
                GovernanceEvidencePassportRevision.__table__.c.id == "revision-a"
            )
        ).scalar_one() == original_json
    finally:
        session.close()


@pytest.mark.parametrize(
    (
        "result_status",
        "capability_state",
        "technical_status",
        "overall_verdict",
        "failure_code",
        "failure_message",
    ),
    [
        ("passed", "validated", "succeeded", "review", None, None),
        (
            "passed_with_limitations",
            "validated",
            "succeeded",
            "review",
            None,
            None,
        ),
        ("failed", "validated", "succeeded", "review", None, None),
        ("informational", "metadata_only", "succeeded", "review", None, None),
        (
            "error",
            "validated",
            "failed",
            "insufficient",
            "provider_timeout",
            "Provider timed out.",
        ),
        (
            "unavailable",
            "unavailable",
            "failed",
            "insufficient",
            "passport_result_unavailable",
            "Bounded unavailable result.",
        ),
        (
            "insufficient_data",
            "insufficient_data",
            "failed",
            "insufficient",
            "passport_result_insufficient_data",
            "Bounded insufficient_data result.",
        ),
        (
            "unknown",
            "metadata_only",
            "failed",
            "insufficient",
            "passport_result_unknown",
            "Bounded unknown result.",
        ),
    ],
)
def test_passport_link_maps_every_result_status_truthfully(
    evaluation_client,
    result_status,
    capability_state,
    technical_status,
    overall_verdict,
    failure_code,
    failure_message,
) -> None:
    client, session_factory, _ = evaluation_client
    _, run = _prepared_run(client)
    snapshot = _passport_snapshot(
        capability_state=capability_state,
        result_status=result_status,
        error_code="provider_timeout" if result_status == "error" else None,
        error_message="Provider timed out." if result_status == "error" else None,
    )
    _seed_passport(
        session_factory,
        evidence_run_id="evidence-a",
        revision_id="revision-a",
        snapshot=snapshot,
    )

    response = _link(client, run["id"], "evidence-a", "revision-a")

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["technicalStatus"] == technical_status
    assert result["overallVerdict"] == overall_verdict
    assert result["failureCode"] == failure_code
    assert result["failureMessage"] == failure_message
    assert result["linkedEvidenceRunId"] == "evidence-a"
    assert result["linkedPassportRevisionId"] == "revision-a"


@pytest.mark.parametrize(
    ("plan_overrides", "snapshot_overrides", "code"),
    [
        ({}, {"suite_name": "FairMind Bias"}, "suite_mismatch"),
        ({}, {"suite_version": "2026.08"}, "suite_mismatch"),
        ({}, {"target_kind": "agent"}, "target_kind_mismatch"),
        ({"targetKind": "agent"}, {"target_kind": "model"}, "target_kind_mismatch"),
        ({"targetKind": "image_generator"}, {}, "target_kind_unverifiable"),
    ],
)
def test_passport_link_requires_exact_suite_and_verifiable_target(
    evaluation_client, plan_overrides, snapshot_overrides, code
) -> None:
    client, session_factory, _ = evaluation_client
    _, run = _prepared_run(client, **plan_overrides)
    snapshot = _passport_snapshot(**snapshot_overrides)
    _seed_passport(
        session_factory,
        evidence_run_id="evidence-a",
        revision_id="revision-a",
        snapshot=snapshot,
    )

    response = _link(client, run["id"], "evidence-a", "revision-a")

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == code
    detail = client.get(
        f"{BASE}/{ORG_A}/systems/system-a/evaluation-runs/{run['id']}"
    ).json()
    assert detail["technicalStatus"] == "awaiting_evidence"
    assert detail["overallVerdict"] == "insufficient"
    assert detail["linkedPassportRevisionId"] is None


@pytest.mark.parametrize(
    "snapshot_overrides",
    [
        {"org_id": ORG_B},
        {"workspace_id": "workspace-b"},
        {"system_id": "system-b"},
    ],
)
def test_passport_link_uses_relational_scope_instead_of_snapshot_display_scope(
    evaluation_client, snapshot_overrides
) -> None:
    client, session_factory, _ = evaluation_client
    _, run = _prepared_run(client)
    snapshot = _passport_snapshot(**snapshot_overrides)
    _seed_passport(
        session_factory,
        evidence_run_id="evidence-a",
        revision_id="revision-a",
        snapshot=snapshot,
    )

    response = _link(client, run["id"], "evidence-a", "revision-a")

    assert response.status_code == 200
    assert response.json()["technicalStatus"] == "succeeded"


def test_passport_link_rejects_wrong_evidence_revision_pair_and_conflicting_relink(
    evaluation_client,
) -> None:
    client, session_factory, _ = evaluation_client
    _, run = _prepared_run(client)
    _seed_passport(
        session_factory,
        evidence_run_id="evidence-a",
        revision_id="revision-a",
        snapshot=_passport_snapshot(),
    )
    _seed_passport(
        session_factory,
        evidence_run_id="evidence-b",
        revision_id="revision-b",
        snapshot=_passport_snapshot(),
    )

    mismatched = _link(client, run["id"], "evidence-b", "revision-a")
    assert mismatched.status_code == 422
    assert mismatched.json()["detail"]["code"] == "passport_scope_mismatch"
    assert _link(client, run["id"], "evidence-a", "revision-a").status_code == 200
    conflict = _link(client, run["id"], "evidence-b", "revision-b")
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "passport_link_conflict"


def test_passport_link_rolls_back_when_audit_write_fails(evaluation_client, monkeypatch) -> None:
    client, session_factory, _ = evaluation_client
    _, run = _prepared_run(client)
    _seed_passport(
        session_factory,
        evidence_run_id="evidence-a",
        revision_id="revision-a",
        snapshot=_passport_snapshot(),
    )

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("injected audit failure")

    monkeypatch.setattr(EvaluationRunsService, "_write_audit", fail_audit)
    response = _link(client, run["id"], "evidence-a", "revision-a")

    assert response.status_code == 500
    detail = client.get(
        f"{BASE}/{ORG_A}/systems/system-a/evaluation-runs/{run['id']}"
    ).json()
    assert detail["technicalStatus"] == "awaiting_evidence"
    assert detail["linkedPassportRevisionId"] is None


def test_passport_link_rolls_back_when_response_read_fails(
    evaluation_client, monkeypatch
) -> None:
    client, session_factory, _ = evaluation_client
    _, run = _prepared_run(client)
    _seed_passport(
        session_factory,
        evidence_run_id="evidence-a",
        revision_id="revision-a",
        snapshot=_passport_snapshot(),
    )
    original_run_row = EvaluationRunsService._run_row
    read_count = 0

    def fail_second_run_read(self, **kwargs):
        nonlocal read_count
        read_count += 1
        if read_count == 2:
            raise RuntimeError("injected response read failure")
        return original_run_row(self, **kwargs)

    monkeypatch.setattr(EvaluationRunsService, "_run_row", fail_second_run_read)
    response = _link(client, run["id"], "evidence-a", "revision-a")

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "evaluation_persistence_failed"
    session = session_factory()
    try:
        stored = session.execute(
            select(GovernanceEvaluationRun.__table__).where(
                GovernanceEvaluationRun.__table__.c.id == run["id"]
            )
        ).mappings().one()
        assert stored["technical_status"] == "awaiting_evidence"
        assert stored["linked_passport_revision_id"] is None
        assert "evaluation_run.passport_linked" not in _audit_actions(session_factory)
    finally:
        session.close()


def test_passport_link_rejects_invalid_canonical_snapshot_without_mutating_run(
    evaluation_client,
) -> None:
    client, session_factory, _ = evaluation_client
    _, run = _prepared_run(client)
    _seed_passport(
        session_factory,
        evidence_run_id="evidence-a",
        revision_id="revision-a",
        snapshot=_passport_snapshot(),
        snapshot_json_override='{"schemaVersion":"1.0.0"}',
    )

    response = _link(client, run["id"], "evidence-a", "revision-a")

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "passport_snapshot_invalid"
    detail = client.get(
        f"{BASE}/{ORG_A}/systems/system-a/evaluation-runs/{run['id']}"
    ).json()
    assert detail["technicalStatus"] == "awaiting_evidence"
    assert detail["linkedPassportRevisionId"] is None


def test_passport_link_rejects_unsupported_passport_contract_version_without_mutation(
    evaluation_client,
) -> None:
    client, session_factory, _ = evaluation_client
    _, run = _prepared_run(client)
    snapshot = _passport_snapshot()
    snapshot["schemaVersion"] = "1.1.0"
    _seed_passport(
        session_factory,
        evidence_run_id="evidence-a",
        revision_id="revision-a",
        snapshot=snapshot,
    )

    response = _link(client, run["id"], "evidence-a", "revision-a")

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "passport_snapshot_invalid"
    detail = client.get(
        f"{BASE}/{ORG_A}/systems/system-a/evaluation-runs/{run['id']}"
    ).json()
    assert detail["technicalStatus"] == "awaiting_evidence"
    assert detail["linkedPassportRevisionId"] is None


def test_two_sessions_atomically_link_only_one_distinct_passport_revision(tmp_path: Path) -> None:
    database_path = tmp_path / "evaluation-race.sqlite3"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )

    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys = ON")
        dbapi_connection.execute("PRAGMA journal_mode = WAL")

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    seed = factory()
    try:
        _seed_org(seed, ORG_A, USER_A)
        _seed_system(seed, org_id=ORG_A, workspace_id="workspace-a", system_id="system-a")
        service = EvaluationRunsService(seed)
        plan = service.create_plan(
            org_id=ORG_A,
            system_id="system-a",
            actor_id=USER_A,
            payload=_plan_payload(),
        )
        service.activate_plan(
            org_id=ORG_A,
            system_id="system-a",
            plan_id=plan["id"],
            actor_id=USER_A,
        )
        run = service.create_run(
            org_id=ORG_A,
            system_id="system-a",
            plan_id=plan["id"],
            actor_id=USER_A,
            trigger="manual",
        )
    finally:
        seed.close()
    _seed_passport(
        factory,
        evidence_run_id="evidence-a",
        revision_id="revision-a",
        snapshot=_passport_snapshot(),
    )
    _seed_passport(
        factory,
        evidence_run_id="evidence-b",
        revision_id="revision-b",
        snapshot=_passport_snapshot(),
    )

    def attempt(pair: tuple[str, str]) -> tuple[str, str]:
        session = factory()
        try:
            result = EvaluationRunsService(session).link_passport_revision(
                org_id=ORG_A,
                system_id="system-a",
                run_id=run["id"],
                evidence_run_id=pair[0],
                passport_revision_id=pair[1],
                actor_id=USER_A,
            )
            return "linked", result["linkedPassportRevisionId"]
        except EvaluationWorkflowError as error:
            return error.code, pair[1]
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(
            executor.map(attempt, [("evidence-a", "revision-a"), ("evidence-b", "revision-b")])
        )

    assert sorted(outcome[0] for outcome in outcomes) == ["linked", "passport_link_conflict"]
    winner = next(value for status_value, value in outcomes if status_value == "linked")
    verify = factory()
    try:
        stored = verify.execute(
            select(GovernanceEvaluationRun.__table__).where(
                GovernanceEvaluationRun.__table__.c.id == run["id"]
            )
        ).mappings().one()
        assert stored["linked_passport_revision_id"] == winner
        assert verify.execute(
            select(OrganizationAuditLog.__table__.c.id).where(
                OrganizationAuditLog.__table__.c.action == "evaluation_run.passport_linked"
            )
        ).all().__len__() == 1
    finally:
        verify.close()
        engine.dispose()
