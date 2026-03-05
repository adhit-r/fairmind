"""Tests for AI Governance phase-1 routes."""

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_ai_governance_frameworks_endpoint():
    response = client.get("/api/v1/ai-governance/compliance/frameworks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item["id"] == "eu_ai_act" for item in data)


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


def test_ai_governance_evidence_collect_and_list():
    collect_resp = client.post(
        "/api/v1/ai-governance/evidence/collect",
        json={
            "system_id": "model-abc",
            "type": "audit_log",
            "content": {"entries": 12},
            "confidence": 0.93,
            "metadata": {"source": "monitoring"},
        },
    )
    assert collect_resp.status_code == 200
    evidence = collect_resp.json()

    list_resp = client.get("/api/v1/ai-governance/evidence/model-abc")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(item["id"] == evidence["id"] for item in items)

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
