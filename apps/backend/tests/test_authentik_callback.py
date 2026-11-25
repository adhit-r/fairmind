"""Authentik proves identity; FairMind decides rights (audit S7).

The callback signs a person in as their existing FairMind account and grants
nothing from IdP groups, so adding someone to an IdP group cannot make them an
admin of every tenant, and SSO cannot create an account that skipped approval.
"""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api.routes import auth
from config.auth import User, UserRole


class _Exchange:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def post(self, *_args, **_kwargs):
        return SimpleNamespace(status_code=200, json=lambda: {"access_token": "idp-token"}, text="")


@pytest.fixture
def idp(monkeypatch):
    for name, value in {
        "authentik_enabled": True,
        "authentik_server_url": "https://idp.test",
        "authentik_oauth_client_id": "client",
        "authentik_oauth_client_secret": "secret",
        "authentik_oauth_redirect_uri": "https://app.test/auth/callback",
    }.items():
        monkeypatch.setattr(auth.settings, name, value)
    monkeypatch.setattr(auth.httpx, "AsyncClient", lambda **_: _Exchange())
    claims = {"sub": "idp-123", "email": "person@corp.test", "groups": ["fairmind-admin"]}

    async def validate(_token):
        return claims

    monkeypatch.setattr(auth, "get_authentik_config", lambda: SimpleNamespace(validate_token=validate))

    async def no_cache(*_args, **_kwargs):
        return None

    monkeypatch.setattr(auth.cache_manager, "set", no_cache)
    return claims


@pytest.mark.asyncio
async def test_unknown_email_is_refused(idp, monkeypatch):
    async def nobody(_email):
        return None

    monkeypatch.setattr(auth.auth_manager, "get_user_by_email", nobody)
    with pytest.raises(HTTPException) as refused:
        await auth.authentik_oauth_callback(code="c", state="s")
    assert refused.value.status_code == 403


@pytest.mark.asyncio
async def test_idp_admin_group_grants_nothing(idp, monkeypatch):
    analyst = User(id="u-1", email="person@corp.test", username="person", role=UserRole.ANALYST,
                   created_at=datetime.now(timezone.utc), org_id="org-1")

    async def stored(_email):
        return analyst

    monkeypatch.setattr(auth.auth_manager, "get_user_by_email", stored)
    response = await auth.authentik_oauth_callback(code="c", state="s")

    assert response.user["id"] == "u-1"
    assert response.user["role"] == "analyst"  # not admin, despite the fairmind-admin group
    claims = auth.auth_manager.jwt_manager.verify_token(response.access_token)
    assert claims["user_id"] == "u-1" and "*" not in claims.get("permissions", [])
