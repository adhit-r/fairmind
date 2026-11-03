from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from config.auth import TokenData, TokenType, UserRole, get_current_active_user


class OrganizationListDatabase:
    def __init__(self) -> None:
        self.query = ""
        self.values = {}

    async def fetch_all(self, query: str, values: dict):
        self.query = query
        self.values = values
        return [
            {
                "id": "org-custom",
                "name": "Custom Role Org",
                "slug": "custom-role-org",
                "domain": None,
                "owner_id": "owner-1",
                "created_at": datetime(2026, 7, 17, tzinfo=timezone.utc),
                "role": "assessor",
                "permissions": '["model:read", "model:write"]',
            },
            {
                "id": "org-owner",
                "name": "Owner Org",
                "slug": "owner-org",
                "domain": "owner.test",
                "owner_id": "user-1",
                "created_at": datetime(2026, 7, 16, tzinfo=timezone.utc),
                "role": "owner",
                "permissions": None,
            },
        ]


def test_organization_list_supplies_effective_custom_role_permissions(monkeypatch) -> None:
    from api.routes import org_management
    from api.main import app as production_app

    assert any(
        route.path == "/api/v1/organizations" and "GET" in route.methods
        for route in production_app.routes
    )

    database = OrganizationListDatabase()

    @asynccontextmanager
    async def connection():
        yield database

    async def current_user():
        now = datetime.now(timezone.utc)
        return TokenData(
            user_id="user-1",
            email="member@example.test",
            role=UserRole.ANALYST,
            token_type=TokenType.ACCESS,
            iat=now,
            exp=now,
        )

    monkeypatch.setattr(org_management, "get_db_connection", connection)
    app = FastAPI()
    app.include_router(org_management.router)
    app.dependency_overrides[get_current_active_user] = current_user

    with TestClient(app) as client:
        response = client.get("/api/v1/organizations")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "organizations": [
            {
                "id": "org-custom",
                "name": "Custom Role Org",
                "slug": "custom-role-org",
                "domain": None,
                "owner_id": "owner-1",
                "created_at": "2026-07-17T00:00:00+00:00",
                "role": "assessor",
                "permissions": ["model:read", "model:write"],
            },
            {
                "id": "org-owner",
                "name": "Owner Org",
                "slug": "owner-org",
                "domain": "owner.test",
                "owner_id": "user-1",
                "created_at": "2026-07-16T00:00:00+00:00",
                "role": "owner",
                "permissions": [],
            },
        ]
    }
    assert "LEFT JOIN org_roles" in database.query
    assert database.values == {"user_id": "user-1"}
