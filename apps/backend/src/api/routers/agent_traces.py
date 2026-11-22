"""Live traces from a running AI system or agent, with the reason it gave at each step.

POST   /ai-systems/{id}/traces               record or extend a trace; safe to call again as the run goes on
GET    /ai-systems/{id}/traces               the latest traces, each with its step count and rationale coverage
GET    /ai-systems/{id}/traces/summary       runs per day, the last run, and the latest evaluations that read live runs
GET    /ai-systems/{id}/traces/{trace_id}    one trace with its steps in order, and its latest explanation
POST   /ai-systems/{id}/traces/{trace_id}/explain   explain the run now (eval_engines/explain.py)
GET    /explained-decisions                  Records: each system's Explanation quality runs on live runs, and recent explained runs
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
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes.ai_governance import _ensure_tables, _utc_now_iso
from api.routes.packs import _ai_row, _manager, _member, _stored_connection
from api.routes.system_targets import _system_or_404, stored_target
from database.connection import get_db
from database.governance_models import _new_id
from src.application.services.eval_engines import explain
from src.application.services.eval_engines.behaviour import CallError
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
MAX_EXPLAINED = 50  # EV-OVS-04 replays each run about 20 times, so it tests at most this many


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


def _decision(db: Session, t) -> Optional[Dict[str, Any]]:
    """A run as EV-OVS-04 reads it: its input, its decision and the reason stated for it; None without all three.
    The decision and reason come from the run's last decision step, else from the run itself."""
    step = db.execute(
        text("SELECT output, rationale FROM governance_agent_trace_steps WHERE trace_pk = :pk AND kind = 'decision' ORDER BY seq DESC LIMIT 1"),
        {"pk": t["id"]},
    ).mappings().fetchone()
    decision = (step and step["output"]) or t["output"]
    reason = (step and step["rationale"]) or t["rationale"]
    if not (t["input"] and decision and reason):
        return None
    return {"traceId": t["trace_id"], "input": _value(t["input"]), "decision": _value(decision), "reason": reason}


def _ovs04_files(db: Session, system_id: str, params: Dict[str, Any]) -> Dict[str, bytes]:
    """The newest finished runs of the week with an input, a decision and a stated reason."""
    try:
        n = min(max(int(float(params.get("runs") or 20)), 1), MAX_EXPLAINED)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="runs must be a number")
    traces = db.execute(
        text(
            "SELECT id, trace_id, input, output, rationale FROM governance_agent_traces WHERE system_id = :sid AND received_at >= :since "
            "AND status = 'ok' AND input IS NOT NULL ORDER BY received_at DESC LIMIT :n"
        ),
        {"sid": system_id, "since": _since(WEEK), "n": n * 5},
    ).mappings().all()
    runs = [r for r in (_decision(db, t) for t in traces) if r][:n]
    if not runs:
        raise HTTPException(status_code=422, detail="No finished live run this week has an input, a decision and a stated reason to test")
    return {"traces": json.dumps(runs, ensure_ascii=False).encode()}


# evaluation id -> reads the week's live runs into that engine's files (and may set params it needs)
TRACE_READERS = {"EV-MON-02": _mon02_files, "EV-TST-03": _tst03_files, "EV-OVS-04": _ovs04_files}
# evaluation id -> the engine that reads live runs, where it is not the evaluation's own (whose input is an upload)
TRACE_ENGINES = {"EV-OVS-04": explain.ENGINE}


def has_decision_runs(db: Session, system_id: str) -> bool:
    """EV-OVS-04 can run on live runs: a finished run this week has a decision step with a stated reason."""
    return db.execute(
        text(
            "SELECT 1 FROM governance_agent_trace_steps s JOIN governance_agent_traces t ON t.id = s.trace_pk WHERE t.system_id = :sid "
            "AND t.received_at >= :since AND t.status = 'ok' AND t.input IS NOT NULL AND s.kind = 'decision' AND s.rationale IS NOT NULL "
            "AND s.rationale <> '' LIMIT 1"
        ),
        {"sid": system_id, "since": _since(WEEK)},
    ).first() is not None


def save_explanations(db: Session, org_id: str, system_id: str, rows: List[Dict[str, Any]], by: str, evidence_id: Optional[str] = None) -> None:
    """Keep each run's explanation, replacing the one before, so the run opens explained."""
    now = _utc_now_iso()
    for r in rows:
        if r.get("verdict") == "error" or not r.get("traceId"):
            continue
        db.execute(
            text(
                "INSERT INTO governance_trace_explanations (id, org_id, system_id, trace_id, evidence_id, result_json, created_by, created_at) "
                "VALUES (:id, :org, :sid, :tid, :ev, :res, :by, :now) ON CONFLICT (system_id, trace_id) DO UPDATE SET "
                "evidence_id = excluded.evidence_id, result_json = excluded.result_json, created_by = excluded.created_by, created_at = excluded.created_at"
            ),
            {"id": _new_id(), "org": org_id, "sid": system_id, "tid": r["traceId"], "ev": evidence_id,
             "res": json.dumps(r, ensure_ascii=False), "by": by, "now": now},
        )
    db.commit()


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


@router.get("/explained-decisions")
def explained_decisions(m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    """Records: every system's Explanation quality runs on live runs, and the runs explained in the last 30 days."""
    _ensure_tables(db)
    since = _since(timedelta(days=30))
    systems: Dict[str, Dict[str, Any]] = {}
    for evidence_id, system_id, name, content, created in db.execute(
        text(
            "SELECT e.id, e.system_id, s.name, e.content_json, e.created_at FROM governance_evidence e JOIN governance_ai_systems s ON s.id = e.system_id "
            "WHERE s.org_id = :org AND e.evidence_type = 'evaluation_run' AND e.content_json LIKE :ev AND e.metadata_json LIKE :src ORDER BY e.created_at"
        ),
        {"org": m.org_id, "ev": f'%"evaluationId": "{explain.ENGINE.id}"%', "src": '%"source": "traces"%'},
    ).fetchall():
        c = json.loads(content or "{}")
        row = systems.setdefault(system_id, {"systemId": system_id, "name": name, "runs": []})
        row["runs"].append({"evidenceId": evidence_id, "status": c.get("status"), "reasonHeldRate": (c.get("metrics") or {}).get("reasonHeldRate"),
                            "faithfulness": (c.get("metrics") or {}).get("faithfulness"), "createdAt": created})
    verdicts, flips = Counter(), 0
    for (res,) in db.execute(
        text("SELECT e.result_json FROM governance_trace_explanations e WHERE e.org_id = :org AND e.created_at >= :since"), {"org": m.org_id, "since": since}
    ).fetchall():
        r = json.loads(res)
        verdicts[r.get("verdict")] += 1
        flips += bool(r.get("flip"))
    sending = db.execute(
        text(
            "SELECT COUNT(DISTINCT t.system_id) FROM governance_agent_traces t WHERE t.org_id = :org AND t.received_at >= :since "
            "AND EXISTS (SELECT 1 FROM governance_agent_trace_steps s WHERE s.trace_pk = t.id AND s.kind = 'decision')"
        ),
        {"org": m.org_id, "since": since},
    ).scalar()
    scored = verdicts["held"] + verdicts["did not hold"] + verdicts["untested"]
    return {
        "systems": sorted(systems.values(), key=lambda r: r["runs"][-1]["createdAt"], reverse=True),
        "totals": {"systemsSending": int(sending or 0), "explained": sum(verdicts.values()), "held": verdicts["held"], "notHeld": verdicts["did not hold"],
                   "notReproducible": verdicts["not reproducible"], "scored": scored, "withFlip": flips},
    }


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
        "decisions": _decisions_summary(db, system_id, days),
    }


def _label(output: Optional[str]) -> str:
    """A decision step's outcome as a label: its output when that is a short string, else other."""
    v = _value(output)
    return " ".join(v.casefold().split()) if isinstance(v, str) and 0 < len(v.strip()) <= 40 else "other"


def _decisions_summary(db: Session, system_id: str, days: List[str]) -> Optional[Dict[str, Any]]:
    """Decision steps per day by outcome over the summary's days, the days before for comparison, and the runs explained.
    None when the system sent no decision step in that time."""
    prior_start = (datetime.fromisoformat(days[0]) - timedelta(days=SUMMARY_DAYS)).date().isoformat()
    last: Dict[str, tuple] = {}  # trace -> its last decision step: (day, label, has reason)
    # ponytail: reads every decision step of 28 days into memory; aggregate in SQL if systems send many thousands a day
    for trace_id, day, output, rationale in db.execute(
        text(
            "SELECT t.trace_id, LEFT(t.received_at, 10), s.output, s.rationale FROM governance_agent_trace_steps s "
            "JOIN governance_agent_traces t ON t.id = s.trace_pk WHERE t.system_id = :sid AND t.received_at >= :since "
            "AND s.kind = 'decision' ORDER BY t.received_at, s.seq"
        ),
        {"sid": system_id, "since": prior_start},
    ).fetchall():
        last[trace_id] = (day, _label(output), bool(rationale and rationale.strip()))
    if not last:
        return None
    now = [v for v in last.values() if v[0] >= days[0]]
    before = [v for v in last.values() if v[0] < days[0]]
    counts = Counter(label for _, label, _ in now)
    labels = [k for k, _ in counts.most_common(2) if k != "other"]
    top = labels[0] if labels else None
    share = lambda rows: round(sum(r[1] == top for r in rows) / len(rows), 4) if rows and top else None  # noqa: E731
    per_day = {d: Counter() for d in days}
    for day, label, _ in now:
        per_day[day][label if label in labels else "other"] += 1
    explained = defaultdict(Counter)
    for day, res in db.execute(
        text(
            "SELECT LEFT(t.received_at, 10), e.result_json FROM governance_trace_explanations e JOIN governance_agent_traces t "
            "ON t.system_id = e.system_id AND t.trace_id = e.trace_id WHERE e.system_id = :sid AND t.received_at >= :since"
        ),
        {"sid": system_id, "since": days[0]},
    ).fetchall():
        explained[day][json.loads(res).get("verdict")] += 1
    total = sum(explained.values(), Counter())
    return {
        "total": len(now), "withReason": sum(r[2] for r in now), "labels": labels, "topLabel": top,
        "topShare": share(now), "priorTopShare": share(before), "priorTotal": len(before),
        "days": [{"date": d, "total": sum(per_day[d].values()), "byLabel": dict(per_day[d]),
                  "held": explained[d]["held"], "tested": explained[d]["held"] + explained[d]["did not hold"]} for d in days],
        "explained": {"held": total["held"], "notHeld": total["did not hold"], "notReproducible": total["not reproducible"], "untested": total["untested"]},
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
    explanation = db.execute(
        text("SELECT result_json, evidence_id, created_at FROM governance_trace_explanations WHERE system_id = :sid AND trace_id = :tid"),
        {"sid": system_id, "tid": trace_id},
    ).mappings().fetchone()
    trace["explanation"] = ({**json.loads(explanation["result_json"]), "evidenceId": explanation["evidence_id"], "createdAt": explanation["created_at"]}
                            if explanation else None)
    trace["explainable"] = _decision(db, row) is not None
    return {"trace": trace}


@router.post("/ai-systems/{system_id}/traces/{trace_id}/explain")
async def explain_trace(system_id: str, trace_id: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    """Explain one run now: about 20 replays on the model connection, judged by the organisation's model; kept on the run."""
    from api.routes import evaluation_runs  # it imports this module

    _ensure_tables(db)
    _system_or_404(db, m.org_id, system_id)
    row = _trace_row(db, system_id, trace_id)
    if not row:
        raise HTTPException(status_code=404, detail="Trace not found")
    run = _decision(db, row)
    if not run:
        raise HTTPException(status_code=422, detail="This run has no input, decision and stated reason to explain")
    ai = _ai_row(db, m.org_id)
    if not ai or not ai["enabled"]:
        raise HTTPException(status_code=409, detail="Explaining a run uses your organisation's AI provider as the judge; set one up in organisation settings")
    target = stored_target(db, m.org_id, system_id)
    if target.via_runner:
        raise HTTPException(status_code=409, detail="This system is on your private network, so only the runner can call it; run Explanation quality from there")
    system = db.execute(text("SELECT name, risk_tier, lifecycle_stage FROM governance_ai_systems WHERE id = :id"), {"id": system_id}).fetchone()
    judge = _stored_connection(ai)
    db.rollback()  # hold no transaction open during the replays

    async def progress(done: int, total: int, phase: str) -> None:
        return None

    live = evaluation_runs.make_live(target, judge, {"name": system[0], "risk_tier": system[1], "lifecycle_stage": system[2]}, progress)
    try:
        out = await explain.explain_run(run, live)
    except CallError as e:
        raise HTTPException(status_code=502, detail=str(e))
    save_explanations(db, m.org_id, system_id, [out], m.user_id)
    return {"explanation": {**out, "evidenceId": None, "createdAt": _utc_now_iso()}}


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
