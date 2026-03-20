"""Tests for AI Governance phase-1 routes."""

import uuid

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


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


def test_ai_governance_lifecycle_summary_persists_stage_progression():
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


def test_ai_governance_workflow_and_request_decision():
    workflow_resp = client.post(
        "/api/v1/ai-governance/approval-workflows",
        json={
            "name": "Policy Approval Flow",
            "entity_type": "policy",
            "steps": [{"order": 1, "role": "reviewer"}, {"order": 2, "role": "approver"}],
        },
    )
    assert workflow_resp.status_code == 200
    workflow = workflow_resp.json()

    request_resp = client.post(
        f"/api/v1/ai-governance/approval-workflows/{workflow['id']}/requests",
        json={
            "entity_type": "policy",
            "entity_id": "policy-123",
            "requested_by": "qa@fairmind.ai",
        },
    )
    assert request_resp.status_code == 200
    approval_request = request_resp.json()
    assert approval_request["status"] == "pending"

    decision_resp = client.post(
        f"/api/v1/ai-governance/approval-requests/{approval_request['id']}/decision",
        json={
            "decision": "approved",
            "notes": "Looks good",
            "decided_by": "approver@fairmind.ai",
        },
    )
    assert decision_resp.status_code == 200
    decision = decision_resp.json()
    assert decision["status"] == "approved"

    get_request_resp = client.get(
        f"/api/v1/ai-governance/approval-requests/{approval_request['id']}"
    )
    assert get_request_resp.status_code == 200
    request_data = get_request_resp.json()
    assert request_data["id"] == approval_request["id"]
    assert request_data["status"] == "approved"
    assert request_data["decision_notes"] == "Looks good"

    decisions_resp = client.get(
        f"/api/v1/ai-governance/approval-requests/{approval_request['id']}/decisions"
    )
    assert decisions_resp.status_code == 200
    trail = decisions_resp.json()
    assert len(trail) >= 1
    assert trail[-1]["decision"] == "approved"
    assert trail[-1]["notes"] == "Looks good"
    assert trail[-1]["decided_by"] == "approver@fairmind.ai"


def test_ai_governance_system_approval_request_flow():
    system_id = f"acme-approval-{uuid.uuid4().hex[:8]}"

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
            "decision": "approved",
            "notes": "Gate cleared for release.",
            "decided_by": "approver@fairmind.ai",
        },
    )
    assert decision_resp.status_code == 200
    assert decision_resp.json()["status"] == "approved"

    latest_resp = client.get(f"/api/v1/ai-governance/approval/system/{system_id}")
    assert latest_resp.status_code == 200
    latest_payload = latest_resp.json()
    assert latest_payload["request"]["status"] == "approved"
    assert latest_payload["request"]["decision_notes"] == "Gate cleared for release."
    assert latest_payload["decisions"][-1]["decision"] == "approved"


def test_ai_governance_evidence_collect_and_list():
    system_id = f"model-abc-{uuid.uuid4().hex[:8]}"
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
    assert collect_resp.status_code == 200
    evidence = collect_resp.json()
    assert evidence["workflowState"] == "collected"
    assert evidence["linkedEntityCount"] == 0
    assert evidence["metadataSummary"]["source"] == "monitoring"

    list_resp = client.get(f"/api/v1/ai-governance/evidence/{system_id}")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(item["id"] == evidence["id"] for item in items)
    listed = next(item for item in items if item["id"] == evidence["id"])
    assert listed["metadataSummary"]["source"] == "monitoring"
    assert listed["workflowState"] == "collected"
    assert listed["linkedEntityCount"] == 0

    link_resp = client.post(
        "/api/v1/ai-governance/evidence/collections",
        json={
            "evidence_id": evidence["id"],
            "entity_type": "policy",
            "entity_id": "policy-xyz",
        },
    )
    assert link_resp.status_code == 200
    link_data = link_resp.json()
    assert link_data["evidence_id"] == evidence["id"]

    summary_resp = client.get(f"/api/v1/ai-governance/evidence/{system_id}/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["systemId"] == system_id
    assert summary["totalEvidence"] == 1
    assert summary["linkedEvidence"] == 1
    assert summary["decisionReadiness"] == "review_ready"
    assert summary["workflowState"] == "review_ready"
    assert summary["metadataSources"][0]["source"] == "monitoring"


def test_ai_governance_risk_dashboard_and_assessment():
    dashboard_resp = client.get("/api/v1/ai-governance/dashboard/risk?system_id=acme-credit")
    assert dashboard_resp.status_code == 200
    dashboard = dashboard_resp.json()
    assert "risks" in dashboard
    assert "summary" in dashboard
    assert len(dashboard["risks"]) >= 1

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
    assert len(created["automation"]["recommendedRisks"]) >= 1

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
