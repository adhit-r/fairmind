"""AI-drafted scoping: does a framework apply to each system? The agent drafts with cited evidence, a person decides.

GET  /frameworks/{key}/scope                      the framework's test, a summary and one item per drafted system
POST /frameworks/{key}/scope/draft                draft the systems that have no draft yet (respects Autopilot)
POST /frameworks/{key}/scope/{system_id}/confirm  the person's in or out; a reason is needed to differ from the draft
POST /frameworks/{key}/scope/accept-sure          confirm every undecided high-confidence draft as drafted
POST /frameworks/{key}/scope/{system_id}/ask-owner  send the system's owner a question link

Mounted under /api/v1/ai-governance. Every query filters on the caller's organisation.
"""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes.ai_governance import org_member, org_mutator
from api.routes.discovery_review import _email
from database.connection import get_db
from src.application.services import framework_scope_service as svc
from src.application.services.governance_assurance_service import OrgMembership

router = APIRouter(prefix="/frameworks/{framework_key}/scope", tags=["framework-scope"])


class ConfirmRequest(BaseModel):
    verdict: Literal["in", "out"]
    reason: Optional[str] = Field(default=None, max_length=2000)


class AskRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


def _known(framework_key: str) -> None:
    if not svc.framework_test(framework_key):
        raise HTTPException(status_code=404, detail="Framework not found")


def _own_system(db: Session, org_id: str, system_id: str) -> None:
    if not db.execute(text("SELECT 1 FROM governance_ai_systems WHERE id = :s AND org_id = :org"), {"s": system_id, "org": org_id}).fetchone():
        raise HTTPException(status_code=404, detail="AI system not found")


@router.get("")
def read_scope(framework_key: str, m: OrgMembership = Depends(org_member), db: Session = Depends(get_db)):
    _known(framework_key)
    return svc.view(db, m.org_id, framework_key)


@router.post("/draft")
async def draft_scope(framework_key: str, m: OrgMembership = Depends(org_mutator), db: Session = Depends(get_db)):
    _known(framework_key)
    await svc.draft_missing(db, m.org_id, framework_key)
    return svc.view(db, m.org_id, framework_key)


@router.post("/accept-sure")
def accept_sure(framework_key: str, m: OrgMembership = Depends(org_mutator), db: Session = Depends(get_db)):
    _known(framework_key)
    n = svc.accept_sure(db, m.org_id, framework_key, m.user_id)
    return {"accepted": n, "view": svc.view(db, m.org_id, framework_key)}


@router.post("/{system_id}/confirm")
def confirm_scope(framework_key: str, system_id: str, body: ConfirmRequest, m: OrgMembership = Depends(org_mutator), db: Session = Depends(get_db)):
    _known(framework_key)
    _own_system(db, m.org_id, system_id)
    svc.confirm(db, m.org_id, framework_key, system_id, body.verdict, body.reason, m.user_id)
    return svc.view_item(db, m.org_id, framework_key, system_id)


@router.post("/{system_id}/ask-owner")
def ask_scope_owner(framework_key: str, system_id: str, body: AskRequest, m: OrgMembership = Depends(org_mutator), db: Session = Depends(get_db)):
    _known(framework_key)
    _own_system(db, m.org_id, system_id)
    email = _email(body.email)
    if not email:
        raise HTTPException(status_code=422, detail="That is not an email address")
    out = svc.ask_owner(db, m.org_id, framework_key, system_id, email, m.user_id)
    return {k: out[k] for k in ("link", "expiresAt", "emailSent")}
