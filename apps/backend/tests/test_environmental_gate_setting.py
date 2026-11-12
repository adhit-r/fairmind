"""Environmental impact counts in an organisation's release gate only when an owner or admin turns it on."""

from tests.test_environmental_governance import _create_system, _set_low_tier

AIG = "/api/v1/ai-governance"


def _attest_and_request(client, system_id: str) -> str:
    assert client.post(
        f"{AIG}/systems/{system_id}/attestations",
        json={"check": "data_governance", "statement": "Training data comes from the licensed 2024 corpus."},
    ).status_code == 200
    response = client.post(f"{AIG}/approval/system/{system_id}/request", json={"requested_by": "owner@fairmind.ai"})
    assert response.status_code == 200, response.text
    return response.json()["request"]["id"]


def test_off_by_default_the_gate_weighs_four_checks_and_approval_needs_no_assessment(environmental_governance_client):
    client, org_id = environmental_governance_client
    system_id = _create_system(client, org_id)
    _set_low_tier(environmental_governance_client, system_id)
    request_id = _attest_and_request(client, system_id)

    assert client.get(f"{AIG}/release-gate/settings", params={"org_id": org_id}).json() == {"environmentalGate": False}
    gate = client.get(f"{AIG}/systems/{system_id}/gate").json()
    assert [c["key"] for c in gate["checks"]] == ["fairness", "data_governance", "human_oversight", "monitoring"]
    assert all(b["key"] != "environmental_assessment" for b in gate["path"]["approvalBlockers"])

    decision = client.post(
        f"{AIG}/approval-requests/{request_id}/decision",
        json={"decision": "approved", "notes": "Accepted with conditions.", "decided_by": "approver@fairmind.ai"},
    )
    # Whatever else may hold it, a missing environmental assessment never does.
    assert "environmentalGate" not in str(decision.json().get("detail", "")), decision.text


def test_an_owner_turns_it_on_and_the_assessment_is_required_again(environmental_governance_client):
    client, org_id = environmental_governance_client
    system_id = _create_system(client, org_id)
    _set_low_tier(environmental_governance_client, system_id)

    turned = client.put(f"{AIG}/release-gate/settings", params={"org_id": org_id}, json={"environmentalGate": True})
    assert turned.status_code == 200 and turned.json() == {"environmentalGate": True}
    assert [c["key"] for c in client.get(f"{AIG}/systems/{system_id}/gate").json()["checks"]][-1] == "environmental"

    request_id = _attest_and_request(client, system_id)
    decision = client.post(
        f"{AIG}/approval-requests/{request_id}/decision",
        json={"decision": "approved", "notes": "No environmental evidence yet.", "decided_by": "approver@fairmind.ai"},
    )
    assert decision.status_code == 409
    assert decision.json()["detail"]["environmentalGate"]["code"] == "missing_environmental_evidence"

    from sqlalchemy import text

    with environmental_governance_client.session_factory() as session:
        actions = session.execute(text("SELECT action FROM org_audit_logs WHERE org_id::text = :org"), {"org": org_id}).scalars().all()
    assert "release_gate_environmental_on" in actions


def test_a_member_who_is_not_owner_or_admin_cannot_change_it(environmental_governance_client):
    client, org_id = environmental_governance_client
    from sqlalchemy import text

    with environmental_governance_client.session_factory() as session:
        session.execute(text("UPDATE org_members SET role = 'member' WHERE org_id::text = :org"), {"org": org_id})
        session.commit()
    refused = client.put(f"{AIG}/release-gate/settings", params={"org_id": org_id}, json={"environmentalGate": True})
    assert refused.status_code == 403
