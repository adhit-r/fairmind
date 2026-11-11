"""Signup is by invitation only, and never makes the signer a platform admin.

New organisations come from approved access requests (test_registration_approval).
The global admin role passes require_admin (registration approvals, user
management), so a public endpoint must not hand it out.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import auth
from tests import pg
from tests.test_registration_approval import _Db, _rows


@pytest.fixture
def env(monkeypatch):
    engine = pg.fresh_engine()
    db = _Db(engine)

    @asynccontextmanager
    async def transaction():
        yield db

    # signup imports it inside the function, so patch it where it lives.
    monkeypatch.setattr("config.database.get_db_transaction", transaction)
    login = AsyncMock(return_value=auth.LoginResponse(access_token="a", refresh_token="r", expires_in=60, user={}))
    monkeypatch.setattr(auth, "login", login)

    app = FastAPI()
    app.include_router(auth.router, prefix="/api/v1")
    with TestClient(app) as client:
        yield client, engine


@pytest.mark.parametrize("extra", ({}, {"org_name": "Corp"}, {"invitation_token": ""}))
def test_signup_without_an_invitation_creates_nothing(env, extra):
    client, engine = env
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "signer@corp.example.com", "password": "a-long-enough-pass", "name": "Signer", **extra},
    )
    assert response.status_code in (400, 422), response.text
    assert _rows(engine, "SELECT id FROM users") == []
    assert _rows(engine, "SELECT id FROM organizations") == []


def _invite(engine, email: str, *, status: str = "pending", days: int = 7) -> str:
    """An organisation with a pending invitation for email; returns the token."""
    import secrets
    import uuid
    from datetime import datetime, timedelta

    from sqlalchemy import text

    owner, org, token = str(uuid.uuid4()), str(uuid.uuid4()), secrets.token_urlsafe(16)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO users (id, email, username, role, is_active) VALUES (:id, :e, :id, 'analyst', TRUE)"),
                     {"id": owner, "e": f"{owner}@corp.example.com"})
        conn.execute(text("INSERT INTO organizations (id, name, slug, owner_id) VALUES (:id, 'Inviting', :id, :o)"),
                     {"id": org, "o": owner})
        conn.execute(text("INSERT INTO org_invitations (id, org_id, email, role, token, expires_at, status) "
                          "VALUES (:id, :org, :e, 'member', :t, :exp, :s)"),
                     {"id": str(uuid.uuid4()), "org": org, "e": email, "t": token,
                      "exp": datetime.utcnow() + timedelta(days=days), "s": status})
    return token


def test_invitee_signup_creates_no_organisation(env):
    client, engine = env
    token = _invite(engine, "Invitee@corp.example.com")
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "invitee@corp.example.com", "password": "a-long-enough-pass", "name": "Invitee",
              "invitation_token": token},
    )
    assert response.status_code in (200, 201), response.text

    [user] = _rows(engine, "SELECT id, org_id, role, roles FROM users WHERE email = :e", e="invitee@corp.example.com")
    assert user["org_id"] is None
    assert user["role"] == "analyst" and "admin" not in str(user["roles"])
    assert _rows(engine, "SELECT id FROM org_members WHERE user_id = :u", u=user["id"]) == []
    assert len(_rows(engine, "SELECT id FROM organizations")) == 1  # only the inviting org


@pytest.mark.parametrize("email,status,days", (
    ("someone-else@corp.example.com", "pending", 7),
    ("invitee@corp.example.com", "accepted", 7),
    ("invitee@corp.example.com", "pending", -1),
))
def test_invitee_signup_needs_a_live_invitation_for_that_email(env, email, status, days):
    client, engine = env
    token = _invite(engine, "invitee@corp.example.com", status=status, days=days)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "a-long-enough-pass", "name": "X", "invitation_token": token},
    )
    assert response.status_code == 400, response.text
    assert _rows(engine, "SELECT id FROM users WHERE email = :e", e=email) == []
