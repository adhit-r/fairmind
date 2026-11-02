"""The sign-up route must be reachable without a token; the auth middleware used to reject it with 401."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_register_is_public():
    # An empty body fails validation in the route (422); the point is that the middleware lets it through.
    response = client.post("/api/v1/auth/register", json={})
    assert response.status_code != 401, response.text


def test_other_auth_routes_still_need_a_token():
    assert client.get("/api/v1/auth/me").status_code == 401
