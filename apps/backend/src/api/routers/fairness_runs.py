"""Fairness runs, monitoring runs, attestations and the release gate for one AI system.

POST /systems/{id}/fairness-runs/inspect   columns, a suggested mapping and protected attributes (inferred, or reused from the last run)
POST /systems/{id}/fairness-runs           run the metrics, store measured evidence and the attribute confirmation
POST /systems/{id}/monitoring-runs         current scores against the last run; drift as measured evidence
GET  /systems/{id}/monitoring-policy       expected snapshot cadence and the drift window (defaults when none stored)
PUT  /systems/{id}/monitoring-policy       set them; stale monitoring stops counting as proven, sustained drift opens a finding
POST /systems/{id}/attestations            a person states a check is satisfied; manual evidence
GET  /systems/{id}/gate                    verdict, confidence, check states, the release decision status, why, and the path to the next verdict
GET  /systems/{id}/clause-map              the gate per framework clause, scoped to the confirmed frameworks
GET  /estate/gates                         the gate of every system in the caller's org, without explain and path
GET  /frameworks/{key}/systems             per requirement, the cell of every system that confirmed the framework

Mounted under /api/v1/ai-governance next to the governance router and sharing
its org scoping and system access rules.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from api.routes.ai_governance import (
    CLOSED_RISK_STATUSES,
    OrgMembership,
    org_member,
    _authenticated_actor,
    _caller_org,
    _enforce_org_scope,
    _ensure_tables,
    _fetch_evidence_records,
    _fetch_latest_system_approval,
    _load_json_value,
    _release_blockers,
    _risk_score,
    _require_system_access,
)
from config.auth import TokenData, get_current_active_user
from database.connection import get_db
from pydantic import BaseModel, Field

from src.application.services.clause_map_service import _catalogue, clause_map, tracked_requirements
from src.application.services.decision_seal_service import list_seals
from src.application.services.system_lifecycle_service import drop_superseded, reopened_since
from src.application.services.fairness_run_service import (
    ATTESTABLE_CHECKS,
    ATTESTATION_CONFIDENCE,
    TIERS,
    FairnessRunError,
    confirm_attributes,
    effective_tier,
    evaluation_status,
    gate_check,
    gate_explain,
    inspect_csv,
    path_forward,
    release_gate,
    run_fairness,
    run_monitoring,
    tier_reasons,
)

router = APIRouter(tags=["fairness"], dependencies=[Depends(_enforce_org_scope)])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def _read_upload(file: UploadFile) -> bytes:
    # Sync on purpose: the handlers run in the threadpool, and the form parser has
    # already spooled the upload. Read one byte past the limit, never the whole file.
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if not data:
        raise HTTPException(status_code=422, detail="The uploaded file is empty")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="CSV larger than 25 MB; export a sample for the first run")
    return data


def _system_row(db: Session, system_id: str) -> Any:
    row = db.execute(
        text("SELECT id, name, risk_tier FROM governance_ai_systems WHERE id = :id"), {"id": system_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="AI system not found")
    return row


def _environmental_assessed(db: Session, system_id: str) -> Optional[Dict[str, Any]]:
    """The newest assessment's provenance and confidence, which the gate counts like any other record; None when there is none."""
    try:
        row = db.execute(
            text("SELECT provenance_class, confidence_score, created_at FROM governance_environmental_assessments WHERE system_id = :id ORDER BY created_at DESC LIMIT 1"),
            {"id": system_id},
        ).fetchone()
    except Exception:
        db.rollback()
        return None
    return {"provenance_class": row[0] or "unknown", "confidence": float(row[1] or 0.0), "created_at": row[2]} if row else None


DEFAULT_CADENCE_HOURS = 168
DEFAULT_DRIFT_WINDOW = 3
WATCH_SOURCE = "fairmind.watch"
RUN_SOURCE = "fairmind.fairness_library"  # the source this router stamps on a fairness run


def _monitoring_policy(db: Session, system_id: str) -> Dict[str, Any]:
    row = db.execute(
        text("SELECT cadence_hours, drift_window, updated_by, updated_at FROM governance_monitoring_policies WHERE system_id = :id"),
        {"id": system_id},
    ).fetchone()
    if not row:
        return {"cadenceHours": DEFAULT_CADENCE_HOURS, "driftWindow": DEFAULT_DRIFT_WINDOW, "updatedBy": None, "updatedAt": None, "isDefault": True}
    return {"cadenceHours": row[0], "driftWindow": row[1], "updatedBy": row[2], "updatedAt": row[3], "isDefault": False}


def _system_applicability(db: Session, system_id: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """(metadata.applicability or None, lifecycle stage) for one system."""
    row = db.execute(text("SELECT metadata_json, lifecycle_stage FROM governance_ai_systems WHERE id = :id"), {"id": system_id}).fetchone()
    applicability = _load_json_value(row[0], {}).get("applicability") if row else None
    return (applicability if isinstance(applicability, dict) else None), (row[1] if row else None)


ENV_BLOCKER_TEXT = {
    "environmental_no_go": "The latest environmental assessment is not no go",
    "environmental_mitigation_required": "A conditional go environmental assessment has documented mitigation or a valid exception",
}


def _approval_blockers(db: Session, system_id: str, gate: Dict[str, Any]) -> List[Dict[str, Any]]:
    """What the approval route enforces besides the verdict: env_gate_status, _release_blockers and blocking policy rules."""
    from src.application.services.environmental_service import env_gate_status

    try:
        env = env_gate_status(db, system_id)
    except Exception:
        db.rollback()
        env = {"blocked": True, "code": "missing_environmental_evidence"}
    counts = (_release_blockers(db, system_id) or {}).get("blockers", {})
    findings, tasks = counts.get("openHighOrCriticalFindings", 0), counts.get("activeCriticalTasks", 0)
    out = []
    if env.get("code") != "not_required":
        out.append({"key": "environmental_assessment", "text": "An environmental impact assessment is on file", "met": env.get("code") != "missing_environmental_evidence"})
    if env.get("blocked") and env.get("code") != "missing_environmental_evidence":
        out.append({"key": env.get("code"), "text": ENV_BLOCKER_TEXT.get(env.get("code"), env.get("reason")), "met": False})
    out.append({"key": "open_findings", "text": "No open high or critical findings" + (f" ({findings} open)" if findings else ""), "met": not findings})
    out.append({"key": "critical_tasks", "text": "No active critical remediation tasks" + (f" ({tasks} active)" if tasks else ""), "met": not tasks})
    if gate["policy"]["blocking"]:
        out.append({"key": "policy", "text": "No blocking policy rule fails", "met": False})
    return out


def _attested_controls(db: Session, system_id: str) -> Dict[str, Dict[str, Any]]:
    """Controls no gate check reaches that the organisation has stated or worked through, for the clause map.

    From done workflow runs a reviewer did not reject (organisation-scope ones, plus runs on this system; a systemless
    run of a system-scope workflow counts for no system, as the plan reads it) and from plan
    attestations, keyed by common control; the newest wins. Gate controls are left out: their checks count already.
    """
    from api.routes.pack_catalogue import WORKFLOWS
    from src.application.services.clause_map_service import GATE_CONTROLS

    org = db.execute(text("SELECT org_id FROM governance_ai_systems WHERE id = :id"), {"id": system_id}).scalar()
    if not org:
        return {}
    found = []
    for wf_id, sys_id, at, by in db.execute(
        text(
            "SELECT r.workflow_id, r.ai_system_id, COALESCE(r.finished_at, r.updated_at), r.started_by FROM workflow_runs r "
            "LEFT JOIN governance_approval_requests a ON a.id = r.approval_request_id "
            "WHERE r.org_id = :org AND r.status = 'done' AND (a.status IS NULL OR a.status <> 'rejected')"
        ),
        {"org": org},
    ).fetchall():
        wf = WORKFLOWS.get(wf_id)
        if wf and wf.commonControl and (sys_id == system_id or (wf.scope or "").lower().startswith("organisation")):
            found.append((wf.commonControl, {"statement": f"{wf.name}: completed", "by": by, "at": str(at), "source": "workflow"}))
    for task_key, statement, by, at in db.execute(
        text("SELECT task_key, statement, attested_by, created_at FROM plan_attestations WHERE org_id = :org"), {"org": org}
    ).fetchall():
        if task_key.startswith("control:"):
            found.append((task_key.split(":", 1)[1], {"statement": statement, "by": by, "at": str(at), "source": "plan_attestation"}))
    out: Dict[str, Dict[str, Any]] = {}
    for control, att in sorted(found, key=lambda f: f[1]["at"]):
        if control not in GATE_CONTROLS:
            out[control] = {**att, "confidence": ATTESTATION_CONFIDENCE}
    return out


def _gate_payload(db: Session, system_id: str, risk_tier: str, *, with_decision: bool = True) -> Dict[str, Any]:
    """The release gate; ``with_decision=False`` reads the evidence alone, as the reviewer deciding a request needs it.

    The verdict is computed on the effective tier: the suggested tier while a lower confirmed tier awaits a
    second person. ``explain`` and ``path`` say why the verdict is what it is and what would move it.
    """
    reopened = reopened_since(db, system_id)
    on_file = _fetch_evidence_records(db, system_id)
    records = drop_superseded(on_file, {k: at for k, (at, _) in reopened.items()})
    kept = {id(r) for r in records}
    # an evaluation run goes stale at any material change, so its check is reopened by the newest one
    stale_runs = {gate_check(r) for r in on_file if evaluation_status(r) and id(r) not in kept}
    newest_change = max(reopened.values()) if reopened else None
    cadence = _monitoring_policy(db, system_id)["cadenceHours"]
    applicability, stage = _system_applicability(db, system_id)
    tier = effective_tier(risk_tier, applicability)
    from src.application.services.environmental_service import system_environmental_gate_enabled

    from api.routes.system_targets import _row as _target_row

    with_env = system_environmental_gate_enabled(db, system_id)
    assessed = _environmental_assessed(db, system_id) if with_env else None
    if assessed and "environmental" in reopened and not drop_superseded([{"evidenceType": "environmental", "createdAt": assessed["created_at"]}], {"environmental": reopened["environmental"][0]}):
        assessed = None  # assessed before the change that reopened it
    approval = decided = None
    if with_decision:
        approval = _fetch_latest_system_approval(db, system_id)
        decided = db.execute(
            text("SELECT status FROM governance_approval_requests WHERE entity_type = 'ai_system' AND entity_id = :id AND status IN ('approved', 'rejected') ORDER BY created_at DESC LIMIT 1"),
            {"id": system_id},
        ).fetchone()
    gate = release_gate(
        tier, records, environmental_assessed=assessed, monitoring_cadence_hours=cadence,
        approval_status=approval["status"] if approval else "not_requested", last_decision=decided[0] if decided else None,
        include_environmental=with_env,
    )
    gate["reasons"] += tier_reasons(risk_tier, applicability)
    for check in gate["checks"]:
        change = reopened.get(check["key"]) or (newest_change if check["key"] in stale_runs else None)
        if change and check["state"] == "open":
            check["reopenedBy"] = change[1]
            gate["reasons"].append(f"Change {change[1]} reopened {check['label'].lower()}")
    _apply_policy_rules(db, system_id, gate)
    gate["systemId"] = system_id
    gate["riskTier"] = risk_tier
    gate["explain"] = gate_explain(risk_tier, applicability, include_environmental=with_env)
    has_target = _target_row(db, system_id) is not None
    gate["path"] = path_forward(
        tier, records, environmental_assessed=assessed, monitoring_cadence_hours=cadence, lifecycle_stage=stage,
        approval_blockers=_approval_blockers(db, system_id, gate), include_environmental=with_env,
        model_target=has_target,
    )
    if not has_target and any(c["key"] == "fairness" and c["state"] != "proven" for c in gate["checks"]):
        gate["path"]["notes"].append(
            "Fairness is priced as a CSV fairness run because no model connection is saved. For a chat or LLM system, save how "
            "FairMind calls it under Model connection, and fairness is measured by a behaviour test instead."
        )
    gate["attestedControls"] = _attested_controls(db, system_id)
    if gate["policy"]["blocking"]:
        gate["path"]["notes"].append("A failing blocking policy rule holds the verdict at no go until the rule passes; evidence steps do not change that.")
    if gate["policy"]["warnings"]:
        # The path reads evidence alone; a warning caps the real verdict at conditional go, so no step promises go.
        if gate["path"]["target"] == "go" or gate["path"]["toGo"]:
            gate["path"]["notes"].append("A failing warning-level policy rule keeps the verdict at conditional go until the rule passes; evidence steps do not change that.")
        gate["path"]["toGo"] = None
        for option in gate["path"]["options"]:
            if option["verdictAfter"] == "go":
                option["verdictAfter"] = "conditional_go"
        if gate["path"]["ceiling"]["verdict"] == "go":
            gate["path"]["ceiling"]["verdict"] = "conditional_go"
    return gate


def _apply_policy_rules(db: Session, system_id: str, gate: Dict[str, Any]) -> None:
    """Fold the org's published policy rules into the gate: a failing blocking rule is no go, a warning is conditional."""
    from src.application.services.policy_service import PolicyService

    row = db.execute(text("SELECT org_id FROM governance_ai_systems WHERE id = :id"), {"id": system_id}).fetchone()
    check = PolicyService(db).release_check(row[0], system_id) if row and row[0] else None
    gate["policy"] = check or {"blocking": [], "warnings": []}
    describe = lambda r: f"Policy rule '{r['ruleTitle']}' ({r['policyName']}) fails"  # noqa: E731
    if gate["policy"]["blocking"]:
        gate["verdict"] = "no_go"
        gate["reasons"][:0] = [describe(r) for r in gate["policy"]["blocking"]]
    if gate["policy"]["warnings"]:
        gate["reasons"] += [describe(r) for r in gate["policy"]["warnings"]]
        if gate["verdict"] == "go":
            gate["verdict"] = "conditional_go"


@router.post("/systems/{system_id}/fairness-runs/inspect")
def inspect_fairness_csv(
    system_id: str,
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    try:
        return inspect_csv(_read_upload(file), _last_run_metadata(db, system_id))
    except FairnessRunError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


def _last_run_metadata(db: Session, system_id: str) -> Optional[Dict[str, Any]]:
    """Metadata of the system's latest fairness run, whose attributes the next inspect reuses."""
    row = db.execute(
        text("SELECT metadata_json FROM governance_evidence WHERE system_id = :id AND evidence_type = 'fairness_test' AND source = :source ORDER BY created_at DESC LIMIT 1"),
        {"id": system_id, "source": RUN_SOURCE},
    ).fetchone()
    return json.loads(row[0] or "{}") if row else None


def _confirmation_summary(record: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not record:
        return None
    return {"confirmed": bool(record.get("confirmed")), "by": record.get("confirmedBy"), "at": record.get("confirmedAt"), "attributes": record.get("attributes") or [], "notTested": record.get("uncoveredGrounds") or []}


@router.post("/systems/{system_id}/fairness-runs")
def create_fairness_run(
    system_id: str,
    http: Request,
    file: UploadFile = File(...),
    outcome: str = Form(...),
    attributes: str = Form(..., description="comma-separated protected attribute columns"),
    prediction: Optional[str] = Form(None),
    score: Optional[str] = Form(None),
    favorable_label: Optional[str] = Form(None),
    confirm: Optional[str] = Form(None, description='"1" when a person confirmed the attributes in the UI'),
    confirm_sha256: Optional[str] = Form(None),
    removal_reason: Optional[str] = Form(None),
    uncovered_reason: Optional[str] = Form(None),
    keep_for_agent: Optional[str] = Form(None, description='"1" keeps this file so the release autopilot can re-run it'),
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    system = _system_row(db, system_id)
    attribute_list = [a.strip() for a in attributes.split(",") if a.strip()]
    data = _read_upload(file)
    now = datetime.now(timezone.utc).isoformat()
    try:
        # The suggestion is recomputed from these bytes, so a client cannot choose what it was shown.
        confirmation = confirm_attributes(
            inspect_csv(data, _last_run_metadata(db, system_id)), attribute_list,
            via_ui=confirm == "1", actor=_authenticated_actor(current_user), now=now,
            confirm_sha256=confirm_sha256, removal_reason=removal_reason, uncovered_reason=uncovered_reason,
        )
        result = run_fairness(
            data,
            outcome=outcome,
            prediction=prediction or None,
            score=score or None,
            attributes=attribute_list,
            favorable_label=favorable_label or None,
        )
    except FairnessRunError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    evidence_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    title = f"Fairness test on {', '.join(attribute_list)} ({result['rows']} rows)"
    metadata = {
        "provenance_class": "measured",
        "run_id": run_id,
        "file_name": file.filename,
        "file_sha256": confirmation["fileSha256"],
        "mapping": result["mapping"],
        "attribute_confirmation": confirmation,
        "thresholds": result["thresholds"],
        "computed_at": now,
        "library": "fairness_library.metrics",
    }
    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, system_id, org_id, evidence_type, title, source, content_json, confidence, status, uploaded_by, metadata_json, captured_at, created_at) "
            "VALUES (:id, :system_id, :org_id, :evidence_type, :title, :source, :content_json, :confidence, :status, :uploaded_by, :metadata_json, :captured_at, :created_at)"
        ),
        {
            "id": evidence_id,
            "system_id": system_id,
            "org_id": _caller_org(http),
            "evidence_type": "fairness_test",
            "title": title,
            "source": RUN_SOURCE,
            "content_json": json.dumps(result),
            "confidence": result["evidence_confidence"],
            "status": "collected",
            "uploaded_by": _authenticated_actor(current_user),
            "metadata_json": json.dumps(metadata),
            "captured_at": now,
            "created_at": now,
        },
    )
    kept = False
    if keep_for_agent == "1" and confirmation["confirmed"]:
        from api.routes.autopilot import keep_source  # autopilot imports this module

        keep_source(
            db, _caller_org(http), system_id, "fairness", kind="upload", file_name=file.filename, content=data,
            actor=_authenticated_actor(current_user), basis={"evidenceId": evidence_id, "mapping": result["mapping"]},
        )
        kept = True
    db.commit()
    return {
        "runId": run_id,
        "keptForAgent": kept,
        "evidenceId": evidence_id,
        "systemId": system_id,
        "title": title,
        "result": result,
        "confirmation": _confirmation_summary(confirmation),
        "gate": _gate_payload(db, system_id, system.risk_tier),
    }


@router.get("/systems/{system_id}/fairness-runs")
def list_fairness_runs(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    rows = db.execute(
        text(
            "SELECT id, title, content_json, confidence, metadata_json, created_at, source FROM governance_evidence "
            "WHERE system_id = :id AND evidence_type = 'fairness_test' ORDER BY created_at DESC LIMIT 20"
        ),
        {"id": system_id},
    ).fetchall()
    runs: List[Dict[str, Any]] = []
    for row in rows:
        content = json.loads(row[2] or "{}")
        runs.append(
            {
                "evidenceId": row[0],
                "title": row[1],
                "rows": content.get("rows"),
                "allChecksPass": content.get("all_checks_pass"),
                "attributes": [
                    {
                        "attribute": a.get("attribute"),
                        "disparateImpactRatio": a.get("disparate_impact_ratio"),
                        "checks": a.get("checks"),
                        # Checks that pass with the value past its threshold: the difference was not significant.
                        "passedOnSignificance": [k for k, ok in (a.get("checks") or {}).items() if ok and (a.get(k) or {}).get("crosses_threshold")],
                    }
                    for a in content.get("attributes", [])
                ],
                "confidence": row[3],
                # Only this router writes a confirmation; generic evidence routes store client metadata verbatim.
                "confirmation": _confirmation_summary(json.loads(row[4] or "{}").get("attribute_confirmation")) if row[6] == RUN_SOURCE else None,
                "createdAt": row[5],
            }
        )
    return runs


@router.get("/systems/{system_id}/clause-map")
def get_clause_map(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """The release gate read per framework clause, via the catalogue's common-control crosswalk.

    Scoped to the frameworks confirmed for the system; every framework while none are confirmed.
    """
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    system = _system_row(db, system_id)
    applicability, _ = _system_applicability(db, system_id)
    confirmed = [{"key": f["key"], "name": f.get("name") or f["key"]} for f in (applicability or {}).get("frameworks") or [] if isinstance(f, dict) and f.get("key")]
    keys = [f["key"] for f in confirmed]
    payload = clause_map(_gate_payload(db, system_id, system.risk_tier), frameworks=keys or None)
    payload["systemId"] = system_id
    payload["scoped"] = bool(keys)
    # Every confirmed framework, including those with no crosswalk to the gate checks (absent from ``frameworks``).
    payload["confirmed"] = confirmed
    return payload


@router.get("/systems/{system_id}/seals")
def get_decision_seals(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Every seal taken at a release decision, each verified against the evidence as it is now."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    return list_seals(db, system_id)


@router.get("/systems/{system_id}/gate")
def get_release_gate(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    system = _system_row(db, system_id)
    return _gate_payload(db, system_id, system.risk_tier)


class ReleaseGateSettings(BaseModel):
    environmentalGate: bool


@router.get("/release-gate/settings", response_model=ReleaseGateSettings)
def get_release_gate_settings(http: Request, m: OrgMembership = Depends(org_member), db: Session = Depends(get_db)):
    """Which checks this organisation's release gate weighs. Any member may read it."""
    from src.application.services.environmental_service import environmental_gate_enabled

    return {"environmentalGate": environmental_gate_enabled(db, m.org_id)}


@router.put("/release-gate/settings", response_model=ReleaseGateSettings)
def set_release_gate_settings(
    body: ReleaseGateSettings, http: Request, m: OrgMembership = Depends(org_member), db: Session = Depends(get_db)
):
    """Owners and admins choose whether environmental impact counts in release decisions; each change is audited."""
    if str(m.role).lower() not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only an owner or admin of the organisation can change the release gate")
    db.execute(
        text(
            "UPDATE organizations SET metadata = COALESCE(metadata::jsonb, '{}'::jsonb) || jsonb_build_object('environmentalGate', CAST(:on AS boolean)), "
            "updated_at = NOW() WHERE id::text = :id"
        ),
        {"on": body.environmentalGate, "id": m.org_id},
    )
    db.execute(
        text(
            "INSERT INTO org_audit_logs (id, org_id, user_id, action, resource_type, resource_id, changes, status, ip_address, user_agent, created_at) "
            "VALUES (:id, :org, :user, :action, 'organization', :org, CAST(:changes AS json), 'success', :ip, :ua, NOW())"
        ),
        {
            "id": str(uuid.uuid4()), "org": m.org_id, "user": m.user_id,
            "action": "release_gate_environmental_" + ("on" if body.environmentalGate else "off"),
            "changes": json.dumps({"environmentalGate": body.environmentalGate}),
            "ip": http.client.host if http.client else None, "ua": http.headers.get("user-agent"),
        },
    )
    db.commit()
    return {"environmentalGate": body.environmentalGate}


def _org_systems(db: Session, http: Request) -> List[Any]:
    # Retired systems leave the live estate; their files stay readable one by one.
    return db.execute(
        text("SELECT id, name, risk_tier FROM governance_ai_systems WHERE org_id = :org AND COALESCE(lifecycle_stage, '') <> 'retired'"),
        {"org": _caller_org(http)},
    ).fetchall()


@router.get("/estate/gates")
def get_estate_gates(
    http: Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """The release gate of every system in the caller's org: verdict, confidence and checks, without explain and path."""
    _ensure_tables(db)
    out = []
    # ponytail: N gate computations (~10 queries each); precompute on evidence write if estates pass ~100 systems.
    for row in _org_systems(db, http):
        gate = _gate_payload(db, row.id, row.risk_tier)
        out.append({
            "systemId": row.id, "verdict": gate["verdict"], "confidence": gate["confidence"], "band": gate["band"], "approvalStatus": gate["approvalStatus"],
            "checks": [{k: v for k, v in c.items() if k != "detail"} for c in gate["checks"]],
        })
    return out


WEAKEST_FIRST = ("fails", "stale", "open", "none", "planned", "estimated", "partial", "attested", "proven")  # none: nothing reaches the clause


def _weakness(state: str) -> int:
    return WEAKEST_FIRST.index(state) if state in WEAKEST_FIRST else WEAKEST_FIRST.index("open")


def _plan_frameworks(db: Session, org_id: str) -> List[str]:
    """The frameworks the organisation chose in its governance plan; [] before it has a plan."""
    try:
        row = db.execute(text("SELECT profile_json FROM governance_plans WHERE org_id = :org"), {"org": org_id}).fetchone()
    except Exception:  # the plan table is created on first use of the plan
        db.rollback()
        return []
    chosen = (_load_json_value(row[0], {}).get("frameworks") or {}).get("value") if row else None
    return [k for k in chosen if isinstance(k, str)] if isinstance(chosen, list) else []


@router.get("/estate/frameworks")
def get_estate_frameworks(
    http: Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """The frameworks the organisation follows and, per framework, the weakest state of each tracked requirement.

    A framework is followed when the plan chose it or a system confirmed it. A system that has not confirmed its
    frameworks inherits the plan's; a system that confirmed a list without a plan framework has opted out of it.
    One gate computation per system, shared by every framework it answers to.
    """
    _ensure_tables(db)
    catalogue = _catalogue()["frameworks"]
    plan = [k for k in _plan_frameworks(db, _caller_org(http)) if k in catalogue]
    worst: Dict[str, Dict[str, str]] = {k: {} for k in plan}
    systems: Dict[str, int] = {k: 0 for k in plan}
    inherited: Dict[str, int] = {k: 0 for k in plan}
    confirmed_by: Dict[str, int] = {}
    unconfirmed = 0
    for row in _org_systems(db, http):
        applicability, _ = _system_applicability(db, row.id)
        if applicability is None:
            unconfirmed += 1
            keys = list(plan)
            for key in keys:
                inherited[key] += 1
        else:
            keys = [f["key"] for f in applicability.get("frameworks") or [] if isinstance(f, dict) and f.get("key") in catalogue]
            for key in keys:
                confirmed_by[key] = confirmed_by.get(key, 0) + 1
        if not keys:
            continue
        payload = clause_map(_gate_payload(db, row.id, row.risk_tier), frameworks=keys)
        cells = {fw["key"]: {c["key"]: c["cell"] for c in fw["clauses"]} for fw in payload["frameworks"]}
        for key in keys:
            systems[key] = systems.get(key, 0) + 1
            fw_worst = worst.setdefault(key, {})
            for req, state in cells.get(key, {}).items():
                if req not in fw_worst or _weakness(state) < _weakness(fw_worst[req]):
                    fw_worst[req] = state
    out = []
    for key, count in systems.items():
        states: Dict[str, int] = {}
        for state in worst[key].values():
            states[state] = states.get(state, 0) + 1
        out.append({
            "key": key, "systems": count, "tracked": len(tracked_requirements(key)), "states": states,
            "source": "plan" if key in plan else "system", "inherited": inherited.get(key, 0), "confirmed": confirmed_by.get(key, 0),
        })
    return {"unconfirmed": unconfirmed, "plan": plan, "frameworks": out}


@router.get("/frameworks/{framework_key}/systems")
def get_framework_systems(
    framework_key: str,
    http: Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Every requirement of one framework the gate speaks to, with one cell per system that confirmed the framework.

    Systems run from the highest tier down; ``cells`` follows that order. Systems with no confirmed applicability
    count as ``unconfirmed``, confirmed ones without this framework as ``notInScope``. When the plan chose this
    framework, unconfirmed systems inherit it and are in scope (``inherited`` counts them).
    """
    framework = _catalogue()["frameworks"].get(framework_key)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    _ensure_tables(db)
    followed_by_plan = framework_key in _plan_frameworks(db, _caller_org(http))
    systems, unconfirmed, not_in_scope, inherited = [], 0, 0, 0
    for row in _org_systems(db, http):
        applicability, _ = _system_applicability(db, row.id)
        if applicability is None:
            unconfirmed += 1
            if followed_by_plan:
                systems.append(row)
                inherited += 1
        elif any(isinstance(f, dict) and f.get("key") == framework_key for f in applicability.get("frameworks") or []):
            systems.append(row)
        else:
            not_in_scope += 1
    systems.sort(key=lambda r: (-TIERS.index(effective_tier(r.risk_tier, None)), r.name))
    # ponytail: one gate computation per system, as /estate/gates.
    clauses = []
    for row in systems:
        payload = clause_map(_gate_payload(db, row.id, row.risk_tier), frameworks=[framework_key])
        clauses.append({c["key"]: c for fw in payload["frameworks"] for c in fw["clauses"]})
    return {
        "framework": {"key": framework_key, "name": framework.get("name") or framework_key},
        "systems": [{"id": r.id, "name": r.name, "riskTier": r.risk_tier} for r in systems],
        "unconfirmed": unconfirmed,
        "notInScope": not_in_scope,
        "inherited": inherited,
        "followedByPlan": followed_by_plan,
        "requirements": [
            # a clause nothing reaches for a system has no cell, so the screen falls back to organisation coverage
            {"key": key, "cells": [{"state": by_key[key]["cell"], "checks": by_key[key]["checks"]} if by_key.get(key, {}).get("cell", "none") != "none" else None for by_key in clauses]}
            for key in tracked_requirements(framework_key)
        ],
    }


def _insert_evidence(db: Session, http: Request, current_user: TokenData, system_id: str, *, evidence_type: str, title: str, source: str, content: Dict[str, Any], confidence: float, metadata: Dict[str, Any]) -> str:
    now = datetime.now(timezone.utc).isoformat()
    evidence_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, system_id, org_id, evidence_type, title, source, content_json, confidence, status, uploaded_by, metadata_json, captured_at, created_at) "
            "VALUES (:id, :system_id, :org_id, :evidence_type, :title, :source, :content_json, :confidence, :status, :uploaded_by, :metadata_json, :captured_at, :created_at)"
        ),
        {
            "id": evidence_id, "system_id": system_id, "org_id": _caller_org(http), "evidence_type": evidence_type, "title": title,
            "source": source, "content_json": json.dumps(content), "confidence": confidence, "status": "collected",
            "uploaded_by": _authenticated_actor(current_user), "metadata_json": json.dumps({**metadata, "computed_at": now}),
            "captured_at": now, "created_at": now,
        },
    )
    db.commit()
    return evidence_id


def _latest_fairness_run(db: Session, system_id: str) -> Optional[Dict[str, Any]]:
    row = db.execute(
        text("SELECT id, content_json, created_at FROM governance_evidence WHERE system_id = :id AND evidence_type = 'fairness_test' ORDER BY created_at DESC LIMIT 1"),
        {"id": system_id},
    ).fetchone()
    if not row:
        return None
    content = json.loads(row[1] or "{}")
    content["_evidence_id"], content["_created_at"] = row[0], row[2]
    return content


@router.post("/systems/{system_id}/monitoring-runs")
def create_monitoring_run(
    system_id: str,
    http: Request,
    file: UploadFile = File(...),
    attributes: str = Form(..., description="comma-separated protected attribute columns"),
    prediction: Optional[str] = Form(None),
    score: Optional[str] = Form(None),
    favorable_label: Optional[str] = Form(None),
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Current production decisions against the latest fairness run: rate drift, impact ratio, score PSI."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    system = _system_row(db, system_id)
    baseline = _latest_fairness_run(db, system_id)
    attribute_list = [a.strip() for a in attributes.split(",") if a.strip()]
    try:
        result = run_monitoring(
            _read_upload(file),
            attributes=attribute_list,
            prediction=prediction or None,
            score=score or None,
            baseline=baseline,
            favorable_label=favorable_label or None,
        )
    except FairnessRunError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    title = f"Monitoring snapshot on {', '.join(attribute_list)} ({result['rows']} rows)"
    evidence_id = _insert_evidence(
        db, http, current_user, system_id,
        evidence_type="monitoring", title=title, source="fairmind.monitoring", content=result, confidence=result["evidence_confidence"],
        metadata={"provenance_class": "measured", "file_name": file.filename, "mapping": result["mapping"], "baseline_evidence_id": (baseline or {}).get("_evidence_id")},
    )
    watch = _watch(db, system_id)
    return {"evidenceId": evidence_id, "systemId": system_id, "title": title, "result": result, "watch": watch, "gate": _gate_payload(db, system_id, system.risk_tier)}


def _watch(db: Session, system_id: str) -> Dict[str, Any]:
    """Count consecutive drifting snapshots; open one finding when they reach the policy window.

    Never opens a second finding while one from the watch is still open, and never closes one.
    """
    policy = _monitoring_policy(db, system_id)
    rows = db.execute(
        text("SELECT id, content_json FROM governance_evidence WHERE system_id = :id AND evidence_type = 'monitoring' AND source = 'fairmind.monitoring' ORDER BY created_at DESC LIMIT 50"),
        {"id": system_id},
    ).fetchall()
    snapshots = [(row[0], json.loads(row[1] or "{}")) for row in rows]
    consecutive = 0
    for _, content in snapshots:
        if content.get("all_checks_pass") is not False:
            break
        consecutive += 1
    open_finding = db.execute(
        text("SELECT id FROM governance_risks WHERE system_id = :id AND source = :source AND status NOT IN :closed ORDER BY created_at DESC LIMIT 1").bindparams(bindparam("closed", expanding=True)),
        {"id": system_id, "source": WATCH_SOURCE, "closed": list(CLOSED_RISK_STATUSES)},
    ).fetchone()
    finding_id, opened = (open_finding[0] if open_finding else None), False
    if finding_id is None and consecutive >= policy["driftWindow"]:
        latest_id, latest = snapshots[0]
        failing = [a for a in latest.get("attributes", []) if not all((a.get("checks") or {}).values())]
        names = ", ".join(a.get("attribute", "") for a in failing) or "monitored attributes"
        metrics = "; ".join(
            f"{a.get('attribute')}: impact ratio {_fmt(a.get('disparate_impact_ratio'))}, max rate drift {_fmt(a.get('max_rate_drift'))}, worst PSI {_fmt(a.get('worst_psi'))}"
            for a in failing
        )
        now = datetime.now(timezone.utc).isoformat()
        finding_id, opened = str(uuid.uuid4()), True
        db.execute(
            text(
                "INSERT INTO governance_risks "
                "(id, system_id, title, severity, status, description, mitigation, likelihood, risk_score, source, categories_json, metadata_json, created_at, updated_at) "
                "VALUES (:id, :system_id, :title, :severity, :status, :description, :mitigation, :likelihood, :risk_score, :source, :categories_json, :metadata_json, :created_at, :updated_at)"
            ),
            {
                "id": finding_id, "system_id": system_id, "title": f"Sustained drift on {names}", "severity": "high", "status": "open",
                "description": f"The last {consecutive} monitoring snapshots all fall outside thresholds. Latest: {metrics}.",
                "mitigation": "Find what changed in the production population or the model, retrain or recalibrate, then record a fresh fairness run and monitoring snapshot.",
                "likelihood": "likely", "risk_score": _risk_score("high", "likely"), "source": WATCH_SOURCE,
                "categories_json": json.dumps(["monitoring", "drift"]),
                "metadata_json": json.dumps({"watch": True, "window": policy["driftWindow"], "snapshot_ids": [sid for sid, _ in snapshots[:consecutive]], "latest_snapshot_id": latest_id}),
                "created_at": now, "updated_at": now,
            },
        )
        db.commit()
    return {"policy": policy, "consecutiveDrifting": consecutive, "findingId": finding_id, "findingOpened": opened}


def _fmt(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.3f}"


class MonitoringPolicyRequest(BaseModel):
    cadenceHours: Optional[int] = Field(default=None, ge=1, le=2160)
    driftWindow: Optional[int] = Field(default=None, ge=2, le=10)


@router.get("/systems/{system_id}/monitoring-policy")
def get_monitoring_policy(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    return _monitoring_policy(db, system_id)


@router.put("/systems/{system_id}/monitoring-policy")
def put_monitoring_policy(
    system_id: str,
    body: MonitoringPolicyRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Cadence 1 to 2160 hours, drift window 2 to 10 snapshots; an omitted field keeps its current value."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    _system_row(db, system_id)
    current = _monitoring_policy(db, system_id)
    values = {
        "id": system_id,
        "cadence": body.cadenceHours if body.cadenceHours is not None else current["cadenceHours"],
        "window": body.driftWindow if body.driftWindow is not None else current["driftWindow"],
        "by": _authenticated_actor(current_user),
        "at": datetime.now(timezone.utc).isoformat(),
    }
    if current["isDefault"]:
        db.execute(
            text("INSERT INTO governance_monitoring_policies (system_id, cadence_hours, drift_window, updated_by, updated_at) VALUES (:id, :cadence, :window, :by, :at)"),
            values,
        )
    else:
        db.execute(
            text("UPDATE governance_monitoring_policies SET cadence_hours = :cadence, drift_window = :window, updated_by = :by, updated_at = :at WHERE system_id = :id"),
            values,
        )
    db.commit()
    return _monitoring_policy(db, system_id)


@router.get("/systems/{system_id}/monitoring-runs")
def list_monitoring_runs(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    rows = db.execute(
        text("SELECT id, title, content_json, confidence, created_at FROM governance_evidence WHERE system_id = :id AND evidence_type = 'monitoring' AND source = 'fairmind.monitoring' ORDER BY created_at DESC LIMIT 20"),
        {"id": system_id},
    ).fetchall()
    out = []
    for row in rows:
        content = json.loads(row[2] or "{}")
        out.append({
            "evidenceId": row[0], "title": row[1], "rows": content.get("rows"), "allChecksPass": content.get("all_checks_pass"),
            "overallPsi": content.get("overall_psi"),
            "attributes": [{"attribute": a.get("attribute"), "disparateImpactRatio": a.get("disparate_impact_ratio"), "maxRateDrift": a.get("max_rate_drift"), "worstPsi": a.get("worst_psi"), "checks": a.get("checks")} for a in content.get("attributes", [])],
            "confidence": row[3], "createdAt": row[4],
        })
    return out


class AttestationRequest(BaseModel):
    check: str = Field(pattern="^(data_governance|human_oversight|monitoring|environmental)$")
    statement: str = Field(min_length=12, max_length=2000)
    reference: Optional[str] = Field(default=None, max_length=500)


@router.post("/systems/{system_id}/attestations")
def create_attestation(
    system_id: str,
    body: AttestationRequest,
    http: Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """A named person states that a gate check is satisfied. Manual provenance: it attests, it never proves."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    system = _system_row(db, system_id)
    evidence_type, title = ATTESTABLE_CHECKS[body.check]
    evidence_id = _insert_evidence(
        db, http, current_user, system_id,
        evidence_type=evidence_type, title=title, source="attestation",
        content={"statement": body.statement, "reference": body.reference, "attested_by": _authenticated_actor(current_user)},
        confidence=ATTESTATION_CONFIDENCE,
        metadata={"provenance_class": "manual", "check": body.check},
    )
    return {"evidenceId": evidence_id, "systemId": system_id, "check": body.check, "gate": _gate_payload(db, system_id, system.risk_tier)}
