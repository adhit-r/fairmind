"""Which risk tier and frameworks a system answers to, suggested by rules and confirmed by a person.

POST /applicability/suggest                       the rule table's suggestion for a set of answers
PUT  /systems/{id}/applicability                  confirm tier and frameworks; sets risk_tier, records evidence
POST /systems/{id}/applicability/accept-override  a second person accepts a tier set below the suggestion

Mounted under /api/v1/ai-governance next to the fairness router, with the same
org scoping and system access rules. The confirmed record lives in
governance_ai_systems.metadata_json.applicability; each decision also writes an
evidence row, so a later decision seal hashes it.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes.ai_governance import (
    _authenticated_actor,
    _caller_org,
    _enforce_org_scope,
    _ensure_tables,
    _fetch_latest_system_approval,
    _load_json_value,
    _require_system_access,
    _utc_now_iso,
    org_member,
)
from api.routes.fairness_runs import _gate_payload
from config.auth import TokenData, get_current_active_user
from database.connection import get_db
from src.application.services.applicability_service import USE_KEYS, ApplicabilityError, build_record, suggest
from src.application.services.fairness_run_service import ATTESTATION_CONFIDENCE

router = APIRouter(tags=["applicability"], dependencies=[Depends(_enforce_org_scope)])

SOURCE = "fairmind.applicability"


class ApplicabilityAnswers(BaseModel):
    use: Optional[str] = None
    decidesAboutPeople: Optional[bool] = None
    humanReview: Optional[Literal["each", "automatic"]] = None
    markets: List[Literal["IN", "EU", "OTHER"]] = Field(default_factory=list, max_length=3)
    rbiRegulated: Optional[Literal["yes", "no", "unsure"]] = None
    personalDataIndia: Optional[bool] = None
    intendedPurpose: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("use")
    @classmethod
    def _known_use(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in USE_KEYS:
            raise ValueError(f"{value} is not one of the listed uses")
        return value


class ApplicabilityConfirmRequest(BaseModel):
    answers: ApplicabilityAnswers
    tier: Literal["low", "medium", "high", "critical"]
    frameworks: List[str] = Field(default_factory=list, max_length=64)
    reason: Optional[str] = Field(default=None, max_length=2000)


class ApplicabilityAcceptRequest(BaseModel):
    evidenceId: str = Field(min_length=1, max_length=64)  # the record the person reviewed


def _locked_system(db: Session, system_id: str) -> tuple:
    """risk_tier and metadata, row-locked until the commit so the metadata merge cannot lose a concurrent write."""
    row = db.execute(
        text("SELECT risk_tier, metadata_json FROM governance_ai_systems WHERE id = :id FOR UPDATE"), {"id": system_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="AI system not found")
    return row[0], _load_json_value(row[1], {})


def _save(db: Session, http: Request, actor: str, system_id: str, *, tier: str, metadata: Dict[str, Any], record: Dict[str, Any], evidence_id: str, evidence_type: str, title: str) -> None:
    """The tier, the metadata with only its applicability key replaced, and one evidence row: one transaction, one commit."""
    now = _utc_now_iso()
    db.execute(
        text("UPDATE governance_ai_systems SET risk_tier = :tier, metadata_json = :metadata, updated_at = :now WHERE id = :id"),
        {"id": system_id, "tier": tier, "metadata": json.dumps({**metadata, "applicability": record}), "now": now},
    )
    # Not _insert_evidence: it commits on its own, and this row belongs to the same transaction.
    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, system_id, org_id, evidence_type, title, source, content_json, confidence, status, uploaded_by, metadata_json, captured_at, created_at) "
            "VALUES (:id, :system_id, :org_id, :evidence_type, :title, :source, :content_json, :confidence, :status, :uploaded_by, :metadata_json, :captured_at, :created_at)"
        ),
        {
            "id": evidence_id,
            "system_id": system_id, "org_id": _caller_org(http), "evidence_type": evidence_type, "title": title, "source": SOURCE,
            "content_json": json.dumps(record), "confidence": ATTESTATION_CONFIDENCE, "status": "collected", "uploaded_by": actor,
            "metadata_json": json.dumps({"provenance_class": "manual", "rules_version": record["rulesVersion"], "computed_at": now}),
            "captured_at": now, "created_at": now,
        },
    )
    db.commit()


@router.post("/applicability/suggest", dependencies=[Depends(org_member)])
def suggest_applicability(body: ApplicabilityAnswers):
    """Stateless: the onboard form calls it on every answer, before the system exists."""
    return suggest(body.model_dump())


@router.put("/systems/{system_id}/applicability")
def confirm_applicability(
    system_id: str,
    body: ApplicabilityConfirmRequest,
    http: Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Confirm the tier and frameworks. The suggestion is recomputed here from the answers, never taken from the client."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    actor = _authenticated_actor(current_user)
    try:
        record = build_record(body.answers.model_dump(), tier=body.tier, frameworks=body.frameworks, reason=body.reason, confirmed_by=actor, confirmed_at=_utc_now_iso())
    except ApplicabilityError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    approval = _fetch_latest_system_approval(db, system_id)
    if approval and approval["status"] == "pending":
        raise HTTPException(status_code=409, detail="An approval request is pending; decide it before changing the tier or rules")
    _, metadata = _locked_system(db, system_id)
    record["evidenceId"] = str(uuid.uuid4())
    _save(
        db, http, actor, system_id, tier=record["tier"], metadata=metadata, record=record,
        evidence_id=record["evidenceId"], evidence_type="applicability_decision", title=f"Risk tier {record['tier']} and frameworks confirmed",
    )
    return {"applicability": record, "gate": _gate_payload(db, system_id, record["tier"])}


@router.post("/systems/{system_id}/applicability/accept-override")
def accept_applicability_override(
    system_id: str,
    body: ApplicabilityAcceptRequest,
    http: Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """A second person accepts a tier set below the suggestion; until then the gate keeps the suggested tier."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    actor = _authenticated_actor(current_user)
    stored_tier, metadata = _locked_system(db, system_id)
    record = metadata.get("applicability")
    if not isinstance(record, dict) or not record.get("tierBelowSuggestion") or record.get("overrideAcceptedBy"):
        raise HTTPException(status_code=409, detail="Nothing to accept")
    if actor == record.get("confirmedBy"):
        raise HTTPException(status_code=403, detail="The person who lowered the tier cannot accept it")
    # Accepting changes the tier the gate uses, so it waits for a pending request like a tier change does.
    approval = _fetch_latest_system_approval(db, system_id)
    if approval and approval["status"] == "pending":
        raise HTTPException(status_code=409, detail="An approval request is pending; decide it before accepting the lower tier")
    # An acceptance holds only for the tier and reason the person read; a newer confirmation needs a fresh look.
    if body.evidenceId != record.get("evidenceId"):
        raise HTTPException(status_code=409, detail="The tier changed since you looked; review it again")
    record = {**record, "overrideAcceptedBy": actor, "overrideAcceptedAt": _utc_now_iso()}
    _save(
        db, http, actor, system_id, tier=stored_tier, metadata=metadata, record=record,
        evidence_id=str(uuid.uuid4()), evidence_type="applicability_override_accepted", title=f"Lower risk tier {record['tier']} accepted",
    )
    return {"applicability": record, "gate": _gate_payload(db, system_id, stored_tier)}
