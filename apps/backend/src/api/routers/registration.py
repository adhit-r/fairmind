"""
Org-specific registration with admin approval flow.

POST /api/v1/register          — public signup request
GET  /api/v1/registrations     — admin: list pending requests
POST /api/v1/registrations/{id}/approve  — admin: approve
POST /api/v1/registrations/{id}/deny     — admin: deny

"admin" here is the platform operator (users.role = 'admin'). Approval only
ever creates a new account and a new organisation owned by it; joining an
existing organisation is the invitation flow's job.
"""

import re
import secrets
import uuid
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel, EmailStr

from config.database import get_db_connection, get_db_transaction
from config.settings import settings
from config.auth import auth_manager, get_current_active_user, require_admin, TokenData
from src.application.services.api_boundary_dependencies import email_service

logger = logging.getLogger("fairmind.registration")
router = APIRouter(tags=["registration"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class RegistrationRequest(BaseModel):
    email: EmailStr
    name: str
    org_name: str
    org_domain: Optional[str] = None
    requested_role: str = "analyst"
    message: Optional[str] = None


class ReviewRequest(BaseModel):
    notes: Optional[str] = None


# ── Public: submit a signup request ──────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def submit_registration(payload: RegistrationRequest, request: Request):
    """Anyone can request access. Admin is notified via Resend."""
    from middleware.security import client_ip
    from src.api.routers.auth import _reset_rate_limited

    # Each request emails the platform admin, so cap them per address and per IP.
    if _reset_rate_limited(f"register-email:{payload.email.lower()}", f"register-ip:{client_ip(request)}"):
        raise HTTPException(status_code=429, detail="Too many requests. Try again in a few minutes.")
    request_id = str(uuid.uuid4())

    try:
        async with get_db_connection() as db:
            # Check for existing pending request from same email
            existing = await db.fetch_one(
                "SELECT id FROM registration_requests WHERE email = :email AND status = 'pending'",
                {"email": payload.email},
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A pending request for this email already exists.",
                )

            # No organisation is created or looked up until an admin approves.
            await db.execute(
                "INSERT INTO registration_requests "
                "(id, email, name, org_name, org_domain, requested_role, message, status) "
                "VALUES (:id, :email, :name, :org_name, :org_domain, :role, :message, 'pending')",
                {
                    "id": request_id,
                    "email": payload.email,
                    "name": payload.name,
                    "org_name": payload.org_name,
                    "org_domain": payload.org_domain,
                    "role": payload.requested_role,
                    "message": payload.message,
                },
            )

        # Notify admin via Resend
        import asyncio
        asyncio.create_task(
            email_service.send_registration_request_to_admin(
                admin_email=settings.admin_email,
                requester_name=payload.name,
                requester_email=payload.email,
                org_name=payload.org_name,
                requested_role=payload.requested_role,
                request_id=request_id,
                message=payload.message,
            )
        )

        logger.info(f"Registration request submitted: {payload.email} for {payload.org_name}")
        return {"id": request_id, "status": "pending", "message": "Request submitted. You will be notified by email."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration request error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit registration request")


# ── Admin: list pending requests ─────────────────────────────────────────────

@router.get("/registrations")
async def list_registrations(
    status_filter: Optional[str] = "pending",
    current_user: TokenData = Depends(require_admin),
):
    """Admin: list registration requests."""
    try:
        async with get_db_connection() as db:
            where = "WHERE status = :status" if status_filter else ""
            rows = await db.fetch_all(
                f"SELECT * FROM registration_requests {where} ORDER BY created_at DESC",
                {"status": status_filter} if status_filter else {},
            )
            return {
                "requests": [
                    {
                        "id": str(r["id"]),
                        "email": r["email"],
                        "name": r["name"],
                        "org_name": r["org_name"],
                        "org_domain": r["org_domain"],
                        "requested_role": r["requested_role"],
                        "message": r["message"],
                        "status": r["status"],
                        "review_notes": r["review_notes"],
                        "reviewed_at": r["reviewed_at"].isoformat() if r["reviewed_at"] else None,
                        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    }
                    for r in rows
                ]
            }
    except Exception as e:
        logger.error(f"List registrations error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list registrations")


# ── Admin: approve ────────────────────────────────────────────────────────────

@router.post("/registrations/{request_id}/approve")
async def approve_registration(
    request_id: str,
    body: ReviewRequest = ReviewRequest(),
    current_user: TokenData = Depends(require_admin),
):
    """Admin: approve request → create user and the new org they own → send approval email.

    Refuses (409) when the email already has an account or the organisation
    name is taken, so approval can never change an existing user or org.
    """
    try:
        async with get_db_transaction() as db:
            req = await db.fetch_one(
                "SELECT * FROM registration_requests WHERE id = :id",
                {"id": request_id},
            )

            if not req:
                raise HTTPException(status_code=404, detail="Request not found")
            if req["status"] != "pending":
                raise HTTPException(status_code=409, detail=f"Request is already {req['status']}")
            if await db.fetch_one("SELECT id FROM users WHERE lower(email) = lower(:e)", {"e": req["email"]}):
                raise HTTPException(
                    status_code=409,
                    detail="An account with this email already exists. Use an organisation invitation instead.",
                )
            if await db.fetch_one("SELECT id FROM organizations WHERE lower(name) = lower(:n)", {"n": req["org_name"]}):
                raise HTTPException(
                    status_code=409,
                    detail="An organisation with this name already exists. Its owner can invite the requester.",
                )

            # The global role stays analyst: requested_role is requester input and
            # 'admin' would make them a platform operator. Org rights come from
            # org_members. The password is a random one nobody knows; the approval
            # email carries a single-use link to choose a real one, which also
            # proves the requester controls the address.
            user_id = str(uuid.uuid4())
            password_hash = auth_manager.get_password_hash(secrets.token_urlsafe(32))
            org_id = str(uuid.uuid4())
            now = datetime.utcnow()
            slug_base = re.sub(r"[^a-z0-9]+", "-", req["org_name"].lower()).strip("-") or "org"
            await db.execute(
                "INSERT INTO users (id, email, username, password_hash, name, role, roles, is_active) "
                "VALUES (:id, :email, :username, :pw, :name, 'analyst', CAST(:roles AS jsonb), TRUE)",
                {
                    "id": user_id,
                    "pw": password_hash,
                    "email": req["email"],
                    "username": f"{req['email'].split('@')[0]}-{secrets.token_hex(3)}",
                    "name": req["name"],
                    "roles": '["analyst"]',
                },
            )
            await db.execute(
                "INSERT INTO organizations (id, name, slug, domain, owner_id, is_active) "
                "VALUES (:id, :name, :slug, :domain, :owner, TRUE)",
                {
                    "id": org_id,
                    "name": req["org_name"],
                    "slug": f"{slug_base}-{secrets.token_hex(3)}",
                    "domain": req["org_domain"],
                    "owner": user_id,
                },
            )
            await db.execute(
                "UPDATE users SET org_id = :org, primary_org_id = :org WHERE id = :id",
                {"org": org_id, "id": user_id},
            )
            await db.execute(
                "INSERT INTO org_members (id, org_id, user_id, role, status, joined_at) "
                "VALUES (:id, :org, :user, 'owner', 'active', :now)",
                {"id": str(uuid.uuid4()), "org": org_id, "user": user_id, "now": now},
            )
            await db.execute(
                "UPDATE registration_requests SET status='approved', org_id=:org, reviewed_by=:reviewer, "
                "reviewed_at=:now, review_notes=:notes WHERE id=:id",
                {"org": org_id, "reviewer": current_user.user_id, "now": now, "notes": body.notes, "id": request_id},
            )

        token = auth_manager.create_password_reset_token(user_id, password_hash)
        # The token rides in the fragment, which browsers never send to a server.
        set_password_url = f"{settings.frontend_url}/reset-password#token={token}"
        import asyncio
        asyncio.create_task(
            email_service.send_approval_email(
                req["email"], req["name"], req["org_name"], set_password_url,
                auth_manager.password_reset_expire_minutes,
            )
        )

        logger.info(f"Registration approved: {req['email']} by {current_user.email}")
        return {"status": "approved", "user_created": True, "user_id": user_id, "org_id": org_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve registration error: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve registration")


# ── Admin: deny ───────────────────────────────────────────────────────────────

@router.post("/registrations/{request_id}/deny")
async def deny_registration(
    request_id: str,
    body: ReviewRequest = ReviewRequest(),
    current_user: TokenData = Depends(require_admin),
):
    """Admin: deny request → send denial email."""
    try:
        async with get_db_connection() as db:
            req = await db.fetch_one(
                "SELECT * FROM registration_requests WHERE id = :id",
                {"id": request_id},
            )

            if not req:
                raise HTTPException(status_code=404, detail="Request not found")
            if req["status"] != "pending":
                raise HTTPException(status_code=409, detail=f"Request is already {req['status']}")

            await db.execute(
                "UPDATE registration_requests SET status='denied', reviewed_by=:reviewer, "
                "reviewed_at=:now, review_notes=:notes WHERE id=:id",
                {"reviewer": current_user.user_id, "now": datetime.utcnow(), "notes": body.notes, "id": request_id},
            )

        import asyncio
        asyncio.create_task(
            email_service.send_denial_email(req["email"], req["name"], req["org_name"], body.notes)
        )

        logger.info(f"Registration denied: {req['email']} by {current_user.email}")
        return {"status": "denied"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deny registration error: {e}")
        raise HTTPException(status_code=500, detail="Failed to deny registration")
