"""Password reset: a generic, rate-limited request; an emailed token that sets a new password once.

The auth router runs against a SQLite users table built from the model.
"""

import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests import pg
from api.routes import auth
from config.auth import auth_manager
from config.settings import settings
from core.middleware.auth import NeonAuthMiddleware
from database.models import Organization, OrganizationMember, User
from middleware.security import JWTAuthenticationMiddleware
from tests.test_registration_approval import _Db, _rows

EMAIL = "person@corp.example.com"


@pytest.fixture
def env(monkeypatch):
    engine = pg.fresh_engine()
    db = _Db(engine)

    @asynccontextmanager
    async def connection():
        yield db

    monkeypatch.setattr("config.database.get_db_connection", connection)
    email = AsyncMock()
    email.api_key = "configured"
    monkeypatch.setattr("src.application.services.api_boundary_dependencies.email_service", email)
    monkeypatch.setattr(auth, "_reset_requests", {})
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO users (id, email, username, role, password_hash, is_active) "
                 "VALUES (:id, :email, 'person', 'analyst', :pw, TRUE)"),
            {"id": str(uuid.uuid4()), "email": EMAIL, "pw": auth_manager.get_password_hash("the-old-password")},
        )
    api = FastAPI()
    api.add_middleware(JWTAuthenticationMiddleware)  # both reset routes must be public
    api.include_router(auth.router, prefix="/api/v1")
    with TestClient(api) as client:
        yield client, engine, email


def _request(client, email, ip="198.51.100.1"):
    # uvicorn puts the caller's address in request.client once the proxy is trusted (FORWARDED_ALLOW_IPS).
    caller = TestClient(client.app, client=(ip, 50000))
    return caller.post("/api/v1/auth/password-reset/request", json={"email": email})


def test_reset_link_sets_a_new_password_once(env):
    client, engine, email = env
    unknown, known = _request(client, "nobody@corp.example.com"), _request(client, EMAIL.upper())
    assert unknown.status_code == known.status_code == 202
    assert unknown.json() == known.json()  # no account enumeration
    email.send_password_reset_email.assert_called_once()
    to, url, minutes = email.send_password_reset_email.call_args.args
    assert to == EMAIL and minutes == 30
    prefix = f"{settings.frontend_url}/reset-password#token="
    assert url.startswith(prefix)
    token = url[len(prefix):]
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401

    def reset(password):
        return client.post("/api/v1/auth/password-reset", json={"token": token, "password": password})

    assert reset("too-short").status_code == 422  # signup's 12-byte minimum
    assert reset("a-brand-new-password").status_code == 200
    [user] = _rows(engine, "SELECT password_hash FROM users")
    assert auth_manager.verify_password("a-brand-new-password", user["password_hash"])
    assert reset("yet-another-password").status_code == 400  # single use
    [after] = _rows(engine, "SELECT password_hash FROM users")
    assert after == user


def test_reset_requests_are_rate_limited_per_email(env):
    client, _, email = env
    assert [_request(client, EMAIL, f"198.51.100.{i}").status_code for i in range(6)] == [202] * 5 + [429]
    assert email.send_password_reset_email.call_count == 5


def test_reset_requests_are_rate_limited_per_client(env):
    client, _, _ = env
    assert [_request(client, f"p{i}@corp.example.com").status_code for i in range(6)] == [202] * 5 + [429]
    # Another caller is not blocked by the first one's requests.
    assert _request(client, "p9@corp.example.com", ip="203.0.113.7").status_code == 202


def test_forged_forwarded_header_does_not_buy_more_attempts(env):
    client, _, _ = env
    caller = TestClient(client.app, client=("198.51.100.9", 50000))
    statuses = [
        caller.post("/api/v1/auth/password-reset/request", json={"email": f"f{i}@corp.example.com"},
                    headers={"X-Forwarded-For": f"203.0.113.{i}"}).status_code
        for i in range(6)
    ]
    assert statuses == [202] * 5 + [429]


def test_sso_only_account_cannot_gain_a_password(env):
    client, engine, email = env
    sso_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO users (id, email, username, role, is_active) "
                 "VALUES (:id, 'sso@corp.example.com', 'sso', 'analyst', TRUE)"),
            {"id": sso_id},
        )
    assert _request(client, "sso@corp.example.com").json() == _request(client, "nobody@corp.example.com").json()
    email.send_password_reset_email.assert_not_called()
    token = auth_manager.create_password_reset_token(sso_id, None)
    response = client.post("/api/v1/auth/password-reset", json={"token": token, "password": "a-brand-new-password"})
    assert response.status_code == 400
    assert _rows(engine, "SELECT password_hash FROM users WHERE id = :id", id=sso_id)[0]["password_hash"] is None


def test_reset_routes_are_public_under_neon_auth():
    neon = NeonAuthMiddleware(app=None)
    assert neon._is_public_endpoint("/api/v1/auth/password-reset/request")
    assert neon._is_public_endpoint("/api/v1/auth/password-reset")


def test_without_email_configured_the_answer_is_unchanged_and_the_gap_is_logged(env, caplog, monkeypatch):
    client, _, email = env
    email.api_key = None
    monkeypatch.setattr(auth.logger, "handlers", [caplog.handler])  # the app's logging config stops propagation
    response = _request(client, EMAIL)
    assert response.status_code == 202
    assert response.json() == _request(client, "nobody@corp.example.com").json()
    email.send_password_reset_email.assert_not_called()
    assert "no email was sent" in caplog.text
