"""
Integration tests for the environmental governance API + approval gate.

Exercises the MVP storage path (assessments persisted as governance evidence)
end to end through the FastAPI app, plus the environmental release-gate hook in
the approvals workflow.
"""

import inspect

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from unittest.mock import patch

from api.main import app
from src.application.services import environmental_service

pytestmark = pytest.mark.integration


def test_environmental_service_uses_migrations_instead_of_request_time_ddl():
    source = inspect.getsource(environmental_service)

    assert "_tables_ready" not in source
    for statement in ("CREATE TABLE", "ALTER TABLE", "DROP TABLE"):
        assert statement not in source


def _seed_system(client: TestClient, org_id: str, name: str = "env-test-system") -> str:
    """Create a governance AI system through the canonical tenant-scoped API."""
    workspace = client.post(
        f"/api/v1/ai-governance/organizations/{org_id}/workspaces",
        json={"name": f"{name}-ws", "owner": "owner@fairmind.ai"},
    )
    assert workspace.status_code == 201, workspace.text
    system = client.post(
        f"/api/v1/ai-governance/organizations/{org_id}/systems",
        json={
            "workspace_id": workspace.json()["id"],
            "name": name,
            "owner": "owner@fairmind.ai",
            "risk_tier": "high",
            "lifecycle_stage": "govern",
            "metadata": {},
        },
    )
    assert system.status_code == 201, system.text
    return system.json()["id"]


def _environmental_base(org_id: str, system_id: str) -> str:
    return (
        f"/api/v1/ai-governance/organizations/{org_id}/systems/{system_id}"
        "/environmental-impact"
    )


def _assessment_body(*, source: str, phase: str, metrics: dict, **extra) -> dict:
    return {
        "assessment": {
            "lifecycle_phase": phase,
            "functional_unit": "1000_requests",
            "boundary": "scope 2, in-region",
            "source": source,
            "uncertainty_pct": 12.0,
            "metrics": metrics,
            **extra,
        },
    }


def test_benchmarks_and_controls_reject_anonymous_requests():
    with TestClient(app) as anonymous_client:
        assert anonymous_client.get("/api/v1/environment/benchmarks").status_code == 401
        assert anonymous_client.get("/api/v1/environment/controls").status_code == 401


def test_environmental_routes_reject_anonymous_requests_in_development(
    environmental_governance_client,
):
    foreign_org_id = environmental_governance_client.foreign_org_id
    foreign_system_id = environmental_governance_client.foreign_system_id
    base = _environmental_base(foreign_org_id, foreign_system_id)
    routes = (
        ("POST", f"{base}/assess", {"assessment": {}}),
        ("GET", base, None),
        ("POST", f"{base}/evidence", {}),
        ("GET", f"{base}/history", None),
        (
            "PUT",
            f"{base}/missing/mitigation",
            {"mitigation": {}},
        ),
        (
            "POST",
            f"{base}/missing/approve",
            {"reviewer": "spoofed"},
        ),
        ("GET", f"{base}/export", None),
        ("GET", f"{base}/controls", None),
    )
    with TestClient(app) as anonymous_client:
        for method, path, body in routes:
            response = anonymous_client.request(method, path, json=body)
            assert response.status_code == 401, (method, path, response.text)


def test_environmental_routes_hide_foreign_tenant_and_do_not_fetch(
    environmental_governance_client,
):
    client = environmental_governance_client.client
    org_id = environmental_governance_client.org_id
    foreign_system_id = environmental_governance_client.foreign_system_id
    confused_base = _environmental_base(org_id, foreign_system_id)
    session = environmental_governance_client.session_factory()
    try:
        before_counts = {
            table: session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            for table in (
                "governance_environmental_assessments",
                "governance_evidence",
                "governance_risks",
                "governance_remediation_tasks",
            )
        }
    finally:
        session.close()
    routes = (
        (
            "POST",
            f"{confused_base}/assess",
            {"assessment": {}},
        ),
        ("GET", confused_base, None),
        (
            "POST",
            f"{confused_base}/evidence",
            {"connector_type": "json", "url": "http://169.254.169.254/latest/meta-data"},
        ),
        ("GET", f"{confused_base}/history", None),
        (
            "PUT",
            f"{confused_base}/missing/mitigation",
            {"mitigation": {}},
        ),
        (
            "POST",
            f"{confused_base}/missing/approve",
            {"reviewer": "spoofed"},
        ),
        ("GET", f"{confused_base}/export", None),
        ("GET", f"{confused_base}/controls", None),
    )
    with patch(
        "src.application.services.environmental_service.fetch_connector_url"
    ) as fetch_connector_url:
        for method, path, body in routes:
            response = client.request(method, path, json=body)
            assert response.status_code == 404, (method, path, response.text)
    fetch_connector_url.assert_not_called()
    session = environmental_governance_client.session_factory()
    try:
        after_counts = {
            table: session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            for table in before_counts
        }
    finally:
        session.close()
    assert after_counts == before_counts


def test_benchmarks_and_controls_are_available_after_authentication(
    environmental_governance_client,
):
    client, _ = environmental_governance_client
    r = client.get("/api/v1/environment/benchmarks")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["provisional"] is True
    assert "training" in data["thresholds"]

    r = client.get("/api/v1/environment/controls")
    assert r.status_code == 200
    codes = [c["code"] for c in r.json()["data"]["controls"]]
    assert codes[:6] == ["ENV-1", "ENV-2", "ENV-3", "ENV-4", "ENV-5", "ENV-6"]


def test_assess_low_impact_measured_is_go(environmental_governance_client):
    client, org_id = environmental_governance_client
    system_id = _seed_system(client, org_id)
    base = _environmental_base(org_id, system_id)
    body = _assessment_body(
        source="hardware_telemetry",  # measured
        phase="training",
        metrics={"total_kwh": 50.0, "total_kg_co2e_location": 40.0, "kg_co2e_per_1m_tokens": 0.2},
    )
    r = client.post(f"{base}/assess", json=body)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["impact_tier"] == "low"
    assert out["confidence_band"] == "measured"
    assert out["recommendation"] == "go"

    # Latest read-back matches.
    r = client.get(base)
    assert r.status_code == 200
    assert r.json()["data"]["latest"]["result"]["recommendation"] == "go"


def test_assess_undisclosed_source_is_no_go(environmental_governance_client):
    client, org_id = environmental_governance_client
    system_id = _seed_system(client, org_id)
    base = _environmental_base(org_id, system_id)
    body = _assessment_body(
        source="unknown", phase="inference",
        metrics={"kg_co2e_per_1000_requests": 0.0001},  # low impact, but no disclosure
    )
    r = client.post(f"{base}/assess", json=body)
    assert r.status_code == 200, r.text
    assert r.json()["recommendation"] == "no_go"
    assert r.json()["evidence_confidence"] == 0.0


def test_export_csrd_shape(environmental_governance_client):
    client, org_id = environmental_governance_client
    system_id = _seed_system(client, org_id)
    base = _environmental_base(org_id, system_id)
    client.post(
        f"{base}/assess",
        json=_assessment_body(
            source="hardware_telemetry", phase="training",
            metrics={"total_kwh": 50.0, "total_kg_co2e_location": 40.0, "energy_renewable_pct": 80.0},
        ),
    )
    r = client.get(f"{base}/export")
    assert r.status_code == 200
    exp = r.json()["data"]
    assert exp["standard"].startswith("ESRS E1")
    assert exp["governance_recommendation"] == "go"


def test_conditional_go_mitigation_flow(environmental_governance_client):
    client, org_id = environmental_governance_client
    system_id = _seed_system(client, org_id)
    base = _environmental_base(org_id, system_id)
    # High impact + measured -> conditional_go, blocked until a dated mitigation.
    body = _assessment_body(
        source="hardware_telemetry", phase="training",
        metrics={"total_kg_co2e_location": 20000.0, "total_kwh": 40000.0, "kg_co2e_per_1m_tokens": 5.0},
    )
    r = client.post(f"{base}/assess", json=body)
    assert r.json()["recommendation"] == "conditional_go"
    assert r.json()["mitigation_blocking"] is True
    assessment_id = r.json()["assessment_id"]

    # Approve is blocked while mitigation is missing.
    r = client.post(
        f"{base}/{assessment_id}/approve",
        json={"reviewer": "grc-lead"},
    )
    assert r.status_code == 409

    # Add a dated mitigation, then approval succeeds.
    r = client.put(
        f"{base}/{assessment_id}/mitigation",
        json={"mitigation": {"description": "4-bit quantise + re-measure", "target_date": "2026-12-01"}},
    )
    assert r.status_code == 200
    r = client.post(
        f"{base}/{assessment_id}/approve",
        json={"reviewer": "grc-lead", "attestation": "Reviewed with mitigation plan"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["reviewerState"] == "accepted"


def test_environmental_gate_blocks_deployment_approval(environmental_governance_client):
    """The env gate must block the deployment-approval workflow on no_go."""
    client, org_id = environmental_governance_client
    system_id = _seed_system(client, org_id, "gate-system")
    base = _environmental_base(org_id, system_id)
    # Record a no_go assessment (undisclosed source).
    client.post(
        f"{base}/assess",
        json=_assessment_body(
            source="unknown", phase="inference",
            metrics={"kg_co2e_per_1000_requests": 0.0001},
        ),
    )

    # Create an approval request for this system and try to approve it.
    r = client.post(
        f"/api/v1/ai-governance/approval/system/{system_id}/request",
        json={"requested_by": "spoofed@fairmind.ai"},
    )
    assert r.status_code == 200, r.text
    request_id = r.json()["request"]["id"]

    r = client.post(
        f"/api/v1/ai-governance/approval-requests/{request_id}/decision",
        json={"decision": "approved", "notes": "ship it"},
    )
    assert r.status_code == 409
    assert r.json()["detail"]["environmentalGate"]["code"] == "environmental_no_go"
