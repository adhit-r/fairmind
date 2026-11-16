"""
Organization Member and Role Management Endpoints

Provides endpoints for organization admins to:
- List members in their organization
- Invite new members via email
- Update member roles
- Remove members from organization
- Manage custom organization roles

Requires org admin authorization for all endpoints.
All queries automatically filtered by org_id for multi-tenant isolation.
"""

import logging
import uuid
import json
from collections import Counter
import csv
from io import StringIO
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr

from config.database import get_db_connection, get_database
from config.settings import settings
from config.auth import get_current_active_user, TokenData
from src.application.services.org_domains import email_domain, is_personal, normalize_domain
from src.application.services.governance_assurance_service import (
    has_legacy_role_delegation_blocked_permission,
    normalize_org_role_permissions,
)

logger = logging.getLogger("fairmind.org_management")



def _audit_report_pdf(report: dict) -> bytes:
    """The audit report as a real PDF: period, summary and every audit-log row."""
    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    period, summary = report["report_period"], report["summary"]
    story = [
        Paragraph("Audit report", styles["Title"]),
        Paragraph(f"Period: {period['start']} to {period['end']}", styles["Normal"]),
        Paragraph(f"Events: {summary['total_events']} &nbsp; Users: {summary['unique_users']}", styles["Normal"]),
        Spacer(1, 12),
    ]
    cols = ["timestamp", "user_email", "action", "resource_type", "resource_id", "ip_address"]
    rows = [cols] + [[str(e.get(c) or "") for c in cols] for e in report["audit_log"]]
    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f4f2")]),
    ]))
    story.append(table if report["audit_log"] else Paragraph("No audit events in this period.", styles["Normal"]))
    buf = BytesIO()
    SimpleDocTemplate(buf, pagesize=landscape(A4), title="Audit report").build(story)
    return buf.getvalue()

router = APIRouter(prefix="/api/v1/organizations", tags=["organization-management"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class MemberResponse(BaseModel):
    """Response model for organization member."""
    id: str
    user_id: str
    email: Optional[str]
    name: Optional[str]
    role: str
    status: str  # "active", "pending", "inactive"
    joined_at: Optional[str]

    class Config:
        from_attributes = True


class MembersListResponse(BaseModel):
    """Response for listing organization members."""
    members: List[MemberResponse]
    total: int


class OrganizationSummaryResponse(BaseModel):
    """Organization membership details used to bootstrap the frontend context."""
    id: str
    name: str
    slug: str
    domain: Optional[str]
    owner_id: str
    created_at: str
    role: str
    permissions: List[str]


class OrganizationsListResponse(BaseModel):
    organizations: List[OrganizationSummaryResponse]


class InviteMemberRequest(BaseModel):
    """Request to invite a new member to organization."""
    email: EmailStr
    role: str = "editor"  # owner, admin, editor, viewer or a custom role

    class Config:
        schema_extra = {
            "example": {
                "email": "newuser@company.com",
                "role": "editor"
            }
        }


class InviteMemberResponse(BaseModel):
    """Response when member is invited."""
    invitation_id: str
    email: str
    role: str
    expires_at: str
    status: str


class InvitationDetailsResponse(BaseModel):
    """Response with invitation details for display."""
    org_id: str
    org_name: str
    email: str
    role: str
    created_at: str
    expires_at: str


class AcceptInvitationResponse(BaseModel):
    """Response when invitation is accepted."""
    success: bool
    org_id: str
    org_name: str
    user_id: str
    role: str
    message: str


class UpdateMemberRequest(BaseModel):
    """Request to update member role or status."""
    role: Optional[str] = None
    status: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "role": "admin",
                "status": "active"
            }
        }


class OrgRoleResponse(BaseModel):
    """Response model for organization role."""
    id: str
    name: str
    description: Optional[str]
    permissions: List[str]
    is_system_role: bool
    created_at: Optional[str]

    class Config:
        from_attributes = True


class CreateOrgRoleRequest(BaseModel):
    """Request to create a custom organization role."""
    name: str
    description: Optional[str] = None
    permissions: List[str] = []

    class Config:
        schema_extra = {
            "example": {
                "name": "Data Analyst",
                "description": "Can view and analyze bias reports",
                "permissions": ["read:reports", "read:datasets"]
            }
        }


# ── Helper Functions ─────────────────────────────────────────────────────────

async def _log_org_audit(
    org_id: str,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    changes: Optional[dict] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log organization audit event for compliance."""
    try:
        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO org_audit_logs
                (id, org_id, user_id, action, resource_type, resource_id, changes, status, error_message, ip_address, user_agent, created_at)
                VALUES (:id, :org_id, :user_id, :action, :resource_type, :resource_id, CAST(:changes AS jsonb), :status, :error_message, :ip_address, :user_agent, :created_at)
                """,
                {
                    "id": str(uuid.uuid4()),
                    "org_id": org_id,
                    "user_id": user_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "changes": json.dumps(changes or {}, default=str),
                    "status": status,
                    "error_message": error_message,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "created_at": datetime.utcnow(),
                }
            )
    except Exception as e:
        logger.warning(f"Failed to log org audit event: {e}")


async def _check_org_membership(org_id: str, user_id: str, db):
    """Check if user is a member of the organization."""
    member = await db.fetch_one(
        "SELECT id, role FROM org_members WHERE org_id = :org_id AND user_id = :user_id AND status = 'active'",
        {"org_id": org_id, "user_id": user_id}
    )
    return member


async def _check_org_admin(org_id: str, user_id: str, db):
    """Check if user is an admin of the organization."""
    admin = await db.fetch_one(
        "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id AND status = 'active' AND role IN ('admin', 'owner')",
        {"org_id": org_id, "user_id": user_id}
    )
    return admin is not None


# Built-in org roles. Owners and admins manage people; editors change governance records
# (GovernanceAssuranceService.may_mutate); viewers read. Only an owner grants, changes or
# removes the owner role, and an organisation always keeps one active owner.
BUILT_IN_ROLES = ("owner", "admin", "editor", "viewer")
MANAGER_ROLES = ("owner", "admin")
MEMBER_STATUSES = ("active", "suspended")


async def _caller_role(org_id: str, user_id: str, db) -> Optional[str]:
    """The caller's active role. An admin of an org with no active owner acts as owner, so it can appoint one."""
    member = await _check_org_membership(org_id, user_id, db)
    if not member:
        return None
    if member["role"] == "admin" and await _count_active_owners(org_id, db) == 0:
        return "owner"
    return member["role"]


async def _count_active_owners(org_id: str, db) -> int:
    row = await db.fetch_one(
        "SELECT COUNT(*) AS count FROM org_members WHERE org_id = :org_id AND status = 'active' AND role = 'owner'",
        {"org_id": org_id},
    )
    return row["count"] if row else 0


async def _require_assignable_role(org_id: str, role: str, db) -> None:
    """A built-in role, or a custom role this org defined; anything else would silently grant nothing."""
    if role in BUILT_IN_ROLES:
        return
    custom = await db.fetch_one("SELECT 1 FROM org_roles WHERE org_id = :org_id AND name = :name", {"org_id": org_id, "name": role})
    if not custom:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown role {role!r}; use owner, admin, editor, viewer or a custom role")


def _require_may_manage(caller_role: Optional[str], *roles_touched: Optional[str]) -> None:
    if caller_role not in MANAGER_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    if "owner" in roles_touched and caller_role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an owner can grant, change or remove the owner role")


async def _require_owner_remains(org_id: str, member, db) -> None:
    """Call before a change that takes an active owner away; refuses when they are the last one."""
    if member["role"] == "owner" and member["status"] == "active" and await _count_active_owners(org_id, db) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An organisation needs at least one active owner. Make someone else owner first.",
        )


async def _sync_owner_id(org_id: str, db) -> None:
    """Keep organizations.owner_id on an active owner after a role change, removal or leave."""
    await db.execute(
        """
        UPDATE organizations o SET owner_id = (
            SELECT m.user_id FROM org_members m
            WHERE m.org_id = o.id AND m.role = 'owner' AND m.status = 'active'
            ORDER BY (m.user_id = o.owner_id) DESC, m.joined_at NULLS LAST LIMIT 1
        )
        WHERE o.id = :org_id AND NOT EXISTS (
            SELECT 1 FROM org_members m WHERE m.org_id = o.id AND m.user_id = o.owner_id AND m.role = 'owner' AND m.status = 'active'
        ) AND EXISTS (SELECT 1 FROM org_members m WHERE m.org_id = o.id AND m.role = 'owner' AND m.status = 'active')
        """,
        {"org_id": org_id},
    )


async def _end_sessions(db, user_id, org_id: Optional[str] = None) -> None:
    """Tokens carry the old rights; bump the version. Leaving an org also clears the user's pointer to it."""
    if org_id is None:
        await db.execute("UPDATE users SET token_version = COALESCE(token_version, 0) + 1 WHERE id = :uid", {"uid": user_id})
        return
    await db.execute(
        "UPDATE users SET token_version = COALESCE(token_version, 0) + 1, "
        "org_id = CASE WHEN CAST(org_id AS TEXT) = :org_id THEN NULL ELSE org_id END, "
        "primary_org_id = CASE WHEN CAST(primary_org_id AS TEXT) = :org_id THEN NULL ELSE primary_org_id END "
        "WHERE id = :user_id",
        {"org_id": str(org_id), "user_id": user_id},
    )


async def _role_has_delegation_blocked_permission(org_id: str, role: str, db) -> bool:
    role_record = await db.fetch_one(
        "SELECT permissions FROM org_roles WHERE org_id = :org_id AND name = :name",
        {"org_id": org_id, "name": role},
    )
    if not role_record:
        return False

    permissions = role_record["permissions"]
    if isinstance(permissions, str):
        try:
            permissions = json.loads(permissions)
        except (TypeError, ValueError):
            return True

    normalized_permissions = normalize_org_role_permissions(permissions)
    if not isinstance(permissions, list) or tuple(permissions) != normalized_permissions:
        return True
    return has_legacy_role_delegation_blocked_permission(permissions)


def _permission_list(value) -> List[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            return []
    return list(normalize_org_role_permissions(value))


def _expired(expires_at: datetime) -> bool:
    """Compare in UTC whether the column is timestamp (ORM) or timestamptz (production schema)."""
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= datetime.now(timezone.utc)


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("", response_model=OrganizationsListResponse)
async def list_organizations(
    current_user: TokenData = Depends(get_current_active_user),
):
    """List the active organizations and effective role permissions for the current user."""
    try:
        async with get_db_connection() as db:
            organizations = await db.fetch_all(
                """
                SELECT
                    o.id,
                    o.name,
                    o.slug,
                    o.domain,
                    o.owner_id,
                    o.created_at,
                    om.role,
                    org_role.permissions
                FROM organizations o
                JOIN org_members om
                    ON om.org_id = o.id
                    AND om.user_id = :user_id
                    AND om.status = 'active'
                LEFT JOIN org_roles org_role
                    ON org_role.org_id = om.org_id
                    AND org_role.name = om.role
                WHERE o.is_active = TRUE
                ORDER BY o.name
                """,
                {"user_id": current_user.user_id},
            )
        return {
            "organizations": [
                {
                    "id": str(organization["id"]),
                    "name": organization["name"],
                    "slug": organization["slug"],
                    "domain": organization["domain"],
                    "owner_id": str(organization["owner_id"]),
                    "created_at": (
                        organization["created_at"].isoformat()
                        if hasattr(organization["created_at"], "isoformat")
                        else str(organization["created_at"])
                    ),
                    "role": organization["role"],
                    "permissions": _permission_list(organization["permissions"]),
                }
                for organization in organizations
            ]
        }
    except Exception as error:
        logger.error("Error listing organizations: %s", error, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list organizations")

@router.get("/{org_id}/members", response_model=MembersListResponse)
async def list_org_members(
    org_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 50
):
    """
    List all members in an organization.

    Requires: Organization membership
    Returns: List of members with roles and status
    """
    try:
        # Verify user is member of this org
        async with get_db_connection() as db:
            membership = await _check_org_membership(org_id, current_user.user_id, db)
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not a member of this organization"
                )

            # Fetch members
            members = await db.fetch_all(
                """
                SELECT
                    om.id,
                    om.user_id,
                    u.email,
                    COALESCE(u.name, u.username) as name,
                    om.role,
                    om.status,
                    om.joined_at
                FROM org_members om
                LEFT JOIN users u ON om.user_id = u.id
                WHERE om.org_id = :org_id
                ORDER BY om.created_at DESC
                LIMIT :limit OFFSET :skip
                """,
                {"org_id": org_id, "limit": limit, "skip": skip}
            )

            # Count total members
            total_result = await db.fetch_one(
                "SELECT COUNT(*) as count FROM org_members WHERE org_id = :org_id",
                {"org_id": org_id}
            )
            total = total_result["count"] if total_result else 0

            return {
                "members": [
                    {
                        "id": str(m["id"]),
                        "user_id": m["user_id"],
                        "email": m["email"],
                        "name": m["name"],
                        "role": m["role"],
                        "status": m["status"],
                        "joined_at": m["joined_at"].isoformat() if m["joined_at"] else None,
                    }
                    for m in members
                ],
                "total": total
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing org members: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list organization members")


@router.post("/{org_id}/members/invite", response_model=InviteMemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    org_id: str,
    payload: InviteMemberRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Invite a new member to organization via email.

    Requires: Organization admin authorization
    Returns: Invitation details with expiration time
    """
    try:
        async with get_db_connection() as db:
            caller = await _caller_role(org_id, current_user.user_id, db)
            if caller not in MANAGER_ROLES:
                await _log_org_audit(
                    org_id=org_id,
                    user_id=current_user.user_id,
                    action="invite_member_attempt",
                    resource_type="member",
                    status="failed",
                    error_message="Insufficient permissions (not admin)",
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
            await _require_assignable_role(org_id, payload.role, db)
            _require_may_manage(caller, payload.role)

            if await _role_has_delegation_blocked_permission(org_id, payload.role, db):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This role cannot be assigned through organization management",
                )

            # Check if user already a member
            existing_member = await db.fetch_one(
                """
                SELECT om.id FROM org_members om
                JOIN users u ON om.user_id = u.id
                WHERE om.org_id = :org_id AND lower(u.email) = lower(:email)
                """,
                {"org_id": org_id, "email": payload.email}
            )
            if existing_member:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User is already a member of this organization"
                )

            # Check if invitation already pending
            existing_invite = await db.fetch_one(
                """
                SELECT id FROM org_invitations
                WHERE org_id = :org_id AND lower(email) = lower(:email) AND status = 'pending' AND expires_at > :now
                """,
                {"org_id": org_id, "email": payload.email, "now": datetime.utcnow()}
            )
            if existing_invite:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A pending invitation already exists for this email"
                )

            # Create invitation
            invitation_id = str(uuid.uuid4())
            token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(days=7)

            await db.execute(
                """
                INSERT INTO org_invitations
                (id, org_id, email, role, token, expires_at, status, invited_by, created_at)
                VALUES (:id, :org_id, :email, :role, :token, :expires_at, 'pending', :invited_by, :created_at)
                """,
                {
                    "id": invitation_id,
                    "org_id": org_id,
                    "email": payload.email,
                    "role": payload.role,
                    "token": token,
                    "expires_at": expires_at,
                    "invited_by": current_user.user_id,
                    "created_at": datetime.utcnow()
                }
            )

            # Log audit event
            await _log_org_audit(
                org_id=org_id,
                user_id=current_user.user_id,
                action="invite_member",
                resource_type="member",
                resource_id=invitation_id,
                changes={"email": payload.email, "role": payload.role},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )

            # Send invitation email asynchronously
            try:
                import asyncio
                from src.application.services.api_boundary_dependencies import email_service

                asyncio.create_task(
                    email_service.send_org_invitation(
                        email=payload.email,
                        token=token,
                        role=payload.role,
                        expires_at=expires_at.isoformat()
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to send invitation email: {e}")
                # Don't fail the request if email fails

            return {
                "invitation_id": invitation_id,
                "email": payload.email,
                "role": payload.role,
                "expires_at": expires_at.isoformat(),
                "status": "pending"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inviting member: {e}", exc_info=True)
        await _log_org_audit(
            org_id=org_id,
            user_id=current_user.user_id,
            action="invite_member",
            resource_type="member",
            status="failed",
            error_message=str(e),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        raise HTTPException(status_code=500, detail="Failed to invite member")


@router.get("/invitations/{token}", response_model=InvitationDetailsResponse)
async def get_invitation_details(token: str):
    """
    Get invitation details using token (no auth required).

    Allows unauthenticated users to preview the invitation.
    Returns organization name, role, and email before accepting.

    Returns: 200 OK with invitation details
    Raises:
    - 400 Bad Request: expired
    - 404 Not Found: unknown, revoked or already used
    """
    try:
        async with get_db_connection() as db:
            # Fetch the invitation
            invitation = await db.fetch_one(
                "SELECT * FROM org_invitations WHERE token = :token",
                {"token": token}
            )

            # Only a pending invitation is shown: a revoked or used one discloses
            # nothing, and an unknown token is not called "expired".
            if not invitation or invitation["status"] != "pending":
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

            # Check if expired
            if _expired(invitation["expires_at"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invitation has expired"
                )

            # Fetch organization details
            org = await db.fetch_one(
                "SELECT id, name FROM organizations WHERE id = :org_id",
                {"org_id": str(invitation["org_id"])}
            )

            if not org:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )

            return InvitationDetailsResponse(
                org_id=str(org["id"]),
                org_name=org["name"],
                email=invitation["email"],
                role=invitation["role"],
                created_at=invitation["created_at"].isoformat() if hasattr(invitation["created_at"], "isoformat") else str(invitation["created_at"]),
                expires_at=invitation["expires_at"].isoformat() if hasattr(invitation["expires_at"], "isoformat") else str(invitation["expires_at"]),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invitation details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch invitation details")


@router.post("/invitations/{token}/accept", response_model=AcceptInvitationResponse, status_code=status.HTTP_201_CREATED)
async def accept_invitation(
    token: str,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Accept an organization invitation using invitation token.

    Requires: Valid JWT with user_id + email
    Logic:
    1. Fetch OrganizationInvitation where token = {token}
    2. Validate: invitation exists, not expired, status = 'pending'
    3. Validate: invited email matches authenticated user's email
    4. Create OrganizationMember (org_id, user_id, role, status='active')
    5. Update User.org_id and User.primary_org_id (if null)
    6. Update OrganizationInvitation.status = 'accepted', accepted_at = NOW
    7. Log to org_audit_logs
    Returns: 201 Created with org details and member role
    """
    try:
        async with get_db_connection() as db:
            # 1. Fetch the invitation
            invitation = await db.fetch_one(
                "SELECT * FROM org_invitations WHERE token = :token",
                {"token": token}
            )

            if not invitation:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

            # 2. Validate invitation is not expired and pending
            if _expired(invitation["expires_at"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invitation has expired"
                )

            if invitation["status"] != "pending":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invitation is already {invitation['status']}"
                )

            # 3. Validate email matches
            if invitation["email"].lower() != current_user.email.lower():
                await _log_org_audit(
                    org_id=str(invitation["org_id"]),
                    user_id=current_user.user_id,
                    action="accept_invitation_attempt",
                    resource_type="organization_member",
                    status="failed",
                    error_message=f"Email mismatch: invitation={invitation['email']}, user={current_user.email}",
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invitation email does not match your account email"
                )

            # Fetch organization details
            org = await db.fetch_one(
                "SELECT id, name FROM organizations WHERE id = :org_id",
                {"org_id": str(invitation["org_id"])}
            )

            if not org:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )

            org_id = str(org["id"])
            org_name = org["name"]

            if await _role_has_delegation_blocked_permission(
                org_id, invitation["role"], db
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This role cannot be assigned through organization management",
                )

            # Check if user is already a member of this org
            existing_member = await db.fetch_one(
                "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id",
                {"org_id": org_id, "user_id": current_user.user_id}
            )

            if existing_member:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You are already a member of this organization"
                )

            # 4. Create OrganizationMember
            member_id = str(uuid.uuid4())
            await db.execute(
                """
                INSERT INTO org_members
                (id, org_id, user_id, role, status, invited_by, joined_at, created_at)
                VALUES (:id, :org_id, :user_id, :role, 'active', :invited_by, :joined_at, :created_at)
                """,
                {
                    "id": member_id,
                    "org_id": org_id,
                    "user_id": current_user.user_id,
                    "role": invitation["role"],
                    "invited_by": invitation["invited_by"],
                    "joined_at": datetime.utcnow(),
                    "created_at": datetime.utcnow(),
                }
            )

            # 5. Update User.org_id and User.primary_org_id (only if primary_org_id is null)
            user = await db.fetch_one(
                "SELECT primary_org_id FROM users WHERE id = :user_id",
                {"user_id": current_user.user_id}
            )

            if user and user["primary_org_id"] is None:
                # Set both org_id and primary_org_id
                await db.execute(
                    "UPDATE users SET org_id = :org_id, primary_org_id = :org_id WHERE id = :user_id",
                    {"org_id": org_id, "user_id": current_user.user_id}
                )
            else:
                # Only set org_id (preserve existing primary_org_id)
                await db.execute(
                    "UPDATE users SET org_id = :org_id WHERE id = :user_id",
                    {"org_id": org_id, "user_id": current_user.user_id}
                )

            # 6. Update invitation status
            await db.execute(
                "UPDATE org_invitations SET status = 'accepted', accepted_at = :accepted_at WHERE id = :id",
                {
                    "id": str(invitation["id"]),
                    "accepted_at": datetime.utcnow(),
                }
            )

            # A pending access request from the same person is answered by this
            # membership; close it so it leaves the admin queue without a denial email.
            await db.execute(
                "UPDATE registration_requests SET status = 'approved', org_id = :org_id, "
                "reviewed_at = :now, review_notes = 'Joined through an organisation invitation' "
                "WHERE lower(email) = lower(:email) AND status = 'pending'",
                {"org_id": org_id, "email": current_user.email, "now": datetime.utcnow()},
            )

            # 7. Log audit event
            await _log_org_audit(
                org_id=org_id,
                user_id=current_user.user_id,
                action="member_accepted_invitation",
                resource_type="organization_member",
                resource_id=member_id,
                changes={"email": current_user.email, "role": invitation["role"]},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )

            return {
                "success": True,
                "org_id": org_id,
                "org_name": org_name,
                "user_id": current_user.user_id,
                "role": invitation["role"],
                "message": f"You have been added to {org_name}"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting invitation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to accept invitation")


@router.put("/{org_id}/members/{member_id}")
async def update_member(
    org_id: str,
    member_id: str,
    payload: UpdateMemberRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Update member role or status.

    Requires: owner or admin; only an owner grants, changes or removes the owner role.
    Safeguard: the organisation keeps at least one active owner.
    """
    try:
        async with get_db_connection() as db:
            caller = await _caller_role(org_id, current_user.user_id, db)
            if caller not in MANAGER_ROLES:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

            member = await db.fetch_one(
                "SELECT id, user_id, role, status FROM org_members WHERE id = :id AND org_id = :org_id",
                {"id": member_id, "org_id": org_id}
            )
            if not member:
                raise HTTPException(status_code=404, detail="Member not found")

            if payload.status is not None and payload.status not in MEMBER_STATUSES:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be active or suspended")
            if payload.role is not None:
                await _require_assignable_role(org_id, payload.role, db)
            _require_may_manage(caller, member["role"], payload.role)

            assigned_role = payload.role or (
                member["role"] if payload.status == "active" else None
            )
            if assigned_role and await _role_has_delegation_blocked_permission(
                org_id, assigned_role, db
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This role cannot be assigned through organization management",
                )

            demoted = payload.role is not None and payload.role != "owner"
            suspended = payload.status is not None and payload.status != "active"
            if demoted or suspended:
                await _require_owner_remains(org_id, member, db)

            updates = []
            params = {"id": member_id, "org_id": org_id}
            changes = {}

            if payload.role:
                updates.append("role = :role")
                params["role"] = payload.role
                changes["role"] = payload.role

            if payload.status:
                updates.append("status = :status")
                params["status"] = payload.status
                changes["status"] = payload.status

            if updates:
                await db.execute(
                    f"UPDATE org_members SET {', '.join(updates)} WHERE id = :id AND org_id = :org_id",
                    params
                )
                if payload.role and payload.role != member["role"]:
                    # Tokens carry the rights of the old role; end them. A suspended
                    # member needs no bump: tokens require an active membership.
                    await _end_sessions(db, member["user_id"])
                await _sync_owner_id(org_id, db)

                # Log audit event
                await _log_org_audit(
                    org_id=org_id,
                    user_id=current_user.user_id,
                    action="update_member",
                    resource_type="member",
                    resource_id=member_id,
                    changes=changes,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )

            return {"status": "updated", "member_id": member_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating member: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update member")


@router.delete("/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: str,
    member_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Remove a member from organization.

    Requires: owner or admin; only an owner removes an owner.
    Safeguard: the organisation keeps at least one active owner.
    """
    try:
        async with get_db_connection() as db:
            caller = await _caller_role(org_id, current_user.user_id, db)
            if caller not in MANAGER_ROLES:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

            member = await db.fetch_one(
                "SELECT id, role, status, user_id FROM org_members WHERE id = :id AND org_id = :org_id",
                {"id": member_id, "org_id": org_id}
            )
            if not member:
                raise HTTPException(status_code=404, detail="Member not found")
            _require_may_manage(caller, member["role"])
            await _require_owner_remains(org_id, member, db)

            await db.execute(
                "DELETE FROM org_members WHERE id = :id AND org_id = :org_id",
                {"id": member_id, "org_id": org_id}
            )
            # End the removed user's sessions, and stop their stored org pointing here.
            await _end_sessions(db, member["user_id"], org_id)
            await _sync_owner_id(org_id, db)

            # Log audit event
            await _log_org_audit(
                org_id=org_id,
                user_id=current_user.user_id,
                action="remove_member",
                resource_type="member",
                resource_id=member_id,
                changes={"removed_user": member["user_id"]},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )

            return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing member: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove member")


class TransferOwnershipRequest(BaseModel):
    member_id: str


@router.post("/{org_id}/transfer-ownership")
async def transfer_ownership(
    org_id: str,
    payload: TransferOwnershipRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Make another active member the owner of record; the caller, an owner, becomes an admin."""
    async with get_db_connection() as db:
        caller = await _check_org_membership(org_id, current_user.user_id, db)
        if not caller or await _caller_role(org_id, current_user.user_id, db) != "owner":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an owner can transfer ownership")
        target = await db.fetch_one(
            "SELECT id, user_id, role, status FROM org_members WHERE id = :id AND org_id = :org_id",
            {"id": payload.member_id, "org_id": org_id},
        )
        if not target or target["status"] != "active":
            raise HTTPException(status_code=404, detail="Active member not found")
        if str(target["user_id"]) == str(current_user.user_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already own this organisation")
        await db.execute("UPDATE org_members SET role = 'owner' WHERE id = :id", {"id": target["id"]})
        await db.execute("UPDATE org_members SET role = 'admin' WHERE id = :id", {"id": caller["id"]})
        await db.execute("UPDATE organizations SET owner_id = :uid WHERE id = :org_id", {"uid": str(target["user_id"]), "org_id": org_id})
        for uid in (target["user_id"], current_user.user_id):
            await _end_sessions(db, uid)
    await _log_org_audit(
        org_id=org_id, user_id=current_user.user_id, action="transfer_ownership", resource_type="member",
        resource_id=payload.member_id, changes={"new_owner": str(target["user_id"])},
        ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"),
    )
    return {"status": "transferred", "owner_member_id": payload.member_id}


@router.post("/{org_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_organization(org_id: str, request: Request, current_user: TokenData = Depends(get_current_active_user)):
    """Leave an organisation. The last active owner must hand ownership on first."""
    async with get_db_connection() as db:
        member = await db.fetch_one(
            "SELECT id, user_id, role, status FROM org_members WHERE org_id = :org_id AND user_id = :uid",
            {"org_id": org_id, "uid": current_user.user_id},
        )
        if not member:
            raise HTTPException(status_code=404, detail="You are not a member of this organisation")
        await _require_owner_remains(org_id, member, db)
        await db.execute("DELETE FROM org_members WHERE id = :id", {"id": member["id"]})
        await _end_sessions(db, member["user_id"], org_id)
        await _sync_owner_id(org_id, db)
    await _log_org_audit(
        org_id=org_id, user_id=current_user.user_id, action="leave_organization", resource_type="member",
        resource_id=str(member["id"]), ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return None


@router.get("/{org_id}/invitations")
async def list_invitations(org_id: str, current_user: TokenData = Depends(get_current_active_user)):
    """Pending, unexpired invitations; owners and admins only."""
    async with get_db_connection() as db:
        if await _caller_role(org_id, current_user.user_id, db) not in MANAGER_ROLES:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
        rows = await db.fetch_all(
            "SELECT id, email, role, expires_at, created_at FROM org_invitations "
            "WHERE org_id = :org_id AND status = 'pending' AND expires_at > :now ORDER BY created_at DESC",
            {"org_id": org_id, "now": datetime.utcnow()},
        )
    return {"invitations": [
        {"id": str(r["id"]), "email": r["email"], "role": r["role"],
         "expires_at": r["expires_at"].isoformat() if r["expires_at"] else None,
         "created_at": r["created_at"].isoformat() if r["created_at"] else None}
        for r in rows
    ]}


@router.delete("/{org_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(org_id: str, invitation_id: str, request: Request, current_user: TokenData = Depends(get_current_active_user)):
    """Revoke a pending invitation so its link stops working; an owner invitation needs an owner."""
    async with get_db_connection() as db:
        caller = await _caller_role(org_id, current_user.user_id, db)
        invitation = await db.fetch_one(
            "SELECT id, role, status FROM org_invitations WHERE id = :id AND org_id = :org_id",
            {"id": invitation_id, "org_id": org_id},
        )
        if not invitation or invitation["status"] != "pending":
            if caller not in MANAGER_ROLES:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
            raise HTTPException(status_code=404, detail="Pending invitation not found")
        _require_may_manage(caller, invitation["role"])
        await db.execute("UPDATE org_invitations SET status = 'revoked' WHERE id = :id", {"id": invitation_id})
    await _log_org_audit(
        org_id=org_id, user_id=current_user.user_id, action="revoke_invitation", resource_type="invitation",
        resource_id=invitation_id, ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return None


class DomainBody(BaseModel):
    domain: str


@router.get("/{org_id}/domains")
async def list_domains(org_id: str, current_user: TokenData = Depends(get_current_active_user)):
    """Email domains this organisation owns; sign-ups from them become join requests here."""
    async with get_db_connection() as db:
        if not await _check_org_membership(org_id, current_user.user_id, db):
            raise HTTPException(status_code=403, detail="You are not a member of this organization")
        rows = await db.fetch_all("SELECT id, domain, verified_via, created_at FROM org_domains WHERE org_id = :org ORDER BY domain", {"org": org_id})
    return {"domains": [{"id": str(r["id"]), "domain": r["domain"], "verified_via": r["verified_via"],
                         "created_at": r["created_at"].isoformat() if r["created_at"] else None} for r in rows]}


@router.post("/{org_id}/domains", status_code=status.HTTP_201_CREATED)
async def add_domain(org_id: str, body: DomainBody, request: Request, current_user: TokenData = Depends(get_current_active_user)):
    """Claim a domain. Proof for now: the owner or admin's own address is on it, or a platform admin adds it."""
    domain = normalize_domain(body.domain)
    if not domain:
        raise HTTPException(status_code=400, detail="That is not a domain, for example sq1.security")
    if is_personal(domain):
        raise HTTPException(status_code=400, detail=f"{domain} is personal mail; it cannot belong to one organisation")
    platform_admin = getattr(current_user.role, "value", current_user.role) == "admin"
    async with get_db_connection() as db:
        if await _caller_role(org_id, current_user.user_id, db) not in MANAGER_ROLES and not platform_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        if email_domain(current_user.email) != domain and not platform_admin:
            raise HTTPException(status_code=403, detail=f"Add a domain your own address is on; yours is on {email_domain(current_user.email)}")
        owner = await db.fetch_one("SELECT org_id FROM org_domains WHERE domain = :d", {"d": domain})
        if owner and str(owner["org_id"]) != str(org_id):
            raise HTTPException(status_code=409, detail=f"{domain} already belongs to another organisation")
        if not owner:
            await db.execute(
                "INSERT INTO org_domains (id, org_id, domain, verified_via, added_by, created_at) VALUES (:id, :org, :d, :via, :by, :now)",
                {"id": str(uuid.uuid4()), "org": org_id, "d": domain, "via": "owner_email" if email_domain(current_user.email) == domain else "platform_admin",
                 "by": current_user.user_id, "now": datetime.utcnow()},
            )
    await _log_org_audit(org_id=org_id, user_id=current_user.user_id, action="add_domain", resource_type="domain", resource_id=domain,
                         ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"))
    return {"domain": domain}


@router.delete("/{org_id}/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_domain(org_id: str, domain_id: str, request: Request, current_user: TokenData = Depends(get_current_active_user)):
    async with get_db_connection() as db:
        if await _caller_role(org_id, current_user.user_id, db) not in MANAGER_ROLES:
            raise HTTPException(status_code=403, detail="Admin access required")
        row = await db.fetch_one("SELECT domain FROM org_domains WHERE id = :id AND org_id = :org", {"id": domain_id, "org": org_id})
        if not row:
            raise HTTPException(status_code=404, detail="Domain not found")
        await db.execute("DELETE FROM org_domains WHERE id = :id", {"id": domain_id})
    await _log_org_audit(org_id=org_id, user_id=current_user.user_id, action="remove_domain", resource_type="domain", resource_id=row["domain"],
                         ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"))
    return None


class JoinDecision(BaseModel):
    role: str = "viewer"
    notes: Optional[str] = None


@router.get("/{org_id}/join-requests")
async def list_join_requests(org_id: str, current_user: TokenData = Depends(get_current_active_user)):
    """People who signed up with an address on this organisation's domains and wait for an owner or admin."""
    async with get_db_connection() as db:
        if await _caller_role(org_id, current_user.user_id, db) not in MANAGER_ROLES:
            raise HTTPException(status_code=403, detail="Admin access required")
        rows = await db.fetch_all(
            "SELECT id, email, name, requested_role, message, created_at FROM registration_requests "
            "WHERE CAST(org_id AS TEXT) = :org AND is_join AND status = 'pending' ORDER BY created_at",
            {"org": str(org_id)},
        )
    return {"requests": [{"id": str(r["id"]), "email": r["email"], "name": r["name"], "message": r["message"],
                          "created_at": r["created_at"].isoformat() if r["created_at"] else None} for r in rows]}


async def _pending_join(db, org_id: str, request_id: str):
    req = await db.fetch_one(
        "SELECT * FROM registration_requests WHERE id = :id AND CAST(org_id AS TEXT) = :org AND is_join AND status = 'pending'",
        {"id": request_id, "org": str(org_id)},
    )
    if not req:
        raise HTTPException(status_code=404, detail="Pending join request not found")
    return req


@router.post("/{org_id}/join-requests/{request_id}/approve")
async def approve_join_request(org_id: str, request_id: str, body: JoinDecision, request: Request, current_user: TokenData = Depends(get_current_active_user)):
    """Let the requester in with a role; a new account gets an email to choose its password."""
    from api.routes.registration import create_account, send_welcome

    async with get_db_connection() as db:
        caller = await _caller_role(org_id, current_user.user_id, db)
        if caller not in MANAGER_ROLES:
            raise HTTPException(status_code=403, detail="Admin access required")
        await _require_assignable_role(org_id, body.role, db)
        _require_may_manage(caller, body.role)
        req = await _pending_join(db, org_id, request_id)
        org = await db.fetch_one("SELECT name FROM organizations WHERE id = :org", {"org": org_id})
        user = await db.fetch_one("SELECT id FROM users WHERE lower(email) = lower(:e)", {"e": req["email"]})
        welcome = None
        if user:
            user_id = str(user["id"])
        else:
            user_id, password_hash = await create_account(db, req["email"], req["name"])
            welcome = password_hash
        if not await db.fetch_one("SELECT 1 FROM org_members WHERE org_id = :org AND user_id = :uid", {"org": org_id, "uid": user_id}):
            await db.execute(
                "INSERT INTO org_members (id, org_id, user_id, role, status, invited_by, joined_at) VALUES (:id, :org, :uid, :role, 'active', :by, :now)",
                {"id": str(uuid.uuid4()), "org": org_id, "uid": user_id, "role": body.role, "by": current_user.user_id, "now": datetime.utcnow()},
            )
        await db.execute("UPDATE users SET primary_org_id = COALESCE(primary_org_id, CAST(:org AS uuid)) WHERE id = :uid", {"org": str(org_id), "uid": user_id})
        await db.execute(
            "UPDATE registration_requests SET status = 'approved', reviewed_by = :by, reviewed_at = :now, review_notes = :notes WHERE id = :id",
            {"by": current_user.user_id, "now": datetime.utcnow(), "notes": body.notes, "id": request_id},
        )
    if welcome:
        send_welcome(user_id, welcome, req["email"], req["name"], org["name"])
    await _log_org_audit(org_id=org_id, user_id=current_user.user_id, action="approve_join_request", resource_type="member", resource_id=request_id,
                         changes={"email": req["email"], "role": body.role}, ip_address=request.client.host if request.client else None,
                         user_agent=request.headers.get("user-agent"))
    return {"status": "approved", "user_id": user_id, "new_account": bool(welcome)}


@router.post("/{org_id}/join-requests/{request_id}/deny")
async def deny_join_request(org_id: str, request_id: str, body: JoinDecision, request: Request, current_user: TokenData = Depends(get_current_active_user)):
    async with get_db_connection() as db:
        if await _caller_role(org_id, current_user.user_id, db) not in MANAGER_ROLES:
            raise HTTPException(status_code=403, detail="Admin access required")
        req = await _pending_join(db, org_id, request_id)
        org = await db.fetch_one("SELECT name FROM organizations WHERE id = :org", {"org": org_id})
        await db.execute(
            "UPDATE registration_requests SET status = 'denied', reviewed_by = :by, reviewed_at = :now, review_notes = :notes WHERE id = :id",
            {"by": current_user.user_id, "now": datetime.utcnow(), "notes": body.notes, "id": request_id},
        )
    try:
        import asyncio
        from src.application.services.api_boundary_dependencies import email_service

        asyncio.create_task(email_service.send_denial_email(req["email"], req["name"], org["name"], body.notes))
    except Exception as exc:
        logger.warning(f"Join denial email failed: {exc}")
    await _log_org_audit(org_id=org_id, user_id=current_user.user_id, action="deny_join_request", resource_type="member", resource_id=request_id,
                         ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"))
    return {"status": "denied"}


# ── Role Management Endpoints ────────────────────────────────────────────────

@router.get("/{org_id}/roles", response_model=dict)
async def list_org_roles(
    org_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    List all roles available in organization.

    Requires: Organization membership
    Returns: List of system and custom roles with permissions
    """
    try:
        async with get_db_connection() as db:
            # Verify membership
            membership = await _check_org_membership(org_id, current_user.user_id, db)
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not a member of this organization"
                )

            # Fetch roles
            roles = await db.fetch_all(
                """
                SELECT id, name, description, permissions, is_system_role, created_at
                FROM org_roles
                WHERE org_id = :org_id
                ORDER BY is_system_role DESC, name
                """,
                {"org_id": org_id}
            )

            return {
                "roles": [
                    {
                        "id": str(r["id"]),
                        "name": r["name"],
                        "description": r["description"],
                        "permissions": _permission_list(r["permissions"]),
                        "is_system_role": r["is_system_role"],
                        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    }
                    for r in roles
                ]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing org roles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list organization roles")


@router.post("/{org_id}/roles", status_code=status.HTTP_201_CREATED)
async def create_org_role(
    org_id: str,
    payload: CreateOrgRoleRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Create custom role in organization.

    Requires: Organization admin authorization
    Returns: Created role details
    """
    try:
        async with get_db_connection() as db:
            # Check admin authorization
            is_admin = await _check_org_admin(org_id, current_user.user_id, db)
            if not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )

            if has_legacy_role_delegation_blocked_permission(payload.permissions):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reserved evaluation permissions cannot be assigned through organization roles",
                )
            if tuple(payload.permissions) != normalize_org_role_permissions(payload.permissions):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role permissions must be a bounded unique list of valid strings",
                )

            # Check for duplicate role name
            existing = await db.fetch_one(
                "SELECT id FROM org_roles WHERE org_id = :org_id AND name = :name",
                {"org_id": org_id, "name": payload.name}
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Role '{payload.name}' already exists in this organization"
                )

            # Create role
            role_id = str(uuid.uuid4())
            await db.execute(
                """
                INSERT INTO org_roles
                (id, org_id, name, description, permissions, is_system_role, created_at)
                VALUES (:id, :org_id, :name, :description, :permissions, FALSE, :created_at)
                """,
                {
                    "id": role_id,
                    "org_id": org_id,
                    "name": payload.name,
                    "description": payload.description,
                    "permissions": payload.permissions,
                    "created_at": datetime.utcnow()
                }
            )

            # Log audit event
            await _log_org_audit(
                org_id=org_id,
                user_id=current_user.user_id,
                action="create_role",
                resource_type="role",
                resource_id=role_id,
                changes={"name": payload.name, "permissions": payload.permissions},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )

            return {
                "role_id": role_id,
                "name": payload.name,
                "status": "created"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating org role: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create organization role")


@router.get("/{org_id}/audit-logs", response_model=dict)
async def list_org_audit_logs(
    org_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 50,
    action: Optional[str] = None,
):
    """
    List organization audit logs.

    Requires: Organization admin authorization
    Returns: Audit trail for compliance and security review
    """
    try:
        async with get_db_connection() as db:
            # Check admin authorization
            is_admin = await _check_org_admin(org_id, current_user.user_id, db)
            if not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )

            # Build query
            where_clauses = ["org_id = :org_id"]
            params = {"org_id": org_id, "limit": limit, "skip": skip}

            if action:
                where_clauses.append("action = :action")
                params["action"] = action

            where = " AND ".join(where_clauses)

            # Fetch logs
            logs = await db.fetch_all(
                f"""
                SELECT id, user_id, action, resource_type, resource_id, changes, status, error_message, created_at
                FROM org_audit_logs
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
                """,
                params
            )

            # Count total
            total_result = await db.fetch_one(
                f"SELECT COUNT(*) as count FROM org_audit_logs WHERE {where}",
                params
            )
            total = total_result["count"] if total_result else 0

            return {
                "logs": [
                    {
                        "id": str(l["id"]),
                        "user_id": l["user_id"],
                        "action": l["action"],
                        "resource_type": l["resource_type"],
                        "resource_id": str(l["resource_id"]) if l["resource_id"] else None,
                        "changes": l["changes"] if isinstance(l["changes"], dict) else {},
                        "status": l["status"],
                        "error_message": l["error_message"],
                        "created_at": l["created_at"].isoformat() if l["created_at"] else None,
                    }
                    for l in logs
                ],
                "total": total
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing org audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list organization audit logs")


# ── Audit Report Endpoint ─────────────────────────────────────────────────────


class AuditReportResponse(BaseModel):
    """Response model for audit report generation."""
    report_period: dict
    summary: dict
    metrics: dict
    audit_log: List[dict]


@router.get("/{org_id}/compliance/audit-report", response_model=Optional[dict])
async def get_audit_report(
    org_id: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    format: str = Query("json", description="Report format (json|csv|pdf)"),
    request: Request = None,
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Generate audit report for organization with compliance metrics and audit logs.

    Requires: owner or admin, as for the audit-log list: the report carries member emails and IP addresses.
    Returns: Audit report in requested format (JSON, CSV, or PDF)
    """
    try:
        async with get_db_connection() as db:
            if await _caller_role(org_id, current_user.user_id, db) not in MANAGER_ROLES:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

            # Parse dates
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )

            # Fetch audit logs for the period
            logs = await db.fetch_all(
                """
                SELECT id, user_id, action, resource_type, resource_id, changes, status, error_message, created_at, ip_address
                FROM org_audit_logs
                WHERE org_id = :org_id AND created_at BETWEEN :start AND :end
                ORDER BY created_at DESC
                """,
                {
                    "org_id": org_id,
                    "start": start,
                    "end": end
                }
            )

            # Fetch user emails for audit log
            user_emails = {}
            for log in logs:
                if log["user_id"] not in user_emails:
                    user_result = await db.fetch_one(
                        "SELECT email FROM users WHERE id = :user_id",
                        {"user_id": log["user_id"]}
                    )
                    user_emails[log["user_id"]] = user_result["email"] if user_result else "unknown"

            # Build audit log entries
            audit_log = []
            for log in logs:
                audit_log.append({
                    "timestamp": log["created_at"].isoformat() if log["created_at"] else None,
                    "user_email": user_emails.get(log["user_id"], "unknown"),
                    "action": log["action"],
                    "resource_type": log["resource_type"],
                    "resource_id": str(log["resource_id"]) if log["resource_id"] else "N/A",
                    "ip_address": log["ip_address"] or "unknown"
                })

            # Calculate metrics
            total_events = len(logs)
            unique_users = len(set(log["user_id"] for log in logs))

            # Count events per day
            events_per_day = {}
            for log in logs:
                date_key = log["created_at"].strftime("%Y-%m-%d") if log["created_at"] else "unknown"
                events_per_day[date_key] = events_per_day.get(date_key, 0) + 1

            events_per_day_list = [
                {"date": date, "count": count}
                for date, count in sorted(events_per_day.items())
            ]

            # Count actions
            action_counts = {}
            for log in logs:
                action = log["action"]
                action_counts[action] = action_counts.get(action, 0) + 1

            action_distribution = [
                {"action": action, "count": count}
                for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
            ][:5]  # Top 5

            # Top actions
            top_actions = sorted(
                [{"action": k, "count": v} for k, v in action_counts.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:3]

            # Build response
            report_data = {
                "report_period": {
                    "start": start_date,
                    "end": end_date
                },
                "summary": {
                    "total_events": total_events,
                    "unique_users": unique_users,
                    "top_actions": top_actions
                },
                "metrics": {
                    "events_per_day": events_per_day_list,
                    "action_distribution": action_distribution,
                    "top_users": [
                        {"user": user, "count": count}
                        for user, count in Counter(
                            entry.get("user_email") or "unknown" for entry in audit_log
                        ).most_common(5)
                    ],
                },
                "audit_log": audit_log
            }

            # Return in requested format
            if format == "csv":
                # Generate CSV
                output = StringIO()
                writer = csv.DictWriter(
                    output,
                    fieldnames=["timestamp", "user_email", "action", "resource_type", "resource_id", "ip_address"]
                )
                writer.writeheader()
                writer.writerows(audit_log)

                return StreamingResponse(
                    iter([output.getvalue()]),
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f"attachment; filename=audit-report-{end_date}.csv"
                    }
                )

            elif format == "pdf":
                return StreamingResponse(
                    iter([_audit_report_pdf(report_data)]),
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename=audit-report-{end_date}.pdf"
                    }
                )

            else:  # JSON
                return report_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating audit report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate audit report")


def _audit_report_pdf(report: Dict[str, Any]) -> bytes:
    """The audit report as a real PDF document."""
    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), title="Audit report")
    period = report.get("report_period", {})
    summary = report.get("summary", {})

    def table(rows):
        t = Table(rows, repeatRows=1)
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        return t

    story = [
        Paragraph("Audit report", styles["Title"]),
        Paragraph(f"Period: {period.get('start')} to {period.get('end')}", styles["Normal"]),
        Paragraph(
            f"Events: {summary.get('total_events', 0)} &middot; Users: {summary.get('unique_users', 0)}",
            styles["Normal"],
        ),
        Spacer(1, 12),
    ]
    top = summary.get("top_actions") or []
    if top:
        story += [Paragraph("Top actions", styles["Heading3"]),
                  table([["Action", "Count"]] + [[a["action"], a["count"]] for a in top]), Spacer(1, 12)]
    columns = ["timestamp", "user_email", "action", "resource_type", "resource_id", "ip_address"]
    log = report.get("audit_log") or []
    story.append(Paragraph("Audit log", styles["Heading3"]))
    if log:
        story.append(table([["Time", "User", "Action", "Resource type", "Resource", "IP"]]
                           + [[str(entry.get(c) or "") for c in columns] for entry in log]))
    else:
        story.append(Paragraph("No events in this period.", styles["Normal"]))
    doc.build(story)
    return buffer.getvalue()
