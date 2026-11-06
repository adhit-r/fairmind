"""Self-serve signup makes the signer owner of a new organisation, never a platform admin.

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


def test_signup_owns_its_organisation_but_is_not_a_platform_admin(env):
    client, engine = env
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "signer@corp.example.com", "password": "a-long-enough-pass", "name": "Signer", "org_name": "Corp"},
    )
    assert response.status_code in (200, 201), response.text

    [user] = _rows(engine, "SELECT id, role, roles FROM users WHERE email = :e", e="signer@corp.example.com")
    assert user["role"] == "analyst"
    assert "admin" not in str(user["roles"])

    [member] = _rows(engine, "SELECT role, status FROM org_members WHERE user_id = :u", u=user["id"])
    assert (member["role"], member["status"]) == ("owner", "active")
    [org] = _rows(engine, "SELECT owner_id FROM organizations WHERE name = 'Corp'")
    assert str(org["owner_id"]) == str(user["id"])
