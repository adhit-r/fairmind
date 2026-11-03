"""Registration approval never changes an existing user or organisation.

The router runs against SQLite with the real users/organizations/org_members
tables and migrations/016_registration_requests.sql.
"""

import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from api.routes import registration
from config.auth import UserRole, require_admin
from database.connection import Base
from database.models import Organization, OrganizationMember, User
from tests.auth_helpers import make_token_data

MIGRATION = Path(__file__).resolve().parents[1] / "migrations" / "016_registration_requests.sql"
ADMIN_ID = "platform-operator"


class _Db:
    """The fetch_one / fetch_all / execute slice of the `databases` API, over SQLAlchemy."""

    def __init__(self, engine):
        self.engine = engine

    async def fetch_all(self, query, params=None):
        with self.engine.begin() as conn:
            return [dict(r) for r in conn.execute(text(query), params or {}).mappings().all()]

    async def fetch_one(self, query, params=None):
        rows = await self.fetch_all(query, params)
        return rows[0] if rows else None

    async def execute(self, query, params=None):
        with self.engine.begin() as conn:
            conn.execute(text(query), params or {})


@pytest.fixture
def env(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[User.__table__, Organization.__table__, OrganizationMember.__table__])
    with engine.begin() as conn:
        for statement in MIGRATION.read_text().split(";"):
            if statement.strip():
                conn.exec_driver_sql(statement)
    db = _Db(engine)

    @asynccontextmanager
    async def connection():
        yield db

    monkeypatch.setattr(registration, "get_db_connection", connection)
    monkeypatch.setattr(registration, "get_db_transaction", connection)
    email = AsyncMock()
    monkeypatch.setattr(registration, "email_service", email)

    app = FastAPI()
    app.include_router(registration.router, prefix="/api/v1")
    app.dependency_overrides[require_admin] = lambda: make_token_data(
        ADMIN_ID, "operator@test.invalid", role=UserRole.ADMIN
    )
    with TestClient(app) as client:
        yield client, engine, email


def _rows(engine, query, **params):
    with engine.begin() as conn:
        return [dict(r) for r in conn.execute(text(query), params).mappings().all()]


def _submit(client, **overrides):
    payload = {"email": "new@corp.example.com", "name": "New Person", "org_name": "Corp", **overrides}
    response = client.post("/api/v1/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _seed_account(engine, email="existing@corp.example.com", role="admin"):
    user_id, org_id = str(uuid.uuid4()), str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO users (id, email, username, role, password_hash, is_active, org_id) "
                 "VALUES (:id, :email, :u, :role, 'hash-before', 1, :org)"),
            {"id": user_id, "email": email, "u": f"u-{user_id[:6]}", "role": role, "org": org_id},
        )
        conn.execute(
            text("INSERT INTO organizations (id, name, slug, owner_id) VALUES (:id, 'Acme', :slug, :owner)"),
            {"id": org_id, "slug": f"acme-{org_id[:6]}", "owner": user_id},
        )
    return user_id, org_id


def test_approval_creates_a_new_org_owned_by_the_requester(env):
    client, engine, email = env
    request_id = _submit(client, requested_role="admin")
    assert _rows(engine, "SELECT id FROM organizations") == []  # submitting creates nothing

    response = client.post(f"/api/v1/registrations/{request_id}/approve", json={})

    assert response.status_code == 200, response.text
    body = response.json()
    [user] = _rows(engine, "SELECT * FROM users")
    [org] = _rows(engine, "SELECT * FROM organizations")
    [member] = _rows(engine, "SELECT * FROM org_members")
    assert user["email"] == "new@corp.example.com" and user["id"] == body["user_id"]
    assert user["role"] == "analyst"  # the requested 'admin' is not granted
    assert user["password_hash"] is None
    assert str(user["org_id"]) == str(user["primary_org_id"]) == str(org["id"]) == body["org_id"]
    assert org["name"] == "Corp" and str(org["owner_id"]) == user["id"]
    assert (member["user_id"], member["role"], member["status"]) == (user["id"], "owner", "active")
    [req] = _rows(engine, "SELECT * FROM registration_requests")
    assert (req["status"], str(req["org_id"]), req["reviewed_by"]) == ("approved", body["org_id"], ADMIN_ID)
    email.send_approval_email.assert_called_once_with("new@corp.example.com", "New Person", "Corp")


def test_approval_refuses_an_email_that_already_has_an_account(env):
    client, engine, email = env
    user_id, org_id = _seed_account(engine)
    before = _rows(engine, "SELECT * FROM users")
    request_id = _submit(client, email="EXISTING@corp.example.com", org_name="Elsewhere", requested_role="viewer")

    response = client.post(f"/api/v1/registrations/{request_id}/approve", json={})

    assert response.status_code == 409
    assert _rows(engine, "SELECT * FROM users") == before  # org, role, password untouched
    assert len(_rows(engine, "SELECT id FROM organizations")) == 1
    assert _rows(engine, "SELECT * FROM org_members") == []
    assert _rows(engine, "SELECT status FROM registration_requests") == [{"status": "pending"}]
    email.send_approval_email.assert_not_called()


def test_approval_refuses_an_existing_org_name(env):
    client, engine, email = env
    _, org_id = _seed_account(engine, email="owner@acme.example.com")
    request_id = _submit(client, email="outsider@else.example.com", org_name="acme")

    response = client.post(f"/api/v1/registrations/{request_id}/approve", json={})

    assert response.status_code == 409
    assert [u["email"] for u in _rows(engine, "SELECT email FROM users")] == ["owner@acme.example.com"]
    assert [str(o["id"]) for o in _rows(engine, "SELECT id FROM organizations")] == [org_id]
    assert _rows(engine, "SELECT * FROM org_members") == []
    assert _rows(engine, "SELECT status FROM registration_requests") == [{"status": "pending"}]
    email.send_approval_email.assert_not_called()


def test_deny_marks_the_request_and_creates_nothing(env):
    client, engine, email = env
    request_id = _submit(client)

    response = client.post(f"/api/v1/registrations/{request_id}/deny", json={"notes": "not a customer"})

    assert response.status_code == 200
    [req] = _rows(engine, "SELECT * FROM registration_requests")
    assert (req["status"], req["review_notes"], req["reviewed_by"]) == ("denied", "not a customer", ADMIN_ID)
    assert _rows(engine, "SELECT id FROM users") == []
    assert _rows(engine, "SELECT id FROM organizations") == []
    email.send_denial_email.assert_called_once_with("new@corp.example.com", "New Person", "Corp", "not a customer")
    assert client.post(f"/api/v1/registrations/{request_id}/approve", json={}).status_code == 409
