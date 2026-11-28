"""Share an Ask FairMind board as a read-only view.

POST   /packs/shared-views                      owner or admin: seal the board's figures and name who can open it
GET    /packs/shared-views                      the views this person shared
DELETE /packs/shared-views/{id}                 revoke: the link stops working at once
GET    /public/shared-views/{id}                no session: whether the view is open and who may open it
POST   /public/shared-views/{id}/code           no session: email a named person a one-time code
POST   /public/shared-views/{id}/verify         no session: trade the code for a reader token
POST   /public/shared-views/{id}/open           no session: a reader token for a view anyone with the link may open
GET    /public/shared-views/{id}/content        a reader token in X-View-Token: the sealed board and its figures

A view is a snapshot. The page the board draws reads its figures from GET endpoints; the browser says which ones, the
server fetches them again as the person sharing (so the figures are the server's, not the browser's) and stores the
responses with a SHA-256 seal over the question, layout, figures and time. The reader's page replays those responses.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes.packs import ASK_BOARD_MAX, _manager
from config.settings import settings
from database.connection import get_db
from src.application.services import ledger_service
from src.application.services.governance_assurance_service import OrgMembership
from src.application.services.reviewer_notify import decision_email, send_in_background

router = APIRouter()
public_router = APIRouter(tags=["shared-views-public"])

MAX_PATHS = 60
MAX_PATH_BYTES = 2_000_000
MAX_TOTAL_BYTES = 12_000_000
MAX_READERS = 10
CODE_MINUTES = 10
CODE_TRIES = 5
TOKEN_HOURS = 12
_PATH = re.compile(r"^/api/v1/[A-Za-z0-9_\-./%?=&,:+~]{1,300}$")
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]+$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _email(value: str) -> str:
    email = value.strip().lower()
    if len(email) > 320 or not _EMAIL.match(email):
        raise HTTPException(status_code=422, detail=f"{value.strip()[:80]} is not an email address")
    return email


def _mac(*parts: str) -> str:
    return hmac.new(settings.jwt_secret.encode(), "|".join(parts).encode(), hashlib.sha256).hexdigest()


def _token(view_id: str, email: str, expires: datetime) -> str:
    payload = f"{view_id}|{email}|{int(expires.timestamp())}"
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=") + "." + _mac("view-token", payload)


def _token_email(view_id: str, token: Optional[str]) -> str:
    """The email a reader token was issued to (empty for a link view); 401 when it is missing, forged, for another view or old."""
    try:
        body, sig = (token or "").split(".", 1)
        payload = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)).decode()
        vid, email, exp = payload.split("|")
        ok = hmac.compare_digest(sig, _mac("view-token", payload)) and vid == view_id and int(exp) > time.time()
    except Exception:
        ok = False
    if not ok:
        raise HTTPException(status_code=401, detail="Open the view again to continue")
    return email


def _seal(question: str, board: str, data: Dict[str, Any], sealed_at: str) -> str:
    blob = json.dumps({"question": question, "board": board, "data": data, "sealedAt": sealed_at}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def _view(db: Session, view_id: str):
    """The view's row when it can still be opened; 404 for an unknown, revoked or expired one (they look the same from outside)."""
    row = db.execute(text("SELECT * FROM shared_views WHERE id = :id"), {"id": view_id}).mappings().fetchone()
    if not row or row["revoked_at"] or row["expires_at"] <= _iso(_now()):
        raise HTTPException(status_code=404, detail="This view is not available")
    return row


class ShareBody(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    board: str = Field(min_length=1, max_length=ASK_BOARD_MAX)
    paths: List[str] = Field(min_length=1, max_length=MAX_PATHS)
    access: Literal["named", "link"] = "named"
    emails: List[str] = Field(default_factory=list, max_length=MAX_READERS)
    days: Literal[7, 30, 90] = 30


async def _fetch(request: Request, paths: List[str]) -> Dict[str, Any]:
    """GET each path from this app as the caller, with the caller's own credentials; a path that does not answer 200 is left out."""
    headers = {k: v for k, v in (("authorization", request.headers.get("authorization")), ("cookie", request.headers.get("cookie"))) if v}
    out: Dict[str, Any] = {}
    total = 0
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=request.app), base_url="http://internal", headers=headers, timeout=30) as client:
        for path in dict.fromkeys(paths):
            res = await client.get(path)
            if res.status_code != 200 or len(res.content) > MAX_PATH_BYTES:
                continue
            total += len(res.content)
            if total > MAX_TOTAL_BYTES:
                raise HTTPException(status_code=413, detail="This board holds too much to share as a view")
            out[path] = res.json()
    return out


@router.post("/shared-views")
async def share_view(body: ShareBody, request: Request, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    for p in body.paths:
        if not _PATH.match(p) or ".." in p or "/public/" in p or "shared-views" in p:
            raise HTTPException(status_code=422, detail="A figure the board reads cannot be shared")
    emails = list(dict.fromkeys(_email(e) for e in body.emails))
    if body.access == "named" and not emails:
        raise HTTPException(status_code=422, detail="Name at least one person, or share by link")
    data = await _fetch(request, body.paths)
    if not data:
        raise HTTPException(status_code=502, detail="The board's figures could not be read, so nothing was shared")
    now = _now()
    view_id = str(uuid.uuid4())
    sealed_at = _iso(now)
    question, board = body.question.strip(), body.board.strip()
    db.execute(
        text(
            "INSERT INTO shared_views (id, org_id, user_id, question, board, access, data_json, seal, sealed_at, expires_at, created_at) "
            "VALUES (:id, :org, :user, :q, :b, :access, :data, :seal, :at, :exp, :at)"
        ),
        {
            "id": view_id, "org": m.org_id, "user": m.user_id, "q": question, "b": board, "access": body.access,
            "data": json.dumps(data), "seal": _seal(question, board, data, sealed_at), "at": sealed_at, "exp": _iso(now + timedelta(days=body.days)),
        },
    )
    ledger_service.append(
        db, m.org_id, "view.sealed", "shared_view", view_id, m.user_id,
        {"seal": _seal(question, board, data, sealed_at), "access": body.access, "readers": len(emails), "expiresAt": _iso(now + timedelta(days=body.days))},
    )
    if body.access == "named":
        for email in emails:
            db.execute(text("INSERT INTO shared_view_readers (id, view_id, email) VALUES (:id, :v, :e)"), {"id": str(uuid.uuid4()), "v": view_id, "e": email})
    db.commit()
    path = f"/view/{view_id}"
    if emails:
        send_in_background(
            emails, "A FairMind board was shared with you",
            decision_email("A FairMind board was shared with you", [question, "You can look at it, not change it. You will be asked for a one-time code sent to this address."], path),
        )
    return {"id": view_id, "link": f"{settings.frontend_url.rstrip('/')}{path}", "expiresAt": _iso(now + timedelta(days=body.days)), "sealedAt": sealed_at}


@router.get("/shared-views")
def list_views(m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT id, question, access, seal, sealed_at, expires_at, revoked_at FROM shared_views WHERE org_id = :org AND user_id = :user ORDER BY created_at DESC LIMIT 50"),
        {"org": m.org_id, "user": m.user_id},
    ).mappings().all()
    readers: Dict[str, list] = {}
    if rows:
        for r in db.execute(
            text("SELECT view_id, email, opens, last_opened_at FROM shared_view_readers WHERE view_id IN (SELECT id FROM shared_views WHERE org_id = :org AND user_id = :user)"),
            {"org": m.org_id, "user": m.user_id},
        ).mappings():
            readers.setdefault(r["view_id"], []).append({"email": r["email"], "opens": r["opens"], "lastOpenedAt": r["last_opened_at"]})
    now = _iso(_now())
    return {"views": [
        {"id": r["id"], "question": r["question"], "access": r["access"], "seal": r["seal"], "sealedAt": r["sealed_at"], "expiresAt": r["expires_at"],
         "revoked": bool(r["revoked_at"]), "expired": r["expires_at"] <= now, "readers": readers.get(r["id"], [])}
        for r in rows
    ]}


@router.delete("/shared-views/{view_id}")
def revoke_view(view_id: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    done = db.execute(
        text("UPDATE shared_views SET revoked_at = :at WHERE id = :id AND org_id = :org AND user_id = :user AND revoked_at IS NULL"),
        {"at": _iso(_now()), "id": view_id, "org": m.org_id, "user": m.user_id},
    ).rowcount
    if done:
        ledger_service.append(db, m.org_id, "view.revoked", "shared_view", view_id, m.user_id, {})
    db.commit()
    if not done:
        raise HTTPException(status_code=404, detail="View not found")  # also what another person's view looks like
    return {"revoked": view_id}


# --- the reader's side: no session -----------------------------------------


class EmailBody(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class CodeBody(EmailBody):
    code: str = Field(min_length=6, max_length=6)


@public_router.get("/shared-views/{view_id}")
def view_status(view_id: str, db: Session = Depends(get_db)):
    row = _view(db, view_id)
    return {"access": row["access"], "expiresAt": row["expires_at"]}


@public_router.post("/shared-views/{view_id}/code")
def send_code(view_id: str, body: EmailBody, db: Session = Depends(get_db)):
    """Always answers the same, so the page never says who is on the list."""
    row = _view(db, view_id)
    email = body.email.strip().lower()
    reader = db.execute(text("SELECT id FROM shared_view_readers WHERE view_id = :v AND email = :e"), {"v": view_id, "e": email}).fetchone()
    if row["access"] == "named" and reader:
        code = f"{secrets.randbelow(10**6):06d}"
        db.execute(
            text("UPDATE shared_view_readers SET code_hash = :h, code_expires_at = :exp, code_attempts = 0 WHERE id = :id"),
            {"h": _mac("view-code", view_id, email, code), "exp": _iso(_now() + timedelta(minutes=CODE_MINUTES)), "id": reader[0]},
        )
        db.commit()
        from html import escape

        html = (
            "<div style=\"font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;padding:28px;color:#15171a\">"
            "<h1 style=\"font-size:20px;font-weight:600;margin:0 0 16px\">Your FairMind code</h1>"
            f"<p style=\"font-size:28px;font-weight:600;letter-spacing:.2em;margin:0 0 12px\">{escape(code)}</p>"
            f"<p style=\"margin:0\">It works for {CODE_MINUTES} minutes. If you did not ask for it, ignore this message.</p></div>"
        )
        send_in_background([email], "Your FairMind code", html)
    return {"sent": True}


@public_router.post("/shared-views/{view_id}/verify")
def verify_code(view_id: str, body: CodeBody, db: Session = Depends(get_db)):
    row = _view(db, view_id)
    email = body.email.strip().lower()
    reader = db.execute(
        text("SELECT id, code_hash, code_expires_at, code_attempts FROM shared_view_readers WHERE view_id = :v AND email = :e"), {"v": view_id, "e": email}
    ).mappings().fetchone()
    wrong = HTTPException(status_code=401, detail="That code did not work. Ask for a new one.")
    if not reader or not reader["code_hash"] or reader["code_expires_at"] <= _iso(_now()) or reader["code_attempts"] >= CODE_TRIES:
        raise wrong
    if not hmac.compare_digest(reader["code_hash"], _mac("view-code", view_id, email, body.code.strip())):
        db.execute(text("UPDATE shared_view_readers SET code_attempts = code_attempts + 1 WHERE id = :id"), {"id": reader["id"]})
        db.commit()
        raise wrong
    db.execute(text("UPDATE shared_view_readers SET code_hash = NULL WHERE id = :id"), {"id": reader["id"]})  # a code works once
    db.commit()
    expires = min(_now() + timedelta(hours=TOKEN_HOURS), datetime.fromisoformat(row["expires_at"]))
    return {"token": _token(view_id, email, expires)}


@public_router.post("/shared-views/{view_id}/open")
def open_link_view(view_id: str, db: Session = Depends(get_db)):
    row = _view(db, view_id)
    if row["access"] != "link":
        raise HTTPException(status_code=403, detail="This view is only for the people it names")
    return {"token": _token(view_id, "", min(_now() + timedelta(hours=TOKEN_HOURS), datetime.fromisoformat(row["expires_at"])))}


@public_router.get("/shared-views/{view_id}/content")
def view_content(view_id: str, x_view_token: Optional[str] = Header(default=None), db: Session = Depends(get_db)):
    email = _token_email(view_id, x_view_token)
    row = _view(db, view_id)
    if email:
        db.execute(
            text("UPDATE shared_view_readers SET opens = opens + 1, last_opened_at = :at WHERE view_id = :v AND email = :e"),
            {"at": _iso(_now()), "v": view_id, "e": email},
        )
        db.commit()
    return {
        "question": row["question"], "board": row["board"], "orgId": row["org_id"], "data": json.loads(row["data_json"]),
        "sealedAt": row["sealed_at"], "seal": row["seal"], "expiresAt": row["expires_at"], "email": email or None,
    }


@public_router.get("/shared-views/{view_id}/seal")
def view_seal(view_id: str, x_view_token: Optional[str] = Header(default=None), db: Session = Depends(get_db)):
    """Recompute the seal from what is stored and compare it with the one the ledger took when the view was sealed."""
    _token_email(view_id, x_view_token)
    row = _view(db, view_id)
    recomputed = _seal(row["question"], row["board"], json.loads(row["data_json"]), row["sealed_at"])
    sealed = next((e for e in ledger_service.entries(db, row["org_id"], "shared_view", view_id) if e["kind"] == "view.sealed"), None)
    return {
        "matchesStored": recomputed == row["seal"],
        "onLedger": bool(sealed) and sealed["payload"].get("seal") == recomputed,  # false for a view sealed before the ledger recorded views
        "ledgerSeq": sealed["seq"] if sealed else None, "ledgerHash": sealed["hash"] if sealed else None, "ledgerAt": sealed["createdAt"] if sealed else None,
        "chainValid": ledger_service.verify(db, row["org_id"])["valid"],
    }
