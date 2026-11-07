"""CORS is the outermost middleware, so even an auth rejection is readable by the browser."""

from fastapi.testclient import TestClient

from api.main import app

ORIGIN = "http://localhost:1111"


def test_auth_rejection_carries_cors_headers():
    client = TestClient(app)
    response = client.get("/api/v1/auth/me", headers={"Origin": ORIGIN})
    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == ORIGIN
    preflight = client.options(
        "/api/v1/auth/me",
        headers={"Origin": ORIGIN, "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "authorization"},
    )
    assert preflight.status_code == 200 and preflight.headers["access-control-allow-origin"] == ORIGIN
