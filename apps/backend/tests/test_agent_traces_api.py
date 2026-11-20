"""Live traces through the API: extending a run, re-sent steps, rationale coverage, truncation, org scope."""

from tests.test_packs_routes import PACKS, _org, _system, no_rate_limit, tmp_database  # noqa: F401  (fixtures)


def _url(system, trace=""):
    return f"{PACKS}/ai-systems/{system}/traces" + (f"/{trace}" if trace else "")


def test_a_run_is_extended_and_resent_steps_update(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    first = {"traceId": "run-1", "name": "Invoice question", "input": {"question": "Where is invoice 42?"}, "steps": [
        {"id": "s1", "kind": "retrieval", "name": "search_invoices", "output": [{"doc": "inv-42"}]},
        {"id": "s2", "kind": "tool", "name": "lookup_invoice", "status": "running"},
    ]}
    assert client.post(_url(system), json=first).json() == {"traceId": "run-1", "stepsReceived": 2, "truncated": False}
    second = {"traceId": "run-1", "status": "ok", "output": "It was paid on 3 March.", "rationale": "The ledger shows a payment.", "steps": [
        {"id": "s2", "kind": "tool", "name": "lookup_invoice", "status": "ok", "rationale": "The retrieved document names invoice 42", "output": {"paid": True}},
        {"id": "s3", "kind": "llm", "name": "answer"},
    ]}
    assert client.post(_url(system), json=second).status_code == 200

    trace = client.get(_url(system, "run-1")).json()["trace"]
    assert [s["id"] for s in trace["steps"]] == ["s1", "s2", "s3"]  # s2 kept its place when it was sent again
    assert trace["steps"][1]["status"] == "ok" and trace["steps"][1]["output"] == {"paid": True}
    assert (trace["name"], trace["status"], trace["input"]) == ("Invoice question", "ok", {"question": "Where is invoice 42?"})  # kept from the first call
    assert trace["rationale"] == "The ledger shows a payment."
    assert trace["rationaleCoverage"] == 0.5  # the tool call has a reason, the model call does not; the retrieval is not counted

    listed = client.get(_url(system)).json()["traces"]
    assert [(t["traceId"], t["stepCount"], t["rationaleCoverage"]) for t in listed] == [("run-1", 3, 0.5)]

    assert client.delete(_url(system, "run-1")).status_code == 200
    assert client.get(_url(system, "run-1")).status_code == 404


def test_long_text_is_cut_and_flagged(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    body = {"traceId": "run-2", "steps": [{"id": "s1", "kind": "llm", "output": "x" * 25_000}]}
    assert client.post(_url(system), json=body).json()["truncated"] is True
    trace = client.get(_url(system, "run-2")).json()["trace"]
    assert trace["truncated"] is True and len(trace["steps"][0]["output"]) == 20_000
    assert trace["rationaleCoverage"] == 0.0


def test_other_organisations_and_viewers_are_refused(tmp_database):
    org, _ = _org(tmp_database)
    system = _system(tmp_database, org)
    _, outsider = _org(tmp_database)
    assert outsider.post(_url(system), json={"traceId": "run-3"}).status_code == 404
    assert outsider.get(_url(system)).status_code == 404
    viewer_org, viewer = _org(tmp_database, role="viewer")
    own = _system(tmp_database, viewer_org)
    assert viewer.post(_url(own), json={"traceId": "run-4"}).status_code == 403
    assert viewer.get(_url(own)).status_code == 200


def test_a_later_call_keeps_what_it_leaves_out(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    start = {"traceId": "run-5", "status": "ok", "steps": [{"id": "s1", "kind": "llm", "name": "plan", "input": {"q": "x"}, "rationale": "Asked to plan"}]}
    assert client.post(_url(system), json=start).status_code == 200
    assert client.post(_url(system), json={"traceId": "run-5", "steps": [{"id": "s1", "output": "42"}]}).status_code == 200
    trace = client.get(_url(system, "run-5")).json()["trace"]
    assert trace["status"] == "ok"  # not back to running
    step = trace["steps"][0]
    assert (step["kind"], step["name"], step["input"], step["rationale"], step["status"]) == ("llm", "plan", {"q": "x"}, "Asked to plan", "ok")
    assert step["output"] == "42"  # the string, not the number


def test_unstorable_text_and_unreadable_ids(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    hindi = {"text": "न" * 5000}  # not cut: each character counts once
    body = {"traceId": "run-6", "rationale": "a\u0000b", "input": hindi, "steps": [{"id": "s1", "kind": "tool", "output": "a\u0000b"}]}
    assert client.post(_url(system), json=body).json()["truncated"] is False
    trace = client.get(_url(system, "run-6")).json()["trace"]
    assert trace["rationale"] == "ab" and trace["input"] == hindi and trace["steps"][0]["output"] == "ab"
    assert client.post(_url(system), json={"traceId": "user/42"}).status_code == 422
    assert client.get(_url(system, "a%00b")).status_code == 404


# --- live runs read by evaluations ------------------------------------------------------------------

import functools  # noqa: E402
import json  # noqa: E402
from datetime import datetime, timedelta, timezone  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402

GOV = "/api/v1/ai-governance"


def _run(system, trace_id, tools, answer="Invoice 42 was paid on 3 March.", source="Invoice 42: paid 3 March"):
    steps = [{"id": "r", "kind": "retrieval", "name": "search", "output": source}]
    steps += [{"id": f"t{i}", "kind": "tool", "name": t, "output": {"ok": True}} for i, t in enumerate(tools)]
    return {"traceId": trace_id, "status": "ok", "input": "Where is invoice 42?", "output": answer, "steps": steps}


def _age(engine, trace_id, days):
    at = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with engine.begin() as conn:
        conn.execute(text("UPDATE governance_agent_traces SET received_at = :at WHERE trace_id = :tid"), {"at": at, "tid": trace_id})


@pytest.fixture
def judge(monkeypatch):
    """The organisation's model, answered here: every claim is supported unless the answer says 'instalment'."""
    from api.routes import llm

    def handler(request):
        user = json.loads(json.loads(request.content)["messages"][1]["content"])
        bad = "instalment" in json.dumps(user)
        verdict = {"claims": 2, "supported": 1 if bad else 2, "unsupported": ["an instalment plan"] if bad else [], "reason": "judged"}
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(verdict)}}], "model": "stub"})

    monkeypatch.setattr(llm, "_public_https", lambda url, what: url.strip().rstrip("/"))
    monkeypatch.setattr(httpx, "AsyncClient", functools.partial(httpx.AsyncClient, transport=httpx.MockTransport(handler)))


def test_summary_counts_runs_per_day_and_errors(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    assert client.get(_url(system, "summary")).json()["lastRunAt"] is None
    client.post(_url(system), json={"traceId": "a", "status": "ok"})
    client.post(_url(system), json={"traceId": "b", "status": "error"})
    client.post(_url(system), json={"traceId": "old", "status": "ok"})
    _age(tmp_database, "old", 3)
    summary = client.get(_url(system, "summary")).json()
    assert summary["week"] == {"runs": 3, "errors": 1}
    assert len(summary["days"]) == 14 and summary["days"][-1]["runs"] == 2 and summary["days"][-1]["errors"] == 1
    assert sum(d["runs"] for d in summary["days"]) == 3 and summary["evaluations"] == []


def test_tool_call_monitoring_reads_live_runs_against_the_weeks_before(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    assert client.get(f"{PACKS}/evaluations/EV-MON-02/engine").json()["liveRuns"] is True
    run = lambda: client.post(f"{PACKS}/evaluations/EV-MON-02/runs", data={"system_id": system, "source": "traces", "params": json.dumps({"max_score": 0.2})})
    assert "No tool calls" in run().json()["detail"]
    for i in range(4):
        client.post(_url(system), json=_run(system, f"base-{i}", ["lookup_invoice", "send_email"]))
        _age(tmp_database, f"base-{i}", 10)
    client.post(_url(system), json=_run(system, "now-1", ["lookup_invoice", "send_email"]))
    client.post(_url(system), json=_run(system, "now-2", ["lookup_invoice", "issue_refund"]))
    stored = run()
    assert stored.status_code == 200, stored.text
    body = stored.json()
    assert body["source"] == "traces" and body["metrics"]["calls"] == 4
    assert [(d["tool"], d["session"]) for d in body["detail"]] == [("issue_refund", "now-2")]  # never seen in the baseline; the run it came from
    assert body["status"] == "failed"  # 1 of 4 is over the agreed 0.2
    latest = client.get(_url(system, "summary")).json()["evaluations"]
    assert [(e["evaluationId"], e["status"]) for e in latest] == [("EV-MON-02", "failed")]


def test_groundedness_judges_recorded_answers_without_calling_the_system(tmp_database, judge):
    from tests.test_behaviour_runs_api import _provider

    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    _provider(client)
    client.post(_url(system), json=_run(system, "good", []))
    client.post(_url(system), json=_run(system, "bad", [], answer="You can pay invoice 42 in an instalment plan."))
    client.post(_url(system), json={"traceId": "no-source", "status": "ok", "output": "Hello"})  # nothing to ground it in
    started = client.post(f"{PACKS}/evaluations/EV-TST-03/runs", data={"system_id": system, "source": "traces"})
    assert started.status_code == 202, started.text  # no model connection needed
    job = client.get(f"{PACKS}/evaluation-jobs/{started.json()['job']['id']}").json()
    assert job["status"] == "done", job
    run = client.get(f"{PACKS}/evaluation-runs/{job['evidenceId']}").json()
    assert run["source"] == "traces" and run["target"] == {"kind": "live-runs"}
    assert run["metrics"]["questions"] == 2 and run["metrics"]["supported"] == 3
    flagged = [r["traceId"] for r in run["detail"] if r["verdict"] != "grounded"]
    assert flagged == ["bad"]


def test_the_gate_names_tool_call_monitoring_once_live_runs_arrive(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)

    def monitoring_steps():
        path = client.get(f"{GOV}/systems/{system}/gate").json()["path"]
        options = path["options"] + ([path["toGo"]] if path["toGo"] else [])
        return [s for o in options for s in o["steps"] if s["check"] == "monitoring" and s["action"] == "evaluation_run"]

    assert monitoring_steps() and all("evaluationId" not in s for s in monitoring_steps())
    client.post(_url(system), json=_run(system, "now", ["lookup_invoice"]))
    assert all("evaluationId" not in s for s in monitoring_steps())  # no baseline yet, so EV-MON-02 could not run
    client.post(_url(system), json=_run(system, "before", ["lookup_invoice"]))
    _age(tmp_database, "before", 10)
    assert {(s["evaluationId"], s["source"]) for s in monitoring_steps()} == {("EV-MON-02", "traces")}


def test_autopilot_reruns_tool_call_monitoring_with_the_settings_a_person_chose(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    base = f"{GOV}/systems/{system}"
    client.post(_url(system), json=_run(system, "before", ["lookup_invoice", "send_email"]))
    _age(tmp_database, "before", 10)
    client.post(_url(system), json=_run(system, "now", ["lookup_invoice", "issue_refund"]))  # a tool the baseline never used

    def step():
        return next(s for s in client.get(f"{base}/autopilot").json()["steps"] if s.get("source") == "traces")

    assert step()["evaluationId"] == "EV-MON-02" and step()["by"] == "person" and "agreed values" in step()["needs"]
    client.post(f"{base}/autopilot/run?action=evaluation_run")
    assert client.get(f"{base}/autopilot").json()["events"] == []  # nothing a person has set yet, so nothing runs

    first = client.post(f"{PACKS}/evaluations/EV-MON-02/runs", data={"system_id": system, "source": "traces", "params": json.dumps({"max_score": 0.1})})
    assert first.status_code == 200, first.text
    # Once a person has run it, the step leaves the route (the check is measured) and the agent may rerun it with the same settings
    # when the check opens again; that rerun is what the scheduled agent calls.
    import asyncio
    from sqlalchemy.orm import Session
    from api.routes import autopilot

    with Session(bind=tmp_database) as db:
        assert autopilot._live_run_needs(db, system, "EV-MON-02") is None
        evidence_id, detail = asyncio.run(autopilot._live_run_evaluation(db, str(org), system, "EV-MON-02"))
        content = json.loads(db.execute(text("SELECT content_json FROM governance_evidence WHERE id = :id"), {"id": evidence_id}).scalar())
        by = db.execute(text("SELECT uploaded_by FROM governance_evidence WHERE id = :id"), {"id": evidence_id}).scalar()
    assert "on this week's live runs" in detail and by == "agent:autopilot"
    assert content["params"]["max_score"] == 0.1 and content["source"] == "traces" and content["status"] == "failed"
