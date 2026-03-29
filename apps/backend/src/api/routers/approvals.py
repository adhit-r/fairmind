"""
Approval Workflow endpoints.

Provides approval request lifecycle:
- Create requests linked to an AI system and optionally a policy
- List/filter by status and AI system
- Approve / reject with comments
- Critical remediation gate: blocks approval while any critical remediation task is open
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

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_tables_ready = False


def _ensure_tables(db: Session) -> None:
    global _tables_ready
    if _tables_ready:
        return
    import database.governance_models  # noqa: F401
    from database.connection import Base, db_manager

    Base.metadata.create_all(bind=db_manager.engine)

    # Ensure all required columns exist on approval_requests (may be missing on older DBs).
    for col_def in [
        ("ai_system_id", "TEXT"),
        ("decision", "TEXT"),
        ("decided_by", "TEXT"),
        ("decided_at", "TEXT"),
    ]:
        try:
            db.execute(text(
                f"ALTER TABLE governance_approval_requests ADD COLUMN {col_def[0]} {col_def[1]}"
            ))
        except Exception:
            pass  # Column already exists.
    db.commit()
    _tables_ready = True


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize_request(row: Any) -> Dict[str, Any]:
    return {
        "id": row[0],
        "workflow_id": row[1],
        "entity_type": row[2],
        "entity_id": row[3],
        "ai_system_id": row[4],
        "requested_by": row[5],
        "status": row[6],
        "current_step": row[7],
        "decision": row[8],
        "decision_notes": row[9] or "",
        "decided_by": row[10],
        "decided_at": row[11],
        "created_at": row[12],
        "updated_at": row[13],
    }


REQUEST_SELECT = (
    "id, workflow_id, entity_type, entity_id, ai_system_id, requested_by, "
    "status, current_step, decision, decision_notes, decided_by, decided_at, "
    "created_at, updated_at"
)


def _fetch_decisions(db: Session, request_id: str) -> List[Dict[str, Any]]:
    rows = db.execute(
        text(
            "SELECT id, request_id, decision, notes, decided_by, created_at "
            "FROM governance_approval_decisions WHERE request_id = :request_id "
            "ORDER BY created_at ASC"
        ),
        {"request_id": request_id},
    ).fetchall()
    return [
        {
            "id": row[0],
            "request_id": row[1],
            "decision": row[2],
            "notes": row[3] or "",
            "decided_by": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]


def _check_critical_remediation_gate(db: Session, ai_system_id: str) -> Optional[str]:
    """
    Return a blocker message if any critical remediation task is open
    for the given AI system.  Returns None when the gate passes.
    """
    row = db.execute(
        text(
            "SELECT COUNT(*) FROM governance_remediation_tasks "
            "WHERE system_id = :system_id AND priority = 'critical' "
            "AND status NOT IN ('resolved', 'closed')"
        ),
        {"system_id": ai_system_id},
    ).fetchone()
    count = row[0] if row else 0
    if count > 0:
        return (
            f"Cannot approve: {count} critical remediation task(s) remain open "
            f"for AI system {ai_system_id}. Resolve them before approving."
        )
    return None


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ApprovalRequestCreate(BaseModel):
    ai_system_id: str = Field(min_length=1)
    policy_id: Optional[str] = None
    requested_by: Optional[str] = None
    workflow_id: Optional[str] = None


class ApprovalActionRequest(BaseModel):
    comment: str = ""
    decided_by: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/requests")
async def create_approval_request(
    request: ApprovalRequestCreate,
    db: Session = Depends(get_db),
):
    """
    Create an approval request linked to an AI system and optionally a policy.

    If workflow_id is omitted the most recent active workflow for entity_type
    'ai_system' is used.  If none exists, one is auto-created.
    """
    _ensure_tables(db)

    # Verify the AI system exists.
    system = db.execute(
        text("SELECT id, name FROM governance_ai_systems WHERE id = :id"),
        {"id": request.ai_system_id},
    ).fetchone()
    if not system:
        raise HTTPException(status_code=404, detail="AI system not found")

    # Resolve workflow.
    workflow_id = request.workflow_id
    if workflow_id:
        wf = db.execute(
            text("SELECT id FROM governance_approval_workflows WHERE id = :id AND is_active = 1"),
            {"id": workflow_id},
        ).fetchone()
        if not wf:
            raise HTTPException(status_code=404, detail="Active workflow not found")
    else:
        wf = db.execute(
            text(
                "SELECT id FROM governance_approval_workflows "
                "WHERE entity_type = 'ai_system' AND is_active = 1 "
                "ORDER BY created_at DESC LIMIT 1"
            ),
        ).fetchone()
        if wf:
            workflow_id = wf[0]
        else:
            # Auto-create a default workflow.
            workflow_id = str(uuid.uuid4())
            now = _utc_now_iso()
            db.execute(
                text(
                    "INSERT INTO governance_approval_workflows "
                    "(id, name, entity_type, steps_json, is_active, created_at, updated_at) "
                    "VALUES (:id, :name, :entity_type, :steps_json, 1, :created_at, :updated_at)"
                ),
                {
                    "id": workflow_id,
                    "name": "AI System Approval",
                    "entity_type": "ai_system",
                    "steps_json": json.dumps([
                        {"step": 1, "role": "reviewer", "action": "review"},
                        {"step": 2, "role": "approver", "action": "approve"},
                    ]),
                    "created_at": now,
                    "updated_at": now,
                },
            )

    entity_type = "policy" if request.policy_id else "ai_system"
    entity_id = request.policy_id or request.ai_system_id

    request_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_approval_requests "
            "(id, workflow_id, entity_type, entity_id, ai_system_id, requested_by, "
            " status, current_step, created_at, updated_at) "
            "VALUES (:id, :workflow_id, :entity_type, :entity_id, :ai_system_id, "
            " :requested_by, 'pending', 1, :created_at, :updated_at)"
        ),
        {
            "id": request_id,
            "workflow_id": workflow_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "ai_system_id": request.ai_system_id,
            "requested_by": request.requested_by,
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()

    return {
        "id": request_id,
        "workflow_id": workflow_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "ai_system_id": request.ai_system_id,
        "status": "pending",
        "current_step": 1,
        "created_at": now,
    }


@router.get("/requests")
async def list_approval_requests(
    status: Optional[str] = Query(default=None),
    ai_system_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """List approval requests with optional status and ai_system filters."""
    _ensure_tables(db)

    filters: List[str] = []
    params: Dict[str, Any] = {}

    if status:
        filters.append("status = :status")
        params["status"] = status
    if ai_system_id:
        filters.append("ai_system_id = :ai_system_id")
        params["ai_system_id"] = ai_system_id

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows = db.execute(
        text(
            f"SELECT {REQUEST_SELECT} FROM governance_approval_requests "
            f"{where} ORDER BY created_at DESC"
        ),
        params,
    ).fetchall()

    return [_serialize_request(row) for row in rows]


@router.get("/requests/{request_id}")
async def get_approval_request(request_id: str, db: Session = Depends(get_db)):
    """Get an approval request with its decision history."""
    _ensure_tables(db)
    row = db.execute(
        text(f"SELECT {REQUEST_SELECT} FROM governance_approval_requests WHERE id = :id"),
        {"id": request_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Approval request not found")

    result = _serialize_request(row)
    result["decisions"] = _fetch_decisions(db, request_id)
    return result


@router.post("/requests/{request_id}/approve")
async def approve_request(
    request_id: str,
    body: ApprovalActionRequest,
    db: Session = Depends(get_db),
):
    """
    Approve an approval request.

    Gate: blocks if the linked AI system has any open critical remediation tasks.
    """
    _ensure_tables(db)

    row = db.execute(
        text(f"SELECT {REQUEST_SELECT} FROM governance_approval_requests WHERE id = :id"),
        {"id": request_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Approval request not found")

    current_status = row[6]
    if current_status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Request is already '{current_status}', only pending requests can be approved",
        )

    ai_system_id = row[4]
    if ai_system_id:
        blocker = _check_critical_remediation_gate(db, ai_system_id)
        if blocker:
            raise HTTPException(status_code=409, detail=blocker)

    now = _utc_now_iso()
    db.execute(
        text(
            "UPDATE governance_approval_requests "
            "SET status = 'approved', decision = 'approved', decision_notes = :notes, "
            "    decided_by = :decided_by, decided_at = :now, updated_at = :now "
            "WHERE id = :id"
        ),
        {
            "id": request_id,
            "notes": body.comment,
            "decided_by": body.decided_by,
            "now": now,
        },
    )
    db.execute(
        text(
            "INSERT INTO governance_approval_decisions "
            "(id, request_id, decision, notes, decided_by, created_at) "
            "VALUES (:id, :request_id, 'approved', :notes, :decided_by, :created_at)"
        ),
        {
            "id": str(uuid.uuid4()),
            "request_id": request_id,
            "notes": body.comment,
            "decided_by": body.decided_by,
            "created_at": now,
        },
    )
    db.commit()

    return {
        "id": request_id,
        "status": "approved",
        "decision": "approved",
        "comment": body.comment,
        "decided_by": body.decided_by,
        "decided_at": now,
    }


@router.post("/requests/{request_id}/reject")
async def reject_request(
    request_id: str,
    body: ApprovalActionRequest,
    db: Session = Depends(get_db),
):
    """Reject an approval request with a reason."""
    _ensure_tables(db)

    row = db.execute(
        text("SELECT status FROM governance_approval_requests WHERE id = :id"),
        {"id": request_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if row[0] != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Request is already '{row[0]}', only pending requests can be rejected",
        )

    now = _utc_now_iso()
    db.execute(
        text(
            "UPDATE governance_approval_requests "
            "SET status = 'rejected', decision = 'rejected', decision_notes = :notes, "
            "    decided_by = :decided_by, decided_at = :now, updated_at = :now "
            "WHERE id = :id"
        ),
        {
            "id": request_id,
            "notes": body.comment,
            "decided_by": body.decided_by,
            "now": now,
        },
    )
    db.execute(
        text(
            "INSERT INTO governance_approval_decisions "
            "(id, request_id, decision, notes, decided_by, created_at) "
            "VALUES (:id, :request_id, 'rejected', :notes, :decided_by, :created_at)"
        ),
        {
            "id": str(uuid.uuid4()),
            "request_id": request_id,
            "notes": body.comment,
            "decided_by": body.decided_by,
            "created_at": now,
        },
    )
    db.commit()

    return {
        "id": request_id,
        "status": "rejected",
        "decision": "rejected",
        "comment": body.comment,
        "decided_by": body.decided_by,
        "decided_at": now,
    }
