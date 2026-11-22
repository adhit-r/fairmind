"""The rules of the internal audit (ISO/IEC 42001 clause 9.2), kept free of the database so they can be tested alone.

Grading, the independence rule, reading the auditors' own plan file, and the hash chain of the audit's events.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

GRADES = ("conformity", "observation", "minor_nc", "major_nc")
GENESIS = "0" * 64
PLAN_COLUMNS = ("area", "clauses", "systems", "auditor", "process_owner")
MAX_PLAN_BYTES = 1_000_000


def suggest_grade(cell_state: str, owner_answered_with_evidence: bool = False) -> Tuple[str, str]:
    """The grade the evidence suggests and the rule behind it. Only a person grades; this is the starting point."""
    if cell_state == "proven":
        return "conformity", "Rule: a proven clause is Conformity."
    if cell_state in ("attested", "estimated"):
        return "observation", f"Rule: a {cell_state} clause rests on a statement or an estimate, so it is an Observation."
    if cell_state == "excluded":
        return "observation", "Rule: a clause excluded as not applicable is an Observation until the auditor confirms the exclusion."
    if cell_state in ("partial", "stale"):
        return "minor_nc", f"Rule: a {cell_state} clause is a Minor NC."
    if owner_answered_with_evidence:
        return "minor_nc", "Rule: an open clause is a Major NC, but the owner answered with evidence, so it is a Minor NC."
    return "major_nc", "Rule: an open clause with no evidence from the owner is a Major NC."


def _ids(*values: Optional[str]) -> set:
    return {v.strip().lower() for v in values if v and v.strip()}


def conflicts(
    auditor: Dict[str, Optional[str]], process_owner: Optional[str], systems: Iterable[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """Why this auditor (their {id, email}) may not audit an area: the process owner or an owner of one of its systems."""
    me = _ids(auditor.get("id"), auditor.get("email"))
    out: List[Dict[str, str]] = []
    if me & _ids(process_owner):
        out.append({"kind": "process_owner", "detail": "The auditor is the area's process owner"})
    for s in systems:
        if me & _ids(s.get("owner")):
            out.append({"kind": "system_owner", "detail": f"The auditor owns {s.get('name') or s.get('id')}", "systemId": s.get("id")})
    return out


# --- the plan file -----------------------------------------------------------


def _split(value: Any) -> List[str]:
    return [p.strip() for p in re.split(r"[;,\n]", str(value or "")) if p.strip()]


def parse_plan(filename: str, data: bytes) -> List[Dict[str, Any]]:
    """The plan's lines as {line, area, clauses, systems, auditor, process_owner}; raw text, nothing matched yet.

    A .csv or .xlsx file with a header row naming area, clauses, systems, auditor and process_owner (any order, any case)."""
    if len(data) > MAX_PLAN_BYTES:
        raise ValueError("The plan file is larger than 1 MB")
    name = (filename or "").lower()
    if name.endswith(".csv"):
        rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig", "replace"))))
    elif name.endswith(".xlsx"):
        from openpyxl import load_workbook

        sheet = load_workbook(io.BytesIO(data), read_only=True, data_only=True).worksheets[0]
        rows = [["" if c is None else str(c) for c in r] for r in sheet.iter_rows(values_only=True)]
    else:
        raise ValueError("Upload the plan as a .csv or .xlsx file")
    if not rows:
        raise ValueError("The plan file is empty")
    header = [h.strip().lower().replace(" ", "_") for h in rows[0]]
    missing = [c for c in ("area", "clauses", "systems") if c not in header]
    if missing:
        raise ValueError(f"The plan needs a column named {', '.join(missing)}; expected {', '.join(PLAN_COLUMNS)}")
    lines = []
    for n, row in enumerate(rows[1:], start=2):
        cells = {h: (row[i].strip() if i < len(row) else "") for i, h in enumerate(header)}
        if not any(cells.values()):
            continue
        lines.append({
            "line": n, "area": cells.get("area", ""), "clauses": _split(cells.get("clauses")), "systems": _split(cells.get("systems")),
            "auditor": cells.get("auditor", "").lower(), "process_owner": cells.get("process_owner", ""),
        })
    return lines


def match_plan(
    lines: List[Dict[str, Any]], controls: Dict[str, Dict[str, str]], systems: List[Dict[str, Any]], users_by_email: Dict[str, str]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """(areas, unmatched). controls maps a clause number to its requirement ({key, title}); systems are the organisation's
    ({id, name, ...}); users_by_email maps a lower-cased email to a user id. An area is {name, clauses, systems, auditor_id,
    process_owner, checks: [(clause, system id)]}. A value that matches nothing is listed in unmatched, never dropped."""
    by_ref = {}
    for s in systems:
        by_ref[s["id"].lower()] = s
        by_ref.setdefault(s["name"].strip().lower(), s)
    areas: List[Dict[str, Any]] = []
    unmatched: List[Dict[str, Any]] = []
    seen: set = set()

    def miss(line: int, column: str, value: str, reason: str) -> None:
        unmatched.append({"line": line, "column": column, "value": value, "reason": reason})

    for ln in lines:
        n = ln["line"]
        if not ln["area"]:
            miss(n, "area", "", "The line has no area name")
            continue
        clauses = []
        for raw in ln["clauses"]:
            key = re.sub(r"^(clause\s+|iso42001\|)", "", raw.strip(), flags=re.I)
            if key in controls:
                clauses.append(key)
            else:
                miss(n, "clauses", raw, "Not a clause of the framework's catalogue")
        picked = []
        for raw in ln["systems"]:
            s = by_ref.get(raw.strip().lower())
            if s:
                picked.append(s)
            else:
                miss(n, "systems", raw, "Not an AI system of this organisation")
        auditor_id = None
        if ln["auditor"]:
            auditor_id = users_by_email.get(ln["auditor"])
            if not auditor_id:
                miss(n, "auditor", ln["auditor"], "Not a member of this organisation")
        checks = []
        for c in dict.fromkeys(clauses):
            for s in {s["id"]: s for s in picked}.values():
                if (c, s["id"]) in seen:
                    miss(n, "clauses", f"{c} / {s['name']}", "Already in an earlier area of this plan")
                else:
                    seen.add((c, s["id"]))
                    checks.append((c, s["id"]))
        if not checks:
            miss(n, "area", ln["area"], "No clause and system on this line matched, so no check was planned")
            continue
        areas.append({
            "name": ln["area"], "clauses": list(dict.fromkeys(c for c, _ in checks)), "systems": list(dict.fromkeys(s for _, s in checks)),
            "auditor_id": auditor_id, "process_owner": ln["process_owner"] or None, "checks": checks,
        })
    return areas, unmatched


# --- the hash chain ----------------------------------------------------------


def canonical(audit_id: str, seq: int, kind: str, actor: Optional[str], payload: dict, created_at: str, prev_hash: str) -> str:
    return json.dumps(
        {"audit_id": audit_id, "seq": seq, "kind": kind, "actor": actor, "payload": payload, "created_at": created_at, "prev_hash": prev_hash},
        sort_keys=True, separators=(",", ":"),
    )


def event_hash(*args: Any) -> str:
    return hashlib.sha256(canonical(*args).encode()).hexdigest()


def verify_chain(events: List[Dict[str, Any]]) -> bool:
    """events are rows in seq order with payload already parsed."""
    prev = GENESIS
    for i, e in enumerate(events, start=1):
        if e["seq"] != i or e["prev_hash"] != prev or event_hash(e["audit_id"], e["seq"], e["kind"], e["actor"], e["payload"], e["created_at"], e["prev_hash"]) != e["hash"]:
            return False
        prev = e["hash"]
    return True
