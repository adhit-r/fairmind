from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app
from config.auth import User as AuthUser, UserRole, auth_manager
from database.connection import db_manager
from database.models import Organization, OrganizationMember, User
from src.application.services import system_assurance_schedule as schedules
from tests.test_report_routes import _exec, _org_of
from tests.test_system_assurance_schedule_api import CALENDAR, PREFIX, SCHEDULES, scope


@pytest.fixture(autouse=True)
def pause_test_schedule(scope):
    yield
    _exec("UPDATE governance_system_assurance_schedules SET active = FALSE, next_run_at = NULL WHERE definition_id = :id",
          id=scope[3]["id"])


def _reviewers(org_id: str):
    accounts = []
    with db_manager.SessionLocal() as db:
        for name, role in (("Asha", "editor"), ("Devi", "admin"), ("Pia", "viewer")):
            uid = uuid4()
            email = f"{uid}@test.invalid"
            db.execute(User.__table__.insert().values(
                id=uid, email=email, username=str(uid), name=name, is_active=True, password_hash="",
            ))
            if not accounts:
                db.execute(Organization.__table__.insert().values(id=UUID(org_id), name=org_id, slug=org_id, owner_id=uid))
            db.execute(OrganizationMember.__table__.insert().values(org_id=UUID(org_id), user_id=uid, status="active", role=role))
            user = AuthUser(id=str(uid), email=email, username=name, role=UserRole.ADMIN if role == "admin" else UserRole.ANALYST,
                            org_id=org_id, created_at=datetime.now(timezone.utc), permissions=[])
            client = TestClient(app, client=(f"assigned-{uid.hex[:8]}", 50000),
                                headers={"Authorization": f"Bearer {auth_manager.create_access_token(user)}"})
            accounts.append(({"id": str(uid), "name": name}, client, email))
        db.commit()
    return accounts


def _prepare(owner, definition, reviewer):
    target = f"{SCHEDULES}/{definition['id']}"
    response = owner.put(target, json=CALENDAR)
    assert response.status_code == 200, response.text
    saved = owner.patch(f"{target}/reviewer", json={"reviewer_id": reviewer["id"]})
    assert saved.status_code == 200, saved.text
    schedule = saved.json()
    assert schedule["defaultReviewer"] == reviewer
    due = datetime.fromisoformat(schedule["next"][0]["scheduledAt"])
    schedules.run_due_schedules(db_manager.SessionLocal, now=due)
    run = owner.get(f"{target}/runs").json()[0]
    assert run["reviewer"] == reviewer and run["reviewState"] == "awaiting_review"
    return target, run


def test_assigned_review_returns_exact_revision_and_can_be_reprepared(scope):
    owner, outsider_viewer, stranger, definition = scope
    org_id = _org_of(definition["systemId"])
    (asha, reviewer, reviewer_email), (devi, next_reviewer, _), (pia, viewer, _) = _reviewers(org_id)
    assert owner.get(f"{PREFIX}/reviewers").json() == [asha, devi]
    assert stranger.get(f"{PREFIX}/reviewers").json() == []
    target, run = _prepare(owner, definition, asha)
    review_url = f"{PREFIX}/scheduled-runs/{run['id']}"
    queue_url = f"{PREFIX}/review-assignments"
    assigned = reviewer.get(queue_url).json()
    assert assigned == [{"run": run, "title": definition["title"], "systemName": "Payments routing"}]
    assert owner.get(queue_url).json() == next_reviewer.get(queue_url).json() == stranger.get(queue_url).json() == []
    assert stranger.get(f"{review_url}/review").status_code == 404
    assert viewer.get(f"{review_url}/review").status_code == 403
    assert outsider_viewer.patch(f"{review_url}/reviewer", json={"reviewer_id": devi["id"]}).status_code == 403
    assert stranger.patch(f"{review_url}/reviewer", json={"reviewer_id": devi["id"]}).status_code == 404
    assert owner.patch(f"{target}/reviewer", json={"reviewer_id": pia["id"]}).status_code == 422
    draft = reviewer.get(f"{review_url}/review").json()
    assert draft["canReview"] and draft["canRefresh"]
    owner_view = owner.get(f"{review_url}/review").json()
    assert not owner_view["canReview"] and owner_view["canRefresh"]
    approve = f"{PREFIX}/{run['reportId']}/approve"
    proposal = {"revision": draft["report"]["revision"], "reason": "  Explain the review scope.  "}
    assert owner.post(approve, json={"revision": proposal["revision"]}).status_code == 403
    assert owner.post(f"{review_url}/return", json=proposal).status_code == 403
    assert reviewer.post(f"{review_url}/return", json={**proposal, "reason": " "}).status_code == 422
    assert reviewer.post(f"{review_url}/return", json={**proposal, "revision": "a" * 64}).status_code == 409
    response = reviewer.post(f"{review_url}/return", json=proposal)
    assert response.status_code == 200, response.text
    returned = response.json()
    assert returned["status"] == "ready" and returned["reviewState"] == "returned"
    assert returned["returned"] == {"reason": "Explain the review scope.", "by": reviewer_email,
                                    "at": returned["returned"]["at"], "revision": proposal["revision"]}
    assert datetime.fromisoformat(returned["returned"]["at"]).tzinfo is not None
    assert reviewer.get(queue_url).json() == []
    assert not reviewer.get(f"{review_url}/review").json()["canReview"]
    assert reviewer.post(approve, json={"revision": proposal["revision"]}).status_code == 409
    assert reviewer.post(f"{review_url}/return", json=proposal).status_code == 409
    assert owner.get(SCHEDULES).json()[0]["attentionRun"]["reviewState"] == "returned"

    changed_default = owner.patch(f"{target}/reviewer", json={"reviewer_id": devi["id"]}).json()
    assert changed_default["defaultReviewer"] == devi and changed_default["latestRun"]["reviewer"] == asha
    reassigned = owner.patch(f"{review_url}/reviewer", json={"reviewer_id": devi["id"]}).json()
    assert reassigned["id"] == run["id"] and reassigned["reviewer"] == devi and reassigned["returned"] == returned["returned"]
    refreshed = owner.post(f"{review_url}/retry").json()
    assert refreshed["id"] == run["id"] and refreshed["reportId"] == run["reportId"]
    assert refreshed["reviewState"] == "awaiting_review" and refreshed["returned"] == returned["returned"]
    assert refreshed["dateFrom"] == run["dateFrom"] and refreshed["dateTo"] == run["dateTo"]
    renewed = next_reviewer.get(f"{review_url}/review").json()
    assert renewed["canReview"] and renewed["report"]["revision"] != proposal["revision"]
    assert reviewer.get(queue_url).json() == [] and next_reviewer.get(queue_url).json()[0]["run"] == refreshed
    assert reviewer.post(approve, json={"revision": renewed["report"]["revision"]}).status_code == 403
    assert next_reviewer.post(approve, json={"revision": proposal["revision"]}).status_code == 409

    _exec("UPDATE org_members SET status = 'suspended' WHERE org_id = :org AND user_id = :user", org=org_id, user=devi["id"])
    assert next_reviewer.post(approve, json={"revision": renewed["report"]["revision"]}).status_code in {403, 404}
    assert next_reviewer.get(queue_url).json() == []
    assert owner.patch(f"{review_url}/reviewer", json={"reviewer_id": devi["id"]}).status_code == 422
    assert owner.patch(f"{review_url}/reviewer", json={"reviewer_id": asha["id"]}).status_code == 200
    approved = reviewer.post(approve, json={"revision": renewed["report"]["revision"]})
    assert approved.status_code == 200, approved.text
    result = viewer.get(f"{review_url}/review").json()
    assert result["run"]["reviewState"] == "approved" and result["run"]["returned"] == returned["returned"]
    assert result["report"] == approved.json() and not result["canReview"] and not result["canRefresh"]
    assert reviewer.get(queue_url).json() == []
    assert owner.patch(f"{review_url}/reviewer", json={"reviewer_id": None}).status_code == 409
    assert owner.post(f"{review_url}/retry").status_code == 409


def test_same_revision_cannot_be_returned_and_approved_concurrently(scope):
    owner, _, _, definition = scope
    (asha, reviewer, _), *_ = _reviewers(_org_of(definition["systemId"]))
    _, run = _prepare(owner, definition, asha)
    review_url = f"{PREFIX}/scheduled-runs/{run['id']}"
    draft = reviewer.get(f"{review_url}/review").json()["report"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        approved = pool.submit(reviewer.post, f"{PREFIX}/{draft['id']}/approve", json={"revision": draft["revision"]})
        returned = pool.submit(reviewer.post, f"{review_url}/return", json={"revision": draft["revision"], "reason": "Add context."})
        assert sorted([approved.result().status_code, returned.result().status_code]) == [200, 409]
    assert reviewer.get(f"{review_url}/review").json()["run"]["reviewState"] in {"approved", "returned"}


def test_default_change_preserves_reviewer_for_occurrences_already_due(scope):
    _, _, _, definition = scope
    org_id = _org_of(definition["systemId"])
    (asha, _, _), (devi, _, _), _ = _reviewers(org_id)
    selected = {"org_id": org_id, "definition_id": definition["id"]}
    with db_manager.SessionLocal() as db:
        schedules.save_schedule(db, **selected, cadence="weekly", time_zone="UTC", local_time="09:00", actor="editor",
                                now=datetime(2026, 1, 1, tzinfo=timezone.utc))
        schedules.set_default_reviewer(db, **selected, reviewer_id=asha["id"], now=datetime(2026, 1, 2, tzinfo=timezone.utc))
        schedules.set_default_reviewer(db, **selected, reviewer_id=devi["id"], now=datetime(2026, 1, 15, tzinfo=timezone.utc))
        due = schedules.list_occurrences(db, **selected)
        assert len(due) == 2 and all(run["reviewer"] == asha and run["status"] == "pending" for run in due)
    schedules.run_due_schedules(db_manager.SessionLocal, now=datetime(2026, 1, 20, tzinfo=timezone.utc))
    with db_manager.SessionLocal() as db:
        runs = schedules.list_occurrences(db, **selected)
        assert [run["reviewer"] for run in runs] == [devi, asha, asha]
        assert all(run["reviewState"] == "awaiting_review" for run in runs)
