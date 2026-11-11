"""Registration approval never changes an existing user or organisation.

The router runs against PostgreSQL with the real users/organizations/org_members
tables and migrations/016_registration_requests.sql.
"""

import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from api.routes import registration
from config.auth import UserRole, auth_manager, require_admin
from tests import pg
from tests.auth_helpers import make_token_data

MIGRATION = Path(__file__).resolve().parents[1] / "migrations" / "016_registration_requests.sql"
ADMIN_ID = "platform-operator"


class _Row(dict):
    """A row like the `databases` Record the app gets: indexable, but no .get()."""

    def get(self, *_args, **_kwargs):
        raise AttributeError("get")


class _Db:
    """The fetch_one / fetch_all / execute slice of the `databases` API, over SQLAlchemy."""

    def __init__(self, engine):
        self.engine = engine

    async def fetch_all(self, query, params=None):
        with self.engine.begin() as conn:
            return [_Row(r) for r in conn.execute(text(query), params or {}).mappings().all()]

    async def fetch_one(self, query, params=None):
        rows = await self.fetch_all(query, params)
        return rows[0] if rows else None

    async def execute(self, query, params=None):
        with self.engine.begin() as conn:
            conn.execute(text(query), params or {})


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

    monkeypatch.setattr(registration, "get_db_connection", connection)
    monkeypatch.setattr(registration, "get_db_transaction", connection)
    email = AsyncMock()
    monkeypatch.setattr(registration, "email_service", email)
    # Submissions share the per-process rate limit with password resets; start each test clean.
    monkeypatch.setattr("src.api.routers.auth._reset_requests", {})

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
    # users.org_id and organizations.owner_id reference each other: insert, then link.
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO users (id, email, username, role, password_hash, is_active) "
                 "VALUES (:id, :email, :u, :role, 'hash-before', TRUE)"),
            {"id": user_id, "email": email, "u": f"u-{user_id[:6]}", "role": role},
        )
        conn.execute(
            text("INSERT INTO organizations (id, name, slug, owner_id) VALUES (:id, 'Acme', :slug, :owner)"),
            {"id": org_id, "slug": f"acme-{org_id[:6]}", "owner": user_id},
        )
        conn.execute(text("UPDATE users SET org_id = :org WHERE id = :id"), {"org": org_id, "id": user_id})
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
    assert user["password_hash"]  # a random one nobody knows, so reset links work
    assert str(user["org_id"]) == str(user["primary_org_id"]) == str(org["id"]) == body["org_id"]
    assert org["name"] == "Corp" and str(org["owner_id"]) == user["id"]
    assert (member["user_id"], member["role"], member["status"]) == (user["id"], "owner", "active")
    [req] = _rows(engine, "SELECT * FROM registration_requests")
    assert (req["status"], str(req["org_id"]), req["reviewed_by"]) == ("approved", body["org_id"], ADMIN_ID)
    [call] = email.send_approval_email.call_args_list
    to, name, org_name, url, _minutes = call.args
    assert (to, name, org_name) == ("new@corp.example.com", "New Person", "Corp")
    # The email's link sets the first password: a reset token bound to this user's hash.
    prefix = "/reset-password#token="
    assert prefix in url
    claims = auth_manager.read_password_reset_token(url.split(prefix, 1)[1])
    assert claims["sub"] == user["id"]
    assert claims["pwd"] == auth_manager.password_fingerprint(user["password_hash"])


def test_submissions_are_rate_limited_per_ip(env):
    client, _, email = env
    for i in range(5):
        _submit(client, email=f"person{i}@corp.example.com")
    response = client.post("/api/v1/register", json={"email": "x@corp.example.com", "name": "X", "org_name": "Y"})
    assert response.status_code == 429
    assert email.send_registration_request_to_admin.call_count == 5


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


def test_admin_lists_pending_requests(env):
    client, _, _ = env
    request_id = _submit(client, message="Pilot for our credit models")

    response = client.get("/api/v1/registrations?status_filter=pending")

    assert response.status_code == 200, response.text
    [row] = response.json()["requests"]
    assert (row["id"], row["status"], row["message"]) == (request_id, "pending", "Pilot for our credit models")
