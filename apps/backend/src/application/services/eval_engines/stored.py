"""Inputs FairMind already holds for an evaluation, so it runs without an upload (the run form's "FairMind's data" way).

Each reader returns the engine's files, built from the organisation's own records for one AI system, or {} when there is
none yet; exists answers the same question cheaply for the run page. Every read is scoped to the organisation and system.
"""

import csv
import io
import json
from typing import Any, Callable, Dict, NamedTuple

from sqlalchemy import text


def _system_prompt(db, org_id: str, system_id: str) -> str:
    raw = db.execute(text("SELECT fields_json FROM governance_ai_system_targets WHERE system_id = :s AND org_id = :org"),
                     {"s": system_id, "org": org_id}).scalar()
    try:
        return str(json.loads(raw or "{}").get("systemPrompt") or "").strip()
    except (ValueError, AttributeError):
        return ""


# Rows FairMind's autopilot (its agent) wrote for the steps it took; check_key 'autopilot' marks a whole run skipped or failed, not a step.
_AGENT_EVENTS = "FROM autopilot_events WHERE org_id = :org AND system_id = :s AND check_key <> 'autopilot'"
# Evidence FairMind's agent filed (autopilot writes uploaded_by agent:autopilot).
_AGENT_EVIDENCE = ("FROM governance_evidence e LEFT JOIN governance_evidence_runs r ON r.id = e.source_run_id "
                   "WHERE e.org_id = :org AND e.system_id = :s AND e.uploaded_by LIKE 'agent:%'")


def _agent_actions(db, org_id: str, system_id: str) -> Dict[str, bytes]:
    rows = db.execute(text(f"SELECT check_key, action, status {_AGENT_EVENTS} ORDER BY created_at"), {"org": org_id, "s": system_id}).fetchall()
    if not rows:
        return {}
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["scenario", "tool", "outcome"])
    for check, action, status in rows:
        # the autopilot writes done or failed; no guardrail stands in front of it, so nothing here is "blocked"
        w.writerow([check, action, "executed" if status == "done" else "failed"])
    return {"actions": out.getvalue().encode()}


def _agent_evidence(db, org_id: str, system_id: str) -> Dict[str, bytes]:
    rows = db.execute(
        text(f"SELECT e.id, e.evidence_type, e.source, e.content_json, e.metadata_json, r.content_hash {_AGENT_EVIDENCE} ORDER BY e.created_at"),
        {"org": org_id, "s": system_id},
    ).fetchall()
    items = []
    for eid, kind, source, content, metadata, digest in rows:
        try:
            body = json.loads(content or "{}")
        except ValueError:
            body = {}
        try:
            meta = json.loads(metadata or "{}")
        except ValueError:
            meta = {}
        # the record as filed; content_hash is only the integrity hash FairMind stored, never one computed here
        items.append({**(body if isinstance(body, dict) else {}), "id": eid, "type": kind, "source": source, "metadata": meta, "content_hash": digest})
    return {"evidence": json.dumps(items, default=str).encode()} if items else {}


def _exists(sql: str) -> Callable[[Any, str, str], bool]:
    return lambda db, org_id, system_id: db.execute(text(f"SELECT 1 {sql} LIMIT 1"), {"org": org_id, "s": system_id}).first() is not None


def _has_prompt(db, org_id: str, system_id: str) -> bool:
    return bool(_system_prompt(db, org_id, system_id))


class Reader(NamedTuple):
    label: str  # what the run's files read as, in place of an upload's file name
    read: Callable[[Any, str, str], Dict[str, bytes]]
    exists: Callable[[Any, str, str], bool]


READERS: Dict[str, Reader] = {
    "EV-DEV-01": Reader("System prompt on the saved connection",
                        lambda db, o, s: {"system_prompt": p.encode()} if (p := _system_prompt(db, o, s)) else {}, _has_prompt),
    "EV-DEV-02": Reader("System prompt on the saved connection",
                        lambda db, o, s: {"file": p.encode()} if (p := _system_prompt(db, o, s)) else {}, _has_prompt),
    "EV-SLF-02": Reader("FairMind agent's actions on this system", _agent_actions, _exists(_AGENT_EVENTS)),
    "EV-SLF-03": Reader("Evidence FairMind's agent filed for this system", _agent_evidence, _exists(_AGENT_EVIDENCE)),
}
