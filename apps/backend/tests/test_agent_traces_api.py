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
    # stored as a person-started run is: hashed inputs, engine versions, provenance
    assert content["provenance"] == {"class": "computed_from_upload", "modelJudged": False}
    assert content["engine"]["id"] == "EV-MON-02" and content["inputs"] and all(len(h) == 64 for h in content["inputs"].values())


# --- more evaluations on live runs: drift, scope, tool-call correctness, runaways, secrets ------------------------


def _live(client, evaluation_id, system, params=None, files=None):
    data = {"system_id": system, "source": "traces", "params": json.dumps(params or {})}
    return client.post(f"{PACKS}/evaluations/{evaluation_id}/runs", data=data, files=files)


def _tools(trace_id, calls, **trace):
    """A finished run whose tool steps are (name, input, status) in order."""
    steps = [{"id": f"t{i}", "kind": "tool", "name": n, "input": a, "status": st} for i, (n, a, st) in enumerate(calls)]
    return {"traceId": trace_id, "status": "ok", "input": "Refund order 7", "steps": steps, **trace}


def test_prompt_drift_reads_this_weeks_prompts_against_the_weeks_before_or_an_upload(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    assert _live(client, "EV-DAT-01", system).json()["detail"] == "No live runs arrived this week"
    for i in range(25):
        prompt = f"Where is invoice {i} for the Pune office?"
        client.post(_url(system), json={"traceId": f"now-{i}", "status": "ok", "input": prompt})
        client.post(_url(system), json={"traceId": f"old-{i}", "status": "ok", "input": prompt})
        _age(tmp_database, f"old-{i}", 10)
    run = _live(client, "EV-DAT-01", system).json()
    # the same prompts as the four weeks before: every current prompt is in distribution
    assert run["status"] == "passed" and run["metrics"]["currentRows"] == 25 and run["metrics"]["datasetDrift"] == 1.0, run
    assert run["files"] == {"traces": "Live runs, last 7 days (reference: 25 prompts from the four weeks before)"}
    assert run["params"]["features"] == "prompt" and "_live_runs_note" not in run["params"]
    assert run["provenance"] == {"class": "computed_from_upload", "modelJudged": False}

    poems = "prompt\n" + "\n".join(f"Translate poem number {i} into French verse" for i in range(25))
    uploaded = _live(client, "EV-DAT-01", system, files={"reference": ("poems.csv", poems.encode(), "text/csv")}).json()
    assert uploaded["status"] == "failed" and uploaded["metrics"]["datasetDrift"] == 0.0  # nothing like the uploaded reference
    assert uploaded["files"] == {"traces": "Live runs, last 7 days", "reference": "poems.csv"}
    assert [u["name"] for u in client.get(f"{PACKS}/evaluations/EV-DAT-01/engine").json()["liveRunsUploads"]] == ["reference"]


def test_out_of_scope_tool_calls_are_read_from_tool_steps_and_a_cap_is_named(tmp_database, monkeypatch):
    from api.routes import agent_traces

    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    allowed = {"allowed_tools": "lookup_order"}
    client.post(_url(system), json={"traceId": "chat", "status": "ok", "input": "Hello", "output": "Hi"})
    empty = _live(client, "EV-AGT-02", system, allowed).json()  # runs arrived, but no tool calls: kept as insufficient
    assert empty["status"] == "insufficient" and "carry no tool calls" in empty["summary"] and empty["source"] == "traces"
    assert client.post(_url(system), json=_tools("r1", [("lookup_order", {"id": 7}, "ok"), ("issue_refund", {"id": 7}, "blocked")])).status_code == 200
    client.post(_url(system), json=_tools("r2", [("delete_account", {"id": 9}, "ok")]))
    run = _live(client, "EV-AGT-02", system, allowed).json()
    assert run["status"] == "failed" and (run["metrics"]["outOfScope"], run["metrics"]["blocked"], run["metrics"]["actions"]) == (2, 1, 3)
    assert [(d["scenario"], d["tool"], d["outcome"]) for d in run["detail"]] == [("r2", "delete_account", "executed"), ("r1", "issue_refund", "blocked")]
    assert client.get(_url(system, "r1")).json()["trace"]["steps"][1]["status"] == "blocked"

    monkeypatch.setattr(agent_traces, "MAX_TOOL_CALLS", 2)
    capped = _live(client, "EV-AGT-02", system, allowed).json()
    assert capped["files"] == {"traces": "Live runs, last 7 days (the newest 2 of 3 tool calls)"} and capped["metrics"]["actions"] == 2
    assert capped["partialRead"] is True and run["partialRead"] is False


def test_tool_names_and_run_ids_are_read_as_sent(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    client.post(_url(system), json=_tools("r1", [("NA", {"id": 1}, "ok"), ("lookup", {"id": 1}, "ok")]))
    # NA is an approved tool, not a missing name: nothing is out of scope
    assert _live(client, "EV-AGT-02", system, {"allowed_tools": "NA,lookup"}).json()["status"] == "insufficient"
    for run in ("001", "1"):
        client.post(_url(system), json=_tools(run, [("search", {"q": "refund"}, "ok")] * 4))
    run = _live(client, "EV-MON-05", system).json()  # four repeats each, two runs: no loop of eight
    assert run["status"] == "passed" and run["metrics"]["runs"] == 3, run


def test_tool_call_correctness_compares_tool_steps_with_the_expected_calls_a_run_sent(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    client.post(_url(system), json=_tools("plain", [("lookup_order", {"id": 7}, "ok")]))  # no expectation: not read
    unexpected = _live(client, "EV-TST-06", system).json()
    assert unexpected["status"] == "insufficient" and "expected tool calls" in unexpected["summary"]
    expected = [{"tool": "lookup_order", "args": {"id": 7}}, {"tool": "send_email"}]
    client.post(_url(system), json=_tools("good", [("lookup_order", {"id": 7, "verbose": True}, "ok"), ("send_email", {"to": "acme"}, "ok")], expectedCalls=expected))
    client.post(_url(system), json=_tools("missed", [], expectedCalls=[{"tool": "issue_refund"}]))
    assert client.get(_url(system, "good")).json()["trace"]["expectedCalls"] == expected
    run = _live(client, "EV-TST-06", system).json()
    # 2 of 3 expected positions right: the extra argument is allowed, the missing refund is wrong
    assert run["status"] == "failed" and (run["metrics"]["correct"], run["metrics"]["calls"], run["metrics"]["scenarios"]) == (2, 3, 2)
    assert {d["scenario"]: d["wrong"] for d in run["detail"]} == {"missed": 1, "good": 0}


def test_expected_calls_that_would_be_cut_are_refused_and_extra_calls_count_as_wrong(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    many = [{"tool": "lookup_order", "args": {"id": i, "note": "x" * 200}} for i in range(150)]
    assert client.post(_url(system), json=_tools("big", [], expectedCalls=many)).status_code == 413
    client.post(_url(system), json=_tools("chatty", [("lookup_order", {"id": 7}, "ok")] * 3, expectedCalls=[{"tool": "lookup_order", "args": {"id": 7}}]))
    run = _live(client, "EV-TST-06", system).json()
    assert (run["metrics"]["correct"], run["metrics"]["calls"], run["metrics"]["scenarios"]) == (1, 3, 1), run


def test_runaway_detection_counts_repeated_identical_tool_calls_per_run(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    client.post(_url(system), json=_tools("loop", [("search", {"q": "refund"}, "ok")] * 7))
    client.post(_url(system), json=_tools("busy", [("search", {"q": f"page {i}"}, "ok") for i in range(7)]))  # different inputs: no loop
    run = _live(client, "EV-MON-05", system).json()
    assert run["status"] == "failed" and (run["metrics"]["runs"], run["metrics"]["calls"], run["metrics"]["runawayEpisodes"]) == (2, 14, 1)
    assert [(d["run_id"], d["longestRepeat"], d["undetected"]) for d in run["detail"]] == [("loop", 7, True)]


def test_secrets_in_run_context_are_found_and_shown_masked(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    key = "AKIAZ7Q3R2M5N8P4K6TW"
    client.post(_url(system), json={"traceId": "clean", "status": "ok", "input": "Hello", "output": "Hi"})
    assert _live(client, "EV-SEC-16", system).json()["status"] == "passed"
    client.post(_url(system), json=_tools("leak", [("read_config", {"path": "settings"}, "ok")], output="done"))
    client.post(_url(system), json={"traceId": "leak", "steps": [{"id": "t0", "output": {"aws_key": key}}]})
    run = client.get(f"{PACKS}/evaluation-runs/{_live(client, 'EV-SEC-16', system).json()['id']}").json()
    assert run["status"] == "failed" and run["metrics"]["secretsByCategory"] == {"aws_access_key": 1}
    assert [d["value"] for d in run["detail"] if d["kind"] == "secret"] == ["AKI...TW"] and key not in json.dumps(run)


def test_replaying_live_runs_is_not_ready_when_the_runner_calls_the_system(tmp_database):
    from tests.test_behaviour_runs_api import RUNNER_TARGET

    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    client.post(_url(system), json={"traceId": "d1", "status": "ok", "input": "x"})
    assert client.put(f"{PACKS}/ai-systems/{system}/target", json=RUNNER_TARGET).status_code == 200
    ways = {w["way"]: w for w in client.get(f"{PACKS}/evaluations/EV-OVS-04/engine", params={"system": system}).json()["ways"]}
    assert ways["live_runs"]["ready"] is False and "runner" in ways["live_runs"]["reason"]
    assert "reason" not in ways.get("calls_system", {})
    # reading live runs alone needs no connection, runner or not
    assert {"way": "live_runs", "ready": True} in client.get(f"{PACKS}/evaluations/EV-MON-05/engine", params={"system": system}).json()["ways"]


def test_a_secret_scan_bounds_the_text_it_reads_and_a_partial_pass_proves_nothing(tmp_database, monkeypatch):
    from api.routes import agent_traces

    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    client.post(_url(system), json={"traceId": "leak", "status": "ok", "input": "x", "output": {"aws_key": "AKIAZ7Q3R2M5N8P4K6TW"}})
    _age(tmp_database, "leak", 1)
    assert _live(client, "EV-SEC-16", system).json()["status"] == "failed"
    client.post(_url(system), json={"traceId": "long", "status": "ok", "steps": [{"id": f"s{i}", "output": "y" * 100} for i in range(5)]})
    monkeypatch.setattr(agent_traces, "MAX_CONTEXT", 250)
    run = client.get(f"{PACKS}/evaluation-runs/{_live(client, 'EV-SEC-16', system).json()['id']}").json()
    assert run["status"] == "passed" and run["partialRead"] is True, run
    assert run["files"] == {"traces": "Live runs, last 7 days (the newest 1 of 2 runs, cut at 250 characters)"}
    with tmp_database.begin() as conn:  # the failure's finding stays open: the leak was never read
        assert conn.execute(text("SELECT status FROM governance_risks WHERE system_id = :s AND metadata_json LIKE '%EV-SEC-16%'"), {"s": system}).scalar() == "open"


def test_prompt_drift_samples_mask_secrets_and_personal_data(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org)
    for i in range(25):
        client.post(_url(system), json={"traceId": f"now-{i}", "status": "ok", "input": f"Email ravi{i}@acme.example the refund for order {i}"})
    poems = "prompt\n" + "\n".join(f"Translate poem number {i} into French verse" for i in range(25))
    created = _live(client, "EV-DAT-01", system, files={"reference": ("poems.csv", poems.encode(), "text/csv")}).json()
    run = client.get(f"{PACKS}/evaluation-runs/{created['id']}").json()
    samples = [d["prompt"] for d in run["detail"] if d["kind"] == "sample"]
    assert samples and all("@acme.example" not in p and "rav..." in p for p in samples), samples
