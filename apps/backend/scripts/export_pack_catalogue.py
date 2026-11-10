"""Export the agentic packs catalogue workbook to the JSON files the backend ships.

Usage: uv run --with openpyxl python scripts/export_pack_catalogue.py <workbook.xlsx> <out.json>

The workbook (docs/product/FairMind_agentic_packs_catalogue_v2.3.xlsx) is the source of truth;
the JSON is static reference data, never written to the database. Writes:

* <out.json>: the structured catalogue the backend parses at import, with
  additions.json (entries not yet in the workbook) merged in;
* workbook.json beside it: every sheet verbatim (rows as lists, header first),
  so nothing in the workbook is lost even where no code reads it yet.
"""

import datetime
import json
import re
import sys
from pathlib import Path

from openpyxl import load_workbook

STEP_KIND = {
    "Start": "trigger",
    "Collect": "collect",
    "Check": "check",
    "Suggest": "suggest",
    "Pre-flight": "preflight",
    "Ask a person (approval gate)": "ask",
    "Ask a person (exception gate)": "exception",
    "Human decides": "decide",
    "Act": "act",
    "Verify": "verify",
    "Escalate": "escalate",
    "File evidence": "file",
}


def rows(wb, name, header_row=1):
    it = wb[name].iter_rows(min_row=header_row, values_only=True)
    hdr = next(it)
    return [dict(zip(hdr, r)) for r in it if r and r[0] is not None]


def split_list(v):
    return [x.strip() for x in re.split(r"[;,]", str(v or "")) if x.strip()]


def parse_next(v):
    """'act (approved / approved with edits); revise (changes asked)' -> [{to, label}]."""
    out = []
    for part in [p.strip() for p in str(v or "").split(";") if p.strip()]:
        m = re.match(r"^([\w-]+)\s*(?:\((.*)\))?$", part)
        if m:
            out.append({"to": m.group(1), "label": m.group(2)})
    return out


def text(v):
    return None if v is None else str(v).strip() or None


def merge_additions(data, path):
    """Insert additions.json's framework and requirements after its 'after' framework; append its crosswalk."""
    if not path.exists():
        return
    add = json.loads(path.read_text(encoding="utf-8"))
    keys = {f["key"] for f in data["frameworks"]}
    for f in add["frameworks"]:
        if f["key"] in keys:
            raise SystemExit(f"{path.name}: {f['key']} is now in the workbook; remove it from {path.name}")
    i = next(n for n, f in enumerate(data["frameworks"]) if f["key"] == add["after"]) + 1
    data["frameworks"][i:i] = add["frameworks"]
    j = max(n for n, r in enumerate(data["requirements"]) if r["framework"] == add["after"]) + 1
    data["requirements"][j:j] = add["requirements"]
    data["crosswalk"] += add["crosswalk"]


def cell(v):
    return v.isoformat() if isinstance(v, (datetime.date, datetime.datetime, datetime.time)) else v


def export_sheets(wb, out):
    sheets = {
        ws.title: [[cell(c) for c in r] for r in ws.iter_rows(values_only=True) if any(c not in (None, "") for c in r)]
        for ws in wb.worksheets
    }
    with open(out, "w") as f:
        json.dump({"source": "docs/product/FairMind_agentic_packs_catalogue_v2.3.xlsx", "sheets": sheets}, f, ensure_ascii=False)
        f.write("\n")
    print({"workbook sheets": len(sheets), "rows": sum(len(r) for r in sheets.values())})


def engine_status(evaluations):
    """Set engine and codeLocation from the code: 'Engine exists' only where FairMind can run the evaluation.

    Runnable means an engine in eval_engines.REGISTRY or a result rule in evaluation_results.RULES.
    For the rest, the workbook's code search survives only as a hint: 'Partial' where it found related code.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.api.routers.evaluation_results import RULES
    from src.application.services import eval_engines
    from src.application.services.eval_engines import VALIDATED

    where = {}
    for m in (eval_engines.data, eval_engines.model, eval_engines.ops, eval_engines.platform, eval_engines.behaviour, eval_engines.suites, eval_engines.assess):
        for e in m.ENGINES:
            where.setdefault(e.id, f"src/application/services/eval_engines/{m.__name__.rsplit('.', 1)[1]}.py")
    for i in RULES:
        where.setdefault(i, "src/api/routers/evaluation_results.py")
    for e in evaluations:
        if e["id"] in where:
            e["engine"], e["codeLocation"] = "Engine exists", where[e["id"]]
            e["maturity"] = "L4" if e["id"] in VALIDATED else "L1"  # L2 and above are not derivable from the code alone
        else:
            e["engine"] = "Partial" if e["engine"] in ("Engine exists", "Partial") else "Not found"


def main(src, out):
    wb = load_workbook(src, data_only=True)
    pillars = [{"id": r["Pillar"], "name": r["Name"], "description": r["What it covers"]} for r in rows(wb, "Pillars")]
    frameworks = [
        {"key": r["Key"], "name": r["Framework"], "publisher": text(r["Publisher"]), "version": text(r["Version in catalogue"]), "type": text(r["Type"]),
         "jurisdiction": text(r["Jurisdiction"]), "binding": text(r["Binding"]), "status": text(r["Status (Nov 2026)"]), "granularity": text(r["Granularity used"]),
         "licence": text(r["Licence constraint"]), "priority": text(r["Priority"]), "pillar": r["Pillar (v2.2)"]}
        for r in rows(wb, "Frameworks")
    ]
    requirements = [
        {"key": r["Key"], "framework": r["Framework key"], "control": str(r["Control"]), "title": r["Title (paraphrase)"], "group": text(r["Group"]),
         "active": r["Status"] == "Active", "status": r["Status"]}
        for r in rows(wb, "Control_Library")
    ]
    common = [{"id": r["Common control"], "name": r["Name"], "objective": r["Objective"], "evaluationsNeeded": text(r["Evaluations needed (assessment layer)"])}
              for r in rows(wb, "Common_Controls")]
    crosswalk = [{"commonControl": r["Common control"], "key": r["Key"], "relation": r["Relation"]} for r in rows(wb, "Crosswalk")]

    steps_by_wf = {}
    for s in rows(wb, "Steps"):
        steps_by_wf.setdefault(s["Workflow ID"], []).append({
            "id": s["Step ID"], "kind": STEP_KIND[s["Step type"]], "type": s["Step type"], "title": s["Title"], "detail": text(s["What happens"]),
            "systems": split_list(s["Systems"]), "permission": text(s["Agent permission"]), "runsWithoutApproval": text(s["Runs without approval"]),
            "next": parse_next(s["Goes to"]), "failure": text(s["Failure / timeout handling"]), "output": text(s["Output"]),
        })
    maps_by_wf = {}
    for c in rows(wb, "Controls"):
        maps_by_wf.setdefault(c["Workflow ID"], []).append({"key": c["Key"], "relation": c["Relation"], "note": text(c["Review note (v2.1)"])})
    workflows = []
    for w in rows(wb, "Workflows"):
        wid = w["Workflow ID"]
        workflows.append({
            "id": wid, "name": w["Workflow"], "pattern": str(w["Pattern (v2.3)"]).split(" ")[0], "pillar": w["Pillar (v2.3)"],
            "commonControl": str(w["Common control (v2.1)"]).split(" ")[0], "status": text(w["Status"]), "stage": text(w["Lifecycle stage"]),
            "scope": text(w["Run scope"]), "description": text(w["Description"]), "schedule": text(w["Schedule"]), "triggers": split_list(w["Event triggers"]),
            "autonomy": text(w["Default autonomy"]), "gate": text(w["Approval gate"]), "gateConditions": text(w["Gate conditions (v2.1)"]),
            "approver": text(w["Approver"]), "separationOfDuties": text(w["Separation of duties"]), "externalWrite": str(w["External write"]).strip().lower() == "yes",
            "systems": split_list(w["Systems touched"]), "evidence": text(w["Evidence produced"]), "agentRisks": split_list(w["FairMind agent risks (OWASP ASI)"]),
            "steps": steps_by_wf.get(wid, []), "mappings": maps_by_wf.get(wid, []),
        })
    ev_tests = {}
    for m in rows(wb, "Eval_Mappings"):
        ev_tests.setdefault(m["Evaluation ID"], []).append(m["Key"])
    evaluations = [
        {"id": e["Evaluation ID"], "name": e["Evaluation"], "measures": e["What it measures"], "metric": e["Metric"], "threshold": e["Default pass threshold"],
         "thresholdSource": text(e["Threshold source"]), "appliesTo": text(e["Applies to"]), "inputs": text(e["Inputs needed"]), "commonControl": e["Common control"],
         "pattern": str(e["Pattern (v2.3)"]).split(" ")[0], "pillar": e["Pillar (v2.3)"], "engine": e["FairMind engine (code search of main, 2 Nov 2026)"],
         "codeLocation": text(e["Code location on main"]), "tests": ev_tests.get(e["Evaluation ID"], [])}
        for e in rows(wb, "Evaluations") if str(e["Evaluation ID"]).startswith("EV-")
    ]
    engine_status(evaluations)
    patterns = [{"id": p["Pattern"], "pillar": p["Pillar"], "name": p["Pattern name"], "objective": p["Objective"], "agentic": p["Agentic"] == "Yes",
                 "pack": p["In pack"], "workflows": split_list(p["Workflows"]), "evaluations": split_list(p["Evaluations"])} for p in rows(wb, "Patterns")]
    packs = [{"id": k["Pack"], "name": k["Pack name"], "pillar": k["Pillar"], "description": k["What it is for"], "patterns": split_list(k["Patterns"])}
             for k in rows(wb, "Pack_Library")]
    bundles = {}
    for b in rows(wb, "Bundles"):
        x = bundles.setdefault(b["Bundle"], {"id": b["Bundle"], "name": b["Bundle name"], "for": b["For"], "packs": split_list(b["Packs"]), "targets": []})
        x["targets"].append(b["Target framework"])
    data = {"version": "2.3", "source": "docs/product/FairMind_agentic_packs_catalogue_v2.3.xlsx", "pillars": pillars, "frameworks": frameworks,
            "requirements": requirements, "commonControls": common, "crosswalk": crosswalk, "workflows": workflows, "evaluations": evaluations,
            "patterns": patterns, "packs": packs, "bundles": list(bundles.values())}
    merge_additions(data, Path(out).parent / "additions.json")
    with open(out, "w") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print({k: len(v) for k, v in data.items() if isinstance(v, list)})
    export_sheets(wb, Path(out).parent / "workbook.json")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
