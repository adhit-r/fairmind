"""A system's kind: stored at registration, read by policy facts, and used to say which evaluations fit and how each can run."""

import json
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.test_packs_routes import PACKS, _org, _system, no_rate_limit, tmp_database  # noqa: F401  (fixtures)
from api.routes import pack_catalogue
from src.application.services.system_kinds import APPLIES_TO, SYSTEM_KINDS, fit, kind_of

GOV = "/api/v1/ai-governance"


def test_every_catalogue_applies_to_maps_to_known_kinds():
    values = {ev.appliesTo for ev in pack_catalogue.EVALUATIONS.values()}
    assert values - set(APPLIES_TO) == set()
    assert all(kinds <= set(SYSTEM_KINDS) for kinds in APPLIES_TO.values())


def test_the_stored_kind_wins_and_an_openai_connection_means_an_llm_app():
    assert kind_of('{"asset_kind": "agent"}', "openai") == "agent"
    assert kind_of({}, "openai") == "llm_app"
    assert kind_of({"asset_kind": "something"}, "http") is None
    assert (fit("Decision systems", None), fit("Decision systems", "ml_model"), fit("Decision systems", "llm_app")) == ("unknown", "applies", "other")


def _workspace(client):
    return client.post(f"{GOV}/workspaces", json={"name": "Lending", "owner": "priya@acme.com"}).json()["id"]


def test_registration_stores_a_known_kind_and_the_patch_changes_it_on_the_record(tmp_database):
    org_id, client = _org(tmp_database)
    body = {"workspace_id": _workspace(client), "name": "Billing bot", "risk_tier": "low", "lifecycle_stage": "onboard"}
    assert client.post(f"{GOV}/systems", json={**body, "metadata": {"asset_kind": "chatbot"}}).status_code == 422
    made = client.post(f"{GOV}/systems", json={**body, "metadata": {"asset_kind": "llm_app"}})
    assert made.status_code == 200, made.text
    system = made.json()["id"]
    with Session(tmp_database) as db:
        assert json.loads(db.execute(text("SELECT metadata_json FROM governance_ai_systems WHERE id = :id"), {"id": system}).scalar())["asset_kind"] == "llm_app"

    assert client.patch(f"{GOV}/systems/{system}", json={"kind": "chatbot"}).status_code == 422
    done = client.patch(f"{GOV}/systems/{system}", json={"kind": "agent"})
    assert done.status_code == 200, done.text
    assert done.json()["kind"] == "agent" and done.json()["change"]["note"] == "Kind changed from llm_app to agent"
    assert client.patch(f"{GOV}/systems/{system}", json={"kind": "agent"}).json()["change"] is None


def test_policy_facts_read_the_kind_not_the_unwritten_column(tmp_database):
    from src.application.services.policy_service import PolicyService

    org_id, _ = _org(tmp_database)
    system = _system(tmp_database, org_id)
    with Session(tmp_database) as db:
        db.execute(text("UPDATE governance_ai_systems SET metadata_json = :m WHERE id = :id"), {"m": '{"asset_kind": "ml_model"}', "id": system})
        db.commit()
        assert PolicyService(db).system_facts(str(org_id), {"id": system})["system.system_type"] == "ml_model"
        drafted = json.loads(PolicyService(db).draft_context(str(org_id), "x"))["aiSystems"]
        assert [s["kind"] for s in drafted] == ["ml_model"] and "system_type" not in drafted[0]


def _ways(row):
    return {w["way"]: w["ready"] for w in row["ways"]}


def test_evaluations_for_a_system_say_whether_they_fit_and_which_ways_are_ready(tmp_database):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    q = {**client.params, "system": system}

    rows = {e["id"]: e for e in client.get(f"{PACKS}/evaluations", params=q).json()}
    assert rows["EV-SEC-01"]["fit"] == "unknown" and _ways(rows["EV-SEC-01"]) == {"calls_system": False}
    assert _ways(rows["EV-DAT-01"]) == {"files": True}
    assert _ways(rows["EV-SEC-06"]) == {"platform": False, "files": True}
    assert _ways(rows["EV-TST-03"]) == {"calls_system": False, "live_runs": False}
    assert "fit" not in client.get(f"{PACKS}/evaluations/EV-SEC-01").json()  # without ?system= nothing changes

    with Session(tmp_database) as db:  # a saved OpenAI-compatible connection and one live run this week
        db.execute(
            text("INSERT INTO governance_ai_system_targets (system_id, org_id, kind, url, fields_json, updated_at) "
                 "VALUES (:id, :org, 'openai', 'https://target.test/v1', '{}', '2026-11-01T00:00:00')"),
            {"id": system, "org": str(org_id)},
        )
        db.execute(
            text("INSERT INTO governance_agent_traces (id, org_id, system_id, trace_id, status, truncated, received_at, updated_at) "
                 "VALUES (:pk, :org, :id, 't1', 'ok', false, :now, :now)"),
            {"pk": str(uuid.uuid4()), "org": str(org_id), "id": system, "now": "9999-01-01T00:00:00+00:00"},
        )
        db.commit()

    one = client.get(f"{PACKS}/evaluations/EV-TST-03", params=q).json()
    assert one["fit"] == "applies" and _ways(one) == {"calls_system": True, "live_runs": True}
    spec = client.get(f"{PACKS}/evaluations/EV-DAT-01/engine", params=q).json()
    assert (spec["kind"], spec["fit"], _ways(spec)) == ("llm_app", "applies", {"files": True})
    assert client.get(f"{PACKS}/evaluations/EV-FAI-01", params=q).json()["fit"] == "other"

    other_org, _ = _org(tmp_database)
    foreign = {**client.params, "system": _system(tmp_database, other_org)}
    assert client.get(f"{PACKS}/evaluations", params=foreign).status_code == 404
    assert client.get(f"{PACKS}/evaluations/EV-DAT-01/engine", params=foreign).status_code == 404
