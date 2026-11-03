"""Human API dependencies accept access tokens and API keys, and refuse refresh tokens.

API keys authorise requests like access tokens since PR #200 (03d8b07); a refresh token
only mints new tokens and must never open a route.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from api.main import app
from config import auth as auth_module
from config.auth import E2E_ADMIN_ID, User, UserRole, auth_manager


@pytest.fixture
def existing_user(monkeypatch) -> User:
    """/auth/me loads the user a token names, so tokens must belong to one that exists. The
    development end-to-end admin is a real user that needs no database row."""
    monkeypatch.setattr(auth_module.settings, "environment", "development")
    monkeypatch.setattr(auth_module.settings, "e2e_admin_email", "token-purpose@example.test")
    monkeypatch.setattr(auth_module.settings, "e2e_admin_password", "token-purpose-only")
    return User(
        id=E2E_ADMIN_ID,
        email="token-purpose@example.test",
        username="e2e-admin",
        role=UserRole.ADMIN,
        created_at=datetime(2026, 8, 13, tzinfo=timezone.utc),
        permissions=["*"],
    )


def _me(token: str):
    with TestClient(app) as client:
        return client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})


def test_human_route_refuses_a_refresh_token(existing_user) -> None:
    response = _me(auth_manager.create_refresh_token(existing_user))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


@pytest.mark.parametrize("credential_kind", ("access", "api_key"))
def test_human_route_accepts_access_tokens_and_api_keys(existing_user, credential_kind: str) -> None:
    token = (
        auth_manager.create_access_token(existing_user)
        if credential_kind == "access"
        else auth_manager.create_api_key(existing_user, "automation-key")
    )
    response = _me(token)
    assert response.status_code == 200, response.text
    assert response.json()["id"] == E2E_ADMIN_ID
