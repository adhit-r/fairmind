"""HTTP contract for recurring preparation, including unfinished reports and exact-revision approval."""

import uuid
from datetime import datetime, timedelta

import pytest

from config.auth import UserRole
from database.connection import db_manager
from database.governance_models import GovernanceFrameworkVersion
from src.application.services import system_assurance_schedule
from src.application.services.governance_assurance_service import GovernanceAssuranceService
from tests.test_estate_routes import _system
from tests.test_report_routes import AIG, _client, _exec, _org_of


PREFIX = f"{AIG}/reports/system-assurance"
SCHEDULES = f"{PREFIX}/schedules"
CALENDAR = {"cadence": "monthly", "time_zone": "Asia/Kolkata", "local_time": "09:00"}


@pytest.fixture
def scope():
    owner = _client()
    system_id = _system(owner, "Payments routing", "high")
    org_id = _org_of(system_id)
    version_id = str(uuid.uuid4())
    with db_manager.SessionLocal() as db:
        db.execute(GovernanceFrameworkVersion.__table__.insert().values(
            id=version_id, framework_key="schedule-api-test", name="Release review", version_label="1",
            source_hash=version_id,
        ))
        db.commit()
        assignment, _ = GovernanceAssuranceService(db).assign_framework(org_id, system_id, version_id)
    res = owner.post(f"{PREFIX}/definitions", json={
        "title": "Monthly release assurance", "system_id": system_id, "assignment_id": assignment["id"],
    })
    assert res.status_code == 201, res.text
    return owner, _client(org_id=org_id, role=UserRole.VIEWER), _client(), res.json()


def _record_failed_occurrence(definition_id: str, slot: dict) -> str:
    run_id = str(uuid.uuid4())
    _exec("""
        INSERT INTO governance_system_assurance_occurrences
        (id, org_id, schedule_id, definition_id, system_id, assignment_id, scheduled_at, date_from, date_to,
         cadence, time_zone, local_time, status, error)
        SELECT :run, org_id, id, definition_id, system_id, assignment_id, :scheduled, :start, :end,
               cadence, time_zone, local_time, 'failed', 'Temporary source error'
        FROM governance_system_assurance_schedules WHERE definition_id = :definition
    """, run=run_id, scheduled=slot["scheduledAt"], start=slot["dateFrom"], end=slot["dateTo"], definition=definition_id)
    return run_id


def test_schedule_preview_save_pause_and_scope(scope):
    owner, viewer, stranger, definition = scope
    url = f"{SCHEDULES}/{definition['id']}"
    response = viewer.post(f"{SCHEDULES}/preview", json=CALENDAR)
    assert response.status_code == 200, response.text
    upcoming = response.json()["next"]
    assert len(upcoming) == 2 and upcoming[0]["scheduledAt"] < upcoming[1]["scheduledAt"]
    assert owner.get(SCHEDULES).json() == []
    for patch in ({"time_zone": "Not/AZone"}, {"local_time": "24:61"}, {"cadence": "annually"}):
        assert viewer.post(f"{SCHEDULES}/preview", json={**CALENDAR, **patch}).status_code == 422
    assert viewer.put(url, json=CALENDAR).status_code == 403
    assert stranger.put(url, json=CALENDAR).status_code == 404
    saved = owner.put(url, json=CALENDAR)
    assert saved.status_code == 200, saved.text
    schedule = saved.json()
    assert schedule["definitionId"] == definition["id"] and schedule["systemId"] == definition["systemId"]
    assert schedule["paused"] is False and schedule["next"] == upcoming and schedule["latestRun"] is None
    assert owner.put(url, json=CALENDAR).json() == schedule
    assert viewer.get(SCHEDULES).json() == [schedule]
    assert viewer.get(f"{url}/runs").json() == []
    assert stranger.get(SCHEDULES).json() == []
    assert stranger.get(f"{url}/runs").status_code == 404
    assert viewer.patch(url, json={"paused": True}).status_code == 403
    assert owner.patch(url, json={"paused": True}).json()["paused"] is True
    edited = owner.put(url, json={**CALENDAR, "local_time": "10:15"}).json()
    assert edited["paused"] is True and edited["localTime"] == "10:15"
    resumed = owner.patch(url, json={"paused": False}).json()
    assert resumed["paused"] is False and len(resumed["next"]) == 2
    _exec("UPDATE governance_ai_systems SET lifecycle_stage = 'retired' WHERE id = :sid", sid=definition["systemId"])
    assert owner.patch(url, json={"paused": True}).json()["paused"] is True
    assert owner.patch(url, json={"paused": False}).status_code == 409


def test_scheduled_draft_retry_review_and_approved_visibility(scope, monkeypatch):
    owner, viewer, stranger, definition = scope
    system_id = definition["systemId"]
    url = f"{SCHEDULES}/{definition['id']}"
    schedule = owner.put(url, json=CALENDAR)
    assert schedule.status_code == 200, schedule.text
    slot = schedule.json()["next"][0]
    # Start from a recorded preparation failure. The retry must use this same occurrence and frozen period.
    run_id = _record_failed_occurrence(definition["id"], slot)
    target = f"{PREFIX}/scheduled-runs/{run_id}"
    failed_review = owner.get(f"{target}/review")
    assert failed_review.status_code == 200, failed_review.text
    assert failed_review.json()["run"]["status"] == "failed" and failed_review.json()["report"] is None
    assert viewer.get(f"{target}/review").status_code == 403
    assert stranger.post(f"{target}/retry").status_code == 404
    assert viewer.post(f"{target}/retry").status_code == 403
    _exec("UPDATE governance_system_assurance_occurrences SET status = 'pending', error = NULL WHERE id = :id", id=run_id)
    pending = owner.get(f"{target}/review").json()
    assert pending["run"]["status"] == "pending" and pending["report"] is None
    assert owner.post(f"{target}/retry").status_code == 409
    _exec("UPDATE governance_system_assurance_occurrences SET status = 'failed' WHERE id = :id", id=run_id)
    response = owner.post(f"{target}/retry")
    assert response.status_code == 200, response.text
    run = response.json()
    assert run["id"] == run_id and run["systemId"] == system_id and run["status"] == "ready"
    assert (run["dateFrom"], run["dateTo"]) == (slot["dateFrom"], slot["dateTo"])
    assert viewer.get(f"{target}/review").status_code in {403, 404}
    assert stranger.get(f"{target}/review").status_code == 404
    preview = owner.get(f"{target}/review")
    assert preview.status_code == 200, preview.text
    report = preview.json()["report"]
    report_id = run["reportId"]
    assert report["id"] == report_id and report["status"] == "preview"
    assert report["config"]["definitionId"] == definition["id"]
    assert report["config"]["assignmentId"] == definition["assignmentId"]
    assert viewer.get(f"{AIG}/reports/{report_id}").status_code == 404
    assert owner.get(f"{AIG}/reports/{report_id}").status_code == 404
    assert viewer.get(f"{AIG}/reports", params={"system_id": system_id, "definition_id": definition["id"]}).json() == []
    assert owner.get(f"/api/v1/reports/snapshots/{report_id}/json").status_code == 409

    approve = f"{PREFIX}/{report_id}/approve"
    with monkeypatch.context() as outage:
        outage.setattr(system_assurance_schedule, "build_system_assurance_report", lambda *args, **kwargs: None)
        assert owner.post(f"{target}/retry").json()["status"] == "failed"
    failed_review = owner.get(f"{target}/review")
    assert failed_review.status_code == 200, failed_review.text
    assert failed_review.json()["run"]["status"] == "failed" and failed_review.json()["report"] is None
    assert owner.post(approve, json={"revision": report["revision"]}).status_code == 409

    _exec("UPDATE governance_ai_systems SET owner = 'Updated reviewer' WHERE id = :sid", sid=system_id)
    assert owner.post(approve, json={"revision": report["revision"]}).status_code == 409
    assert owner.post(f"{target}/retry").json()["reportId"] == report_id
    assert owner.post(approve, json={"revision": report["revision"]}).status_code == 409
    refreshed = owner.get(f"{target}/review").json()["report"]
    assert refreshed["revision"] != report["revision"]
    approved = owner.post(approve, json={"revision": refreshed["revision"]})
    assert approved.status_code == 200, approved.text
    historical = viewer.get(f"{target}/review").json()
    assert historical["run"]["status"] == "approved" and historical["report"] == approved.json()
    assert viewer.get(f"{url}/runs").json() == [historical["run"]]
    assert owner.get(SCHEDULES).json()[0]["latestRun"] == historical["run"]
    assert owner.get(SCHEDULES).json()[0]["attentionRun"] is None
    assert owner.post(f"{target}/retry").status_code == 409
    assert viewer.get(f"{AIG}/reports/{report_id}").json() == approved.json()
    assert stranger.get(f"{target}/review").status_code == 404

    # The latest successful result must not hide an earlier occurrence that still needs work.
    previous_time = datetime.fromisoformat(slot["scheduledAt"]) - timedelta(days=32)
    previous = _record_failed_occurrence(definition["id"], {**slot, "scheduledAt": previous_time.isoformat()})
    listed = viewer.get(SCHEDULES).json()[0]
    assert listed["latestRun"]["id"] == run_id and listed["attentionRun"]["id"] == previous
    assert listed["attentionRun"]["status"] == "failed"
