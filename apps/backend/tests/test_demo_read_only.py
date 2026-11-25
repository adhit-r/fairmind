"""The public demo account reads everything and changes nothing."""

from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import settings
from middleware.security import DemoReadOnlyMiddleware

DEMO = "demo@fairmind.example"


def _client(email: str | None) -> TestClient:
    app = FastAPI()

    @app.api_route("/api/v1/systems", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def systems() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/v1/auth/logout")
    async def logout() -> dict[str, bool]:
        return {"ok": True}

    # Inner first: the guard runs after this stand-in for the auth middleware sets the user.
    app.add_middleware(DemoReadOnlyMiddleware)

    class FakeAuth(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if email:
                request.state.user = SimpleNamespace(email=email)
            return await call_next(request)

    app.add_middleware(FakeAuth)
    return TestClient(app)


def test_demo_user_reads_but_cannot_write(monkeypatch):
    monkeypatch.setattr(settings, "demo_user_email", DEMO)
    c = _client(DEMO.upper())
    assert c.get("/api/v1/systems").status_code == 200
    for method in ("post", "put", "patch", "delete"):
        r = getattr(c, method)("/api/v1/systems")
        assert r.status_code == 403, method
        assert "read-only" in r.json()["detail"]
    assert c.post("/api/v1/auth/logout").status_code == 200


def test_other_users_and_disabled_demo_are_untouched(monkeypatch):
    monkeypatch.setattr(settings, "demo_user_email", DEMO)
    assert _client("someone@fairmind.example").post("/api/v1/systems").status_code == 200
    assert _client(None).post("/api/v1/systems").status_code == 200
    monkeypatch.setattr(settings, "demo_user_email", None)
    assert _client(DEMO).post("/api/v1/systems").status_code == 200


def test_demo_sign_in_is_public_and_off_without_a_demo_user(monkeypatch):
    from api.main import app

    monkeypatch.setattr(settings, "demo_user_email", None)
    r = TestClient(app).post("/api/v1/auth/demo")
    assert r.status_code == 404  # reached the route without a token: public, and off
