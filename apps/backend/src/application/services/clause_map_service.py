"""Read the release gate per framework clause.

Each gate check corresponds to one of the catalogue's common controls; the catalogue's
crosswalk says which clause of which framework that control satisfies, supports or
aligns with. The clause map joins the two: for every framework, the clauses the gate
speaks to, each carrying the state of the check behind it (proven, attested, open).
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
    for entry in data["crosswalk"]:
        req = requirements.get(entry["key"])
        if req and req.get("active", True):
            by_control.setdefault(entry["commonControl"], []).append({**entry, "requirement": req})
    # raw lists for GET /packs/controls
    return {"frameworks": frameworks, "by_control": by_control, "commonControls": data["commonControls"], "crosswalk": data["crosswalk"]}


# a clause cell is as good as its best-evidenced check, unless one of them fails
CELL_RANK = ("proven", "estimated", "attested", "stale", "open")


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
    """Keys of one framework's active requirements that the gate checks speak to, in clause order."""
    cat = _catalogue()
    reqs = {e["key"]: e["requirement"] for control in CHECK_CONTROLS.values() for e in cat["by_control"].get(control, []) if e["requirement"]["framework"] == framework_key}
    return sorted(reqs, key=lambda k: _natural(reqs[k]["control"]))


def framework_keys(requested: Optional[List[str]]) -> Optional[List[str]]:
    """Normalise report-request framework ids to catalogue keys; None means every framework."""
    if not requested:
        return None
    return [FRAMEWORK_ALIASES.get(f, f) for f in requested]


def clause_map(gate: Dict[str, Any], *, frameworks: Optional[List[str]] = None) -> Dict[str, Any]:
    cat = _catalogue()
    checks = {c["key"]: c for c in gate.get("checks", [])}
    per_framework: Dict[str, Dict[str, Any]] = {}
    for check_key, control in CHECK_CONTROLS.items():
        check = checks.get(check_key)
        if not check:
            continue
        for entry in cat["by_control"].get(control, []):
            req = entry["requirement"]
            fw_key = req["framework"]
            if frameworks and fw_key not in frameworks:
                continue
            fw = per_framework.setdefault(fw_key, {"key": fw_key, "name": cat["frameworks"].get(fw_key, {}).get("name", fw_key), "clauses": {}})
            clause = fw["clauses"].setdefault(req["key"], {"key": req["key"], "control": req["control"], "title": req["title"], "group": req.get("group"), "checks": []})
            clause["checks"].append({
                "check": check_key, "label": check.get("label"), "state": check["state"], "confidence": check.get("confidence", 0.0),
                "evidenceId": check.get("evidenceId"), "evidenceClass": check.get("evidenceClass"), "relation": entry["relation"], "cell": cell_state(check),
                **{flag: True for flag in ("stale", "fails") if check.get(flag)},
            })

    out: List[Dict[str, Any]] = []
    for fw_key, fw in per_framework.items():
        clauses = []
        for clause in fw["clauses"].values():
            clause["checks"].sort(key=lambda c: RELATION_RANK.get(c["relation"], 9))
            states = {c["state"] for c in clause["checks"]}
            # a clause is as good as its best-evidenced check: proven beats attested beats open
            clause["state"] = "proven" if "proven" in states else "attested" if "attested" in states else "open"
            cells = {c["cell"] for c in clause["checks"]}
            clause["cell"] = "fails" if "fails" in cells else min(cells, key=CELL_RANK.index)
            clauses.append(clause)
        clauses.sort(key=lambda c: _natural(c["control"]))
        counts = {s: sum(1 for c in clauses if c["state"] == s) for s in ("proven", "attested", "open")}
        out.append({**fw, "clauses": clauses, "counts": {**counts, "total": len(clauses)}})
    order = {k: i for i, k in enumerate(LEAD_FRAMEWORKS)}
    out.sort(key=lambda f: (order.get(f["key"], len(order)), f["name"]))
    return {"verdict": gate.get("verdict"), "confidence": gate.get("confidence"), "frameworks": out}
