"""Tests for agentic pack routes, on a fresh PostgreSQL database with real organizations and members."""

import copy
import json
import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Boolean, create_engine, text
from sqlalchemy.orm import sessionmaker

import api.routes.ai_governance as ai_governance
from api.main import app
from api.routes import pack_catalogue
from config.auth import User as AuthUser, UserRole, auth_manager
from database.connection import Base, get_db
from database.governance_models import GovernanceApprovalWorkflow
from database.models import Organization, OrganizationMember, User
from middleware.security import RateLimitMiddleware
from tests import pg

PACKS = "/api/v1/packs"
FOUNDATION = "PK-FOUNDATION"
WORKFLOW = "ai_policy_review"  # in PK-FOUNDATION
MONITORING = "PK-MONITORING"
ASK_STEP = "ask"


@pytest.fixture(scope="module", autouse=True)
def no_rate_limit():
    """This module makes enough calls to exhaust the shared per-IP budget other test modules rely on."""

    async def _allow(self, client_ip, current_time):
        return False, self.requests_per_minute, current_time + self.window_size

    original = RateLimitMiddleware.check_rate_limit
    RateLimitMiddleware.check_rate_limit = _allow
    yield
    RateLimitMiddleware.check_rate_limit = original


@contextmanager
def _serving(engine):
    """Build every table from the models on engine and point the app at it."""
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    def override_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    # Tables already exist on this engine; stop _ensure_tables touching the dev database.
    saved_ready = ai_governance._tables_ready
    ai_governance._tables_ready = True
    app.dependency_overrides[get_db] = override_db
    yield engine
    app.dependency_overrides.clear()
    ai_governance._tables_ready = saved_ready
    engine.dispose()


@pytest.fixture(autouse=True)
def tmp_database():
    with _serving(pg.fresh_engine()) as engine:
        yield engine


@pytest.fixture
def pg_database():
    """A fresh schema on FAIRMIND_TEST_POSTGRES_URL, built from the models alone as a new install does."""
    database_url = os.getenv("FAIRMIND_TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL")
    schema = f"fairmind_packs_{uuid.uuid4().hex}"
    admin = create_engine(database_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    try:
        with _serving(create_engine(database_url, connect_args={"options": f"-csearch_path={schema}"})) as engine:
            yield engine
    finally:
        with admin.connect() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def _client(engine, org_id: uuid.UUID, role: str = "owner", token_role: UserRole = UserRole.ADMIN) -> TestClient:
    """A member of org_id with the given org role, signed in with a real access token."""
    user_id = uuid.uuid4()
    with engine.begin() as conn:
        conn.execute(User.__table__.insert().values(password_hash="", id=user_id, email=f"{user_id}@packs.test", username=str(user_id)))
        conn.execute(
            OrganizationMember.__table__.insert().values(
                id=uuid.uuid4(), org_id=org_id, user_id=user_id, role=role, status="active"
            )
        )
    token = auth_manager.create_access_token(
        AuthUser(
            id=str(user_id),
            email=f"{user_id}@packs.test",
            username=str(user_id),
            role=token_role,
            created_at=datetime.now(timezone.utc),
            permissions=["*"],
        )
    )
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    client.params = {"org_id": str(org_id)}
    return client


def _new_org(engine) -> uuid.UUID:
    org_id, owner_id = uuid.uuid4(), uuid.uuid4()
    with engine.begin() as conn:
        conn.execute(User.__table__.insert().values(password_hash="", id=owner_id, email=f"{owner_id}@packs.test", username=str(owner_id)))
        conn.execute(
            Organization.__table__.insert().values(id=org_id, name="Packs test org", slug=f"packs-{org_id}", owner_id=owner_id)
        )
    return org_id


def _org(engine, **kw):
    org_id = _new_org(engine)
    return org_id, _client(engine, org_id, **kw)


def _installed_org(engine):
    org_id, client = _org(engine)
    assert client.post(f"{PACKS}/{FOUNDATION}/install").status_code == 200
    return org_id, client


def _start(client, workflow=WORKFLOW, **body):
    response = client.post(f"{PACKS}/workflows/{workflow}/runs", json=body)
    assert response.status_code == 200, response.text
    return response.json()


def _submit(client, run, **body):
    body = {"summary": "Reviewed and recorded", **body}
    response = client.post(f"{PACKS}/runs/{run['id']}/steps/{run['currentStep']}/output", json=body)
    assert response.status_code == 200, response.text
    return response.json()


def _to_gate(client, workflow=WORKFLOW):
    run = _start(client, workflow)
    while run["waitingFor"] == "input":
        run = _submit(client, run)
    return run


def _decide(client, run, decision, notes=""):
    response = client.post(f"{PACKS}/runs/{run['id']}/decision", json={"decision": decision, "notes": notes})
    assert response.status_code == 200, response.text
    return response.json()


def _kinds(run):
    return [(e["kind"], e["stepId"]) for e in run["events"]]


def _approval_count(engine, run_id):
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT COUNT(*) FROM governance_approval_requests WHERE entity_type = 'workflow_run' AND entity_id = :id"),
            {"id": run_id},
        ).scalar()


def test_catalogue_counts(tmp_database):
    _, client = _org(tmp_database)
    body = client.get(f"{PACKS}/catalogue").json()
    assert body["counts"] == {"packs": 21, "patterns": 38, "workflows": 90, "evaluations": 109, "frameworks": 51, "requirements": 539}
    assert [p["id"] for p in body["pillars"]] == ["GOVERN", "EVALUATE", "SECURE", "COMPLY"]
    assert sum(p["packs"] for p in body["pillars"]) == 21
    packs = client.get(PACKS).json()
    assert len(packs) == 21 and FOUNDATION in {p["id"] for p in packs}


def test_catalogue_engine_status_matches_the_code():
    """'Engine exists' means runnable; rerun scripts/export_pack_catalogue.py when an engine is added."""
    from src.application.services.evaluation_results import RULES
    from src.application.services.eval_engines import REGISTRY

    catalogue = json.loads((Path(__file__).resolve().parents[1] / "src/api/routers/pack_catalogue_data/catalogue.json").read_text())
    exists = {e["id"] for e in catalogue["evaluations"] if e["engine"] == "Engine exists"}
    assert exists == set(REGISTRY) | set(RULES)


def test_install_and_uninstall_toggle(tmp_database):
    _, client = _org(tmp_database)
    assert client.post(f"{PACKS}/{FOUNDATION}/install").json()["installed"] is True
    assert {p["id"]: p["installed"] for p in client.get(PACKS).json()}[FOUNDATION] is True
    assert client.delete(f"{PACKS}/{FOUNDATION}/install").json()["installed"] is False
    assert {p["id"]: p["installed"] for p in client.get(PACKS).json()}[FOUNDATION] is False
    assert client.post(f"{PACKS}/nope/install").status_code == 404


def test_installed_pack_ids_missing_from_catalogue_are_ignored(tmp_database):
    org_id, client = _org(tmp_database)
    client.get(PACKS)  # creates the tables
    with tmp_database.begin() as conn:
        conn.execute(
            text("INSERT INTO pack_installs (id, org_id, pack_id, installed_by, created_at) VALUES (:id, :org, 'iso_42001', 'x', 'now')"),
            {"id": str(uuid.uuid4()), "org": str(org_id)},
        )
    assert all(not p["installed"] for p in client.get(PACKS).json())
    assert client.get(f"{PACKS}/journeys/ISO42001").status_code == 200


def test_bundle_install_installs_its_packs(tmp_database):
    _, client = _org(tmp_database)
    bundle = client.get(f"{PACKS}/bundles").json()[0]
    assert bundle["installedCount"] == 0
    done = client.post(f"{PACKS}/bundles/{bundle['id']}/install").json()
    assert done["installedCount"] == len(done["packs"]) == len(bundle["packs"]) and all(p["installed"] for p in done["packs"])
    assert {p["id"] for p in client.get(PACKS).json() if p["installed"]} == {p["id"] for p in bundle["packs"]}
    # Installed packs cover through their workflows; their evaluations test nothing until a result passes.
    covered_only = pack_catalogue.Coverage([p["id"] for p in bundle["packs"]], tested_by=[])
    assert all(t["coveredInstalled"] == covered_only.count(t["key"]) <= t["coveredAll"] for t in done["targets"])
    assert client.post(f"{PACKS}/bundles/nope/install").status_code == 404


def test_journey_requirement_moves_from_available_to_covered(tmp_database):
    _, client = _org(tmp_database)
    # A requirement that only PK-FOUNDATION's workflows cover.
    only = pack_catalogue.PACK_DONE[FOUNDATION] - set().union(*(d for p, d in pack_catalogue.PACK_DONE.items() if p != FOUNDATION))
    key = next(k for k in sorted(only) if k in pack_catalogue._C.pack_covers[FOUNDATION])
    framework = pack_catalogue.REQUIREMENTS[key].framework

    def status():
        journey = client.get(f"{PACKS}/journeys/{framework}").json()
        return journey, {r["key"]: r["status"] for g in journey["groups"] for r in g["requirements"]}[key]

    before, state = status()
    assert state == "available" and before["coveredInstalled"] == 0
    client.post(f"{PACKS}/{FOUNDATION}/install")
    after, state = status()
    assert state == "covered" and after["coveredInstalled"] > 0
    assert after["coveredAll"] == before["coveredAll"]
    assert [s["installed"] for s in after["steps"] if s["pack"] == FOUNDATION] == [True]
    assert FOUNDATION in {j["contributingPacks"][0] for j in client.get(f"{PACKS}/journeys").json() if j["key"] == framework}


def test_journeys_list_has_five_active_requirements_each(tmp_database):
    _, client = _org(tmp_database)
    journeys = client.get(f"{PACKS}/journeys").json()
    assert journeys and all(j["active"] >= 5 for j in journeys)
    assert [j["name"] for j in journeys] == sorted(j["name"] for j in journeys)
    assert all(j["type"] for j in journeys)
    owasp = client.get(f"{PACKS}/journeys/OWASPLLM").json()
    assert owasp["type"] == "Risk taxonomy"
    assert client.get(f"{PACKS}/journeys/nope").status_code == 404


def test_evaluations_filter_by_pillar_and_engine(tmp_database):
    _, client = _org(tmp_database)
    everything = client.get(f"{PACKS}/evaluations").json()
    assert len(everything) == 109
    secure = client.get(f"{PACKS}/evaluations", params={"pillar": "SECURE", "engine": "Engine exists"}).json()
    assert secure and all(e["pillar"] == "SECURE" and e["engine"] == "Engine exists" for e in secure)
    assert client.get(f"{PACKS}/evaluations", params={"engine": "Partial"}).json() == []
    drift = client.get(f"{PACKS}/evaluations", params={"q": "data drift"}).json()
    assert [e["id"] for e in drift] == ["EV-DAT-01"] and drift[0]["tests"] and drift[0]["installed"] is False
    assert client.get(f"{PACKS}/evaluations/EV-DAT-01").json()["pack"]["id"] == drift[0]["pack"]["id"]
    assert client.get(f"{PACKS}/evaluations/nope").status_code == 404


def test_library_and_workflow_detail(tmp_database):
    _, client = _org(tmp_database)
    library = client.get(f"{PACKS}/library/{FOUNDATION}").json()
    assert library["patterns"] and library["frameworks"]
    assert any(w["id"] == WORKFLOW for p in library["patterns"] for w in p["workflows"])
    assert client.get(f"{PACKS}/library/nope").status_code == 404
    detail = client.get(f"{PACKS}/workflows/{WORKFLOW}").json()
    assert detail["pack"]["id"] == FOUNDATION and detail["mappings"] and detail["steps"][0]["kind"] == "trigger"


def test_start_run_requires_install_and_known_workflow(tmp_database):
    _, client = _org(tmp_database)
    assert client.post(f"{PACKS}/workflows/{WORKFLOW}/runs", json={}).status_code == 409
    assert client.post(f"{PACKS}/workflows/nope/runs", json={}).status_code == 404


def test_run_starts_and_waits_on_the_first_step_that_needs_a_person(tmp_database):
    _, client = _installed_org(tmp_database)
    run = _start(client)
    assert (run["status"], run["currentStep"], run["waitingFor"]) == ("waiting", "collect", "input")
    assert _kinds(run) == [
        ("run.created", None),
        ("step.started", "trigger"),
        ("step.completed", "trigger"),
        ("step.started", "collect"),
    ]
    assert run["chainValid"] and run["events"][0]["prevHash"] == "0" * 64
    assert client.get(f"{PACKS}/workflows/{WORKFLOW}").json()["latestRun"]["id"] == run["id"]
    assert [r["id"] for r in client.get(f"{PACKS}/runs?status=waiting").json()] == [run["id"]]


def test_approval_workflow_is_active_matches_the_postgresql_boolean_contract():
    column = GovernanceApprovalWorkflow.__table__.c.is_active
    assert isinstance(column.type, Boolean) and column.default.arg is True
    migration = (Path(__file__).parents[1] / "migrations/008_governance_canonical.sql").read_text()
    assert "is_active BOOLEAN NOT NULL DEFAULT TRUE" in migration


def test_a_model_built_postgres_database_opens_the_approval_gate(pg_database):
    _, client = _installed_org(pg_database)
    run = _to_gate(client)
    assert (run["currentStep"], run["waitingFor"]) == (ASK_STEP, "approval")
    assert _approval_count(pg_database, run["id"]) == 1


def test_approved_run_acts_files_evidence_and_completes(tmp_database):
    _, client = _installed_org(tmp_database)
    run = _to_gate(client)
    assert (run["currentStep"], run["waitingFor"]) == (ASK_STEP, "approval")
    assert run["approval"]["status"] == "pending" and _approval_count(tmp_database, run["id"]) == 1
    assert run["events"][-2]["payload"]["summary"] == "Reviewed and recorded"

    run = _decide(client, run, "approve", "ok")
    assert (run["currentStep"], run["waitingFor"]) == ("record", "input")
    assert run["approval"] == {"status": "approved", "decisionNotes": "ok"}

    run = _submit(client, run)
    assert run["status"] == "done" and run["finishedAt"] and run["currentStep"] is None and run["chainValid"]
    sealed = run["events"][-2]
    assert (sealed["kind"], sealed["stepId"]) == ("step.completed", "file-evidence")
    assert sealed["payload"]["sealedHeadHash"] == run["events"][-3]["hash"]
    assert _kinds(run)[-1] == ("run.completed", None)


def test_reject_files_evidence_and_completes(tmp_database):
    _, client = _installed_org(tmp_database)
    run = _decide(client, _to_gate(client), "reject", "no")
    assert run["status"] == "done" and run["approval"]["status"] == "rejected"
    assert ("step.completed", "record") not in _kinds(run)


def test_changes_loop_through_revise_then_escalate_after_three_rounds(tmp_database):
    _, client = _installed_org(tmp_database)
    run = _to_gate(client)
    for _ in range(3):
        run = _decide(client, run, "request_changes", "tighten scope")
        assert (run["currentStep"], run["waitingFor"]) == ("revise", "input")
        run = _submit(client, run)
        assert (run["currentStep"], run["waitingFor"]) == (ASK_STEP, "approval")
    run = _decide(client, run, "request_changes", "still not right")
    assert run["events"][-4]["payload"]["escalated"]
    assert ("step.completed", "escalate") in _kinds(run)
    # The ledger says who was told; it never claims a message nobody sent.
    told = next(e["payload"] for e in run["events"] if (e["kind"], e["stepId"]) == ("step.completed", "escalate"))
    assert told["notificationSent"] == (told["recipients"] > 0)
    assert told["notificationSent"] or told["reason"]
    assert (run["currentStep"], run["waitingFor"]) == (ASK_STEP, "approval")
    assert _approval_count(tmp_database, run["id"]) == 5


def test_step_output_and_decision_rules(tmp_database):
    _, client = _installed_org(tmp_database)
    run = _start(client)
    url = f"{PACKS}/runs/{run['id']}"
    assert client.post(f"{url}/steps/check/output", json={"summary": "x"}).status_code == 409
    assert client.post(f"{url}/steps/nope/output", json={"summary": "x"}).status_code == 404
    assert client.post(f"{url}/steps/collect/output", json={"summary": ""}).status_code == 422
    assert client.post(f"{url}/decision", json={"decision": "approve"}).status_code == 409

    run = _to_gate(client)
    url = f"{PACKS}/runs/{run['id']}"
    assert client.post(f"{url}/steps/{ASK_STEP}/output", json={"summary": "x"}).status_code == 409
    _decide(client, run, "approve")
    assert client.post(f"{url}/decision", json={"decision": "approve"}).status_code == 409


def test_branching_step_needs_a_route(tmp_database):
    _, client = _org(tmp_database)
    client.post(f"{PACKS}/{MONITORING}/install")
    workflow = "agent_activity_monitoring"  # its suggest step branches to routine or exception
    run = _start(client, workflow)
    run = _submit(client, _submit(client, run))
    assert run["currentStep"] == "suggest"
    missing = client.post(f"{PACKS}/runs/{run['id']}/steps/suggest/output", json={"summary": "x"})
    assert missing.status_code == 422
    assert _submit(client, run, route="routine")["currentStep"] == "record"

    exception = _start(client, workflow)
    exception = _submit(client, _submit(client, _submit(client, exception)), route="exception")
    assert (exception["currentStep"], exception["waitingFor"]) == ("ask", "approval")


def test_decision_must_be_one_the_gate_offers(tmp_database):
    _, client = _installed_org(tmp_database)
    run = _to_gate(client, "ai_ethics_committee_review")  # a decide step: no rejected branch
    response = client.post(f"{PACKS}/runs/{run['id']}/decision", json={"decision": "reject"})
    assert response.status_code == 422
    assert _decide(client, run, "approve")["currentStep"] == "record"


def test_tampered_event_breaks_chain(tmp_database):
    _, client = _installed_org(tmp_database)
    run = _start(client)
    with tmp_database.begin() as conn:
        conn.execute(
            text("UPDATE workflow_run_events SET payload_json = :p WHERE run_id = :id AND seq = 1"),
            {"p": '{"x":1}', "id": run["id"]},
        )
    assert client.get(f"{PACKS}/runs/{run['id']}").json()["chainValid"] is False


def test_other_org_cannot_read_or_decide_run(tmp_database):
    _, client = _installed_org(tmp_database)
    run = _to_gate(client)
    _, other = _org(tmp_database)
    assert other.get(f"{PACKS}/runs/{run['id']}").status_code == 404
    assert other.post(f"{PACKS}/runs/{run['id']}/decision", json={"decision": "approve"}).status_code == 404
    assert other.post(f"{PACKS}/runs/{run['id']}/steps/collect/output", json={"summary": "x"}).status_code == 404
    assert other.get(f"{PACKS}/runs").json() == []


def test_foreign_system_id_is_404(tmp_database):
    _, client = _installed_org(tmp_database)
    response = client.post(f"{PACKS}/workflows/{WORKFLOW}/runs", json={"system_id": "not-in-this-org"})
    assert response.status_code == 404


def _raw():
    return copy.deepcopy(json.loads(pack_catalogue.DATA_FILE.read_text(encoding="utf-8")))


def test_loader_accepts_the_shipped_catalogue():
    assert len(pack_catalogue.load(_raw()).workflows) == 90


def test_loader_rejects_unknown_workflow_in_pattern():
    raw = _raw()
    raw["patterns"][0]["workflows"].append("missing")
    with pytest.raises(ValueError, match="unknown workflow"):
        pack_catalogue.load(raw)


def test_loader_rejects_unknown_next_step():
    raw = _raw()
    raw["workflows"][0]["steps"][0]["next"] = [{"to": "zzz", "label": None}]
    with pytest.raises(ValueError, match="unknown step"):
        pack_catalogue.load(raw)


def test_loader_rejects_unknown_requirement_and_orphans():
    raw = _raw()
    raw["workflows"][0]["mappings"][0]["key"] = "NOPE|1"
    with pytest.raises(ValueError, match="unknown requirement"):
        pack_catalogue.load(raw)
    raw = _raw()
    raw["packs"][0]["patterns"].pop()
    with pytest.raises(ValueError, match="is in no pack"):
        pack_catalogue.load(raw)


def test_requires_org_membership(tmp_database):
    org_id = _new_org(tmp_database)
    outsider = _client(tmp_database, _new_org(tmp_database))
    outsider.params = {"org_id": str(org_id)}
    assert outsider.get(PACKS).status_code == 404
    outsider.params = {}
    assert outsider.get(PACKS).status_code == 422
    assert TestClient(app).get(PACKS, params={"org_id": str(org_id)}).status_code in (401, 403)


def test_plain_member_can_read_but_not_change(tmp_database):
    org_id = _new_org(tmp_database)
    member = _client(tmp_database, org_id, role="member", token_role=UserRole.ANALYST)
    assert member.get(PACKS).status_code == 200
    assert member.post(f"{PACKS}/{FOUNDATION}/install").status_code == 403
    assert member.post(f"{PACKS}/bundles/BN-GENAI-COPILOT/install").status_code == 403
    _, owner = org_id, _client(tmp_database, org_id)
    owner.post(f"{PACKS}/{FOUNDATION}/install")
    run = _start(owner)
    assert member.post(f"{PACKS}/runs/{run['id']}/steps/collect/output", json={"summary": "x"}).status_code == 403


# --- builder ---------------------------------------------------------------


def _without_check(steps):
    """The policy review with its check step removed: collect goes straight to suggest."""
    steps = [s for s in steps if s["id"] != "check"]
    next(s for s in steps if s["id"] == "collect")["next"] = [{"to": "suggest", "label": None}]
    return steps


def test_published_version_drives_new_runs_and_old_runs_keep_theirs(tmp_database):
    _, client = _installed_org(tmp_database)
    url = f"{PACKS}/workflows/{WORKFLOW}"
    draft = client.post(f"{url}/draft").json()
    assert (draft["version"], draft["basedOn"], draft["problems"]) == (1, "2.3", [])
    assert client.post(f"{url}/draft").json()["version"] == 1  # one draft at a time

    saved = client.put(f"{url}/draft", json={"steps": _without_check(draft["steps"])})
    assert saved.status_code == 200 and saved.json()["problems"] == []
    detail = client.get(url).json()
    assert detail["version"] == "2.3" and detail["draft"]["version"] == 1  # a draft is not live
    old_run = _start(client)

    published = client.post(f"{url}/draft/publish").json()
    assert published["version"] == "org-1" and published["draft"] is None
    assert "check" not in [s["id"] for s in published["steps"]]
    assert [v["status"] for v in client.get(f"{url}/versions").json()] == ["published"]

    new_run = _start(client)
    assert new_run["version"] == "org-1"
    assert _submit(client, new_run)["currentStep"] == "suggest"
    assert _submit(client, old_run)["currentStep"] == "check"  # started on 2.3, stays on 2.3

    assert client.post(f"{url}/draft").json()["basedOn"] == "org-1"


def test_publish_refuses_a_draft_with_problems(tmp_database):
    _, client = _installed_org(tmp_database)
    url = f"{PACKS}/workflows/{WORKFLOW}"
    steps = client.post(f"{url}/draft").json()["steps"]
    steps = [s for s in steps if s["kind"] != "file"]
    for s in steps:
        s["next"] = [e for e in s["next"] if e["to"] != "file-evidence"]
    ask = next(s for s in steps if s["id"] == ASK_STEP)
    ask["next"] = [e for e in ask["next"] if not (e["label"] or "").startswith("approved")]
    steps.append({"id": "orphan", "kind": "check", "title": "Orphan check", "detail": "", "next": []})

    problems = client.put(f"{url}/draft", json={"steps": steps}).json()["problems"]
    assert "Keep a file evidence step so every run is sealed." in problems
    assert any("approves" in p for p in problems)
    assert "Orphan check cannot be reached from the start." in problems
    response = client.post(f"{url}/draft/publish")
    assert response.status_code == 422 and response.json()["detail"]["problems"] == problems
    assert client.get(url).json()["version"] == "2.3"


def test_draft_rules(tmp_database):
    org_id, client = _org(tmp_database)
    url = f"{PACKS}/workflows/{WORKFLOW}"
    assert client.post(f"{url}/draft").status_code == 409  # pack not installed
    client.post(f"{PACKS}/{FOUNDATION}/install")
    assert client.get(f"{url}/draft").status_code == 404
    client.post(f"{url}/draft")
    member = _client(tmp_database, org_id, role="member", token_role=UserRole.ANALYST)
    assert member.get(f"{url}/draft").status_code == 200
    assert member.post(f"{url}/draft/publish").status_code == 403
    _, other = _org(tmp_database)
    assert other.get(f"{url}/draft").status_code == 404
    assert client.put(f"{url}/draft", json={"steps": []}).status_code == 422
    assert client.delete(f"{url}/draft").status_code == 200
    assert client.get(f"{url}/draft").status_code == 404


def test_adding_a_framework_installs_its_packs_and_journeys_show_waiting_runs(tmp_database):
    _, client = _org(tmp_database)
    before = next(j for j in client.get(f"{PACKS}/journeys").json() if j["key"] == "ISO42001")
    assert before["workflows"] == [] and before["waiting"] == 0

    assert client.post(f"{PACKS}/journeys/ISO42001/install").status_code == 200
    installed = {p["id"] for p in client.get(PACKS).json() if p["installed"]}
    assert installed == set(before["contributingPacks"])

    run = _start(client)  # the AI policy review waits for its collect step
    after = next(j for j in client.get(f"{PACKS}/journeys").json() if j["key"] == "ISO42001")
    policy = next(w for w in after["workflows"] if w["id"] == WORKFLOW)
    assert policy["status"] == "waiting" and policy["stage"] and after["waiting"] == 1
    # Installed packs cover through their workflows; their evaluations count only once a result passes.
    assert after["coveredInstalled"] == pack_catalogue.Coverage(before["contributingPacks"], tested_by=[]).count("ISO42001")

    journey = client.get(f"{PACKS}/journeys/ISO42001").json()
    assert all(w["stage"] for g in journey["groups"] for r in g["requirements"] for w in r["workflows"])
    assert client.post(f"{PACKS}/journeys/NOPE/install").status_code == 404
    assert run["status"] == "waiting"


def test_a_plain_member_cannot_add_a_framework(tmp_database):
    org_id = _new_org(tmp_database)
    member = _client(tmp_database, org_id, role="member", token_role=UserRole.ANALYST)
    assert member.post(f"{PACKS}/journeys/ISO42001/install").status_code == 403
# --- evaluation results ----------------------------------------------------
# Runs are produced by the real fairness engine and stored the way its router stores them.


def _system(engine, org_id, name="Credit model"):
    from database.governance_models import GovernanceAISystem, GovernanceWorkspace

    workspace_id, system_id = str(uuid.uuid4()), str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(GovernanceWorkspace.__table__.insert().values(id=workspace_id, org_id=str(org_id), name="Workspace"))
        conn.execute(GovernanceAISystem.__table__.insert().values(id=system_id, workspace_id=workspace_id, org_id=str(org_id), name=name))
    return system_id


def _store(engine, org_id, system_id, evidence_type, content, at):
    from database.governance_models import GovernanceEvidence

    with engine.begin() as conn:
        conn.execute(
            GovernanceEvidence.__table__.insert().values(
                id=str(uuid.uuid4()), system_id=system_id, org_id=str(org_id), evidence_type=evidence_type,
                content_json=json.dumps(content), status="collected", created_at=at,
            )
        )


def _decisions(fair: bool, attribute="gender") -> bytes:
    rows = ["y_true,y_pred," + attribute]
    for i in range(400):
        group = "a" if i % 2 else "b"
        pred = (i // 2) % 2 if fair else int(group == "a")
        rows.append(f"{(i // 2) % 2},{pred},{group}")
    return "\n".join(rows).encode()


def _fairness(fair: bool, attribute="gender"):
    from src.application.services.fairness_run_service import run_fairness

    return run_fairness(_decisions(fair, attribute), outcome="y_true", prediction="y_pred", attributes=[attribute], favorable_label=1)


def _requirement(client, framework, key):
    journey = client.get(f"{PACKS}/journeys/{framework}").json()
    return next(r for g in journey["groups"] for r in g["requirements"] if r["key"] == key)


def test_a_passing_fairness_run_marks_its_requirements_tested(tmp_database):
    org_id, client = _org(tmp_database)
    key = "NISTRMF|MEASURE 2.11"  # tested by EV-FAI-01 and EV-FAI-02
    assert _requirement(client, "NISTRMF", key)["status"] == "available"
    assert client.get(f"{PACKS}/evaluations/EV-FAI-01").json()["results"]["status"] == "not_run"

    _store(tmp_database, org_id, _system(tmp_database, org_id), "fairness_test", _fairness(True), "2026-11-01T10:00:00")
    result = client.get(f"{PACKS}/evaluations/EV-FAI-01").json()["results"]
    assert result["status"] == "passed"
    assert result["systems"][0]["systemName"] == "Credit model" and result["systems"][0]["detail"].startswith("Impact ratio gender")
    requirement = _requirement(client, "NISTRMF", key)
    assert requirement["status"] == "tested"
    assert {e["id"]: e["result"] for e in requirement["evaluations"]}["EV-FAI-01"] == "passed"

    _, other = _org(tmp_database)
    assert other.get(f"{PACKS}/evaluations/EV-FAI-01").json()["results"]["status"] == "not_run"


def test_a_failing_system_fails_the_evaluation_and_the_latest_run_counts(tmp_database):
    org_id, client = _org(tmp_database)
    fair, unfair = _system(tmp_database, org_id, "Fair model"), _system(tmp_database, org_id, "Skewed model")
    _store(tmp_database, org_id, fair, "fairness_test", _fairness(True), "2026-11-01T10:00:00")
    _store(tmp_database, org_id, unfair, "fairness_test", _fairness(False), "2026-11-01T11:00:00")
    assert client.get(f"{PACKS}/evaluations/EV-FAI-01").json()["results"]["status"] == "failed"
    assert _requirement(client, "NISTRMF", "NISTRMF|MEASURE 2.11")["status"] == "available"

    _store(tmp_database, org_id, unfair, "fairness_test", _fairness(True), "2026-11-02T09:00:00")  # fixed and re-run
    assert client.get(f"{PACKS}/evaluations/EV-FAI-01").json()["results"]["status"] == "passed"


def test_india_bias_needs_an_india_attribute_and_drift_needs_a_baseline(tmp_database):
    from src.application.services.fairness_run_service import run_monitoring

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    _store(tmp_database, org_id, system, "fairness_test", _fairness(True, "gender"), "2026-11-01T10:00:00")
    assert client.get(f"{PACKS}/evaluations/EV-FAI-06").json()["results"]["status"] == "not_run"
    _store(tmp_database, org_id, system, "fairness_test", _fairness(True, "caste"), "2026-11-01T11:00:00")
    assert client.get(f"{PACKS}/evaluations/EV-FAI-06").json()["results"]["status"] == "passed"

    monitoring = run_monitoring(_decisions(True), prediction="y_pred", attributes=["gender"], favorable_label=1)
    _store(tmp_database, org_id, system, "monitoring", monitoring, "2026-11-01T12:00:00")
    drift = client.get(f"{PACKS}/evaluations/EV-FAI-07").json()["results"]
    assert drift["status"] == "insufficient" and drift["systems"][0]["detail"] == "No baseline run to compare against"
    assert client.get(f"{PACKS}/evaluations/EV-SEC-22").json()["results"]["status"] == "not_run"  # engine since Nov 2026, not run yet
    assert client.get(f"{PACKS}/evaluations/EV-TST-01").json()["results"]["status"] == "not_run"  # has an engine, not run yet


def test_deciding_on_your_own_proposal_is_recorded_not_blocked(tmp_database):
    org_id, author = _installed_org(tmp_database)
    run = _to_gate(author)
    submitted = [e["payload"]["submittedBy"] for e in run["events"] if e["kind"] == "step.completed" and "submittedBy" in e["payload"]]
    assert run["proposalBy"] == submitted[-1]

    decided = _decide(author, run, "approve")  # allowed: a one-person organisation must still be able to decide
    gate = next(e for e in reversed(decided["events"]) if e["kind"] == "gate.decided")
    assert gate["payload"]["selfReview"] is True

    reviewer = _client(tmp_database, org_id)
    other = _decide(reviewer, _to_gate(author), "approve")
    gate = next(e for e in reversed(other["events"]) if e["kind"] == "gate.decided")
    assert "selfReview" not in gate["payload"]


# --- the agent and the organisation's model -------------------------------------


def _agent(client, run):
    response = client.post(f"{PACKS}/runs/{run['id']}/steps/{run['currentStep']}/agent")
    assert response.status_code == 200, response.text
    return response.json()


def _completed(run, step_id):
    return next(e["payload"] for e in reversed(run["events"]) if e["kind"] == "step.completed" and e["stepId"] == step_id)


def _save_provider(client, **body):
    return client.put(f"{PACKS}/ai-provider", json={"provider": "anthropic", "apiKey": "sk-ant-test-key-wxyz", **body})


def test_without_a_provider_the_agent_does_steps_by_rules(tmp_database):
    org_id, client = _installed_org(tmp_database)
    system = _system(tmp_database, org_id)
    _store(tmp_database, org_id, system, "fairness_test", _fairness(False), "2026-11-01T10:00:00")
    run = _start(client, system_id=system)
    collected = _agent(client, run)
    payload = _completed(collected, "collect")
    assert (payload["mode"], payload["source"], payload["submittedBy"]) == ("rules", "agent", "agent")
    assert payload["requestedBy"] and "Evidence on file: 1 records (1 fairness_test)" in payload["summary"]
    assert "failed" in payload["summary"] and collected["currentStep"] != "collect"
    while collected["waitingFor"] == "input":
        collected = _agent(client, collected)
    assert collected["waitingFor"] == "approval" and collected["proposalBy"] == "agent"


def test_rules_send_a_run_with_gaps_down_the_exception_branch(tmp_database):
    org_id, client = _org(tmp_database)
    client.post(f"{PACKS}/{MONITORING}/install")
    run = _start(client, "agent_activity_monitoring")  # no system and no evidence: a gap
    while run["currentStep"] != "suggest":
        run = _agent(client, run)
    run = _agent(client, run)
    assert _completed(run, "suggest")["route"] == "exception" and run["currentStep"] == "ask"


def test_a_saved_provider_never_returns_its_key_and_keeps_it_when_left_blank(tmp_database):
    org_id, client = _org(tmp_database)
    providers = {p["id"] for p in client.get(f"{PACKS}/ai-providers").json()}
    assert {"anthropic", "openai", "azure_openai", "bedrock", "google", "sarvam", "ollama"} <= providers
    assert client.get(f"{PACKS}/ai-provider").json() == {"config": None}

    config = _save_provider(client).json()["config"]
    assert (config["provider"], config["model"], config["keyHint"], config["hasKey"]) == ("anthropic", "claude-opus-5-5", "...wxyz", True)
    assert "sk-ant-test-key-wxyz" not in json.dumps(config)
    with tmp_database.connect() as conn:
        stored = conn.execute(text("SELECT api_key_enc FROM org_ai_providers")).scalar()
    assert stored and "sk-ant-test-key-wxyz" not in stored

    kept = client.put(f"{PACKS}/ai-provider", json={"provider": "anthropic", "model": "claude-sonnet-5-5"}).json()["config"]
    assert (kept["model"], kept["keyHint"]) == ("claude-sonnet-5-5", "...wxyz")
    assert client.put(f"{PACKS}/ai-provider", json={"provider": "openai"}).status_code == 422  # a new provider needs its own key

    member = _client(tmp_database, org_id, role="member", token_role=UserRole.ANALYST)
    assert member.get(f"{PACKS}/ai-provider").json()["config"]["keyHint"] == "...wxyz"
    assert _save_provider(member).status_code == 403
    assert client.delete(f"{PACKS}/ai-provider").json() == {"config": None}


def test_endpoints_must_be_public_https(tmp_database):
    _, client = _org(tmp_database)
    for url in ("http://models.example.com/v1", "https://localhost:11434/v1", "https://127.0.0.1/v1", "https://169.254.169.254/v1"):
        response = client.put(f"{PACKS}/ai-provider", json={"provider": "ollama", "baseUrl": url, "model": "llama3"})
        assert response.status_code == 422, url
    assert client.put(f"{PACKS}/ai-provider", json={"provider": "bedrock", "apiKey": "k" * 12, "region": "nowhere"}).status_code == 422


def test_testing_a_provider_reports_the_result_and_records_it(tmp_database, monkeypatch):
    from api.routes import llm

    _, client = _org(tmp_database)
    _save_provider(client)

    async def models(conn):
        assert conn.api_key == "sk-ant-test-key-wxyz"  # the stored key, since the form left it blank
        return ["claude-opus-5-5", "claude-sonnet-5-5"]

    async def answer(conn, system, user, schema):
        return {"ok": True}, {"model": conn.model, "latencyMs": 1, "usage": {}}

    monkeypatch.setattr(llm, "list_models", models)
    monkeypatch.setattr(llm, "complete", answer)
    result = client.post(f"{PACKS}/ai-provider/test", json={"provider": "anthropic"}).json()
    assert result["ok"] and result["models"] == ["claude-opus-5-5", "claude-sonnet-5-5"]
    assert client.get(f"{PACKS}/ai-provider").json()["config"]["testedOk"] is True

    async def rejected(conn):
        raise llm.LLMError("Anthropic rejected the key")

    monkeypatch.setattr(llm, "list_models", rejected)
    result = client.post(f"{PACKS}/ai-provider/test", json={"provider": "anthropic"}).json()
    assert (result["ok"], result["message"]) == (False, "Anthropic rejected the key")
    assert client.get(f"{PACKS}/ai-provider").json()["config"]["testMessage"] == "Anthropic rejected the key"


def test_the_grok_cli_stands_in_for_the_saved_provider_where_it_is_enabled_and_is_never_saved(tmp_database, monkeypatch, tmp_path):
    from config.settings import settings
    from tests.grok_helpers import fake_grok, recorded, stream

    _, client = _org(tmp_database)
    monkeypatch.setattr(settings, "grok_cli_enabled", False)
    assert "grok_cli" not in {p["id"] for p in client.get(f"{PACKS}/ai-providers").json()}
    for path, call in ((f"{PACKS}/ai-provider", client.put), (f"{PACKS}/ai-provider/test", client.post)):
        response = call(path, json={"provider": "grok_cli"})
        assert (response.status_code, response.json()["detail"]) == (422, "The Grok CLI is not enabled on this server")
    _save_provider(client)
    with tmp_database.connect() as conn:
        saved = conn.execute(text("SELECT * FROM org_ai_providers")).mappings().one()

    agent = '{"summary": "Model output", "route": "", "confidence": "high"}'
    calls = fake_grok(monkeypatch, tmp_path, out=stream(agent))
    assert "grok_cli" in {p["id"] for p in client.get(f"{PACKS}/ai-providers").json()}
    config = client.get(f"{PACKS}/ai-provider").json()["config"]
    assert (config["provider"], config["providerName"], config["model"], config["enabled"], config["hasKey"]) == (
        "grok_cli", "Grok CLI (local)", "grok-4.7", True, False)
    for response in (client.put(f"{PACKS}/ai-provider", json={"provider": "grok_cli"}), client.delete(f"{PACKS}/ai-provider")):
        assert response.status_code == 409 and "saves nothing" in response.json()["detail"]
    client.post(f"{PACKS}/{MONITORING}/install")
    payload = _completed(_agent(client, _start(client, "agent_activity_monitoring")), "collect")
    assert (payload["mode"], payload["provider"], payload["model"], payload["summary"]) == ("llm", "grok_cli", "grok-4.7", "Model output")
    assert '"workflow"' in recorded(calls)[-1]["prompt"]

    fake_grok(monkeypatch, tmp_path)
    result = client.post(f"{PACKS}/ai-provider/test", json={"provider": "grok_cli"}).json()
    assert (result["ok"], result["message"], result["models"]) == (True, "grok-4.7 answered", ["grok-4.7", "grok-4.6", "grok-4.5"])
    with tmp_database.connect() as conn:
        assert conn.execute(text("SELECT * FROM org_ai_providers")).mappings().one() == saved  # the saved key and test are untouched

    monkeypatch.setattr(settings, "grok_cli_enabled", False)
    assert client.get(f"{PACKS}/ai-provider").json()["config"]["provider"] == "anthropic"


def test_a_saved_grok_cli_row_reads_as_off_where_the_cli_is_not_enabled(tmp_database, monkeypatch):
    from config.settings import settings

    org_id, client = _installed_org(tmp_database)
    monkeypatch.setattr(settings, "grok_cli_enabled", False)
    with tmp_database.begin() as conn:  # as an earlier build saved it
        conn.execute(
            text("INSERT INTO org_ai_providers (org_id, provider, model, fields_json, enabled, updated_by, updated_at) "
                 "VALUES (:org, 'grok_cli', 'grok-4.7', '{}', TRUE, 'u', '2026-11-07T10:00:00')"),
            {"org": org_id},
        )
    config = client.get(f"{PACKS}/ai-provider").json()["config"]
    assert (config["provider"], config["enabled"]) == ("grok_cli", False)
    assert _completed(_agent(client, _start(client)), "collect")["mode"] == "rules"


def test_with_a_provider_the_model_does_the_step_and_the_trace_is_on_the_ledger(tmp_database, monkeypatch):
    from api.routes import llm

    org_id, client = _org(tmp_database)
    client.post(f"{PACKS}/{MONITORING}/install")
    _save_provider(client)
    seen = {}

    async def answer(conn, system, user, schema):
        seen["facts"] = json.loads(user)
        route = "routine" if seen["facts"]["step"]["branches"] else ""
        return {"summary": "Model output", "route": route, "confidence": "high"}, {
            "model": conn.model, "latencyMs": 12, "usage": {"inputTokens": 10, "outputTokens": 5}}

    monkeypatch.setattr(llm, "complete", answer)
    run = _start(client, "agent_activity_monitoring")
    run = _agent(client, run)
    payload = _completed(run, "collect")
    assert (payload["mode"], payload["model"], payload["confidence"], payload["summary"]) == ("llm", "claude-opus-5-5", "high", "Model output")
    assert len(payload["promptHash"]) == 64 and seen["facts"]["workflow"]["name"]
    while run["currentStep"] != "suggest":
        run = _agent(client, run)
    run = _agent(client, run)
    assert _completed(run, "suggest")["route"] == "routine" and run["currentStep"] == "record"
    assert run["chainValid"]

    async def failing(conn, system, user, schema):
        raise llm.LLMError("Anthropic is rate limiting this key")

    monkeypatch.setattr(llm, "complete", failing)
    waiting = _start(client, "agent_activity_monitoring")
    response = client.post(f"{PACKS}/runs/{waiting['id']}/steps/collect/agent")
    assert response.status_code == 502 and response.json()["detail"] == "Anthropic is rate limiting this key"
    assert client.get(f"{PACKS}/runs/{waiting['id']}").json()["currentStep"] == "collect"

    client.put(f"{PACKS}/ai-provider", json={"provider": "anthropic", "enabled": False})
    assert _completed(_agent(client, waiting), "collect")["mode"] == "rules"  # switched off: rules again


def test_the_agent_only_does_a_step_that_is_waiting_for_output(tmp_database):
    _, client = _installed_org(tmp_database)
    gate = _to_gate(client)
    assert client.post(f"{PACKS}/runs/{gate['id']}/steps/{gate['currentStep']}/agent").status_code == 409


def test_ask_answers_from_the_estate_and_cites_only_this_orgs_systems(tmp_database, monkeypatch):
    from api.routes import llm

    org_id, client = _org(tmp_database)
    assert client.post(f"{PACKS}/ask", json={"question": "Which systems are blocked?"}).status_code == 409  # no provider yet
    system = _system(tmp_database, org_id)
    _store(tmp_database, org_id, system, "fairness_test", _fairness(False), "2026-11-01T10:00:00")
    _save_provider(client)
    seen = {}

    async def answer(conn, system_prompt, user, schema):
        seen["prompt"] = json.loads(user)
        return {"answer": "Credit model fails fairness.", "systems": [{"id": system, "reason": "Fairness fails"}, {"id": "not-ours", "reason": "x"}]}, {
            "model": conn.model, "latencyMs": 5, "usage": {}}

    monkeypatch.setattr(llm, "complete", answer)
    body = client.post(f"{PACKS}/ask", json={"question": "Which systems are blocked?"}).json()
    assert body["answer"] == "Credit model fails fairness."
    assert body["systems"] == [{"id": system, "name": "Credit model", "reason": "Fairness fails"}]
    assert body["systemsRead"] == 1 and seen["prompt"]["question"] == "Which systems are blocked?"
    gate = seen["prompt"]["facts"]["systems"][0]
    assert gate["verdict"] and any(c["label"] for c in gate["checks"])

    async def failing(conn, system_prompt, user, schema):
        raise llm.LLMError("Anthropic is rate limiting this key")

    monkeypatch.setattr(llm, "complete", failing)
    failed = client.post(f"{PACKS}/ask", json={"question": "Anything?"})
    assert failed.status_code == 502 and failed.json()["detail"] == "Anthropic is rate limiting this key"
    assert client.post(f"{PACKS}/ask", json={"question": ""}).status_code == 422
