"""Organisations own email domains: sign-ups from a domain join that org through its admins instead of
creating a look-alike org, and the platform admin sees likely duplicates before approving a new one."""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from api.routes import org_management, registration
from config.auth import UserRole, get_current_active_user, require_admin
from tests import pg
from tests.auth_helpers import make_token_data
from tests.test_registration_approval import MIGRATION, _Db, _rows, _submit

ORGS = "/api/v1/organizations"


@pytest.fixture
def env(monkeypatch):
    engine = pg.fresh_engine()
    with engine.begin() as conn:
        for statement in MIGRATION.read_text().split(";"):
            if statement.strip():
                conn.exec_driver_sql(statement)
    db = _Db(engine)

    @asynccontextmanager
    async def connection():
        yield db

    for module in (registration, org_management):
        monkeypatch.setattr(module, "get_db_connection", connection)
    monkeypatch.setattr(registration, "get_db_transaction", connection)
    email = AsyncMock()
    monkeypatch.setattr(registration, "email_service", email)
    monkeypatch.setattr("src.application.services.api_boundary_dependencies.email_service", email)
    monkeypatch.setattr(registration.settings, "admin_email", "operator@example.com")
    monkeypatch.setattr("src.api.routers.auth._reset_requests", {})
    monkeypatch.setattr(org_management, "_log_org_audit", AsyncMock())

    # An org with an owner on acme.example.com.
    org_id, owner_id = str(uuid.uuid4()), str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO users (id, email, username, role, password_hash, is_active) VALUES (:id, 'owner@acme.example.com', :u, 'analyst', 'x', TRUE)"), {"id": owner_id, "u": f"o-{owner_id[:6]}"})
        conn.execute(text("INSERT INTO organizations (id, name, slug, owner_id) VALUES (:id, 'acme', :slug, :o)"), {"id": org_id, "slug": f"acme-{org_id[:6]}", "o": owner_id})
        conn.execute(text("INSERT INTO org_members (id, org_id, user_id, role, status, joined_at) VALUES (:id, :org, :u, 'owner', 'active', :now)"),
                     {"id": str(uuid.uuid4()), "org": org_id, "u": owner_id, "now": datetime.utcnow()})

    app = FastAPI()
    app.include_router(registration.router, prefix="/api/v1")
    app.include_router(org_management.router)
    acting = {"as": make_token_data(owner_id, "owner@acme.example.com")}
    app.dependency_overrides[get_current_active_user] = lambda: acting["as"]
    app.dependency_overrides[require_admin] = lambda: make_token_data("platform-operator", "operator@example.com", role=UserRole.ADMIN)
    with TestClient(app) as client:
        yield client, engine, email, f"{ORGS}/{org_id}", org_id


def test_an_owner_claims_only_their_own_work_domain(env):
    client, _, _, base, _ = env
    assert client.post(f"{base}/domains", json={"domain": "gmail.com"}).status_code == 400
    assert client.post(f"{base}/domains", json={"domain": "other.example.com"}).status_code == 403
    assert client.post(f"{base}/domains", json={"domain": "not a domain"}).status_code == 400
    assert client.post(f"{base}/domains", json={"domain": "@Acme.Example.com "}).json() == {"domain": "acme.example.com"}
    assert [d["domain"] for d in client.get(f"{base}/domains").json()["domains"]] == ["acme.example.com"]


def test_a_signup_on_the_domain_joins_the_org_through_its_admins(env):
    client, engine, email, base, org_id = env
    client.post(f"{base}/domains", json={"domain": "acme.example.com"})
    request_id = _submit(client, email="sam@acme.example.com", name="Sam", org_name="Acme Security Pvt Ltd")

    [req] = _rows(engine, "SELECT org_id, org_name FROM registration_requests")
    assert (str(req["org_id"]), req["org_name"]) == (org_id, "acme")  # the typed name does not make a new org
    email.send_registration_request_to_admin.assert_not_called()
    assert email.send_join_request.call_args.args[0] == "owner@acme.example.com"
    assert client.post(f"/api/v1/registrations/{request_id}/approve", json={}).status_code == 409  # not the platform's call

    assert [r["email"] for r in client.get(f"{base}/join-requests").json()["requests"]] == ["sam@acme.example.com"]
    approved = client.post(f"{base}/join-requests/{request_id}/approve", json={"role": "editor"})
    assert approved.status_code == 200, approved.text
    assert approved.json()["new_account"] is True
    [member] = _rows(engine, "SELECT m.role FROM org_members m JOIN users u ON u.id::text = m.user_id::text WHERE u.email = 'sam@acme.example.com'")
    assert member["role"] == "editor"
    assert _rows(engine, "SELECT status FROM registration_requests")[0]["status"] == "approved"
    assert len(_rows(engine, "SELECT id FROM organizations")) == 1
    email.send_approval_email.assert_called_once()


def test_a_domain_belongs_to_one_org_and_new_orgs_take_their_owners_domain(env):
    client, engine, _, base, _ = env
    client.post(f"{base}/domains", json={"domain": "acme.example.com"})
    fresh = _submit(client, email="founder@neworg.example.com", name="Founder", org_name="New Org")
    assert client.post(f"/api/v1/registrations/{fresh}/approve", json={}).status_code == 200
    assert {r["domain"] for r in _rows(engine, "SELECT domain FROM org_domains")} == {"acme.example.com", "neworg.example.com"}
    assert client.post(f"{base}/domains", json={"domain": "neworg.example.com"}).status_code == 403  # not the owner's address
    personal = _submit(client, email="someone@gmail.com", name="Someone", org_name="New Org")
    assert client.post(f"/api/v1/registrations/{personal}/approve", json={}).status_code == 409  # the name is taken


def test_the_platform_admin_sees_look_alike_orgs(env):
    client, _, _, _, _ = env
    _submit(client, email="person@gmail.com", name="Person", org_name="AC-ME Security Ltd")
    [req] = client.get("/api/v1/registrations").json()["requests"]
    assert req["join"] is False
    assert [o["name"] for o in req["similar_orgs"]] == ["acme"]


def test_an_older_request_that_carries_an_org_is_not_a_join_request(env):
    client, engine, _, _, org_id = env
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO registration_requests (id, email, name, org_name, org_id, status) VALUES (:id, 'old@corp.example.com', 'Old', 'Corp', :org, 'pending')"),
                     {"id": str(uuid.uuid4()), "org": org_id})
    [req] = client.get("/api/v1/registrations").json()["requests"]
    assert req["join"] is False  # still the platform admin's to decide, as before
