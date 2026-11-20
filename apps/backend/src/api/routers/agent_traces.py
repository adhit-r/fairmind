"""Live traces from a running AI system or agent, with the reason it gave at each step.

POST   /ai-systems/{id}/traces               record or extend a trace; safe to call again as the run goes on
GET    /ai-systems/{id}/traces               the latest traces, each with its step count and rationale coverage
GET    /ai-systems/{id}/traces/summary       runs per day, the last run, and the latest evaluations that read live runs
GET    /ai-systems/{id}/traces/{trace_id}    one trace with its steps in order
DELETE /ai-systems/{id}/traces/{trace_id}

The customer's own code sends these (the SDK's record_trace), keyed by its own trace id and step ids, so
re-sending a step updates it instead of adding a second one. A step is a model call, a tool call, a
retrieval, a memory read or write, or a decision; its input and output are whatever JSON the caller has.

A rationale is the reason the system itself stated, on a step or on the whole trace. It is stored as
stated: nothing here checks that it reflects what the model computed. Coverage is the share of model
calls, tool calls and decisions that carry one. Mounted under /api/v1/packs beside the packs router.
"""

import csv
import io
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes.ai_governance import _ensure_tables, _utc_now_iso
from api.routes.packs import _manager, _member
from api.routes.system_targets import _system_or_404
from database.connection import get_db
from database.governance_models import _new_id
from src.application.services.governance_assurance_service import OrgMembership

router = APIRouter()

MAX_STEPS = 500  # per request; a longer run sends several requests
MAX_TEXT = 20_000  # characters kept of any one input, output or rationale
MAX_TRACE_STEPS = 10_000  # per trace, across all requests
DECISIONS = ("llm", "tool", "decision")  # the step kinds a rationale is expected on
Status = Literal["running", "ok", "error"]
WEEK = timedelta(days=7)  # the live runs an evaluation reads
BASELINE = timedelta(days=28)  # EV-MON-02 compares the week with the four weeks before it
SUMMARY_DAYS = 14
MAX_GROUNDED = 200  # EV-TST-03 judges at most this many runs, the newest; the engine's own probe limit


def _clean(s: str) -> str:
    """Without what PostgreSQL text cannot hold: NUL bytes and lone surrogates."""
    return s.replace("\x00", "").encode("utf-8", "replace").decode()


class _Body(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def _storable(cls, v: Any) -> Any:
        return _clean(v) if isinstance(v, str) else v


class StepBody(_Body):
    id: Optional[str] = Field(default=None, max_length=200)  # the caller's step id; send it to make re-sends update
    parentId: Optional[str] = Field(default=None, max_length=200)
    kind: Optional[Literal["llm", "tool", "retrieval", "memory", "decision", "other"]] = None  # other when never sent
    name: Optional[str] = Field(default=None, max_length=300)
    input: Any = None
    output: Any = None
    rationale: Optional[str] = None
    status: Optional[Status] = None  # ok when never sent
    error: Optional[str] = None
    startedAt: Optional[str] = Field(default=None, max_length=40)
    endedAt: Optional[str] = Field(default=None, max_length=40)


class TraceBody(_Body):
    traceId: str = Field(min_length=1, max_length=200, pattern=r"^[^/]+$")  # it is read back from the URL path
    name: Optional[str] = Field(default=None, max_length=300)
    status: Optional[Status] = None
    input: Any = None
    output: Any = None
    rationale: Optional[str] = None
    startedAt: Optional[str] = Field(default=None, max_length=40)
    endedAt: Optional[str] = Field(default=None, max_length=40)
    steps: List[StepBody] = Field(default_factory=list, max_length=MAX_STEPS)


def _text(value: Optional[str], cut: List[bool]) -> Optional[str]:
    """Plain text cut to MAX_TEXT; cut[0] records that something was shortened."""
    if value is not None and len(value) > MAX_TEXT:
        cut[0] = True
        return value[:MAX_TEXT]
    return value


def _clip(value: Any, cut: List[bool]) -> Optional[str]:
    """Any input or output as JSON text, so a string that looks like JSON comes back as the string it was."""
    return None if value is None else _text(_clean(json.dumps(value, ensure_ascii=False, default=str)), cut)


def _value(s: Optional[str]) -> Any:
    if s is None:
        return None
    try:
        return json.loads(s)
    except ValueError:
        return s  # JSON that was cut short


def _trace_row(db: Session, system_id: str, trace_id: str):
    if "\x00" in trace_id:
        return None
    return db.execute(
        text("SELECT * FROM governance_agent_traces WHERE system_id = :sid AND trace_id = :tid"), {"sid": system_id, "tid": trace_id}
    ).mappings().fetchone()


def _trace_json(row, steps: int, decisions: int, explained: int) -> Dict[str, Any]:
    return {
        "traceId": row["trace_id"],
        "name": row["name"],
        "status": row["status"],
        "input": _value(row["input"]),
        "output": _value(row["output"]),
        "rationale": row["rationale"],
        "startedAt": row["started_at"],
        "endedAt": row["ended_at"],
        "receivedAt": row["received_at"],
        "updatedAt": row["updated_at"],
        "truncated": bool(row["truncated"]),
        "stepCount": steps,
        # None when the trace has no model call, tool call or decision to explain
        "rationaleCoverage": round(explained / decisions, 3) if decisions else None,
    }


@router.post("/ai-systems/{system_id}/traces")
def record_trace(system_id: str, body: TraceBody, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _system_or_404(db, m.org_id, system_id)
    now, cut = _utc_now_iso(), [False]
    sent = {
        "name": body.name,
        "status": body.status,
        "input": _clip(body.input, cut),
        "output": _clip(body.output, cut),
        "rationale": _text(body.rationale, cut),
        "started_at": body.startedAt,
        "ended_at": body.endedAt,
    }
    # A later call that leaves a field out keeps what an earlier call stored.
    # status reads the parameter: excluded.status already holds the insert's 'running' default.
    keep = ", ".join(
        f"{c} = COALESCE(" + ("CAST(:status AS TEXT)" if c == "status" else f"excluded.{c}") + f", governance_agent_traces.{c})" for c in sent
    )
    pk = db.execute(
        text(
            "INSERT INTO governance_agent_traces (id, org_id, system_id, trace_id, name, status, input, output, rationale, "
            "started_at, ended_at, truncated, received_at, updated_at) VALUES (:id, :org, :sid, :tid, :name, COALESCE(:status, 'running'), "
            ":input, :output, :rationale, :started_at, :ended_at, :cut, :now, :now) "
            f"ON CONFLICT (system_id, trace_id) DO UPDATE SET {keep}, updated_at = excluded.updated_at RETURNING id"
        ),
        {"id": _new_id(), "org": m.org_id, "sid": system_id, "tid": body.traceId, "cut": False, "now": now, **sent},
    ).scalar()
    # ponytail: seq is arrival order, so two requests for one trace at the same moment can share numbers;
    # the read breaks ties by started_at. Take a row lock on the trace if strict ordering ever matters.
    seq = db.execute(text("SELECT COALESCE(MAX(seq), 0) FROM governance_agent_trace_steps WHERE trace_pk = :pk"), {"pk": pk}).scalar()
    if seq + len(body.steps) > MAX_TRACE_STEPS:
        db.rollback()
        raise HTTPException(status_code=413, detail=f"A trace holds at most {MAX_TRACE_STEPS} steps; start a new trace id")
    step_keep = ", ".join(
        f"{c} = COALESCE(" + (f"CAST(:{c} AS TEXT)" if c in ("kind", "name", "status") else f"excluded.{c}") + f", governance_agent_trace_steps.{c})"
        for c in ("parent_id", "kind", "name", "input", "output", "rationale", "status", "error", "started_at", "ended_at")
    )
    for i, step in enumerate(body.steps, start=1):
        db.execute(
            text(
                "INSERT INTO governance_agent_trace_steps (trace_pk, step_id, org_id, parent_id, seq, kind, name, input, output, "
                "rationale, status, error, started_at, ended_at) VALUES (:pk, :step, :org, :parent_id, :seq, COALESCE(:kind, 'other'), "
                "COALESCE(:name, ''), :input, :output, :rationale, COALESCE(:status, 'ok'), :error, :started_at, :ended_at) "
                # A re-sent step keeps its place and whatever this call left out.
                f"ON CONFLICT (trace_pk, step_id) DO UPDATE SET {step_keep}"
            ),
            {
                "pk": pk,
                "step": step.id or _new_id(),
                "org": m.org_id,
                "parent_id": step.parentId,
                "seq": seq + i,
                "kind": step.kind,
                "name": step.name,
                "input": _clip(step.input, cut),
                "output": _clip(step.output, cut),
                "rationale": _text(step.rationale, cut),
                "status": step.status,
                "error": _text(step.error, cut),
                "started_at": step.startedAt,
                "ended_at": step.endedAt,
            },
        )
    if cut[0]:
        db.execute(text("UPDATE governance_agent_traces SET truncated = :t WHERE id = :pk"), {"t": True, "pk": pk})
    db.commit()
    return {"traceId": body.traceId, "stepsReceived": len(body.steps), "truncated": cut[0]}


_COUNTS = (
    "(SELECT COUNT(*) FROM governance_agent_trace_steps s WHERE s.trace_pk = t.id) AS steps, "
    "(SELECT COUNT(*) FROM governance_agent_trace_steps s WHERE s.trace_pk = t.id AND s.kind IN ('llm', 'tool', 'decision')) AS decisions, "
    "(SELECT COUNT(*) FROM governance_agent_trace_steps s WHERE s.trace_pk = t.id AND s.kind IN ('llm', 'tool', 'decision') "
    "AND s.rationale IS NOT NULL AND s.rationale <> '') AS explained"
)


@router.get("/ai-systems/{system_id}/traces")
def list_traces(system_id: str, limit: int = Query(default=50, ge=1, le=200), m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _system_or_404(db, m.org_id, system_id)
    rows = db.execute(
        text(f"SELECT t.*, {_COUNTS} FROM governance_agent_traces t WHERE t.system_id = :sid ORDER BY t.received_at DESC LIMIT :n"),
        {"sid": system_id, "n": limit},
    ).mappings().all()
    return {"traces": [_trace_json(r, r["steps"], r["decisions"], r["explained"]) for r in rows]}


def _since(delta: timedelta) -> str:
    return (datetime.now(timezone.utc) - delta).isoformat()


def _has_tool_calls(db: Session, system_id: str, start: str, end: str) -> bool:
    return db.execute(
        text(
            "SELECT 1 FROM governance_agent_trace_steps s JOIN governance_agent_traces t ON t.id = s.trace_pk WHERE t.system_id = :sid "
            "AND t.received_at >= :start AND t.received_at < :end AND s.kind = 'tool' AND s.name <> '' LIMIT 1"
        ),
        {"sid": system_id, "start": start, "end": end},
    ).first() is not None


def has_live_runs(db: Session, system_id: str) -> bool:
    """EV-MON-02 can run on live runs: tool calls arrived this week and in the four weeks before, its baseline."""
    week = _since(WEEK)
    return _has_tool_calls(db, system_id, week, _utc_now_iso()) and _has_tool_calls(db, system_id, _since(WEEK + BASELINE), week)


def _tool_calls(db: Session, system_id: str, start: str, end: str) -> bytes:
    rows = db.execute(
        text(
            "SELECT s.name, t.trace_id FROM governance_agent_trace_steps s JOIN governance_agent_traces t ON t.id = s.trace_pk "
            "WHERE t.system_id = :sid AND t.received_at >= :start AND t.received_at < :end AND s.kind = 'tool' AND s.name <> '' "
            "ORDER BY t.received_at, s.seq"
        ),
        {"sid": system_id, "start": start, "end": end},
    ).fetchall()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["tool", "session"])
    writer.writerows([name, trace_id] for name, trace_id in rows)
    return out.getvalue().encode() if rows else b""


def _mon02_files(db: Session, system_id: str, params: Dict[str, Any]) -> Dict[str, bytes]:
    now, week = _utc_now_iso(), _since(WEEK)
    baseline, calls = _tool_calls(db, system_id, _since(WEEK + BASELINE), week), _tool_calls(db, system_id, week, now)
    if not calls:
        raise HTTPException(status_code=422, detail="No tool calls arrived in live runs this week")
    if not baseline:
        raise HTTPException(status_code=422, detail="Live runs need tool calls from the four weeks before this one as a baseline; send runs for longer first")
    params.update({"tool_column": "tool", "session_column": "session", "target_column": ""})
    return {"baseline": baseline, "calls": calls}


def _tst03_files(db: Session, system_id: str, params: Dict[str, Any]) -> Dict[str, bytes]:
    """Each finished run with an answer and something retrieved or returned by a tool to ground it in."""
    traces = db.execute(
        text(
            "SELECT id, trace_id, input, output FROM governance_agent_traces WHERE system_id = :sid AND received_at >= :since "
            "AND status = 'ok' AND output IS NOT NULL ORDER BY received_at DESC LIMIT :n"
        ),
        {"sid": system_id, "since": _since(WEEK), "n": MAX_GROUNDED * 3},
    ).mappings().all()
    probes = []
    for t in traces:
        sources = db.execute(
            text("SELECT output FROM governance_agent_trace_steps WHERE trace_pk = :pk AND kind IN ('retrieval', 'tool') AND output IS NOT NULL ORDER BY seq"),
            {"pk": t["id"]},
        ).scalars().all()
        if sources:
            text_of = lambda v: v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)  # noqa: E731
            probes.append({"traceId": t["trace_id"], "prompt": text_of(_value(t["input"]) or ""), "answer": text_of(_value(t["output"])),
                           "source": "\n\n".join(text_of(_value(x)) for x in sources)})
        if len(probes) == MAX_GROUNDED:
            break
    if not probes:
        raise HTTPException(status_code=422, detail="No finished live run this week has an answer and a retrieval or tool output to check it against")
    return {"traces": json.dumps(probes, ensure_ascii=False).encode()}


# evaluation id -> reads the week's live runs into that engine's files (and may set params it needs)
TRACE_READERS = {"EV-MON-02": _mon02_files, "EV-TST-03": _tst03_files}


def live_run_evaluations(db: Session, system_id: str) -> List[Dict[str, Any]]:
    """The latest run of each evaluation that read live runs."""
    out = []
    for evaluation_id in TRACE_READERS:
        row = db.execute(
            text(
                "SELECT id, content_json, created_at FROM governance_evidence WHERE system_id = :sid AND evidence_type = 'evaluation_run' "
                "AND content_json LIKE :ev AND metadata_json LIKE :src ORDER BY created_at DESC LIMIT 1"
            ),
            {"sid": system_id, "ev": f'%"evaluationId": "{evaluation_id}"%', "src": '%"source": "traces"%'},
        ).mappings().fetchone()
        if row:
            content = json.loads(row["content_json"] or "{}")
            out.append({"evaluationId": evaluation_id, "evidenceId": row["id"], "status": content.get("status"), "summary": content.get("summary"),
                        "metrics": content.get("metrics", {}), "createdAt": row["created_at"]})
    return out


@router.get("/ai-systems/{system_id}/traces/summary")
def trace_summary(system_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _system_or_404(db, m.org_id, system_id)
    since = (datetime.now(timezone.utc) - timedelta(days=SUMMARY_DAYS - 1)).date().isoformat()
    by_day = {
        day: (runs, errors)
        for day, runs, errors in db.execute(
            text(
                "SELECT LEFT(received_at, 10) AS day, COUNT(*), SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) FROM governance_agent_traces "
                "WHERE system_id = :sid AND received_at >= :since GROUP BY LEFT(received_at, 10)"
            ),
            {"sid": system_id, "since": since},
        ).fetchall()
    }
    today = datetime.now(timezone.utc).date()
    days = [(today - timedelta(days=i)).isoformat() for i in range(SUMMARY_DAYS - 1, -1, -1)]
    week = db.execute(
        text("SELECT COUNT(*), SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) FROM governance_agent_traces WHERE system_id = :sid AND received_at >= :since"),
        {"sid": system_id, "since": _since(WEEK)},
    ).fetchone()
    last = db.execute(text("SELECT MAX(received_at) FROM governance_agent_traces WHERE system_id = :sid"), {"sid": system_id}).scalar()
    return {
        "lastRunAt": last,
        "week": {"runs": int(week[0] or 0), "errors": int(week[1] or 0)},
        "days": [{"date": d, "runs": int(by_day.get(d, (0, 0))[0]), "errors": int(by_day.get(d, (0, 0))[1] or 0)} for d in days],
        "evaluations": live_run_evaluations(db, system_id),
    }


@router.get("/ai-systems/{system_id}/traces/{trace_id}")
def get_trace(system_id: str, trace_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _system_or_404(db, m.org_id, system_id)
    row = _trace_row(db, system_id, trace_id)
    if not row:
        raise HTTPException(status_code=404, detail="Trace not found")
    steps = db.execute(
        text("SELECT * FROM governance_agent_trace_steps WHERE trace_pk = :pk ORDER BY seq, started_at"), {"pk": row["id"]}
    ).mappings().all()
    decisions = [s for s in steps if s["kind"] in DECISIONS]
    trace = _trace_json(row, len(steps), len(decisions), sum(1 for s in decisions if s["rationale"]))
    trace["steps"] = [
        {
            "id": s["step_id"],
            "parentId": s["parent_id"],
            "kind": s["kind"],
            "name": s["name"],
            "input": _value(s["input"]),
            "output": _value(s["output"]),
            "rationale": s["rationale"],
            "status": s["status"],
            "error": s["error"],
            "startedAt": s["started_at"],
            "endedAt": s["ended_at"],
        }
        for s in steps
    ]
    return {"trace": trace}


@router.delete("/ai-systems/{system_id}/traces/{trace_id}")
def delete_trace(system_id: str, trace_id: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _system_or_404(db, m.org_id, system_id)
    row = _trace_row(db, system_id, trace_id)
    if not row:
        raise HTTPException(status_code=404, detail="Trace not found")
    db.execute(text("DELETE FROM governance_agent_trace_steps WHERE trace_pk = :pk"), {"pk": row["id"]})
    db.execute(text("DELETE FROM governance_agent_traces WHERE id = :pk"), {"pk": row["id"]})
    db.commit()
    return {"deleted": trace_id}
