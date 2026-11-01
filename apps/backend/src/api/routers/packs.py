"""Agentic packs: catalogue, per-org install, and hash-chained workflow runs."""

import hashlib
import json
import uuid
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.routes.ai_governance import (
    ApprovalDecisionRequest,
    _caller_org,
    _enforce_org_scope,
    _ensure_tables,
    _utc_now_iso,
    make_approval_decision,
)
from api.routes.pack_catalogue import PACKS, WORKFLOWS, Workflow
from config.auth import TokenData, UserRole, require_role
from database.connection import get_db

router = APIRouter(dependencies=[Depends(_enforce_org_scope)])

GENESIS_HASH = "0" * 64
RUN_STATUSES = ("queued", "running", "waiting", "blocked", "done", "failed")

# ponytail: the chain is tamper-evident only. Anyone with write access to the
# database can rewrite every row and recompute every hash. Anchor the head hash
# outside the database (signed export, external log) before relying on it as
# proof.


class StartRunBody(BaseModel):
    system_id: Optional[str] = None


class EventBody(BaseModel):
    kind: Literal[
        "step.started",
        "step.completed",
        "finding.recorded",
        "gate.opened",
        "evidence.sealed",
        "run.completed",
        "run.failed",
    ]
    step_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class DecisionBody(BaseModel):
    decision: Literal["approve", "reject"]
    notes: str = ""


def _user_id(request: Request) -> Optional[str]:
    user = getattr(request.state, "user", None)
    return getattr(user, "user_id", None)


def _pack_json(pack_id: str, installed: bool) -> dict:
    pack = PACKS[pack_id]
    return {
        "id": pack.id,
        "name": pack.name,
        "version": pack.version,
        "description": pack.description,
        "installed": installed,
        "hasJourney": pack.journey is not None,
        "workflowIds": [w.id for w in WORKFLOWS.values() if w.pack_id == pack.id],
    }


def _is_installed(db: Session, org_id: str, pack_id: str) -> bool:
    return (
        db.execute(
            text("SELECT 1 FROM pack_installs WHERE org_id = :org_id AND pack_id = :pack_id"),
            {"org_id": org_id, "pack_id": pack_id},
        ).fetchone()
        is not None
    )


def _summary(run) -> dict:
    return {
        "id": run["id"],
        "workflowId": run["workflow_id"],
        "workflowName": WORKFLOWS[run["workflow_id"]].name,
        "status": run["status"],
        "currentStep": run["current_step"],
        "createdAt": run["created_at"],
        "updatedAt": run["updated_at"],
    }


def _latest_runs(db: Session, org_id: str, workflow_ids: List[str]) -> Dict[str, Any]:
    rows = (
        db.execute(
            text("SELECT * FROM workflow_runs WHERE org_id = :org_id ORDER BY created_at DESC"),
            {"org_id": org_id},
        )
        .mappings()
        .all()
    )
    latest: Dict[str, Any] = {}
    for row in rows:
        if row["workflow_id"] in workflow_ids:
            latest.setdefault(row["workflow_id"], row)
    return latest


# --- hash chain ------------------------------------------------------------


def _canonical(run_id: str, seq: int, kind: str, step_id: Optional[str], payload: dict, created_at: str, prev_hash: str) -> str:
    return json.dumps(
        {
            "run_id": run_id,
            "seq": seq,
            "kind": kind,
            "step_id": step_id,
            "payload": payload,
            "created_at": created_at,
            "prev_hash": prev_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _append(db: Session, run_id: str, kind: str, step_id: Optional[str], payload: dict) -> None:
    """Add the next event to a run's chain in the caller's transaction. Caller commits."""
    last = db.execute(
        text("SELECT seq, hash FROM workflow_run_events WHERE run_id = :id ORDER BY seq DESC LIMIT 1"),
        {"id": run_id},
    ).fetchone()
    seq = (last[0] if last else 0) + 1
    prev_hash = last[1] if last else GENESIS_HASH
    created_at = _utc_now_iso()
    canonical = _canonical(run_id, seq, kind, step_id, payload, created_at, prev_hash)
    try:
        db.execute(
            text(
                "INSERT INTO workflow_run_events "
                "(id, run_id, seq, kind, step_id, payload_json, canonical_json, prev_hash, hash, created_at) "
                "VALUES (:id, :run_id, :seq, :kind, :step_id, :payload_json, :canonical_json, :prev_hash, :hash, :created_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "seq": seq,
                "kind": kind,
                "step_id": step_id,
                "payload_json": json.dumps(payload, sort_keys=True),
                "canonical_json": canonical,
                "prev_hash": prev_hash,
                "hash": hashlib.sha256(canonical.encode()).hexdigest(),
                "created_at": created_at,
            },
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Run changed concurrently, retry")


def _verify_chain(events) -> bool:
    prev = GENESIS_HASH
    for index, e in enumerate(events, start=1):
        rebuilt = _canonical(e["run_id"], e["seq"], e["kind"], e["step_id"], json.loads(e["payload_json"]), e["created_at"], e["prev_hash"])
        if (
            e["seq"] != index
            or e["prev_hash"] != prev
            or rebuilt != e["canonical_json"]
            or hashlib.sha256(rebuilt.encode()).hexdigest() != e["hash"]
        ):
            return False
        prev = e["hash"]
    return True


def _run_json(db: Session, run_id: str) -> dict:
    run = db.execute(text("SELECT * FROM workflow_runs WHERE id = :id"), {"id": run_id}).mappings().fetchone()
    events = (
        db.execute(text("SELECT * FROM workflow_run_events WHERE run_id = :id ORDER BY seq"), {"id": run_id})
        .mappings()
        .all()
    )
    approval = None
    if run["approval_request_id"]:
        row = db.execute(
            text("SELECT status, decision_notes FROM governance_approval_requests WHERE id = :id"),
            {"id": run["approval_request_id"]},
        ).fetchone()
        if row:
            approval = {"status": row[0], "decisionNotes": row[1]}
    return {
        **_summary(run),
        "systemId": run["ai_system_id"],
        "approvalRequestId": run["approval_request_id"],
        "approval": approval,
        "finishedAt": run["finished_at"],
        "events": [
            {
                "seq": e["seq"],
                "kind": e["kind"],
                "stepId": e["step_id"],
                "payload": json.loads(e["payload_json"]),
                "prevHash": e["prev_hash"],
                "hash": e["hash"],
                "createdAt": e["created_at"],
            }
            for e in events
        ],
        "chainValid": _verify_chain(events),
    }


def _run_or_404(db: Session, request: Request, run_id: str):
    run = (
        db.execute(
            text("SELECT * FROM workflow_runs WHERE id = :id AND org_id = :org_id"),
            {"id": run_id, "org_id": _caller_org(request)},
        )
        .mappings()
        .fetchone()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


# --- catalogue and install -------------------------------------------------


@router.get("")
async def list_packs(request: Request, db: Session = Depends(get_db)):
    _ensure_tables(db)
    rows = db.execute(text("SELECT pack_id FROM pack_installs WHERE org_id = :org_id"), {"org_id": _caller_org(request)})
    installed = {r[0] for r in rows}
    return [_pack_json(pid, pid in installed) for pid in PACKS]


@router.post("/{pack_id}/install")
async def install_pack(pack_id: str, request: Request, db: Session = Depends(get_db)):
    if pack_id not in PACKS:
        raise HTTPException(status_code=404, detail="Pack not found")
    _ensure_tables(db)
    org_id = _caller_org(request)
    if not _is_installed(db, org_id, pack_id):
        try:
            db.execute(
                text(
                    "INSERT INTO pack_installs (id, org_id, pack_id, installed_by, created_at) "
                    "VALUES (:id, :org_id, :pack_id, :installed_by, :created_at)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "org_id": org_id,
                    "pack_id": pack_id,
                    "installed_by": _user_id(request),
                    "created_at": _utc_now_iso(),
                },
            )
            db.commit()
        except IntegrityError:
            db.rollback()  # a concurrent install won; same end state
    return _pack_json(pack_id, True)


@router.delete("/{pack_id}/install")
async def uninstall_pack(pack_id: str, request: Request, db: Session = Depends(get_db)):
    if pack_id not in PACKS:
        raise HTTPException(status_code=404, detail="Pack not found")
    _ensure_tables(db)
    db.execute(
        text("DELETE FROM pack_installs WHERE org_id = :org_id AND pack_id = :pack_id"),
        {"org_id": _caller_org(request), "pack_id": pack_id},
    )
    db.commit()
    return _pack_json(pack_id, False)


@router.get("/journeys/{pack_id}")
async def get_journey(pack_id: str, request: Request, db: Session = Depends(get_db)):
    pack = PACKS.get(pack_id)
    if not pack or pack.journey is None:
        raise HTTPException(status_code=404, detail="Journey not found")
    _ensure_tables(db)
    org_id = _caller_org(request)
    workflow_ids = [wid for c in pack.journey for wid in c.workflow_ids]
    latest = _latest_runs(db, org_id, workflow_ids)
    return {
        "packId": pack.id,
        "name": pack.name,
        "installed": _is_installed(db, org_id, pack.id),
        "clauses": [
            {
                "number": c.number,
                "name": c.name,
                "workflows": [
                    {
                        "id": wid,
                        "name": WORKFLOWS[wid].name,
                        "stage": WORKFLOWS[wid].stage,
                        "latestRun": _summary(latest[wid]) if wid in latest else None,
                    }
                    for wid in c.workflow_ids
                ],
            }
            for c in pack.journey
        ],
    }


def _workflow_or_404(workflow_id: str) -> Workflow:
    wf = WORKFLOWS.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str, request: Request, db: Session = Depends(get_db)):
    wf = _workflow_or_404(workflow_id)
    _ensure_tables(db)
    org_id = _caller_org(request)
    latest = _latest_runs(db, org_id, [wf.id]).get(wf.id)
    return {
        "id": wf.id,
        "name": wf.name,
        "version": wf.version,
        "stage": wf.stage,
        "description": wf.description,
        "packId": wf.pack_id,
        "installed": _is_installed(db, org_id, wf.pack_id),
        "steps": [
            {
                "id": s.id,
                "kind": s.kind,
                "title": s.title,
                "detail": s.detail,
                "systems": s.systems,
                "next": [{"to": n.to, "label": n.label} for n in s.next],
            }
            for s in wf.steps
        ],
        "controls": [c.model_dump() for c in wf.controls],
        "latestRun": _summary(latest) if latest else None,
    }


# --- runs ------------------------------------------------------------------


@router.post("/workflows/{workflow_id}/runs")
async def start_run(
    workflow_id: str,
    request: Request,
    body: StartRunBody = StartRunBody(),
    db: Session = Depends(get_db),
):
    wf = _workflow_or_404(workflow_id)
    _ensure_tables(db)
    org_id = _caller_org(request)
    if not _is_installed(db, org_id, wf.pack_id):
        raise HTTPException(status_code=409, detail="Install the pack before starting a run")
    now = _utc_now_iso()
    run_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO workflow_runs "
            "(id, org_id, workflow_id, workflow_version, ai_system_id, status, started_by, created_at, updated_at) "
            "VALUES (:id, :org_id, :workflow_id, :workflow_version, :ai_system_id, 'queued', :started_by, :now, :now)"
        ),
        {
            "id": run_id,
            "org_id": org_id,
            "workflow_id": wf.id,
            "workflow_version": wf.version,
            "ai_system_id": body.system_id,
            "started_by": _user_id(request),
            "now": now,
        },
    )
    _append(db, run_id, "run.created", None, {"workflowId": wf.id, "workflowVersion": wf.version})
    db.commit()
    return _run_json(db, run_id)


@router.get("/runs")
async def list_runs(
    request: Request,
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    if status is not None and status not in RUN_STATUSES:
        raise HTTPException(status_code=422, detail="Unknown status")
    _ensure_tables(db)
    rows = (
        db.execute(
            text(
                "SELECT * FROM workflow_runs WHERE org_id = :org_id AND (:status IS NULL OR status = :status) "
                "ORDER BY created_at DESC"
            ),
            {"org_id": _caller_org(request), "status": status},
        )
        .mappings()
        .all()
    )
    return [_summary(r) for r in rows]


@router.get("/runs/{run_id}")
async def get_run(run_id: str, request: Request, db: Session = Depends(get_db)):
    _ensure_tables(db)
    _run_or_404(db, request, run_id)
    return _run_json(db, run_id)


def _open_gate(db: Session, run, requested_by: Optional[str]) -> str:
    """Create the governance approval request for a run, using the shared workflow_run approval workflow."""
    workflow_row = db.execute(
        text(
            "SELECT id FROM governance_approval_workflows "
            "WHERE entity_type = 'workflow_run' AND is_active = 1 LIMIT 1"
        )
    ).fetchone()
    now = _utc_now_iso()
    if workflow_row:
        approval_workflow_id = workflow_row[0]
    else:
        approval_workflow_id = str(uuid.uuid4())
        db.execute(
            text(
                "INSERT INTO governance_approval_workflows "
                "(id, name, entity_type, steps_json, is_active, created_by, created_at, updated_at) "
                "VALUES (:id, :name, :entity_type, :steps_json, :is_active, :created_by, :created_at, :updated_at)"
            ),
            {
                "id": approval_workflow_id,
                "name": "Agentic Workflow Approval",
                "entity_type": "workflow_run",
                "steps_json": json.dumps([{"step": 1, "name": "Owner Approval", "approver_role": "governance_lead"}]),
                "is_active": 1,
                "created_by": "system",
                "created_at": now,
                "updated_at": now,
            },
        )
    request_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_approval_requests "
            "(id, workflow_id, entity_type, entity_id, ai_system_id, requested_by, "
            "status, current_step, created_at, updated_at) "
            "VALUES (:id, :workflow_id, :entity_type, :entity_id, :ai_system_id, "
            ":requested_by, :status, :current_step, :created_at, :updated_at)"
        ),
        {
            "id": request_id,
            "workflow_id": approval_workflow_id,
            "entity_type": "workflow_run",
            "entity_id": run["id"],
            "ai_system_id": run["ai_system_id"],
            "requested_by": requested_by,
            "status": "pending",
            "current_step": 0,
            "created_at": now,
            "updated_at": now,
        },
    )
    return request_id


@router.post("/runs/{run_id}/events")
async def append_event(
    run_id: str,
    body: EventBody,
    request: Request,
    db: Session = Depends(get_db),
    _admin: TokenData = Depends(require_role([UserRole.ADMIN])),
):
    """Hook for a future agent executor. Status, current step and finish time are derived here, never client-set."""
    _ensure_tables(db)
    run = _run_or_404(db, request, run_id)
    steps = {s.id: s for s in WORKFLOWS[run["workflow_id"]].steps}
    if run["status"] in ("done", "failed"):
        raise HTTPException(status_code=409, detail="Run is finished")
    # A waiting or blocked run must not resume by appending events; only an approval decision moves it.
    if run["status"] in ("waiting", "blocked") and body.kind != "run.failed":
        raise HTTPException(status_code=409, detail=f"Run is {run['status']}")
    if body.kind in ("step.started", "step.completed", "gate.opened") and not body.step_id:
        raise HTTPException(status_code=422, detail="step_id is required for this event kind")
    if body.step_id and body.step_id not in steps:
        raise HTTPException(status_code=422, detail="Unknown step for this workflow")
    if body.kind == "gate.opened" and steps[body.step_id].kind != "ask":
        raise HTTPException(status_code=422, detail="A gate can only open on an ask step")

    now = _utc_now_iso()
    payload = dict(body.payload)
    status, current_step, finished_at = run["status"], run["current_step"], run["finished_at"]
    approval_request_id = run["approval_request_id"]
    if body.kind == "step.started":
        status, current_step = "running", body.step_id
    elif body.kind == "gate.opened":
        approval_request_id = _open_gate(db, run, _user_id(request))
        payload["approvalRequestId"] = approval_request_id
        status, current_step = "waiting", body.step_id
    elif body.kind == "run.completed":
        status, finished_at = "done", now
    elif body.kind == "run.failed":
        status, finished_at = "failed", now
    db.execute(
        text(
            "UPDATE workflow_runs SET status = :status, current_step = :current_step, finished_at = :finished_at, "
            "approval_request_id = :approval_request_id, updated_at = :now WHERE id = :id"
        ),
        {
            "status": status,
            "current_step": current_step,
            "finished_at": finished_at,
            "approval_request_id": approval_request_id,
            "now": now,
            "id": run_id,
        },
    )
    _append(db, run_id, body.kind, body.step_id, payload)
    db.commit()
    return _run_json(db, run_id)


@router.post("/runs/{run_id}/decision")
async def decide_run(run_id: str, body: DecisionBody, request: Request, db: Session = Depends(get_db)):
    _ensure_tables(db)
    run = _run_or_404(db, request, run_id)
    if run["status"] != "waiting" or not run["approval_request_id"]:
        raise HTTPException(status_code=409, detail="Run is not waiting for a decision")
    approved = body.decision == "approve"
    # Claim the run first: a concurrent second decision updates zero rows and gets 409.
    claimed = db.execute(
        text("UPDATE workflow_runs SET status = :status, updated_at = :now WHERE id = :id AND status = 'waiting'"),
        {"status": "running" if approved else "blocked", "now": _utc_now_iso(), "id": run_id},
    ).rowcount
    if not claimed:
        db.rollback()
        raise HTTPException(status_code=409, detail="Run is not waiting for a decision")
    _append(db, run_id, "gate.decided", run["current_step"], {"decision": body.decision, "notes": body.notes})
    try:
        # Commits the run claim, the event and the approval decision together.
        await make_approval_decision(
            run["approval_request_id"],
            ApprovalDecisionRequest(
                decision="approved" if approved else "rejected",
                notes=body.notes,
                decided_by=_user_id(request),
            ),
            db,
        )
    except HTTPException:
        db.rollback()
        raise
    return _run_json(db, run_id)
