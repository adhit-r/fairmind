"""API keys authorise requests only while they are stored and their user is active; refresh tokens never do.

The auth router and JWTAuthenticationMiddleware run against SQLite tables built
from the models (api_keys has the shape migrations/001_initial_schema.sql gives it).
"""

import hashlib
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests import pg
from api.main import app
from api.routes import auth
from config.auth import E2E_ADMIN_ID, User, UserRole, auth_manager
from config.settings import settings
from database.models import ApiKey, Organization, OrganizationMember, User as UserRow
from middleware.security import JWTAuthenticationMiddleware
from tests.test_registration_approval import _Db, _rows


def _user():
    return User(id=str(uuid.uuid4()), email="ci@test.invalid", username="ci", role=UserRole.ADMIN,
                created_at=datetime.now(timezone.utc), permissions=["*"], org_id=str(uuid.uuid4()))


@pytest.fixture
def env(monkeypatch):
    engine = pg.fresh_engine()
    db = _Db(engine)

    @asynccontextmanager
    async def connection():
        yield db

    monkeypatch.setattr("config.database.get_db_connection", connection)
    monkeypatch.setattr("config.database.get_db_transaction", connection)
    user = _user()
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO users (id, email, username, role, is_active) VALUES (:id, :email, 'ci', 'analyst', TRUE)"),
            {"id": user.id, "email": user.email},
        )
    api = FastAPI()
    api.add_middleware(JWTAuthenticationMiddleware)
    api.include_router(auth.router, prefix="/api/v1")
    with TestClient(api) as client:
        session = {"Authorization": f"Bearer {auth_manager.create_access_token(user)}"}
        yield client, engine, user, session


def _mint(client, session, name="ci"):
    response = client.post("/api/v1/auth/api-keys", json={"name": name}, headers=session)
    assert response.status_code == 200, response.text
    return response.json()["api_key"]


def test_revoked_key_stops_working_on_its_next_request(env):
    client, engine, _, session = env
    key = _mint(client, session)
    [row] = _rows(engine, "SELECT * FROM api_keys")
    assert row["key_hash"] == hashlib.sha256(key.encode()).hexdigest()
    assert key not in str(row)  # only the hash is stored
    assert [k["name"] for k in client.get("/api/v1/auth/api-keys", headers=session).json()["api_keys"]] == ["ci"]
    as_key = {"Authorization": f"Bearer {key}"}
    assert client.get("/api/v1/auth/me", headers=as_key).status_code == 200

    assert client.delete("/api/v1/auth/api-keys/ci", headers=session).status_code == 200

    assert client.get("/api/v1/auth/me", headers=as_key).status_code == 401
    assert client.get("/api/v1/auth/api-keys", headers=session).json() == {"api_keys": []}
    assert client.delete("/api/v1/auth/api-keys/ci", headers=session).status_code == 404


@pytest.mark.parametrize("change", (
    "UPDATE users SET is_active = FALSE WHERE id = :id",
    "DELETE FROM users WHERE id = :id",
))
def test_key_of_a_deactivated_or_deleted_user_is_refused(env, change):
    client, engine, user, session = env
    as_key = {"Authorization": f"Bearer {_mint(client, session)}"}
    with engine.begin() as conn:
        conn.execute(text(change), {"id": user.id})
    assert client.get("/api/v1/auth/me", headers=as_key).status_code == 401


def test_e2e_admin_is_told_it_cannot_hold_api_keys(env, monkeypatch):
    client, engine, _, _ = env
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "e2e_admin_email", "e2e@test.invalid")
    monkeypatch.setattr(settings, "e2e_admin_password", "e2e-only-password")
    e2e = User(id=E2E_ADMIN_ID, email="e2e@test.invalid", username="e2e-admin", role=UserRole.ADMIN,
               created_at=datetime.now(timezone.utc), permissions=["*"], org_id=str(uuid.uuid4()))
    session = {"Authorization": f"Bearer {auth_manager.create_access_token(e2e)}"}
    response = client.post("/api/v1/auth/api-keys", json={"name": "ci"}, headers=session)
    assert response.status_code == 403, response.text
    assert _rows(engine, "SELECT * FROM api_keys") == []


def test_refresh_token_is_still_refused():
    client = TestClient(app, client=(f"apikey-{uuid.uuid4().hex[:8]}", 50000))
    refresh = auth_manager.create_refresh_token(_user())
    assert client.get("/api/v1/ai-governance/systems", headers={"Authorization": f"Bearer {refresh}"}).status_code == 401
