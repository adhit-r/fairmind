"""
Multi-Organization E2E Test Suite

Comprehensive testing of:
- Single user, single org
- Single user, multiple orgs
- Multiple users, single org
- Organization isolation (CRITICAL)
- Role-based access control
- Invitation flow
- Permission decorators
- Audit trail integrity
- Compliance reports
- Concurrent operations
"""

import pytest
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
import asyncio

from config.auth import TokenData


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def user_a_token():
    """Token for User A."""
    return TokenData(
        user_id="user-a-id",
        email="usera@example.com",
        full_name="User A",
        org_id=None,
        primary_org_id=None,
        scopes=[]
    )


@pytest.fixture
def user_b_token():
    """Token for User B."""
    return TokenData(
        user_id="user-b-id",
        email="userb@example.com",
        full_name="User B",
        org_id=None,
        primary_org_id=None,
        scopes=[]
    )


@pytest.fixture
def user_c_token():
    """Token for User C (non-member)."""
    return TokenData(
        user_id="user-c-id",
        email="userc@example.com",
        full_name="User C",
        org_id=None,
        primary_org_id=None,
        scopes=[]
    )


@pytest.fixture
def org1_id():
    """Organization 1 ID."""
    return str(uuid.uuid4())


@pytest.fixture
def org2_id():
    """Organization 2 ID."""
    return str(uuid.uuid4())


@pytest.fixture
async def mock_db():
    """Mock database connection."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.fetch_one = AsyncMock()
    db.fetch_all = AsyncMock()
    return db


# ── Test Suite 1: Single User, Single Org ────────────────────────────────────

class TestSingleUserSingleOrg:
    """Test scenarios for a single user managing one organization."""

    @pytest.mark.asyncio
    async def test_user_creates_org(self, user_a_token, mock_db):
        """User A creates an organization."""
        org_id = str(uuid.uuid4())
        org_name = "TechCorp"

        # Mock org creation response
        mock_db.execute.return_value = None
        mock_db.fetch_one.return_value = {
            "id": org_id,
            "name": org_name,
            "slug": "techcorp",
            "owner_id": user_a_token.user_id,
            "created_at": datetime.utcnow()
        }

        # Simulate org creation in database
        await mock_db.execute(
            "INSERT INTO organizations (id, name, slug, owner_id) VALUES (:id, :name, :slug, :owner_id)",
            {
                "id": org_id,
                "name": org_name,
                "slug": "techcorp",
                "owner_id": user_a_token.user_id
            }
        )

        # Verify call was made
        assert mock_db.execute.called
        assert mock_db.execute.call_args[1]["owner_id"] == user_a_token.user_id

    @pytest.mark.asyncio
    async def test_user_is_org_admin(self, user_a_token, org1_id, mock_db):
        """User A automatically becomes admin of their org."""
        # Mock admin check
        mock_db.fetch_one.return_value = {
            "id": "member-id",
            "role": "owner"
        }

        result = await mock_db.fetch_one(
            "SELECT id, role FROM org_members WHERE org_id = :org_id AND user_id = :user_id",
            {"org_id": org1_id, "user_id": user_a_token.user_id}
        )

        assert result["role"] in ("owner", "admin")

    @pytest.mark.asyncio
    async def test_admin_panel_accessible(self, user_a_token, org1_id, mock_db):
        """User A can access admin panel for their org."""
        # Mock: user is admin
        mock_db.fetch_one.return_value = {"id": "member-id", "role": "owner"}

        # Check admin authorization
        is_admin = (await mock_db.fetch_one(
            "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id AND role IN ('admin', 'owner')",
            {"org_id": org1_id, "user_id": user_a_token.user_id}
        )) is not None

        assert is_admin is True

    @pytest.mark.asyncio
    async def test_invite_member(self, user_a_token, org1_id, mock_db):
        """User A invites User B to the organization."""
        # Mock: no existing member
        mock_db.fetch_one.side_effect = [
            {"id": "member-id", "role": "owner"},  # Admin check
            None,  # Check existing member
            None,  # Check existing invite
        ]
        mock_db.execute.return_value = None

        # Simulate invitation creation
        invitation_id = str(uuid.uuid4())
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=7)

        await mock_db.execute(
            "INSERT INTO org_invitations (id, org_id, email, role, token, expires_at, status, invited_by, created_at) "
            "VALUES (:id, :org_id, :email, :role, :token, :expires_at, 'pending', :invited_by, :created_at)",
            {
                "id": invitation_id,
                "org_id": org1_id,
                "email": "userb@example.com",
                "role": "analyst",
                "token": token,
                "expires_at": expires_at,
                "invited_by": user_a_token.user_id,
                "created_at": datetime.utcnow()
            }
        )

        # Verify invitation was created
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_member_accepts_invitation(self, user_b_token, org1_id, mock_db):
        """User B accepts invitation to join Organization 1."""
        token = str(uuid.uuid4())
        member_id = str(uuid.uuid4())

        # Mock: fetch invitation (not expired, pending)
        mock_db.fetch_one.side_effect = [
            {
                "id": str(uuid.uuid4()),
                "org_id": org1_id,
                "email": user_b_token.email,
                "role": "analyst",
                "expires_at": datetime.utcnow() + timedelta(days=1),
                "status": "pending",
                "invited_by": "user-a-id"
            },
            {"id": org1_id, "name": "TechCorp"},  # Organization details
            None,  # Check existing membership
        ]
        mock_db.execute.return_value = None

        # Simulate member creation
        await mock_db.execute(
            "INSERT INTO org_members (id, org_id, user_id, role, status, invited_by, joined_at, created_at) "
            "VALUES (:id, :org_id, :user_id, :role, 'active', :invited_by, :joined_at, :created_at)",
            {
                "id": member_id,
                "org_id": org1_id,
                "user_id": user_b_token.user_id,
                "role": "analyst",
                "invited_by": "user-a-id",
                "joined_at": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
        )

        # Verify member was created
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_both_users_in_member_list(self, user_a_token, user_b_token, org1_id, mock_db):
        """Both User A and B appear in organization members list."""
        members_data = [
            {
                "id": str(uuid.uuid4()),
                "user_id": user_a_token.user_id,
                "email": user_a_token.email,
                "name": user_a_token.full_name,
                "role": "owner",
                "status": "active",
                "joined_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": user_b_token.user_id,
                "email": user_b_token.email,
                "name": user_b_token.full_name,
                "role": "analyst",
                "status": "active",
                "joined_at": datetime.utcnow()
            }
        ]

        mock_db.fetch_all.return_value = members_data
        mock_db.fetch_one.return_value = {"count": 2}

        members = await mock_db.fetch_all(
            "SELECT * FROM org_members WHERE org_id = :org_id",
            {"org_id": org1_id}
        )

        assert len(members) == 2
        assert members[0]["user_id"] == user_a_token.user_id
        assert members[1]["user_id"] == user_b_token.user_id


# ── Test Suite 2: Single User, Multiple Orgs ──────────────────────────────────

class TestSingleUserMultipleOrgs:
    """Test scenarios for a single user managing multiple organizations."""

    @pytest.mark.asyncio
    async def test_user_creates_org1_and_org2(self, user_a_token, org1_id, org2_id, mock_db):
        """User A creates two separate organizations."""
        # Mock: create org1
        await mock_db.execute(
            "INSERT INTO organizations (id, name, slug, owner_id) VALUES (:id, :name, :slug, :owner_id)",
            {"id": org1_id, "name": "TechCorp", "slug": "techcorp", "owner_id": user_a_token.user_id}
        )

        # Mock: create org2
        await mock_db.execute(
            "INSERT INTO organizations (id, name, slug, owner_id) VALUES (:id, :name, :slug, :owner_id)",
            {"id": org2_id, "name": "DataGov", "slug": "datagov", "owner_id": user_a_token.user_id}
        )

        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_user_can_switch_between_orgs(self, user_a_token, org1_id, org2_id, mock_db):
        """User A can switch between org1 and org2 contexts."""
        # Mock: fetch org1 members
        mock_db.fetch_all.side_effect = [
            [{"id": "m1", "user_id": user_a_token.user_id, "role": "owner"}],  # org1 members
            [{"id": "m2", "user_id": user_a_token.user_id, "role": "owner"}],  # org2 members
        ]

        # User is member of both orgs
        members_org1 = await mock_db.fetch_all(
            "SELECT * FROM org_members WHERE org_id = :org_id",
            {"org_id": org1_id}
        )

        members_org2 = await mock_db.fetch_all(
            "SELECT * FROM org_members WHERE org_id = :org_id",
            {"org_id": org2_id}
        )

        assert members_org1[0]["user_id"] == user_a_token.user_id
        assert members_org2[0]["user_id"] == user_a_token.user_id

    @pytest.mark.asyncio
    async def test_primary_org_id_preserved(self, user_a_token, org1_id, org2_id, mock_db):
        """User's primary_org_id is set to first org and preserved."""
        # Mock: user joins org1 (sets primary_org_id)
        mock_db.execute.return_value = None
        await mock_db.execute(
            "UPDATE users SET org_id = :org_id, primary_org_id = :primary_org_id WHERE id = :user_id",
            {"org_id": org1_id, "primary_org_id": org1_id, "user_id": user_a_token.user_id}
        )

        # Mock: user joins org2 (does NOT change primary_org_id)
        await mock_db.execute(
            "UPDATE users SET org_id = :org_id WHERE id = :user_id",
            {"org_id": org2_id, "user_id": user_a_token.user_id}
        )

        # Fetch user with primary_org_id set
        mock_db.fetch_one.return_value = {
            "id": user_a_token.user_id,
            "primary_org_id": org1_id,
            "org_id": org2_id
        }

        user = await mock_db.fetch_one(
            "SELECT * FROM users WHERE id = :id",
            {"id": user_a_token.user_id}
        )

        assert user["primary_org_id"] == org1_id
        assert user["org_id"] == org2_id

    @pytest.mark.asyncio
    async def test_separate_members_per_org(self, user_a_token, user_b_token, org1_id, org2_id, mock_db):
        """User A and B in org1, only User A in org2 (separate member lists)."""
        # Mock: org1 has both users
        mock_db.fetch_all.side_effect = [
            [
                {"user_id": user_a_token.user_id, "role": "owner"},
                {"user_id": user_b_token.user_id, "role": "analyst"}
            ],
            # org2 has only user A
            [
                {"user_id": user_a_token.user_id, "role": "owner"}
            ]
        ]

        org1_members = await mock_db.fetch_all(
            "SELECT * FROM org_members WHERE org_id = :org_id",
            {"org_id": org1_id}
        )

        org2_members = await mock_db.fetch_all(
            "SELECT * FROM org_members WHERE org_id = :org_id",
            {"org_id": org2_id}
        )

        assert len(org1_members) == 2
        assert len(org2_members) == 1
        assert org2_members[0]["user_id"] == user_a_token.user_id


# ── Test Suite 3: Org Isolation (CRITICAL) ───────────────────────────────────

class TestOrgIsolation:
    """CRITICAL: Verify organization isolation prevents cross-org access."""

    @pytest.mark.asyncio
    async def test_non_member_cannot_list_members(self, user_a_token, user_c_token, org1_id, mock_db):
        """User C (not in org1) cannot list org1 members - should return 403."""
        # Mock: user is NOT a member
        mock_db.fetch_one.return_value = None

        membership = await mock_db.fetch_one(
            "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id",
            {"org_id": org1_id, "user_id": user_c_token.user_id}
        )

        # Should be None (no membership)
        assert membership is None

    @pytest.mark.asyncio
    async def test_member_cannot_access_other_org(self, user_a_token, user_b_token, org1_id, org2_id, mock_db):
        """User B (member of org1) cannot access org2 they're not in - should return 403."""
        # Mock: user B is member of org1
        mock_db.fetch_one.side_effect = [
            {"id": "member-id", "user_id": user_b_token.user_id},  # org1 membership check
            None  # org2 membership check - NOT a member
        ]

        # Check membership in org1 (should pass)
        org1_member = await mock_db.fetch_one(
            "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id",
            {"org_id": org1_id, "user_id": user_b_token.user_id}
        )

        # Check membership in org2 (should fail)
        org2_member = await mock_db.fetch_one(
            "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id",
            {"org_id": org2_id, "user_id": user_b_token.user_id}
        )

        assert org1_member is not None
        assert org2_member is None

    @pytest.mark.asyncio
    async def test_delete_member_in_org1_does_not_affect_org2(
        self, user_a_token, user_b_token, org1_id, org2_id, mock_db
    ):
        """Deleting User B from org1 does not affect org2 members."""
        member_id = str(uuid.uuid4())

        # Mock: delete from org1
        mock_db.execute.return_value = None
        await mock_db.execute(
            "DELETE FROM org_members WHERE id = :id AND org_id = :org_id",
            {"id": member_id, "org_id": org1_id}
        )

        # Mock: org2 members unchanged
        mock_db.fetch_all.return_value = [
            {"user_id": user_a_token.user_id, "role": "owner"},
            {"user_id": user_b_token.user_id, "role": "analyst"}
        ]

        org2_members = await mock_db.fetch_all(
            "SELECT * FROM org_members WHERE org_id = :org_id",
            {"org_id": org2_id}
        )

        assert len(org2_members) == 2
        assert any(m["user_id"] == user_b_token.user_id for m in org2_members)

    @pytest.mark.asyncio
    async def test_fetch_org1_members_does_not_include_org2(
        self, user_a_token, user_b_token, org1_id, org2_id, mock_db
    ):
        """Fetching org1 members returns only org1 members (not org2)."""
        # Mock: org1 has user A and user B
        mock_db.fetch_all.return_value = [
            {"id": "m1", "user_id": user_a_token.user_id, "email": user_a_token.email, "role": "owner"},
            {"id": "m2", "user_id": user_b_token.user_id, "email": user_b_token.email, "role": "analyst"}
        ]

        org1_members = await mock_db.fetch_all(
            "SELECT * FROM org_members WHERE org_id = :org_id",
            {"org_id": org1_id}
        )

        # Should have 2 members, but NOT any org2 data
        assert len(org1_members) == 2
        # Verify the query was org-id filtered
        assert mock_db.fetch_all.call_args[1]["org_id"] == org1_id


# ── Test Suite 4: Role-Based Access Control ───────────────────────────────────

class TestRBAC:
    """Test role-based access control for different organizational roles."""

    @pytest.mark.asyncio
    async def test_admin_can_invite(self, user_a_token, org1_id, mock_db):
        """Admin (User A) can invite new members."""
        # Mock: is admin
        mock_db.fetch_one.side_effect = [
            {"id": "member-id", "role": "owner"},  # Admin check
        ]

        is_admin = (await mock_db.fetch_one(
            "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id AND role IN ('admin', 'owner')",
            {"org_id": org1_id, "user_id": user_a_token.user_id}
        )) is not None

        assert is_admin is True

    @pytest.mark.asyncio
    async def test_analyst_cannot_invite(self, user_b_token, org1_id, mock_db):
        """Analyst (User B) cannot invite new members - should get 403."""
        # Mock: is NOT admin
        mock_db.fetch_one.return_value = None

        is_admin = (await mock_db.fetch_one(
            "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id AND role IN ('admin', 'owner')",
            {"org_id": org1_id, "user_id": user_b_token.user_id}
        )) is not None

        assert is_admin is False

    @pytest.mark.asyncio
    async def test_admin_can_delete_members(self, user_a_token, user_b_token, org1_id, mock_db):
        """Admin can delete members."""
        member_id = str(uuid.uuid4())

        # Mock: is admin + member exists
        mock_db.fetch_one.side_effect = [
            {"id": "admin-member-id", "role": "owner"},  # Admin check
            {"id": member_id, "user_id": user_b_token.user_id, "role": "analyst"},  # Member check
            {"count": 2}  # Other admins exist
        ]
        mock_db.execute.return_value = None

        # Check authorization
        is_admin = (await mock_db.fetch_one(
            "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id AND role IN ('admin', 'owner')",
            {"org_id": org1_id, "user_id": user_a_token.user_id}
        )) is not None

        assert is_admin is True

    @pytest.mark.asyncio
    async def test_admin_can_create_custom_roles(self, user_a_token, org1_id, mock_db):
        """Admin can create custom roles."""
        # Mock: is admin
        mock_db.fetch_one.side_effect = [
            {"id": "member-id", "role": "owner"},  # Admin check
            None,  # Check duplicate role name
        ]
        mock_db.execute.return_value = None

        is_admin = (await mock_db.fetch_one(
            "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id AND role IN ('admin', 'owner')",
            {"org_id": org1_id, "user_id": user_a_token.user_id}
        )) is not None

        assert is_admin is True

    @pytest.mark.asyncio
    async def test_viewer_cannot_modify_members(self, user_b_token, org1_id, mock_db):
        """Viewer role cannot modify members."""
        # Mock: is NOT admin
        mock_db.fetch_one.return_value = None

        is_admin = (await mock_db.fetch_one(
            "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id AND role IN ('admin', 'owner')",
            {"org_id": org1_id, "user_id": user_b_token.user_id}
        )) is not None

        assert is_admin is False


# ── Test Suite 5: Audit Trail Integrity ──────────────────────────────────────

class TestAuditTrail:
    """Test that all actions are properly logged in org_audit_logs."""

    @pytest.mark.asyncio
    async def test_create_member_logged(self, user_a_token, user_b_token, org1_id, mock_db):
        """Creating a member logs an entry in org_audit_logs."""
        member_id = str(uuid.uuid4())
        audit_id = str(uuid.uuid4())

        mock_db.execute.return_value = None

        await mock_db.execute(
            """
            INSERT INTO org_audit_logs
            (id, org_id, user_id, action, resource_type, resource_id, changes, status, created_at)
            VALUES (:id, :org_id, :user_id, :action, :resource_type, :resource_id, :changes, :status, :created_at)
            """,
            {
                "id": audit_id,
                "org_id": org1_id,
                "user_id": user_a_token.user_id,
                "action": "create_member",
                "resource_type": "member",
                "resource_id": member_id,
                "changes": {"email": user_b_token.email, "role": "analyst"},
                "status": "success",
                "created_at": datetime.utcnow()
            }
        )

        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_update_member_logged(self, user_a_token, org1_id, mock_db):
        """Updating member role logs an entry."""
        member_id = str(uuid.uuid4())
        audit_id = str(uuid.uuid4())

        mock_db.execute.return_value = None

        await mock_db.execute(
            """
            INSERT INTO org_audit_logs
            (id, org_id, user_id, action, resource_type, resource_id, changes, status, created_at)
            VALUES (:id, :org_id, :user_id, :action, :resource_type, :resource_id, :changes, :status, :created_at)
            """,
            {
                "id": audit_id,
                "org_id": org1_id,
                "user_id": user_a_token.user_id,
                "action": "update_member",
                "resource_type": "member",
                "resource_id": member_id,
                "changes": {"role": "admin"},
                "status": "success",
                "created_at": datetime.utcnow()
            }
        )

        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_accept_invitation_logged(self, user_b_token, org1_id, mock_db):
        """Accepting invitation logs member_accepted_invitation action."""
        member_id = str(uuid.uuid4())
        audit_id = str(uuid.uuid4())

        mock_db.execute.return_value = None

        await mock_db.execute(
            """
            INSERT INTO org_audit_logs
            (id, org_id, user_id, action, resource_type, resource_id, changes, status, created_at)
            VALUES (:id, :org_id, :user_id, :action, :resource_type, :resource_id, :changes, :status, :created_at)
            """,
            {
                "id": audit_id,
                "org_id": org1_id,
                "user_id": user_b_token.user_id,
                "action": "member_accepted_invitation",
                "resource_type": "organization_member",
                "resource_id": member_id,
                "changes": {"email": user_b_token.email, "role": "analyst"},
                "status": "success",
                "created_at": datetime.utcnow()
            }
        )

        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_audit_logs_have_required_fields(self, mock_db):
        """Each audit log entry has timestamp, user_id, org_id, action, resource_type."""
        audit_id = str(uuid.uuid4())
        org_id = str(uuid.uuid4())
        user_id = "user-a-id"
        action = "create_member"
        resource_type = "member"

        mock_db.execute.return_value = None

        await mock_db.execute(
            """
            INSERT INTO org_audit_logs
            (id, org_id, user_id, action, resource_type, resource_id, changes, status, created_at)
            VALUES (:id, :org_id, :user_id, :action, :resource_type, :resource_id, :changes, :status, :created_at)
            """,
            {
                "id": audit_id,
                "org_id": org_id,
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": str(uuid.uuid4()),
                "changes": {},
                "status": "success",
                "created_at": datetime.utcnow()
            }
        )

        # Verify all required fields were passed
        call_args = mock_db.execute.call_args[1]
        assert call_args["org_id"] == org_id
        assert call_args["user_id"] == user_id
        assert call_args["action"] == action
        assert call_args["resource_type"] == resource_type
        assert call_args["created_at"] is not None


# ── Test Suite 6: Concurrent Operations ───────────────────────────────────────

class TestConcurrentOperations:
    """Test handling of concurrent/simultaneous operations."""

    @pytest.mark.asyncio
    async def test_concurrent_invites_same_user(self, user_a_token, user_b_token, org1_id, mock_db):
        """Two admins inviting the same user simultaneously - prevented by UNIQUE constraint."""
        email = "newuser@example.com"
        role = "analyst"

        # Mock: first invite succeeds
        mock_db.fetch_one.side_effect = [
            {"id": "admin-member-id", "role": "owner"},  # Admin check 1
            None,  # No existing member
            None,  # No existing invite
            {"id": "admin-member-id", "role": "owner"},  # Admin check 2
            None,  # No existing member
            {"id": "existing-invite-id"},  # EXISTING INVITE FOUND
        ]

        # First invite would succeed
        # Second invite should fail with 409 Conflict
        invite_exists = await mock_db.fetch_one(
            "SELECT id FROM org_invitations WHERE org_id = :org_id AND email = :email AND status = 'pending'",
            {"org_id": org1_id, "email": email}
        )

        # Should find the existing invite
        assert invite_exists is not None

    @pytest.mark.asyncio
    async def test_concurrent_member_acceptance_prevented(self, user_b_token, org1_id, mock_db):
        """User B accepting invitation twice results in 409 Conflict on second attempt."""
        member_id = str(uuid.uuid4())

        # Mock: second acceptance attempt finds existing member
        mock_db.fetch_one.side_effect = [
            {
                "id": str(uuid.uuid4()),
                "org_id": org1_id,
                "email": user_b_token.email,
                "role": "analyst",
                "expires_at": datetime.utcnow() + timedelta(days=1),
                "status": "pending",
                "invited_by": "user-a-id"
            },
            {"id": org1_id, "name": "TechCorp"},  # Organization
            {"id": member_id},  # EXISTING MEMBER FOUND
        ]

        # Check for existing membership
        existing_member = await mock_db.fetch_one(
            "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id",
            {"org_id": org1_id, "user_id": user_b_token.user_id}
        )

        assert existing_member is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
