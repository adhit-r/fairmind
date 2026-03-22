"""
Org-specific registration with admin approval flow.

POST /api/v1/register          — public signup request
GET  /api/v1/registrations     — admin: list pending requests
POST /api/v1/registrations/{id}/approve  — admin: approve
POST /api/v1/registrations/{id}/deny     — admin: deny
"""

import uuid
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr

from config.database import get_db_connection
from config.settings import settings
from config.auth import get_current_active_user, require_admin, TokenData
from src.infrastructure.email.resend_service import email_service

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
async def submit_registration(payload: RegistrationRequest):
    """Anyone can request access. Admin is notified via Resend."""
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

            # Resolve or create org
            org = await db.fetch_one(
                "SELECT id FROM organizations WHERE name = :name",
                {"name": payload.org_name},
            )
            if not org:
                org_id = str(uuid.uuid4())
                slug = payload.org_name.lower().replace(" ", "-").replace(".", "-")
                await db.execute(
                    "INSERT INTO organizations (id, name, slug, domain) "
                    "VALUES (:id, :name, :slug, :domain)",
                    {"id": org_id, "name": payload.org_name, "slug": slug, "domain": payload.org_domain},
                )
            else:
                org_id = str(org["id"])

            await db.execute(
                "INSERT INTO registration_requests "
                "(id, email, name, org_name, org_domain, requested_role, message, org_id, status) "
                "VALUES (:id, :email, :name, :org_name, :org_domain, :role, :message, :org_id, 'pending')",
                {
                    "id": request_id,
                    "email": payload.email,
                    "name": payload.name,
                    "org_name": payload.org_name,
                    "org_domain": payload.org_domain,
                    "role": payload.requested_role,
                    "message": payload.message,
                    "org_id": org_id,
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
                        "org_domain": r.get("org_domain"),
                        "requested_role": r["requested_role"],
                        "message": r.get("message"),
                        "status": r["status"],
                        "review_notes": r.get("review_notes"),
                        "reviewed_at": r["reviewed_at"].isoformat() if r.get("reviewed_at") else None,
                        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
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
    """Admin: approve request → create user → send approval email."""
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

            # Create user account
            new_user_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO users (id, email, username, role, is_active, org_id, roles, name) "
                "VALUES (:id, :email, :username, :role, TRUE, :org_id, :roles::jsonb, :name) "
                "ON CONFLICT (email) DO UPDATE SET role = EXCLUDED.role, is_active = TRUE, org_id = EXCLUDED.org_id",
                {
                    "id": new_user_id,
                    "email": req["email"],
                    "username": req["email"].split("@")[0],
                    "role": req["requested_role"],
                    "org_id": str(req["org_id"]) if req.get("org_id") else None,
                    "roles": f'["{req["requested_role"]}"]',
                    "name": req["name"],
                },
            )

            # Mark request as approved
            await db.execute(
                "UPDATE registration_requests SET status='approved', reviewed_by=:reviewer, "
                "reviewed_at=:now, review_notes=:notes WHERE id=:id",
                {"reviewer": current_user.user_id, "now": datetime.utcnow(), "notes": body.notes, "id": request_id},
            )

        import asyncio
        asyncio.create_task(
            email_service.send_approval_email(req["email"], req["name"], req["org_name"])
        )

        logger.info(f"Registration approved: {req['email']} by {current_user.email}")
        return {"status": "approved", "user_created": True}

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
