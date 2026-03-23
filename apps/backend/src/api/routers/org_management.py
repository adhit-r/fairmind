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
import csv
from io import StringIO
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr

from config.database import get_db_connection, get_database
from config.settings import settings
from config.auth import get_current_active_user, TokenData
from src.infrastructure.email.resend_service import email_service
from core.decorators.org_permissions import require_org_admin, require_org_member

logger = logging.getLogger("fairmind.org_management")
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


class InviteMemberRequest(BaseModel):
    """Request to invite a new member to organization."""
    email: EmailStr
    role: str = "analyst"  # Default role

    class Config:
        schema_extra = {
            "example": {
                "email": "newuser@company.com",
                "role": "analyst"
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
                VALUES (:id, :org_id, :user_id, :action, :resource_type, :resource_id, :changes, :status, :error_message, :ip_address, :user_agent, :created_at)
                """,
                {
                    "id": str(uuid.uuid4()),
                    "org_id": org_id,
                    "user_id": user_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "changes": changes or {},
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
        "SELECT id, role FROM org_members WHERE org_id = :org_id AND user_id = :user_id",
        {"org_id": org_id, "user_id": user_id}
    )
    return member


async def _check_org_admin(org_id: str, user_id: str, db):
    """Check if user is an admin of the organization."""
    admin = await db.fetch_one(
        "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id AND role IN ('admin', 'owner')",
        {"org_id": org_id, "user_id": user_id}
    )
    return admin is not None


async def _count_org_admins(org_id: str, db):
    """Count number of admins in organization."""
    result = await db.fetch_one(
        "SELECT COUNT(*) as count FROM org_members WHERE org_id = :org_id AND role IN ('admin', 'owner')",
        {"org_id": org_id}
    )
    return result["count"] if result else 0


# ── Endpoints ────────────────────────────────────────────────────────────────

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
                    u.full_name as name,
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
            # Check admin authorization
            is_admin = await _check_org_admin(org_id, current_user.user_id, db)
            if not is_admin:
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

            # Check if user already a member
            existing_member = await db.fetch_one(
                """
                SELECT om.id FROM org_members om
                JOIN users u ON om.user_id = u.id
                WHERE om.org_id = :org_id AND u.email = :email
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
                WHERE org_id = :org_id AND email = :email AND status = 'pending' AND expires_at > :now
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
    - 400 Bad Request: Invalid or expired token
    - 404 Not Found: Invitation not found
    """
    try:
        async with get_db_connection() as db:
            # Fetch the invitation
            invitation = await db.fetch_one(
                "SELECT * FROM org_invitations WHERE token = :token",
                {"token": token}
            )

            if not invitation:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired invitation token"
                )

            # Check if expired
            if invitation["expires_at"] <= datetime.utcnow():
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
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired invitation token"
                )

            # 2. Validate invitation is not expired and pending
            if invitation["expires_at"] <= datetime.utcnow():
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
            if invitation["email"] != current_user.email:
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

    Requires: Organization admin authorization
    Returns: Updated member status
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

            # Verify member exists in this org
            member = await db.fetch_one(
                "SELECT id, user_id, role FROM org_members WHERE id = :id AND org_id = :org_id",
                {"id": member_id, "org_id": org_id}
            )
            if not member:
                raise HTTPException(status_code=404, detail="Member not found")

            # Prevent removing last admin
            if payload.role and payload.role not in ('admin', 'owner') and member["role"] in ('admin', 'owner'):
                admin_count = await _count_org_admins(org_id, db)
                if admin_count == 1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot remove the last organization admin"
                    )

            # Build update query
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

    Requires: Organization admin authorization
    Safeguard: Cannot remove the last organization admin
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

            # Verify member exists
            member = await db.fetch_one(
                "SELECT id, role, user_id FROM org_members WHERE id = :id AND org_id = :org_id",
                {"id": member_id, "org_id": org_id}
            )
            if not member:
                raise HTTPException(status_code=404, detail="Member not found")

            # Prevent removing last admin
            if member["role"] in ('admin', 'owner'):
                admin_count = await _count_org_admins(org_id, db)
                if admin_count == 1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot remove the last organization admin"
                    )

            # Delete member
            await db.execute(
                "DELETE FROM org_members WHERE id = :id AND org_id = :org_id",
                {"id": member_id, "org_id": org_id}
            )

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
                        "permissions": r["permissions"] if isinstance(r["permissions"], list) else [],
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

    Requires: Organization membership
    Returns: Audit report in requested format (JSON, CSV, or PDF)
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
                    "top_users": []  # Can be populated if needed
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
                # For PDF, return JSON for now (PDF generation would require additional library)
                # In production, use pypdf or reportlab
                return StreamingResponse(
                    iter([json.dumps(report_data)]),
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
