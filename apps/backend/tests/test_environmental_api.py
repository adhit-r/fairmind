"""
Integration tests for the environmental governance API + approval gate.

Exercises the MVP storage path (assessments persisted as governance evidence)
end to end through the FastAPI app, plus the environmental release-gate hook in
the approvals workflow.
"""

import pytest

pytestmark = pytest.mark.integration


def _seed_system(client, name: str = "env-test-system") -> str:
    """Create a governance AI system through the public governance API."""
    workspace = client.post(
        "/api/v1/ai-governance/workspaces",
        json={"name": f"{name}-ws", "owner": "owner@fairmind.ai"},
    )
    assert workspace.status_code == 200, workspace.text
    system = client.post(
        "/api/v1/ai-governance/systems",
        json={
            "workspace_id": workspace.json()["id"],
            "name": name,
            "owner": "owner@fairmind.ai",
            "risk_tier": "high",
            "lifecycle_stage": "govern",
            "metadata": {},
        },
    )
    assert system.status_code == 200, system.text
    return system.json()["id"]


def _assessment_body(system_id: str, *, source: str, phase: str, metrics: dict, **extra) -> dict:
    body = {
        "system_id": system_id,
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
    return body


def test_benchmarks_and_controls_are_public(client):
    r = client.get("/api/v1/environment/benchmarks")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["provisional"] is True
    assert "training" in data["thresholds"]

    r = client.get("/api/v1/environment/controls")
    assert r.status_code == 200
    codes = [c["code"] for c in r.json()["data"]["controls"]]
    assert codes[:6] == ["ENV-1", "ENV-2", "ENV-3", "ENV-4", "ENV-5", "ENV-6"]


def test_assess_low_impact_measured_is_go(client):
    system_id = _seed_system(client)
    body = _assessment_body(
        system_id,
        source="hardware_telemetry",  # measured
        phase="training",
        metrics={"total_kwh": 50.0, "total_kg_co2e_location": 40.0, "kg_co2e_per_1m_tokens": 0.2},
    )
    r = client.post("/api/v1/ai-governance/environment/assess", json=body)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["impact_tier"] == "low"
    assert out["confidence_band"] == "measured"
    assert out["recommendation"] == "go"

    # Latest read-back matches.
    r = client.get(f"/api/v1/systems/{system_id}/environmental-impact")
    assert r.status_code == 200
    assert r.json()["data"]["latest"]["result"]["recommendation"] == "go"


def test_assess_undisclosed_source_is_no_go(client):
    system_id = _seed_system(client)
    body = _assessment_body(
        system_id, source="unknown", phase="inference",
        metrics={"kg_co2e_per_1000_requests": 0.0001},  # low impact, but no disclosure
    )
    r = client.post("/api/v1/ai-governance/environment/assess", json=body)
    assert r.status_code == 200, r.text
    assert r.json()["recommendation"] == "no_go"
    assert r.json()["evidence_confidence"] == 0.0


def test_export_csrd_shape(client):
    system_id = _seed_system(client)
    client.post(
        "/api/v1/ai-governance/environment/assess",
        json=_assessment_body(
            system_id, source="hardware_telemetry", phase="training",
            metrics={"total_kwh": 50.0, "total_kg_co2e_location": 40.0, "energy_renewable_pct": 80.0},
        ),
    )
    r = client.get(f"/api/v1/systems/{system_id}/environmental-impact/export")
    assert r.status_code == 200
    exp = r.json()["data"]
    assert exp["standard"].startswith("ESRS E1")
    assert exp["governance_recommendation"] == "go"


def test_conditional_go_mitigation_flow(client):
    system_id = _seed_system(client)
    # High impact + measured -> conditional_go, blocked until a dated mitigation.
    body = _assessment_body(
        system_id, source="hardware_telemetry", phase="training",
        metrics={"total_kg_co2e_location": 20000.0, "total_kwh": 40000.0, "kg_co2e_per_1m_tokens": 5.0},
    )
    r = client.post("/api/v1/ai-governance/environment/assess", json=body)
    assert r.json()["recommendation"] == "conditional_go"
    assert r.json()["mitigation_blocking"] is True
    assessment_id = r.json()["assessment_id"]

    # Approve is blocked while mitigation is missing.
    r = client.post(
        f"/api/v1/systems/{system_id}/environmental-impact/{assessment_id}/approve",
        json={"reviewer": "grc-lead"},
    )
    assert r.status_code == 409

    # Add a dated mitigation, then approval succeeds.
    r = client.put(
        f"/api/v1/systems/{system_id}/environmental-impact/{assessment_id}/mitigation",
        json={"mitigation": {"description": "4-bit quantise + re-measure", "target_date": "2026-12-01"}},
    )
    assert r.status_code == 200
    r = client.post(
        f"/api/v1/systems/{system_id}/environmental-impact/{assessment_id}/approve",
        json={"reviewer": "grc-lead", "attestation": "Reviewed with mitigation plan"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["reviewerState"] == "accepted"


def test_environmental_gate_blocks_deployment_approval(client):
    """The env gate must block the deployment-approval workflow on no_go."""
    system_id = _seed_system(client, "gate-system")
    # Record a no_go assessment (undisclosed source).
    client.post(
        "/api/v1/ai-governance/environment/assess",
        json=_assessment_body(
            system_id, source="unknown", phase="inference",
            metrics={"kg_co2e_per_1000_requests": 0.0001},
        ),
    )

    # Create an approval request for this system and try to approve it.
    r = client.post("/api/approvals/requests", json={"ai_system_id": system_id})
    assert r.status_code in (200, 201), r.text
    request_id = r.json()["id"]

    r = client.post(f"/api/approvals/requests/{request_id}/approve", json={"comment": "ship it"})
    assert r.status_code == 409
    assert "Environmental gate" in r.json()["detail"]
