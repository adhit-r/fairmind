"""API keys authorise requests; refresh tokens never do."""

import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from api.main import app
from config.auth import User, UserRole, auth_manager


def _user():
    return User(id=str(uuid.uuid4()), email="ci@test.invalid", username="ci", role=UserRole.ADMIN,
                created_at=datetime.now(timezone.utc), permissions=["*"], org_id=str(uuid.uuid4()))


def test_api_key_reads_governance_routes():
    client = TestClient(app, client=(f"apikey-{uuid.uuid4().hex[:8]}", 50000))
    key = auth_manager.create_api_key(_user(), "ci")
    assert client.get("/api/v1/ai-governance/systems", headers={"Authorization": f"Bearer {key}"}).status_code == 200


def test_refresh_token_is_still_refused():
    client = TestClient(app, client=(f"apikey-{uuid.uuid4().hex[:8]}", 50000))
    refresh = auth_manager.create_refresh_token(_user())
    assert client.get("/api/v1/ai-governance/systems", headers={"Authorization": f"Bearer {refresh}"}).status_code == 401
