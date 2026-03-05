"""
AI Governance endpoints (Phase 1 MVP)

Provides practical governance primitives:
- Policy management
- Approval workflows and requests
- Evidence collection and linking
- Basic framework/controls discovery for UI contracts
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.connection import get_db


router = APIRouter(tags=["ai-governance"])


FRAMEWORKS: List[Dict[str, Any]] = [
    {
        "id": "eu_ai_act",
        "name": "EU AI Act",
        "description": "European Union AI regulation",
        "controls": ["risk_management", "transparency", "human_oversight", "incident_reporting"],
    },
    {
        "id": "iso_42001",
        "name": "ISO/IEC 42001",
        "description": "AI management system standard",
        "controls": ["governance", "policy", "monitoring", "continuous_improvement"],
    },
    {
        "id": "nist_ai_rmf",
        "name": "NIST AI RMF",
        "description": "NIST AI Risk Management Framework",
        "controls": ["govern", "map", "measure", "manage"],
    },
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_tables(db: Session) -> None:
    """Create governance tables if missing (idempotent)."""
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS governance_policies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                framework TEXT NOT NULL,
                description TEXT,
                rules_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS governance_approval_workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                steps_json TEXT NOT NULL,
                is_active INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS governance_approval_requests (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                requested_by TEXT,
                status TEXT NOT NULL,
                current_step INTEGER NOT NULL,
                decision_notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (workflow_id) REFERENCES governance_approval_workflows(id)
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS governance_evidence (
                id TEXT PRIMARY KEY,
                system_id TEXT NOT NULL,
                evidence_type TEXT NOT NULL,
                content_json TEXT NOT NULL,
                confidence REAL NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS governance_evidence_links (
                id TEXT PRIMARY KEY,
                evidence_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (evidence_id) REFERENCES governance_evidence(id)
            )
            """
        )
    )
    db.commit()


class PolicyCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    framework: str = Field(min_length=1)
    description: str = ""
    rules: List[Dict[str, Any]] = Field(default_factory=list)


class ApprovalWorkflowCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    steps: List[Dict[str, Any]] = Field(default_factory=list)


class ApprovalRequestCreateRequest(BaseModel):
    entity_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    requested_by: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    notes: str = ""


class EvidenceCollectRequest(BaseModel):
    system_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    content: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceLinkRequest(BaseModel):
    evidence_id: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)


@router.get("/status")
async def governance_status(db: Session = Depends(get_db)):
    _ensure_tables(db)
    return {
        "status": "operational",
        "timestamp": _utc_now_iso(),
        "capabilities": ["policies", "approval-workflows", "evidence-linking"],
    }


@router.get("/compliance/frameworks")
async def get_frameworks():
    return FRAMEWORKS


@router.get("/compliance/frameworks/{framework}/controls")
async def get_framework_controls(framework: str):
    found = next((f for f in FRAMEWORKS if f["id"] == framework), None)
    if not found:
        raise HTTPException(status_code=404, detail="Framework not found")
    return {
        "framework": framework,
        "controls": found["controls"],
    }


@router.get("/policies")
async def list_policies(
    framework: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    if framework:
        rows = db.execute(
            text(
                "SELECT id, name, framework, description, rules_json, status, created_at FROM governance_policies "
                "WHERE framework = :framework ORDER BY created_at DESC"
            ),
            {"framework": framework},
        ).fetchall()
    else:
        rows = db.execute(
            text(
                "SELECT id, name, framework, description, rules_json, status, created_at FROM governance_policies "
                "ORDER BY created_at DESC"
            )
        ).fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "framework": row[2],
            "description": row[3] or "",
            "rules": json.loads(row[4]),
            "status": row[5],
            "createdAt": row[6],
        }
        for row in rows
    ]


@router.post("/policies")
async def create_policy(request: PolicyCreateRequest, db: Session = Depends(get_db)):
    _ensure_tables(db)
    policy_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_policies (id, name, framework, description, rules_json, status, created_at, updated_at) "
            "VALUES (:id, :name, :framework, :description, :rules_json, :status, :created_at, :updated_at)"
        ),
        {
            "id": policy_id,
            "name": request.name,
            "framework": request.framework,
            "description": request.description,
            "rules_json": json.dumps(request.rules),
            "status": "draft",
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()

    return {
        "id": policy_id,
        "name": request.name,
        "framework": request.framework,
        "description": request.description,
        "rules": request.rules,
        "status": "draft",
        "createdAt": now,
    }


@router.post("/policies/{policy_id}/submit")
async def submit_policy_for_approval(policy_id: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
    now = _utc_now_iso()
    result = db.execute(
        text(
            "UPDATE governance_policies SET status = :status, updated_at = :updated_at "
            "WHERE id = :id"
        ),
        {"status": "awaiting_approval", "updated_at": now, "id": policy_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.commit()
    return {"id": policy_id, "status": "awaiting_approval", "updatedAt": now}


@router.post("/approval-workflows")
async def create_approval_workflow(
    request: ApprovalWorkflowCreateRequest,
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    workflow_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_approval_workflows (id, name, entity_type, steps_json, is_active, created_at, updated_at) "
            "VALUES (:id, :name, :entity_type, :steps_json, :is_active, :created_at, :updated_at)"
        ),
        {
            "id": workflow_id,
            "name": request.name,
            "entity_type": request.entity_type,
            "steps_json": json.dumps(request.steps),
            "is_active": 1,
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()
    return {
        "id": workflow_id,
        "name": request.name,
        "entity_type": request.entity_type,
        "steps": request.steps,
        "is_active": True,
        "createdAt": now,
    }


@router.get("/approval-workflows")
async def list_approval_workflows(
    entity_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    if entity_type:
        rows = db.execute(
            text(
                "SELECT id, name, entity_type, steps_json, is_active, created_at "
                "FROM governance_approval_workflows WHERE entity_type = :entity_type ORDER BY created_at DESC"
            ),
            {"entity_type": entity_type},
        ).fetchall()
    else:
        rows = db.execute(
            text(
                "SELECT id, name, entity_type, steps_json, is_active, created_at "
                "FROM governance_approval_workflows ORDER BY created_at DESC"
            )
        ).fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "entity_type": row[2],
            "steps": json.loads(row[3]),
            "is_active": bool(row[4]),
            "createdAt": row[5],
        }
        for row in rows
    ]


@router.post("/approval-workflows/{workflow_id}/requests")
async def create_approval_request(
    workflow_id: str,
    request: ApprovalRequestCreateRequest,
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    workflow = db.execute(
        text("SELECT id FROM governance_approval_workflows WHERE id = :id AND is_active = 1"),
        {"id": workflow_id},
    ).fetchone()
    if not workflow:
        raise HTTPException(status_code=404, detail="Active workflow not found")

    request_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_approval_requests "
            "(id, workflow_id, entity_type, entity_id, requested_by, status, current_step, decision_notes, created_at, updated_at) "
            "VALUES (:id, :workflow_id, :entity_type, :entity_id, :requested_by, :status, :current_step, :decision_notes, :created_at, :updated_at)"
        ),
        {
            "id": request_id,
            "workflow_id": workflow_id,
            "entity_type": request.entity_type,
            "entity_id": request.entity_id,
            "requested_by": request.requested_by,
            "status": "pending",
            "current_step": 1,
            "decision_notes": "",
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()
    return {
        "id": request_id,
        "workflow_id": workflow_id,
        "entity_type": request.entity_type,
        "entity_id": request.entity_id,
        "status": "pending",
        "current_step": 1,
        "createdAt": now,
    }


@router.post("/approval-requests/{request_id}/decision")
async def make_approval_decision(
    request_id: str,
    request: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    new_status = "approved" if request.decision == "approved" else "rejected"
    now = _utc_now_iso()
    result = db.execute(
        text(
            "UPDATE governance_approval_requests "
            "SET status = :status, decision_notes = :notes, updated_at = :updated_at "
            "WHERE id = :id"
        ),
        {
            "status": new_status,
            "notes": request.notes,
            "updated_at": now,
            "id": request_id,
        },
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Approval request not found")

    db.commit()
    return {
        "id": request_id,
        "status": new_status,
        "notes": request.notes,
        "updatedAt": now,
    }


@router.post("/evidence/collect")
async def collect_evidence(request: EvidenceCollectRequest, db: Session = Depends(get_db)):
    _ensure_tables(db)
    evidence_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_evidence (id, system_id, evidence_type, content_json, confidence, metadata_json, created_at) "
            "VALUES (:id, :system_id, :evidence_type, :content_json, :confidence, :metadata_json, :created_at)"
        ),
        {
            "id": evidence_id,
            "system_id": request.system_id,
            "evidence_type": request.type,
            "content_json": json.dumps(request.content),
            "confidence": request.confidence,
            "metadata_json": json.dumps(request.metadata),
            "created_at": now,
        },
    )
    db.commit()
    return {
        "id": evidence_id,
        "systemId": request.system_id,
        "type": request.type,
        "content": request.content,
        "confidence": request.confidence,
        "metadata": request.metadata,
        "timestamp": now,
    }


@router.post("/evidence/upload")
async def upload_evidence(request: EvidenceCollectRequest, db: Session = Depends(get_db)):
    # Alias to keep frontend contract compatibility.
    return await collect_evidence(request, db)


@router.post("/evidence/collections")
async def link_evidence_to_entity(request: EvidenceLinkRequest, db: Session = Depends(get_db)):
    _ensure_tables(db)

    exists = db.execute(
        text("SELECT id FROM governance_evidence WHERE id = :id"),
        {"id": request.evidence_id},
    ).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="Evidence not found")

    link_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_evidence_links (id, evidence_id, entity_type, entity_id, created_at) "
            "VALUES (:id, :evidence_id, :entity_type, :entity_id, :created_at)"
        ),
        {
            "id": link_id,
            "evidence_id": request.evidence_id,
            "entity_type": request.entity_type,
            "entity_id": request.entity_id,
            "created_at": now,
        },
    )
    db.commit()

    return {
        "id": link_id,
        "evidence_id": request.evidence_id,
        "entity_type": request.entity_type,
        "entity_id": request.entity_id,
        "createdAt": now,
    }


@router.get("/evidence/{system_id}")
async def list_evidence(system_id: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
    rows = db.execute(
        text(
            "SELECT id, system_id, evidence_type, content_json, confidence, metadata_json, created_at "
            "FROM governance_evidence WHERE system_id = :system_id ORDER BY created_at DESC"
        ),
        {"system_id": system_id},
    ).fetchall()

    return [
        {
            "id": row[0],
            "systemId": row[1],
            "type": row[2],
            "content": json.loads(row[3]),
            "confidence": float(row[4]),
            "metadata": json.loads(row[5]),
            "timestamp": row[6],
        }
        for row in rows
    ]
