"""Results for catalogue evaluations, read from evidence FairMind already stores.

Five catalogue evaluations have a FairMind engine whose runs are saved per AI
system in governance_evidence: fairness runs, monitoring runs and environmental
assessments. Each is matched to one evidence type and a rule that reads the
stored checks. Nothing here runs an engine or writes data; an evaluation with
no rule has no results yet.
"""

import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.services.fairness_run_service import (
    MIN_GROUP_SIZE,
    RATE_DRIFT_THRESHOLD,
    _record_time,
    _tokens,
    error_rate_gap,
    gap_status,
    large_group_ratio,
    ratio_status,
    worst_status,
)

# Attribute names the fairness engine treats as India-specific (see fairness_run_service.ATTRIBUTE_HINTS),
# matched as whole words of the column name, so "real_estate" and "statement_type" do not count.
INDIA_ATTRIBUTES = ("caste", "social_category", "religion", "region", "state", "district", "language", "city_tier", "urban_rural")

# (status, one line on what was measured); None when the run does not speak to the evaluation.
Verdict = Optional[Tuple[str, str]]


def _ok(passed: bool) -> str:
    return "passed" if passed else "failed"


def _small_groups(attrs: List[dict]) -> str:
    """Names the groups under MIN_GROUP_SIZE rows, which are left out of a ratio and keep a failing gap from being judged."""
    small = [f"{a['attribute']} {g}" for a in attrs for g, n in a["groups"].items() if n < MIN_GROUP_SIZE]
    return f"; groups under {MIN_GROUP_SIZE} rows: {', '.join(small)}" if small else ""


def _impact_ratio(c: dict) -> Verdict:
    attrs = c.get("attributes") or []
    if not attrs:
        return None
    ratios = [(a["attribute"], large_group_ratio(a)) for a in attrs]
    detail = ", ".join(f"{name} {r:.2f}" if r is not None else f"{name} not measurable" for name, r in ratios)
    return worst_status(ratio_status(a) for a in attrs), f"Impact ratio {detail}{_small_groups(attrs)}"


def _error_rates(c: dict) -> Verdict:
    attrs = c.get("attributes") or []
    if not attrs:
        return None
    worst = max(attrs, key=error_rate_gap)
    detail = f"Largest error-rate gap {error_rate_gap(worst):.3f} ({worst['attribute']}){_small_groups(attrs)}"
    return worst_status(gap_status(a) for a in attrs), detail


def _is_india(name: str) -> bool:
    words = f"_{'_'.join(_tokens(name))}_"
    return any(f"_{h}_" in words for h in INDIA_ATTRIBUTES)


def _india(c: dict) -> Verdict:
    attrs = [a for a in c.get("attributes") or [] if _is_india(a["attribute"])]
    if not attrs:
        return None
    status = worst_status(s for a in attrs for s in (ratio_status(a), gap_status(a)))
    return status, f"Checked {', '.join(a['attribute'] for a in attrs)}{_small_groups(attrs)}"


def _fairness_drift(c: dict) -> Verdict:
    attrs = c.get("attributes") or []
    compared = [a for a in attrs if "selection_rate_stable" in a["checks"]]
    if not attrs:
        return None
    if not compared:
        return "insufficient", "No baseline run to compare against"
    drift = max(a["max_rate_drift"] for a in compared)
    # the stored max_rate_drift, not the stored check, so a run saved when a change of exactly 0.05 passed is judged as drift too
    passed = all(a["max_rate_drift"] < RATE_DRIFT_THRESHOLD and a["checks"].get("disparate_impact") for a in compared)
    return _ok(passed), f"Largest selection-rate drift {drift:.3f}"


def _energy(c: dict) -> Verdict:
    kwh = c.get("total_kwh")
    co2 = c.get("total_kg_co2e_location", c.get("total_kg_co2e_market"))
    parts = [f"{kwh:g} kWh" if isinstance(kwh, (int, float)) else None, f"{co2:g} kg CO2e" if isinstance(co2, (int, float)) else None]
    # The catalogue threshold is "Reported": a recorded assessment meets it.
    return "passed", ", ".join(p for p in parts if p) or "Assessment recorded"


RULES: Dict[str, Tuple[str, Callable[[dict], Verdict]]] = {
    "EV-FAI-01": ("fairness_test", _impact_ratio),
    "EV-FAI-02": ("fairness_test", _error_rates),
    "EV-FAI-06": ("fairness_test", _india),
    "EV-FAI-07": ("monitoring", _fairness_drift),
    "EV-ENV-01": ("environmental_impact", _energy),
}


def _rollup(systems: List[dict]) -> str:
    """failed if any system's latest result failed; passed if at least one passed and none failed."""
    statuses = {s["status"] for s in systems}
    if not statuses:
        return "not_run"
    if "failed" in statuses:
        return "failed"
    return "passed" if "passed" in statuses else "insufficient"


# the gate check each rule's evidence type feeds; a rule's result goes stale only when a change reopens that check
RULE_CHECK = {"fairness_test": "fairness", "monitoring": "monitoring", "environmental_impact": "environmental"}
ANY_CHANGE = "*"


def _changed_at(db: Session, org_id: str) -> Dict[str, Dict[str, datetime]]:
    """Per system, its newest material change (ANY_CHANGE) and the newest change that reopened each check."""
    rows = db.execute(
        text(
            "SELECT c.system_id, c.reopens_json, c.created_at FROM governance_system_changes c JOIN governance_ai_systems s ON s.id = c.system_id "
            "WHERE s.org_id = :org_id AND c.material"
        ),
        {"org_id": org_id},
    ).fetchall()
    out: Dict[str, Dict[str, datetime]] = {}
    for sid, reopens_json, raw in rows:
        at = _record_time({"createdAt": raw})
        if at is None:
            continue
        newest = out.setdefault(sid, {})
        for key in [ANY_CHANGE, *json.loads(reopens_json or "[]")]:
            if key not in newest or at > newest[key]:
                newest[key] = at
    return out


def _stale(row, changed: Dict[str, Dict[str, datetime]], check: str = ANY_CHANGE) -> bool:
    """An engine run goes stale at any material change; a rule result only at a change that reopens its check."""
    at = changed.get(row["system_id"], {}).get(check)
    if at is None:
        return False
    filed = _record_time({"createdAt": row["created_at"]})
    return filed is None or filed < at


def results(db: Session, org_id: str) -> Dict[str, Dict[str, Any]]:
    """Latest result per AI system for every evaluation that has a rule, and the organisation-wide status.

    A result filed before the change that reopened its check (any material change, for an engine run) no longer
    counts: that system reads as not run.
    """
    rows = (
        db.execute(
            text(
                "SELECT e.id, e.system_id, e.evidence_type, e.content_json, e.created_at, s.name AS system_name "
                "FROM governance_evidence e JOIN governance_ai_systems s ON s.id = e.system_id "
                "WHERE s.org_id = :org_id AND e.evidence_type IN ('fairness_test', 'monitoring', 'environmental_impact') "
                "ORDER BY e.created_at DESC"
            ),
            {"org_id": org_id},
        )
        .mappings()
        .all()
    )
    changed = _changed_at(db, org_id)
    out: Dict[str, Dict[str, Any]] = {}
    for ev_id, (evidence_type, rule) in RULES.items():
        latest: Dict[str, dict] = {}
        for row in rows:
            if row["evidence_type"] != evidence_type or row["system_id"] in latest or _stale(row, changed, RULE_CHECK[evidence_type]):
                continue
            try:
                verdict = rule(json.loads(row["content_json"] or "{}"))
            except (KeyError, TypeError, ValueError):
                verdict = None  # a run stored in an older shape is skipped, not guessed at
            if verdict:
                latest[row["system_id"]] = {
                    "systemId": row["system_id"],
                    "systemName": row["system_name"],
                    "status": verdict[0],
                    "detail": verdict[1],
                    "evidenceId": row["id"],
                    "at": row["created_at"],
                }
        systems = sorted(latest.values(), key=lambda s: s["at"], reverse=True)
        out[ev_id] = {"status": _rollup(systems), "systems": systems, "latestAt": systems[0]["at"] if systems else None}
    return {**_engine_runs(db, org_id, changed), **out}


def _engine_runs(db: Session, org_id: str, changed: Dict[str, Dict[str, datetime]]) -> Dict[str, Dict[str, Any]]:
    """Latest engine run per AI system for every evaluation FairMind runs itself (evaluation_runs router): the newest
    passed or failed one, or the newest insufficient one when nothing else is on file."""
    from src.application.services.eval_engines import REGISTRY

    rows = db.execute(
        text(
            "SELECT e.id, e.system_id, e.content_json, e.created_at, s.name AS system_name "
            "FROM governance_evidence e JOIN governance_ai_systems s ON s.id = e.system_id "
            "WHERE s.org_id = :org_id AND e.evidence_type = 'evaluation_run' ORDER BY e.created_at DESC"
        ),
        {"org_id": org_id},
    ).mappings().all()
    latest: Dict[str, Dict[str, dict]] = {ev: {} for ev in REGISTRY}
    for row in rows:
        if _stale(row, changed):
            continue
        content = json.loads(row["content_json"] or "{}")
        ev_id = content.get("evaluationId")
        if ev_id not in latest:
            continue
        held = latest[ev_id].get(row["system_id"])
        # newest first; an insufficient run measured nothing, so an older passed or failed run still stands, as in the gate
        if held and (held["status"] != "insufficient" or content.get("status") == "insufficient"):
            continue
        latest[ev_id][row["system_id"]] = {
            "systemId": row["system_id"],
            "systemName": row["system_name"],
            "status": content.get("status"),
            "detail": content.get("summary"),
            "evidenceId": row["id"],
            "at": row["created_at"],
        }
    out = {}
    for ev_id, by_system in latest.items():
        systems = sorted(by_system.values(), key=lambda s: s["at"], reverse=True)
        out[ev_id] = {"status": _rollup(systems), "systems": systems, "latestAt": systems[0]["at"] if systems else None}
    return out


def system_result(res: Dict[str, Dict[str, Any]], evaluation_id: str, system_id: str) -> Optional[Dict[str, Any]]:
    """One system's own latest result for one evaluation, or None when it has none: never another system's."""
    return next((x for x in (res.get(evaluation_id) or {}).get("systems", []) if x["systemId"] == system_id), None)


def passed(res: Dict[str, Dict[str, Any]]) -> List[str]:
    return [ev for ev, r in res.items() if r["status"] == "passed"]
