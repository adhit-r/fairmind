"""Release autopilot on a chat model: behaviour tests on the saved connection, judged by the organisation's AI provider."""

import functools
import json

import httpx
import pytest
from sqlalchemy import text

from tests.test_behaviour_runs_api import _answer, _provider, _target
from tests.test_packs_routes import _org, _system, no_rate_limit, tmp_database  # noqa: F401  (fixtures)

ROOT = "/api/v1/ai-governance"


@pytest.fixture
def stub(monkeypatch):
    """The target and the judge on one mock transport; the judge writes prompt pairs for the output-bias test."""
    from api.routes import llm

    calls = {"target": [], "judge": []}

    def handler(request: httpx.Request):
        body = json.loads(request.content)
        if request.url.host == "target.test":
            calls["target"].append(body)
            return _answer("Here is the invoice help you asked for.")
        calls["judge"].append(body)
        user = json.loads(body["messages"][1]["content"])
        if "write" in user:
            return _answer(json.dumps({"probes": [{"prompt": f"Help {g} customer {i // 2}", "category": "c", "pair": str(i // 2), "group": g}
                                                  for i, g in zip(range(user["count"]), ["women", "men"] * user["count"])]}))
        return _answer(json.dumps({"biased": False, "reason": "same answer"}))

    monkeypatch.setattr(llm, "_public_https", lambda url, what: url.strip().rstrip("/"))
    monkeypatch.setattr(httpx, "AsyncClient", functools.partial(httpx.AsyncClient, transport=httpx.MockTransport(handler)))
    return calls


def test_a_chat_model_gets_behaviour_tests_for_its_open_checks_once_target_and_judge_are_set(tmp_database, stub):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    base = f"{ROOT}/systems/{system}"

    assert not any(s.get("evaluationId") for s in client.get(f"{base}/autopilot").json()["steps"])  # no connection: nothing the agent can call
    assert _target(client, system).status_code == 200
    step = next(s for s in client.get(f"{base}/autopilot").json()["steps"] if s.get("evaluationId"))
    # the route's catalogue-evaluation step for fairness becomes the one behaviour test that counts for it, keeping its price
    assert (step["check"], step["evaluationId"], step["by"]) == ("fairness", "EV-FAI-05", "person") and step["gain"] > 0
    assert "AI provider" in step["needs"]
    client.post(f"{base}/autopilot/run?action=evaluation_run")
    assert client.get(f"{base}/autopilot").json()["events"] == []  # not ready: nothing runs

    _provider(client)
    assert _target(client, system, via="runner").status_code == 200
    step = next(s for s in client.get(f"{base}/autopilot").json()["steps"] if s.get("evaluationId"))
    assert step["by"] == "person" and "runner" in step["needs"]  # the agent cannot reach a private network
    assert _target(client, system).status_code == 200
    view = client.get(f"{base}/autopilot").json()
    assert [s["by"] for s in view["steps"] if s.get("evaluationId")] == ["agent"]
    assert any(s["action"] == "evaluation_run" and not s.get("evaluationId") and s["by"] == "person" for s in view["steps"])  # no behaviour test for it

    assert client.put(f"{base}/autopilot", json={"mode": "run"}).json()["mode"] == "run"  # turning the schedule on runs it at once,
    on = client.get(f"{base}/autopilot").json()  # after the response
    assert [(e["action"], e["actor"], e["status"]) for e in on["events"]] == [("evaluation_run", "autopilot", "done")], on["events"]
    assert on["events"][0]["detail"] == "Ran EV-FAI-05 LLM output bias on the saved connection; insufficient"  # the first run sets the baseline
    assert stub["target"] and stub["judge"]  # the system under test was asked and the judge decided
    run = client.get(f"/api/v1/packs/evaluation-runs/{on['events'][0]['evidenceId']}").json()
    assert run["evaluationId"] == "EV-FAI-05" and run["createdBy"] == "agent:autopilot" and run["judge"]["model"] == "judge-1"
    with tmp_database.connect() as conn:
        assert conn.execute(text("SELECT status FROM governance_evaluation_jobs WHERE system_id = :s"), {"s": system}).scalars().all() == ["done"]
    client.put(f"{base}/autopilot", json={"mode": "run"})
    assert client.get(f"{base}/autopilot").json()["events"] == on["events"]  # not again inside the day

    client.post(f"{base}/autopilot/run?action=evaluation_run")  # "Run now" is not limited; it compares with the first run
    again = client.get(f"{base}/autopilot").json()
    assert again["events"][0]["detail"].endswith("; passed"), again["events"]
    assert not any(s.get("evaluationId") for s in again["steps"])  # the gate counts the passing run: fairness is proven and leaves the route


def test_behaviour_tests_no_gate_check_counts_are_rerun_until_they_pass(tmp_database, stub):
    from tests.test_packs_routes import _store

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    base = f"{ROOT}/systems/{system}"
    # before a connection is saved, the route says why fairness reads as a CSV run
    assert any("Model connection" in n for n in client.get(f"{base}/gate").json()["path"]["notes"])
    assert _target(client, system).status_code == 200
    assert not any("Model connection" in n for n in client.get(f"{base}/gate").json()["path"]["notes"])

    _store(tmp_database, org_id, system, "evaluation_run", {"evaluationId": "EV-SEC-01", "status": "failed"}, "2026-11-01T10:00:00")
    upkeep = [s for s in client.get(f"{base}/autopilot").json()["steps"] if s.get("evaluationId") == "EV-SEC-01"]
    assert [(s["check"], s["action"], s.get("upkeep")) for s in upkeep] == [("behaviour", "evaluation_run", True)]
    _store(tmp_database, org_id, system, "evaluation_run", {"evaluationId": "EV-SEC-01", "status": "passed"}, "2026-11-01T11:00:00")
    assert not any(s.get("evaluationId") == "EV-SEC-01" for s in client.get(f"{base}/autopilot").json()["steps"])


def test_autopilot_waits_for_an_intended_use_and_takes_it_from_classification(tmp_database, stub):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    base = f"{ROOT}/systems/{system}"
    _provider(client)
    assert _target(client, system, intendedUse="").status_code == 200
    step = next(s for s in client.get(f"{base}/autopilot").json()["steps"] if s.get("evaluationId"))
    assert step["by"] == "person" and "intended use" in step["needs"]  # the judge would have nothing to write probes from

    with tmp_database.begin() as conn:
        conn.execute(text("UPDATE governance_ai_systems SET metadata_json = :m WHERE id = :id"),
                     {"m": json.dumps({"applicability": {"answers": {"intendedPurpose": "Answers invoice questions"}}}), "id": system})
    step = next(s for s in client.get(f"{base}/autopilot").json()["steps"] if s.get("evaluationId"))
    assert step["by"] == "agent" and step["needs"] is None
