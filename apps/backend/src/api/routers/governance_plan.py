"""The agentic governance plan: discovery, a map of what applies, and the tasks that close the gaps.

GET   /plan                          discovery state (next question, what was inferred, the map) or the active plan
POST  /plan/discovery                answer one discovery question; free text is read by the organisation's model
POST  /plan/generate                 turn discovery into the plan (needs the frameworks question answered)
PATCH /plan/tasks/{key}              assign an owner or leave a note
POST  /plan/tasks/{key}/attest       state an organisation-level control is in place, with a reference

Tasks are never invented. Each is one catalogue common control that the chosen frameworks require (the crosswalk
says which requirements), and its state comes from the estate: the release gate's checks for each system, confirmed
applicability, done workflow runs, or a person's attestation for organisation-level controls. The agent's part is
discovery (asking, reading free text, inferring from the inventory), choosing frameworks to suggest, ordering,
owners and dependencies. The plan is recomputed on every read, so it follows the estate; the change log says what
moved since the last read.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import llm
from api.routes.ai_governance import _ensure_tables
from api.routes.pack_catalogue import WORKFLOW_PACK, WORKFLOWS
from api.routes.packs import _ai_row, _is_installed, _manager, _member, _stored_connection
from database.connection import get_db
from src.application.services.clause_map_service import CHECK_CONTROLS, _catalogue
from src.application.services.governance_assurance_service import OrgMembership

router = APIRouter()

# --- discovery: the questions, their answers and what they map to (static configuration) --------------------------

JURISDICTIONS = {"india": "India", "eu": "European Union", "uk": "United Kingdom", "us": "United States", "singapore": "Singapore", "other": "Elsewhere"}
SECTORS = {"financial": "Banking, lending or payments", "insurance": "Insurance", "healthcare": "Healthcare", "public": "Public sector",
           "technology": "Technology or SaaS", "retail": "Retail or consumer", "other": "Something else"}
VALUE_CHAIN = {"deployer": "We use models others built", "developer": "We build our own models", "both": "Both",
               "gpai_provider": "We provide a general-purpose model to others"}
AI_TYPES = {"predictive": "Predictive or scoring models", "genai": "Generative AI or LLMs", "agents": "AI agents that take actions", "vision": "Vision or biometrics"}
DECISIONS = {"yes": "Yes, they decide about individual people", "some": "Some shape decisions a person makes", "no": "No"}
MATURITY = {"none": "Not yet", "partial": "Partly", "established": "In place"}
ROLES = {
    "head_ai_governance": "Head of AI governance", "exec_sponsor": "Executive sponsor", "ai_policy_owner": "AI policy owner",
    "legal": "Legal counsel", "dpo": "Data protection officer", "ciso": "Security lead", "risk_owner": "Risk owner",
    "internal_audit": "Internal auditor", "model_owner": "Model and system owners",
}
# Organisation-level controls discovery asks about; the rest are read from the estate.
MATURITY_CONTROLS = ["FMC-GOV-01", "FMC-GOV-02", "FMC-GOV-03", "FMC-GOV-04", "FMC-INV-01", "FMC-RSK-01", "FMC-INC-01", "FMC-SUP-01", "FMC-PRV-01"]

QUESTIONS: List[Dict[str, Any]] = [
    {"key": "about", "short": "", "kind": "text", "text": "Tell me about your organisation and how it uses AI.",
     "why": "I read this to fill in as much of the rest as I can, so you answer fewer questions.",
     "placeholder": "A mid-size NBFC in Mumbai. We score loan applications with gradient-boosted models and run an LLM support assistant for customers in India."},
    {"key": "jurisdictions", "short": "where your AI is used", "kind": "multi", "options": JURISDICTIONS, "text": "Where are the people your AI affects?",
     "why": "Jurisdiction decides which laws and guidelines apply."},
    {"key": "sector", "short": "your sector", "kind": "single", "options": SECTORS, "text": "Which sector are you in?", "why": "Regulated sectors add their own rules, such as RBI FREE-AI for lenders in India."},
    {"key": "value_chain", "short": "whether you build or use models", "kind": "single", "options": VALUE_CHAIN, "text": "Do you build models, use others', or both?",
     "why": "Providers and deployers carry different obligations."},
    {"key": "ai_types", "short": "the kinds of AI you run", "kind": "multi", "options": AI_TYPES, "text": "What kinds of AI do you run?", "why": "Agents and generative AI bring their own controls."},
    {"key": "decisions_about_people", "short": "whether it decides about people", "kind": "single", "options": DECISIONS, "text": "Do your AI systems decide about individual people?",
     "why": "Decisions about people raise the risk tier and the oversight you need."},
    {"key": "maturity", "short": "what you have in place", "kind": "maturity", "options": MATURITY, "text": "Which of these do you have in place today?",
     "why": "What you already have moves down the plan; what is missing moves up."},
    {"key": "people", "short": "who holds which role", "kind": "people", "options": ROLES, "text": "Who holds these roles?", "why": "I suggest task owners from these. Leave any blank."},
    {"key": "frameworks", "short": "", "kind": "frameworks", "text": "These frameworks apply to you. Keep, add or remove.", "why": "Every task in the plan traces to a requirement in one of these."},
]
QUESTION_KEYS = [q["key"] for q in QUESTIONS]

# --- the plan's shape (static configuration) -------------------------------------------------------------------

LANES = [("foundation", "Foundation"), ("inventory", "Inventory and risk"), ("build", "Build and test"), ("release", "Release"), ("operate", "Operate")]
CONTROL_LANE = {
    "FMC-GOV-01": "foundation", "FMC-GOV-02": "foundation", "FMC-GOV-03": "foundation", "FMC-GOV-04": "foundation", "FMC-GOV-05": "foundation",
    "FMC-GOV-08": "foundation", "FMC-INV-01": "inventory", "FMC-RSK-01": "inventory", "FMC-RSK-02": "inventory", "FMC-RSK-03": "inventory",
    "FMC-DAT-01": "build", "FMC-PRV-01": "build", "FMC-DEV-01": "build", "FMC-TST-01": "build", "FMC-FAI-01": "build", "FMC-AGT-01": "build",
    "FMC-AGT-02": "build", "FMC-LEG-01": "build", "FMC-REL-01": "release", "FMC-OVS-01": "release", "FMC-TRN-01": "release",
    "FMC-MON-01": "operate", "FMC-INC-01": "operate", "FMC-ENV-01": "operate", "FMC-SUP-01": "operate", "FMC-GOV-06": "operate",
    "FMC-GOV-07": "operate", "FMC-OFF-01": "operate",
}
CONTROL_DEPENDS = {
    "FMC-GOV-02": ["FMC-GOV-01"], "FMC-GOV-03": ["FMC-GOV-01"], "FMC-GOV-04": ["FMC-GOV-02"], "FMC-GOV-05": ["FMC-GOV-01"],
    "FMC-GOV-08": ["FMC-GOV-01"], "FMC-INV-01": ["FMC-GOV-03"], "FMC-RSK-01": ["FMC-INV-01", "FMC-GOV-02"], "FMC-RSK-02": ["FMC-INV-01"],
    "FMC-RSK-03": ["FMC-INV-01"], "FMC-DAT-01": ["FMC-INV-01"], "FMC-PRV-01": ["FMC-INV-01"], "FMC-DEV-01": ["FMC-RSK-01"],
    "FMC-TST-01": ["FMC-RSK-01"], "FMC-FAI-01": ["FMC-INV-01"], "FMC-AGT-01": ["FMC-INV-01"], "FMC-AGT-02": ["FMC-AGT-01"],
    "FMC-LEG-01": ["FMC-INV-01"], "FMC-REL-01": ["FMC-TST-01", "FMC-FAI-01", "FMC-OVS-01"], "FMC-OVS-01": ["FMC-GOV-03"],
    "FMC-TRN-01": ["FMC-RSK-02"], "FMC-MON-01": ["FMC-REL-01"], "FMC-INC-01": ["FMC-GOV-03"], "FMC-ENV-01": ["FMC-INV-01"],
    "FMC-SUP-01": ["FMC-INV-01"], "FMC-GOV-06": ["FMC-GOV-02"], "FMC-GOV-07": ["FMC-GOV-06"], "FMC-OFF-01": ["FMC-GOV-02"],
}
AGENT_CONTROLS = {"FMC-AGT-01", "FMC-AGT-02"}  # in scope only when the organisation runs agents
EXCLUDED_CONTROLS = {"FMC-SLF-01"}  # FairMind's own agent: FairMind's job, not the customer's
GATE_CONTROLS = {control: check for check, control in CHECK_CONTROLS.items()}
# The approver named in a control's first workflow, read for the role that should own the task; first match wins.
ROLE_KEYWORDS = [
    ("head of ai governance", "head_ai_governance"), ("top management", "exec_sponsor"), ("executive", "exec_sponsor"),
    ("ai policy owner", "ai_policy_owner"), ("internal auditor", "internal_audit"), ("legal", "legal"), ("dpo", "dpo"),
    ("ciso", "ciso"), ("security", "ciso"), ("risk", "risk_owner"),
]
STATES = ["todo", "needs_you", "agent", "review", "proven"]
MATURITY_WEIGHT = {"none": 6, "partial": 3, "established": 0, None: 3}


class AnswerBody(BaseModel):
    key: str
    value: Any = None


class TaskPatch(BaseModel):
    owner: Optional[str] = Field(default=None, max_length=200)
    note: Optional[str] = Field(default=None, max_length=2000)


class AttestBody(BaseModel):
    statement: str = Field(min_length=12, max_length=4000)
    reference: Optional[str] = Field(default=None, max_length=1000)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- storage ---------------------------------------------------------------------------------------------------


def _plan_row(db: Session, org_id: str) -> Dict[str, Any]:
    row = db.execute(text("SELECT * FROM governance_plans WHERE org_id = :org"), {"org": org_id}).mappings().fetchone()
    if not row:
        return {"org_id": org_id, "status": "discovery", "profile": {}, "transcript": [], "snapshot": {}, "exists": False}
    return {**dict(row), "profile": json.loads(row["profile_json"] or "{}"), "transcript": json.loads(row["transcript_json"] or "[]"),
            "snapshot": json.loads(row["snapshot_json"] or "{}"), "exists": True}


def _save_plan(db: Session, plan: Dict[str, Any], actor: Optional[str] = None) -> None:
    db.execute(
        text(
            "INSERT INTO governance_plans (org_id, status, profile_json, transcript_json, snapshot_json, created_by, created_at, updated_at) "
            "VALUES (:org, :status, :profile, :transcript, :snapshot, :by, :now, :now) "
            "ON CONFLICT (org_id) DO UPDATE SET status = :status, profile_json = :profile, transcript_json = :transcript, snapshot_json = :snapshot, updated_at = :now"
        ),
        {"org": plan["org_id"], "status": plan["status"], "profile": json.dumps(plan["profile"]), "transcript": json.dumps(plan["transcript"][-200:]),
         "snapshot": json.dumps(plan["snapshot"]), "by": actor, "now": _now()},
    )


# --- what the estate already says ------------------------------------------------------------------------------

GENAI_HINT = re.compile(r"\b(llm|gpt|llama|gemma|phi|mistral|qwen|claude|chat|whisper|nemotron|genai|instruct)", re.I)
AGENT_HINT = re.compile(r"\bagent", re.I)
VISION_HINT = re.compile(r"\b(vit|vision|face|yolo|resnet|clip|ocr)", re.I)


def _systems(db: Session, org_id: str) -> List[Dict[str, Any]]:
    rows = db.execute(
        text("SELECT id, name, risk_tier, owner, metadata_json FROM governance_ai_systems WHERE org_id = :org ORDER BY name"), {"org": org_id}
    ).mappings().all()
    out = []
    for r in rows:
        try:
            meta = json.loads(r["metadata_json"] or "{}")
        except ValueError:
            meta = {}
        applicability = meta.get("applicability") if isinstance(meta.get("applicability"), dict) else None
        out.append({"id": r["id"], "name": r["name"], "riskTier": r["risk_tier"], "owner": r["owner"], "applicability": applicability,
                    "source": meta.get("source"), "model": str(meta.get("model_id") or meta.get("model") or meta.get("repo_id") or "")})
    return out


def _done_runs(db: Session, org_id: str) -> List[Dict[str, Any]]:
    rows = db.execute(text("SELECT workflow_id, ai_system_id, status FROM workflow_runs WHERE org_id = :org"), {"org": org_id}).mappings().all()
    return [dict(r) for r in rows]


def _estate_inferences(systems: List[Dict[str, Any]], runs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """What the inventory and the run history say about discovery questions, each with its basis."""
    out: Dict[str, Dict[str, Any]] = {}
    if not systems:
        return out
    names = " ".join(f"{s['name']} {s['model']}" for s in systems)
    types = []
    if GENAI_HINT.search(names):
        types.append("genai")
    if AGENT_HINT.search(names):
        types.append("agents")
    if VISION_HINT.search(names):
        types.append("vision")
    if types:
        out["ai_types"] = {"value": types, "source": "estate", "basis": f"Names and models of your {len(systems)} registered systems"}
    confirmed = [s["applicability"] for s in systems if s["applicability"]]
    fw = {f.get("key") for a in confirmed for f in (a.get("frameworks") or []) if isinstance(f, dict)}
    where = sorted({"eu" for k in fw if k == "EUAIA"} | {"india" for k in fw if k in ("INDAI", "RBIFREEAI", "DPDP", "NITI")})
    if where:
        out["jurisdictions"] = {"value": where, "source": "estate", "basis": f"Frameworks confirmed on {len(confirmed)} systems"}
    if "RBIFREEAI" in fw:
        out["sector"] = {"value": "financial", "source": "estate", "basis": "RBI FREE-AI is confirmed on a system"}
    uses = {u for a in confirmed for u in ((a.get("answers") or {}).get("uses") or [])}
    if uses:
        people = uses - {"operations", "marketing", "other"}
        out["decisions_about_people"] = {"value": "yes" if people else "no", "source": "estate", "basis": "Uses recorded on your systems' applicability answers"}
    done_workflows = {r["workflow_id"] for r in runs if r["status"] == "done"}
    established = {wf.commonControl: "established" for wf in WORKFLOWS.values() if wf.id in done_workflows and wf.commonControl in MATURITY_CONTROLS}
    if established:
        out["maturity"] = {"value": established, "source": "estate", "basis": "Completed workflow runs"}
    return out


# --- reading free text: the organisation's model, or keyword rules without one -----------------------------------

RULE_HINTS = [
    ("jurisdictions", "india", r"\b(india|indian|mumbai|bengaluru|bangalore|delhi|chennai|hyderabad|pune|rbi|dpdp|sebi)\b"),
    ("jurisdictions", "eu", r"\b(eu|europe|european|germany|france|gdpr)\b"),
    ("jurisdictions", "uk", r"\b(uk|united kingdom|britain|london)\b"),
    ("jurisdictions", "us", r"\b(us|usa|united states|america|new york|california)\b"),
    ("jurisdictions", "singapore", r"\b(singapore|mas)\b"),
    ("sector", "financial", r"\b(bank|banking|nbfc|lend|lending|loan|credit|payments?|fintech|rbi)\b"),
    ("sector", "insurance", r"\b(insur\w*)\b"),
    ("sector", "healthcare", r"\b(hospital|health\w*|clinic\w*|medical|pharma\w*)\b"),
    ("sector", "public", r"\b(government|ministry|public sector|municipal)\b"),
    ("ai_types", "genai", r"\b(llm|gpt|chatbot|assistant|generative|genai|copilot)\b"),
    ("ai_types", "agents", r"\b(agents?|agentic)\b"),
    ("ai_types", "predictive", r"\b(scor\w*|predict\w*|classif\w*|gradient|xgboost|regression|forecast\w*)\b"),
    ("ai_types", "vision", r"\b(vision|image|face|biometric\w*|ocr)\b"),
    ("decisions_about_people", "yes", r"\b(loan|credit|hiring|recruit\w*|claims?|eligibility|underwrit\w*|admission)\b"),
]


def _rules_read(textv: str) -> Dict[str, Any]:
    found: Dict[str, Any] = {}
    for key, value, pattern in RULE_HINTS:
        if re.search(pattern, textv, re.I):
            if key in ("jurisdictions", "ai_types"):
                found.setdefault(key, [])
                if value not in found[key]:
                    found[key].append(value)
            else:
                found.setdefault(key, value)
    return found


def _read_schema() -> Dict[str, Any]:
    enum = lambda values: {"type": "string", "enum": [""] + list(values)}  # noqa: E731
    obj = lambda keys, values: {  # noqa: E731
        "type": "object", "properties": {k: values for k in keys}, "required": list(keys), "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "understood": {"type": "string"},
            "jurisdictions": {"type": "array", "items": {"type": "string", "enum": list(JURISDICTIONS)}},
            "sector": enum(SECTORS), "value_chain": enum(VALUE_CHAIN),
            "ai_types": {"type": "array", "items": {"type": "string", "enum": list(AI_TYPES)}},
            "decisions_about_people": enum(DECISIONS),
            "maturity": obj(MATURITY_CONTROLS, enum(MATURITY)),
            "people": obj(list(ROLES), {"type": "string"}),
        },
        "required": ["understood", "jurisdictions", "sector", "value_chain", "ai_types", "decisions_about_people", "maturity", "people"],
        "additionalProperties": False,
    }


READ_SYSTEM = (
    "You help an organisation set up AI governance. Read what the person wrote about their organisation and fill in only "
    "what it clearly states or directly implies; leave a field empty (an empty string, an empty list, or an empty "
    "string per key) when it does not say. Never guess. Maturity keys are catalogue controls: FMC-GOV-01 scope and "
    "objectives of AI governance, FMC-GOV-02 AI policies, FMC-GOV-03 roles and oversight bodies, FMC-GOV-04 AI literacy "
    "training, FMC-INV-01 an AI inventory, FMC-RSK-01 AI risk assessment, FMC-INC-01 incident and concern reporting, "
    "FMC-SUP-01 third-party AI vendor review, FMC-PRV-01 privacy review of AI. People are names or emails for roles. "
    "In understood, say in one or two sentences what you took from it."
)


async def _read_text(db: Session, org_id: str, textv: str) -> tuple:
    """(fields, how, understood) from free text: the organisation's model when one is on, else keyword rules."""
    row = _ai_row(db, org_id)
    if row and row["enabled"]:
        conn = _stored_connection(row)
        db.rollback()  # hold no transaction open while the model works
        try:
            data, _meta = await llm.complete(conn, READ_SYSTEM, textv[:6000], _read_schema())
        except llm.LLMError:
            data = None
        if isinstance(data, dict):
            fields: Dict[str, Any] = {}
            for key in ("jurisdictions", "ai_types"):
                vals = [v for v in (data.get(key) or []) if v in (JURISDICTIONS if key == "jurisdictions" else AI_TYPES)]
                if vals:
                    fields[key] = vals
            for key, allowed in (("sector", SECTORS), ("value_chain", VALUE_CHAIN), ("decisions_about_people", DECISIONS)):
                if data.get(key) in allowed:
                    fields[key] = data[key]
            maturity = {k: v for k, v in (data.get("maturity") or {}).items() if k in MATURITY_CONTROLS and v in MATURITY}
            if maturity:
                fields["maturity"] = maturity
            people = {k: str(v).strip()[:200] for k, v in (data.get("people") or {}).items() if k in ROLES and str(v).strip()}
            if people:
                fields["people"] = people
            return fields, "llm", str(data.get("understood") or "")[:600]
    return _rules_read(textv), "rules", ""


# --- discovery state -------------------------------------------------------------------------------------------


def _resolved(plan: Dict[str, Any], inferred: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Each question's value with where it came from: your answer beats your description beats the estate."""
    out: Dict[str, Dict[str, Any]] = {}
    for key in QUESTION_KEYS:
        if key == "maturity":
            merged: Dict[str, Any] = {}
            sources: Dict[str, str] = {}
            for layer in (inferred.get(key), plan["profile"].get(f"{key}__description"), plan["profile"].get(key)):
                if layer:
                    for c, v in (layer.get("value") or {}).items():
                        merged[c], sources[c] = v, layer["source"]
            if merged:
                out[key] = {"value": merged, "source": "mixed", "sources": sources}
            continue
        for layer in (plan["profile"].get(key), plan["profile"].get(f"{key}__description"), inferred.get(key)):
            if layer and layer.get("value") not in (None, "", []):
                out[key] = layer
                break
    return out


def _suggest_frameworks(resolved: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    frameworks = _catalogue()["frameworks"]
    where = set((resolved.get("jurisdictions") or {}).get("value") or [])
    sector = (resolved.get("sector") or {}).get("value")
    types = set((resolved.get("ai_types") or {}).get("value") or [])
    picks = [("ISO42001", "The international AI management system standard; a baseline whatever the jurisdiction")]
    if "india" in where:
        picks.append(("INDAI", "People in India are affected"))
        if sector == "financial":
            picks.append(("RBIFREEAI", "A lender or payments firm in India"))
    if "eu" in where:
        picks.append(("EUAIA", "People in the EU are affected"))
    if "uk" in where:
        picks.append(("UKAICOP", "People in the UK are affected"))
    if "us" in where:
        picks.append(("NISTRMF", "People in the US are affected"))
    if "singapore" in where:
        picks.append(("SGMGF", "People in Singapore are affected"))
        if sector == "financial":
            picks.append(("MASFEAT", "A financial firm in Singapore"))
    if "genai" in types:
        picks.append(("OWASPLLM", "You run generative AI"))
    if "agents" in types:
        picks.append(("OWASPAG", "You run AI agents"))
    return [{"key": k, "name": frameworks[k]["name"], "reason": why} for k, why in picks if k in frameworks]


def _selected_frameworks(plan: Dict[str, Any], resolved: Dict[str, Dict[str, Any]]) -> List[str]:
    chosen = (plan["profile"].get("frameworks") or {}).get("value")
    return list(chosen) if chosen else [f["key"] for f in _suggest_frameworks(resolved)]


def _next_question(resolved: Dict[str, Dict[str, Any]], plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for q in QUESTIONS:
        key = q["key"]
        if key == "maturity":
            known = (resolved.get("maturity") or {}).get("value") or {}
            missing = [c for c in MATURITY_CONTROLS if c not in known]
            if missing:
                names = {c["id"]: c["name"] for c in _catalogue()["commonControls"]}
                return {**q, "controls": [{"id": c, "name": names.get(c, c), "value": known.get(c)} for c in MATURITY_CONTROLS]}
            continue
        if key in ("people", "frameworks"):
            if key not in plan["profile"]:  # asked once even when blank answers are fine
                return q
            continue
        if key not in resolved:
            return q
        if q["kind"] == "multi" and resolved[key].get("source") == "estate":
            # The estate shows some of the answer, never all of it: ask, starting from what it shows.
            return {**q, "suggestedValue": resolved[key]["value"], "suggestedBasis": resolved[key].get("basis")}
    return None


def _scope_controls(frameworks: List[str], resolved: Dict[str, Dict[str, Any]]) -> tuple:
    """(controls in scope with their requirements, controls left out with why) for the chosen frameworks."""
    cat = _catalogue()
    agents = "agents" in ((resolved.get("ai_types") or {}).get("value") or [])
    in_scope, out_of_scope = [], []
    for control in cat["commonControls"]:
        cid = control["id"]
        reqs = [e["requirement"] for e in cat["by_control"].get(cid, []) if e["requirement"]["framework"] in frameworks]
        if cid in EXCLUDED_CONTROLS or not reqs:
            continue
        if cid in AGENT_CONTROLS and not agents:
            out_of_scope.append({"id": cid, "name": control["name"], "why": "You have not said you run AI agents"})
            continue
        in_scope.append({**control, "requirements": reqs})
    return in_scope, out_of_scope


def _discovery(db: Session, org_id: str, plan: Dict[str, Any]) -> Dict[str, Any]:
    systems = _systems(db, org_id)
    inferred = _estate_inferences(systems, _done_runs(db, org_id))
    resolved = _resolved(plan, inferred)
    frameworks = _selected_frameworks(plan, resolved)
    suggested = _suggest_frameworks(resolved)
    in_scope, out_of_scope = _scope_controls(frameworks, resolved)
    maturity = (resolved.get("maturity") or {}).get("value") or {}
    people = (plan["profile"].get("people") or {}).get("value") or {}
    question = _next_question(resolved, plan)
    if question and question["key"] == "frameworks":
        question = {**question, "suggested": suggested, "selected": frameworks,
                    "all": [{"key": k, "name": f["name"], "jurisdiction": f.get("jurisdiction")} for k, f in _catalogue()["frameworks"].items()]}
    answered = sum(1 for q in QUESTIONS if (q["key"] in resolved and q["key"] not in ("people", "frameworks")) or q["key"] in plan["profile"])
    row = _ai_row(db, org_id)
    return {
        "status": plan["status"],
        "agent": "llm" if row and row["enabled"] else "rules",
        "next": question,
        "progress": {"answered": min(answered, len(QUESTIONS)), "total": len(QUESTIONS)},
        "transcript": plan["transcript"][-60:],
        "facts": [
            {"key": k, "label": next(q["text"] for q in QUESTIONS if q["key"] == k), "value": v["value"], "display": _say(v["value"], k),
             "source": v.get("source"), "basis": v.get("basis")}
            for k, v in resolved.items() if k not in ("maturity",)
        ],
        "map": {
            "frameworks": [{"key": k, "name": _catalogue()["frameworks"][k]["name"], "reason": next((s["reason"] for s in suggested if s["key"] == k), "You chose it"),
                            "requirements": sum(1 for c in in_scope for r in c["requirements"] if r["framework"] == k)} for k in frameworks if k in _catalogue()["frameworks"]],
            "controls": [{"id": c["id"], "name": c["name"], "lane": CONTROL_LANE.get(c["id"], "build"), "requirements": len(c["requirements"]),
                          "maturity": maturity.get(c["id"])} for c in in_scope],
            "outOfScope": out_of_scope,
            "systems": [{"id": s["id"], "name": s["name"], "riskTier": s["riskTier"], "owner": s["owner"], "confirmed": bool(s["applicability"])} for s in systems],
            "owners": [{"role": k, "label": ROLES[k], "person": people.get(k) or None} for k in ROLES],
        },
    }


# --- tasks -----------------------------------------------------------------------------------------------------


def _role_for(control_id: str) -> str:
    wf = next((w for w in WORKFLOWS.values() if w.commonControl == control_id), None)
    approver = (wf.approver or "").lower() if wf else ""
    return next((role for kw, role in ROLE_KEYWORDS if kw in approver), "model_owner")


def _is_org_control(control_id: str) -> bool:
    wf = next((w for w in WORKFLOWS.values() if w.commonControl == control_id), None)
    return bool(wf and (wf.scope or "").lower().startswith("organisation"))


def _tasks(db: Session, org_id: str, plan: Dict[str, Any], disc: Dict[str, Any]) -> List[Dict[str, Any]]:
    from api.routes.fairness_runs import _gate_payload  # imported late: that router imports the governance router

    resolved_frameworks = [f["key"] for f in disc["map"]["frameworks"]]
    systems = _systems(db, org_id)
    runs = _done_runs(db, org_id)
    people = {o["role"]: o["person"] for o in disc["map"]["owners"]}
    maturity = {c["id"]: c["maturity"] for c in disc["map"]["controls"]}
    frameworks = _catalogue()["frameworks"]
    overrides = {r["task_key"]: dict(r) for r in db.execute(text("SELECT * FROM plan_task_overrides WHERE org_id = :org"), {"org": org_id}).mappings().all()}
    attestations: Dict[str, Dict[str, Any]] = {}
    for r in db.execute(text("SELECT task_key, statement, reference, attested_by, created_at FROM plan_attestations WHERE org_id = :org ORDER BY created_at"), {"org": org_id}).mappings().all():
        attestations[r["task_key"]] = dict(r)
    gates = {s["id"]: _gate_payload(db, s["id"], s["riskTier"]) for s in systems} if any(c["id"] in GATE_CONTROLS for c in disc["map"]["controls"]) else {}
    autopilot_on = {r[0] for r in db.execute(text("SELECT system_id FROM system_autopilot WHERE org_id = :org AND mode = 'run'"), {"org": org_id}).fetchall()}
    sources = {(r[0], r[1]) for r in db.execute(text("SELECT system_id, purpose FROM system_data_sources WHERE org_id = :org"), {"org": org_id}).fetchall()}
    in_scope, _ = _scope_controls(resolved_frameworks, {"ai_types": {"value": next((f["value"] for f in disc["facts"] if f["key"] == "ai_types"), [])}})

    tasks = []
    for control in in_scope:
        cid = control["id"]
        key = f"control:{cid}"
        workflows = [w for w in WORKFLOWS.values() if w.commonControl == cid]
        wf_ids = {w.id for w in workflows}
        control_runs = [r for r in runs if r["workflow_id"] in wf_ids]
        reqs = control["requirements"]
        binding = [r for r in reqs if str(frameworks.get(r["framework"], {}).get("binding") or "").startswith("Binding")]
        system_rows: List[Dict[str, Any]] = []
        by = "person"
        if cid in GATE_CONTROLS:
            kind, check = "gate", GATE_CONTROLS[cid]
            for s in systems:
                c = next((x for x in gates[s["id"]]["checks"] if x["key"] == check), None)
                state = c["state"] if c else "open"
                agent_ready = s["id"] in autopilot_on and ((check == "fairness" and (s["id"], "fairness") in sources) or (check == "monitoring" and (s["id"], "monitoring") in sources))
                system_rows.append({"id": s["id"], "name": s["name"], "done": state in ("proven", "attested"),
                                    "detail": "fails" if c and c.get("fails") else state, "agent": agent_ready})
            if any(r["agent"] and not r["done"] for r in system_rows):
                by = "agent"
        elif cid == "FMC-INV-01":
            kind = "inventory"
            system_rows = [{"id": s["id"], "name": s["name"], "done": bool(s["applicability"]), "detail": "tier confirmed" if s["applicability"] else "tier not confirmed", "agent": False} for s in systems]
        elif _is_org_control(cid):
            kind = "org"
        else:
            kind = "system"
            for s in systems:
                mine = [r for r in control_runs if r["ai_system_id"] == s["id"]]
                done = any(r["status"] == "done" for r in mine)
                detail = "done" if done else ("waiting for approval" if any(r["status"] == "waiting" for r in mine) else "running" if any(r["status"] in ("queued", "running") for r in mine) else "not started")
                system_rows.append({"id": s["id"], "name": s["name"], "done": done, "detail": detail, "agent": False})

        attestation = attestations.get(key)
        if kind == "org":
            total, done_count = 1, 1 if (attestation or any(r["status"] == "done" for r in control_runs)) else 0
            running = any(r["status"] in ("queued", "running") for r in control_runs)
            waiting = any(r["status"] == "waiting" for r in control_runs)
        else:
            total, done_count = len(system_rows), sum(1 for r in system_rows if r["done"])
            running = by == "agent" or any(r["detail"] == "running" for r in system_rows)
            waiting = any(r["detail"] == "waiting for approval" for r in system_rows)
        proven = total > 0 and done_count == total

        role = _role_for(cid)
        if kind in ("gate", "inventory", "system"):
            owners = sorted({s["owner"] for s in systems if s["owner"]})
            suggested = owners[0] if len(owners) == 1 else (people.get("model_owner") or (f"{len(owners)} system owners" if owners else None))
            reason = "Owns every system this covers" if len(owners) == 1 else "Each system's owner does their part"
        else:
            suggested = people.get(role)
            reason = f"Holds the {ROLES[role]} role" if suggested else f"Needs someone in the {ROLES[role]} role; none named yet"
        override = overrides.get(key) or {}
        level = maturity.get(cid)
        verb = {"none": "Establish", "partial": "Formalise", "established": "Evidence"}.get(level or "", "Put in place")
        if kind == "gate":
            title = f"{control['name']} for every system"
        elif kind == "inventory":
            title = "Confirm risk tier and frameworks for every system"
        elif kind == "system":
            title = f"{control['name']} for each system"
        else:
            name = control["name"]
            title = f"{verb} {name[0].lower() + name[1:] if name[1:2].islower() else name}"
        tasks.append({
            "key": key, "controlId": cid, "controlName": control["name"], "objective": control.get("objective"), "title": title,
            "kind": kind, "lane": CONTROL_LANE.get(cid, "build"),
            "requirements": [{"key": r["key"], "framework": r["framework"], "control": r["control"], "title": r["title"]} for r in reqs],
            "frameworks": sorted({r["framework"] for r in reqs}), "bindingCount": len(binding),
            "dependsOn": [f"control:{d}" for d in CONTROL_DEPENDS.get(cid, []) if any(c["id"] == d for c in in_scope)],
            "maturity": level, "by": by,
            "owner": override.get("owner") or None, "ownerSuggested": suggested, "ownerReason": reason, "note": override.get("note"),
            "progress": {"done": done_count, "total": total}, "systems": system_rows,
            "actions": [{"id": w.id, "name": w.name, "scope": w.scope, "approver": w.approver, "installed": _is_installed(db, org_id, WORKFLOW_PACK[w.id])} for w in workflows],
            "attestation": attestation,
            "_flags": {"proven": proven, "running": running, "waiting": waiting, "empty": total == 0},
            "score": 3 * len(binding) + len(reqs) + (8 if kind == "gate" else 0) + MATURITY_WEIGHT.get(level, 3) - 2 * [k for k, _ in LANES].index(CONTROL_LANE.get(cid, "build")),
        })

    # A dependency blocks only while nothing has happened on it: work that has started, here or upstream, is live.
    by_key = {t["key"]: t for t in tasks}
    untouched = {t["key"] for t in tasks if t["progress"]["done"] == 0 and not (t["_flags"]["running"] or t["_flags"]["waiting"])}
    for t in tasks:
        f = t.pop("_flags")
        if f["proven"]:
            t["state"] = "proven"
        elif f["waiting"]:
            t["state"] = "review"
        elif f["running"]:
            t["state"] = "agent"
        else:
            blocking = [d for d in t["dependsOn"] if d in untouched and d in by_key]
            t["state"] = "needs_you" if t["progress"]["done"] > 0 or not blocking else "todo"
            t["blockedBy"] = blocking if t["state"] == "todo" else []
        if f["empty"]:
            t["state"] = "todo"
            t["blockedBy"] = sorted(set(t.get("blockedBy") or []) | {"control:FMC-INV-01"} - {t["key"]})
    tasks.sort(key=lambda t: (-t["score"], t["controlId"]))
    for i, t in enumerate(tasks, 1):
        t["priority"] = i
    return tasks


def _record_changes(db: Session, plan: Dict[str, Any], tasks: List[Dict[str, Any]]) -> None:
    """Compare with the last read; log tasks added, dropped and newly proven, and keep the new snapshot."""
    now = {t["key"]: t["state"] for t in tasks}
    before = plan["snapshot"] or {}
    if now == before:
        return
    names = {t["key"]: t["controlName"] for t in tasks}
    added = [k for k in now if k not in before]
    dropped = [k for k in before if k not in now]
    proven = [k for k in now if now[k] == "proven" and before.get(k) not in (None, "proven")]
    moved = [k for k in now if k in before and now[k] != before[k] and k not in proven]
    parts = []
    if before and added:
        parts.append(f"{len(added)} new: {', '.join(names[k] for k in added[:3])}")
    if dropped:
        parts.append(f"{len(dropped)} no longer needed")
    if proven:
        parts.append(f"{len(proven)} proven: {', '.join(names[k] for k in proven[:3])}")
    if moved:
        parts.append(f"{len(moved)} moved")
    summary = "Plan created with " + f"{len(tasks)} tasks" if not before else "; ".join(parts) or "Plan updated"
    db.execute(
        text("INSERT INTO plan_changes (id, org_id, summary, detail_json, created_at) VALUES (:id, :org, :summary, :detail, :now)"),
        {"id": str(uuid.uuid4()), "org": plan["org_id"], "summary": summary[:1000],
         "detail": json.dumps({"added": added, "dropped": dropped, "proven": proven, "moved": moved}), "now": _now()},
    )
    plan["snapshot"] = now
    _save_plan(db, plan)


def _view(db: Session, org_id: str) -> Dict[str, Any]:
    plan = _plan_row(db, org_id)
    disc = _discovery(db, org_id, plan)
    out: Dict[str, Any] = {"exists": plan["exists"], "status": plan["status"], "discovery": disc, "lanes": [{"key": k, "label": v} for k, v in LANES]}
    if plan["status"] == "active":
        tasks = _tasks(db, org_id, plan, disc)
        _record_changes(db, plan, tasks)
        db.commit()
        changes = db.execute(
            text("SELECT summary, created_at FROM plan_changes WHERE org_id = :org ORDER BY created_at DESC LIMIT 8"), {"org": org_id}
        ).mappings().all()
        out.update({
            "tasks": tasks,
            "summary": {state: sum(1 for t in tasks if t["state"] == state) for state in STATES},
            "changes": [{"summary": c["summary"], "at": c["created_at"]} for c in changes],
        })
    return out


# --- routes ----------------------------------------------------------------------------------------------------


@router.get("")
async def get_plan(m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _ensure_tables(db)
    return _view(db, m.org_id)


def _validate(key: str, value: Any) -> Any:
    if key not in QUESTION_KEYS:
        raise HTTPException(status_code=422, detail="Unknown question")
    q = next(q for q in QUESTIONS if q["key"] == key)
    if q["kind"] == "text":
        if not isinstance(value, str) or len(value.strip()) < 10:
            raise HTTPException(status_code=422, detail="Write a sentence or two")
        return value.strip()[:6000]
    if q["kind"] == "single":
        if value not in q["options"]:
            raise HTTPException(status_code=422, detail="Choose one of the options")
        return value
    if q["kind"] == "multi":
        if not isinstance(value, list) or not value or any(v not in q["options"] for v in value):
            raise HTTPException(status_code=422, detail="Choose at least one option")
        return list(dict.fromkeys(value))
    if q["kind"] == "maturity":
        if not isinstance(value, dict) or any(k not in MATURITY_CONTROLS or v not in MATURITY for k, v in value.items()):
            raise HTTPException(status_code=422, detail="Choose not yet, partly or in place for each")
        return value
    if q["kind"] == "people":
        if not isinstance(value, dict) or any(k not in ROLES for k in value):
            raise HTTPException(status_code=422, detail="Unknown role")
        return {k: str(v).strip()[:200] for k, v in value.items() if str(v or "").strip()}
    frameworks = _catalogue()["frameworks"]
    if not isinstance(value, list) or not value or any(v not in frameworks for v in value):
        raise HTTPException(status_code=422, detail="Choose at least one framework")
    return list(dict.fromkeys(value))


def _say(value: Any, key: str) -> str:
    """The answer as a line in the conversation."""
    options = next(q for q in QUESTIONS if q["key"] == key).get("options") or {}
    if key == "frameworks":
        names = _catalogue()["frameworks"]
        return ", ".join(names[v]["name"] for v in value)
    if key == "maturity":
        controls = {c["id"]: c["name"] for c in _catalogue()["commonControls"]}
        return "; ".join(f"{controls.get(k, k)}: {MATURITY[v].lower()}" for k, v in value.items())
    if key == "people":
        return "; ".join(f"{ROLES[k]}: {v}" for k, v in value.items()) or "None named yet"
    if isinstance(value, list):
        return ", ".join(options.get(v, v) for v in value)
    return options.get(value, value) if isinstance(value, str) else str(value)


@router.post("/discovery")
async def answer(body: AnswerBody, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    _ensure_tables(db)
    value = _validate(body.key, body.value)
    plan = _plan_row(db, m.org_id)
    now = _now()
    plan["profile"][body.key] = {"value": value, "source": "answer", "basis": "You answered"}
    plan["transcript"].append({"role": "user", "key": body.key, "text": value if body.key == "about" else _say(value, body.key), "at": now})
    if body.key == "about":
        fields, how, understood = await _read_text(db, m.org_id, value)
        for k, v in fields.items():
            plan["profile"][f"{k}__description"] = {"value": v, "source": "description", "basis": "From your description" + (" (read by your AI provider)" if how == "llm" else "")}
        took = ", ".join(next(q["short"] for q in QUESTIONS if q["key"] == k) for k in fields)
        plan["transcript"].append({"role": "agent", "key": "about", "at": now, "text": (understood + " " if understood else "")
                                   + (f"I filled in: {took}. You can change any of it in the map." if fields else "I could not fill anything in from that; I will ask.")})
    _save_plan(db, plan, m.user_id)
    db.commit()
    return _view(db, m.org_id)


@router.post("/generate")
async def generate(m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    _ensure_tables(db)
    plan = _plan_row(db, m.org_id)
    if "frameworks" not in plan["profile"]:
        raise HTTPException(status_code=409, detail="Confirm the frameworks first")
    plan["status"] = "active"
    plan["transcript"].append({"role": "agent", "key": "generate", "text": "I built your plan from the frameworks and your estate.", "at": _now()})
    _save_plan(db, plan, m.user_id)
    db.commit()
    return _view(db, m.org_id)


def _task_or_404(db: Session, org_id: str, key: str) -> Dict[str, Any]:
    view = _view(db, org_id)
    task = next((t for t in view.get("tasks") or [] if t["key"] == key), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/tasks/{key}")
async def patch_task(key: str, body: TaskPatch, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _task_or_404(db, m.org_id, key)
    db.execute(
        text(
            "INSERT INTO plan_task_overrides (org_id, task_key, owner, note, updated_by, updated_at) VALUES (:org, :key, :owner, :note, :by, :now) "
            "ON CONFLICT (org_id, task_key) DO UPDATE SET owner = COALESCE(:owner, plan_task_overrides.owner), note = COALESCE(:note, plan_task_overrides.note), updated_by = :by, updated_at = :now"
        ),
        {"org": m.org_id, "key": key, "owner": (body.owner or "").strip() or None, "note": (body.note or "").strip() or None, "by": m.user_id, "now": _now()},
    )
    db.commit()
    return _view(db, m.org_id)


@router.post("/tasks/{key}/attest")
async def attest_task(key: str, body: AttestBody, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    _ensure_tables(db)
    task = _task_or_404(db, m.org_id, key)
    if task["kind"] != "org":
        raise HTTPException(status_code=409, detail="System tasks close from each system's evidence, not an attestation")
    db.execute(
        text("INSERT INTO plan_attestations (id, org_id, task_key, statement, reference, attested_by, created_at) VALUES (:id, :org, :key, :statement, :reference, :by, :now)"),
        {"id": str(uuid.uuid4()), "org": m.org_id, "key": key, "statement": body.statement.strip(), "reference": (body.reference or "").strip() or None, "by": m.user_id, "now": _now()},
    )
    db.commit()
    return _view(db, m.org_id)
