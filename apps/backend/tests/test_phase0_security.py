"""Trust-floor regressions: auth cannot be bypassed and orgs cannot see each other."""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from api.main import app
from config.auth import User, UserRole, auth_manager
from tests.auth_helpers import auth_headers, fake_fetch_user_row, make_user_store, new_password


def _client(**kwargs) -> TestClient:
    # A fresh client address per client: the in-memory rate limiter counts the
    # whole suite's requests against the default "testclient" host.
    return TestClient(app, client=(f"phase0-{uuid.uuid4().hex[:8]}", 50000), **kwargs)


def test_non_public_routes_require_a_token():
    anon = _client()
    for path in ("/api/v1/ai-governance/systems", "/api/v1/monitoring/metrics", "/api/v1/core/models"):
        assert anon.get(path).status_code == 401, path


def test_refresh_token_cannot_authorize_requests():
    user = User(id=str(uuid.uuid4()), email="r@test.invalid", username="r", role=UserRole.ADMIN,
                created_at=datetime.now(timezone.utc), org_id=str(uuid.uuid4()))
    refresh = auth_manager.create_refresh_token(user)
    resp = _client().get("/api/v1/ai-governance/systems", headers={"Authorization": f"Bearer {refresh}"})
    assert resp.status_code == 401


def test_one_org_cannot_read_another_orgs_system():
    org_a, org_b = _client(headers=auth_headers()), _client(headers=auth_headers())
    ws = org_a.post("/api/v1/ai-governance/workspaces", json={"name": "A", "owner": "a"}).json()
    system = org_a.post("/api/v1/ai-governance/systems", json={
        "workspace_id": ws["id"], "name": "A system", "risk_tier": "high", "lifecycle_stage": "onboard",
    }).json()

    assert org_a.get(f"/api/v1/ai-governance/systems/{system['id']}").status_code == 200
    assert org_b.get(f"/api/v1/ai-governance/systems/{system['id']}").status_code == 404
    assert all(s["id"] != system["id"] for s in org_b.get("/api/v1/ai-governance/systems").json())
    # Writing against a foreign workspace is refused the same way.
    assert org_b.post("/api/v1/ai-governance/systems", json={
        "workspace_id": ws["id"], "name": "B", "risk_tier": "low", "lifecycle_stage": "onboard",
    }).status_code == 404


def test_login_checks_the_users_table(monkeypatch):
    password = new_password()
    monkeypatch.setattr("config.auth._fetch_user_row",
                        fake_fetch_user_row(make_user_store(("owner@example.com", password, "admin"))))
    client = _client()
    assert client.post("/api/v1/auth/login", json={"email": "admin@fairmind.ai", "password": "admin123"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "wrong-password"}).status_code == 401
    ok = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": password})
    assert ok.status_code == 200
    assert ok.json()["user"]["org_id"]
