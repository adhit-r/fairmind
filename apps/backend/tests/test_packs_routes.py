"""Tests for agentic pack routes. Runs against a throwaway sqlite file, never the dev database."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import api.routes.ai_governance as ai_governance
from api.main import app
from api.routes import pack_catalogue
from config.auth import UserRole
from middleware.security import RateLimitMiddleware
from database.connection import Base, db_manager
from tests.auth_helpers import auth_headers

PACKS = "/api/v1/packs"
WORKFLOW = "ai_policy_review"
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


@pytest.fixture(scope="module", autouse=True)
def tmp_database():
    # The app and its engine are built by conftest before this module is imported,
    # so setting DATABASE_URL here would be too late: swap the engine instead.
    import database.governance_models  # noqa: F401

    path = Path(tempfile.mkdtemp()) / "packs.db"
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    saved = (db_manager.engine, db_manager.SessionLocal, ai_governance._tables_ready)
    db_manager.engine = engine
    db_manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    ai_governance._tables_ready = True
    yield engine
    db_manager.engine, db_manager.SessionLocal, ai_governance._tables_ready = saved
    engine.dispose()


def _org():
    """A fresh org with an admin client."""
    import uuid

    org_id = str(uuid.uuid4())
    return org_id, TestClient(app, headers=auth_headers(org_id))


def _installed_org():
    org_id, client = _org()
    assert client.post(f"{PACKS}/iso_42001/install").status_code == 200
    return org_id, client


def _start(client, **body):
    response = client.post(f"{PACKS}/workflows/{WORKFLOW}/runs", json=body)
    assert response.status_code == 200, response.text
    return response.json()


def _gate(client, run_id):
    client.post(f"{PACKS}/runs/{run_id}/events", json={"kind": "step.started", "step_id": "trigger"})
    response = client.post(f"{PACKS}/runs/{run_id}/events", json={"kind": "gate.opened", "step_id": ASK_STEP})
    assert response.status_code == 200, response.text
    return response.json()


def _approval_count(engine, run_id):
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT COUNT(*) FROM governance_approval_requests WHERE entity_type = 'workflow_run' AND entity_id = :id"),
            {"id": run_id},
        ).scalar()


def test_catalogue_lists_both_packs():
    _, client = _org()
    packs = {p["id"]: p for p in client.get(PACKS).json()}
    assert set(packs) == {"iso_42001", "security_controls"}
    assert packs["iso_42001"]["hasJourney"] and not packs["security_controls"]["hasJourney"]
    assert packs["security_controls"]["workflowIds"] == ["access_control_review"]


def test_install_and_uninstall_toggle():
    _, client = _org()
    assert client.post(f"{PACKS}/iso_42001/install").json()["installed"] is True
    assert {p["id"]: p["installed"] for p in client.get(PACKS).json()}["iso_42001"] is True
    assert client.delete(f"{PACKS}/iso_42001/install").json()["installed"] is False
    assert {p["id"]: p["installed"] for p in client.get(PACKS).json()}["iso_42001"] is False
    assert client.post(f"{PACKS}/nope/install").status_code == 404


def test_journey_statuses_null_before_runs():
    _, client = _org()
    journey = client.get(f"{PACKS}/journeys/iso_42001").json()
    assert [c["number"] for c in journey["clauses"]] == ["4", "5", "6", "7", "8", "9", "10"]
    workflows = [w for c in journey["clauses"] for w in c["workflows"]]
    assert len(workflows) == 3 and all(w["latestRun"] is None for w in workflows)


def test_start_run_requires_install_and_known_workflow():
    _, client = _org()
    assert client.post(f"{PACKS}/workflows/{WORKFLOW}/runs", json={}).status_code == 409
    assert client.post(f"{PACKS}/workflows/nope/runs", json={}).status_code == 404


def test_run_creation_chain_valid():
    _, client = _installed_org()
    run = _start(client)
    assert run["status"] == "queued" and run["chainValid"] is True
    assert [e["kind"] for e in run["events"]] == ["run.created"]
    assert run["events"][0]["prevHash"] == "0" * 64
    assert client.get(f"{PACKS}/workflows/{WORKFLOW}").json()["latestRun"]["id"] == run["id"]
    assert [r["id"] for r in client.get(f"{PACKS}/runs?status=queued").json()] == [run["id"]]


def test_non_admin_cannot_append_events():
    org_id, client = _installed_org()
    run = _start(client)
    analyst = TestClient(app, headers=auth_headers(org_id, UserRole.ANALYST))
    response = analyst.post(f"{PACKS}/runs/{run['id']}/events", json={"kind": "step.started", "step_id": "trigger"})
    assert response.status_code == 403


def test_event_validation():
    _, client = _installed_org()
    run = _start(client)
    url = f"{PACKS}/runs/{run['id']}/events"
    assert client.post(url, json={"kind": "gate.decided", "step_id": ASK_STEP}).status_code == 422
    assert client.post(url, json={"kind": "step.started", "step_id": "nope"}).status_code == 422
    assert client.post(url, json={"kind": "gate.opened", "step_id": "trigger"}).status_code == 422
    done = client.post(url, json={"kind": "run.completed"}).json()
    assert done["status"] == "done" and done["finishedAt"]
    assert client.post(url, json={"kind": "step.started", "step_id": "trigger"}).status_code == 409


def test_gate_opens_one_approval_and_decision_resumes(tmp_database):
    _, client = _installed_org()
    run = _gate(client, _start(client)["id"])
    assert run["status"] == "waiting" and run["currentStep"] == ASK_STEP and run["chainValid"]
    assert run["approval"]["status"] == "pending"
    assert _approval_count(tmp_database, run["id"]) == 1
    # a waiting run cannot be resumed by appending events
    resume = client.post(f"{PACKS}/runs/{run['id']}/events", json={"kind": "step.started", "step_id": "record"})
    assert resume.status_code == 409

    decided = client.post(f"{PACKS}/runs/{run['id']}/decision", json={"decision": "approve", "notes": "ok"}).json()
    assert decided["status"] == "running" and decided["chainValid"]
    assert decided["events"][-1]["kind"] == "gate.decided"
    assert decided["approval"] == {"status": "approved", "decisionNotes": "ok"}
    assert _approval_count(tmp_database, run["id"]) == 1
    again = client.post(f"{PACKS}/runs/{run['id']}/decision", json={"decision": "approve"})
    assert again.status_code == 409


def test_reject_blocks_run():
    _, client = _installed_org()
    run = _gate(client, _start(client)["id"])
    decided = client.post(f"{PACKS}/runs/{run['id']}/decision", json={"decision": "reject", "notes": "no"}).json()
    assert decided["status"] == "blocked" and decided["chainValid"]
    assert decided["approval"]["status"] == "rejected"


def test_decision_requires_waiting_run():
    _, client = _installed_org()
    run = _start(client)
    assert client.post(f"{PACKS}/runs/{run['id']}/decision", json={"decision": "approve"}).status_code == 409


def test_tampered_event_breaks_chain(tmp_database):
    _, client = _installed_org()
    run = _gate(client, _start(client)["id"])
    with tmp_database.begin() as conn:
        conn.execute(
            text("UPDATE workflow_run_events SET payload_json = :p WHERE run_id = :id AND seq = 1"),
            {"p": '{"x":1}', "id": run["id"]},
        )
    assert client.get(f"{PACKS}/runs/{run['id']}").json()["chainValid"] is False


def test_other_org_cannot_read_or_decide_run():
    _, client = _installed_org()
    run = _gate(client, _start(client)["id"])
    _, other = _org()
    assert other.get(f"{PACKS}/runs/{run['id']}").status_code == 404
    assert other.post(f"{PACKS}/runs/{run['id']}/decision", json={"decision": "approve"}).status_code == 404
    assert other.get(f"{PACKS}/runs").json() == []


def test_foreign_system_id_is_404():
    _, client = _installed_org()
    response = client.post(f"{PACKS}/workflows/{WORKFLOW}/runs", json={"system_id": "not-in-this-org"})
    assert response.status_code == 404


def test_loader_rejects_unknown_workflow_in_journey():
    iso, security = pack_catalogue._PACKS
    packs = [{**iso, "journey": [{"number": "5", "name": "Leadership", "workflow_ids": ["missing"]}]}, security]
    with pytest.raises(ValueError, match="unknown workflow"):
        pack_catalogue.load(packs, pack_catalogue._WORKFLOWS)


def test_loader_rejects_unknown_next_step():
    bad = {**pack_catalogue._WORKFLOWS[0], "steps": [{"id": "a", "kind": "trigger", "title": "t", "detail": "d", "next": [{"to": "zzz"}]}]}
    with pytest.raises(ValueError, match="unknown step"):
        pack_catalogue.load(pack_catalogue._PACKS, [bad])
