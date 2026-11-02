"""Export the agentic packs catalogue workbook to the JSON file the backend loads.

Usage: uv run --with openpyxl python scripts/export_pack_catalogue.py <workbook.xlsx> <out.json>

The workbook (docs/product/FairMind_agentic_packs_catalogue_v2.3.xlsx) is the source of truth;
the JSON is static reference data, never written to the database.
"""

import json
import re
import sys

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
    with open(out, "w") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print({k: len(v) for k, v in data.items() if isinstance(v, list)})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
