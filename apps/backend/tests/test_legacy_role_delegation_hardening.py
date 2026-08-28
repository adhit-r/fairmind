"""Regression contracts for legacy organization-role delegation boundaries."""

from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from api.routes import org_management
from config.auth import TokenData, TokenType, UserRole
from src.application.services.governance_assurance_service import GovernanceAssuranceService


ORG_ID = str(uuid.uuid4())
ACTOR_ID = str(uuid.uuid4())
TARGET_ID = str(uuid.uuid4())
RESERVED_DELEGATION_PERMISSIONS = (
    "evaluation:trust:admin",
    "evaluation:worker",
    "evaluation:separation:override",
)
UNTRUSTED_STORED_ROLE_PERMISSIONS = (
    json.dumps(["evaluation:trust:admin"]),
    "{not-json",
    json.dumps({"model:write": True}),
    ("model:write",),
    {"model:write": True},
)


def _token(*, user_id: str = ACTOR_ID, email: str = "actor@example.test") -> TokenData:
    now = datetime.now(timezone.utc)
    return TokenData(
        user_id=user_id,
        email=email,
        role=UserRole.ANALYST,
        token_type=TokenType.ACCESS,
        iat=now,
        exp=now,
    )


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/",
            "headers": [],
            "client": ("127.0.0.1", 1234),
        }
    )


class _ScalarResult:
    def __init__(self, value: object) -> None:
        self.value = value

    def scalar_one_or_none(self) -> object:
        return self.value


class _MembershipSession:
    def __init__(self, permissions: object) -> None:
        self._results = iter(("assessor", permissions))

    def execute(self, _statement: object) -> _ScalarResult:
        return _ScalarResult(next(self._results))


def _membership(permissions: object):
    return GovernanceAssuranceService(_MembershipSession(permissions)).membership(ORG_ID, ACTOR_ID)


@pytest.mark.parametrize(
    "malformed_permissions",
    [
        "model:write",
        {"model:write": True},
        ("model:write",),
        ["model:write", "model:write"],
        ["model:write", 1],
        ["model:write", "not a valid permission"],
        [f"scope:permission-{index}" for index in range(65)],
    ],
)
def test_assurance_membership_fails_closed_for_malformed_role_permissions(
    malformed_permissions: object,
) -> None:
    membership = _membership(malformed_permissions)

    assert membership is not None
    assert membership.permissions == ()
    assert not GovernanceAssuranceService.may_mutate(membership)


def test_assurance_membership_keeps_valid_trust_admin_but_strips_nonhuman_permissions() -> None:
    membership = _membership(
        [
            "model:write",
            "evaluation:trust:admin",
            "evaluation:worker",
            "evaluation:separation:override",
        ]
    )

    assert membership is not None
    assert membership.permissions == ("model:write", "evaluation:trust:admin")
    assert GovernanceAssuranceService.may_mutate(membership)


class _MembershipProbe:
    def __init__(self) -> None:
        self.queries: list[str] = []

    async def fetch_one(self, query: str, _values: dict) -> object:
        self.queries.append(query)
        if "COUNT(*)" in query:
            return {"count": 0}
        return None if "status = 'active'" in query else {"id": "inactive"}


@pytest.mark.asyncio
async def test_legacy_org_checks_require_active_membership() -> None:
    database = _MembershipProbe()

    assert await org_management._check_org_membership(ORG_ID, ACTOR_ID, database) is None
    assert not await org_management._check_org_admin(ORG_ID, ACTOR_ID, database)
    assert await org_management._count_org_admins(ORG_ID, database) == 0
    assert all("status = 'active'" in query for query in database.queries)


class _RoleMutationDatabase:
    def __init__(
        self,
        role_permissions: object,
        member_role: str = "analyst",
        is_admin: bool = True,
    ) -> None:
        self.role_permissions = role_permissions
        self.member_role = member_role
        self.is_admin = is_admin
        self.executions: list[tuple[str, dict]] = []
        self.invitation = {
            "id": "invitation-1",
            "org_id": ORG_ID,
            "email": "target@example.com",
            "role": "preseeded-role",
            "token": "token-1",
            "expires_at": datetime.utcnow() + timedelta(days=1),
            "status": "pending",
            "invited_by": ACTOR_ID,
            "created_at": datetime.utcnow(),
        }

    async def fetch_one(self, query: str, _values: dict) -> object:
        if "role IN ('admin', 'owner')" in query:
            return {"id": "active-admin"} if self.is_admin else None
        if "SELECT permissions FROM org_roles" in query:
            return {"permissions": self.role_permissions}
        if "SELECT id, user_id, role FROM org_members" in query:
            return {"id": "member-1", "user_id": TARGET_ID, "role": self.member_role}
        if "SELECT om.id FROM org_members om" in query:
            return None
        if "SELECT id FROM org_invitations" in query:
            return None
        if "SELECT id FROM org_roles" in query:
            return None
        if "SELECT * FROM org_invitations" in query:
            return self.invitation
        if "SELECT id, name FROM organizations" in query:
            return {"id": ORG_ID, "name": "Delegation Org"}
        if "SELECT id FROM org_members WHERE org_id" in query:
            return None
        if "SELECT primary_org_id FROM users" in query:
            return {"primary_org_id": None}
        return None

    async def execute(self, query: str, values: dict) -> str:
        self.executions.append((query, values))
        return "ok"


def _connection(database: _RoleMutationDatabase):
    @asynccontextmanager
    async def connection():
        yield database

    return connection


def _patch_org_management_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    database: _RoleMutationDatabase,
) -> AsyncMock:
    audit = AsyncMock()
    monkeypatch.setattr(org_management, "get_db_connection", _connection(database))
    monkeypatch.setattr(org_management, "_log_org_audit", audit)
    return audit


@pytest.mark.asyncio
async def test_inactive_admin_cannot_create_a_legacy_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = _RoleMutationDatabase(["model:write"], is_admin=False)
    audit = _patch_org_management_dependencies(monkeypatch, database)

    with pytest.raises(HTTPException) as error:
        await org_management.create_org_role(
            ORG_ID,
            org_management.CreateOrgRoleRequest(
                name="assessor", permissions=["model:write"]
            ),
            _request(),
            _token(),
        )

    assert error.value.status_code == 403
    assert not database.executions
    audit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("permission", RESERVED_DELEGATION_PERMISSIONS)
async def test_legacy_role_creation_rejects_reserved_permissions(
    monkeypatch: pytest.MonkeyPatch,
    permission: str,
) -> None:
    database = _RoleMutationDatabase(["model:write"])
    audit = _patch_org_management_dependencies(monkeypatch, database)

    with pytest.raises(HTTPException) as error:
        await org_management.create_org_role(
            ORG_ID,
            org_management.CreateOrgRoleRequest(
                name="ordinary-name", permissions=[permission]
            ),
            _request(),
            _token(),
        )

    assert error.value.status_code == 400
    assert not database.executions
    audit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("permission", RESERVED_DELEGATION_PERMISSIONS)
async def test_legacy_invitation_and_member_assignment_reject_preseeded_reserved_role(
    monkeypatch: pytest.MonkeyPatch,
    permission: str,
) -> None:
    invite_database = _RoleMutationDatabase([permission])
    invite_audit = _patch_org_management_dependencies(monkeypatch, invite_database)

    with pytest.raises(HTTPException) as invitation_error:
        await org_management.invite_member(
            ORG_ID,
            org_management.InviteMemberRequest(
                email="target@example.com", role="preseeded-role"
            ),
            _request(),
            _token(),
        )

    assert invitation_error.value.status_code == 400
    assert not invite_database.executions
    invite_audit.assert_not_awaited()

    assignment_database = _RoleMutationDatabase([permission])
    assignment_audit = _patch_org_management_dependencies(monkeypatch, assignment_database)

    with pytest.raises(HTTPException) as assignment_error:
        await org_management.update_member(
            ORG_ID,
            "member-1",
            org_management.UpdateMemberRequest(role="preseeded-role"),
            _request(),
            _token(),
        )

    assert assignment_error.value.status_code == 400
    assert not assignment_database.executions
    assignment_audit.assert_not_awaited()

    activation_database = _RoleMutationDatabase(
        [permission], member_role="preseeded-role"
    )
    activation_audit = _patch_org_management_dependencies(
        monkeypatch, activation_database
    )

    with pytest.raises(HTTPException) as activation_error:
        await org_management.update_member(
            ORG_ID,
            "member-1",
            org_management.UpdateMemberRequest(status="active"),
            _request(),
            _token(),
        )

    assert activation_error.value.status_code == 400
    assert not activation_database.executions
    activation_audit.assert_not_awaited()


@pytest.mark.asyncio
async def test_accepting_a_legacy_invitation_rejects_a_preseeded_trust_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = _RoleMutationDatabase(["evaluation:trust:admin"])
    audit = _patch_org_management_dependencies(monkeypatch, database)

    with pytest.raises(HTTPException) as error:
        await org_management.accept_invitation(
            "token-1",
            _request(),
            _token(user_id=TARGET_ID, email="target@example.com"),
        )

    assert error.value.status_code == 400
    assert not database.executions
    audit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("stored_permissions", UNTRUSTED_STORED_ROLE_PERMISSIONS)
async def test_untrusted_persisted_roles_cannot_be_invited_or_assigned(
    monkeypatch: pytest.MonkeyPatch,
    stored_permissions: object,
) -> None:
    invite_database = _RoleMutationDatabase(stored_permissions)
    invite_audit = _patch_org_management_dependencies(monkeypatch, invite_database)

    with pytest.raises(HTTPException) as invitation_error:
        await org_management.invite_member(
            ORG_ID,
            org_management.InviteMemberRequest(
                email="target@example.com", role="preseeded-role"
            ),
            _request(),
            _token(),
        )

    assert invitation_error.value.status_code == 400
    assert not invite_database.executions
    invite_audit.assert_not_awaited()

    assignment_database = _RoleMutationDatabase(stored_permissions)
    assignment_audit = _patch_org_management_dependencies(
        monkeypatch, assignment_database
    )

    with pytest.raises(HTTPException) as assignment_error:
        await org_management.update_member(
            ORG_ID,
            "member-1",
            org_management.UpdateMemberRequest(role="preseeded-role"),
            _request(),
            _token(),
        )

    assert assignment_error.value.status_code == 400
    assert not assignment_database.executions
    assignment_audit.assert_not_awaited()


@pytest.mark.asyncio
async def test_json_encoded_ordinary_custom_role_remains_invitable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = _RoleMutationDatabase(json.dumps(["model:write"]))
    _patch_org_management_dependencies(monkeypatch, database)

    def discard_task(coroutine):
        coroutine.close()
        return None

    monkeypatch.setattr(asyncio, "create_task", discard_task)
    invited = await org_management.invite_member(
        ORG_ID,
        org_management.InviteMemberRequest(email="target@example.com", role="assessor"),
        _request(),
        _token(),
    )

    assert invited["status"] == "pending"
    assert any(
        "INSERT INTO org_invitations" in query for query, _ in database.executions
    )


@pytest.mark.asyncio
async def test_ordinary_custom_role_creation_and_invitation_remain_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_database = _RoleMutationDatabase(["model:write"])
    _patch_org_management_dependencies(monkeypatch, create_database)

    created = await org_management.create_org_role(
        ORG_ID,
        org_management.CreateOrgRoleRequest(
            name="assessor", permissions=["model:write"]
        ),
        _request(),
        _token(),
    )

    assert created["status"] == "created"
    assert any("INSERT INTO org_roles" in query for query, _ in create_database.executions)

    invitation_database = _RoleMutationDatabase(["model:write"])
    _patch_org_management_dependencies(monkeypatch, invitation_database)

    def discard_task(coroutine):
        coroutine.close()
        return None

    monkeypatch.setattr(asyncio, "create_task", discard_task)
    invited = await org_management.invite_member(
        ORG_ID,
        org_management.InviteMemberRequest(email="target@example.com", role="assessor"),
        _request(),
        _token(),
    )

    assert invited["status"] == "pending"
    assert any(
        "INSERT INTO org_invitations" in query
        for query, _ in invitation_database.executions
    )
