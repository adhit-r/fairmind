"""Behavioral regressions for the internal JWT middleware's public routes."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from api.main import app as main_app
from config.auth import PrincipalKind, TokenType, UserRole, auth_manager
from config.jwt_exceptions import InvalidTokenException
from core.middleware.auth import NeonAuthMiddleware
from middleware.security import (
    JWTAuthenticationMiddleware,
    get_current_user_from_request,
)


def _signed_service_token() -> str:
    return auth_manager.jwt_manager.create_token(
        {
            "sub": "worker-a",
            "user_id": "worker-a",
            "email": "worker-a@example.test",
            "roles": [UserRole.API_USER.value],
            "permissions": ["evaluation:worker"],
            "token_type": TokenType.ACCESS.value,
            "principal_kind": PrincipalKind.SERVICE.value,
            "organization_id": "org-a",
        }
    )


def _client() -> TestClient:
    app = FastAPI()
    app.add_middleware(JWTAuthenticationMiddleware)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"path": "root"}

    @app.get("/health/live")
    async def health_live() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/health-private")
    async def health_private() -> dict[str, bool]:
        return {"protected": True}

    @app.get("/api")
    async def api_info() -> dict[str, str]:
        return {"path": "api"}

    @app.post("/api/v1/auth/refresh")
    async def refresh() -> dict[str, bool]:
        return {"refreshed": True}

    @app.get("/api/v1/auth/login")
    async def login_wrong_method() -> dict[str, bool]:
        return {"protected": True}

    @app.post("/api/v1/auth/login-admin")
    async def login_admin() -> dict[str, bool]:
        return {"protected": True}

    @app.post("/api/v1/register")
    async def register() -> dict[str, bool]:
        return {"public": True}

    @app.post("/api/v1/auth/callback")
    async def callback() -> dict[str, bool]:
        return {"public": True}

    @app.post("/api/v1/auth/oauth2/validate")
    async def oauth2_validate() -> dict[str, bool]:
        return {"public": True}

    @app.post("/api/v1/auth/oauth2/sync-user")
    async def oauth2_sync_user() -> dict[str, bool]:
        return {"public": True}

    @app.post("/api/v1/auth/oauth2/refresh")
    async def oauth2_refresh() -> dict[str, bool]:
        return {"public": True}

    @app.get("/api/v1/protected")
    async def protected() -> dict[str, bool]:
        return {"protected": True}

    return TestClient(app)


def _neon_client() -> TestClient:
    app = FastAPI()
    app.add_middleware(NeonAuthMiddleware)

    @app.get("/api/v1/protected")
    async def protected() -> dict[str, bool]:
        return {"protected": True}

    return TestClient(app)


def test_root_path_remains_public_without_a_token() -> None:
    response = _client().get("/")

    assert response.status_code == 200
    assert response.json() == {"path": "root"}


def test_non_root_path_does_not_inherit_the_root_public_exception() -> None:
    response = _client().get("/api/v1/protected")

    assert response.status_code == 401
    assert response.json()["error"] == "Authentication required"
    assert response.json()["detail"] == "Authentication required"


def test_service_principal_cannot_cross_app_wide_human_middleware() -> None:
    response = _client().get(
        "/api/v1/protected",
        headers={"Authorization": f"Bearer {_signed_service_token()}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_main_app_rejects_service_principal_before_legacy_governance_route() -> None:
    with TestClient(main_app) as client:
        response = client.get(
            "/api/v1/ai-governance/status",
            headers={"Authorization": f"Bearer {_signed_service_token()}"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


@pytest.mark.asyncio
async def test_request_state_helper_rejects_service_principal() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/protected",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
        }
    )
    request.state.user = await auth_manager.verify_token(_signed_service_token())
    request.state.authenticated = True

    with pytest.raises(InvalidTokenException, match="Human principal required"):
        await get_current_user_from_request(request)


def test_neon_auth_middleware_rejects_service_principal() -> None:
    response = _neon_client().get(
        "/api/v1/protected",
        headers={"Authorization": f"Bearer {_signed_service_token()}"},
    )

    assert response.status_code == 401
    assert response.text == "Service principals require a dedicated route"


def test_non_root_public_prefixes_keep_matching_descendant_paths() -> None:
    response = _client().get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "live"}


def test_api_info_path_is_an_exact_public_exception() -> None:
    response = _client().get("/api")

    assert response.status_code == 200
    assert response.json() == {"path": "api"}


def test_refresh_endpoint_is_public_without_an_access_token() -> None:
    response = _client().post("/api/v1/auth/refresh")

    assert response.status_code == 200
    assert response.json() == {"refreshed": True}


@pytest.mark.parametrize(
    "path",
    [
        "/health-private",
        "/api/v1/auth/login-admin",
    ],
)
def test_public_route_names_do_not_make_sibling_paths_public(path: str) -> None:
    response = _client().request(
        "GET" if path == "/health-private" else "POST",
        path,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_public_route_requires_the_declared_http_method() -> None:
    response = _client().get("/api/v1/auth/login")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/register",
        "/api/v1/auth/callback",
        "/api/v1/auth/oauth2/validate",
        "/api/v1/auth/oauth2/sync-user",
        "/api/v1/auth/oauth2/refresh",
    ],
)
def test_identity_bootstrap_routes_are_public_without_an_access_token(path: str) -> None:
    response = _client().post(path)

    assert response.status_code == 200
    assert response.json() == {"public": True}


@pytest.mark.parametrize(
    ("path", "body", "expected_status"),
    [
        # Registration is an optional router in the lean test environment; a
        # 405 still proves JWT did not intercept its documented public path.
        ("/api/v1/register", {}, 405),
        ("/api/v1/auth/callback", None, 422),
    ],
)
def test_main_app_reaches_public_identity_bootstrap_validation(
    path: str,
    body: dict[str, object] | None,
    expected_status: int,
) -> None:
    client = TestClient(main_app)

    response = client.post(path, json=body) if body is not None else client.post(path)

    assert response.status_code == expected_status
