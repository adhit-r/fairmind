"""Agentic governance plan: discovery reads and asks, the map follows the answers, tasks come from the crosswalk."""

import pytest

from config.settings import settings
from tests.test_packs_routes import _fairness, _org, _save_provider, _store, _system, no_rate_limit, tmp_database  # noqa: F401

PLAN = "/api/v1/plan"
ABOUT = "We are an NBFC in Mumbai. We score loan applications with gradient boosted models and run an LLM chatbot for customers."


@pytest.fixture(autouse=True)
def no_grok_cli(monkeypatch):
    """A developer machine may run the Grok CLI for every organisation; these tests need the saved provider or none."""
    monkeypatch.setattr(settings, "grok_cli_enabled", False)


def _answer(client, key, value):
    response = client.post(f"{PLAN}/discovery", json={"key": key, "value": value})
    assert response.status_code == 200, response.text
    return response.json()


def _task(view, control):
    return next(t for t in view["tasks"] if t["controlId"] == control)


def test_discovery_reads_the_description_asks_the_rest_and_builds_a_plan_from_the_crosswalk(tmp_database):
    org_id, client = _org(tmp_database)
    view = client.get(PLAN).json()
    assert view["status"] == "discovery" and view["discovery"]["next"]["key"] == "about" and view["discovery"]["agent"] == "rules"
    assert client.post(f"{PLAN}/discovery", json={"key": "about", "value": "short"}).status_code == 422

    disc = _answer(client, "about", ABOUT)["discovery"]
    facts = {f["key"]: f for f in disc["facts"]}
    assert facts["jurisdictions"]["value"] == ["india"] and facts["sector"]["value"] == "financial"
    assert set(facts["ai_types"]["value"]) == {"genai", "predictive"} and facts["decisions_about_people"]["value"] == "yes"
    assert facts["sector"]["source"] == "description"
    assert disc["next"]["key"] == "value_chain"  # everything the description answered is skipped
    assert disc["transcript"][-1]["role"] == "agent" and "filled in" in disc["transcript"][-1]["text"]

    assert client.post(f"{PLAN}/discovery", json={"key": "value_chain", "value": "nonsense"}).status_code == 422
    assert _answer(client, "value_chain", "deployer")["discovery"]["next"]["key"] == "maturity"
    levels = {c: "none" for c in ("FMC-GOV-01", "FMC-GOV-02", "FMC-GOV-03", "FMC-GOV-04", "FMC-INV-01", "FMC-RSK-01", "FMC-INC-01", "FMC-SUP-01", "FMC-PRV-01")}
    levels["FMC-GOV-02"] = "partial"
    assert _answer(client, "maturity", levels)["discovery"]["next"]["key"] == "people"
    disc = _answer(client, "people", {"head_ai_governance": "A. Rao", "legal": "S. Iyer"})["discovery"]
    question = disc["next"]
    assert question["key"] == "frameworks"
    assert [f["key"] for f in question["suggested"]] == ["ISO42001", "INDAI", "RBIFREEAI", "OWASPLLM"]
    assert {o["role"]: o["person"] for o in disc["map"]["owners"]}["head_ai_governance"] == "A. Rao"
    assert any(c["id"] == "FMC-AGT-01" for c in disc["map"]["outOfScope"])  # no agents

    assert client.post(f"{PLAN}/generate").status_code == 409  # frameworks not confirmed yet
    _answer(client, "frameworks", ["ISO42001", "INDAI", "RBIFREEAI"])
    view = client.post(f"{PLAN}/generate").json()
    assert view["status"] == "active" and view["tasks"]
    chosen = {"ISO42001", "INDAI", "RBIFREEAI"}
    for t in view["tasks"]:
        assert t["requirements"] and {r["framework"] for r in t["requirements"]} <= chosen, t["key"]
        assert t["state"] in ("todo", "needs_you", "agent", "review", "attested", "proven")
    assert not any(t["controlId"] in ("FMC-AGT-01", "FMC-AGT-02", "FMC-SLF-01") for t in view["tasks"])
    assert [t["priority"] for t in view["tasks"]] == list(range(1, len(view["tasks"]) + 1))
    scope = _task(view, "FMC-GOV-01")
    assert scope["kind"] == "org" and scope["state"] == "needs_you" and scope["ownerSuggested"] == "A. Rao" and scope["title"].startswith("Establish")
    policy = _task(view, "FMC-GOV-02")
    assert policy["state"] == "todo" and policy["blockedBy"] == ["control:FMC-GOV-01"] and policy["title"].startswith("Formalise")
    assert view["changes"][0]["summary"] == f"Plan created with {len(view['tasks'])} tasks"

    assert client.post(f"{PLAN}/tasks/control:FMC-GOV-01/attest", json={"statement": "short"}).status_code == 422
    view = client.post(f"{PLAN}/tasks/control:FMC-GOV-01/attest", json={"statement": "Board approved the AI governance scope on 3 Nov", "reference": "Board minutes 2026-11-03"}).json()
    # a statement alone, with no completed run, is attested, not proven
    assert _task(view, "FMC-GOV-01")["state"] == "attested" and _task(view, "FMC-GOV-01")["attestation"]["reference"] == "Board minutes 2026-11-03"
    assert _task(view, "FMC-GOV-02")["state"] == "needs_you"
    assert view["changes"][0]["summary"].startswith("1 attested: AIMS scope")

    system = _system(tmp_database, org_id, name="Loan scorer")
    _store(tmp_database, org_id, system, "fairness_test", _fairness(True), "2026-11-01T10:00:00")
    view = client.get(PLAN).json()
    inventory = _task(view, "FMC-INV-01")
    assert inventory["kind"] == "inventory" and inventory["progress"] == {"done": 0, "total": 1} and inventory["systems"][0]["name"] == "Loan scorer"
    gate_tasks = [t for t in view["tasks"] if t["kind"] == "gate"]
    assert gate_tasks and all(t["progress"]["total"] == 1 for t in gate_tasks)
    assert client.post(f"{PLAN}/tasks/control:FMC-INV-01/attest", json={"statement": "All systems are confirmed in a spreadsheet"}).status_code == 409

    view = client.patch(f"{PLAN}/tasks/control:FMC-INV-01", json={"owner": "K. Mehta"}).json()
    assert _task(view, "FMC-INV-01")["owner"] == "K. Mehta"
    assert client.patch(f"{PLAN}/tasks/control:FMC-NOPE", json={"owner": "x"}).status_code == 404


def test_with_a_provider_the_model_reads_the_description(tmp_database, monkeypatch):
    from api.routes import llm

    _, client = _org(tmp_database)
    _save_provider(client)

    async def read(conn, system, user, schema):
        assert "Mumbai" in user and set(schema["properties"]) >= {"jurisdictions", "maturity", "people"}
        return {"understood": "An Indian lender using credit models and agents.", "jurisdictions": ["india", "eu"], "sector": "financial",
                "value_chain": "both", "ai_types": ["predictive", "agents"], "decisions_about_people": "yes",
                "maturity": {"FMC-GOV-02": "established", "FMC-INC-01": "made-up"}, "people": {"dpo": "P. Nair", "nobody": "x"}}, {"model": conn.model, "latencyMs": 1, "usage": {}}

    monkeypatch.setattr(llm, "complete", read)
    disc = _answer(client, "about", ABOUT)["discovery"]
    assert disc["agent"] == "llm" and disc["transcript"][-1]["text"].startswith("An Indian lender")
    facts = {f["key"]: f for f in disc["facts"]}
    assert facts["jurisdictions"]["value"] == ["india", "eu"] and facts["value_chain"]["value"] == "both"
    assert "your AI provider" in facts["sector"]["basis"]
    assert disc["next"]["key"] == "maturity"
    assert [c["value"] for c in disc["next"]["controls"] if c["id"] == "FMC-GOV-02"] == ["established"]
    assert [c["value"] for c in disc["next"]["controls"] if c["id"] == "FMC-INC-01"] == [None]  # an invalid level is dropped
    assert not any(c["id"] == "FMC-AGT-01" for c in disc["map"]["outOfScope"])  # agents are in scope now


def test_a_passing_evaluation_does_a_system_task_and_an_attested_check_reads_attested(tmp_database):
    org_id, client = _org(tmp_database)
    for key, value in (("about", ABOUT), ("value_chain", "deployer"), ("maturity", {}), ("people", {}), ("frameworks", ["ISO42001"])):
        _answer(client, key, value)
    assert client.post(f"{PLAN}/generate").status_code == 200
    system = _system(tmp_database, org_id, name="Support chatbot")
    assert _task(client.get(PLAN).json(), "FMC-TST-01")["systems"][0]["detail"] == "not started"

    _store(tmp_database, org_id, system, "evaluation_run", {"evaluationId": "EV-TST-04", "status": "failed"}, "2026-11-01T10:00:00")
    assert _task(client.get(PLAN).json(), "FMC-TST-01")["systems"][0]["detail"] == "test failed"
    _store(tmp_database, org_id, system, "evaluation_run", {"evaluationId": "EV-TST-04", "status": "passed"}, "2026-11-01T11:00:00")
    _store(tmp_database, org_id, system, "human_oversight", {"statement": "Reviewers sign off each release"}, "2026-11-01T11:00:00")
    view = client.get(PLAN).json()
    testing = _task(view, "FMC-TST-01")
    assert testing["systems"][0]["detail"] == "tested" and testing["state"] == "proven"
    oversight = _task(view, "FMC-OVS-01")
    assert oversight["systems"][0]["detail"] == "attested" and oversight["state"] == "attested"  # as the clause map reads it

    # an insufficient rerun measured nothing: the earlier pass stands, as in the gate and the clause map
    _store(tmp_database, org_id, system, "evaluation_run", {"evaluationId": "EV-TST-04", "status": "insufficient"}, "2026-11-01T12:00:00")
    assert _task(client.get(PLAN).json(), "FMC-TST-01")["systems"][0]["detail"] == "tested"
    # another test of the control failing keeps the task open, as a failing check keeps the clause from proven
    _store(tmp_database, org_id, system, "evaluation_run", {"evaluationId": "EV-TST-01", "status": "failed"}, "2026-11-01T12:00:00")
    testing = _task(client.get(PLAN).json(), "FMC-TST-01")
    assert testing["systems"][0] == {**testing["systems"][0], "done": False, "detail": "test failed"} and testing["state"] != "proven"


def test_a_failing_gate_check_leaves_its_task_open_and_org_work_reaches_the_clause_map(tmp_database):
    org_id, client = _org(tmp_database)
    for key, value in (("about", ABOUT), ("value_chain", "deployer"), ("maturity", {}), ("people", {}), ("frameworks", ["ISO42001"])):
        _answer(client, key, value)
    assert client.post(f"{PLAN}/generate").status_code == 200
    system = _system(tmp_database, org_id, name="Support chatbot")
    _store(tmp_database, org_id, system, "evaluation_run", {"evaluationId": "EV-FAI-05", "status": "failed"}, "2026-11-01T10:00:00")
    fairness = _task(client.get(PLAN).json(), "FMC-FAI-01")
    assert fairness["systems"][0]["detail"] == "fails" and not fairness["systems"][0]["done"] and fairness["state"] != "proven"

    iso = lambda: {c["control"]: c for fw in client.get(f"/api/v1/ai-governance/systems/{system}/clause-map").json()["frameworks"] if fw["key"] == "ISO42001" for c in fw["clauses"]}  # noqa: E731
    assert iso()["5.2"]["state"] == "open"
    client.post(f"{PLAN}/tasks/control:FMC-GOV-02/attest", json={"statement": "The board approved the AI policy on 3 Nov", "reference": "Minutes"})
    policy = iso()["5.2"]
    assert (policy["state"], policy["cell"]) == ("attested", "attested")
    assert policy["checks"][0]["check"] == "FMC-GOV-02" and policy["checks"][0]["label"] == "The board approved the AI policy on 3 Nov"
    # a done organisation workflow run reaches its control's clauses the same way
    from sqlalchemy import text

    assert iso()["9.2"]["state"] == "open"
    with tmp_database.begin() as conn:
        conn.execute(text("INSERT INTO workflow_runs (id, org_id, workflow_id, workflow_version, status, created_at, updated_at, finished_at) "
                          "VALUES ('run-audit', :org, 'internal_audit', '1', 'done', '2026-11-02', '2026-11-02', '2026-11-02')"), {"org": str(org_id)})
    assert iso()["9.2"]["state"] == "attested" and iso()["9.2"]["checks"][0]["label"] == "Internal audit support: completed"
    # a systemless run of a system-scope workflow counts for no system; a run on this system does
    with tmp_database.begin() as conn:
        conn.execute(text("INSERT INTO workflow_runs (id, org_id, workflow_id, workflow_version, status, created_at, updated_at, finished_at) "
                          "VALUES ('run-incident', :org, 'serious_incident_reporting', '1', 'done', '2026-11-02', '2026-11-02', '2026-11-02')"), {"org": str(org_id)})
    assert iso()["10.2"]["state"] == "open"
    with tmp_database.begin() as conn:
        conn.execute(text("UPDATE workflow_runs SET ai_system_id = :sys WHERE id = 'run-incident'"), {"sys": str(system)})
    assert iso()["10.2"]["state"] == "attested"
