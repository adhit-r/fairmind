"""Read the release gate per framework clause.

Each gate check corresponds to one of the catalogue's common controls; the catalogue's
crosswalk says which clause of which framework that control satisfies, supports or
aligns with. Catalogue evaluation runs reach clauses the same way, through their
evaluation's common control. The clause map joins them: for every framework, every
active clause, each carrying the state of the checks behind it. A clause is proven only
through a "Satisfies" link; proof through a weaker link makes it partial.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

CATALOGUE_PATH = Path(__file__).resolve().parents[2] / "api" / "routers" / "pack_catalogue_data" / "catalogue.json"

# gate check key -> catalogue common control
CHECK_CONTROLS: Dict[str, str] = {
    "fairness": "FMC-FAI-01",
    "data_governance": "FMC-DAT-01",
    "human_oversight": "FMC-OVS-01",
    "monitoring": "FMC-MON-01",
    "environmental": "FMC-ENV-01",
}
# catalogue common control -> gate check key
GATE_CONTROLS: Dict[str, str] = {control: check for check, control in CHECK_CONTROLS.items()}

# legacy framework ids used by the report request -> catalogue framework keys
# (the audit-reports picker sends its display names, so those resolve too)
FRAMEWORK_ALIASES: Dict[str, str] = {
    "eu_ai_act": "EUAIA", "iso_42001": "ISO42001", "nist_ai_rmf": "NISTRMF", "india_ai": "INDAI", "rbi_free_ai": "RBIFREEAI",
    "EU AI Act": "EUAIA", "ISO 42001": "ISO42001", "NIST AI RMF": "NISTRMF", "RBI FREE-AI": "RBIFREEAI",
}

# the frameworks a decision record is usually read against, in display order; the rest follow alphabetically
LEAD_FRAMEWORKS = ("EUAIA", "ISO42001", "NISTRMF", "INDAI", "RBIFREEAI")

RELATION_RANK = {"Satisfies": 0, "Partially satisfies": 1, "Supports": 2, "Aligns with": 3}


def _natural(control: str) -> List[Any]:
    """'Art 10' < 'Art 12' < 'Art 53'; 'A.6.2.4' < 'A.7.2'; 'MAP 3.5' < 'MEASURE 2.11'."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", control)]


@lru_cache(maxsize=1)
def _catalogue() -> Dict[str, Any]:
    data = json.loads(CATALOGUE_PATH.read_text())
    requirements = {r["key"]: r for r in data["requirements"]}
    frameworks = {f["key"]: f for f in data["frameworks"]}
    by_control: Dict[str, List[Dict[str, Any]]] = {}
    by_framework: Dict[str, List[Dict[str, Any]]] = {}
    for req in data["requirements"]:
        if req.get("active", True):
            by_framework.setdefault(req["framework"], []).append(req)
    for entry in data["crosswalk"]:
        req = requirements.get(entry["key"])
        if req and req.get("active", True):
            by_control.setdefault(entry["commonControl"], []).append({**entry, "requirement": req})
    # raw lists for GET /packs/controls
    return {"frameworks": frameworks, "by_control": by_control, "by_framework": by_framework,
            "evaluations": {e["id"]: e for e in data["evaluations"]}, "commonControls": data["commonControls"], "crosswalk": data["crosswalk"]}


def evaluation_control(content: Any) -> Optional[str]:
    """The common control of the catalogue evaluation an evaluation_run record's content names."""
    ev = _catalogue()["evaluations"].get(str((content or {}).get("evaluationId") or "")) if isinstance(content, dict) else None
    return ev.get("commonControl") if ev else None


# a clause cell is as good as its best-evidenced check, unless one of them fails; "none": no check reaches it
CELL_RANK = ("proven", "estimated", "partial", "attested", "stale", "open", "none")


def cell_state(check: Dict[str, Any]) -> str:
    """The grid cell for one gate check: fails, stale, open, attested, estimated or proven.

    ``fails`` is set by release_gate when a measured or tool-estimated record reports all_checks_pass False.
    """
    cls = check.get("evidenceClass")
    if check.get("fails"):
        return "fails"
    if check.get("stale"):
        return "stale"
    if check["state"] == "open":
        return "open"
    if cls == "manual":
        return "attested"
    if cls == "tool_estimated":
        return "estimated"
    if check["state"] == "proven" and cls == "measured":
        return "proven"
    return "estimated"


def tracked_requirements(framework_key: str) -> List[str]:
    """Keys of every active requirement of one framework, in clause order: the clause map reads them all."""
    reqs = _catalogue()["by_framework"].get(framework_key, [])
    return [r["key"] for r in sorted(reqs, key=lambda r: _natural(r["control"]))]


def framework_keys(requested: Optional[List[str]]) -> Optional[List[str]]:
    """Normalise report-request framework ids to catalogue keys; None means every framework."""
    if not requested:
        return None
    return [FRAMEWORK_ALIASES.get(f, f) for f in requested]


def clause_state(checks: List[Dict[str, Any]]) -> str:
    """proven only through a proven check that satisfies the clause; a proven check on a weaker link makes it partial.

    A failing check proves and attests nothing, so a clause reached only by failing checks stays open, and a
    clause with any failing check is never proven.
    """
    failing = any(c.get("fails") for c in checks)
    checks = [c for c in checks if not c.get("fails")]
    proven = [c for c in checks if c["state"] == "proven"]
    if any(c["relation"] == "Satisfies" for c in proven):
        return "partial" if failing else "proven"
    return "partial" if proven else "attested" if any(c["state"] == "attested" for c in checks) else "open"


def clause_map(gate: Dict[str, Any], *, frameworks: Optional[List[str]] = None) -> Dict[str, Any]:
    """Every active clause of each requested framework (every framework something reaches when none are requested).

    A gate check left out of the organisation's gate reaches its clauses as "not in gate", which proves nothing;
    ``gate["evaluations"]`` (newest passed or failed run per non-gate control) reaches clauses through its control.
    """
    from src.application.services.fairness_run_service import GATE_CHECKS  # function-level: that module imports this one

    cat = _catalogue()
    checks = {c["key"]: c for c in gate.get("checks", [])}
    labels = {key: label for key, label, _ in GATE_CHECKS}
    entries: List[tuple] = []  # (control, check entry without relation)
    for check_key, control in CHECK_CONTROLS.items():
        check = checks.get(check_key)
        if not check:
            entries.append((control, {"check": check_key, "label": labels.get(check_key), "state": "open", "confidence": 0.0, "evidenceId": None, "evidenceClass": None, "cell": "not in gate"}))
            continue
        entries.append((control, {
            "check": check_key, "label": check.get("label"), "state": check["state"], "confidence": check.get("confidence", 0.0),
            "evidenceId": check.get("evidenceId"), "evidenceClass": check.get("evidenceClass"), "cell": cell_state(check),
            **{flag: True for flag in ("stale", "fails") if check.get(flag)},
        }))
    for run in gate.get("evaluations", []):
        name = cat["evaluations"].get(run["evaluationId"], {}).get("name", "")
        entry = {
            "check": run["evaluationId"], "label": f"{run['evaluationId']} {name}".strip(), "state": run["state"],
            "confidence": run["confidence"], "evidenceId": run.get("evidenceId"), "evidenceClass": run["evidenceClass"],
            **({"fails": True} if run["status"] == "failed" else {}),
        }
        entries.append((run["control"], {**entry, "cell": cell_state(entry)}))

    per_framework: Dict[str, Dict[str, Any]] = {}

    def framework(fw_key: str) -> Dict[str, Any]:
        return per_framework.setdefault(fw_key, {"key": fw_key, "name": cat["frameworks"].get(fw_key, {}).get("name", fw_key), "clauses": {}})

    def clause(fw: Dict[str, Any], req: Dict[str, Any]) -> Dict[str, Any]:
        return fw["clauses"].setdefault(req["key"], {"key": req["key"], "control": req["control"], "title": req["title"], "group": req.get("group"), "checks": []})

    for control, entry in entries:
        for link in cat["by_control"].get(control, []):
            req = link["requirement"]
            if frameworks and req["framework"] not in frameworks:
                continue
            clause(framework(req["framework"]), req)["checks"].append({**entry, "relation": link["relation"]})
    # seed every active clause, so a clause nothing reaches still counts as open
    for fw_key in frameworks or list(per_framework):
        for req in cat["by_framework"].get(fw_key, []):
            clause(framework(fw_key), req)

    out: List[Dict[str, Any]] = []
    for fw_key, fw in per_framework.items():
        clauses = []
        for clause_row in fw["clauses"].values():
            clause_row["checks"].sort(key=lambda c: RELATION_RANK.get(c["relation"], 9))
            clause_row["state"] = clause_state(clause_row["checks"])
            cells = {c["cell"] for c in clause_row["checks"]} - {"not in gate"}
            clause_row["cell"] = "fails" if "fails" in cells else min(cells, key=CELL_RANK.index) if cells else "none"
            if clause_row["state"] == "partial" and clause_row["cell"] in ("proven", "estimated"):
                clause_row["cell"] = "partial"  # proof through a weaker link: the grid reads what the clause state says
            clauses.append(clause_row)
        clauses.sort(key=lambda c: _natural(c["control"]))
        counts = {s: sum(1 for c in clauses if c["state"] == s) for s in ("proven", "partial", "attested", "open")}
        out.append({**fw, "clauses": clauses, "counts": {**counts, "total": len(clauses)}})
    order = {k: i for i, k in enumerate(LEAD_FRAMEWORKS)}
    out.sort(key=lambda f: (order.get(f["key"], len(order)), f["name"]))
    return {"verdict": gate.get("verdict"), "confidence": gate.get("confidence"), "frameworks": out}
