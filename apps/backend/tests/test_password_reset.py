"""Password reset: a generic, rate-limited request; an emailed token that sets a new password once.

The auth router runs against a SQLite users table built from the model.
"""

import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from api.routes import auth
from config.auth import auth_manager
from config.settings import settings
from database.connection import Base
from database.models import Organization, OrganizationMember, User
from middleware.security import JWTAuthenticationMiddleware
from tests.test_registration_approval import _Db, _rows

EMAIL = "person@corp.example.com"


@pytest.fixture
def env(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[User.__table__, Organization.__table__, OrganizationMember.__table__])
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
                 "VALUES (:id, :email, 'person', 'analyst', :pw, 1)"),
            {"id": str(uuid.uuid4()), "email": EMAIL, "pw": auth_manager.get_password_hash("the-old-password")},
        )
    api = FastAPI()
    api.add_middleware(JWTAuthenticationMiddleware)  # both reset routes must be public
    api.include_router(auth.router, prefix="/api/v1")
    with TestClient(api) as client:
        yield client, engine, email


def _request(client, email):
    return client.post("/api/v1/auth/password-reset/request", json={"email": email})


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
    assert [_request(client, EMAIL).status_code for _ in range(6)] == [202] * 5 + [429]
    assert email.send_password_reset_email.call_count == 5


def test_without_email_configured_the_answer_is_unchanged_and_the_gap_is_logged(env, caplog, monkeypatch):
    client, _, email = env
    email.api_key = None
    monkeypatch.setattr(auth.logger, "handlers", [caplog.handler])  # the app's logging config stops propagation
    response = _request(client, EMAIL)
    assert response.status_code == 202
    assert response.json() == _request(client, "nobody@corp.example.com").json()
    email.send_password_reset_email.assert_not_called()
    assert "no email was sent" in caplog.text
