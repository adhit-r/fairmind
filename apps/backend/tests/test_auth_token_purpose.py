"""Human API dependencies reject credentials minted for another purpose."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from api.main import app
from config.auth import User, UserRole, auth_manager


def _human_user() -> User:
    return User(
        id="token-purpose-user",
        email="token-purpose@example.test",
        username="token-purpose-user",
        role=UserRole.ADMIN,
        created_at=datetime(2026, 8, 13, tzinfo=timezone.utc),
        permissions=["*"],
    )


@pytest.mark.parametrize("credential_kind", ("refresh", "api_key"))
def test_human_route_rejects_non_access_bearer_credentials(
    credential_kind: str,
) -> None:
    user = _human_user()
    token = (
        auth_manager.create_refresh_token(user)
        if credential_kind == "refresh"
        else auth_manager.create_api_key(user, "automation-key")
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token. Please login again."}


def test_human_route_accepts_access_bearer_credential() -> None:
    token = auth_manager.create_access_token(_human_user())

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["id"] == "token-purpose-user"
