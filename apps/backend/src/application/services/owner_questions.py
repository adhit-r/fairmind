"""Ask the likely owner of something a few questions through a link that needs no sign-in.

One row in governance_owner_checks per link; only the token's SHA-256 is stored. A check is about a discovered
asset (anchor_asset_id) or about any other subject (subject_type + subject_id, with the questions in questions_json).
The owner answers through /api/v1/public/owner-check/{token}.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

OWNER_LINK_DAYS = 14


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def ask(
    db: Session,
    *,
    org_id: str,
    email: str,
    title: str,
    created_by: Optional[str],
    subject_type: Optional[str] = None,
    subject_id: Optional[str] = None,
    questions: Optional[List[Dict[str, Any]]] = None,
    anchor_asset_id: Optional[str] = None,
    lines: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Mint a link, store the check, email the owner. Commits. The link is returned once, for copying when email is not set up.

    questions: [{key, text, options?, draft?, basis?}]. lines are the email's body; the default names the questions."""
    from config.settings import settings
    from src.application.services.reviewer_notify import decision_email, send_in_background

    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(days=OWNER_LINK_DAYS)).isoformat()
    check_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_owner_checks (id, org_id, anchor_asset_id, subject_type, subject_id, questions_json, email, token_hash, expires_at, created_by, created_at) "
            "VALUES (:id, :org, :anchor, :st, :sid, :q, :email, :hash, :exp, :by, :now)"
        ),
        {
            "id": check_id, "org": org_id, "anchor": anchor_asset_id, "st": subject_type, "sid": subject_id,
            "q": json.dumps(questions) if questions is not None else None, "email": email, "hash": hash_token(token),
            "exp": expires, "by": created_by, "now": now.isoformat(),
        },
    )
    db.commit()
    path = f"/owner-check/{token}"
    body = lines or ["Your AI governance team has a question about something you own.", *[str(q.get("text", "")) for q in questions or []]]
    send_in_background([email], title, decision_email(title, body, path))
    return {"link": f"{settings.frontend_url.rstrip('/')}{path}", "expiresAt": expires, "emailSent": bool(getattr(settings, "resend_api_key", None)), "id": check_id}


def answers_for(db: Session, subject_type: str, subject_id: str, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Every check about the subject, newest first: [{id, email, sentAt, answeredAt, questions, answers}]. Pass org_id to scope it."""
    rows = db.execute(
        text(
            "SELECT id, email, created_at, answered_at, questions_json, answers_json FROM governance_owner_checks "
            "WHERE subject_type = :st AND subject_id = :sid AND (CAST(:org AS text) IS NULL OR org_id = :org) ORDER BY created_at DESC"
        ),
        {"st": subject_type, "sid": subject_id, "org": org_id},
    ).fetchall()
    return [
        {"id": r[0], "email": r[1], "sentAt": r[2], "answeredAt": r[3],
         "questions": json.loads(r[4]) if r[4] else [], "answers": json.loads(r[5]) if r[5] else None}
        for r in rows
    ]
