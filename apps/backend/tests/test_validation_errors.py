"""A rejected request names the field and reason, in every environment, and never echoes input."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_validation_error_names_the_field_without_echoing_input():
    secret = "never-echo-this-password"
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "A", "email": "not-an-email", "org_name": "B", "password": secret},
    )

    assert response.status_code == 422
    details = response.json()["details"]
    assert any(d["loc"][-1] == "email" and d["msg"] for d in details)
    assert all(set(d) == {"loc", "msg", "type"} for d in details)
    assert secret not in response.text
