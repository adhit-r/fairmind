"""Evaluations that run on records FairMind already holds (source=fairmind): the saved connection's system prompt for
EV-DEV-01 and EV-DEV-02, and FairMind's own agent's actions and filed evidence for EV-SLF-02 and EV-SLF-03."""

import json
import uuid

from sqlalchemy import text

from tests.test_packs_routes import PACKS, _org, _system, no_rate_limit, tmp_database  # noqa: F401  (fixtures)
from tests.test_eval_engines_ops import FAKE_AWS, GOOD_PROMPT


def _ways(row):
    return {w["way"]: w["ready"] for w in row["ways"]}


def _target(engine, org_id, system_id, prompt):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO governance_ai_system_targets (system_id, org_id, kind, url, fields_json, updated_at) "
                 "VALUES (:id, :org, 'openai', 'https://target.test/v1', :f, '2026-11-01T00:00:00')"),
            {"id": system_id, "org": str(org_id), "f": json.dumps({"systemPrompt": prompt, "model": "m"})},
        )


def _event(engine, org_id, system_id, action, status="done", check="fairness"):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO autopilot_events (id, org_id, system_id, check_key, action, status, detail, actor, created_at) "
                 "VALUES (:id, :org, :s, :c, :a, :st, '', 'autopilot', :now)"),
            {"id": str(uuid.uuid4()), "org": str(org_id), "s": system_id, "c": check, "a": action, "st": status, "now": "2026-11-20T00:00:00"},
        )


def _evidence(engine, org_id, system_id, content, by, run_hash=None):
    run_id = None
    with engine.begin() as conn:
        if run_hash:  # the integrity hash FairMind stored when it collected the evidence
            from database.governance_models import GovernanceEvidenceRun

            workspace = conn.execute(text("SELECT workspace_id FROM governance_ai_systems WHERE id = :s"), {"s": system_id}).scalar()
            run_id = str(uuid.uuid4())
            conn.execute(GovernanceEvidenceRun.__table__.insert().values(
                id=run_id, org_id=str(org_id), system_id=system_id, workspace_id=workspace, source_type="autopilot", source_identifier=run_id,
                run_id=run_id, content_hash=run_hash, passport_id=run_id, schema_version="1", capability_state="collected", assurance_source="autopilot"))
        conn.execute(
            text("INSERT INTO governance_evidence (id, system_id, org_id, evidence_type, content_json, confidence, status, uploaded_by, metadata_json, source_run_id, created_at) "
                 "VALUES (:id, :s, :org, 'monitoring', :c, 1.0, 'collected', :by, '{}', :run, '2026-11-20T00:00:00')"),
            {"id": str(uuid.uuid4()), "s": system_id, "org": str(org_id), "c": json.dumps(content), "by": by, "run": run_id},
        )


def _run(client, ev, system, params=None):
    return client.post(f"{PACKS}/evaluations/{ev}/runs", data={"system_id": system, "source": "fairmind", "params": json.dumps(params or {})})


def test_fairmind_data_is_a_way_ready_only_when_the_system_has_it(tmp_database):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    q = {**client.params, "system": system}

    def ways(ev):
        return _ways(client.get(f"{PACKS}/evaluations/{ev}/engine", params=q).json())

    assert ways("EV-DEV-01") == {"platform": False, "fairmind_data": False, "files": True}
    assert ways("EV-SLF-02")["fairmind_data"] is False and ways("EV-SLF-03")["fairmind_data"] is False
    assert ways("EV-TRN-01") == {"calls_system": False, "files": True}  # the live disclosure check beside the inventory upload

    other_org, _ = _org(tmp_database)
    foreign = _system(tmp_database, other_org)
    _event(tmp_database, other_org, foreign, "fairness_run")  # another organisation's agent actions never count here
    _event(tmp_database, org_id, system, "run", "skipped", check="autopilot")  # a whole run skipped is not an action
    assert ways("EV-SLF-02")["fairmind_data"] is False

    _target(tmp_database, org_id, system, GOOD_PROMPT)
    _event(tmp_database, org_id, system, "fairness_run")
    _evidence(tmp_database, org_id, system, {"model": "m"}, "agent:autopilot")
    assert ways("EV-DEV-01")["fairmind_data"] and ways("EV-DEV-02")["fairmind_data"]
    assert ways("EV-SLF-02")["fairmind_data"] and ways("EV-SLF-03")["fairmind_data"]
    assert ways("EV-TRN-01")["calls_system"] is True


def test_the_system_prompt_on_the_connection_runs_dev_01_and_dev_02_with_the_secret_masked(tmp_database):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    assert _run(client, "EV-DEV-01", system).status_code == 409  # no connection yet: upload instead
    assert _run(client, "EV-DAT-01", system).status_code == 422  # FairMind holds nothing for this evaluation
    _target(tmp_database, org_id, system, GOOD_PROMPT + f"\nAWS key {FAKE_AWS}")

    clauses = _run(client, "EV-DEV-01", system)
    assert clauses.status_code == 200, clauses.text
    # no judge set: a full set of keywords is insufficient for EV-DEV-01 (the judge decides each clause)
    assert clauses.json()["status"] == "insufficient" and clauses.json()["source"] == "fairmind"
    assert clauses.json()["files"] == {"system_prompt": "System prompt on the saved connection"}

    secrets = _run(client, "EV-DEV-02", system).json()
    assert secrets["status"] == "failed" and secrets["metrics"]["secrets"] == 1
    assert secrets["provenance"] == {"class": "computed_from_upload", "modelJudged": False}
    with tmp_database.connect() as conn:
        stored = conn.execute(text("SELECT content_json, metadata_json FROM governance_evidence WHERE id = :id"), {"id": secrets["id"]}).fetchone()
    assert FAKE_AWS not in stored[0] and FAKE_AWS not in json.dumps(secrets)  # shown masked, never in full
    assert json.loads(stored[1])["provenance_class"] == "computed_from_upload"


def test_slf_02_reads_the_agents_actions_on_the_system(tmp_database):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    _event(tmp_database, org_id, system, "fairness_run")
    _event(tmp_database, org_id, system, "evaluation_run", check="behaviour")
    _event(tmp_database, org_id, system, "monitoring_snapshot", "failed", check="monitoring")
    _event(tmp_database, org_id, system, "run", "skipped", check="autopilot")
    other_org, _ = _org(tmp_database)
    _event(tmp_database, other_org, _system(tmp_database, other_org), "delete_system")

    ok = _run(client, "EV-SLF-02", system, {"allowed_tools": "fairness_run,evaluation_run,monitoring_snapshot"}).json()
    assert ok["status"] == "passed" and ok["metrics"]["actions"] == 3
    out = _run(client, "EV-SLF-02", system, {"allowed_tools": "fairness_run,evaluation_run"}).json()
    assert out["status"] == "failed" and out["metrics"]["attemptsOutsideScope"] == 1 and out["metrics"]["executedOutsideScope"] == 0
    assert [r["outcome"] for r in out["detail"]] == ["failed"]  # the step errored; no guardrail blocked it


def test_slf_03_reads_the_evidence_the_agent_filed_and_only_a_stored_hash_counts(tmp_database):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    _evidence(tmp_database, org_id, system, {"model": "m", "prompt": "p", "tool_calls": []}, "agent:autopilot")
    _evidence(tmp_database, org_id, system, {"prompt": "p"}, "agent:autopilot")
    _evidence(tmp_database, org_id, system, {}, "person-1")  # a person's upload is not the agent's

    out = _run(client, "EV-SLF-03", system).json()
    assert out["status"] == "failed" and out["metrics"]["items"] == 2 and out["metrics"]["complete"] == 0  # no integrity hash stored
    some = _run(client, "EV-SLF-03", system, {"required_fields": "prompt"}).json()
    assert some["status"] == "passed" and some["metrics"]["items"] == 2


def test_slf_03_ignores_a_hash_written_inside_the_evidence_body(tmp_database):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    _evidence(tmp_database, org_id, system, {"prompt": "p", "content_hash": "x"}, "agent:autopilot")  # self-declared, no stored run
    _evidence(tmp_database, org_id, system, {"prompt": "p"}, "agent:autopilot", run_hash="a" * 64)

    out = _run(client, "EV-SLF-03", system, {"required_fields": "content_hash"}).json()
    assert out["status"] == "failed" and out["metrics"]["items"] == 2 and out["metrics"]["complete"] == 1
    assert out["detail"][0]["missing"] == ["content_hash"]  # the self-declared hash did not count
