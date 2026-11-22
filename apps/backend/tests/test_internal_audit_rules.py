"""The internal audit's rules without a database: grading, independence, reading the auditors' plan, the hash chain."""

import io

import pytest

from src.application.services import internal_audit_rules as r


@pytest.mark.parametrize("cell,answered,grade", [
    ("proven", False, "conformity"), ("attested", False, "observation"), ("estimated", False, "observation"),
    ("partial", False, "minor_nc"), ("stale", False, "minor_nc"), ("open", False, "major_nc"), ("none", False, "major_nc"),
    ("open", True, "minor_nc"), ("none", True, "minor_nc"), ("proven", True, "conformity"),
])
def test_grading_rule(cell, answered, grade):
    got, basis = r.suggest_grade(cell, answered)
    assert got == grade and basis.startswith("Rule:")


def test_independence():
    me = {"id": "u1", "email": "Ann@acme.test"}
    systems = [{"id": "s1", "name": "Credit model", "owner": "ann@acme.test"}, {"id": "s2", "name": "Chatbot", "owner": "bob@acme.test"}]
    assert [c["kind"] for c in r.conflicts(me, None, systems)] == ["system_owner"]
    assert [c["kind"] for c in r.conflicts(me, "U1", systems[1:])] == ["process_owner"]
    assert r.conflicts(me, "bob@acme.test", systems[1:]) == []


CONTROLS = {"6.1.2": {"key": "ISO42001|6.1.2"}, "9.2": {"key": "ISO42001|9.2"}}
SYSTEMS = [{"id": "sys-1", "name": "Credit model"}, {"id": "sys-2", "name": "Chatbot"}]


def test_plan_csv_is_matched_and_nothing_is_dropped():
    csv_bytes = (
        "Area,Clauses,Systems,Auditor,Process Owner\n"
        "Risk,6.1.2; 9.2; 99.9,Credit model,ann@acme.test,bob@acme.test\n"
        "Support,Clause 9.2,Chatbot;Unknown bot,nobody@acme.test,\n"
        "Empty,1.1,Nothing,,\n"
        ",9.2,Chatbot,,\n"
        "Again,9.2,Credit model,,\n"
    ).encode()
    lines, skipped = r.parse_plan("plan.csv", csv_bytes)
    assert skipped == []
    areas, unmatched = r.match_plan(lines, CONTROLS, SYSTEMS, {"ann@acme.test": "u1"})
    assert [a["name"] for a in areas] == ["Risk", "Support"]
    assert areas[0]["checks"] == [("6.1.2", "sys-1"), ("9.2", "sys-1")] and areas[0]["auditor_id"] == "u1"
    assert areas[1]["checks"] == [("9.2", "sys-2")] and areas[1]["auditor_id"] is None
    got = {(u["line"], u["column"], u["value"]) for u in unmatched}
    assert {(2, "clauses", "99.9"), (3, "systems", "Unknown bot"), (3, "auditor", "nobody@acme.test"), (4, "clauses", "1.1"), (4, "systems", "Nothing"), (5, "area", "")} <= got
    assert any(u["line"] == 6 and "earlier area" in u["reason"] for u in unmatched)  # 9.2 on Credit model already planned
    assert any(u["line"] == 4 and u["column"] == "area" for u in unmatched)


def test_plan_xlsx_and_bad_files():
    from openpyxl import Workbook

    wb = Workbook()
    wb.active.append(["area", "clauses", "systems"])
    wb.active.append(["Risk", "9.2", "Credit model"])
    buf = io.BytesIO()
    wb.save(buf)
    assert r.parse_plan("plan.xlsx", buf.getvalue())[0][0]["clauses"] == ["9.2"]
    with pytest.raises(ValueError):
        r.parse_plan("plan.pdf", b"x")
    with pytest.raises(ValueError):
        r.parse_plan("plan.csv", b"area,systems\nRisk,x\n")


def test_chain_detects_tampering():
    events, prev = [], r.GENESIS
    for i, kind in enumerate(("created", "plan_uploaded"), start=1):
        e = {"audit_id": "a", "seq": i, "kind": kind, "actor": "u", "payload": {"n": i}, "created_at": "t", "prev_hash": prev}
        e["hash"] = r.event_hash("a", i, kind, "u", e["payload"], "t", prev)
        events.append(e)
        prev = e["hash"]
    assert r.verify_chain(events)
    events[0]["payload"] = {"n": 9}
    assert not r.verify_chain(events)


def test_a_failing_check_is_never_softened_and_the_basis_names_the_state():
    assert r.suggest_grade("fails", True)[0] == "major_nc"
    grade, basis = r.suggest_grade("none", True)
    assert grade == "minor_nc" and "no evidence reaches this clause" in basis and "open" not in basis


def test_unverifiable_owners_are_reported():
    me = {"id": "u1", "email": "ann@acme.test"}
    known = {"u1", "ann@acme.test", "bob@acme.test"}
    got = r.conflicts(me, "ops@acme.test", [{"id": "s", "name": "Chatbot", "owner": "Bob"}, {"id": "t", "name": "Bot", "owner": "bob@acme.test"}], known)
    assert [c["kind"] for c in got] == ["unverifiable", "unverifiable"]
    assert r.conflicts(me, "ops@acme.test", []) == []  # nothing to compare with when the caller gives no known people


def test_xlsx_limits_and_what_was_not_read():
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["area", "clauses", "systems", "notes"])
    ws.append(["Risk", "9.2", "Credit model", "keep this note"])
    ws.append(["Risk2", "9.2", "Chatbot", "", "stray"])
    for _ in range(r.MAX_ROWS + 5):
        ws.append(["More", "9.2", "Chatbot"])
    wb.create_sheet("Second")
    buf = io.BytesIO()
    wb.save(buf)
    lines, skipped = r.parse_plan("plan.xlsx", buf.getvalue())
    assert len(lines) == r.MAX_ROWS
    reasons = {(s["column"], s["value"]) for s in skipped}
    assert {("sheet", "Second"), ("notes", "keep this note"), ("(no header)", "stray"), ("rows", "")} <= reasons
