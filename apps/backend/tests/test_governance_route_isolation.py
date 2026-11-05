"""Cross-tenant tests for the ai-governance routes and /api/v1/audit-logs.

Same two organisations as test_org_isolation_audit (A and B, one registered AI
system each, plus a plain member of A). Each test signs in as one tenant and
tries to read or change the other tenant's records.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI, Request
from sqlalchemy import text

from core.middleware.audit import AuditLoggingMiddleware
from database.models import OrganizationMember
from tests.test_org_isolation_audit import (  # noqa: F401  (db, client and legacy are fixtures)
    A,
    A_ADMIN,
    A_MEMBER,
    B,
    ORG_A,
    ORG_B,
    OWNER_A,
    OWNER_B,
    _insert,
    _EngineConnection,
    client,
    db,
    legacy,
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
    connection = _EngineConnection(engine)

    @asynccontextmanager
    async def fake_connection():
        yield connection

    monkeypatch.setattr(config.database, "get_db_connection", fake_connection)
    return engine


def test_audit_logs_list_only_the_organisations_members(client, audit_logs):
    for org, user, action in ((ORG_A, OWNER_A, "a-did-this"), (ORG_B, OWNER_B, "b-did-this")):
        _insert(audit_logs, "audit_logs", org_id=org, user_id=user, action=action, created_at="2026-01-01")
    _insert(audit_logs, "audit_logs", user_id=None, action="system", created_at="2026-01-02")

    assert client.get("/api/v1/audit-logs").status_code in (401, 403)
    assert [log["action"] for log in client.get("/api/v1/audit-logs", headers=A).json()["logs"]] == ["a-did-this"]
    assert [log["action"] for log in client.get("/api/v1/audit-logs", headers=B).json()["logs"]] == ["b-did-this"]
    assert client.get("/api/v1/audit-logs?action=b-did-this", headers=A).json()["logs"] == []
    # The reads above are audited too, so pick the seeded row by its action.
    assert client.get("/api/v1/audit-logs?action=a-did-this", headers=A).json()["logs"][0]["timestamp"].startswith("2026-01-01")


def test_requests_through_the_app_write_a_readable_audit_row_without_the_body(client, audit_logs):
    secret = "audit-body-secret-5d1c"
    body = {"kind": "github", "name": "models-repo", "config": {"repo": "acme/models"}, "token": secret}
    assert client.post("/api/v1/integrations", headers=A, json=body).status_code == 201

    [log] = client.get("/api/v1/audit-logs", headers=A).json()["logs"]
    assert (log["action"], log["user_id"], log["resource_type"]) == ("POST /api/v1/integrations", OWNER_A, "integrations")
    details = log["details"]  # a JSON column comes back as an object
    assert details["status_code"] == 201
    assert log["timestamp"]

    with audit_logs.begin() as conn:
        stored = [dict(row) for row in conn.execute(text("SELECT * FROM audit_logs")).mappings()]
    assert [row["action"] for row in stored] == ["POST /api/v1/integrations", "GET /api/v1/audit-logs"]
    assert secret not in repr(stored)
    assert A["Authorization"].split(" ", 1)[1] not in repr(stored)


def _stored(engine):
    with engine.begin() as conn:
        return [dict(row) for row in conn.execute(text("SELECT * FROM audit_logs ORDER BY id")).mappings()]


def test_audit_rows_name_the_route_not_the_credential_in_its_path(client, audit_logs):
    token = "invite-secret-token-abc123"
    client.get(f"/api/v1/organizations/invitations/{token}", headers=A)
    client.post(f"/api/v1/organizations/invitations/{token}/accept", headers=A)

    stored = _stored(audit_logs)
    assert [row["action"] for row in stored] == [
        "GET /api/v1/organizations/invitations/{token}",
        "POST /api/v1/organizations/invitations/{token}/accept",
    ]
    assert token not in repr(stored)


def test_a_shared_members_activity_in_another_organisation_stays_out_of_its_log(client, db, audit_logs):
    with db[1]() as session:
        session.execute(
            OrganizationMember.__table__.insert().values(
                id=uuid.uuid4(), org_id=uuid.UUID(ORG_A), user_id=uuid.UUID(OWNER_B), role="member", status="active"
            )
        )
        session.commit()
    in_b = ["GET /api/v1/ai-governance/systems/{system_id}", "GET /api/v1/ai-governance/organizations/{org_id}/frameworks"]
    client.get(f"{GOV}/systems/system-b?org_id={ORG_B}", headers=B)
    client.get(f"{GOV}/organizations/{ORG_B}/frameworks", headers=B)

    def actions(headers, org):
        return [log["action"] for log in client.get(f"/api/v1/audit-logs?org_id={org}", headers=headers).json()["logs"]]

    assert not set(in_b) & set(actions(A, ORG_A))
    assert set(in_b) <= set(actions(B, ORG_B))


def test_activity_feeds_are_not_filled_by_their_own_reads(client, audit_logs, legacy):
    _insert(audit_logs, "audit_logs", org_id=ORG_A, user_id=OWNER_A, action="model_uploaded",
            resource_type="model", created_at="2026-01-01")
    for _ in range(5):
        client.get("/api/v1/core/activity/recent?limit=3", headers=A)
        client.get("/api/v1/database/dashboard-stats", headers=A)

    feed = client.get("/api/v1/core/activity/recent?limit=3", headers=A).json()["data"]
    stats = client.get("/api/v1/database/dashboard-stats", headers=A).json()["data"]
    assert [a["type"] for a in feed] == ["model_uploaded"]
    assert [a["type"] for a in stats["recentActivity"]] == ["model_uploaded"]


@pytest.mark.asyncio
async def test_a_failing_request_is_not_held_back_by_its_audit_write(monkeypatch):
    database_answers = asyncio.Event()
    written = []

    async def slow_write(self, context):
        await database_answers.wait()
        written.append(context["route"])

    monkeypatch.setattr(AuditLoggingMiddleware, "_persist_audit_log", slow_write)
    app = FastAPI()
    app.add_middleware(AuditLoggingMiddleware)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("route failed")

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as http:
        with pytest.raises(RuntimeError, match="route failed"):
            await asyncio.wait_for(http.get("/boom"), timeout=2)
    assert written == []
    database_answers.set()
    await asyncio.sleep(0.01)
    assert written == ["/boom"]


def test_the_audited_ip_is_the_connecting_peer_not_a_forwarded_header():
    request = Request(
        {"type": "http", "headers": [(b"x-forwarded-for", b"203.0.113.9")], "client": ("198.51.100.7", 4242)}
    )
    assert AuditLoggingMiddleware(app=None)._get_client_ip(request) == "198.51.100.7"
