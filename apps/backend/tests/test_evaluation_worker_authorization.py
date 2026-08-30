"""Fail-closed authorization contract for future Assurance V2 workers."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from config.auth import (
    PrincipalKind,
    TokenData,
    TokenType,
    User,
    UserRole,
    auth_manager,
    get_current_active_user,
    get_current_user,
)
from config.jwt_exceptions import InvalidTokenException
from src.api.evaluation_permissions import require_evaluation_worker_principal


NOW = datetime(2026, 8, 29, tzinfo=timezone.utc)
WORKER_PERMISSION = "evaluation:worker"


def _signed_service_token(token_type: TokenType = TokenType.ACCESS) -> str:
    return auth_manager.jwt_manager.create_token(
        {
            "sub": "worker-a",
            "user_id": "worker-a",
            "email": "worker-a@example.test",
            "roles": [UserRole.API_USER.value],
            "permissions": [WORKER_PERMISSION],
            "token_type": token_type.value,
            "principal_kind": PrincipalKind.SERVICE.value,
            "organization_id": "org-a",
        }
    )


def _principal(
    *,
    principal_kind: PrincipalKind = PrincipalKind.HUMAN,
    token_type: TokenType = TokenType.ACCESS,
    role: UserRole = UserRole.VIEWER,
    permissions: list[str] | None = None,
    organization_id: str | None = "org-a",
) -> TokenData:
    return TokenData(
        user_id="principal-a",
        email="principal-a@example.test",
        role=role,
        token_type=token_type,
        principal_kind=principal_kind,
        organization_id=organization_id,
        exp=NOW,
        iat=NOW,
        permissions=permissions or [],
    )


@pytest.mark.parametrize(
    "principal",
    (
        _principal(permissions=[WORKER_PERMISSION]),
        _principal(role=UserRole.ADMIN, permissions=[WORKER_PERMISSION]),
        _principal(role=UserRole.ADMIN, permissions=["*"]),
        _principal(
            principal_kind=PrincipalKind.SERVICE,
            token_type=TokenType.API_KEY,
            permissions=[WORKER_PERMISSION],
        ),
        _principal(
            principal_kind=PrincipalKind.SERVICE,
            permissions=["*"],
        ),
        _principal(
            principal_kind=PrincipalKind.SERVICE,
            permissions=["*", WORKER_PERMISSION],
        ),
        _principal(principal_kind=PrincipalKind.SERVICE),
        _principal(
            principal_kind=PrincipalKind.SERVICE,
            permissions=[WORKER_PERMISSION],
            organization_id=None,
        ),
    ),
)
def test_worker_authorization_rejects_non_service_or_nonliteral_authority(
    principal: TokenData,
) -> None:
    with pytest.raises(HTTPException) as denied:
        require_evaluation_worker_principal(principal, expected_org_id="org-a")

    assert denied.value.status_code == 403
    assert denied.value.detail == {
        "code": "evaluation_worker_forbidden",
        "message": "A tenant-bound FairMind worker principal is required.",
    }


def test_worker_authorization_rejects_cross_tenant_service_principal() -> None:
    principal = _principal(
        principal_kind=PrincipalKind.SERVICE,
        permissions=[WORKER_PERMISSION],
        organization_id="org-b",
    )

    with pytest.raises(HTTPException) as denied:
        require_evaluation_worker_principal(principal, expected_org_id="org-a")

    assert denied.value.status_code == 403
    assert denied.value.detail["code"] == "evaluation_worker_forbidden"


@pytest.mark.parametrize(
    "permissions",
    (
        [WORKER_PERMISSION, WORKER_PERMISSION],
        [WORKER_PERMISSION, "Evaluation:worker"],
        [WORKER_PERMISSION, "evaluation::worker"],
        [WORKER_PERMISSION, "a" * 129],
        [WORKER_PERMISSION, *(f"scope:p{index}" for index in range(64))],
    ),
)
def test_worker_authorization_rejects_noncanonical_permission_arrays(
    permissions: list[str],
) -> None:
    principal = _principal(
        principal_kind=PrincipalKind.SERVICE,
        permissions=permissions,
    )

    with pytest.raises(HTTPException) as denied:
        require_evaluation_worker_principal(principal, expected_org_id="org-a")

    assert denied.value.status_code == 403
    assert denied.value.detail["code"] == "evaluation_worker_forbidden"


@pytest.mark.parametrize("expected_org_id", ("", " org-a", "org-a "))
def test_worker_authorization_rejects_noncanonical_expected_tenant(
    expected_org_id: str,
) -> None:
    principal = _principal(
        principal_kind=PrincipalKind.SERVICE,
        permissions=[WORKER_PERMISSION],
    )

    with pytest.raises(HTTPException) as denied:
        require_evaluation_worker_principal(
            principal,
            expected_org_id=expected_org_id,
        )

    assert denied.value.status_code == 403
    assert denied.value.detail["code"] == "evaluation_worker_forbidden"


def test_worker_authorization_accepts_exact_tenant_service_principal() -> None:
    principal = _principal(
        principal_kind=PrincipalKind.SERVICE,
        permissions=[WORKER_PERMISSION],
    )

    assert (
        require_evaluation_worker_principal(principal, expected_org_id="org-a")
        is principal
    )


@pytest.mark.asyncio
async def test_human_dependency_rejects_service_principal() -> None:
    principal = _principal(
        principal_kind=PrincipalKind.SERVICE,
        permissions=[WORKER_PERMISSION],
    )

    with pytest.raises(InvalidTokenException, match="Human access token required"):
        await get_current_active_user(principal)


@pytest.mark.asyncio
async def test_verified_token_projects_tenant_bound_service_principal() -> None:
    token = _signed_service_token()

    principal = await auth_manager.verify_token(token)

    assert principal.principal_kind is PrincipalKind.SERVICE
    assert principal.organization_id == "org-a"
    assert require_evaluation_worker_principal(principal, expected_org_id="org-a")


@pytest.mark.asyncio
async def test_verified_service_token_requires_exact_organization_claim() -> None:
    token = auth_manager.jwt_manager.create_token(
        {
            "sub": "worker-a",
            "user_id": "worker-a",
            "email": "worker-a@example.test",
            "roles": [UserRole.API_USER.value],
            "permissions": [WORKER_PERMISSION],
            "token_type": TokenType.ACCESS.value,
            "principal_kind": PrincipalKind.SERVICE.value,
        }
    )

    with pytest.raises(
        InvalidTokenException,
        match="Service principal organization is invalid",
    ):
        await auth_manager.verify_token(token)


def _signed_legacy_human_token(token_type: TokenType) -> str:
    """Model a still-valid human token minted before principal kinds existed."""

    return auth_manager.jwt_manager.create_token(
        {
            "sub": "legacy-human-a",
            "user_id": "legacy-human-a",
            "email": "legacy-human-a@example.test",
            "roles": [UserRole.VIEWER.value],
            "permissions": [],
            "token_type": token_type.value,
        }
    )


@pytest.mark.asyncio
async def test_legacy_untyped_access_token_remains_human_during_migration() -> None:
    principal = await auth_manager.verify_token(
        _signed_legacy_human_token(TokenType.ACCESS)
    )

    assert principal.principal_kind is PrincipalKind.HUMAN
    assert principal.token_type is TokenType.ACCESS


@pytest.mark.asyncio
async def test_legacy_untyped_refresh_token_remains_exchangeable() -> None:
    access_token = await auth_manager.refresh_access_token(
        _signed_legacy_human_token(TokenType.REFRESH)
    )

    payload = auth_manager.jwt_manager.decode_token_unsafe(access_token)
    assert payload is not None
    assert payload["principal_kind"] == PrincipalKind.HUMAN.value
    assert payload["token_type"] == TokenType.ACCESS.value


@pytest.mark.asyncio
async def test_unknown_explicit_principal_kind_is_rejected() -> None:
    token = auth_manager.jwt_manager.create_token(
        {
            "sub": "unknown-a",
            "user_id": "unknown-a",
            "email": "unknown-a@example.test",
            "roles": [UserRole.VIEWER.value],
            "permissions": [],
            "token_type": TokenType.ACCESS.value,
            "principal_kind": "robot",
        }
    )

    with pytest.raises(InvalidTokenException, match="Invalid principal kind"):
        await auth_manager.verify_token(token)


@pytest.mark.asyncio
async def test_current_user_dependency_rejects_service_principal() -> None:
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=_signed_service_token(),
    )

    with pytest.raises(InvalidTokenException, match="Human principal required"):
        await get_current_user(credentials)


@pytest.mark.asyncio
async def test_refresh_rejects_service_to_human_purpose_exchange() -> None:
    with pytest.raises(InvalidTokenException, match="Human refresh token required"):
        await auth_manager.refresh_access_token(
            _signed_service_token(TokenType.REFRESH)
        )


def test_human_token_issuers_mark_principal_kind_explicitly() -> None:
    user = User(
        id="human-a",
        email="human-a@example.test",
        username="human-a",
        role=UserRole.ADMIN,
        created_at=NOW,
        permissions=[WORKER_PERMISSION],
    )

    for token in (
        auth_manager.create_access_token(user),
        auth_manager.create_refresh_token(user),
        auth_manager.create_api_key(user, "automation-key"),
    ):
        payload = auth_manager.jwt_manager.decode_token_unsafe(token)
        assert payload is not None
        assert payload["principal_kind"] == PrincipalKind.HUMAN.value
