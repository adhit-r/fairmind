"""Run a catalogue evaluation on uploaded files and keep the result as measured evidence.

GET  /evaluations/{id}/engine        the files and settings the engine takes; 404 when FairMind cannot run it
POST /evaluations/{id}/runs          multipart: system_id, params (JSON), source, then one file per slot;
                                     source=connection reads the organisation's agent platform instead of files,
                                     source=traces reads the system's live runs of the last week (agent_traces.TRACE_READERS),
                                     with any slot in agent_traces.TRACE_UPLOADS as an optional file beside them,
                                     source=fairmind reads records FairMind already holds for the system (eval_engines.stored.READERS),
                                     mode=live runs an evaluation's alternate behaviour test
GET  /evaluations/{id}/runs          recent runs, optionally for one AI system
GET  /evaluation-runs/{evidence_id}  one run in full
GET  /systems/{system_id}/evaluation-runs   recent runs of every evaluation for one AI system
GET  /evaluation-jobs/{job_id}       a behaviour test in progress
GET  /evaluation-jobs/{job_id}/prompts   for a runner: the job and the prompts waiting for the system's answer
POST /evaluation-jobs/{job_id}/answers   for a runner: the system's answers to those prompts

A behaviour test (an engine with live set) calls the AI system under test and the organisation's
model as judge, which takes longer than Cloudflare's 100-second request limit allows. Its POST answers
202 with a job at once and the run continues in the background; the job reports progress and, when it
is done, the evidence id of the stored run.

A system whose connection is via=runner sits on the customer's private network. Its run is started by
the CLI inside that network with runner=1 (`fairmind eval run --live --local`); the job runs here as
usual, but each prompt to the system waits until the runner picks it up, calls the system and posts the
answer. Only outbound https from the customer; the judge and the stored evidence stay here.

Mounted under /api/v1/packs beside the packs router and sharing its organisation checks.
"""

import asyncio
import functools
import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import anyio
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import insert, select, text
from sqlalchemy.orm import Session

from api.routes.ai_governance import CLOSED_RISK_STATUSES, _ensure_tables, _load_json_value, _risk_score, _utc_now_iso
from api.routes import llm, platform_connections
from api.routes.agent_traces import (LIVE_RUNS, TRACE_ENGINES, TRACE_READERS, TRACE_UPLOADS, Insufficient, has_runs_this_week,
                                     read_live_runs, save_explanations)
from api.routes.packs import AGENT_SCHEMA, AGENT_SYSTEM, _ai_row, _manager, _member, _require_org_system, _stored_connection
from api.routes.pack_catalogue import EVALUATIONS, VERSION as CATALOGUE_VERSION
from api.routes.system_targets import MAX_ANSWER_BYTES, TIMEOUT_S, Target, TargetError, ask, runner_command, stored_target
from database.connection import get_db
from database.governance_models import GovernanceAISystem, GovernanceEvidenceRun, GovernanceRisk
from src.application.services.eval_engines import ALTERNATES, ENGINE_VERSION, REGISTRY, EngineError, Judge
from src.application.services.eval_engines.common import matches_schema, result
from src.application.services.eval_engines.behaviour import GEN_SYSTEM, CallError, Live
from src.application.services.eval_engines.platform import load_export
from src.application.services.eval_engines.stored import READERS as STORED_READERS
from src.application.services.governance_assurance_service import CATALOGUE_RUN_SCHEMA, GovernanceAssuranceService, OrgMembership
from src.application.services.system_kinds import fit, system_kind

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
EVIDENCE_TYPE = "evaluation_run"
STALE_AFTER = timedelta(minutes=5)  # a running job that has not reported for this long died with its worker
RUNNER_GONE_S = 60  # a runner that has not asked for prompts for this long has stopped
RUNNER_ANSWER_S = TIMEOUT_S + 30  # the runner's own call to the system, plus its round trips to FairMind
RUN_RESULT = {"passed": "passed", "failed": "failed", "insufficient": "insufficient_data"}
PLATFORM = "claude_managed_agents"  # ponytail: the one connector; take it from the form when a second platform lands
PLATFORM_PROVIDER = "anthropic"  # the llm provider whose models run on PLATFORM
# Sample-size floors: a smaller group is listed but skipped, so raising one hides more groups and loosens the test.
FLOORS = ("min_support", "min_rows", "min_slice")


def _vacuous(evaluation_id: str, name: str, value: float, params: Dict[str, Any]) -> bool:
    """An agreed setting with no catalogue default that accepts every result."""
    if name == "max_rate":
        return value >= 100  # a violation rate of 100%
    if name != "baseline":
        return False
    if evaluation_id == "EV-FAI-05":
        return abs(value) >= 2  # a ceiling on WEAT effect size, which lies within -2 to 2
    if evaluation_id == "EV-TST-01" and str(params.get("task") or "").lower() == "regression":
        return False  # a ceiling on MAE: 0 is the strictest, and no finite value accepts everything
    return value <= 0  # a floor on accuracy or success rate


def _engine(evaluation_id: str, mode: str = ""):
    if evaluation_id not in EVALUATIONS:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    engine = REGISTRY.get(evaluation_id)
    if mode == "live" and not (engine and engine.live):  # live mode: the behaviour test, registered or as an alternate
        engine = ALTERNATES.get(evaluation_id)
    if not engine:
        raise HTTPException(status_code=404, detail="FairMind cannot run this evaluation yet")
    return engine


def _judge(db: Session, org_id: str) -> Optional[Judge]:
    """The organisation's own model as a judge, called from the engine's worker thread; None when none is set.
    judge.connection is that model and judge.calls counts its verdicts, so the run records who judged."""
    row = _ai_row(db, org_id)
    if not row or not row["enabled"]:
        return None
    conn = _stored_connection(row)

    def judge(system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        judge.calls += 1
        try:
            answer = anyio.from_thread.run(functools.partial(llm.complete, conn, system, user, schema, deterministic=True))[0]
        except llm.LLMError:
            # ponytail: the provider's reason is dropped here; the AI provider test in settings shows it
            raise EngineError("Your model could not judge this; test it under organization settings, AI provider")
        if not matches_schema(answer, schema):  # a missing key or "false" for false is no verdict, never a pass
            raise EngineError("Your model's answer was not in the expected format; test it under organization settings, AI provider")
        return answer

    judge.connection, judge.calls = conn, 0
    return judge


def _host(url: str) -> Optional[str]:
    return urlparse(url or "").hostname


def _judge_json(conn, shares: Optional[bool]) -> Dict[str, Any]:
    """Who judged a run; sharesProviderWithSystem is None when the system under test's provider is unknown."""
    return {"provider": conn.provider.id, "model": conn.model, "sharesProviderWithSystem": shares}


def _loosened(engine, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Threshold settings looser than the catalogue default the engine declares, or an agreed setting that accepts anything."""
    out = []
    for p in engine.params:
        try:
            value = float(params[p.name])
        except (KeyError, TypeError, ValueError):
            continue  # unset, or not a number: the engine uses its default or rejects it
        up = p.name.startswith("max_") or p.name in ("psi_limit", "tolerance", *FLOORS)
        down = (p.name.startswith("min_") and p.name not in FLOORS) or p.name == "similarity"
        if p.kind == "number" and isinstance(p.default, (int, float)) and ((up and value > p.default) or (down and value < p.default)):
            out.append({"param": p.name, "value": value, "catalogue": p.default})
        elif p.default is None and _vacuous(engine.id, p.name, value, params):
            out.append({"param": p.name, "value": value, "catalogue": None})
    return out


def _record(engine, evaluation_id: str, path: str, files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    """What a run needs to be checked or repeated: a sha256 of every input, the engine and catalogue versions, and any loosened threshold."""
    loosened = _loosened(engine, params)
    return {
        "inputs": {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()},
        "engine": {"id": evaluation_id, "path": path, "catalogueVersion": CATALOGUE_VERSION, "codeVersion": ENGINE_VERSION},
        **({"thresholdLoosened": loosened} if loosened else {}),
    }


def _run_json(row, full: bool) -> Dict[str, Any]:
    content = json.loads(row["content_json"] or "{}")
    out = {
        "id": row["id"],
        "evaluationId": content.get("evaluationId"),
        "systemId": row["system_id"],
        "systemName": row["system_name"],
        "status": content.get("status"),
        "summary": content.get("summary"),
        "metrics": content.get("metrics", {}),
        "files": content.get("files", {}),
        "source": content.get("source", "upload"),
        "createdAt": row["created_at"],
        "createdBy": row["uploaded_by"],
    }
    if content.get("judge"):
        out.update({"judge": content["judge"], "target": content.get("target")})
    # runs stored before provenance classes carry none
    out.update({"provenance": content.get("provenance"), "thresholdLoosened": content.get("thresholdLoosened"), "partialRead": bool(content.get("partialRead"))})
    if full:
        out.update({"params": content.get("params", {}), "detail": content.get("detail", []), "detailTotal": content.get("detailTotal", 0),
                    "inputs": content.get("inputs"), "engine": content.get("engine"), "probes": content.get("probes")})
    return out


_RUN_COLS = (
    "SELECT e.id, e.system_id, e.content_json, e.created_at, e.uploaded_by, s.name AS system_name "
    "FROM governance_evidence e JOIN governance_ai_systems s ON s.id = e.system_id "
)


def system_setup(db: Session, org_id: str, system_id: str) -> Dict[str, Any]:
    """The system's kind and which ways of running it are set up; 404 for a system outside the organisation."""
    _ensure_tables(db)
    row = db.execute(text("SELECT org_id FROM governance_ai_systems WHERE id = :id"), {"id": system_id}).fetchone()
    if not row or str(row[0]) != org_id:
        raise HTTPException(status_code=404, detail="AI system not found")
    target = db.execute(text("SELECT fields_json FROM governance_ai_system_targets WHERE system_id = :id"), {"id": system_id}).first()
    return {
        "kind": system_kind(db, system_id),
        "calls_system": target is not None,
        # the runner inside the customer's network calls the system; a run started here cannot (stored_target, Target.via_runner)
        "via_runner": target is not None and json.loads(target[0] or "{}").get("via") == "runner",
        "live_runs": has_runs_this_week(db, system_id),
        "platform": db.execute(
            text("SELECT 1 FROM org_platform_connections WHERE org_id = :org AND platform = :p"), {"org": org_id, "p": PLATFORM}
        ).first() is not None,
        # the evaluations whose inputs FairMind already holds for this system
        "fairmind_data": frozenset(ev for ev, r in STORED_READERS.items() if r.exists(db, org_id, system_id)),
    }


REPLAY_VIA_RUNNER = "This system is called by your runner inside your network, and FairMind replays live runs only on a connection it calls itself"


def fit_and_ways(evaluation_id: str, setup: Dict[str, Any]) -> Dict[str, Any]:
    """Whether the evaluation fits the system's kind, and each way FairMind can run it with whether that way is ready."""
    engines = [e for e in (REGISTRY.get(evaluation_id), ALTERNATES.get(evaluation_id)) if e]
    has = {
        "calls_system": any(e.live == "target" for e in engines),
        "live_runs": evaluation_id in TRACE_READERS,
        "platform": any(e.platform for e in engines),
        "fairmind_data": evaluation_id in STORED_READERS,
        "files": any(e.slots and not e.live for e in engines),  # a live engine's slots are optional extra probes
    }
    ready = {**setup, "fairmind_data": evaluation_id in setup.get("fairmind_data", ())}
    ways = [{"way": w, "ready": ready.get(w, True)} for w, ok in has.items() if ok]
    # an engine of its own for live runs replays them on the system's connection, so it needs a connection FairMind calls itself
    for way in ways:
        if way["way"] == "live_runs" and evaluation_id in TRACE_ENGINES:
            if setup.get("via_runner"):
                way.update(ready=False, reason=REPLAY_VIA_RUNNER)
            elif not setup["calls_system"]:
                way["ready"] = False
    return {"fit": fit(EVALUATIONS[evaluation_id].appliesTo, setup["kind"]), "ways": ways}


@router.get("/evaluations/{evaluation_id}/engine")
def get_engine(evaluation_id: str, system: Optional[str] = Query(default=None, min_length=1), m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    alternate = ALTERNATES.get(evaluation_id)
    own = TRACE_ENGINES.get(evaluation_id)  # an engine of its own for live runs, whose settings differ from the upload's
    out = {**_engine(evaluation_id).spec(), "alternate": alternate.spec() if alternate else None, "liveRuns": evaluation_id in TRACE_READERS,
           "liveRunsEngine": own.spec() if own else None,
           # files a person may add to a run on live runs, with help for the form
           "liveRunsUploads": [{"name": n, "help": h} for n, h in TRACE_UPLOADS.get(evaluation_id, {}).items()]}
    if system:
        setup = system_setup(db, m.org_id, system)
        out.update({"kind": setup["kind"], **fit_and_ways(evaluation_id, setup)})
    return out


@router.post("/evaluations/{evaluation_id}/runs")
async def create_run(
    evaluation_id: str,
    request: Request,
    background: BackgroundTasks,
    m: OrgMembership = Depends(_manager),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    form = await request.form()
    engine = _engine(evaluation_id, str(form.get("mode") or ""))
    system_id = str(form.get("system_id") or "")
    system = db.execute(
        text("SELECT org_id, name, risk_tier, lifecycle_stage FROM governance_ai_systems WHERE id = :id"), {"id": system_id}
    ).fetchone()
    if not system or str(system[0]) != m.org_id:
        raise HTTPException(status_code=404, detail="AI system not found")
    try:
        params = json.loads(str(form.get("params") or "{}"))
        assert isinstance(params, dict)
    except (ValueError, AssertionError):
        raise HTTPException(status_code=422, detail="params must be a JSON object")
    source = str(form.get("source") or "upload")
    if (source not in ("upload", "connection", "traces", "fairmind") or (source == "connection" and not engine.platform)
            or (source == "traces" and evaluation_id not in TRACE_READERS) or (source == "fairmind" and (engine.live or evaluation_id not in STORED_READERS))):
        raise HTTPException(status_code=422, detail="source must be upload, connection for an evaluation that reads platform configuration, "
                            "traces for one that reads live runs, or fairmind for one that reads records FairMind holds")
    files, names, insufficient, partial = {}, {}, None, False
    if source == "fairmind":
        stored = STORED_READERS[evaluation_id]
        files = stored.read(db, m.org_id, system_id)
        if not files:
            raise HTTPException(status_code=409, detail=f"{stored.label}: none on file yet; upload the file instead")
        names = {name: stored.label for name in files}
    for slot in engine.slots if source == "upload" else [s for s in engine.slots if s.name in TRACE_UPLOADS.get(evaluation_id, {})]:
        upload = form.get(slot.name)
        if upload is None or not hasattr(upload, "read"):
            if slot.required and source == "upload":
                raise HTTPException(status_code=422, detail=f"Add the {slot.label.lower()}")
            continue
        raw = await upload.read(MAX_UPLOAD_BYTES + 1)
        if len(raw) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"{slot.label} is over 25 MB")
        files[slot.name], names[slot.name] = raw, upload.filename
    if source == "traces":
        engine = TRACE_ENGINES.get(evaluation_id, engine)
        try:
            live, live_names, partial = read_live_runs(db, evaluation_id, system_id, params, frozenset(files))
            files, names = {**live, **files}, {**live_names, **names}
        except Insufficient as exc:  # runs arrived but lack what it reads: kept as insufficient, like an engine's own
            insufficient, names = result("insufficient", exc.detail, {}), {"traces": LIVE_RUNS}
    if engine.collect:
        files.update(engine.collect(db, m.org_id, system_id))
    for p in engine.params:
        if p.required and params.get(p.name) in (None, ""):
            raise HTTPException(status_code=422, detail=f"Set {p.label.lower()}")
    if engine.live:
        runner = str(form.get("runner") or "") in ("1", "true")
        return _start_job(db, background, m, evaluation_id, engine, system, system_id, files, names, params, runner,
                          use_target=source != "traces" or evaluation_id in TRACE_ENGINES)
    reads_platform = source == "connection" or engine.run is None
    judge = _judge(db, m.org_id) if (engine.judge if reads_platform else engine.file_judge) else None
    key = None
    if source == "connection":
        key = platform_connections.stored_key(db, m.org_id, PLATFORM)
        names = {"connection": platform_connections.PLATFORMS[PLATFORM]["name"]}
    db.rollback()  # hold no transaction open while the platform answers or the engine computes
    try:
        if reads_platform:
            snap = await platform_connections.snapshot(key) if key else load_export(files["export"])
            outcome = await run_in_threadpool(engine.platform, snap, params, judge)
        else:
            outcome = insufficient or await run_in_threadpool(engine.run, files, params, *((judge,) if engine.file_judge else ()))
    except platform_connections.PlatformError as exc:
        raise HTTPException(status_code=422, detail=platform_connections.public_message(exc))
    except EngineError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    judged = bool(judge and judge.calls)
    outcome = {
        **outcome, "params": params, "files": names, "source": source, **({"partialRead": True} if partial else {}),
        **_record(engine, evaluation_id, "platform" if reads_platform else "file", files, params),
        # a connection is read live from the platform; an export, an upload or records FairMind holds are computed from the file
        "provenance": {"class": "measured_live" if source == "connection" else "computed_from_upload", "modelJudged": judged},
        **({"judge": _judge_json(judge.connection, judge.connection.provider.id == PLATFORM_PROVIDER)} if judged else {}),
    }
    evidence_id = _store_run(db, m.org_id, m.user_id, system_id, evaluation_id, outcome)
    row = db.execute(text(_RUN_COLS + "WHERE e.id = :id"), {"id": evidence_id}).mappings().fetchone()
    return _run_json(row, full=True)


def _store_run(db: Session, org_id: str, user_id: str, system_id: str, evaluation_id: str, outcome: Dict[str, Any]) -> str:
    evidence_id = str(uuid.uuid4())
    provenance = outcome.get("provenance") or {}
    content = json.dumps({"evaluationId": evaluation_id, **outcome}, default=str)
    # The run row lists the run under Evidence > Evaluation runs and lets a reviewer map it to a control.
    # It is no Evidence Passport, so it has no passport revision; only a passed result can support a control.
    run_pk = str(uuid.uuid4())
    workspace_id = db.execute(
        select(GovernanceAISystem.workspace_id)
        .where(GovernanceAISystem.id == system_id, GovernanceAISystem.org_id == org_id)
        .with_for_update()  # serialize finding creation and retests for simultaneous runs of this system
    ).scalar_one()
    now = _utc_now_iso()
    db.execute(
        insert(GovernanceEvidenceRun.__table__).values(
            id=run_pk, org_id=org_id, system_id=system_id, workspace_id=workspace_id, passport_id=evidence_id,
            schema_version=CATALOGUE_RUN_SCHEMA, capability_state="insufficient_data" if outcome["status"] == "insufficient" else "validated",
            assurance_source="fairmind_internal", source_type="fairmind_evaluation", source_identifier=evaluation_id,
            run_id=evidence_id, content_hash=hashlib.sha256(content.encode()).hexdigest(),
            result=RUN_RESULT.get(outcome["status"], "unknown"),
            provenance_json=json.dumps({"evaluation": {"suite": {"name": f"{evaluation_id} {EVALUATIONS[evaluation_id].name}"}}}),
            captured_at=now, evidence_id=evidence_id, created_at=now,
        )
    )
    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, system_id, org_id, evidence_type, title, source, content_json, confidence, status, uploaded_by, metadata_json, source_run_id, captured_at, created_at) "
            "VALUES (:id, :system_id, :org_id, :type, :title, :source, :content, :confidence, 'collected', :by, :metadata, :run, :now, :now)"
        ),
        {
            "id": evidence_id,
            "system_id": system_id,
            "org_id": org_id,
            "type": EVIDENCE_TYPE,
            "title": f"{evaluation_id} {EVALUATIONS[evaluation_id].name}: {outcome['status']}",
            "source": "fairmind.eval_engines",
            "content": content,
            "run": run_pk,
            # Measured by the engine from the data itself; an insufficient run measured nothing.
            "confidence": 0.0 if outcome["status"] == "insufficient" else 1.0,
            "by": user_id,
            "metadata": json.dumps({
                "provenance_class": provenance.get("class", "computed_from_upload"), "model_judged": bool(provenance.get("modelJudged")),
                "engine": evaluation_id, "source": outcome.get("source", "upload"), "computed_at": now,
            }),
            "now": now,
        },
    )
    # a pass on thresholds looser than the catalogue's, or a zero-tolerance pass on part of the live runs,
    # shows its own result but proves nothing: no mappings, no resolved finding
    proves = outcome["status"] == "passed" and not outcome.get("thresholdLoosened") and not outcome.get("partialRead")
    if proves:  # proposes the ISO 42001 clauses this evaluation tests directly, for a reviewer to accept
        GovernanceAssuranceService(db).map_catalogue_run(org_id, system_id, run_pk, evidence_id, evaluation_id)
    # A failed run opens one finding for this evaluation on this system; a passing run resolves it.
    source = "fairmind.eval_engines"
    open_findings = db.scalars(
        select(GovernanceRisk).where(
            GovernanceRisk.system_id == system_id,
            GovernanceRisk.source == source,
            GovernanceRisk.status.not_in(CLOSED_RISK_STATUSES),
        ).with_for_update()
    ).all()
    matched = False
    for risk in open_findings:
        metadata = _load_json_value(risk.metadata_json, {})
        if not isinstance(metadata, dict) or metadata.get("evaluationId") != evaluation_id:
            continue
        matched = True
        # A previously shared retest remains attributable even after another attempt or closure.
        previous = metadata.get("retestEvidenceIds")
        attempts = list(previous) if isinstance(previous, list) else []
        attempts.extend([metadata.get("retestEvidenceId"), evidence_id])
        metadata["retestEvidenceIds"] = list(dict.fromkeys(
            attempt for attempt in attempts if isinstance(attempt, str) and attempt and attempt != metadata.get("evidenceId")
        ))
        metadata["retestEvidenceId"] = evidence_id
        if proves:
            risk.status = "resolved"
            metadata.pop("pendingAcceptance", None)
        risk.metadata_json = json.dumps(metadata)
        risk.updated_at = now
    if not matched and outcome["status"] == "failed":
        db.execute(
            text(
                "INSERT INTO governance_risks "
                "(id, system_id, title, severity, status, description, mitigation, likelihood, risk_score, source, categories_json, metadata_json, created_at, updated_at) "
                "VALUES (:id, :sys, :title, 'high', 'open', :description, :mitigation, 'likely', :score, :source, :categories, :metadata, :now, :now)"
            ),
            {
                "sys": system_id,
                "source": source,
                "now": now,
                "id": str(uuid.uuid4()),
                "title": f"{evaluation_id} {EVALUATIONS[evaluation_id].name} failed",
                "description": outcome.get("summary") or "The evaluation run failed.",
                "mitigation": "Fix what the run found, then run the evaluation again; a passing run resolves this finding.",
                "score": _risk_score("high", "likely"),
                "categories": json.dumps(["evaluation"]),
                "metadata": json.dumps({"evaluationId": evaluation_id, "evidenceId": evidence_id}),
            },
        )
    db.commit()
    return evidence_id


# --- behaviour tests: background jobs ------------------------------------------------------------


def _job_json(row) -> Dict[str, Any]:
    status, error = row["status"], row["error"]
    if status == "running" and datetime.now(timezone.utc) - datetime.fromisoformat(row["updated_at"]) > STALE_AFTER:
        status, error = "failed", "The run stopped when its server restarted; start it again"
    return {
        "id": row["id"],
        "evaluationId": row["evaluation_id"],
        "systemId": row["system_id"],
        "status": status,
        "phase": row["phase"],
        "done": row["done"],
        "total": row["total"],
        "error": error,
        "evidenceId": row["evidence_id"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _job_row(db: Session, job_id: str):
    return db.execute(text("SELECT * FROM governance_evaluation_jobs WHERE id = :id"), {"id": job_id}).mappings().fetchone()


def _update_job(db: Session, job_id: str, **values) -> None:
    sets = ", ".join(f"{k} = :{k}" for k in values)
    db.execute(text(f"UPDATE governance_evaluation_jobs SET {sets}, updated_at = :now WHERE id = :id"), {**values, "now": _utc_now_iso(), "id": job_id})
    db.commit()


def _previous_metrics(db: Session, system_id: str, evaluation_id: str) -> Optional[Dict[str, Any]]:
    row = db.execute(
        text(_RUN_COLS + "WHERE e.system_id = :sys AND e.evidence_type = :type AND e.content_json LIKE :tag ORDER BY e.created_at DESC LIMIT 1"),
        {"sys": system_id, "type": EVIDENCE_TYPE, "tag": f'%"evaluationId": "{evaluation_id}"%'},
    ).mappings().fetchone()
    return json.loads(row["content_json"] or "{}").get("metrics") if row else None


def _start_job(db, background, m, evaluation_id, engine, system, system_id, files, names, params, runner=False, use_target=True):
    """Check the judge and the target now, so a missing setting fails the request and not the job; then run in the background."""
    row = _ai_row(db, m.org_id)
    if not row or not row["enabled"]:
        raise HTTPException(status_code=409, detail="Behaviour tests use your organisation's AI provider as the judge; set one up in organisation settings")
    judge = _stored_connection(row)
    target = stored_target(db, m.org_id, system_id) if engine.live == "target" and use_target else None
    if target and target.via_runner and not runner:
        raise HTTPException(status_code=409, detail="This system is on your private network, so the runner calls it. Run this from a "
                            f"machine that can reach it: {runner_command(evaluation_id, system_id)}")
    if target and runner and not target.via_runner:
        raise HTTPException(status_code=422, detail="FairMind calls this system directly; run it without --local, or set its connection to a runner")
    facts = {"name": system[1], "risk_tier": system[2], "lifecycle_stage": system[3]}
    previous = _previous_metrics(db, system_id, evaluation_id)
    now = _utc_now_iso()
    job_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_evaluation_jobs (id, org_id, system_id, evaluation_id, status, phase, done, total, created_by, created_at, updated_at) "
            "VALUES (:id, :org, :sys, :ev, 'running', 'Starting', 0, 0, :by, :now, :now)"
        ),
        {"id": job_id, "org": m.org_id, "sys": system_id, "ev": evaluation_id, "by": m.user_id, "now": now},
    )
    db.commit()
    background.add_task(
        _run_job, db.get_bind(), job_id, m.org_id, m.user_id, system_id, evaluation_id, engine, files, names, params, judge, target, facts, previous
    )
    return JSONResponse(status_code=202, content={"job": _job_json(_job_row(db, job_id))})


def make_live(target: Optional[Target], judge, facts: Dict[str, Any], progress, previous=None, ask_override=None) -> Live:
    """The calls an engine makes: the system under test, the judge (the organisation's model) and FairMind's agent."""

    async def call_target(prompt: str) -> str:
        try:
            return await ask(target, prompt, attempts=llm.RETRY_ATTEMPTS)
        except (TargetError, llm.LLMError) as e:
            raise CallError(f"System under test: {e}")

    async def call_judge(system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        live.judged += system != GEN_SYSTEM
        try:
            return (await llm.complete(judge, system, user, schema, attempts=llm.RETRY_ATTEMPTS, deterministic=True))[0]
        except llm.LLMError as e:
            raise CallError(f"Judge: {e}")

    async def call_agent(agent_facts: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return (await llm.complete(judge, AGENT_SYSTEM, json.dumps(agent_facts, default=str, sort_keys=True), AGENT_SCHEMA,
                                       attempts=llm.RETRY_ATTEMPTS, deterministic=True))[0]
        except llm.LLMError as e:
            raise CallError(f"FairMind agent: {e}")

    live = Live(
        ask=ask_override or call_target,
        judge=call_judge,
        progress=progress,
        system=facts,
        system_prompt=target.system_prompt if target else "",
        intended_use=target.intended_use if target else "",
        previous=previous,
        agent=call_agent,
    )
    return live


async def _run_job(bind, job_id, org_id, user_id, system_id, evaluation_id, engine, files, names, params, judge, target: Optional[Target], facts, previous):
    db = Session(bind=bind)
    lock = asyncio.Lock()

    async def progress(done: int, total: int, phase: str) -> None:
        async with lock:  # probes run a few at a time; their reports share this session
            await run_in_threadpool(_update_job, db, job_id, done=done, total=total, phase=phase)

    relay = None
    if target and target.via_runner:
        relay = _RELAYS[job_id] = _Relay(asyncio.get_running_loop())
    live = make_live(target, judge, facts, progress, previous, relay.ask if relay else None)
    try:
        outcome = await engine.run(files, params, live)
        traces = "traces" in files
        # FairMind's agent runs on the judge's own connection; live runs say nothing of the provider behind them
        shares = (_host(judge.base_url) == _host(target.url)) if target else None if traces else True
        outcome.update({
            "params": params,
            "files": names,
            "judge": _judge_json(judge, shares),
            "target": ({"kind": target.kind, "url": target.url, **({"via": "runner"} if target.via_runner else {})}
                       if target else {"kind": "live-runs"} if traces else {"kind": "fairmind-agent"}),
            **({"source": "traces"} if traces else {}),
            **_record(engine, evaluation_id, "live", files, params),
            # live runs read alone are records the system sent; replayed on the connection (EV-OVS-04), FairMind made the calls
            "provenance": {"class": "computed_from_upload" if traces and not target else "measured_live", "modelJudged": live.judged > 0},
            **({"probes": live.generated} if live.generated else {}),  # restricted suites never generate, so never land here
        })
        evidence_id = await run_in_threadpool(_store_run, db, org_id, user_id, system_id, evaluation_id, outcome)
        if "traces" in files and evaluation_id in TRACE_ENGINES:  # each run tested opens explained
            await run_in_threadpool(save_explanations, db, org_id, system_id, outcome["detail"], user_id, evidence_id)
        await run_in_threadpool(_update_job, db, job_id, status="done", phase="Done", evidence_id=evidence_id)
    except EngineError as e:
        await run_in_threadpool(_update_job, db, job_id, status="failed", error=str(e))
    except Exception:
        logger.exception("behaviour test %s for %s failed", evaluation_id, system_id)
        db.rollback()
        await run_in_threadpool(_update_job, db, job_id, status="failed", error="The run stopped on an unexpected error")
    finally:
        _RELAYS.pop(job_id, None)
        db.close()


# --- the runner: prompts out to the customer's network, answers back ------------------------------


@dataclass
class _Relay:
    """A runner job's prompts waiting for an answer. Futures belong to the job's event loop."""

    loop: asyncio.AbstractEventLoop
    seen: float = field(default_factory=time.monotonic)  # the runner's last request for prompts
    pending: Dict[str, Tuple[str, asyncio.Future]] = field(default_factory=dict)

    async def ask(self, prompt: str) -> str:
        if time.monotonic() - self.seen > RUNNER_GONE_S:
            raise CallError("System under test: the runner stopped answering")
        prompt_id, future = str(uuid.uuid4()), self.loop.create_future()
        self.pending[prompt_id] = (prompt, future)
        try:
            return await asyncio.wait_for(future, RUNNER_ANSWER_S)
        except asyncio.TimeoutError:
            raise CallError("System under test: the runner did not answer in time")
        finally:
            self.pending.pop(prompt_id, None)


# ponytail: in this process, like the background job itself; the API runs one worker (see the Dockerfile).
# Move to a table if it ever runs more.
_RELAYS: Dict[str, _Relay] = {}


class RunnerAnswer(BaseModel):
    id: str = Field(max_length=64)
    answer: Optional[str] = Field(default=None, max_length=MAX_ANSWER_BYTES)
    error: Optional[str] = Field(default=None, max_length=300)


class RunnerAnswers(BaseModel):
    answers: List[RunnerAnswer] = Field(max_length=50)


def _runner_job(db: Session, m: OrgMembership, job_id: str):
    _ensure_tables(db)
    row = _job_row(db, job_id)
    if not row or row["org_id"] != m.org_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return row, _RELAYS.get(job_id)


@router.get("/evaluation-jobs/{job_id}/prompts")
def runner_prompts(job_id: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    row, relay = _runner_job(db, m, job_id)
    if relay is None:
        return {"job": _job_json(row), "prompts": []}
    relay.seen = time.monotonic()
    waiting = [{"id": pid, "prompt": prompt} for pid, (prompt, future) in list(relay.pending.items()) if not future.done()]
    return {"job": _job_json(row), "prompts": waiting}


def _settle(future: asyncio.Future, answer: RunnerAnswer) -> None:
    if future.done():
        return
    if answer.error is not None or answer.answer is None:
        future.set_exception(CallError(f"System under test: {answer.error or 'the runner sent no answer'}"))
    else:
        future.set_result(answer.answer)


@router.post("/evaluation-jobs/{job_id}/answers")
def runner_answers(job_id: str, body: RunnerAnswers, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    _, relay = _runner_job(db, m, job_id)
    accepted = 0
    for answer in body.answers:
        entry = relay.pending.get(answer.id) if relay else None
        if entry:  # late or unknown ids are dropped: their prompt already failed or never existed
            relay.loop.call_soon_threadsafe(_settle, entry[1], answer)
            accepted += 1
    if relay:
        relay.seen = time.monotonic()
    return {"accepted": accepted}


@router.get("/evaluation-jobs/{job_id}")
def get_job(job_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _ensure_tables(db)
    row = _job_row(db, job_id)
    if not row or row["org_id"] != m.org_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_json(row)


@router.get("/evaluations/{evaluation_id}/runs")
def list_runs(
    evaluation_id: str,
    system_id: Optional[str] = Query(default=None, min_length=1),
    m: OrgMembership = Depends(_member),
    db: Session = Depends(get_db),
):
    if evaluation_id not in EVALUATIONS:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    _ensure_tables(db)
    if system_id is not None:
        _require_org_system(db, m.org_id, system_id)
    rows = db.execute(
        text(
            _RUN_COLS + "WHERE s.org_id = :org AND e.evidence_type = :type "
            "AND CAST(e.content_json AS jsonb) ->> 'evaluationId' = :evaluation_id "
            "AND (CAST(:sys AS text) IS NULL OR e.system_id = :sys) ORDER BY e.created_at DESC, e.id DESC LIMIT 20"
        ),
        {"org": m.org_id, "type": EVIDENCE_TYPE, "evaluation_id": evaluation_id, "sys": system_id},
    ).mappings().all()
    return [_run_json(r, full=False) for r in rows]


@router.get("/evaluation-runs/{evidence_id}")
def get_run(
    evidence_id: str,
    system_id: Optional[str] = Query(default=None, min_length=1),
    evaluation_id: Optional[str] = Query(default=None, min_length=1),
    m: OrgMembership = Depends(_member),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    row = db.execute(
        text(_RUN_COLS + "WHERE e.id = :id AND s.org_id = :org AND e.evidence_type = :type"),
        {"id": evidence_id, "org": m.org_id, "type": EVIDENCE_TYPE},
    ).mappings().fetchone()
    if not row or (system_id is not None and row["system_id"] != system_id):
        raise HTTPException(status_code=404, detail="Run not found")
    run = _run_json(row, full=True)
    if evaluation_id is not None and run["evaluationId"] != evaluation_id:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/systems/{system_id}/evaluation-runs")
def list_system_runs(system_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    """The system's recent catalogue runs, every evaluation, newest first: what its system file shows."""
    _ensure_tables(db)
    rows = db.execute(
        text(_RUN_COLS + "WHERE s.org_id = :org AND e.evidence_type = :type AND e.system_id = :sys ORDER BY e.created_at DESC LIMIT 20"),
        {"org": m.org_id, "type": EVIDENCE_TYPE, "sys": system_id},
    ).mappings().all()
    return [_run_json(r, full=False) for r in rows]
