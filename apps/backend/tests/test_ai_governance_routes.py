"""Tests for AI Governance phase-1 routes."""

from datetime import datetime, timedelta, timezone
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from config.auth import TokenData, TokenType, UserRole, get_current_active_user
from database.connection import Base, get_db
from database.models import Organization, OrganizationMember, User


client = TestClient(app)


@pytest.fixture(autouse=True)
def authenticated_org_database():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    user_id, org_id = uuid.uuid4(), uuid.uuid4()
    session = session_factory()
    session.execute(
        User.__table__.insert().values(
            id=user_id, email="governance@example.test", username="governance-owner"
        )
    )
    session.execute(
        Organization.__table__.insert().values(
            id=org_id,
            name="Governance test organization",
            slug=f"governance-{org_id}",
            owner_id=user_id,
        )
    )
    session.execute(
        OrganizationMember.__table__.insert().values(
            id=uuid.uuid4(),
            org_id=org_id,
            user_id=user_id,
            role="owner",
            status="active",
        )
    )
    session.commit()
    session.close()

    def override_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    async def override_user():
        now = datetime.now(timezone.utc)
        return TokenData(
            user_id=str(user_id),
            email="governance@example.test",
            role=UserRole.ADMIN,
            token_type=TokenType.ACCESS,
            iat=now,
            exp=now + timedelta(hours=1),
            permissions=["*"],
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_active_user] = override_user
    try:
        yield {
            "session_factory": session_factory,
            "org_id": str(org_id),
            "override_user": override_user,
        }
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _scope_system(test_context, system_id: str) -> None:
    session = test_context["session_factory"]()
    session.execute(
        text("UPDATE governance_ai_systems SET org_id = :org_id WHERE id = :system_id"),
        {"org_id": test_context["org_id"], "system_id": system_id},
    )
    session.commit()
    session.close()


def _create_scoped_system(test_context, name: str) -> str:
    workspace = client.post(
        "/api/v1/ai-governance/workspaces",
        json={"name": f"{name} workspace", "owner": "governance@example.test"},
    )
    system = client.post(
        "/api/v1/ai-governance/systems",
        json={
            "workspace_id": workspace.json()["id"],
            "name": name,
            "owner": "governance@example.test",
            "risk_tier": "high",
            "lifecycle_stage": "onboard",
            "metadata": {},
        },
    )
    system_id = system.json()["id"]
    _scope_system(test_context, system_id)
    return system_id


def test_ai_governance_frameworks_endpoint():
    response = client.get("/api/v1/ai-governance/compliance/frameworks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item["id"] == "eu_ai_act" for item in data)


def test_ai_governance_workspace_and_system_registry():
    workspace_resp = client.post(
        "/api/v1/ai-governance/workspaces",
        json={
            "name": f"Acme Workspace {uuid.uuid4().hex[:6]}",
            "owner": "owner@acme.ai",
        },
    )
    assert workspace_resp.status_code == 200
    workspace = workspace_resp.json()
    assert workspace["name"].startswith("Acme Workspace")

    system_resp = client.post(
        "/api/v1/ai-governance/systems",
        json={
            "workspace_id": workspace["id"],
            "name": "Acme Credit Underwriting",
            "owner": "risk-ml@acme.ai",
            "risk_tier": "high",
            "lifecycle_stage": "onboard",
            "metadata": {"region": "us", "model_type": "tabular"},
        },
    )
    assert system_resp.status_code == 200
    system = system_resp.json()
    assert system["workspaceId"] == workspace["id"]
    assert system["riskTier"] == "high"
    assert system["lifecycleStage"] == "onboard"
    assert system["metadata"]["region"] == "us"

    workspace_list = client.get("/api/v1/ai-governance/workspaces")
    assert workspace_list.status_code == 200
    assert any(item["id"] == workspace["id"] for item in workspace_list.json())

    system_list = client.get(f"/api/v1/ai-governance/systems?workspace_id={workspace['id']}")
    assert system_list.status_code == 200
    systems = system_list.json()
    assert any(item["id"] == system["id"] for item in systems)

    get_system = client.get(f"/api/v1/ai-governance/systems/{system['id']}")
    assert get_system.status_code == 200
    fetched_system = get_system.json()
    assert fetched_system["id"] == system["id"]
    assert fetched_system["workspaceId"] == workspace["id"]
    assert "readiness" in fetched_system
    assert "lifecycleSummary" in fetched_system
    assert fetched_system["lifecycleSummary"]["stage"] == fetched_system["lifecycleStage"]


def test_ai_governance_lifecycle_summary_persists_stage_progression(authenticated_org_database):
    workspace_resp = client.post(
        "/api/v1/ai-governance/workspaces",
        json={
            "name": f"Lifecycle Workspace {uuid.uuid4().hex[:6]}",
            "owner": "owner@acme.ai",
        },
    )
    workspace = workspace_resp.json()

    system_resp = client.post(
        "/api/v1/ai-governance/systems",
        json={
            "workspace_id": workspace["id"],
            "name": "Lifecycle Test System",
            "owner": "risk@acme.ai",
            "risk_tier": "high",
            "lifecycle_stage": "onboard",
            "metadata": {},
        },
    )
    system = system_resp.json()
    system_id = system["id"]
    _scope_system(authenticated_org_database, system_id)

    initial_summary = client.get(f"/api/v1/ai-governance/lifecycle/{system_id}/summary")
    assert initial_summary.status_code == 200
    assert initial_summary.json()["stage"] == "onboard"

    risk_resp = client.post(
        "/api/v1/ai-governance/risks/assess",
        json={
            "systemId": system_id,
            "riskType": "bias",
            "severity": "high",
            "description": "Approval disparity detected.",
        },
    )
    assert risk_resp.status_code == 200

    govern_summary = client.get(f"/api/v1/ai-governance/lifecycle/{system_id}/summary")
    assert govern_summary.status_code == 200
    assert govern_summary.json()["stage"] == "govern"

    persisted_govern = client.get(f"/api/v1/ai-governance/systems/{system_id}")
    assert persisted_govern.status_code == 200
    assert persisted_govern.json()["lifecycleStage"] == "govern"

    remediation_resp = client.post(
        "/api/v1/ai-governance/remediation",
        json={
            "system_id": system_id,
            "title": "Fix fairness threshold",
            "description": "Adjust threshold and rerun validation.",
            "source_type": "risk",
            "source_id": "risk-1",
            "linked_risk_ids": ["risk-1"],
            "owner": "ml@example.com",
            "priority": "high",
            "retest_required": True,
            "notes": "Queued.",
        },
    )
    assert remediation_resp.status_code == 200

    remediate_summary = client.get(f"/api/v1/ai-governance/lifecycle/{system_id}/summary")
    assert remediate_summary.status_code == 200
    assert remediate_summary.json()["stage"] == "remediate"

    approval_req = client.post(
        f"/api/v1/ai-governance/approval/system/{system_id}/request",
        json={"requested_by": "owner@fairmind.ai"},
    )
    assert approval_req.status_code == 200
    request_id = approval_req.json()["request"]["id"]

    environmental_resp = client.post(
        "/api/v1/ai-governance/environment/assess",
        json={
            "system_id": system_id,
            "assessment": {
                "boundary_json": {"scope": "release gate"},
                "lifecycle_phase": "training",
                "functional_unit": "one run",
                "metrics": {
                    "total_kwh": 1200.0,
                    "total_kg_co2e_location": 12_000.0,
                    "total_kg_co2e_market": 9_000.0,
                    "kg_co2e_per_1m_tokens": 5.0,
                },
                "measurement_source": "hardware_telemetry",
                "provenance_class": "measured",
                "uncertainty_pct": 8.0,
                "confidence_score": 0.92,
                "mitigation_readiness": "documented",
                "mitigations_json": [
                    {
                        "description": "Shift next run to a lower-carbon region.",
                        "target_date": "2026-12-31",
                    }
                ],
            },
        },
    )
    assert environmental_resp.status_code == 200

    approval_decision = client.post(
        f"/api/v1/ai-governance/approval-requests/{request_id}/decision",
        json={
            "decision": "approved",
            "notes": "Gate cleared.",
            "decided_by": "approver@fairmind.ai",
        },
    )
    assert approval_decision.status_code == 200

    operate_summary = client.get(f"/api/v1/ai-governance/lifecycle/{system_id}/summary")
    assert operate_summary.status_code == 200
    assert operate_summary.json()["stage"] == "operate"
    assert operate_summary.json()["approvalStatus"] == "approved"

    persisted_operate = client.get(f"/api/v1/ai-governance/systems/{system_id}")
    assert persisted_operate.status_code == 200
    assert persisted_operate.json()["lifecycleStage"] == "operate"


def test_ai_governance_policy_create_and_list():
    create_resp = client.post(
        "/api/v1/ai-governance/policies",
        json={
            "name": "Model Transparency Policy",
            "framework": "eu_ai_act",
            "description": "Ensure explainability artifacts exist",
            "rules": [{"id": "R1", "text": "publish model card"}],
        },
    )
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["name"] == "Model Transparency Policy"
    assert created["status"] == "draft"

    list_resp = client.get("/api/v1/ai-governance/policies?framework=eu_ai_act")
    assert list_resp.status_code == 200
    policies = list_resp.json()
    assert any(p["id"] == created["id"] for p in policies)


def test_ai_governance_workflow_and_request_decision(authenticated_org_database):
    system_id = _create_scoped_system(authenticated_org_database, "Workflow decision system")
    workflow_resp = client.post(
        "/api/v1/ai-governance/approval-workflows",
        json={
            "name": "AI System Approval Flow",
            "entity_type": "ai_system",
            "steps": [{"order": 1, "role": "reviewer"}, {"order": 2, "role": "approver"}],
        },
    )
    assert workflow_resp.status_code == 200
    workflow = workflow_resp.json()

    request_resp = client.post(
        f"/api/v1/ai-governance/approval-workflows/{workflow['id']}/requests",
        json={
            "entity_type": "ai_system",
            "entity_id": system_id,
            "requested_by": "qa@fairmind.ai",
        },
    )
    assert request_resp.status_code == 200
    approval_request = request_resp.json()
    assert approval_request["status"] == "pending"

    decision_resp = client.post(
        f"/api/v1/ai-governance/approval-requests/{approval_request['id']}/decision",
        json={
            "decision": "rejected",
            "notes": "Evidence gap remains",
            "decided_by": "approver@fairmind.ai",
        },
    )
    assert decision_resp.status_code == 200
    decision = decision_resp.json()
    assert decision["status"] == "rejected"

    get_request_resp = client.get(
        f"/api/v1/ai-governance/approval-requests/{approval_request['id']}"
    )
    assert get_request_resp.status_code == 200
    request_data = get_request_resp.json()
    assert request_data["id"] == approval_request["id"]
    assert request_data["status"] == "rejected"
    assert request_data["decision_notes"] == "Evidence gap remains"

    decisions_resp = client.get(
        f"/api/v1/ai-governance/approval-requests/{approval_request['id']}/decisions"
    )
    assert decisions_resp.status_code == 200
    trail = decisions_resp.json()
    assert len(trail) >= 1
    assert trail[-1]["decision"] == "rejected"
    assert trail[-1]["notes"] == "Evidence gap remains"
    assert trail[-1]["decided_by"] == "governance@example.test"


def test_ai_governance_system_approval_request_flow(authenticated_org_database):
    system_id = _create_scoped_system(authenticated_org_database, "System approval flow")

    initial_resp = client.get(f"/api/v1/ai-governance/approval/system/{system_id}")
    assert initial_resp.status_code == 200
    initial_payload = initial_resp.json()
    assert initial_payload["systemId"] == system_id
    assert initial_payload["request"] is None

    create_resp = client.post(
        f"/api/v1/ai-governance/approval/system/{system_id}/request",
        json={"requested_by": "owner@fairmind.ai"},
    )
    assert create_resp.status_code == 200
    created_payload = create_resp.json()
    assert created_payload["request"]["entity_type"] == "ai_system"
    assert created_payload["request"]["entity_id"] == system_id
    assert created_payload["request"]["status"] == "pending"

    list_resp = client.get(
        f"/api/v1/ai-governance/approval-requests?entity_type=ai_system&entity_id={system_id}"
    )
    assert list_resp.status_code == 200
    request_list = list_resp.json()
    assert len(request_list) == 1
    request_id = request_list[0]["id"]

    decision_resp = client.post(
        f"/api/v1/ai-governance/approval-requests/{request_id}/decision",
        json={
            "decision": "rejected",
            "notes": "Release evidence is incomplete.",
            "decided_by": "approver@fairmind.ai",
        },
    )
    assert decision_resp.status_code == 200
    assert decision_resp.json()["status"] == "rejected"

    latest_resp = client.get(f"/api/v1/ai-governance/approval/system/{system_id}")
    assert latest_resp.status_code == 200
    latest_payload = latest_resp.json()
    assert latest_payload["request"]["status"] == "rejected"
    assert latest_payload["request"]["decision_notes"] == "Release evidence is incomplete."
    assert latest_payload["decisions"][-1]["decision"] == "rejected"


def test_ai_governance_evidence_endpoints_require_authentication(authenticated_org_database):
    system_id = f"model-abc-{uuid.uuid4().hex[:8]}"
    app.dependency_overrides.pop(get_current_active_user)
    try:
        collect_resp = client.post(
            "/api/v1/ai-governance/evidence/collect",
            json={
                "system_id": system_id,
                "type": "audit_log",
                "content": {"entries": 12},
                "confidence": 0.93,
                "metadata": {"source": "monitoring"},
            },
        )
        assert collect_resp.status_code == 401
        assert client.get(f"/api/v1/ai-governance/evidence-v2/{system_id}").status_code == 401
        assert client.get(f"/api/v1/ai-governance/evidence/{system_id}/summary").status_code == 401
        assert client.post(
            f"/api/v1/ai-governance/systems/{system_id}/evidence",
            json={"evidence_type": "policy", "content": {}},
        ).status_code == 401
    finally:
        app.dependency_overrides[get_current_active_user] = authenticated_org_database[
            "override_user"
        ]


def test_ai_governance_risk_dashboard_and_assessment():
    dashboard_resp = client.get("/api/v1/ai-governance/dashboard/risk?system_id=acme-credit")
    assert dashboard_resp.status_code == 200
    dashboard = dashboard_resp.json()
    assert "risks" in dashboard
    assert "summary" in dashboard
    assert isinstance(dashboard["risks"], list)

    create_resp = client.post(
        "/api/v1/ai-governance/risks/assess",
        json={
            "systemId": "acme-credit",
            "riskType": "bias",
            "severity": "high",
            "description": "Approval disparity detected for older applicants.",
        },
    )
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["systemId"] == "acme-credit"
    assert created["severity"] == "high"
    assert created["source"] == "manual_assessment"
    assert isinstance(created["automation"]["recommendedRisks"], list)

    refreshed_resp = client.get("/api/v1/ai-governance/dashboard/risk?system_id=acme-credit")
    assert refreshed_resp.status_code == 200
    refreshed = refreshed_resp.json()
    assert any(risk["id"] == created["id"] for risk in refreshed["risks"])


def test_ai_governance_remediation_task_loop():
    system_id = f"acme-remediation-{uuid.uuid4().hex[:8]}"
    create_resp = client.post(
        "/api/v1/ai-governance/remediation",
        json={
            "system_id": system_id,
            "title": "Close fairness gaps in approval flow",
            "description": "Rebalance thresholds and rerun validation before sign-off.",
            "source_type": "risk",
            "source_id": "risk-123",
            "linked_risk_ids": ["risk-123", "risk-456"],
            "owner": "ml@example.com",
            "priority": "high",
            "due_date": "2026-03-31",
            "retest_required": True,
            "notes": "Initial triage completed.",
        },
    )
    assert create_resp.status_code == 200
    task = create_resp.json()
    assert task["systemId"] == system_id
    assert task["sourceType"] == "risk"
    assert task["sourceId"] == "risk-123"
    assert task["linkedRiskIds"] == ["risk-123", "risk-456"]
    assert task["status"] == "open"
    assert task["retestRequired"] is True
    assert task["retestStatus"] == "not_started"

    list_resp = client.get(f"/api/v1/ai-governance/remediation?system_id={system_id}")
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert payload["summary"]["systemId"] == system_id
    assert payload["summary"]["totalTasks"] == 1
    assert payload["summary"]["activeTasks"] == 1
    assert payload["summary"]["retestRequiredTasks"] == 1
    assert payload["summary"]["linkedRiskRefs"] == 2
    assert payload["summary"]["byPriority"]["high"] == 1
    assert payload["summary"]["byStatus"]["open"] == 1
    assert payload["tasks"][0]["id"] == task["id"]

    update_resp = client.patch(
        f"/api/v1/ai-governance/remediation/{task['id']}",
        json={
            "status": "ready_for_retest",
            "notes": "Fixed threshold drift; queued for validation rerun.",
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["id"] == task["id"]
    assert updated["status"] == "ready_for_retest"
    assert updated["notes"] == "Fixed threshold drift; queued for validation rerun."

    refreshed_list = client.get(f"/api/v1/ai-governance/remediation?system_id={system_id}")
    assert refreshed_list.status_code == 200
    refreshed_payload = refreshed_list.json()
    assert refreshed_payload["summary"]["totalTasks"] == 1
    assert refreshed_payload["summary"]["activeTasks"] == 1
    assert refreshed_payload["summary"]["byStatus"]["ready_for_retest"] == 1
    assert refreshed_payload["tasks"][0]["status"] == "ready_for_retest"
    assert refreshed_payload["tasks"][0]["notes"] == "Fixed threshold drift; queued for validation rerun."
