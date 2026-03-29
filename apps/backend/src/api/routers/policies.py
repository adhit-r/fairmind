"""
Policy Manager endpoints.

Provides full CRUD for governance policies with:
- Framework/status filtering
- Status transitions: draft -> review -> approved (with archived support)
- Version history tracking via governance_policy_versions table
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

router = APIRouter(prefix="/api/policies", tags=["policies"])


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

    # Add new columns to governance_policies if they don't exist yet.
    for col_def in [
        ("version", "INTEGER NOT NULL DEFAULT 1"),
        ("owner", "TEXT"),
        ("reviewer", "TEXT"),
        ("approver", "TEXT"),
        ("approved_at", "TEXT"),
    ]:
        try:
            db.execute(text(f"ALTER TABLE governance_policies ADD COLUMN {col_def[0]} {col_def[1]}"))
        except Exception:
            pass  # Column already exists.

    # Create the policy_versions table if not yet present.
    db.execute(
        text(
            "CREATE TABLE IF NOT EXISTS governance_policy_versions ("
            "  id TEXT PRIMARY KEY,"
            "  policy_id TEXT NOT NULL,"
            "  version INTEGER NOT NULL,"
            "  name TEXT NOT NULL,"
            "  framework TEXT NOT NULL,"
            "  description TEXT,"
            "  rules_json TEXT NOT NULL DEFAULT '[]',"
            "  status TEXT NOT NULL,"
            "  changed_by TEXT,"
            "  change_summary TEXT,"
            "  created_at TEXT NOT NULL,"
            "  FOREIGN KEY (policy_id) REFERENCES governance_policies(id)"
            ")"
        )
    )
    db.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_gpv_policy_id "
            "ON governance_policy_versions(policy_id)"
        )
    )
    db.commit()
    _tables_ready = True


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Valid status transitions.
VALID_TRANSITIONS: Dict[str, List[str]] = {
    "draft": ["review", "archived"],
    "review": ["approved", "draft", "archived"],
    "approved": ["archived"],
    "archived": ["draft"],
}


def _serialize_policy(row: Any) -> Dict[str, Any]:
    return {
        "id": row[0],
        "name": row[1],
        "framework": row[2],
        "description": row[3] or "",
        "rules": json.loads(row[4]) if row[4] else [],
        "status": row[5],
        "version": row[6],
        "owner": row[7],
        "reviewer": row[8],
        "approver": row[9],
        "approved_at": row[10],
        "created_at": row[11],
        "updated_at": row[12],
    }


POLICY_SELECT = (
    "id, name, framework, description, rules_json, status, "
    "version, owner, reviewer, approver, approved_at, created_at, updated_at"
)


def _snapshot_version(
    db: Session,
    policy_id: str,
    version: int,
    name: str,
    framework: str,
    description: str,
    rules_json: str,
    status: str,
    changed_by: Optional[str],
    change_summary: Optional[str],
) -> None:
    """Insert a snapshot row into governance_policy_versions."""
    db.execute(
        text(
            "INSERT INTO governance_policy_versions "
            "(id, policy_id, version, name, framework, description, rules_json, status, changed_by, change_summary, created_at) "
            "VALUES (:id, :policy_id, :version, :name, :framework, :description, :rules_json, :status, :changed_by, :change_summary, :created_at)"
        ),
        {
            "id": str(uuid.uuid4()),
            "policy_id": policy_id,
            "version": version,
            "name": name,
            "framework": framework,
            "description": description or "",
            "rules_json": rules_json,
            "status": status,
            "changed_by": changed_by,
            "change_summary": change_summary,
            "created_at": _utc_now_iso(),
        },
    )


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PolicyCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    framework: str = Field(min_length=1)
    description: str = ""
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    owner: Optional[str] = None
    reviewer: Optional[str] = None
    approver: Optional[str] = None


class PolicyUpdateRequest(BaseModel):
    name: Optional[str] = None
    framework: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = Field(
        default=None,
        pattern="^(draft|review|approved|archived)$",
    )
    owner: Optional[str] = None
    reviewer: Optional[str] = None
    approver: Optional[str] = None
    changed_by: Optional[str] = None
    change_summary: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("")
async def create_policy(
    request: PolicyCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new policy in draft status."""
    _ensure_tables(db)
    policy_id = str(uuid.uuid4())
    now = _utc_now_iso()
    rules_json = json.dumps(request.rules)

    db.execute(
        text(
            "INSERT INTO governance_policies "
            "(id, name, framework, description, rules_json, status, version, owner, reviewer, approver, created_at, updated_at) "
            "VALUES (:id, :name, :framework, :description, :rules_json, 'draft', 1, :owner, :reviewer, :approver, :created_at, :updated_at)"
        ),
        {
            "id": policy_id,
            "name": request.name,
            "framework": request.framework,
            "description": request.description,
            "rules_json": rules_json,
            "owner": request.owner,
            "reviewer": request.reviewer,
            "approver": request.approver,
            "created_at": now,
            "updated_at": now,
        },
    )

    # Snapshot v1
    _snapshot_version(
        db,
        policy_id=policy_id,
        version=1,
        name=request.name,
        framework=request.framework,
        description=request.description,
        rules_json=rules_json,
        status="draft",
        changed_by=request.owner,
        change_summary="Policy created",
    )
    db.commit()

    return {
        "id": policy_id,
        "name": request.name,
        "framework": request.framework,
        "description": request.description,
        "rules": request.rules,
        "status": "draft",
        "version": 1,
        "owner": request.owner,
        "reviewer": request.reviewer,
        "approver": request.approver,
        "approved_at": None,
        "created_at": now,
        "updated_at": now,
    }


@router.get("")
async def list_policies(
    framework: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """List policies with optional framework and status filters."""
    _ensure_tables(db)

    filters: List[str] = []
    params: Dict[str, Any] = {}

    if framework:
        filters.append("framework = :framework")
        params["framework"] = framework
    if status:
        filters.append("status = :status")
        params["status"] = status

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows = db.execute(
        text(f"SELECT {POLICY_SELECT} FROM governance_policies {where} ORDER BY created_at DESC"),
        params,
    ).fetchall()

    return [_serialize_policy(row) for row in rows]


@router.get("/{policy_id}")
async def get_policy(policy_id: str, db: Session = Depends(get_db)):
    """Get a single policy by ID."""
    _ensure_tables(db)
    row = db.execute(
        text(f"SELECT {POLICY_SELECT} FROM governance_policies WHERE id = :id"),
        {"id": policy_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Policy not found")
    return _serialize_policy(row)


@router.patch("/{policy_id}")
async def update_policy(
    policy_id: str,
    request: PolicyUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Update a policy.

    Status transitions are enforced:
      draft -> review | archived
      review -> approved | draft | archived
      approved -> archived
      archived -> draft
    """
    _ensure_tables(db)

    existing = db.execute(
        text(f"SELECT {POLICY_SELECT} FROM governance_policies WHERE id = :id"),
        {"id": policy_id},
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Policy not found")

    current_status = existing[5]
    current_version = existing[6] or 1

    # Validate status transition if a status change is requested.
    new_status = request.status
    if new_status and new_status != current_status:
        allowed = VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot transition from '{current_status}' to '{new_status}'. Allowed: {allowed}",
            )

    # Build dynamic SET clause.
    updates: Dict[str, Any] = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.framework is not None:
        updates["framework"] = request.framework
    if request.description is not None:
        updates["description"] = request.description
    if request.rules is not None:
        updates["rules_json"] = json.dumps(request.rules)
    if request.owner is not None:
        updates["owner"] = request.owner
    if request.reviewer is not None:
        updates["reviewer"] = request.reviewer
    if request.approver is not None:
        updates["approver"] = request.approver

    bump_version = False
    if new_status and new_status != current_status:
        updates["status"] = new_status
        bump_version = True
        if new_status == "approved":
            updates["approved_at"] = _utc_now_iso()
    elif updates:
        # Content change without status change also bumps version.
        bump_version = True

    if not updates:
        return _serialize_policy(existing)

    now = _utc_now_iso()
    new_version = current_version + 1 if bump_version else current_version
    updates["updated_at"] = now
    if bump_version:
        updates["version"] = new_version

    set_parts = [f"{key} = :{key}" for key in updates]
    params = {**updates, "id": policy_id}
    db.execute(
        text(f"UPDATE governance_policies SET {', '.join(set_parts)} WHERE id = :id"),
        params,
    )

    # Snapshot version history.
    if bump_version:
        _snapshot_version(
            db,
            policy_id=policy_id,
            version=new_version,
            name=updates.get("name", existing[1]),
            framework=updates.get("framework", existing[2]),
            description=updates.get("description", existing[3] or ""),
            rules_json=updates.get("rules_json", existing[4] or "[]"),
            status=updates.get("status", current_status),
            changed_by=request.changed_by,
            change_summary=request.change_summary,
        )

    db.commit()

    # Re-fetch to return accurate state.
    return await get_policy(policy_id, db)


@router.get("/{policy_id}/versions")
async def list_policy_versions(policy_id: str, db: Session = Depends(get_db)):
    """Return the version history for a policy."""
    _ensure_tables(db)

    # Verify the policy exists.
    exists = db.execute(
        text("SELECT id FROM governance_policies WHERE id = :id"),
        {"id": policy_id},
    ).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="Policy not found")

    rows = db.execute(
        text(
            "SELECT id, policy_id, version, name, framework, description, rules_json, "
            "status, changed_by, change_summary, created_at "
            "FROM governance_policy_versions WHERE policy_id = :policy_id "
            "ORDER BY version DESC"
        ),
        {"policy_id": policy_id},
    ).fetchall()

    return [
        {
            "id": row[0],
            "policy_id": row[1],
            "version": row[2],
            "name": row[3],
            "framework": row[4],
            "description": row[5] or "",
            "rules": json.loads(row[6]) if row[6] else [],
            "status": row[7],
            "changed_by": row[8],
            "change_summary": row[9],
            "created_at": row[10],
        }
        for row in rows
    ]
