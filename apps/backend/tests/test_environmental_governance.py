"""FairMind-E environmental governance API and gate tests."""

import uuid

from fastapi.testclient import TestClient

from src.domain.environmental import run_assessment


def _set_low_tier(fixture, system_id: str) -> None:
    """The org-scoped create route ignores risk_tier; a low tier lets the release gate read conditional go so the environmental rule is what blocks."""
    from sqlalchemy import text

    with fixture.session_factory() as session:
        session.execute(text("UPDATE governance_ai_systems SET risk_tier = 'low' WHERE id = :id"), {"id": system_id})
        session.commit()


def _create_system(client: TestClient, org_id: str) -> str:
    workspace_resp = client.post(
        f"/api/v1/ai-governance/organizations/{org_id}/workspaces",
        json={
            "name": f"FairMind-E Workspace {uuid.uuid4().hex[:8]}",
            "owner": "owner@fairmind.ai",
        },
    )
    assert workspace_resp.status_code == 201, workspace_resp.text
    workspace = workspace_resp.json()
    system_resp = client.post(
        f"/api/v1/ai-governance/organizations/{org_id}/systems",
        json={
            "workspace_id": workspace["id"],
            "name": f"FairMind-E System {uuid.uuid4().hex[:8]}",
            "owner": "ml@fairmind.ai",
            "risk_tier": "high",
            "lifecycle_stage": "govern",
            "metadata": {},
        },
    )
    assert system_resp.status_code == 201, system_resp.text
    return system_resp.json()["id"]


def _assessment(**overrides):
    payload = {
        "boundary_json": {"scope": "training", "region": "us-east-1"},
        "lifecycle_phase": "training",
        "functional_unit": "one training run",
        "impact_type": "carbon",
        "metrics": {
            "total_kwh": 1200.0,
            "total_kg_co2e_location": 12_000.0,
            "total_kg_co2e_market": 9_000.0,
            "kg_co2e_per_1m_tokens": 5.0,
        },
        "measurement_source": "nvidia-smi",
        "provenance_class": "measured",
        "uncertainty_pct": 8.0,
        "confidence_score": 0.92,
        "mitigation_readiness": "documented",
        "mitigations_json": [
            {
                "description": "Shift the next run to the lowest-carbon region.",
                "target_date": "2026-12-31",
                "owner": "platform",
            }
        ],
    }
    payload.update(overrides)
    return payload


def _environmental_base(org_id: str, system_id: str) -> str:
    return (
        f"/api/v1/ai-governance/organizations/{org_id}/systems/{system_id}"
        "/environmental-impact"
    )


def test_domain_import_and_environmental_gate_invariants():
    measured = run_assessment(_assessment())
    assert measured.recommendation == "conditional_go"
    assert measured.approval_blocking is False

    unknown = run_assessment(
        _assessment(
            metrics={
                "total_kwh": 120.0,
                "total_kg_co2e_location": 500.0,
                "total_kg_co2e_market": 500.0,
                "kg_co2e_per_1m_tokens": 1.0,
            },
            provenance_class="unknown",
            confidence_score=0.50,
            mitigation_readiness="missing",
            mitigations_json=[],
        )
    )
    assert unknown.evidence_confidence == 0.0
    assert unknown.recommendation == "no_go"

    vendor = run_assessment(
        _assessment(
            lifecycle_phase="inference",
            metrics={
                "total_kwh": 8.0,
                "total_kg_co2e_location": 2.0,
                "total_kg_co2e_market": 2.0,
                "kg_co2e_per_1000_requests": 0.0005,
            },
            provenance_class="vendor_reported",
            confidence_score=0.95,
            mitigation_readiness="missing",
            mitigations_json=[],
        )
    )
    assert vendor.evidence_confidence == 0.60

    no_offsets = run_assessment(_assessment(mitigation_readiness="planned", mitigations_json=[]))
    with_offsets = run_assessment(
        {
            **_assessment(mitigation_readiness="planned", mitigations_json=[]),
            "offsets_json": {"rec_mwh": 100, "offset_kg_co2e": 12_000},
        }
    )
    assert with_offsets.evidence_confidence == no_offsets.evidence_confidence
    assert with_offsets.impact_tier == no_offsets.impact_tier
    assert with_offsets.recommendation == no_offsets.recommendation


def test_assessment_post_appends_versions_and_mirrors_evidence(environmental_governance_client):
    client, org_id = environmental_governance_client
    system_id = _create_system(client, org_id)
    base = _environmental_base(org_id, system_id)
    first = client.post(
        f"{base}/assess",
        json={"assessment": _assessment()},
    )
    assert first.status_code == 200
    first_payload = first.json()
    assert first_payload["version"] == 1
    assert first_payload["recommendation"] == "conditional_go"
    assert first_payload["evidence_id"]

    second = client.post(
        f"{base}/assess",
        json={"assessment": _assessment(confidence_score=0.90)},
    )
    assert second.status_code == 200
    assert second.json()["version"] == 2
    assert second.json()["assessment_id"] != first_payload["assessment_id"]

    latest = client.get(base)
    assert latest.status_code == 200
    data = latest.json()["data"]
    assert data["latest"]["version"] == 2
    assert [item["version"] for item in data["versionTrail"]][:2] == [2, 1]
    assert data["latest"]["evidenceId"] == second.json()["evidence_id"]


def test_evidence_ingest_creates_no_go_risk_remediation_and_blocks_approval(
    environmental_governance_client,
):
    client, org_id = environmental_governance_client
    system_id = _create_system(client, org_id)
    _set_low_tier(environmental_governance_client, system_id)
    ingest = client.post(
        f"{_environmental_base(org_id, system_id)}/evidence",
        json={
            "connector_type": "codecarbon_csv",
            "content": "energy_consumed,emissions\n10,500\n",
            "assessment": {
                "boundary_json": {"scope": "training"},
                "lifecycle_phase": "training",
                "functional_unit": "one run",
                "provenance_class": "unknown",
                "confidence_score": 0.4,
                "uncertainty_pct": 40.0,
            },
        },
    )
    assert ingest.status_code == 200
    saved = ingest.json()["data"]
    assert saved["recommendation"] == "no_go"
    assert saved["riskId"]
    assert saved["remediationTaskId"]

    approval_req = client.post(
        f"/api/v1/ai-governance/approval/system/{system_id}/request",
        json={"requested_by": "owner@fairmind.ai"},
    )
    assert approval_req.status_code == 200
    request_id = approval_req.json()["request"]["id"]
    decision = client.post(
        f"/api/v1/ai-governance/approval-requests/{request_id}/decision",
        json={
            "decision": "approved",
            "notes": "Attempting release.",
            "decided_by": "approver@fairmind.ai",
        },
    )
    assert decision.status_code == 409
    assert decision.json()["detail"]["environmentalGate"]["code"] == "environmental_no_go"


def test_approval_blocks_missing_environmental_evidence_for_registered_system(
    environmental_governance_client,
):
    client, org_id = environmental_governance_client
    system_id = _create_system(client, org_id)
    _set_low_tier(environmental_governance_client, system_id)
    approval_req = client.post(
        f"/api/v1/ai-governance/approval/system/{system_id}/request",
        json={"requested_by": "owner@fairmind.ai"},
    )
    # Any evidence on file lifts the gate off no go, so the missing environmental assessment is what blocks.
    attested = client.post(
        f"/api/v1/ai-governance/systems/{system_id}/attestations",
        json={"check": "data_governance", "statement": "Training data comes from the licensed 2024 corpus."},
    )
    assert attested.status_code == 200, attested.text
    assert approval_req.status_code == 200
    decision = client.post(
        f"/api/v1/ai-governance/approval-requests/{approval_req.json()['request']['id']}/decision",
        json={
            "decision": "approved",
            "notes": "No environmental evidence yet.",
            "decided_by": "approver@fairmind.ai",
        },
    )
    assert decision.status_code == 409
    assert decision.json()["detail"]["environmentalGate"]["code"] == "missing_environmental_evidence"


def test_documented_conditional_go_allows_system_approval(environmental_governance_client):
    client, org_id = environmental_governance_client
    system_id = _create_system(client, org_id)
    _set_low_tier(environmental_governance_client, system_id)
    assessed = client.post(
        f"{_environmental_base(org_id, system_id)}/assess",
        json={"assessment": _assessment()},
    )
    assert assessed.status_code == 200
    assert assessed.json()["recommendation"] == "conditional_go"

    approval_req = client.post(
        f"/api/v1/ai-governance/approval/system/{system_id}/request",
        json={"requested_by": "owner@fairmind.ai"},
    )
    assert approval_req.status_code == 200
    request_id = approval_req.json()["request"]["id"]
    decision = client.post(
        f"/api/v1/ai-governance/approval-requests/{request_id}/decision",
        json={
            "decision": "approved",
            "notes": "Environmental mitigation documented.",
            "decided_by": "approver@fairmind.ai",
        },
    )
    assert decision.status_code == 200
    assert decision.json()["status"] == "approved"


def test_approval_is_refused_while_findings_or_critical_tasks_are_open(environmental_governance_client):
    client, org_id = environmental_governance_client
    system_id = _create_system(client, org_id)
    _set_low_tier(environmental_governance_client, system_id)
    assert client.post(f"{_environmental_base(org_id, system_id)}/assess", json={"assessment": _assessment()}).status_code == 200
    risk = client.post("/api/v1/ai-governance/risks/assess", json={"systemId": system_id, "riskType": "fairness", "severity": "high", "description": "Approval rates differ by region"})
    assert risk.status_code == 200, risk.text
    task = client.post("/api/v1/ai-governance/remediation", json={"system_id": system_id, "title": "Recalibrate", "description": "Recalibrate by region", "source_type": "risk", "source_id": risk.json()["id"], "priority": "critical"})
    assert task.status_code == 200, task.text
    request_id = client.post(f"/api/v1/ai-governance/approval/system/{system_id}/request", json={}).json()["request"]["id"]
    url = f"/api/v1/ai-governance/approval-requests/{request_id}/decision"

    refused = client.post(url, json={"decision": "approved", "notes": "Environmental mitigation documented."})
    assert refused.status_code == 409, refused.text
    detail = refused.json()["detail"]
    assert detail["blockers"] == {"openHighOrCriticalFindings": 1, "activeCriticalTasks": 1}
    assert detail["message"].startswith("Approval is blocked by 1 open high or critical finding and 1 active critical remediation task")
    assert client.post(url, json={"decision": "rejected", "notes": "Findings open."}).status_code == 200


def test_resolving_the_linked_task_closes_the_finding_and_unblocks_approval(environmental_governance_client):
    client, org_id = environmental_governance_client
    system_id = _create_system(client, org_id)
    _set_low_tier(environmental_governance_client, system_id)
    blocked = client.post(
        f"{_environmental_base(org_id, system_id)}/assess",
        json={"assessment": _assessment(provenance_class="unknown", confidence_score=0.5, mitigation_readiness="missing", mitigations_json=[])},
    )
    assert blocked.status_code == 200 and blocked.json()["recommendation"] == "no_go"
    assert client.post(f"{_environmental_base(org_id, system_id)}/assess", json={"assessment": _assessment()}).status_code == 200
    task = next(t for t in client.get(f"/api/v1/ai-governance/remediation?system_id={system_id}").json()["tasks"] if t["sourceType"] == "environmental_assessment")
    request_id = client.post(f"/api/v1/ai-governance/approval/system/{system_id}/request", json={}).json()["request"]["id"]
    url = f"/api/v1/ai-governance/approval-requests/{request_id}/decision"
    approve = {"decision": "approved", "notes": "Environmental mitigation documented."}
    assert client.post(url, json=approve).json()["detail"]["blockers"]["openHighOrCriticalFindings"] == 1

    assert client.patch(f"/api/v1/ai-governance/remediation/{task['id']}", json={"status": "resolved"}).status_code == 200
    risks = client.get(f"/api/v1/ai-governance/dashboard/risk?system_id={system_id}").json()
    assert [r["status"] for r in risks["risks"] if r["id"] in task["linkedRiskIds"]] == ["resolved"]
    assert client.post(url, json=approve).status_code == 200


def test_a_rejection_stands_until_a_reviewer_approves_a_new_request(environmental_governance_client):
    client, org_id = environmental_governance_client
    system_id = _create_system(client, org_id)
    _set_low_tier(environmental_governance_client, system_id)
    assert client.post(f"{_environmental_base(org_id, system_id)}/assess", json={"assessment": _assessment()}).status_code == 200
    gate = lambda: client.get(f"/api/v1/ai-governance/systems/{system_id}/gate").json()
    decide = lambda decision: client.post(
        f"/api/v1/ai-governance/approval-requests/{client.post(f'/api/v1/ai-governance/approval/system/{system_id}/request', json={}).json()['request']['id']}/decision",
        json={"decision": decision, "notes": "Environmental mitigation documented."},
    )
    evidence_verdict = gate()["verdict"]
    assert evidence_verdict != "no_go"
    assert decide("rejected").status_code == 200

    client.post(f"/api/v1/ai-governance/approval/system/{system_id}/request", json={})
    pending = gate()
    assert pending["approvalStatus"] == "pending" and pending["verdict"] == "no_go"
    assert pending["reasons"][0].startswith("The last release decision was rejected")

    assert decide("approved").status_code == 200
    approved = gate()
    assert approved["approvalStatus"] == "approved" and approved["verdict"] == evidence_verdict
