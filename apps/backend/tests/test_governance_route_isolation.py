"""Cross-tenant tests for the ai-governance routes and /api/v1/audit-logs.

Same two organisations as test_org_isolation_audit (A and B, one registered AI
system each, plus a plain member of A). Each test signs in as one tenant and
tries to read or change the other tenant's records.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import pytest

from tests.test_org_isolation_audit import (  # noqa: F401  (db and client are fixtures)
    A,
    A_ADMIN,
    A_MEMBER,
    B,
    OWNER_A,
    OWNER_B,
    _insert,
    _SqliteConnection,
    client,
    db,
)

GOV = "/api/v1/ai-governance"


# --------------------------------------------------------------------------- policies


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", f"{GOV}/policies"),
        ("POST", f"{GOV}/policies"),
        ("GET", f"{GOV}/policies/p1"),
        ("PUT", f"{GOV}/policies/p1"),
        ("DELETE", f"{GOV}/policies/p1"),
        ("POST", f"{GOV}/policies/p1/submit"),
        ("GET", "/api/policies"),
        ("POST", "/api/policies"),
    ],
)
def test_legacy_policy_routes_are_gone(client, method, path):
    # Policies live under /organizations/{org_id}/policies (policy_center). 405 is
    # the global OPTIONS catch-all matching the path, not a policy handler.
    assert client.request(method, path, headers=A).status_code in (404, 405)


# --------------------------------------------------------------------------- risks and remediation


def _assess(client, headers, system_id):
    return client.post(
        f"{GOV}/risks/assess",
        headers=headers,
        json={"systemId": system_id, "riskType": "bias", "severity": "high", "description": "Disparity."},
    )


def test_risk_dashboard_and_assessment_stay_in_the_organisation(client):
    b_risk = _assess(client, B, "system-b")
    assert b_risk.status_code == 200, b_risk.text
    a_risk = _assess(client, A, "system-a").json()["id"]

    def stored(headers, query=""):
        risks = client.get(f"{GOV}/dashboard/risk{query}", headers=headers).json()["risks"]
        return [r["id"] for r in risks if r.get("source") == "manual_assessment"]

    assert stored(A) == [a_risk]
    assert stored(B) == [b_risk.json()["id"]]
    assert stored(A, "?system_id=system-a") == [a_risk]
    assert client.get(f"{GOV}/dashboard/risk?system_id=system-b", headers=A).status_code == 404
    assert _assess(client, A, "system-b").status_code == 404
    # A system id nobody registered has no owner, so nobody may file risks under it.
    assert _assess(client, A, "unregistered").status_code == 404
    assert client.get(f"{GOV}/dashboard/risk?system_id=unregistered", headers=A).status_code == 404
    assert _assess(client, A_MEMBER, "system-a").status_code == 403


def _task(client, headers, system_id):
    return client.post(
        f"{GOV}/remediation",
        headers=headers,
        json={
            "system_id": system_id,
            "title": "Fix threshold",
            "description": "Rerun validation.",
            "source_type": "risk",
            "source_id": "risk-1",
        },
    )


def test_remediation_tasks_stay_in_the_organisation(client):
    created = _task(client, B, "system-b")
    assert created.status_code == 200, created.text
    task_id = created.json()["id"]

    assert client.get(f"{GOV}/remediation?system_id=system-b", headers=A).status_code == 404
    assert client.patch(f"{GOV}/remediation/{task_id}", headers=A, json={"status": "closed"}).status_code == 404
    assert _task(client, A, "system-b").status_code == 404
    assert _task(client, A, "unregistered").status_code == 404
    assert client.get(f"{GOV}/remediation?system_id=unregistered", headers=A).status_code == 404

    tasks = client.get(f"{GOV}/remediation?system_id=system-b", headers=B).json()["tasks"]
    assert [(t["id"], t["status"]) for t in tasks] == [(task_id, "open")]
    assert client.patch(f"{GOV}/remediation/{task_id}", headers=B, json={"status": "closed"}).json()["status"] == "closed"


# --------------------------------------------------------------------------- shared catalogue


def test_framework_control_catalogue_is_written_only_by_platform_admins(client):
    body = {"control_id": "EU-1", "title": "Risk management"}
    assert client.post(f"{GOV}/frameworks/eu_ai_act/controls", headers=A, json=body).status_code == 403
    assert client.post(f"{GOV}/frameworks/eu_ai_act/controls", headers=A_ADMIN, json=body).status_code == 200
    # Reference data: every signed-in organisation reads the same catalogue.
    assert [c["controlId"] for c in client.get(f"{GOV}/frameworks/eu_ai_act/controls", headers=B).json()] == ["EU-1"]
    assert client.get(f"{GOV}/compliance/frameworks", headers=B).status_code == 200


# --------------------------------------------------------------------------- routes scoped through the system id


def test_system_records_addressed_by_id_stay_in_the_organisation(client):
    assert client.get(f"{GOV}/systems/system-b", headers=A).status_code == 404
    assert client.get(f"{GOV}/lifecycle/system-b/summary", headers=A).status_code == 404
    assert [s["id"] for s in client.get(f"{GOV}/systems", headers=A).json()] == ["system-a"]
    assert [w["id"] for w in client.get(f"{GOV}/workspaces", headers=A).json()] == ["ws-a"]
    assert client.post(
        f"{GOV}/systems",
        headers=A,
        json={"workspace_id": "ws-b", "name": "x", "risk_tier": "low", "lifecycle_stage": "onboard"},
    ).status_code == 404

    evidence = client.post(f"{GOV}/evidence/upload", headers=B, json={"system_id": "system-b", "type": "audit_log"})
    assert evidence.status_code == 200, evidence.text
    evidence_id = evidence.json()["id"]
    assert client.post(f"{GOV}/evidence/upload", headers=A, json={"system_id": "system-b", "type": "x"}).status_code == 404
    assert client.get(f"{GOV}/evidence-item/{evidence_id}", headers=A).status_code == 404
    assert client.patch(f"{GOV}/evidence-item/{evidence_id}", headers=A, json={"title": "x"}).status_code == 404
    assert client.post(
        f"{GOV}/evidence-item/{evidence_id}/links", headers=A, json={"entity_type": "risk", "entity_id": "r"}
    ).status_code == 404


# --------------------------------------------------------------------------- audit logs


@pytest.fixture
def audit_logs(db, monkeypatch):
    import config.database

    engine = db[0]
    connection = _SqliteConnection(engine)

    @asynccontextmanager
    async def fake_connection():
        yield connection

    monkeypatch.setattr(config.database, "get_db_connection", fake_connection)
    return engine


def test_audit_logs_list_only_the_organisations_members(client, audit_logs):
    for user, action in ((OWNER_A, "a-did-this"), (OWNER_B, "b-did-this")):
        _insert(audit_logs, "audit_logs", user_id=user, action=action, created_at="2026-01-01")
    _insert(audit_logs, "audit_logs", user_id=None, action="system", created_at="2026-01-02")

    assert client.get("/api/v1/audit-logs").status_code in (401, 403)
    assert [log["action"] for log in client.get("/api/v1/audit-logs", headers=A).json()["logs"]] == ["a-did-this"]
    assert [log["action"] for log in client.get("/api/v1/audit-logs", headers=B).json()["logs"]] == ["b-did-this"]
    assert client.get("/api/v1/audit-logs?action=b-did-this", headers=A).json()["logs"] == []
    assert client.get("/api/v1/audit-logs", headers=A).json()["logs"][0]["timestamp"] == "2026-01-01"
