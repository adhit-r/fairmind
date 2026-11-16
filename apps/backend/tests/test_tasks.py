"""Tasks: editors assign work to members or to the release autopilot; assignees move their own; agents report back."""

import pytest
from sqlalchemy import text

import api.routes.packs  # noqa: F401  (the routers import each other through api.routes)
from tests import pg
from tests.test_packs_routes import _client, _new_org, _serving

AIG = "/api/v1/ai-governance"


@pytest.fixture
def org():
    with _serving(pg.fresh_engine()) as engine:
        org_id = _new_org(engine)
        clients = {role: _client(engine, org_id, role=role) for role in ("owner", "editor", "viewer")}
        with engine.connect() as conn:
            ids = dict(conn.execute(text("SELECT role, CAST(user_id AS TEXT) FROM org_members WHERE org_id = :o"), {"o": org_id}).fetchall())
        owner = clients["owner"]
        ws = owner.post(f"{AIG}/workspaces", json={"name": "Models", "owner": "owner"}).json()
        system = owner.post(f"{AIG}/systems", json={"workspace_id": ws["id"], "name": "tinyLlama", "owner": "owner", "risk_tier": "medium", "lifecycle_stage": "onboard"}).json()
        yield clients, ids, system["id"], engine


def test_an_editor_assigns_a_member_who_moves_only_their_own_task(org):
    clients, ids, system_id, _ = org
    created = clients["editor"].post("/api/v1/tasks", json={
        "title": "Attach a data quality report", "assignee_user_id": ids["viewer"], "due_date": "2026-11-24", "priority": "high",
        "subject_type": "requirement", "subject_id": "ISO42001|A.7.4", "subject_label": "ISO 42001 A.7.4 Quality of data", "system_id": system_id,
    })
    assert created.status_code == 201, created.text
    task = created.json()
    assert (task["number"], task["status"], task["assigneeUserId"]) == (1, "open", ids["viewer"])

    viewer = clients["viewer"]
    assert [t["id"] for t in viewer.get("/api/v1/tasks", params={"mine": "true"}).json()["tasks"]] == [task["id"]]
    assert viewer.patch(f"/api/v1/tasks/{task['id']}", json={"title": "Something else"}).status_code == 403
    assert viewer.post("/api/v1/tasks", json={"title": "Mine"}).status_code == 403
    assert viewer.patch(f"/api/v1/tasks/{task['id']}", json={"status": "done"}).json()["status"] == "done"
    assert viewer.post(f"/api/v1/tasks/{task['id']}/comments", json={"body": "Attached it."}).status_code == 201

    detail = clients["owner"].get(f"/api/v1/tasks/{task['id']}").json()
    assert [c["body"] for c in detail["comments"]] == ["Attached it."]
    assert {e["kind"] for e in detail["events"]} == {"created", "assigned", "status"}
    assert detail["completedAt"]
    assert clients["owner"].post("/api/v1/tasks", json={"title": "Second"}).json()["number"] == 2


def test_assignees_are_members_and_dates_are_dates(org):
    clients, _, _, _ = org
    editor = clients["editor"]
    assert editor.post("/api/v1/tasks", json={"title": "x", "assignee_user_id": "not-a-member"}).status_code == 400
    assert editor.post("/api/v1/tasks", json={"title": "x", "due_date": "next week"}).status_code == 400


def test_an_agent_task_reports_back_and_blocks_when_it_cannot_run(org):
    clients, _, system_id, _ = org
    editor = clients["editor"]
    assert editor.post("/api/v1/tasks", json={"title": "x", "assignee_agent": "autopilot", "agent_action": "fairness_run"}).status_code == 400
    assert editor.post("/api/v1/tasks", json={"title": "x", "assignee_agent": "autopilot", "agent_action": "write_policy", "system_id": system_id}).status_code == 400
    assert [a["key"] for a in editor.get("/api/v1/tasks/agents").json()] == ["autopilot"]

    created = editor.post("/api/v1/tasks", json={
        "title": "Re-run the fairness check", "assignee_agent": "autopilot", "agent_action": "fairness_run", "system_id": system_id,
    })
    assert created.status_code == 201, created.text
    task = created.json()
    assert task["status"] == "blocked"  # the system has no fairness data source yet
    detail = editor.get(f"/api/v1/tasks/{task['id']}").json()
    assert detail["comments"][-1]["author"] == "agent:autopilot"
    assert "data source" in detail["comments"][-1]["body"]
    assert editor.post(f"/api/v1/tasks/{task['id']}/run").json()["status"] == "blocked"


def test_tasks_stay_in_their_organisation(org):
    clients, _, _, engine = org
    task = clients["editor"].post("/api/v1/tasks", json={"title": "Ours"}).json()
    other = _client(engine, _new_org(engine), role="owner")
    assert other.get(f"/api/v1/tasks/{task['id']}").status_code == 404
    assert other.get("/api/v1/tasks").json()["tasks"] == []
