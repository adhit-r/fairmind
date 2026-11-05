"""Results for catalogue evaluations, read from evidence FairMind already stores.

Five catalogue evaluations have a FairMind engine whose runs are saved per AI
system in governance_evidence: fairness runs, monitoring runs and environmental
assessments. Each is matched to one evidence type and a rule that reads the
stored checks. Nothing here runs an engine or writes data; an evaluation with
no rule has no results yet.
"""

import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

# Attribute names the fairness engine treats as India-specific (see fairness_run_service.ATTRIBUTE_HINTS).
INDIA_ATTRIBUTES = ("caste", "religion", "region", "state", "district", "language")

# (status, one line on what was measured); None when the run does not speak to the evaluation.
Verdict = Optional[Tuple[str, str]]


def _ok(passed: bool) -> str:
    return "passed" if passed else "failed"


def _impact_ratio(c: dict) -> Verdict:
    attrs = c.get("attributes") or []
    if not attrs:
        return None
    detail = ", ".join(f"{a['attribute']} {a['disparate_impact_ratio']:.2f}" for a in attrs)
    return _ok(all(a["checks"].get("disparate_impact") for a in attrs)), f"Impact ratio {detail}"


def _error_rates(c: dict) -> Verdict:
    attrs = c.get("attributes") or []
    if not attrs:
        return None
    worst = max(attrs, key=lambda a: max(a["equal_opportunity"]["value"], a["equalized_odds"]["value"]))
    gap = max(worst["equal_opportunity"]["value"], worst["equalized_odds"]["value"])
    passed = all(a["checks"].get("equal_opportunity") and a["checks"].get("equalized_odds") for a in attrs)
    return _ok(passed), f"Largest error-rate gap {gap:.3f} ({worst['attribute']})"


def _india(c: dict) -> Verdict:
    attrs = [a for a in c.get("attributes") or [] if any(h in a["attribute"].lower() for h in INDIA_ATTRIBUTES)]
    if not attrs:
        return None
    passed = all(all(a["checks"].get(k) for k in ("disparate_impact", "equal_opportunity", "equalized_odds")) for a in attrs)
    return _ok(passed), f"Checked {', '.join(a['attribute'] for a in attrs)}"


def _fairness_drift(c: dict) -> Verdict:
    attrs = c.get("attributes") or []
    compared = [a for a in attrs if "selection_rate_stable" in a["checks"]]
    if not attrs:
        return None
    if not compared:
        return "insufficient", "No baseline run to compare against"
    drift = max(a["max_rate_drift"] for a in compared)
    passed = all(a["checks"]["selection_rate_stable"] and a["checks"].get("disparate_impact") for a in compared)
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


def results(db: Session, org_id: str) -> Dict[str, Dict[str, Any]]:
    """Latest result per AI system for every evaluation that has a rule, and the organisation-wide status."""
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
    out: Dict[str, Dict[str, Any]] = {}
    for ev_id, (evidence_type, rule) in RULES.items():
        latest: Dict[str, dict] = {}
        for row in rows:
            if row["evidence_type"] != evidence_type or row["system_id"] in latest:
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
    return {**_engine_runs(db, org_id), **out}


def _engine_runs(db: Session, org_id: str) -> Dict[str, Dict[str, Any]]:
    """Latest engine run per AI system for every evaluation FairMind runs itself (evaluation_runs router)."""
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
        content = json.loads(row["content_json"] or "{}")
        ev_id = content.get("evaluationId")
        if ev_id not in latest or row["system_id"] in latest[ev_id]:
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


def passed(res: Dict[str, Dict[str, Any]]) -> List[str]:
    return [ev for ev, r in res.items() if r["status"] == "passed"]
