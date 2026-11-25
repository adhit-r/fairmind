"""Monitors read the status code: not ready or unhealthy must be a 5xx (audit C5)."""

from fastapi.testclient import TestClient

from api.main import app
from services.health import health_service


def test_readiness_is_503_when_the_database_is_down(monkeypatch):
    async def down():
        return {"status": "unhealthy"}

    with TestClient(app) as client:  # runs startup, which connects the database
        assert client.get("/health/ready").status_code == 200
        monkeypatch.setattr(health_service, "_check_database", down)
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
