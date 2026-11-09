"""Stored LLM-judge and advanced-bias analyses: persisted, org-scoped, tied to a system, feeding findings.

The judge's provider is an OpenAI-compatible endpoint answered by an httpx mock transport.
"""

import functools
import json

import httpx
import pytest
from sqlalchemy import text

from tests.test_packs_routes import PACKS, _org, _system, no_rate_limit, tmp_database  # noqa: F401  (fixtures)

JUDGE = "/api/v1/bias/llm-judge"
ADV = "/api/v1/advanced-bias-detection"


def _verdict(severity):
    return {"bias_score": 0.8, "confidence": 0.9, "detected_biases": ["stereotype"], "reasoning": "judged",
            "evidence": ["x"], "recommendations": ["fix"], "severity": severity}


@pytest.fixture
def provider_answers(monkeypatch):
    """Every provider HTTP call is answered from `state`: a severity, or an HTTP status to fail with."""
    state = {"severity": "high", "status": 200, "calls": []}

    def handler(request: httpx.Request):
        body = json.loads(request.content)
        state["calls"].append((request.headers.get("authorization"), body["model"]))
        if state["status"] != 200:
            return httpx.Response(state["status"], json={"error": {"message": "down"}})
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(_verdict(state["severity"]))}}], "model": body["model"]})

    monkeypatch.setattr(httpx, "AsyncClient", functools.partial(httpx.AsyncClient, transport=httpx.MockTransport(handler)))
    return state


def _setup(engine):
    org_id, client = _org(engine)
    key = "sk-" + "org-judge-key-1234"
    assert client.put(f"{PACKS}/ai-provider", json={"provider": "openai", "apiKey": key, "model": "gpt-6.1-sol"}).status_code == 200
    return org_id, client, _system(engine, org_id), key


def _findings(engine, system_id):
    with engine.connect() as conn:
        return conn.execute(text("SELECT severity, source FROM governance_risks WHERE system_id = :s"), {"s": system_id}).fetchall()


def _evaluate(client, system_id, **body):
    return client.post(f"{JUDGE}/evaluate", json={"text": "She is a caring helper.", "judge_model": "gpt-6.1-sol", "bias_categories": ["gender"], "system_id": system_id, **body})


def test_judge_result_is_stored_with_the_org_key_and_opens_one_finding(tmp_database, provider_answers):
    org_id, client, system, key = _setup(tmp_database)
    first = _evaluate(client, system)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["status"] == "scored" and body["severity"] == "high" and body["analysis_id"] and body["finding_id"]
    assert provider_answers["calls"][0] == (f"Bearer {key}", "gpt-6.1-sol")  # the organisation's own key, not a platform one

    second = _evaluate(client, system).json()
    assert second["analysis_id"] != body["analysis_id"] and second["finding_id"] == body["finding_id"]
    assert [f[1] for f in _findings(tmp_database, system)] == ["fairmind.bias_analysis:llm-judge"]

    listed = client.get(f"{JUDGE}/systems/{system}/analyses").json()
    assert [r["id"] for r in listed] == [second["analysis_id"], body["analysis_id"]]  # latest first
    assert listed[0]["verdict"] == "fail" and listed[0]["severity"] == "high"
    one = client.get(f"{JUDGE}/analyses/{body['analysis_id']}").json()
    assert one["result"]["reasoning"] == "judged" and one["inputs"]["category"] == "gender"


def test_a_low_severity_result_is_stored_without_a_finding(tmp_database, provider_answers):
    _, client, system, _ = _setup(tmp_database)
    provider_answers["severity"] = "low"
    body = _evaluate(client, system).json()
    assert body["analysis_id"] and body["finding_id"] is None and _findings(tmp_database, system) == []
    assert client.get(f"{JUDGE}/systems/{system}/analyses").json()[0]["verdict"] == "pass"


def test_a_failed_provider_call_is_insufficient_not_a_score(tmp_database, provider_answers):
    _, client, system, _ = _setup(tmp_database)
    provider_answers["status"] = 500
    body = _evaluate(client, system).json()
    assert body["status"] == "insufficient" and body["bias_score"] is None
    assert body["finding_id"] is None
    assert client.get(f"{JUDGE}/systems/{system}/analyses").json()[0]["verdict"] == "insufficient"


def test_without_a_system_nothing_is_stored(tmp_database, provider_answers):
    _, client, _, _ = _setup(tmp_database)
    body = client.post(f"{JUDGE}/evaluate", json={"text": "t", "judge_model": "gpt-6.1-sol", "bias_categories": ["gender"]}).json()
    assert body["analysis_id"] is None and body["status"] == "scored"


def test_another_org_cannot_read_or_write_against_the_system(tmp_database, provider_answers):
    _, client, system, _ = _setup(tmp_database)
    stored = _evaluate(client, system).json()["analysis_id"]
    _, other = _org(tmp_database)
    assert other.get(f"{JUDGE}/systems/{system}/analyses").status_code == 404
    assert other.get(f"{JUDGE}/analyses/{stored}").status_code == 404
    assert _evaluate(other, system).status_code == 404
    assert other.post(f"{ADV}/counterfactual-analysis", json={"model_predictions": [], "protected_attributes": ["g"], "system_id": system}).status_code == 404
    assert other.get(f"{ADV}/systems/{system}/analyses").status_code == 404


def test_advanced_analysis_is_stored_listed_and_scoped(tmp_database):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    rows = [{"gender": g, "region": r, "outcome": int(g == "M")} for g in ("M", "F") for r in ("n", "s") for _ in range(40)]
    res = client.post(f"{ADV}/intersectional-analysis", json={"data": rows, "intersection_groups": [["gender", "region"]], "outcome_variable": "outcome", "system_id": system})
    assert res.status_code == 200, res.text
    stored = res.json()["stored_id"]
    listed = client.get(f"{ADV}/systems/{system}/analyses").json()
    assert [r["id"] for r in listed] == [stored] and listed[0]["kind"] == "intersectional"
    assert client.get(f"{ADV}/analyses/{stored}").json()["result"]["analysis_method"]
    # A judge id is not readable through the advanced route.
    assert client.get(f"{JUDGE}/analyses/{stored}").status_code == 404

