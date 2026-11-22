"""The report model behind the Reports page: one dict per role, built only from the record.

Every number the page, the PDF, the DOCX and the CSV show comes from here, computed on read from the same
sources the rest of the app uses: the release gate and its path forward, the clause map, tasks, risks,
discovery, the hash-chained ledgers and evidence packs. A section with nothing behind it is empty, never
filled with a guess.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from statistics import median
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.services.clause_map_service import CHECK_CONTROLS, _catalogue, clause_map, evaluation_links
from src.application.services.plan_assignment_service import plan_frameworks

ROLES = ("executive", "compliance", "engineering", "auditor", "risk")

# The four states a person reads readiness in; mirrors READINESS_OF on the frameworks page (frameworks/parts.tsx).
READINESS_OF = {
    "proven": "met", "attested": "met", "excluded": "met",
    "partial": "progress", "estimated": "progress", "planned": "progress", "atorg": "progress",
    "fails": "attention", "stale": "attention",
    "open": "notstarted", "none": "notstarted",
}
SEVERITY_LEVEL = {"low": 1, "medium": 2, "high": 3, "critical": 4}
LIKELIHOOD_LEVEL = {"rare": 1, "unlikely": 2, "possible": 3, "likely": 4, "almost certain": 5}
OPEN_RISK = ("open", "acceptance_pending")
SAMPLE_SIZE = 25
OVERSIGHT_DAYS = 30


def _json(value: Any, default: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def _parse(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def readiness(cell: str) -> str:
    return READINESS_OF.get(cell, "notstarted")


def _pct(part: float, whole: float) -> int:
    return round(100 * part / whole) if whole else 0


@dataclass(frozen=True)
class Sources:
    """What the model reads that lives in the api layer, handed in by the route so this layer never imports it.

    gate_payload(db, system_id, tier) is the release gate with its path forward (fairness_runs._gate_payload);
    verify_run_chain(events) recomputes one workflow run's hash chain (packs._verify_chain).
    """

    gate_payload: Callable[[Session, str, str], Dict[str, Any]]
    verify_run_chain: Callable[[List[Dict[str, Any]]], bool]


class Estate:
    """The systems in scope and, lazily, each one's gate and clause map, so every section shares one computation."""

    def __init__(self, db: Session, org_id: str, system_id: Optional[str], framework: Optional[str], sources: "Sources"):
        self.db, self.org_id, self.sources = db, org_id, sources
        catalogue = _catalogue()["frameworks"]
        self.plan = [k for k in plan_frameworks(db, org_id) if k in catalogue]
        rows = db.execute(
            text("SELECT id, name, risk_tier, metadata_json FROM governance_ai_systems "
                 "WHERE org_id = :org AND COALESCE(lifecycle_stage, '') <> 'retired' ORDER BY name"),
            {"org": org_id},
        ).fetchall()
        self.all = [{"id": r[0], "name": r[1], "tier": r[2] or "medium", "frameworks": self._frameworks(_json(r[3], {}))} for r in rows]
        followed = list(dict.fromkeys(self.plan + [k for s in self.all for k in s["frameworks"]]))
        self.framework = framework if framework in catalogue else (followed[0] if followed else None)
        self.framework_name = catalogue.get(self.framework, {}).get("name") if self.framework else None
        self.followed = followed
        self.systems = [s for s in self.all if (system_id is None or s["id"] == system_id)]
        self.in_scope = [s for s in self.systems if self.framework and self.framework in s["frameworks"]]
        self._gates: Dict[str, Dict[str, Any]] = {}
        self._maps: Dict[str, Dict[str, Any]] = {}

    def _frameworks(self, metadata: Dict[str, Any]) -> List[str]:
        """A system answers to its confirmed frameworks; without a confirmation it inherits the plan's."""
        applicability = metadata.get("applicability")
        if isinstance(applicability, dict):
            return [f["key"] for f in applicability.get("frameworks") or [] if isinstance(f, dict) and f.get("key")]
        return list(self.plan)

    def gate(self, system: Dict[str, Any]) -> Dict[str, Any]:
        if system["id"] not in self._gates:
            self._gates[system["id"]] = self.sources.gate_payload(self.db, system["id"], system["tier"])
        return self._gates[system["id"]]

    def clauses(self, system: Dict[str, Any], framework: Optional[str] = None) -> List[Dict[str, Any]]:
        """Clauses of one framework for one system; every framework something reaches is computed once."""
        if system["id"] not in self._maps:
            self._maps[system["id"]] = {fw["key"]: fw for fw in clause_map(self.gate(system))["frameworks"]}
        fw = self._maps[system["id"]].get(framework or self.framework)
        if fw is None and (framework or self.framework):  # nothing reached it: every clause open
            fw = clause_map(self.gate(system), frameworks=[framework or self.framework])["frameworks"][0]
            self._maps[system["id"]][fw["key"]] = fw
        return fw["clauses"] if fw else []


# --- sections -------------------------------------------------------------------------------------------------


def readiness_section(e: Estate) -> Dict[str, Any]:
    counts = {"met": 0, "progress": 0, "attention": 0, "notstarted": 0}
    for s in e.in_scope:
        for c in e.clauses(s):
            counts[readiness(c["cell"])] += 1
    total = sum(counts.values())
    return {**counts, "total": total, "pct": _pct(counts["met"], total), "systems": len(e.in_scope)}


def _owners(e: Estate) -> Dict[Tuple[str, str], str]:
    """(system id or "", requirement key) -> who holds the open task for it."""
    rows = e.db.execute(
        text("SELECT t.system_id, t.subject_id, COALESCE(u.name, u.email, t.assignee_agent) FROM org_tasks t "
             "LEFT JOIN users u ON CAST(u.id AS TEXT) = t.assignee_user_id "
             "WHERE t.org_id = :org AND t.status <> 'done' AND t.subject_type = 'requirement'"),
        {"org": e.org_id},
    ).fetchall()
    return {(r[0] or "", r[1]): r[2] for r in rows if r[1] and r[2]}


def road_section(e: Estate, ready: Dict[str, Any]) -> Dict[str, Any]:
    """The gate's path forward per system, each step scored by the requirements it would close in this framework.

    A step closes the clauses its check (or evaluation) reaches through the crosswalk that are not met yet for that
    system; each requirement counts once. Gain is in readiness points: closed cells over every in-scope cell.
    """
    total = ready["total"]
    cat = _catalogue()
    owners = _owners(e) if e.in_scope else {}
    steps: List[Dict[str, Any]] = []
    for s in e.in_scope:
        open_keys = {c["key"]: c for c in e.clauses(s) if readiness(c["cell"]) != "met"}
        path = e.gate(s).get("path") or {}
        option = next((o for o in path.get("options") or [] if o.get("kind") == "measured_first"), None) or next(iter(path.get("options") or []), None)
        taken: set = set()
        for step in (option or {}).get("steps") or []:
            control = CHECK_CONTROLS.get(step.get("check"))
            if control:
                reach = {l["requirement"]["key"] for l in cat["by_control"].get(control, []) if l["requirement"]["framework"] == e.framework}
            else:
                reach = set(evaluation_links(step.get("evaluationId") or step.get("check") or ""))
            closes = sorted((reach & set(open_keys)) - taken)
            if not closes:
                continue
            taken.update(closes)
            owner = next((owners[(sid, k)] for k in closes for sid in (s["id"], "") if (sid, k) in owners), None)
            steps.append({
                "systemId": s["id"], "systemName": s["name"], "check": step.get("check"), "kind": step.get("action"), "action": step_label(step),
                "evidenceClass": step.get("evidenceClass"), "closes": closes, "gain": round(100 * len(closes) / total, 1) if total else 0,
                "owner": owner,
            })
    steps.sort(key=lambda x: -x["gain"])
    steps = steps[:8]
    return {"start": ready["pct"], "steps": steps, "forecast": min(100, round(ready["pct"] + sum(x["gain"] for x in steps)))}


ACTION_WORDS = {
    "fairness_run": "Run a fairness test", "monitoring_snapshot": "Take a monitoring snapshot", "evaluation_run": "Run an evaluation",
    "environmental_assessment": "Run the environmental assessment", "attest": "Attest", "evidence_upload": "Upload evidence",
}


def step_label(step: Dict[str, Any]) -> str:
    """A path-forward step in words: "Run an evaluation for human oversight", or the named catalogue evaluation."""
    from src.application.services.fairness_run_service import GATE_CHECKS  # function-level: that module imports clause_map

    evaluation = _catalogue()["evaluations"].get(step.get("evaluationId") or "")
    if evaluation:
        return f"Run {step['evaluationId']} {evaluation.get('name', '')}".strip()
    check = {key: label for key, label, _ in GATE_CHECKS}.get(step.get("check"), step.get("check") or "")
    return f"{ACTION_WORDS.get(step.get('action'), 'Act on')} for {check.lower()}"


def _proof_of(clause: Dict[str, Any]) -> str:
    """How a clause is backed: measured by FairMind, a tool estimate, a person's word, or nothing yet.
    Only met or in-progress clauses count as backed; a failing or stale one has no proof to show."""
    if readiness(clause["cell"]) not in ("met", "progress"):
        return "none"
    backing = [c for c in clause.get("checks") or [] if not c.get("fails") and c.get("state") in ("proven", "attested")]
    if any(c["state"] == "proven" and c.get("evidenceClass") == "measured" for c in backing):
        return "measured"
    if any(c["state"] == "proven" and c.get("evidenceClass") == "tool_estimated" for c in backing):
        return "estimated"
    return "attested" if backing or clause.get("state") == "excluded" else "none"


def proof_section(e: Estate) -> Dict[str, Any]:
    zero = lambda: {"measured": 0, "estimated": 0, "attested": 0, "none": 0}  # noqa: E731
    total, by_system, by_group = zero(), [], {}
    for s in e.in_scope:
        mine = zero()
        for c in e.clauses(s):
            kind = _proof_of(c)
            mine[kind] += 1
            total[kind] += 1
            group = by_group.setdefault(c.get("group") or "Other", zero())
            group[kind] += 1
        by_system.append({"systemId": s["id"], "name": s["name"], **mine})
    return {**total, "bySystem": by_system, "byGroup": [{"group": g, **v} for g, v in by_group.items()]}


def systems_section(e: Estate) -> List[Dict[str, Any]]:
    out = []
    for s in e.systems:
        g = e.gate(s)
        out.append({
            "id": s["id"], "name": s["name"], "tier": s["tier"], "verdict": g.get("verdict"), "approvalStatus": g.get("approvalStatus"),
            "confidence": g.get("confidence"),
            "checks": [{"key": c["key"], "label": c.get("label"), "state": c["state"], "fails": bool(c.get("fails")), "stale": bool(c.get("stale"))} for c in g.get("checks", [])],
        })
    return out


def grid_section(e: Estate, limit: int = 12) -> Dict[str, Any]:
    """The requirements with the most gaps across in-scope systems, one cell per system."""
    rows: Dict[str, Dict[str, Any]] = {}
    for s in e.in_scope:
        for c in e.clauses(s):
            row = rows.setdefault(c["key"], {"key": c["key"], "control": c["control"], "title": c["title"], "group": c.get("group"), "cells": {}})
            row["cells"][s["id"]] = c["cell"]
    ranked = sorted(rows.values(), key=lambda r: (-sum(readiness(v) != "met" for v in r["cells"].values()), r["control"]))
    systems = [{"id": s["id"], "name": s["name"]} for s in e.in_scope]
    return {"systems": systems, "requirements": [{**r, "cells": [r["cells"].get(s["id"], "none") for s in e.in_scope]} for r in ranked[:limit]]}


def governed_section(e: Estate) -> Dict[str, Any]:
    try:
        assets = e.db.execute(
            text("SELECT name, kind, source FROM governance_discovered_assets WHERE org_id = :org AND status = 'new' ORDER BY discovered_at DESC"),
            {"org": e.org_id},
        ).fetchall()
    except Exception:  # discovery tables are created on first use
        e.db.rollback()
        assets = []
    registered = len(e.all)
    gates = [e.gate(s) for s in e.all]
    return {
        "found": registered + len(assets), "registered": registered,
        "checked": sum(1 for g in gates if g.get("proven")), "approved": sum(1 for g in gates if g.get("approvalStatus") == "approved"),
        "unregistered": [{"name": a[0], "kind": a[1], "source": a[2]} for a in assets[:6]], "unregisteredCount": len(assets),
    }


def oversight_section(e: Estate, today: date) -> Dict[str, Any]:
    """Per day for the last 30 days: steps agents completed and decisions people made, from the ledgers."""
    since = (today - timedelta(days=OVERSIGHT_DAYS - 1)).isoformat()
    days = {(today - timedelta(days=i)).isoformat(): {"agentSteps": 0, "decisions": 0} for i in range(OVERSIGHT_DAYS)}

    def bump(ts: Optional[str], key: str) -> None:
        if ts and ts[:10] in days:
            days[ts[:10]][key] += 1

    try:
        events = e.db.execute(
            text("SELECT ev.kind, ev.payload_json, ev.created_at FROM workflow_run_events ev JOIN workflow_runs r ON r.id = ev.run_id "
                 "WHERE r.org_id = :org AND ev.created_at >= :since AND ev.kind IN ('step.completed', 'gate.decided')"),
            {"org": e.org_id, "since": since},
        ).fetchall()
    except Exception:
        e.db.rollback()
        events = []
    for kind, payload, at in events:
        if kind == "gate.decided":
            bump(at, "decisions")
        elif _json(payload, {}).get("source") == "agent":
            bump(at, "agentSteps")
    try:
        for (at,) in e.db.execute(text("SELECT created_at FROM autopilot_events WHERE org_id = :org AND created_at >= :since"), {"org": e.org_id, "since": since}):
            bump(at, "agentSteps")
    except Exception:
        e.db.rollback()
    approvals = e.db.execute(
        text("SELECT a.created_at, a.decided_at, a.decided_by, a.status FROM governance_approval_requests a "
             "JOIN governance_ai_systems s ON s.id = a.ai_system_id WHERE s.org_id = :org AND a.decided_at >= :since"),
        {"org": e.org_id, "since": since},
    ).fetchall()
    waits = []
    for created, decided, by, status in approvals:
        bump(decided, "decisions")
        c, d = _parse(created), _parse(decided)
        if c and d:
            waits.append((d - c).total_seconds() / 3600)
    series = [{"date": k, **v} for k, v in sorted(days.items())]
    return {
        "days": series, "agentSteps": sum(d["agentSteps"] for d in series), "decisions": sum(d["decisions"] for d in series),
        "medianWaitHours": round(median(waits), 1) if waits else None,
        "approvedWithoutPerson": sum(1 for _, _, by, status in approvals if status == "approved" and not by),
    }


def _source_of(check: Dict[str, Any]) -> str:
    if check.get("check") in CHECK_CONTROLS and check.get("state") == "proven":
        return check.get("label") or check["check"]
    if str(check.get("check") or "").startswith("EV-") and check.get("state") == "proven":
        return "Evaluation runs"
    return "Attested by people"


def crosswalk_section(e: Estate, top: int = 3) -> Dict[str, Any]:
    """What evidence already covers, per framework, through the clause map: the followed one and the best others."""
    cat = _catalogue()["frameworks"]
    covered: Dict[str, Dict[str, str]] = {}  # framework -> clause key -> source of its strongest backing
    for s in e.systems:
        self_maps = e._maps.get(s["id"]) or {fw["key"]: fw for fw in clause_map(e.gate(s))["frameworks"]}
        e._maps[s["id"]] = self_maps
        for key, fw in self_maps.items():
            for c in fw["clauses"]:
                if readiness(c["cell"]) in ("met", "progress"):
                    backing = next((x for x in c.get("checks") or [] if not x.get("fails") and x.get("state") in ("proven", "attested")), None)
                    if backing:
                        covered.setdefault(key, {}).setdefault(c["key"], _source_of(backing))
    totals = {k: len(_catalogue()["by_framework"].get(k, [])) for k in covered}
    coverage = {k: _pct(len(v), totals[k]) for k, v in covered.items() if totals.get(k)}
    followed = [k for k in e.followed if k in coverage] or ([e.framework] if e.framework in coverage else [])
    others = sorted((k for k in coverage if k not in e.followed), key=lambda k: -coverage[k])[:top]
    frameworks = followed[:1] + others
    sources = sorted({src for k in frameworks for src in covered[k].values()})
    links = [[sum(1 for v in covered[k].values() if v == src) for k in frameworks] for src in sources]
    return {
        "frameworks": [{"key": k, "name": cat.get(k, {}).get("name", k), "followed": k in e.followed, "coverage": coverage[k]} for k in frameworks],
        "sources": sources, "links": links,
    }


def tasks_section(e: Estate, today: date) -> Dict[str, Any]:
    params: Dict[str, Any] = {"org": e.org_id}
    scope = ""
    if len(e.systems) == 1 and len(e.all) > 1:
        scope, params["sid"] = " AND (t.system_id = :sid OR t.system_id IS NULL)", e.systems[0]["id"]
    rows = e.db.execute(
        text("SELECT t.title, t.subject_label, t.due_date, COALESCE(u.name, u.email, t.assignee_agent) FROM org_tasks t "
             "LEFT JOIN users u ON CAST(u.id AS TEXT) = t.assignee_user_id WHERE t.org_id = :org AND t.status <> 'done'" + scope),
        params,
    ).fetchall()
    owners: Dict[str, Dict[str, int]] = {}
    late = []
    for title, subject, due, who in rows:
        name = who or "Unassigned"
        days_late = (today - date.fromisoformat(due)).days if due else 0
        bucket = owners.setdefault(name, {"onTime": 0, "overdue": 0})
        bucket["overdue" if days_late > 0 else "onTime"] += 1
        if days_late > 0:
            late.append({"title": title, "subject": subject, "owner": name, "daysLate": days_late})
    late.sort(key=lambda x: -x["daysLate"])
    return {
        "open": len(rows), "overdue": len(late), "overdueList": late[:5],
        "byOwner": sorted(({"owner": k, **v} for k, v in owners.items()), key=lambda x: -(x["onTime"] + x["overdue"])),
    }


def _latest_runs(e: Estate, evaluation_id: str) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    out = []
    for s in e.systems:
        rows = e.db.execute(
            text("SELECT content_json FROM governance_evidence WHERE system_id = :sid AND evidence_type = 'evaluation_run' "
                 "AND content_json LIKE :like ORDER BY created_at DESC LIMIT 5"),
            {"sid": s["id"], "like": f"%{evaluation_id}%"},
        ).fetchall()
        run = next((body for body in (_json(r[0], {}) for r in rows) if body.get("evaluationId") == evaluation_id), None)
        if run:
            out.append((s, run))
    return out


def engineering_section(e: Estate) -> Dict[str, Any]:
    tools = []
    for s, run in _latest_runs(e, "EV-SEC-06"):
        for r in run.get("detail") if isinstance(run.get("detail"), list) else []:
            if isinstance(r, dict) and r.get("tool"):
                tools.append({"systemId": s["id"], "systemName": s["name"], "agent": r.get("agent"), "tool": r["tool"], "policy": r.get("policy"),
                              "gated": bool(r.get("gated")), "effect": r.get("effect")})
    drift = []
    for s in e.systems:
        rows = e.db.execute(
            text("SELECT content_json, created_at FROM governance_evidence WHERE system_id = :sid AND evidence_type = 'fairness_test' ORDER BY created_at LIMIT 26"),
            {"sid": s["id"]},
        ).fetchall()
        points, threshold = [], None
        for content, at in rows:
            body = _json(content, {})
            attributes = body.get("attributes") if isinstance(body.get("attributes"), list) else []
            ratios = [a["disparate_impact_ratio"] for a in attributes if isinstance(a, dict) and isinstance(a.get("disparate_impact_ratio"), (int, float))]
            if ratios:
                points.append({"at": at, "value": round(min(ratios), 3)})
                threshold = (body.get("thresholds") or {}).get("disparate_impact_ratio", threshold)
        if len(points) >= 2:
            drift.append({"systemId": s["id"], "systemName": s["name"], "threshold": threshold, "points": points})
    ids = [s["id"] for s in e.systems]
    fixes = []
    if ids:
        marks = ", ".join(f":s{i}" for i in range(len(ids)))
        fixes = [
            {"title": r[0], "systemName": r[1], "priority": r[2], "status": r[3], "owner": r[4]}
            for r in e.db.execute(
                text(f"SELECT t.title, s.name, t.priority, t.status, t.owner FROM governance_remediation_tasks t JOIN governance_ai_systems s ON s.id = t.system_id "
                     f"WHERE t.system_id IN ({marks}) AND t.status NOT IN ('done', 'closed', 'resolved') ORDER BY CASE t.priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END LIMIT 8"),
                {f"s{i}": sid for i, sid in enumerate(ids)},
            ).fetchall()
        ]
    return {"toolExposure": tools, "fairnessDrift": drift, "fixes": fixes}


def _chains(e: Estate) -> Dict[str, Any]:
    """Every hash chain the organisation has, verified now; the newest entries for the strip."""
    from src.application.services.internal_audit_rules import verify_chain as verify_audit
    from src.application.services.system_lifecycle_service import verify_chain as verify_lifecycle

    chains, recent = [], []
    try:
        rows = e.db.execute(
            text("SELECT ev.run_id, ev.seq, ev.kind, ev.step_id, ev.payload_json, ev.canonical_json, ev.prev_hash, ev.hash, ev.created_at "
                 "FROM workflow_run_events ev JOIN workflow_runs r ON r.id = ev.run_id WHERE r.org_id = :org ORDER BY ev.run_id, ev.seq"),
            {"org": e.org_id},
        ).mappings().fetchall()
    except Exception:
        e.db.rollback()
        rows = []
    by_run: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        by_run.setdefault(r["run_id"], []).append(dict(r))
        recent.append({"at": r["created_at"], "kind": "decision" if r["kind"] == "gate.decided" else "agent" if _json(r["payload_json"], {}).get("source") == "agent" else "step", "hash": r["hash"]})
    broken = [run for run, ev in by_run.items() if not e.sources.verify_run_chain(ev)]
    chains.append({"kind": "Workflow runs", "chains": len(by_run), "entries": len(rows), "broken": len(broken)})
    try:
        audit_rows = e.db.execute(
            text("SELECT ev.audit_id, ev.seq, ev.kind, ev.actor, ev.payload, ev.prev_hash, ev.hash, ev.created_at FROM internal_audit_events ev "
                 "JOIN internal_audits a ON a.id = ev.audit_id WHERE a.org_id = :org ORDER BY ev.audit_id, ev.seq"),
            {"org": e.org_id},
        ).mappings().fetchall()
    except Exception:
        e.db.rollback()
        audit_rows = []
    by_audit: Dict[str, List[Dict[str, Any]]] = {}
    for r in audit_rows:
        by_audit.setdefault(r["audit_id"], []).append({**dict(r), "payload": _json(r["payload"], r["payload"])})
        recent.append({"at": r["created_at"], "kind": "audit", "hash": r["hash"]})
    chains.append({"kind": "Internal audits", "chains": len(by_audit), "entries": len(audit_rows), "broken": sum(1 for ev in by_audit.values() if not verify_audit(ev))})
    lifecycle = [verify_lifecycle(e.db, s["id"]) for s in e.all]
    chains.append({"kind": "System changes", "chains": len(lifecycle), "entries": None, "broken": sum(1 for v in lifecycle if v.get("status") == "broken")})
    seals = e.db.execute(
        text("SELECT d.chain_head, d.created_at FROM governance_decision_seals d JOIN governance_ai_systems s ON s.id = d.system_id WHERE s.org_id = :org"),
        {"org": e.org_id},
    ).fetchall()
    for head, at in seals:
        recent.append({"at": at, "kind": "seal", "hash": head})
    chains.append({"kind": "Decision seals", "chains": len(seals), "entries": len(seals), "broken": 0})
    recent.sort(key=lambda r: r["at"] or "")
    entries = sum(c["entries"] or 0 for c in chains)
    return {"chains": chains, "entries": entries, "intact": all(c["broken"] == 0 for c in chains), "recent": recent[-150:],
            "head": recent[-1]["hash"] if recent else None}


def auditor_section(e: Estate) -> Dict[str, Any]:
    ledger = _chains(e)
    ids = [s["id"] for s in e.systems]
    evidence = []
    if ids:
        marks = ", ".join(f":s{i}" for i in range(len(ids)))
        evidence = e.db.execute(
            text(f"SELECT g.id, g.title, g.evidence_type, g.metadata_json, s.name FROM governance_evidence g JOIN governance_ai_systems s ON s.id = g.system_id "
                 f"WHERE g.system_id IN ({marks}) ORDER BY g.id"),
            {f"s{i}": sid for i, sid in enumerate(ids)},
        ).fetchall()
    seed = ledger["head"] or e.org_id
    picked = random.Random(seed).sample(list(evidence), min(SAMPLE_SIZE, len(evidence))) if evidence else []
    sample = {
        "seed": seed, "size": len(picked), "population": len(evidence),
        "items": [{"id": r[0], "title": r[1], "type": r[2], "provenance": _json(r[3], {}).get("provenance_class") or "manual", "systemName": r[4]} for r in picked],
    }
    soa_system = e.in_scope[0] if e.in_scope else None
    soa = None
    if soa_system:
        soa = {"systemId": soa_system["id"], "systemName": soa_system["name"], "controls": [
            {"key": c["key"], "control": c["control"], "title": c["title"], "group": c.get("group"), "readiness": readiness(c["cell"]),
             "applicability": c.get("applicability"), "justification": c.get("justification")}
            for c in e.clauses(soa_system)
        ]}
    packs = [
        {"id": r[0], "title": r[1], "createdAt": r[2], "manifestHash": r[3], "items": len((_json(r[4], {}) or {}).get("evidence") or [])}
        for r in e.db.execute(
            text("SELECT id, title, created_at, manifest_hash, manifest_json FROM governance_evidence_packs WHERE org_id = :org ORDER BY created_at DESC LIMIT 6"),
            {"org": e.org_id},
        ).fetchall()
    ]
    return {"ledger": {k: v for k, v in ledger.items() if k != "head"}, "sample": sample, "soa": soa, "packs": packs}


def risk_section(e: Estate, today: date) -> Dict[str, Any]:
    ids = [s["id"] for s in e.systems]
    if not ids:
        return {"risks": [], "heat": [], "acceptanceWaiting": []}
    marks = ", ".join(f":s{i}" for i in range(len(ids)))
    rows = e.db.execute(
        text(f"SELECT r.id, r.title, s.name, r.severity, r.likelihood, r.status, r.metadata_json, r.updated_at FROM governance_risks r "
             f"JOIN governance_ai_systems s ON s.id = r.system_id WHERE r.system_id IN ({marks}) ORDER BY r.risk_score DESC"),
        {f"s{i}": sid for i, sid in enumerate(ids)},
    ).fetchall()
    risks, waiting, heat = [], [], {}
    for rid, title, system, severity, likelihood, status, metadata, updated in rows:
        meta = _json(metadata, {})
        pending = meta.get("pendingAcceptance") or {}
        impact, chance = SEVERITY_LEVEL.get(severity, 2), LIKELIHOOD_LEVEL.get(likelihood, 3)
        risks.append({"id": rid, "title": title, "systemName": system, "severity": severity, "likelihood": likelihood, "impact": impact, "chance": chance,
                      "status": status, "owner": pending.get("owner") or meta.get("owner")})
        if status in OPEN_RISK:
            heat[(chance, impact)] = heat.get((chance, impact), 0) + 1
        if status == "acceptance_pending":
            proposed = _parse(pending.get("proposedAt"))
            waiting.append({"id": rid, "title": title, "systemName": system, "owner": pending.get("owner"), "proposedBy": pending.get("proposedBy"),
                            "waitingDays": (today - proposed.date()).days if proposed else None})
    return {"risks": risks, "heat": [{"chance": c, "impact": i, "count": n} for (c, i), n in sorted(heat.items())], "acceptanceWaiting": waiting}


def decisions_section(e: Estate, today: date) -> List[Dict[str, Any]]:
    ids = [s["id"] for s in e.systems]
    if not ids:
        return []
    marks = ", ".join(f":s{i}" for i in range(len(ids)))
    rows = e.db.execute(
        text(f"SELECT a.id, s.name, a.created_at, a.requested_by FROM governance_approval_requests a JOIN governance_ai_systems s ON s.id = a.ai_system_id "
             f"WHERE a.ai_system_id IN ({marks}) AND a.status = 'pending' ORDER BY a.created_at"),
        {f"s{i}": sid for i, sid in enumerate(ids)},
    ).fetchall()
    return [{"id": r[0], "systemName": r[1], "requestedBy": r[3], "waitingDays": (today - _parse(r[2]).date()).days if _parse(r[2]) else None} for r in rows]


# --- the model ------------------------------------------------------------------------------------------------

SECTIONS: Dict[str, Tuple[str, ...]] = {
    "executive": ("readiness", "road", "governed", "proof", "oversight", "decisions", "risk"),
    "compliance": ("readiness", "road", "proof", "crosswalk", "tasks", "grid"),
    "engineering": ("systems", "engineering"),
    "auditor": ("readiness", "auditor", "proof"),
    "risk": ("risk",),
}


def build_overview(db: Session, org_id: str, role: str, sources: Sources, system_id: Optional[str] = None, framework: Optional[str] = None,
                   today: Optional[date] = None) -> Dict[str, Any]:
    if role not in ROLES:
        raise ValueError(f"Unknown role {role!r}")
    today = today or datetime.now(timezone.utc).date()
    e = Estate(db, org_id, system_id, framework, sources)
    model: Dict[str, Any] = {
        "role": role,
        "scope": {"systemId": system_id, "systemName": e.systems[0]["name"] if system_id and e.systems else None},
        "framework": {"key": e.framework, "name": e.framework_name},
        "followed": e.followed,
        "systemsCount": len(e.systems),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
    ready = readiness_section(e)
    builders: Dict[str, Callable[[], Any]] = {
        "readiness": lambda: ready,
        "road": lambda: road_section(e, ready),
        "governed": lambda: governed_section(e),
        "proof": lambda: proof_section(e),
        "oversight": lambda: oversight_section(e, today),
        "decisions": lambda: decisions_section(e, today),
        "risk": lambda: risk_section(e, today),
        "crosswalk": lambda: crosswalk_section(e),
        "tasks": lambda: tasks_section(e, today),
        "grid": lambda: grid_section(e),
        "systems": lambda: systems_section(e),
        "engineering": lambda: engineering_section(e),
        "auditor": lambda: auditor_section(e),
    }
    for name in SECTIONS[role]:
        model[name] = builders[name]()
    from src.application.services.report_briefing_service import template_briefing

    model["briefing"] = template_briefing(model)
    return model
