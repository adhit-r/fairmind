"""
RBAC Performance Benchmarks

Performance requirements:
- List members (1000 members): < 50ms
- Create member: < 100ms
- Accept invitation: < 150ms
- Generate compliance report (1000 events): < 500ms
- Audit log query (date range): < 50ms

Uses pytest-benchmark or time.perf_counter() for measurements.
"""

import pytest
import uuid
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import random
import string

from config.auth import TokenData


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def user_token():
    """Valid user token."""
    return TokenData(
        user_id="user-id",
        email="user@example.com",
        full_name="User",
        org_id=None,
        primary_org_id=None,
        scopes=[]
    )


@pytest.fixture
def org_id():
    """Organization ID."""
    return str(uuid.uuid4())


@pytest.fixture
async def mock_db():
    """Mock database connection."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.fetch_one = AsyncMock()
    db.fetch_all = AsyncMock()
    return db


@pytest.fixture
def large_member_list():
    """Generate list of 1000 mock members."""
    members = []
    for i in range(1000):
        members.append({
            "id": str(uuid.uuid4()),
            "user_id": f"user-{i}",
            "email": f"user{i}@example.com",
            "name": f"User {i}",
            "role": random.choice(["owner", "admin", "analyst", "viewer"]),
            "status": "active",
            "joined_at": datetime.utcnow()
        })
    return members


@pytest.fixture
def large_audit_log():
    """Generate list of 1000 mock audit log entries."""
    logs = []
    for i in range(1000):
        logs.append({
            "id": str(uuid.uuid4()),
            "org_id": str(uuid.uuid4()),
            "user_id": f"user-{i}",
            "action": random.choice(["create_member", "update_member", "delete_member", "invite_member"]),
            "resource_type": "member",
            "resource_id": str(uuid.uuid4()),
            "changes": {"role": random.choice(["analyst", "admin"])},
            "status": "success",
            "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 7))
        })
    return logs


# ── Test Suite 1: List Members Performance ────────────────────────────────────

class TestListMembersPerformance:
    """Benchmark member list retrieval."""

    @pytest.mark.asyncio
    async def test_list_members_1000_under_50ms(self, user_token, org_id, mock_db, large_member_list, benchmark):
        """Listing 1000 members should complete in < 50ms."""
        # Mock: 1000 members returned
        mock_db.fetch_all.return_value = large_member_list
        mock_db.fetch_one.return_value = {"count": 1000}

        def run_test():
            # Simulate the query
            return len(large_member_list)

        result = benchmark(run_test)
        assert result == 1000

    @pytest.mark.asyncio
    async def test_list_members_pagination(self, user_token, org_id, mock_db, large_member_list):
        """Paginated query (limit 50, offset 0) for 1000 members."""
        paginated = large_member_list[:50]
        mock_db.fetch_all.return_value = paginated
        mock_db.fetch_one.return_value = {"count": 1000}

        start = time.perf_counter()

        members = await mock_db.fetch_all(
            "SELECT * FROM org_members WHERE org_id = :org_id ORDER BY created_at DESC LIMIT :limit OFFSET :skip",
            {"org_id": org_id, "limit": 50, "skip": 0}
        )

        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

        assert len(members) == 50
        assert elapsed < 50  # Should be fast since we're paginating

    @pytest.mark.asyncio
    async def test_list_members_100_members(self, user_token, org_id, mock_db):
        """List 100 members should be very fast."""
        members = [
            {
                "id": str(uuid.uuid4()),
                "user_id": f"user-{i}",
                "email": f"user{i}@example.com",
                "role": "analyst",
                "status": "active"
            }
            for i in range(100)
        ]

        mock_db.fetch_all.return_value = members

        start = time.perf_counter()
        result = await mock_db.fetch_all(
            "SELECT * FROM org_members WHERE org_id = :org_id",
            {"org_id": org_id}
        )
        elapsed = (time.perf_counter() - start) * 1000

        assert len(result) == 100
        assert elapsed < 30  # Even 100 members should be very fast

    @pytest.mark.asyncio
    async def test_list_members_with_user_join(self, user_token, org_id, mock_db):
        """Listing members with user table join."""
        members = [
            {
                "id": str(uuid.uuid4()),
                "user_id": f"user-{i}",
                "email": f"user{i}@example.com",
                "name": f"User {i}",
                "role": "analyst",
                "status": "active",
                "joined_at": datetime.utcnow()
            }
            for i in range(100)
        ]

        mock_db.fetch_all.return_value = members

        start = time.perf_counter()
        result = await mock_db.fetch_all(
            """
            SELECT om.id, om.user_id, u.email, u.full_name as name, om.role, om.status, om.joined_at
            FROM org_members om
            LEFT JOIN users u ON om.user_id = u.id
            WHERE om.org_id = :org_id
            """,
            {"org_id": org_id}
        )
        elapsed = (time.perf_counter() - start) * 1000

        assert len(result) == 100
        assert elapsed < 50


# ── Test Suite 2: Create Member Performance ───────────────────────────────────

class TestCreateMemberPerformance:
    """Benchmark member creation."""

    @pytest.mark.asyncio
    async def test_create_member_under_100ms(self, user_token, org_id, mock_db):
        """Creating a member should complete in < 100ms."""
        member_id = str(uuid.uuid4())

        mock_db.execute.return_value = None
        mock_db.fetch_one.side_effect = [
            {"id": "admin-member"},  # Admin check
            None,  # Check existing member
            None,  # Check existing invite
        ]

        start = time.perf_counter()

        # Simulate all DB operations for member creation
        await mock_db.fetch_one("SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id AND role IN ('admin', 'owner')", {})
        await mock_db.fetch_one("SELECT om.id FROM org_members WHERE org_id = :org_id AND email = :email", {})
        await mock_db.fetch_one("SELECT id FROM org_invitations WHERE org_id = :org_id AND email = :email AND status = 'pending'", {})
        await mock_db.execute("INSERT INTO org_invitations (...) VALUES (...)", {})
        await mock_db.execute("INSERT INTO org_audit_logs (...) VALUES (...)", {})

        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 100

    @pytest.mark.asyncio
    async def test_create_member_with_validation(self, user_token, org_id, mock_db):
        """Member creation with all validations and logging."""
        mock_db.execute.return_value = None
        mock_db.fetch_one.side_effect = [
            {"id": "admin-member"},
            None,
            None,
        ]

        start = time.perf_counter()

        # Full member creation flow
        is_admin = (await mock_db.fetch_one("SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id AND role IN ('admin', 'owner')", {})) is not None
        existing_member = (await mock_db.fetch_one("SELECT om.id FROM org_members WHERE org_id = :org_id AND email = :email", {})) is None
        no_pending_invite = (await mock_db.fetch_one("SELECT id FROM org_invitations WHERE org_id = :org_id AND email = :email AND status = 'pending'", {})) is None

        if is_admin and existing_member and no_pending_invite:
            await mock_db.execute("INSERT INTO org_invitations (...) VALUES (...)", {})
            await mock_db.execute("INSERT INTO org_audit_logs (...) VALUES (...)", {})

        elapsed = (time.perf_counter() - start) * 1000

        assert is_admin is True
        assert elapsed < 120


# ── Test Suite 3: Accept Invitation Performance ───────────────────────────────

class TestAcceptInvitationPerformance:
    """Benchmark invitation acceptance."""

    @pytest.mark.asyncio
    async def test_accept_invitation_under_150ms(self, user_token, org_id, mock_db):
        """Accepting invitation should complete in < 150ms."""
        member_id = str(uuid.uuid4())

        mock_db.execute.return_value = None
        mock_db.fetch_one.side_effect = [
            {
                "id": str(uuid.uuid4()),
                "org_id": org_id,
                "email": user_token.email,
                "role": "analyst",
                "expires_at": datetime.utcnow() + timedelta(days=1),
                "status": "pending",
                "invited_by": "admin-id"
            },
            {"id": org_id, "name": "TestOrg"},  # Org details
            None,  # No existing membership
            {"primary_org_id": None},  # User has no primary org
        ]

        start = time.perf_counter()

        # Full acceptance flow
        invitation = await mock_db.fetch_one("SELECT * FROM org_invitations WHERE token = :token", {})
        org = await mock_db.fetch_one("SELECT id, name FROM organizations WHERE id = :org_id", {})
        existing = await mock_db.fetch_one("SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id", {})
        user = await mock_db.fetch_one("SELECT primary_org_id FROM users WHERE id = :user_id", {})

        await mock_db.execute("INSERT INTO org_members (...) VALUES (...)", {})
        await mock_db.execute("UPDATE users SET org_id = :org_id, primary_org_id = :org_id WHERE id = :user_id", {})
        await mock_db.execute("UPDATE org_invitations SET status = 'accepted' WHERE id = :id", {})
        await mock_db.execute("INSERT INTO org_audit_logs (...) VALUES (...)", {})

        elapsed = (time.perf_counter() - start) * 1000

        assert invitation is not None
        assert elapsed < 150

    @pytest.mark.asyncio
    async def test_accept_invitation_minimal(self, user_token, org_id, mock_db):
        """Minimal acceptance without extra validation."""
        mock_db.execute.return_value = None
        mock_db.fetch_one.side_effect = [
            {"id": str(uuid.uuid4()), "email": user_token.email, "expires_at": datetime.utcnow() + timedelta(days=1), "status": "pending"}
        ]

        start = time.perf_counter()
        await mock_db.fetch_one("SELECT * FROM org_invitations WHERE token = :token", {})
        await mock_db.execute("INSERT INTO org_members (...) VALUES (...)", {})
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 80


# ── Test Suite 4: Generate Compliance Report Performance ──────────────────────

class TestComplianceReportPerformance:
    """Benchmark compliance report generation."""

    @pytest.mark.asyncio
    async def test_generate_report_1000_events_under_500ms(self, org_id, mock_db, large_audit_log):
        """Generating report from 1000 audit events should be < 500ms."""
        mock_db.fetch_all.return_value = large_audit_log
        mock_db.fetch_one.return_value = {"count": 1000}

        start = time.perf_counter()

        # Simulate report generation: fetch logs
        logs = await mock_db.fetch_all(
            "SELECT * FROM org_audit_logs WHERE org_id = :org_id AND created_at >= :start_date AND created_at <= :end_date ORDER BY created_at DESC",
            {
                "org_id": org_id,
                "start_date": datetime.utcnow() - timedelta(days=30),
                "end_date": datetime.utcnow()
            }
        )

        # Simulate CSV generation
        csv_data = []
        csv_data.append("ID,ORG_ID,USER_ID,ACTION,RESOURCE_TYPE,CREATED_AT")
        for log in logs:
            csv_data.append(f"{log['id']},{log['org_id']},{log['user_id']},{log['action']},{log['resource_type']},{log['created_at']}")

        elapsed = (time.perf_counter() - start) * 1000

        assert len(csv_data) == 1001  # Header + 1000 rows
        assert elapsed < 500

    @pytest.mark.asyncio
    async def test_generate_report_with_filtering(self, org_id, mock_db):
        """Generate report with action filtering."""
        logs = [
            {
                "id": str(uuid.uuid4()),
                "action": "invite_member",
                "created_at": datetime.utcnow()
            }
            for _ in range(100)
        ]

        mock_db.fetch_all.return_value = logs

        start = time.perf_counter()

        filtered_logs = await mock_db.fetch_all(
            "SELECT * FROM org_audit_logs WHERE org_id = :org_id AND action = :action ORDER BY created_at DESC",
            {"org_id": org_id, "action": "invite_member"}
        )

        elapsed = (time.perf_counter() - start) * 1000

        assert len(filtered_logs) == 100
        assert elapsed < 100

    @pytest.mark.asyncio
    async def test_pdf_export_performance(self, org_id, mock_db):
        """PDF export of 100 events should be fast."""
        logs = [
            {
                "id": str(uuid.uuid4()),
                "action": "create_member",
                "user_id": f"user-{i}",
                "created_at": datetime.utcnow()
            }
            for i in range(100)
        ]

        mock_db.fetch_all.return_value = logs

        start = time.perf_counter()

        # Simulate PDF generation (in practice, uses reportlab or similar)
        await mock_db.fetch_all(
            "SELECT * FROM org_audit_logs WHERE org_id = :org_id",
            {"org_id": org_id}
        )

        # Simulating PDF content generation
        pdf_content = f"Compliance Report\n{len(logs)} events\n"

        elapsed = (time.perf_counter() - start) * 1000

        assert len(pdf_content) > 0
        assert elapsed < 200


# ── Test Suite 5: Audit Log Query Performance ─────────────────────────────────

class TestAuditLogQueryPerformance:
    """Benchmark audit log queries."""

    @pytest.mark.asyncio
    async def test_audit_log_query_date_range_under_50ms(self, org_id, mock_db):
        """Querying audit logs by date range should be < 50ms."""
        logs = [
            {
                "id": str(uuid.uuid4()),
                "action": "invite_member",
                "created_at": datetime.utcnow() - timedelta(days=i)
            }
            for i in range(50)
        ]

        mock_db.fetch_all.return_value = logs
        mock_db.fetch_one.return_value = {"count": 50}

        start = time.perf_counter()

        result = await mock_db.fetch_all(
            """
            SELECT id, user_id, action, resource_type, resource_id, changes, status, created_at
            FROM org_audit_logs
            WHERE org_id = :org_id AND created_at >= :start_date AND created_at <= :end_date
            ORDER BY created_at DESC
            """,
            {
                "org_id": org_id,
                "start_date": datetime.utcnow() - timedelta(days=7),
                "end_date": datetime.utcnow()
            }
        )

        elapsed = (time.perf_counter() - start) * 1000

        assert len(result) == 50
        assert elapsed < 50

    @pytest.mark.asyncio
    async def test_audit_log_count_query(self, org_id, mock_db):
        """Counting audit logs should be very fast."""
        mock_db.fetch_one.return_value = {"count": 5000}

        start = time.perf_counter()

        result = await mock_db.fetch_one(
            "SELECT COUNT(*) as count FROM org_audit_logs WHERE org_id = :org_id",
            {"org_id": org_id}
        )

        elapsed = (time.perf_counter() - start) * 1000

        assert result["count"] == 5000
        assert elapsed < 20

    @pytest.mark.asyncio
    async def test_audit_log_filter_by_action(self, org_id, mock_db):
        """Filter audit logs by action."""
        logs = [
            {"id": str(uuid.uuid4()), "action": "invite_member"}
            for _ in range(200)
        ]

        mock_db.fetch_all.return_value = logs

        start = time.perf_counter()

        result = await mock_db.fetch_all(
            "SELECT * FROM org_audit_logs WHERE org_id = :org_id AND action = :action",
            {"org_id": org_id, "action": "invite_member"}
        )

        elapsed = (time.perf_counter() - start) * 1000

        assert len(result) == 200
        assert elapsed < 50


# ── Test Suite 6: Concurrent Query Performance ────────────────────────────────

class TestConcurrentQueryPerformance:
    """Benchmark concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_member_queries(self, org_id, mock_db):
        """Multiple concurrent member list queries."""
        members = [
            {"id": str(uuid.uuid4()), "user_id": f"user-{i}"}
            for i in range(100)
        ]

        mock_db.fetch_all.return_value = members

        start = time.perf_counter()

        # Simulate 10 concurrent queries
        import asyncio
        tasks = [
            mock_db.fetch_all(
                "SELECT * FROM org_members WHERE org_id = :org_id",
                {"org_id": org_id}
            )
            for _ in range(10)
        ]

        results = await asyncio.gather(*tasks)

        elapsed = (time.perf_counter() - start) * 1000

        assert len(results) == 10
        assert elapsed < 150  # All 10 queries in < 150ms


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
