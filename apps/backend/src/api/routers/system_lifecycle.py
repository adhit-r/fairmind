"""Recorded changes and retirement for one AI system.

GET  /systems/{id}/changes      the parts a change can name, what each reopens, and the changes on file
POST /systems/{id}/changes      record a change; a material one reopens the gate checks it touches
GET  /systems/{id}/retirement   the retirement on file, or the closing tasks and the suggested retention
POST /systems/{id}/retire       retire the system once every closing task is done; its file is then read only
"""

from __future__ import annotations

from datetime import date
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.routes.ai_governance import _authenticated_actor, _caller_org, _enforce_org_scope, _ensure_tables, _require_system_access
from api.routes.fairness_runs import _gate_payload, _system_row
from config.auth import TokenData, get_current_active_user
from database.connection import get_db
from src.application.services import system_lifecycle_service as lifecycle

router = APIRouter(tags=["lifecycle"], dependencies=[Depends(_enforce_org_scope)])

PartKey = Literal["data", "model", "tools", "threshold", "use", "docs"]
Reason = Literal["replaced", "not_needed", "failed_review", "rule_changed"]


def _with_env(db: Session, system_id: str) -> bool:
    from src.application.services.environmental_service import system_environmental_gate_enabled

    return system_environmental_gate_enabled(db, system_id)


def _snapshot(gate: dict) -> List[dict]:
    return [{"key": c["key"], "label": c["label"], "state": c["state"], "confidence": c["confidence"]} for c in gate["checks"]]


@router.get("/systems/{system_id}/changes")
def get_changes(system_id: str, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    with_env = _with_env(db, system_id)
    return {
        "parts": [{"key": k, "label": label, "reopens": lifecycle.reopens([k], with_env)} for k, label, _ in lifecycle.PARTS],
        "changes": [{**lifecycle._change_payload(r), "seal": r.seal} for r in lifecycle.list_changes(db, system_id)],
        "chain": lifecycle.verify_chain(db, system_id),
    }


class ChangeRequest(BaseModel):
    parts: List[PartKey] = Field(min_length=1)
    toVersion: Optional[str] = Field(default=None, max_length=64)
    note: Optional[str] = Field(default=None, max_length=2000)


@router.post("/systems/{system_id}/changes")
def post_change(
    system_id: str, body: ChangeRequest, http: Request,
    current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    """A named person records what changed. The gate is snapshotted first, so the record shows what the change reopened."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    system = _system_row(db, system_id)
    before = _gate_payload(db, system_id, system.risk_tier)
    change = lifecycle.record_change(
        db, system_id, _caller_org(http), parts=list(body.parts), to_version=(body.toVersion or "").strip() or None,
        note=(body.note or "").strip() or None, gate_before=_snapshot(before), recorded_by=_authenticated_actor(current_user),
        include_environmental=_with_env(db, system_id),
    )
    return {"change": change, "gate": _gate_payload(db, system_id, system.risk_tier)}


def _tasks(db: Session, system_id: str, org_id: Optional[str], reason: Optional[str], replaced_by: Optional[str]) -> List[dict]:
    computed = lifecycle.computed_tasks(db, system_id, org_id, reason, replaced_by)
    out = []
    for key, label, who, column in lifecycle.RETIREMENT_TASKS:
        if who == "fairmind" and computed.get(key) is None:
            continue  # does not apply, e.g. no replacement when the reason is not "replaced"
        out.append({"key": key, "label": label, "who": who, "column": column, "done": computed.get(key) if who == "fairmind" else None})
    return out


@router.get("/systems/{system_id}/retirement")
def get_retirement(
    system_id: str, http: Request, reason: Optional[Reason] = None, replacedBy: Optional[str] = None,
    current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    system = _system_row(db, system_id)
    row = lifecycle.get_retirement(db, system_id)
    return {
        "retired": {**lifecycle._retirement_payload(row), "seal": row.seal} if row is not None else None,
        "tasks": [] if row is not None else _tasks(db, system_id, _caller_org(http), reason, replacedBy),
        "retention": lifecycle.suggested_retention(system.risk_tier),
        "chain": lifecycle.verify_chain(db, system_id),
    }


class RetireRequest(BaseModel):
    reason: Reason
    replacedBy: Optional[str] = Field(default=None, max_length=64)
    lastDay: date
    retainYears: int = Field(ge=1, le=50)
    confirmed: List[str] = Field(default_factory=list)
    note: Optional[str] = Field(default=None, max_length=2000)


@router.post("/systems/{system_id}/retire")
def post_retire(
    system_id: str, body: RetireRequest, http: Request,
    current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    """Retire the system. Every person task must be confirmed and every check FairMind works out must pass."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)  # a retired system answers 409 here
    system = _system_row(db, system_id)
    org_id = _caller_org(http)
    if body.reason == "replaced" and not body.replacedBy:
        raise HTTPException(status_code=422, detail="Name the system that replaces it")
    missing = [label for key, label, who, _ in lifecycle.RETIREMENT_TASKS if who == "person" and key not in body.confirmed]
    if missing:
        raise HTTPException(status_code=422, detail=f"Not confirmed yet: {', '.join(missing)}")
    tasks = _tasks(db, system_id, org_id, body.reason, body.replacedBy)
    failing = [t["label"] for t in tasks if t["who"] == "fairmind" and not t["done"]]
    if failing:
        raise HTTPException(status_code=409, detail=f"Not true yet: {', '.join(failing)}")
    actor = _authenticated_actor(current_user)
    suggested = lifecycle.suggested_retention(system.risk_tier)
    basis = suggested["basis"] if suggested and suggested["years"] == body.retainYears else f"{body.retainYears} years, set by {actor}"
    record = lifecycle.retire(
        db, system_id, org_id, reason=body.reason, replaced_by=body.replacedBy if body.reason == "replaced" else None,
        last_day=body.lastDay, retain_years=body.retainYears, retain_basis=basis, note=(body.note or "").strip() or None,
        gate_snapshot=_snapshot(_gate_payload(db, system_id, system.risk_tier)),
        tasks=[{**t, "done": True, "by": actor if t["who"] == "person" else "FairMind"} for t in tasks], retired_by=actor,
    )
    return {"retired": record}
