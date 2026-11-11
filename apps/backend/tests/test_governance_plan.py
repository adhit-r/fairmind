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
        assert t["state"] in ("todo", "needs_you", "agent", "review", "proven")
    assert not any(t["controlId"] in ("FMC-AGT-01", "FMC-AGT-02", "FMC-SLF-01") for t in view["tasks"])
    assert [t["priority"] for t in view["tasks"]] == list(range(1, len(view["tasks"]) + 1))
    scope = _task(view, "FMC-GOV-01")
    assert scope["kind"] == "org" and scope["state"] == "needs_you" and scope["ownerSuggested"] == "A. Rao" and scope["title"].startswith("Establish")
    policy = _task(view, "FMC-GOV-02")
    assert policy["state"] == "todo" and policy["blockedBy"] == ["control:FMC-GOV-01"] and policy["title"].startswith("Formalise")
    assert view["changes"][0]["summary"] == f"Plan created with {len(view['tasks'])} tasks"

    assert client.post(f"{PLAN}/tasks/control:FMC-GOV-01/attest", json={"statement": "short"}).status_code == 422
    view = client.post(f"{PLAN}/tasks/control:FMC-GOV-01/attest", json={"statement": "Board approved the AI governance scope on 3 Nov", "reference": "Board minutes 2026-11-03"}).json()
    assert _task(view, "FMC-GOV-01")["state"] == "proven" and _task(view, "FMC-GOV-01")["attestation"]["reference"] == "Board minutes 2026-11-03"
    assert _task(view, "FMC-GOV-02")["state"] == "needs_you"
    assert view["changes"][0]["summary"].startswith("1 proven: AIMS scope")

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
