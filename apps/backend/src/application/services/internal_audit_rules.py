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
MAX_ROWS = 5000
MAX_COLS = 20


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
    if cell_state == "fails":
        return "major_nc", "Rule: a clause with a failing check is a Major NC, whatever the owner says."
    if owner_answered_with_evidence:
        return "minor_nc", f"Rule: a clause that is {cell_state} is a Major NC, but its owner answered with evidence, so it is a Minor NC."
    return "major_nc", f"Rule: a clause that is {cell_state} with no evidence from its owner is a Major NC."


def _ids(*values: Optional[str]) -> set:
    return {v.strip().lower() for v in values if v and v.strip()}


def conflicts(
    auditor: Dict[str, Optional[str]], process_owner: Optional[str], systems: Iterable[Dict[str, Any]], known: Optional[set] = None
) -> List[Dict[str, str]]:
    """Why this auditor (their {id, email}) may not audit an area: the process owner or an owner of one of its systems.

    known, when given, is every lower-cased user id and email of the organisation: an owner value outside it cannot be
    compared with the auditor, so it is reported as kind "unverifiable" (a warning, not a conflict)."""
    me = _ids(auditor.get("id"), auditor.get("email"))
    out: List[Dict[str, str]] = []
    systems = list(systems)
    if me & _ids(process_owner):
        out.append({"kind": "process_owner", "detail": "The auditor is the area's process owner"})
    for s in systems:
        if me & _ids(s.get("owner")):
            out.append({"kind": "system_owner", "detail": f"The auditor owns {s.get('name') or s.get('id')}", "systemId": s.get("id")})
    if known is not None:
        for who, value in [("process owner", process_owner)] + [(f"owner of {s.get('name') or s.get('id')}", s.get("owner")) for s in systems]:
            if value and value.strip() and value.strip().lower() not in known:
                out.append({"kind": "unverifiable", "detail": f"The {who} '{value.strip()}' is not an organisation member's email or user id, so independence cannot be checked"})
    return out


# --- the plan file -----------------------------------------------------------


def _split(value: Any) -> List[str]:
    return [p.strip() for p in re.split(r"[;,\n]", str(value or "")) if p.strip()]


def parse_plan(filename: str, data: bytes) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """(lines, skipped). Lines are {line, area, clauses, systems, auditor, process_owner}, raw text, nothing matched yet.

    A .csv or .xlsx file with a header row naming area, clauses, systems, auditor and process_owner (any order, any case).
    At most MAX_ROWS rows and MAX_COLS columns are read; whatever is not read (more rows or columns, other sheets, cells
    under an unknown or missing header) is listed in skipped, in the shape of unmatched lines."""
    if len(data) > MAX_PLAN_BYTES:
        raise ValueError("The plan file is larger than 1 MB")
    name = (filename or "").lower()
    skipped: List[Dict[str, Any]] = []
    if name.endswith(".csv"):
        rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig", "replace"))))
    elif name.endswith(".xlsx"):
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        for extra in wb.sheetnames[1:]:
            skipped.append({"line": 0, "column": "sheet", "value": extra, "reason": "Only the first sheet is read"})
        sheet = wb.worksheets[0]
        rows = [["" if c is None else str(c) for c in r] for r in sheet.iter_rows(max_row=MAX_ROWS + 2, max_col=MAX_COLS + 1, values_only=True)]
    else:
        raise ValueError("Upload the plan as a .csv or .xlsx file")
    if not rows:
        raise ValueError("The plan file is empty")
    if len(rows) > MAX_ROWS + 1:
        rows = rows[: MAX_ROWS + 1]
        skipped.append({"line": MAX_ROWS + 2, "column": "rows", "value": "", "reason": f"Rows after the first {MAX_ROWS} were not read"})
    if any(len(r) > MAX_COLS and any(c.strip() for c in r[MAX_COLS:]) for r in rows):
        skipped.append({"line": 0, "column": "columns", "value": "", "reason": f"Columns after the first {MAX_COLS} were not read"})
    rows = [r[:MAX_COLS] for r in rows]
    header = [h.strip().lower().replace(" ", "_") for h in rows[0]]
    missing = [c for c in ("area", "clauses", "systems") if c not in header]
    if missing:
        raise ValueError(f"The plan needs a column named {', '.join(missing)}; expected {', '.join(PLAN_COLUMNS)}")
    lines = []
    for n, row in enumerate(rows[1:], start=2):
        cells = {h: (row[i].strip() if i < len(row) else "") for i, h in enumerate(header)}
        for i, value in enumerate(row):
            if value.strip() and (i >= len(header) or header[i] not in PLAN_COLUMNS):
                skipped.append({"line": n, "column": header[i] if i < len(header) and header[i] else "(no header)", "value": value.strip()[:200], "reason": "A cell under no known column was not read"})
        if not any(cells.values()):
            continue
        lines.append({
            "line": n, "area": cells.get("area", ""), "clauses": _split(cells.get("clauses")), "systems": _split(cells.get("systems")),
            "auditor": cells.get("auditor", "").lower(), "process_owner": cells.get("process_owner", ""),
        })
    return lines, skipped


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


# --- what the chain vouches for ------------------------------------------------


def _digest(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def evidence_digest(evidence: Any, cell_state: Optional[str]) -> str:
    return _digest({"evidence": evidence, "cell_state": cell_state})


def decision_digest(statement: Any, override_reason: Any, evidence: Any, cell_state: Any, suggested_basis: Any) -> str:
    return _digest({"statement": statement, "override_reason": override_reason, "evidence": evidence, "cell_state": cell_state, "suggested_basis": suggested_basis})


def check_digests(check: Dict[str, Any]) -> Tuple[str, str]:
    """(evidence digest, decision digest) of a check row with its evidence parsed."""
    return (
        evidence_digest(check["evidence"], check["cell_state"]),
        decision_digest(check["statement"], check["override_reason"], check["evidence"], check["cell_state"], check["suggested_basis"]),
    )


def check_mismatches(events: List[Dict[str, Any]], checks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Checks whose current row no longer matches what the chain recorded: the latest conclusion for a concluded check,
    the latest preparation for one still open. checks carry parsed evidence."""
    last_concluded: Dict[str, Dict[str, Any]] = {}
    last_prepared: Dict[str, str] = {}
    for e in events:
        if e["kind"] == "concluded":
            last_concluded[e["payload"].get("checkId")] = e["payload"]
        elif e["kind"] == "prepared":
            last_prepared.update(e["payload"].get("digests") or {})
    out = []
    for c in checks:
        evidence_d, decision_d = check_digests(c)
        if c["grade"]:
            rec = last_concluded.get(c["id"])
            if not rec or rec.get("sha256") != decision_d or rec.get("grade") != c["grade"]:
                out.append({"checkId": c["id"], "reason": "The conclusion on file differs from the one the chain recorded"})
        elif c["id"] in last_prepared and last_prepared[c["id"]] != evidence_d:
            out.append({"checkId": c["id"], "reason": "The evidence on file differs from what the chain recorded when it was prepared"})
    return out
