"""
FairMind's reading of Shadow AI: the organisation's own model explains a finding, or a story of related
findings, in plain words. The rules decide severity and certainty; the model only explains the evidence and
must cite it. People, laptops and serial numbers are replaced with placeholders before anything is sent.

GET  /shadow-ai/reading?key=   the kept reading, and whether the evidence changed since it was written
POST /shadow-ai/reading        write (or rewrite) it with the organisation's model

A story is three or more open findings about one tool in one team (story:<service>:<team>).
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import llm
from api.routes import shadow_ai as sa
from api.routes.ai_governance import _caller_org
from api.routes.org_scope import org_member, org_mutator
from database.connection import get_db

router = APIRouter(prefix="/shadow-ai", tags=["shadow-ai"], dependencies=[Depends(org_member)])

STANCE_TEXT = {"approved": "approved", "limited": "approved for some teams", "not_allowed": "not allowed", "not_reviewed": "not reviewed"}
MAX_PARAGRAPHS = 4
MAX_TEXT = 700
MAX_NUDGE = 1200
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

SYSTEM = """You explain Shadow AI findings to the person who governs AI in an organisation.
Use only the numbered evidence you are given. Every paragraph lists the evidence numbers it rests on in cites.
Do not judge how serious it is or how sure it is; that is already decided and shown separately.
Do not guess at anyone's intent. People, laptops and serial numbers appear as placeholders such as Person A
and Laptop 1: keep them exactly as written and never try to reveal who they are.
Write short, plain sentences. No jargon, no headings, no emoji. At most four paragraphs.
next_step: one concrete thing to do next, with the evidence it rests on.
nudge: only when told a nudge is wanted, a short friendly message to Person A about using the company
account; otherwise an empty string."""

_CITED = {
    "type": "object",
    "properties": {"text": {"type": "string"}, "cites": {"type": "array", "items": {"type": "integer"}}},
    "required": ["text", "cites"],
    "additionalProperties": False,
}
SCHEMA = {
    "type": "object",
    "properties": {"paragraphs": {"type": "array", "items": _CITED}, "next_step": _CITED, "nudge": {"type": "string"}},
    "required": ["paragraphs", "next_step", "nudge"],
    "additionalProperties": False,
}


# ---------------------------------------------------------------------------
# Pure parts: stories, placeholders, what the model reads, what is kept
# ---------------------------------------------------------------------------


class Masks:
    """Placeholders for people, laptops and serials, applied before sending and undone on the way back."""

    def __init__(self) -> None:
        self.forward: Dict[str, str] = {}
        self.original: Dict[str, str] = {}  # label -> the value as first written
        self.counts = {"Person": 0, "Laptop": 0, "Serial": 0}

    def add(self, value: Optional[str], kind: str) -> None:
        v = (value or "").strip()
        if len(v) < 2 or v.lower() in self.forward:
            return
        n = self.counts[kind]
        self.counts[kind] += 1
        label = f"{kind} {chr(65 + n) if kind == 'Person' and n < 26 else n + 1}"
        self.forward[v.lower()] = label
        self.original[label] = v
        if kind == "Person" and "@" in v:
            self.forward.setdefault(v.split("@")[0].lower(), label)

    def mask(self, s: str) -> str:
        for real in sorted(self.forward, key=len, reverse=True):
            s = re.sub(rf"(?<![\w.@-]){re.escape(real)}(?![\w-]|\.\w|@)", self.forward[real], s, flags=re.I)
        return _EMAIL.sub("an address", s)

    def unmask(self, s: str) -> str:
        for label in sorted(self.original, key=len, reverse=True):
            s = s.replace(label, self.original[label])
        return s


def _grid_lines(grid: Dict[str, Any]) -> List[str]:
    lines = []
    for r in grid.get("rows") or []:
        parts = [f"{r['label']} ({STANCE_TEXT.get(r['stance'], r['stance'])})"]
        if r.get("onLaptop"):
            parts.append(f"on the laptop ({', '.join(r['onLaptop']['kinds'])}), seen by {', '.join(r['onLaptop']['sources'])}")
        if r.get("traffic"):
            parts.append(f"{r['traffic']['requests']} connections, seen by {', '.join(r['traffic']['sources'])}")
        if r.get("seat"):
            parts.append({"held": "holds a company seat", "none": "no company seat", "unknown": "seat list cannot be compared"}[r["seat"]["status"]])
        lines.append("; ".join(parts))
    return lines


def build_input(findings: List[Dict[str, Any]], grid: Optional[Dict[str, Any]], story: Optional[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Masks]:
    """What the model reads (masked), the numbered evidence it may cite (unmasked, for display) and the masks."""
    masks = Masks()
    for f in findings:
        masks.add(f.get("person"), "Person")
        masks.add(f.get("subject") if f.get("person") or f["type"] == "personal_account" else None, "Person")
    for lt in (grid or {}).get("laptops") or []:
        masks.add(lt["name"], "Laptop")
        masks.add(lt.get("serial"), "Serial")
    evidence: List[Dict[str, Any]] = []
    for f in findings:
        for e in f["evidence"]:
            evidence.append({"id": len(evidence) + 1, "title": e["title"], "detail": e["detail"], "source": e["source"]})
    for line in _grid_lines(grid or {}):
        evidence.append({"id": len(evidence) + 1, "title": "Tools on the laptop", "detail": line, "source": "devices"})
    subject = story or findings[0]
    payload = {
        "what": "story" if story else "finding",
        "title": masks.mask(subject["title"]),
        "findings": [{"title": masks.mask(f["title"]), "severity": f["severity"], "certainty": f["confidence"], "rule_says": masks.mask(f["verdict"])} for f in findings],
        "evidence": [{"n": e["id"], "source": e["title"], "says": masks.mask(e["detail"])} for e in evidence],
        "nudge_wanted": not story and findings[0]["type"] == "personal_account" and bool(findings[0].get("person")),
    }
    return payload, evidence, masks


def evidence_hash(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def keep(data: Dict[str, Any], evidence_ids: set, masks: Masks, nudge_wanted: bool) -> Dict[str, Any]:
    """Only what cites real evidence survives; placeholders become names again; no address the model invented stays."""

    def cited(item: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(item, dict):
            return None
        cites = sorted({int(c) for c in item.get("cites") or [] if isinstance(c, (int, float)) and int(c) in evidence_ids})
        body = _EMAIL.sub("an address", str(item.get("text") or "").strip())[:MAX_TEXT]
        return {"text": masks.unmask(body), "cites": cites} if body and cites else None

    paragraphs = [p for p in (cited(x) for x in (data.get("paragraphs") or [])[:MAX_PARAGRAPHS]) if p]
    nudge = masks.unmask(_EMAIL.sub("an address", str(data.get("nudge") or "").strip())[:MAX_NUDGE]) if nudge_wanted else ""
    return {"paragraphs": paragraphs, "next_step": cited(data.get("next_step")), "nudge": nudge, "dropped": len(data.get("paragraphs") or []) - len(paragraphs)}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


def _subject(db: Session, org: str, key: str) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    cur = sa._current(db, org)
    findings = cur["findings"]
    states = dict(db.execute(text("SELECT finding_key, status FROM governance_shadow_states WHERE org_id = :org"), {"org": org}).fetchall())
    for f in findings:
        f["status"] = states.get(f["key"], "open")
    if key.startswith("story:"):
        story = next((s for s in sa.stories(findings) if s["key"] == key), None)
        if not story:
            raise HTTPException(status_code=404, detail="That story is no longer open")
        picked = [f for f in findings if f["key"] in story["findingKeys"]]
        return picked, None, story
    f = next((x for x in findings if x["key"] == key), None)
    if not f:
        raise HTTPException(status_code=404, detail="That finding is no longer open")
    grid = sa.evidence(cur["assets"], cur["people"], cur["fleet"], cur["stance"], person=f["person"]) if f.get("person") else None
    return [f], grid, None


def _kept(db: Session, org: str, key: str) -> Optional[Any]:
    return db.execute(
        text("SELECT evidence_hash, reading_json, model, created_at FROM governance_shadow_readings WHERE org_id = :org AND subject_key = :k"), {"org": org, "k": key}
    ).fetchone()


def _org_model(db: Session, org: str) -> Optional[llm.Connection]:
    from api.routes.packs import _ai_row, _stored_connection

    row = _ai_row(db, org)
    return _stored_connection(row) if row and row["enabled"] else None


def _out(row: Any, evidence: List[Dict[str, Any]], current_hash: str) -> Dict[str, Any]:
    return {**json.loads(row[1]), "model": row[2], "createdAt": row[3], "stale": row[0] != current_hash, "evidence": evidence}


@router.get("/reading")
def get_reading(key: str, http: Request, db: Session = Depends(get_db)):
    sa.hub._ensure_tables()
    org = _caller_org(http)
    findings, grid, story = _subject(db, org, key)
    payload, evidence, _ = build_input(findings, grid, story)
    row = _kept(db, org, key)
    return {"reading": _out(row, evidence, evidence_hash(payload)) if row else None, "modelConnected": _org_model(db, org) is not None}


class ReadingBody(BaseModel):
    key: str = Field(min_length=1, max_length=500)


@router.post("/reading")
async def write_reading(body: ReadingBody, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    sa.hub._ensure_tables()
    org = _caller_org(http)
    conn = _org_model(db, org)
    if not conn:
        raise HTTPException(status_code=409, detail="Connect your organisation's AI model in Organisation settings to have FairMind read findings")
    findings, grid, story = _subject(db, org, body.key)
    payload, evidence, masks = build_input(findings, grid, story)
    db.rollback()  # hold no transaction open while the model works
    try:
        data, meta = await llm.complete(conn, SYSTEM, json.dumps(payload, sort_keys=True), SCHEMA)
    except llm.LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    reading = keep(data, {e["id"] for e in evidence}, masks, payload["nudge_wanted"])
    if not reading["paragraphs"]:
        raise HTTPException(status_code=502, detail="The model's answer cited none of the evidence, so nothing was kept. Try again.")
    now = datetime.now(timezone.utc).isoformat()
    db.execute(text("DELETE FROM governance_shadow_readings WHERE org_id = :org AND subject_key = :k"), {"org": org, "k": body.key})
    db.execute(
        text(
            "INSERT INTO governance_shadow_readings (id, org_id, subject_key, evidence_hash, reading_json, model, created_by, created_at) "
            "VALUES (:id, :org, :k, :h, :r, :m, :by, :now)"
        ),
        {"id": str(uuid.uuid4()), "org": org, "k": body.key, "h": evidence_hash(payload), "r": json.dumps(reading), "m": meta.get("model"), "by": getattr(who, "user_id", None), "now": now},
    )
    db.commit()
    return {"reading": _out(_kept(db, org, body.key), evidence, evidence_hash(payload)), "modelConnected": True}
