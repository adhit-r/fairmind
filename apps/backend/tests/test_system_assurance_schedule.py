from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import text

from database.connection import db_manager
from database.governance_models import GovernanceFrameworkVersion
from src.application.services import system_assurance_schedule as schedules
from src.application.services.governance_assurance_service import GovernanceAssuranceService
from tests.test_estate_routes import _system
from tests.test_report_routes import AIG, _client, _org_of


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value + "+00:00")


@pytest.fixture
def report_scope():
    client = _client()
    sid = _system(client, "Claims", "high")
    org_id = _org_of(sid)
    version = str(uuid4())
    with db_manager.SessionLocal() as db:
        db.execute(GovernanceFrameworkVersion.__table__.insert().values(
            id=version, framework_key="schedule-test", name="Risk framework", version_label="1", source_hash=version,
        ))
        db.commit()
        assignment, _ = GovernanceAssuranceService(db).assign_framework(org_id, sid, version)
    response = client.post(f"{AIG}/reports/system-assurance/definitions", json={
        "system_id": sid, "assignment_id": assignment["id"], "title": "Claims assurance",
    })
    assert response.status_code == 201, response.text
    definition_id = response.json()["id"]
    yield client, {"org_id": org_id, "definition_id": definition_id}
    with db_manager.SessionLocal() as db:
        db.execute(text("UPDATE governance_system_assurance_schedules SET active = FALSE, next_run_at = NULL "
                        "WHERE definition_id = :id"), {"id": definition_id})
        db.commit()


def test_occurrences_pin_previous_complete_utc_period_across_date_and_dst_changes():
    monday = schedules.preview_schedule("weekly", "America/Los_Angeles", "09:30", now=utc("2026-03-01T00:00:00"))
    assert monday == [
        {"scheduledAt": "2026-03-02T17:30:00+00:00", "dateFrom": "2026-02-23", "dateTo": "2026-03-01"},
        {"scheduledAt": "2026-03-09T16:30:00+00:00", "dateFrom": "2026-03-02", "dateTo": "2026-03-08"},
    ]
    assert schedules.preview_schedule("weekly", "Asia/Kolkata", "00:30", now=utc("2026-03-01T00:00:00"))[0] == {
        "scheduledAt": "2026-03-01T19:00:00+00:00", "dateFrom": "2026-02-16", "dateTo": "2026-02-22",
    }
    assert schedules.preview_schedule("monthly", "Australia/Sydney", "02:30", now=utc("2023-09-29T00:00:00"))[0] == {
        "scheduledAt": "2023-09-30T16:30:00+00:00", "dateFrom": "2023-08-01", "dateTo": "2023-08-31",
    }
    repeated = schedules.preview_schedule("monthly", "Australia/Sydney", "02:30", now=utc("2018-03-30T00:00:00"))
    assert repeated[0]["scheduledAt"] == "2018-03-31T15:30:00+00:00"
    assert repeated[1]["scheduledAt"] == "2018-04-30T16:30:00+00:00"
    with pytest.raises(schedules.ScheduleInputError):
        schedules.preview_schedule("weekly", "Europe/Nonexistent", "12:00")
    with pytest.raises(schedules.ScheduleInputError):
        schedules.preview_schedule("weekly", "UTC", "24:00")


def test_durable_due_cursor_catches_up_after_restart_and_concurrent_ticks(report_scope, monkeypatch):
    client, scope = report_scope
    with db_manager.SessionLocal() as db:
        saved = schedules.save_schedule(db, **scope, cadence="weekly", time_zone="UTC", local_time="10:00",
                                        actor="author", now=utc("2026-01-02T00:00:00"))
    assert saved["nextRunAt"] == "2026-01-05T10:00:00+00:00"
    assert saved["upcoming"][0]["scheduledAt"] == saved["nextRunAt"]

    downtime = utc("2026-01-26T11:00:00")
    class Interrupted(BaseException):
        pass

    def stop_process(*args, **kwargs):
        raise Interrupted

    with monkeypatch.context() as patch:
        patch.setattr(schedules, "_prepare_preview", stop_process)
        with pytest.raises(Interrupted):
            schedules.run_due_schedules(db_manager.SessionLocal, now=downtime)
    with db_manager.SessionLocal() as db:
        assert schedules.list_occurrences(db, **scope) == []
        assert schedules.get_schedule(db, **scope)["nextRunAt"] == saved["nextRunAt"]
    assert schedules.run_due_schedules(db_manager.SessionLocal, now=downtime, limit=2) == 2
    with ThreadPoolExecutor(max_workers=2) as pool:
        ticks = list(pool.map(lambda _: schedules.run_due_schedules(db_manager.SessionLocal, now=downtime), range(2)))
    assert sum(ticks) == 2
    assert schedules.run_due_schedules(db_manager.SessionLocal, now=downtime) == 0

    with db_manager.SessionLocal() as db:
        runs = schedules.list_occurrences(db, **scope)
        assert len({run["id"] for run in runs}) == len({run["reportId"] for run in runs}) == 4
        assert [r["dateFrom"] for r in runs] == ["2026-01-19", "2026-01-12", "2026-01-05", "2025-12-29"]
        assert {r["status"] for r in runs} == {"ready"}
        assert schedules.list_schedules(db, org_id=str(uuid4())) == []
        current = schedules.list_schedules(db, org_id=scope["org_id"])[0]
        assert current["id"] == saved["id"] and current["nextRunAt"] == "2026-02-02T10:00:00+00:00"
        assert current["latestRun"]["id"] == runs[0]["id"] and current["attentionRun"]["id"] == runs[-1]["id"]
    run = runs[0]
    review = client.get(f"{AIG}/reports/system-assurance/scheduled-runs/{run['id']}/review")
    assert review.status_code == 200, review.text
    report = review.json()["report"]
    assert report["title"] == "Claims assurance" and report["status"] == "preview"
    assert report["config"]["definitionId"] == scope["definition_id"]
    assert report["config"]["dateFrom"] == run["dateFrom"] and report["config"]["dateTo"] == run["dateTo"]
    assert client.get(f"/api/v1/reports/snapshots/{report['id']}/pdf").status_code == 409


def test_schedule_edits_keep_due_periods_and_pause_without_losing_history(report_scope):
    _, scope = report_scope
    with db_manager.SessionLocal() as db:
        saved = schedules.save_schedule(db, **scope, cadence="weekly", time_zone="UTC", local_time="08:00",
                                        actor="author", now=utc("2026-01-02T00:00:00"))
        changed = schedules.save_schedule(db, **scope, cadence="monthly", time_zone="UTC", local_time="17:00",
                                          actor="author", now=utc("2026-01-12T12:00:00"))
        assert changed["id"] == saved["id"] and changed["nextRunAt"] == "2026-02-01T17:00:00+00:00"
        queued = schedules.list_occurrences(db, **scope)
        assert [r["scheduledAt"] for r in queued] == ["2026-01-12T08:00:00+00:00", "2026-01-05T08:00:00+00:00"]
        assert {r["status"] for r in queued} == {"pending"}
        assert {r["localTime"] for r in queued} == {"08:00"}
        paused = schedules.set_schedule_active(db, **scope, active=False, actor="author", now=utc("2026-01-20T00:00:00"))
        assert not paused["active"] and paused["nextRunAt"] is None
        paused_edit = schedules.save_schedule(db, **scope, cadence="monthly", time_zone="UTC", local_time="19:00",
                                              actor="author", now=utc("2026-01-30T00:00:00"))
        assert not paused_edit["active"]

    assert schedules.run_due_schedules(db_manager.SessionLocal, now=utc("2026-02-11T00:00:00")) == 2
    with db_manager.SessionLocal() as db:
        resumed = schedules.set_schedule_active(db, **scope, active=True, actor="author", now=utc("2026-02-14T00:00:00"))
        assert resumed["nextRunAt"] == "2026-03-01T19:00:00+00:00"
        runs = schedules.list_occurrences(db, **scope)
        assert [r["id"] for r in runs] == [r["id"] for r in queued]
        assert {r["status"] for r in runs} == {"ready"}


def test_failure_retry_and_refresh_keep_occurrence_and_preserve_approval(report_scope, monkeypatch):
    client, scope = report_scope
    with db_manager.SessionLocal() as db:
        schedules.save_schedule(db, **scope, cadence="monthly", time_zone="UTC", local_time="09:00",
                                actor="author", now=utc("2026-01-20T00:00:00"))

    def fail_preparation(*args, **kwargs):
        raise RuntimeError("internal test failure")

    with monkeypatch.context() as patch:
        patch.setattr(schedules, "build_system_assurance_report", fail_preparation)
        assert schedules.run_due_schedules(db_manager.SessionLocal, now=utc("2026-02-01T09:00:00")) == 1
    assert schedules.run_due_schedules(db_manager.SessionLocal, now=utc("2026-03-01T10:00:00")) == 1

    with db_manager.SessionLocal() as db:
        ready, failed = schedules.list_occurrences(db, **scope)
        assert failed["status"] == "failed" and not failed["reportId"]
        assert "internal test failure" not in failed["error"]
        current = schedules.get_schedule(db, **scope)
        assert current["latestRun"]["id"] == ready["id"] and current["attentionRun"]["id"] == failed["id"]
        retried = schedules.retry_occurrence(db, **scope, occurrence_id=failed["id"], actor="reviewer", now=utc("2026-03-02T10:00:00"))
        assert retried["status"] == "ready" and retried["dateFrom"] == "2026-01-01"
        assert retried["id"] == failed["id"] and retried["scheduledAt"] == failed["scheduledAt"]

    review_url = f"{AIG}/reports/system-assurance/scheduled-runs/{retried['id']}/review"
    before_refresh = client.get(review_url).json()["report"]
    with db_manager.SessionLocal() as db:
        refreshed = schedules.retry_occurrence(db, **scope, occurrence_id=failed["id"], actor="reviewer", now=utc("2026-03-03T10:00:00"))
        assert refreshed["reportId"] == retried["reportId"]
    after_refresh = client.get(review_url).json()["report"]
    assert after_refresh["revision"] != before_refresh["revision"]
    assert after_refresh["config"] == before_refresh["config"]
    approve_url = f"{AIG}/reports/system-assurance/{after_refresh['id']}/approve"
    assert client.post(approve_url, json={"revision": before_refresh["revision"]}).status_code == 409
    approved = client.post(approve_url, json={"revision": after_refresh["revision"]})
    assert approved.status_code == 200, approved.text
    with db_manager.SessionLocal() as db:
        assert schedules.get_occurrence(db, org_id=scope["org_id"], occurrence_id=failed["id"])["status"] == "approved"
        with pytest.raises(schedules.ScheduleConflict):
            schedules.retry_occurrence(db, **scope, occurrence_id=failed["id"], actor="reviewer")
        assert db.execute(text("SELECT sha256 FROM governance_audit_reports WHERE id = :id"), {"id": retried["reportId"]}).scalar() == after_refresh["revision"]
