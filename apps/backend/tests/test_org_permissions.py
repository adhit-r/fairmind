"""
Tests for organization permission decorators.

Tests cover:
- @require_org_owner
- @require_org_admin
- @require_org_member
- @require_permission()
- @require_permissions()
- @audit_org_action()
- Decorator stacking
- Error handling and logging
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from uuid import uuid4

from core.decorators import (
    require_org_owner,
    require_org_admin,
    require_org_member,
    require_permission,
    require_permissions,
    audit_org_action,
    PermissionDenied,
)


# ── Test Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def mock_request():
    """Create a mock request with state object."""
    request = MagicMock(spec=Request)
    request.state = MagicMock()
    request.headers = {}
    request.client = MagicMock(host="192.168.1.1")
    return request


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    return AsyncMock()


@pytest.fixture
def sample_org_id():
    """Generate a sample organization ID."""
    return str(uuid4())


@pytest.fixture
def sample_user_id():
    """Generate a sample user ID."""
    return str(uuid4())


@pytest.fixture
def sample_owner_id():
    """Generate a sample owner ID."""
    return str(uuid4())


# ── @require_org_owner Tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_require_org_owner_success(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_org_owner allows owner to access endpoint."""
    mock_request.state.user_id = sample_user_id
    mock_db.fetch_one.return_value = {"owner_id": sample_user_id}

    @require_org_owner
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    result = await test_endpoint(
        org_id=sample_org_id, request=mock_request, db=mock_db
    )

    assert result == {"status": "success"}
    mock_db.fetch_one.assert_called_once()


@pytest.mark.asyncio
async def test_require_org_owner_denied(mock_request, mock_db, sample_org_id):
    """Test @require_org_owner denies non-owner access."""
    user_id = str(uuid4())
    owner_id = str(uuid4())
    mock_request.state.user_id = user_id
    mock_db.fetch_one.return_value = {"owner_id": owner_id}

    @require_org_owner
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    with pytest.raises(PermissionDenied) as exc_info:
        await test_endpoint(org_id=sample_org_id, request=mock_request, db=mock_db)

    assert "owner" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_require_org_owner_missing_context(mock_request, mock_db):
    """Test @require_org_owner fails with missing user context."""
    mock_request.state.user_id = None

    @require_org_owner
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    with pytest.raises(PermissionDenied):
        await test_endpoint(org_id="some-org", request=mock_request, db=mock_db)


# ── @require_org_admin Tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_require_org_admin_success_admin_role(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_org_admin allows admin role."""
    mock_request.state.user_id = sample_user_id
    mock_db.fetch_one.return_value = {"role": "admin"}

    @require_org_admin
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    result = await test_endpoint(
        org_id=sample_org_id, request=mock_request, db=mock_db
    )

    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_require_org_admin_success_owner_role(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_org_admin allows owner role."""
    mock_request.state.user_id = sample_user_id
    mock_db.fetch_one.return_value = {"role": "owner"}

    @require_org_admin
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    result = await test_endpoint(
        org_id=sample_org_id, request=mock_request, db=mock_db
    )

    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_require_org_admin_denied_member_role(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_org_admin denies member role."""
    mock_request.state.user_id = sample_user_id
    mock_db.fetch_one.return_value = {"role": "member"}

    @require_org_admin
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    with pytest.raises(PermissionDenied) as exc_info:
        await test_endpoint(org_id=sample_org_id, request=mock_request, db=mock_db)

    assert "admin" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_require_org_admin_denied_not_member(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_org_admin denies non-member."""
    mock_request.state.user_id = sample_user_id
    mock_db.fetch_one.return_value = None

    @require_org_admin
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    with pytest.raises(PermissionDenied):
        await test_endpoint(org_id=sample_org_id, request=mock_request, db=mock_db)


# ── @require_org_member Tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_require_org_member_success(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_org_member allows member access."""
    mock_request.state.user_id = sample_user_id
    mock_db.fetch_one.return_value = {"id": "member-id"}

    @require_org_member
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    result = await test_endpoint(
        org_id=sample_org_id, request=mock_request, db=mock_db
    )

    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_require_org_member_denied_not_member(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_org_member denies non-member."""
    mock_request.state.user_id = sample_user_id
    mock_db.fetch_one.return_value = None

    @require_org_member
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    with pytest.raises(PermissionDenied) as exc_info:
        await test_endpoint(org_id=sample_org_id, request=mock_request, db=mock_db)

    assert "member" in str(exc_info.value.detail).lower()


# ── @require_permission Tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_require_permission_success(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_permission allows user with permission."""
    mock_request.state.user_id = sample_user_id

    # First call: get user's role
    # Second call: get role's permissions
    mock_db.fetch_one.side_effect = [
        {"role": "admin"},
        {"permissions": ["members:invite", "members:remove"]},
    ]

    @require_permission("members:invite")
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    result = await test_endpoint(
        org_id=sample_org_id, request=mock_request, db=mock_db
    )

    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_require_permission_denied(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_permission denies user without permission."""
    mock_request.state.user_id = sample_user_id

    # First call: get user's role
    # Second call: get role's permissions (doesn't include requested permission)
    mock_db.fetch_one.side_effect = [
        {"role": "member"},
        {"permissions": ["reports:view"]},
    ]

    @require_permission("members:invite")
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    with pytest.raises(PermissionDenied) as exc_info:
        await test_endpoint(org_id=sample_org_id, request=mock_request, db=mock_db)

    assert "members:invite" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_require_permission_denied_not_member(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_permission denies non-member."""
    mock_request.state.user_id = sample_user_id
    mock_db.fetch_one.return_value = None

    @require_permission("members:invite")
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    with pytest.raises(PermissionDenied):
        await test_endpoint(org_id=sample_org_id, request=mock_request, db=mock_db)


# ── @require_permissions Tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_require_permissions_all_success(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_permissions with require_all=True and all permissions present."""
    mock_request.state.user_id = sample_user_id

    mock_db.fetch_one.side_effect = [
        {"role": "admin"},
        {"permissions": ["reports:view", "reports:export", "reports:schedule"]},
    ]

    @require_permissions(["reports:view", "reports:export"])
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    result = await test_endpoint(
        org_id=sample_org_id, request=mock_request, db=mock_db
    )

    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_require_permissions_all_denied(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_permissions with require_all=True missing one permission."""
    mock_request.state.user_id = sample_user_id

    mock_db.fetch_one.side_effect = [
        {"role": "member"},
        {"permissions": ["reports:view"]},  # Missing reports:export
    ]

    @require_permissions(["reports:view", "reports:export"], require_all=True)
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    with pytest.raises(PermissionDenied) as exc_info:
        await test_endpoint(org_id=sample_org_id, request=mock_request, db=mock_db)

    assert "Missing permissions" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_require_permissions_any_success(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_permissions with require_all=False and one permission present."""
    mock_request.state.user_id = sample_user_id

    mock_db.fetch_one.side_effect = [
        {"role": "member"},
        {"permissions": ["reports:view"]},  # Has one of the required permissions
    ]

    @require_permissions(
        ["reports:export", "reports:view", "reports:admin"], require_all=False
    )
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    result = await test_endpoint(
        org_id=sample_org_id, request=mock_request, db=mock_db
    )

    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_require_permissions_any_denied(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @require_permissions with require_all=False and no permissions match."""
    mock_request.state.user_id = sample_user_id

    mock_db.fetch_one.side_effect = [
        {"role": "member"},
        {"permissions": ["compliance:view"]},  # Doesn't match any required permissions
    ]

    @require_permissions(
        ["reports:export", "reports:view"], require_all=False
    )
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    with pytest.raises(PermissionDenied) as exc_info:
        await test_endpoint(org_id=sample_org_id, request=mock_request, db=mock_db)

    assert "Must have one of" in str(exc_info.value.detail)


# ── @audit_org_action Tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_org_action_success(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @audit_org_action logs successful action."""
    mock_request.state.user_id = sample_user_id
    mock_request.state.ip_address = "192.168.1.100"
    mock_request.headers = {}
    mock_request.client = MagicMock(host="192.168.1.1")
    mock_db.execute = AsyncMock()

    @audit_org_action("invite_member", "org_member")
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    result = await test_endpoint(
        org_id=sample_org_id, request=mock_request, db=mock_db
    )

    assert result == {"status": "success"}

    # Verify audit log was written
    mock_db.execute.assert_called_once()
    call_args = mock_db.execute.call_args
    assert "org_audit_logs" in call_args[0][0]
    assert call_args[1]["action"] == "invite_member"
    assert call_args[1]["resource_type"] == "org_member"
    assert call_args[1]["status"] == "success"


@pytest.mark.asyncio
async def test_audit_org_action_failure(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @audit_org_action logs failed action."""
    mock_request.state.user_id = sample_user_id
    mock_request.state.ip_address = "192.168.1.100"
    mock_request.headers = {}
    mock_request.client = MagicMock(host="192.168.1.1")
    mock_db.execute = AsyncMock()

    @audit_org_action("remove_member", "org_member")
    async def test_endpoint(org_id: str, request: Request, db):
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        await test_endpoint(
            org_id=sample_org_id, request=mock_request, db=mock_db
        )

    # Verify failure was logged
    mock_db.execute.assert_called_once()
    call_args = mock_db.execute.call_args
    assert call_args[1]["status"] == "failure"
    assert "error_message" in call_args[1]


@pytest.mark.asyncio
async def test_audit_org_action_ip_extraction_forwarded(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @audit_org_action extracts IP from X-Forwarded-For header."""
    mock_request.state.user_id = sample_user_id
    mock_request.state.ip_address = None
    mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 192.168.1.1"}
    mock_request.client = MagicMock(host="10.0.0.1")
    mock_db.execute = AsyncMock()

    @audit_org_action("test_action", "test_resource")
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    await test_endpoint(
        org_id=sample_org_id, request=mock_request, db=mock_db
    )

    # Verify correct IP was logged
    call_args = mock_db.execute.call_args
    assert call_args[1]["ip_address"] == "203.0.113.1"


@pytest.mark.asyncio
async def test_audit_org_action_ip_extraction_real_ip(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @audit_org_action extracts IP from X-Real-IP header."""
    mock_request.state.user_id = sample_user_id
    mock_request.state.ip_address = None
    mock_request.headers = {"X-Real-IP": "203.0.113.2"}
    mock_request.client = MagicMock(host="10.0.0.1")
    mock_db.execute = AsyncMock()

    @audit_org_action("test_action", "test_resource")
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    await test_endpoint(
        org_id=sample_org_id, request=mock_request, db=mock_db
    )

    # Verify correct IP was logged
    call_args = mock_db.execute.call_args
    assert call_args[1]["ip_address"] == "203.0.113.2"


@pytest.mark.asyncio
async def test_audit_org_action_ip_extraction_client_host(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test @audit_org_action falls back to request.client.host."""
    mock_request.state.user_id = sample_user_id
    mock_request.state.ip_address = None
    mock_request.headers = {}
    mock_request.client = MagicMock(host="203.0.113.3")
    mock_db.execute = AsyncMock()

    @audit_org_action("test_action", "test_resource")
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    await test_endpoint(
        org_id=sample_org_id, request=mock_request, db=mock_db
    )

    # Verify correct IP was logged
    call_args = mock_db.execute.call_args
    assert call_args[1]["ip_address"] == "203.0.113.3"


# ── Decorator Stacking Tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_decorator_stacking_success(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test decorators stack correctly in success case."""
    mock_request.state.user_id = sample_user_id
    mock_request.state.ip_address = "192.168.1.100"
    mock_request.headers = {}
    mock_request.client = MagicMock(host="192.168.1.1")

    # Setup mock responses:
    # 1. require_org_admin: get user's role
    # 2. audit_org_action: insert audit log
    mock_db.fetch_one = AsyncMock(return_value={"role": "admin"})
    mock_db.execute = AsyncMock()

    @audit_org_action("test_action", "test_resource")
    @require_org_admin
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    result = await test_endpoint(
        org_id=sample_org_id, request=mock_request, db=mock_db
    )

    assert result == {"status": "success"}

    # Verify both checks ran:
    # 1. Permission check (fetch_one for role)
    # 2. Audit log (execute for audit)
    assert mock_db.fetch_one.called
    assert mock_db.execute.called


@pytest.mark.asyncio
async def test_decorator_stacking_permission_denied(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test that permission denial prevents audit logging."""
    mock_request.state.user_id = sample_user_id
    mock_request.state.ip_address = "192.168.1.100"
    mock_request.headers = {}
    mock_request.client = MagicMock(host="192.168.1.1")

    # Mock returns non-admin role
    mock_db.fetch_one = AsyncMock(return_value={"role": "member"})
    mock_db.execute = AsyncMock()

    @audit_org_action("test_action", "test_resource")
    @require_org_admin
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    with pytest.raises(PermissionDenied):
        await test_endpoint(
            org_id=sample_org_id, request=mock_request, db=mock_db
        )

    # Audit log should NOT have been called (permission denied before execution)
    mock_db.execute.assert_not_called()


# ── Error Handling Tests ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_database_error_handling(mock_request, sample_org_id, sample_user_id):
    """Test graceful handling of database errors."""
    mock_request.state.user_id = sample_user_id
    mock_db = AsyncMock()
    mock_db.fetch_one.side_effect = Exception("Database connection failed")

    @require_org_admin
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    with pytest.raises(PermissionDenied) as exc_info:
        await test_endpoint(org_id=sample_org_id, request=mock_request, db=mock_db)

    assert "failed" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_audit_logging_error_doesnt_break_request(
    mock_request, mock_db, sample_org_id, sample_user_id
):
    """Test that audit logging errors don't break successful requests."""
    mock_request.state.user_id = sample_user_id
    mock_request.state.ip_address = "192.168.1.100"
    mock_request.headers = {}
    mock_request.client = MagicMock(host="192.168.1.1")

    # Mock execute to fail (audit logging fails)
    mock_db.execute = AsyncMock(side_effect=Exception("Audit log write failed"))

    @audit_org_action("test_action", "test_resource")
    async def test_endpoint(org_id: str, request: Request, db):
        return {"status": "success"}

    # Should succeed despite audit logging failure
    result = await test_endpoint(
        org_id=sample_org_id, request=mock_request, db=mock_db
    )

    assert result == {"status": "success"}
