"""Auth routes that used to fake success now refuse: Authentik without a client secret, admin user creation."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import auth
from config.auth import UserRole, require_admin
from config.settings import Settings
from tests.auth_helpers import make_token_data


def _client():
    api = FastAPI()
    api.include_router(auth.router, prefix="/api/v1")
    api.dependency_overrides[require_admin] = lambda: make_token_data(
        "platform-operator", "operator@test.invalid", role=UserRole.ADMIN
    )
    return TestClient(api)


@pytest.mark.parametrize("unset", (
    "authentik_oauth_client_id", "authentik_oauth_client_secret", "authentik_oauth_redirect_uri",
))
def test_authentik_callback_missing_any_client_setting_never_calls_authentik(monkeypatch, unset):
    monkeypatch.setattr(auth.settings, "authentik_enabled", True)
    monkeypatch.setattr(auth.settings, "authentik_server_url", "https://sso.corp.example.com")
    monkeypatch.setattr(auth.settings, "authentik_oauth_client_id", "fairmind")
    monkeypatch.setattr(auth.settings, "authentik_oauth_client_secret", "configured")
    monkeypatch.setattr(auth.settings, "authentik_oauth_redirect_uri", "https://app.corp.example.com/callback")
    # Left out of the environment, the setting keeps its declared default.
    monkeypatch.setattr(auth.settings, unset, Settings.model_fields[unset].default)
    post = AsyncMock()
    monkeypatch.setattr(auth.httpx.AsyncClient, "post", post)

    response = _client().post("/api/v1/auth/callback", params={"code": "code", "state": "state"})

    assert response.status_code == 503
    assert response.json()["detail"] == "Authentik sign-in is not configured on this server"
    post.assert_not_called()


def test_admin_user_creation_is_not_faked():
    response = _client().post(
        "/api/v1/auth/users",
        json={"email": "new@corp.example.com", "username": "new", "password": "a-long-enough-pass"},
    )
    assert response.status_code == 501
    assert "/api/v1/organizations/{org_id}/members/invite" in response.json()["detail"]
