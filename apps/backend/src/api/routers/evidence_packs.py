"""Inspection packs: build a hashed manifest, share a read-only auditor link, verify offline.

POST   /packs                 build a pack for chosen systems and frameworks
GET    /packs                 the caller's organisation's packs
GET    /packs/frameworks      frameworks the clause map covers
GET    /packs/{id}            manifest, hash and share state
GET    /packs/{id}/download   manifest and hash as an attachment
POST   /packs/{id}/share      mint an auditor token (returned once; only its SHA-256 is stored)
DELETE /packs/{id}/share      revoke the token
GET    /api/v1/public/packs/{id}?t=<token>   no auth; the token is the credential

The first group is mounted under /api/v1/ai-governance with its org scoping; the
public router carries no org dependency because an auditor has no session.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes.ai_governance import (
    _authenticated_actor,
    _caller_org,
    _enforce_org_scope,
    _ensure_tables,
    _require_system_access,
)
from api.routes.fairness_runs import _gate_payload, _system_row
from config.auth import TokenData, get_current_active_user
from config.settings import settings
from database.connection import get_db
from src.application.services.evidence_pack_service import (
    build_manifest,
    canonical_bytes,
    clause_frameworks,
    is_expired,
    manifest_digest,
    new_share_token,
    token_matches,
)
from src.application.services.governance_assurance_service import GovernanceAssuranceService, OrgMembership

router = APIRouter(tags=["evidence-packs"], dependencies=[Depends(_enforce_org_scope)])
public_router = APIRouter(tags=["evidence-packs-public"])

_COLUMNS = "id, org_id, title, frameworks_json, system_ids_json, manifest_json, manifest_hash, created_by, created_at, share_token_hash, share_expires_at"


class PackCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    frameworks: List[str] = Field(..., min_length=1)
    system_ids: List[str] = Field(..., min_length=1, max_length=50)


def _pack_row(db: Session, pack_id: str, org_id: str) -> Any:
    row = db.execute(text(f"SELECT {_COLUMNS} FROM governance_evidence_packs WHERE id = :id"), {"id": pack_id}).fetchone()
    if not row or str(row[1]) != str(org_id):
        raise HTTPException(status_code=404, detail="Pack not found")
    return row


def _share_state(row: Any) -> Dict[str, Any]:
    active = bool(row[9]) and not is_expired(row[10])
    return {"shared": active, "expiresAt": row[10] if row[9] else None, "expired": bool(row[9]) and not active}


def _summary(row: Any) -> Dict[str, Any]:
    return {
        "id": row[0], "title": row[2], "frameworks": json.loads(row[3]), "systemIds": json.loads(row[4]),
        "manifestHash": row[6], "createdBy": row[7], "createdAt": row[8], "share": _share_state(row),
    }


def _require_org_mutator(db: Session, org_id: str, current_user: TokenData) -> None:
    service = GovernanceAssuranceService(db)
    membership = service.membership(org_id, current_user.user_id)
    if not membership and settings.is_development and current_user.org_id and str(current_user.org_id) == str(org_id):
        # Same development fallback as _require_system_access: memberships live in another database.
        membership = OrgMembership(str(org_id), current_user.user_id, current_user.role.value, tuple(current_user.permissions))
    if not membership:
        raise HTTPException(status_code=404, detail="Pack not found")
    if not service.may_mutate(membership):
        raise HTTPException(status_code=403, detail="Organization mutation permission required")


@router.get("/packs/frameworks")
def list_pack_frameworks(current_user: TokenData = Depends(get_current_active_user)):
    return clause_frameworks()


@router.post("/packs")
def create_pack(
    body: PackCreateRequest,
    http: Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    org_id = _caller_org(http)
    known = {f["key"] for f in clause_frameworks()}
    unknown = [f for f in body.frameworks if f not in known]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown frameworks: {', '.join(unknown)}")
    system_ids = list(dict.fromkeys(body.system_ids))
    systems = []
    for system_id in system_ids:
        _require_system_access(db, system_id, current_user)
        system = _system_row(db, system_id)
        org = db.execute(text("SELECT org_id FROM governance_ai_systems WHERE id = :id"), {"id": system_id}).scalar()
        if str(org) != str(org_id):
            raise HTTPException(status_code=404, detail="AI system not found")
        systems.append({"id": system.id, "name": system.name, "riskTier": system.risk_tier, "gate": _gate_payload(db, system_id, system.risk_tier)})
    frameworks = list(dict.fromkeys(body.frameworks))
    manifest = build_manifest(db, title=body.title.strip(), frameworks=frameworks, systems=systems, created_by=_authenticated_actor(current_user))
    pack_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_evidence_packs (id, org_id, title, frameworks_json, system_ids_json, manifest_json, manifest_hash, created_by, created_at) "
            "VALUES (:id, :org_id, :title, :frameworks, :system_ids, :manifest, :hash, :created_by, :created_at)"
        ),
        {
            "id": pack_id, "org_id": org_id, "title": manifest["title"], "frameworks": json.dumps(frameworks), "system_ids": json.dumps(system_ids),
            # stored as the canonical text so the hash is always recomputable from the column
            "manifest": canonical_bytes(manifest).decode(), "hash": manifest_digest(manifest), "created_by": manifest["createdBy"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    db.commit()
    return _summary(_pack_row(db, pack_id, org_id))


@router.get("/packs")
def list_packs(http: Request, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _ensure_tables(db)
    rows = db.execute(
        text(f"SELECT {_COLUMNS} FROM governance_evidence_packs WHERE org_id = :org ORDER BY created_at DESC"), {"org": _caller_org(http)}
    ).fetchall()
    return [_summary(r) for r in rows]


@router.get("/packs/{pack_id}")
def get_pack(pack_id: str, http: Request, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _ensure_tables(db)
    row = _pack_row(db, pack_id, _caller_org(http))
    return {**_summary(row), "manifest": json.loads(row[5])}


@router.get("/packs/{pack_id}/download")
def download_pack(pack_id: str, http: Request, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _ensure_tables(db)
    row = _pack_row(db, pack_id, _caller_org(http))
    body = json.dumps({"manifest": json.loads(row[5]), "manifestHash": row[6]}, indent=2, ensure_ascii=False)
    return Response(body, media_type="application/json", headers={"Content-Disposition": f'attachment; filename="inspection-pack-{row[0]}.json"'})


@router.post("/packs/{pack_id}/share")
def share_pack(pack_id: str, http: Request, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _ensure_tables(db)
    org_id = _caller_org(http)
    _pack_row(db, pack_id, org_id)
    _require_org_mutator(db, org_id, current_user)
    share = new_share_token()
    db.execute(
        text("UPDATE governance_evidence_packs SET share_token_hash = :h, share_expires_at = :e WHERE id = :id"),
        {"h": share["hash"], "e": share["expiresAt"], "id": pack_id},
    )
    db.commit()
    return {"packId": pack_id, "token": share["token"], "expiresAt": share["expiresAt"]}


@router.delete("/packs/{pack_id}/share")
def revoke_pack_share(pack_id: str, http: Request, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _ensure_tables(db)
    org_id = _caller_org(http)
    _pack_row(db, pack_id, org_id)
    _require_org_mutator(db, org_id, current_user)
    db.execute(text("UPDATE governance_evidence_packs SET share_token_hash = NULL, share_expires_at = NULL WHERE id = :id"), {"id": pack_id})
    db.commit()
    return {"packId": pack_id, "shared": False}


@public_router.get("/packs/{pack_id}")
def public_pack(pack_id: str, t: Optional[str] = Query(None, max_length=256), db: Session = Depends(get_db)):
    """Read-only pack for an auditor holding the share token. Unknown pack and wrong token look the same."""
    _ensure_tables(db)
    row = db.execute(text(f"SELECT {_COLUMNS} FROM governance_evidence_packs WHERE id = :id"), {"id": pack_id}).fetchone()
    if not row or not t or not token_matches(t, row[9]):
        raise HTTPException(status_code=404, detail="Pack not found")
    if is_expired(row[10]):
        raise HTTPException(status_code=410, detail="This auditor link has expired")
    return {
        "id": row[0], "title": row[2], "frameworks": json.loads(row[3]), "createdAt": row[8],
        "manifestHash": row[6], "manifest": json.loads(row[5]), "expiresAt": row[10],
    }
