"""Agentic packs: catalogue, per-org install, and hash-chained workflow runs."""

import hashlib
import json
import uuid
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.routes.ai_governance import _ensure_tables, _utc_now_iso
from api.routes import pack_catalogue as cat
from api.routes.pack_catalogue import (
    BUNDLES,
    EVALUATIONS,
    EVERY_PACK,
    FRAMEWORK_KEYS,
    FRAMEWORKS,
    GATE_KINDS,
    PACKS,
    PATTERNS,
    PILLARS,
    REQUIREMENTS,
    WORKFLOWS,
    Coverage,
    Step,
    Workflow,
    requirement_status,
)
from config.auth import TokenData, get_current_active_user
from database.connection import get_db
from src.application.services.governance_assurance_service import (
    GovernanceAssuranceService,
    OrgMembership,
)

router = APIRouter()

GENESIS_HASH = "0" * 64
RUN_STATUSES = ("queued", "running", "waiting", "blocked", "done", "failed")

# ponytail: the chain is tamper-evident only. Anyone with write access to the
# database can rewrite every row and recompute every hash. Anchor the head hash
# outside the database (signed export, external log) before relying on it as
# proof.


class StartRunBody(BaseModel):
    system_id: Optional[str] = None


class StepOutputBody(BaseModel):
    summary: str = Field(min_length=1, max_length=20000)
    # Required when the step branches: the label of the branch to take, e.g. "routine" or "exception".
    route: Optional[str] = None


class DecisionBody(BaseModel):
    decision: Literal["approve", "request_changes", "reject"]
    notes: str = ""


def _member(
    org_id: str = Query(min_length=1),
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> OrgMembership:
    """The caller's membership in the requested organization; 404 when they are not a member."""
    membership = GovernanceAssuranceService(db).membership(org_id, current_user.user_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Organization not found")
    return membership


def _manager(membership: OrgMembership = Depends(_member)) -> OrgMembership:
    """Installing, removing, starting runs and deciding gates need owner or admin rights."""
    if not GovernanceAssuranceService.may_mutate(membership):
        raise HTTPException(status_code=403, detail="Organization mutation permission required")
    return membership


def _pack_json(pack_id: str, installed: bool) -> dict:
    pack = PACKS[pack_id]
    return {
        "id": pack.id,
        "name": pack.name,
        "pillar": pack.pillar,
        "description": pack.description,
        "installed": installed,
        "patterns": [
            {
                "id": p.id,
                "name": p.name,
                "agentic": p.agentic,
                "workflowCount": len(p.workflows),
                "evaluationCount": len(p.evaluations),
            }
            for p in (PATTERNS[pid] for pid in pack.patterns)
        ],
        "workflowCount": len(cat.PACK_WORKFLOWS[pack_id]),
        "evaluationCount": len(cat.PACK_EVALUATIONS[pack_id]),
        "requirementsTouched": len(cat.PACK_TOUCHED[pack_id]),
        "agentic": any(PATTERNS[pid].agentic for pid in pack.patterns),
    }


def _installed_ids(db: Session, org_id: str) -> List[str]:
    """Installed pack ids the catalogue still knows; ids left over from an older catalogue are ignored."""
    rows = db.execute(text("SELECT pack_id FROM pack_installs WHERE org_id = :org_id"), {"org_id": org_id})
    return [r[0] for r in rows if r[0] in PACKS]


def _pack_ref(pack_id: str) -> dict:
    return {"id": pack_id, "name": PACKS[pack_id].name}


def _is_installed(db: Session, org_id: str, pack_id: str) -> bool:
    return (
        db.execute(
            text("SELECT 1 FROM pack_installs WHERE org_id = :org_id AND pack_id = :pack_id"),
            {"org_id": org_id, "pack_id": pack_id},
        ).fetchone()
        is not None
    )


# --- versions --------------------------------------------------------------
# An organization can edit a catalogue workflow: one draft at a time, published
# as numbered versions that are never changed afterwards. A run records the
# version it ran ("org-3", or the catalogue version), so its steps stay fixed.


def _version_label(version: int) -> str:
    return f"org-{version}"


def _published(db: Session, org_id: str, workflow_id: str):
    return (
        db.execute(
            text(
                "SELECT * FROM workflow_versions WHERE org_id = :org_id AND workflow_id = :wf AND status = 'published' "
                "ORDER BY version DESC LIMIT 1"
            ),
            {"org_id": org_id, "wf": workflow_id},
        )
        .mappings()
        .fetchone()
    )


def _draft(db: Session, org_id: str, workflow_id: str):
    return (
        db.execute(
            text("SELECT * FROM workflow_versions WHERE org_id = :org_id AND workflow_id = :wf AND status = 'draft'"),
            {"org_id": org_id, "wf": workflow_id},
        )
        .mappings()
        .fetchone()
    )


def _steps_of(row) -> List[Step]:
    return [Step(**s) for s in json.loads(row["steps_json"])]


def _current(db: Session, org_id: str, wf: Workflow):
    """The steps new runs use and their version label: the latest published org version, else the catalogue's."""
    row = _published(db, org_id, wf.id)
    return (_steps_of(row), _version_label(row["version"])) if row else (wf.steps, cat.VERSION)


def _run_steps(db: Session, run) -> List[Step]:
    label = run["workflow_version"]
    if label.startswith("org-"):
        row = (
            db.execute(
                text("SELECT steps_json FROM workflow_versions WHERE org_id = :org_id AND workflow_id = :wf AND version = :v"),
                {"org_id": run["org_id"], "wf": run["workflow_id"], "v": int(label[4:])},
            )
            .mappings()
            .fetchone()
        )
        if row:
            return _steps_of(row)
    return WORKFLOWS[run["workflow_id"]].steps


def _waiting_for(db: Session, run) -> Optional[str]:
    """What a waiting run needs: a gate decision ("approval") or a person to submit the step's output ("input")."""
    if run["status"] != "waiting" or not run["current_step"]:
        return None
    step = next((s for s in _run_steps(db, run) if s.id == run["current_step"]), None)
    if not step:
        return None
    return "approval" if step.kind in GATE_KINDS else "input"


def _summary(db: Session, run) -> dict:
    return {
        "id": run["id"],
        "workflowId": run["workflow_id"],
        "workflowName": WORKFLOWS[run["workflow_id"]].name,
        "status": run["status"],
        "currentStep": run["current_step"],
        "version": run["workflow_version"],
        "waitingFor": _waiting_for(db, run),
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
        **_summary(db, run),
        "steps": [s.model_dump() for s in _run_steps(db, run)],
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


def _run_or_404(db: Session, org_id: str, run_id: str):
    run = (
        db.execute(
            text("SELECT * FROM workflow_runs WHERE id = :id AND org_id = :org_id"),
            {"id": run_id, "org_id": org_id},
        )
        .mappings()
        .fetchone()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


# --- catalogue, library and install ----------------------------------------
# Fixed paths come before parameterised ones so nothing is shadowed.


@router.get("/catalogue")
async def get_catalogue(_m: OrgMembership = Depends(_member)):
    pillars = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "packs": sum(1 for x in PACKS.values() if x.pillar == p.id),
            "workflows": sum(1 for x in WORKFLOWS.values() if x.pillar == p.id),
            "evaluations": sum(1 for x in EVALUATIONS.values() if x.pillar == p.id),
            "frameworks": sum(1 for x in FRAMEWORKS.values() if x.pillar == p.id),
        }
        for p in PILLARS.values()
    ]
    counts = {
        "packs": len(PACKS),
        "patterns": len(PATTERNS),
        "workflows": len(WORKFLOWS),
        "evaluations": len(EVALUATIONS),
        "frameworks": len(FRAMEWORKS),
        "requirements": len(REQUIREMENTS),
    }
    return {"version": cat.VERSION, "pillars": pillars, "counts": counts}


@router.get("")
async def list_packs(m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _ensure_tables(db)
    installed = set(_installed_ids(db, m.org_id))
    return [_pack_json(pid, pid in installed) for pid in PACKS]


def _evaluation_json(ev, installed: set) -> dict:
    pattern = PATTERNS[ev.pattern]
    pack_id = cat.EVALUATION_PACK[ev.id]
    return {
        "id": ev.id,
        "name": ev.name,
        "measures": ev.measures,
        "metric": ev.metric,
        "threshold": ev.threshold,
        "appliesTo": ev.appliesTo,
        "pillar": ev.pillar,
        "pattern": {"id": pattern.id, "name": pattern.name},
        "pack": _pack_ref(pack_id),
        "engine": ev.engine,
        "codeLocation": ev.codeLocation,
        "tests": [
            {"key": k, "framework": REQUIREMENTS[k].framework, "control": REQUIREMENTS[k].control, "title": REQUIREMENTS[k].title}
            for k in ev.tests
        ],
        "installed": pack_id in installed,
    }


@router.get("/evaluations")
async def list_evaluations(
    pillar: Optional[str] = Query(default=None),
    engine: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    m: OrgMembership = Depends(_member),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    installed = set(_installed_ids(db, m.org_id))
    needle = q.strip().lower() if q else ""
    return [
        _evaluation_json(ev, installed)
        for ev in EVALUATIONS.values()
        if (not pillar or ev.pillar == pillar.upper())
        and (not engine or ev.engine == engine)
        and (not needle or needle in f"{ev.id} {ev.name} {ev.measures or ''} {ev.metric or ''}".lower())
    ]


@router.get("/evaluations/{evaluation_id}")
async def get_evaluation(evaluation_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    ev = EVALUATIONS.get(evaluation_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    _ensure_tables(db)
    return _evaluation_json(ev, set(_installed_ids(db, m.org_id)))


@router.get("/library/{pack_id}")
async def get_library(pack_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    if pack_id not in PACKS:
        raise HTTPException(status_code=404, detail="Pack not found")
    _ensure_tables(db)
    org_id = m.org_id
    latest = _latest_runs(db, org_id, set(cat.PACK_WORKFLOWS[pack_id]))
    patterns = [
        {
            "id": p.id,
            "name": p.name,
            "objective": p.objective,
            "agentic": p.agentic,
            "workflows": [
                {
                    "id": wid,
                    "name": WORKFLOWS[wid].name,
                    "autonomy": WORKFLOWS[wid].autonomy,
                    "stage": WORKFLOWS[wid].stage,
                    "latestRun": _summary(db, latest[wid]) if wid in latest else None,
                }
                for wid in p.workflows
            ],
            "evaluations": [{"id": e, "name": EVALUATIONS[e].name, "engine": EVALUATIONS[e].engine} for e in p.evaluations],
        }
        for p in (PATTERNS[pid] for pid in PACKS[pack_id].patterns)
    ]
    own = Coverage([pack_id])
    frameworks = [
        {"key": fk, "name": fw.name, "touched": touched, "covered": own.count(fk)}
        for fk, fw in FRAMEWORKS.items()
        if (touched := len(FRAMEWORK_KEYS[fk] & cat.PACK_TOUCHED[pack_id]))
    ]
    return {**_pack_json(pack_id, pack_id in _installed_ids(db, org_id)), "patterns": patterns, "frameworks": frameworks}


def _bundle_json(bundle_id: str, installed: List[str]) -> dict:
    bundle = BUNDLES[bundle_id]
    own, org = Coverage(bundle.packs), Coverage(installed)
    return {
        "id": bundle.id,
        "name": bundle.name,
        "for": bundle.for_,
        "packs": [{**_pack_ref(p), "installed": p in installed} for p in bundle.packs],
        "installedCount": sum(1 for p in bundle.packs if p in installed),
        "targets": [
            {
                "key": fk,
                "name": FRAMEWORKS[fk].name,
                "active": len(FRAMEWORK_KEYS[fk]),
                "coveredAll": own.count(fk),
                "coveredInstalled": org.count(fk),
            }
            for fk in bundle.targets
        ],
    }


@router.get("/bundles")
async def list_bundles(m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _ensure_tables(db)
    installed = _installed_ids(db, m.org_id)
    return [_bundle_json(b, installed) for b in BUNDLES]


@router.post("/bundles/{bundle_id}/install")
async def install_bundle(bundle_id: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    if bundle_id not in BUNDLES:
        raise HTTPException(status_code=404, detail="Bundle not found")
    _ensure_tables(db)
    for pack_id in BUNDLES[bundle_id].packs:
        _install(db, m, pack_id)
    return _bundle_json(bundle_id, _installed_ids(db, m.org_id))


@router.get("/journeys")
async def list_journeys(m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _ensure_tables(db)
    org = Coverage(_installed_ids(db, m.org_id))
    installed = set(_installed_ids(db, m.org_id))
    latest = _latest_runs(db, m.org_id, set(WORKFLOWS))
    rows = [
        {
            "key": fk,
            "name": fw.name,
            "pillar": fw.pillar,
            "active": len(FRAMEWORK_KEYS[fk]),
            "coveredAll": EVERY_PACK.count(fk),
            "coveredInstalled": org.count(fk),
            "contributingPacks": [p for p in PACKS if FRAMEWORK_KEYS[fk] & cat.PACK_DONE[p]],
            "binding": fw.binding,
            **_framework_workflows(fk, installed, latest),
        }
        for fk, fw in FRAMEWORKS.items()
        if len(FRAMEWORK_KEYS[fk]) >= 5
    ]
    return sorted(rows, key=lambda r: r["name"])


def _framework_workflows(framework_key: str, installed: set, latest: Dict[str, Any]) -> dict:
    """Workflows of installed packs that map to the framework, each with its latest run status, and how many wait for a person."""
    ids = sorted({w for k in FRAMEWORK_KEYS[framework_key] for w, _ in cat.REQUIREMENT_WORKFLOWS.get(k, []) if cat.WORKFLOW_PACK[w] in installed})
    workflows = [
        {"id": w, "name": WORKFLOWS[w].name, "stage": WORKFLOWS[w].stage, "status": latest[w]["status"] if w in latest else None}
        for w in ids
    ]
    return {"workflows": workflows, "waiting": sum(1 for w in workflows if w["status"] == "waiting")}


@router.post("/journeys/{framework_key}/install")
async def install_framework(framework_key: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    """Add a framework: install every pack that covers or tests one of its requirements."""
    if framework_key not in FRAMEWORKS:
        raise HTTPException(status_code=404, detail="Journey not found")
    _ensure_tables(db)
    for pack_id in PACKS:
        if FRAMEWORK_KEYS[framework_key] & cat.PACK_DONE[pack_id]:
            _install(db, m, pack_id)
    return {"installed": _installed_ids(db, m.org_id)}


@router.get("/journeys/{framework_key}")
async def get_journey(framework_key: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    fw = FRAMEWORKS.get(framework_key)
    if not fw:
        raise HTTPException(status_code=404, detail="Journey not found")
    _ensure_tables(db)
    ids = _installed_ids(db, m.org_id)
    installed, org = set(ids), Coverage(ids)
    keys = FRAMEWORK_KEYS[framework_key]
    latest = _latest_runs(db, m.org_id, {w for k in keys for w, _ in cat.REQUIREMENT_WORKFLOWS.get(k, [])})
    groups: Dict[str, list] = {}
    for req in REQUIREMENTS.values():
        if req.key not in keys:
            continue
        groups.setdefault(req.group or "Other", []).append(
            {
                "key": req.key,
                "control": req.control,
                "title": req.title,
                "status": requirement_status(req.key, org),
                "workflows": [
                    {
                        "id": wid,
                        "name": WORKFLOWS[wid].name,
                        "relation": relation,
                        "stage": WORKFLOWS[wid].stage,
                        "pack": cat.WORKFLOW_PACK[wid],
                        "installed": cat.WORKFLOW_PACK[wid] in installed,
                        "latestRun": _summary(db, latest[wid]) if wid in latest else None,
                    }
                    for wid, relation in cat.REQUIREMENT_WORKFLOWS.get(req.key, [])
                ],
                "evaluations": [
                    {
                        "id": eid,
                        "name": EVALUATIONS[eid].name,
                        "engine": EVALUATIONS[eid].engine,
                        "pack": cat.EVALUATION_PACK[eid],
                        "installed": cat.EVALUATION_PACK[eid] in installed,
                    }
                    for eid in cat.REQUIREMENT_EVALUATIONS.get(req.key, [])
                ],
            }
        )
    # Only packs that cover or test something in this framework are steps; cumulative runs over all of them in catalogue order.
    steps, seen = [], set()
    for pack_id, pack in PACKS.items():
        done = keys & cat.PACK_DONE[pack_id]
        if not done:
            continue
        new = done - seen
        seen |= done
        steps.append(
            {
                "pack": pack_id,
                "name": pack.name,
                "installed": pack_id in installed,
                "newlyCovered": len(new),
                "cumulative": len(seen),
            }
        )
    return {
        "key": fw.key,
        "name": fw.name,
        "pillar": fw.pillar,
        "version": fw.version,
        "binding": fw.binding,
        "status": fw.status,
        "active": len(keys),
        "coveredAll": EVERY_PACK.count(framework_key),
        "coveredInstalled": org.count(framework_key),
        "groups": [{"name": name, "requirements": reqs} for name, reqs in groups.items()],
        "steps": steps,
    }


def _install(db: Session, m: OrgMembership, pack_id: str) -> None:
    if _is_installed(db, m.org_id, pack_id):
        return
    try:
        db.execute(
            text(
                "INSERT INTO pack_installs (id, org_id, pack_id, installed_by, created_at) "
                "VALUES (:id, :org_id, :pack_id, :installed_by, :created_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "org_id": m.org_id,
                "pack_id": pack_id,
                "installed_by": m.user_id,
                "created_at": _utc_now_iso(),
            },
        )
        db.commit()
    except IntegrityError:
        db.rollback()  # a concurrent install won; same end state


@router.post("/{pack_id}/install")
async def install_pack(pack_id: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    if pack_id not in PACKS:
        raise HTTPException(status_code=404, detail="Pack not found")
    _ensure_tables(db)
    _install(db, m, pack_id)
    return _pack_json(pack_id, True)


@router.delete("/{pack_id}/install")
async def uninstall_pack(pack_id: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    if pack_id not in PACKS:
        raise HTTPException(status_code=404, detail="Pack not found")
    _ensure_tables(db)
    db.execute(
        text("DELETE FROM pack_installs WHERE org_id = :org_id AND pack_id = :pack_id"),
        {"org_id": m.org_id, "pack_id": pack_id},
    )
    db.commit()
    return _pack_json(pack_id, False)


def _workflow_or_404(workflow_id: str) -> Workflow:
    wf = WORKFLOWS.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    wf = _workflow_or_404(workflow_id)
    _ensure_tables(db)
    org_id = m.org_id
    latest = _latest_runs(db, org_id, [wf.id]).get(wf.id)
    pattern = PATTERNS[wf.pattern]
    pack_id = cat.WORKFLOW_PACK[wf.id]
    steps, version = _current(db, org_id, wf)
    draft = _draft(db, org_id, wf.id)
    return {
        "id": wf.id,
        "name": wf.name,
        "version": version,
        "catalogueVersion": cat.VERSION,
        "draft": {"version": draft["version"], "updatedAt": draft["updated_at"]} if draft else None,
        "stage": wf.stage,
        "description": wf.description,
        "packId": pack_id,
        "pack": _pack_ref(pack_id),
        "installed": _is_installed(db, org_id, pack_id),
        "pattern": {"id": pattern.id, "name": pattern.name},
        "pillar": wf.pillar,
        "commonControl": wf.commonControl,
        "autonomy": wf.autonomy,
        "gate": wf.gate,
        "gateConditions": wf.gateConditions,
        "approver": wf.approver,
        "separationOfDuties": wf.separationOfDuties,
        "externalWrite": wf.externalWrite,
        "triggers": wf.triggers,
        "mappings": [
            {
                "key": mp.key,
                "framework": REQUIREMENTS[mp.key].framework,
                "control": REQUIREMENTS[mp.key].control,
                "title": REQUIREMENTS[mp.key].title,
                "relation": mp.relation,
                "note": mp.note,
            }
            for mp in wf.mappings
        ],
        "evaluations": [{"id": e, "name": EVALUATIONS[e].name, "engine": EVALUATIONS[e].engine} for e in pattern.evaluations],
        "steps": [s.model_dump() for s in steps],
        "latestRun": _summary(db, latest) if latest else None,
    }


# --- runs ------------------------------------------------------------------


@router.post("/workflows/{workflow_id}/runs")
async def start_run(
    workflow_id: str,
    body: StartRunBody = StartRunBody(),
    m: OrgMembership = Depends(_manager),
    db: Session = Depends(get_db),
):
    wf = _workflow_or_404(workflow_id)
    _ensure_tables(db)
    org_id = m.org_id
    if not _is_installed(db, org_id, cat.WORKFLOW_PACK[wf.id]):
        raise HTTPException(status_code=409, detail="Install the pack before starting a run")
    if body.system_id:
        system = db.execute(
            text("SELECT org_id FROM governance_ai_systems WHERE id = :id"), {"id": body.system_id}
        ).fetchone()
        if not system or str(system[0]) != org_id:
            raise HTTPException(status_code=404, detail="AI system not found")
    steps, version = _current(db, org_id, wf)
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
            "workflow_version": version,
            "ai_system_id": body.system_id,
            "started_by": m.user_id,
            "now": now,
        },
    )
    _append(db, run_id, "run.created", None, {"workflowId": wf.id, "workflowVersion": version})
    run = {
        "id": run_id,
        "org_id": org_id,
        "workflow_id": wf.id,
        "workflow_version": version,
        "ai_system_id": body.system_id,
        "started_by": m.user_id,
        "approval_request_id": None,
    }
    _advance(db, run, steps[0].id, m.user_id)
    db.commit()
    return _run_json(db, run_id)


@router.get("/runs")
async def list_runs(
    status: Optional[str] = Query(default=None),
    m: OrgMembership = Depends(_member),
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
            {"org_id": m.org_id, "status": status},
        )
        .mappings()
        .all()
    )
    return [_summary(db, r) for r in rows]


@router.get("/runs/{run_id}")
async def get_run(run_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _run_or_404(db, m.org_id, run_id)
    return _run_json(db, run_id)


def _open_gate(db: Session, run, requested_by: Optional[str]) -> str:
    """Create the governance approval request for a run, using the shared workflow_run approval workflow."""
    workflow_row = db.execute(
        text(
            "SELECT id FROM governance_approval_workflows "
            "WHERE entity_type = 'workflow_run' AND is_active = TRUE LIMIT 1"
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
                "is_active": True,
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


# --- engine ----------------------------------------------------------------
# A guided run: the engine finishes the steps it can do alone (start, escalate,
# file evidence), opens a gate on ask, exception and decide steps, and stops on
# every other step until a person (later an agent) submits that step's output.

AUTO_KINDS = ("trigger", "escalate", "file")
MAX_REVISIONS = 3  # the catalogue's "changes asked: max 3 rounds then escalate"
DECISION_EDGES = {
    "approve": ("approved", "conclusions"),
    "request_changes": ("changes asked", "more drafting"),
    "reject": ("rejected", "risk accepted"),
}
DECISION_STATUS = {"approve": "approved", "request_changes": "changes_requested", "reject": "rejected"}


def _edge(step, *needles: str) -> Optional[str]:
    """The step that follows: the only edge when no needles are given, else the first whose label contains one."""
    if not needles:
        return step.next[0].to if step.next else None
    for e in step.next:
        if e.label and any(n in e.label.lower() for n in needles):
            return e.to
    return None


def _advance(db: Session, run, step_id: Optional[str], user_id: Optional[str]) -> None:
    """Move the run onto step_id and through every step the engine finishes itself. Caller commits."""
    wf = WORKFLOWS[run["workflow_id"]]
    steps = {s.id: s for s in _run_steps(db, run)}
    status, approval_request_id, finished_at = "running", run["approval_request_id"], None
    while step_id is not None:
        step = steps[step_id]
        if step.kind in GATE_KINDS:
            approval_request_id = _open_gate(db, run, user_id)
            _append(db, run["id"], "gate.opened", step_id, {"approvalRequestId": approval_request_id, "approver": wf.approver})
            status = "waiting"
            break
        _append(db, run["id"], "step.started", step_id, {})
        if step.kind not in AUTO_KINDS:
            status = "waiting"
            break
        if step.kind == "trigger":
            payload = {"systemId": run["ai_system_id"], "startedBy": run["started_by"], "workflowVersion": run["workflow_version"]}
        elif step.kind == "escalate":
            # ponytail: recorded only; no notifier exists yet, so nobody is messaged.
            payload = {"approver": wf.approver, "notificationSent": False}
        else:
            head = db.execute(
                text("SELECT seq, hash FROM workflow_run_events WHERE run_id = :id ORDER BY seq DESC LIMIT 1"),
                {"id": run["id"]},
            ).fetchone()
            payload = {"sealedThroughSeq": head[0], "sealedHeadHash": head[1]}
        _append(db, run["id"], "step.completed", step_id, payload)
        step_id = _edge(step)
    if step_id is None:
        status, finished_at = "done", _utc_now_iso()
        _append(db, run["id"], "run.completed", None, {})
    db.execute(
        text(
            "UPDATE workflow_runs SET status = :status, current_step = :current_step, finished_at = :finished_at, "
            "approval_request_id = :approval_request_id, updated_at = :now WHERE id = :id"
        ),
        {
            "status": status,
            "current_step": step_id,
            "finished_at": finished_at,
            "approval_request_id": approval_request_id,
            "now": _utc_now_iso(),
            "id": run["id"],
        },
    )


def _claim(db: Session, run_id: str, step_id: str) -> None:
    """Take a waiting run off its step; a concurrent second caller updates zero rows and gets 409."""
    claimed = db.execute(
        text(
            "UPDATE workflow_runs SET status = 'running', updated_at = :now "
            "WHERE id = :id AND status = 'waiting' AND current_step = :step"
        ),
        {"now": _utc_now_iso(), "id": run_id, "step": step_id},
    ).rowcount
    if not claimed:
        db.rollback()
        raise HTTPException(status_code=409, detail="Run is no longer waiting on this step")


@router.post("/runs/{run_id}/steps/{step_id}/output")
async def submit_step_output(
    run_id: str,
    step_id: str,
    body: StepOutputBody,
    m: OrgMembership = Depends(_manager),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    run = _run_or_404(db, m.org_id, run_id)
    step = next((s for s in _run_steps(db, run) if s.id == step_id), None)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    if run["status"] != "waiting" or run["current_step"] != step_id or step.kind in GATE_KINDS:
        raise HTTPException(status_code=409, detail="This step is not waiting for output")
    if len(step.next) > 1:
        target = next((e.to for e in step.next if e.label == body.route), None)
        if target is None:
            raise HTTPException(status_code=422, detail=f"route must be one of: {', '.join(e.label or '' for e in step.next)}")
    else:
        target = _edge(step)
    _claim(db, run_id, step_id)
    payload = {"summary": body.summary, "source": "manual", "submittedBy": m.user_id}
    if len(step.next) > 1:
        payload["route"] = body.route
    _append(db, run_id, "step.completed", step_id, payload)
    _advance(db, run, target, m.user_id)
    db.commit()
    return _run_json(db, run_id)


@router.post("/runs/{run_id}/decision")
async def decide_run(
    run_id: str,
    body: DecisionBody,
    m: OrgMembership = Depends(_manager),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    run = _run_or_404(db, m.org_id, run_id)
    if _waiting_for(db, run) != "approval" or not run["approval_request_id"]:
        raise HTTPException(status_code=409, detail="Run is not waiting for a decision")
    step = next(s for s in _run_steps(db, run) if s.id == run["current_step"])
    target = _edge(step, *DECISION_EDGES[body.decision])
    if target is None:
        raise HTTPException(status_code=422, detail="This step does not offer that decision")
    escalated = False
    if body.decision == "request_changes":
        rounds = sum(
            json.loads(p).get("decision") == "request_changes"
            for (p,) in db.execute(
                text("SELECT payload_json FROM workflow_run_events WHERE run_id = :id AND kind = 'gate.decided' AND step_id = :step"),
                {"id": run_id, "step": step.id},
            )
        )
        if rounds >= MAX_REVISIONS and _edge(step, "sla"):
            target, escalated = _edge(step, "sla"), True
    _claim(db, run_id, step.id)
    decision = DECISION_STATUS[body.decision]
    now = _utc_now_iso()
    decided = db.execute(
        text(
            "UPDATE governance_approval_requests "
            "SET status = :status, decision = :status, decision_notes = :notes, "
            "decided_by = :decided_by, decided_at = :now, updated_at = :now "
            "WHERE id = :id AND entity_type = 'workflow_run' AND status = 'pending'"
        ),
        {"status": decision, "notes": body.notes, "decided_by": m.user_id, "now": now, "id": run["approval_request_id"]},
    ).rowcount
    if not decided:
        db.rollback()
        raise HTTPException(status_code=409, detail="Run is not waiting for a decision")
    db.execute(
        text(
            "INSERT INTO governance_approval_decisions (id, request_id, decision, notes, decided_by, created_at) "
            "VALUES (:id, :request_id, :decision, :notes, :decided_by, :created_at)"
        ),
        {
            "id": str(uuid.uuid4()),
            "request_id": run["approval_request_id"],
            "decision": decision,
            "notes": body.notes,
            "decided_by": m.user_id,
            "created_at": now,
        },
    )
    payload = {"decision": body.decision, "notes": body.notes, "decidedBy": m.user_id}
    if escalated:
        payload["escalated"] = f"more than {MAX_REVISIONS} rounds of changes"
    _append(db, run_id, "gate.decided", step.id, payload)
    _advance(db, run, target, m.user_id)
    db.commit()
    return _run_json(db, run_id)


# --- builder ---------------------------------------------------------------

MAX_STEPS = 60


class DraftBody(BaseModel):
    steps: List[Step] = Field(min_length=1, max_length=MAX_STEPS)


def _problems(steps: List[Step], wf: Workflow) -> List[str]:
    """Why a draft cannot be published yet; empty when it can."""
    by_id = {s.id: s for s in steps}
    out: List[str] = []
    if len(by_id) != len(steps):
        out.append("Two steps share an id.")
    if steps[0].kind != "trigger":
        out.append("The first step must be the start step.")
    if sum(s.kind == "trigger" for s in steps) > 1:
        out.append("A workflow has only one start step.")
    for s in steps:
        for e in s.next:
            if e.to not in by_id:
                out.append(f"{s.title} goes to a step that no longer exists.")
            elif e.to == s.id:
                out.append(f"{s.title} goes back to itself.")
        if s.kind in GATE_KINDS:
            if not _edge(s, *DECISION_EDGES["approve"]):
                out.append(f"{s.title} needs a branch for when the person approves.")
        elif len(s.next) > 1:
            labels = [e.label for e in s.next]
            if not all(labels) or len(set(labels)) != len(labels):
                out.append(f"{s.title} branches, so each branch needs its own name.")
    seen, queue = {steps[0].id}, [steps[0].id]
    while queue:
        for e in by_id[queue.pop()].next:
            if e.to in by_id and e.to not in seen:
                seen.add(e.to)
                queue.append(e.to)
    out += [f"{s.title} cannot be reached from the start." for s in steps if s.id not in seen]
    if not any(not s.next for s in steps):
        out.append("The workflow never finishes: one step must have no next step.")
    if not any(s.kind == "file" for s in steps):
        out.append("Keep a file evidence step so every run is sealed.")
    if any(s.kind in GATE_KINDS for s in wf.steps) and not any(s.kind in GATE_KINDS for s in steps):
        out.append("Keep at least one step where a person decides; the catalogue workflow has one.")
    return out


def _draft_json(db: Session, row, wf: Workflow) -> dict:
    steps = _steps_of(row)
    return {
        "workflowId": wf.id,
        "version": row["version"],
        "basedOn": row["base_version"],
        "steps": [s.model_dump() for s in steps],
        "problems": _problems(steps, wf),
        "updatedAt": row["updated_at"],
        "updatedBy": row["updated_by"],
    }


def _editable(db: Session, m: OrgMembership, workflow_id: str) -> Workflow:
    wf = _workflow_or_404(workflow_id)
    _ensure_tables(db)
    if not _is_installed(db, m.org_id, cat.WORKFLOW_PACK[wf.id]):
        raise HTTPException(status_code=409, detail="Install the pack before editing its workflows")
    return wf


def _draft_or_404(db: Session, org_id: str, workflow_id: str):
    row = _draft(db, org_id, workflow_id)
    if not row:
        raise HTTPException(status_code=404, detail="No draft for this workflow")
    return row


@router.get("/workflows/{workflow_id}/versions")
async def list_versions(workflow_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _workflow_or_404(workflow_id)
    _ensure_tables(db)
    rows = (
        db.execute(
            text(
                "SELECT version, status, base_version, created_by, published_by, created_at, published_at "
                "FROM workflow_versions WHERE org_id = :org_id AND workflow_id = :wf ORDER BY version DESC"
            ),
            {"org_id": m.org_id, "wf": workflow_id},
        )
        .mappings()
        .all()
    )
    return [
        {
            "version": r["version"],
            "label": _version_label(r["version"]),
            "status": r["status"],
            "basedOn": r["base_version"],
            "createdBy": r["created_by"],
            "publishedBy": r["published_by"],
            "createdAt": r["created_at"],
            "publishedAt": r["published_at"],
        }
        for r in rows
    ]


@router.get("/workflows/{workflow_id}/draft")
async def get_draft(workflow_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    wf = _workflow_or_404(workflow_id)
    _ensure_tables(db)
    return _draft_json(db, _draft_or_404(db, m.org_id, wf.id), wf)


@router.post("/workflows/{workflow_id}/draft")
async def create_draft(workflow_id: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    """Start a draft from the version runs use now. If one exists it is returned as it is."""
    wf = _editable(db, m, workflow_id)
    row = _draft(db, m.org_id, wf.id)
    if not row:
        steps, base = _current(db, m.org_id, wf)
        top = db.execute(
            text("SELECT MAX(version) FROM workflow_versions WHERE org_id = :org_id AND workflow_id = :wf"),
            {"org_id": m.org_id, "wf": wf.id},
        ).scalar()
        now = _utc_now_iso()
        try:
            db.execute(
                text(
                    "INSERT INTO workflow_versions "
                    "(id, org_id, workflow_id, version, status, base_version, steps_json, created_by, updated_by, created_at, updated_at) "
                    "VALUES (:id, :org_id, :wf, :version, 'draft', :base, :steps, :user, :user, :now, :now)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "org_id": m.org_id,
                    "wf": wf.id,
                    "version": (top or 0) + 1,
                    "base": base,
                    "steps": json.dumps([s.model_dump() for s in steps]),
                    "user": m.user_id,
                    "now": now,
                },
            )
            db.commit()
        except IntegrityError:
            db.rollback()  # someone else started the draft first; return theirs
        row = _draft_or_404(db, m.org_id, wf.id)
    return _draft_json(db, row, wf)


@router.put("/workflows/{workflow_id}/draft")
async def save_draft(workflow_id: str, body: DraftBody, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    """Save the draft as it is; problems are reported, not refused, so half-finished edits are kept."""
    wf = _editable(db, m, workflow_id)
    row = _draft_or_404(db, m.org_id, wf.id)
    steps_json = json.dumps([s.model_dump() for s in body.steps])
    if len(steps_json) > 200_000:
        raise HTTPException(status_code=413, detail="This workflow is too large to save")
    db.execute(
        text("UPDATE workflow_versions SET steps_json = :steps, updated_by = :user, updated_at = :now WHERE id = :id AND status = 'draft'"),
        {"steps": steps_json, "user": m.user_id, "now": _utc_now_iso(), "id": row["id"]},
    )
    db.commit()
    return _draft_json(db, _draft_or_404(db, m.org_id, wf.id), wf)


@router.delete("/workflows/{workflow_id}/draft")
async def discard_draft(workflow_id: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    wf = _editable(db, m, workflow_id)
    row = _draft_or_404(db, m.org_id, wf.id)
    db.execute(text("DELETE FROM workflow_versions WHERE id = :id AND status = 'draft'"), {"id": row["id"]})
    db.commit()
    return {"discarded": row["version"]}


@router.post("/workflows/{workflow_id}/draft/publish")
async def publish_draft(workflow_id: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    wf = _editable(db, m, workflow_id)
    row = _draft_or_404(db, m.org_id, wf.id)
    problems = _problems(_steps_of(row), wf)
    if problems:
        raise HTTPException(status_code=422, detail={"message": "Fix these before publishing", "problems": problems})
    now = _utc_now_iso()
    published = db.execute(
        text(
            "UPDATE workflow_versions SET status = 'published', published_by = :user, published_at = :now, updated_at = :now "
            "WHERE id = :id AND status = 'draft'"
        ),
        {"user": m.user_id, "now": now, "id": row["id"]},
    ).rowcount
    if not published:
        db.rollback()
        raise HTTPException(status_code=409, detail="The draft changed while publishing, retry")
    db.commit()
    return await get_workflow(workflow_id, m, db)
