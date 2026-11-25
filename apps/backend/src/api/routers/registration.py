"""
Org-specific registration with admin approval flow.

POST /api/v1/register          — public signup request
GET  /api/v1/registrations     — admin: list pending requests
POST /api/v1/registrations/{id}/approve  — admin: approve
POST /api/v1/registrations/{id}/deny     — admin: deny

"admin" here is the platform operator (users.role = 'admin'). A request from an
address whose domain an organisation owns (org_domains) is a join request: it is
routed to that organisation's owners and admins, who decide it in Settings. Any
other request is the platform operator's, and approving it creates a new account
and a new organisation it owns.
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
from config.turnstile import require_turnstile
from config.auth import auth_manager, get_current_active_user, require_admin, TokenData
from src.application.services.api_boundary_dependencies import email_service
from src.application.services.org_domains import email_domain, is_personal, name_key

logger = logging.getLogger("fairmind.registration")
router = APIRouter(tags=["registration"])


async def create_account(db, email: str, name: str) -> tuple:
    """A new account with a random password nobody knows; the welcome email's link sets a real one.

    The global role stays analyst: org rights come from org_members, and 'admin' would make them a
    platform operator. Returns (user_id, password_hash), the hash binding the single-use link.
    """
    user_id = str(uuid.uuid4())
    password_hash = auth_manager.get_password_hash(secrets.token_urlsafe(32))
    await db.execute(
        "INSERT INTO users (id, email, username, password_hash, name, role, roles, is_active) "
        "VALUES (:id, :email, :username, :pw, :name, 'analyst', CAST(:roles AS jsonb), TRUE)",
        {"id": user_id, "pw": password_hash, "email": email, "username": f"{email.split('@')[0]}-{secrets.token_hex(3)}",
         "name": name, "roles": '["analyst"]'},
    )
    return user_id, password_hash


def send_welcome(user_id: str, password_hash: str, email: str, name: str, org_name: str) -> None:
    """The approval email with a single-use link to choose a password, which also proves the address."""
    import asyncio

    token = auth_manager.create_password_reset_token(user_id, password_hash)
    # The token rides in the fragment, which browsers never send to a server.
    url = f"{settings.frontend_url}/reset-password#token={token}&welcome=1"
    asyncio.create_task(email_service.send_approval_email(email, name, org_name, url, auth_manager.password_reset_expire_minutes))


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

@router.post("/register", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_turnstile)])
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
                "SELECT id FROM registration_requests WHERE lower(email) = lower(:email) AND status = 'pending'",
                {"email": payload.email},
            )
            if existing:
                # Same answer as a new request, so the form cannot be used to learn
                # who has applied; no second row and no second admin email.
                return {"id": str(existing["id"]), "status": "pending", "message": "Request submitted. You will be notified by email."}

            # An address on a domain an organisation owns joins that organisation; whatever name was typed.
            domain = email_domain(payload.email)
            owner_org = None if is_personal(domain) else await db.fetch_one(
                "SELECT o.id, o.name FROM org_domains d JOIN organizations o ON o.id = d.org_id WHERE d.domain = :d",
                {"d": domain},
            )
            await db.execute(
                "INSERT INTO registration_requests "
                "(id, email, name, org_name, org_domain, requested_role, message, status, org_id, is_join) "
                "VALUES (:id, :email, :name, :org_name, :org_domain, :role, :message, 'pending', :org, :join)",
                {
                    "id": request_id,
                    "email": payload.email,
                    "name": payload.name,
                    "org_name": owner_org["name"] if owner_org else payload.org_name,
                    "org_domain": payload.org_domain,
                    "role": payload.requested_role,
                    "message": payload.message,
                    "org": str(owner_org["id"]) if owner_org else None,
                    "join": bool(owner_org),
                },
            )
            managers = [] if not owner_org else await db.fetch_all(
                "SELECT u.email FROM org_members m JOIN users u ON CAST(u.id AS TEXT) = CAST(m.user_id AS TEXT) "
                "WHERE m.org_id = :org AND m.status = 'active' AND m.role IN ('owner', 'admin')",
                {"org": str(owner_org["id"])},
            )

        if owner_org:
            import asyncio
            for m in managers:
                asyncio.create_task(email_service.send_join_request(
                    m["email"], payload.name, payload.email, owner_org["name"], f"{settings.frontend_url}/settings?section=team",
                ))
            logger.info("Join request %s routed to the admins of %s", request_id, owner_org["id"])
            return {"id": request_id, "status": "pending", "message": "Request submitted. You will be notified by email."}

        # Notify admin via Resend
        if settings.admin_email:
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
        else:
            logger.warning("ADMIN_EMAIL is not set; access request %s was saved but no notice was sent", request_id)

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
            orgs = await db.fetch_all("SELECT o.id, o.name, d.domain FROM organizations o LEFT JOIN org_domains d ON d.org_id = o.id")
            by_key: dict = {}
            for o in orgs:
                by_key.setdefault(name_key(o["name"]), {"id": str(o["id"]), "name": o["name"], "domains": []})["domains"] += [o["domain"]] if o["domain"] else []

            def similar(r):
                if r["is_join"]:
                    return []
                hit = by_key.get(name_key(r["org_name"]))
                return [hit] if hit else []

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
                        # Pending with an org: a join request its owners decide. Approved: the org it created or joined.
                        "org_id": str(r["org_id"]) if r["org_id"] else None,
                        "join": bool(r["is_join"]) and r["status"] == "pending",
                        "similar_orgs": similar(r),
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
            if req["is_join"]:
                raise HTTPException(status_code=409, detail="This request is to join an existing organisation; its owners and admins decide it")
            if await db.fetch_one("SELECT id FROM organizations WHERE lower(name) = lower(:n)", {"n": req["org_name"]}):
                raise HTTPException(
                    status_code=409,
                    detail="An organisation with this name already exists. Its owner can invite the requester.",
                )
            domain = email_domain(req["email"])
            taken = None if is_personal(domain) else await db.fetch_one(
                "SELECT o.name FROM org_domains d JOIN organizations o ON o.id = d.org_id WHERE d.domain = :d", {"d": domain}
            )
            if taken:
                raise HTTPException(status_code=409, detail=f"{domain} belongs to {taken['name']}; its owner can invite the requester")

            # The global role stays analyst: requested_role is requester input and
            # 'admin' would make them a platform operator. Org rights come from
            # org_members. The password is a random one nobody knows; the approval
            # email carries a single-use link to choose a real one, which also
            # proves the requester controls the address.
            user_id, password_hash = await create_account(db, req["email"], req["name"])
            org_id = str(uuid.uuid4())
            now = datetime.utcnow()
            slug_base = re.sub(r"[^a-z0-9]+", "-", req["org_name"].lower()).strip("-") or "org"
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
            if not is_personal(domain):
                # The owner's own work address is the first proof the new org owns its domain.
                await db.execute(
                    "INSERT INTO org_domains (id, org_id, domain, verified_via, added_by, created_at) "
                    "VALUES (:id, :org, :d, 'owner_email', :by, :now)",
                    {"id": str(uuid.uuid4()), "org": org_id, "d": domain, "by": user_id, "now": now},
                )
            await db.execute(
                "UPDATE registration_requests SET status='approved', org_id=:org, reviewed_by=:reviewer, "
                "reviewed_at=:now, review_notes=:notes WHERE id=:id",
                {"org": org_id, "reviewer": current_user.user_id, "now": now, "notes": body.notes, "id": request_id},
            )

        send_welcome(user_id, password_hash, req["email"], req["name"], req["org_name"])

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
