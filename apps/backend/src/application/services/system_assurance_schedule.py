"""Durable, review-only preparation of saved System Assurance Reports."""

import json
import logging
import re
import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.services.governance_assurance_service import (
    GovernanceAssuranceService, OrgMembership, normalize_org_role_permissions,
)
from src.application.services.system_assurance_report import REPORT_TYPE, build_system_assurance_report, report_revision

logger = logging.getLogger(__name__)
TICK_LIMIT = 20
EDIT_BACKLOG_LIMIT = 250
SCHEDULER_ACTOR = "FairMind scheduler"


class ScheduleInputError(ValueError):
    pass


class ScheduleNotFound(LookupError):
    pass


class ScheduleConflict(RuntimeError):
    pass


class ScheduleDenied(PermissionError):
    pass


def _validate(cadence: str, time_zone: str, local_time: str) -> tuple[ZoneInfo, time]:
    if cadence not in {"weekly", "monthly"}:
        raise ScheduleInputError("Choose weekly or monthly preparation.")
    if not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", local_time):
        raise ScheduleInputError("Enter a local time in HH:MM format.")
    try:
        zone = ZoneInfo(time_zone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ScheduleInputError("Choose a valid IANA time zone.") from error
    return zone, time.fromisoformat(local_time)


def _next_month(day: date) -> date:
    return (day.replace(day=28) + timedelta(days=4)).replace(day=1)


def _next_run(cadence: str, zone: ZoneInfo, wall_time: time, after: datetime) -> datetime:
    local_day = after.astimezone(zone).date()
    if cadence == "weekly":
        candidate = local_day - timedelta(days=local_day.weekday())
    else:
        candidate = local_day.replace(day=1)
    # On a repeated wall time use the first occurrence. In a gap, using the
    # pre-transition offset advances the local time by the length of the gap.
    instant = datetime.combine(candidate, wall_time, zone).astimezone(timezone.utc)
    if instant <= after:
        candidate = candidate + timedelta(days=7) if cadence == "weekly" else _next_month(candidate)
        instant = datetime.combine(candidate, wall_time, zone).astimezone(timezone.utc)
    return instant


def _report_period(cadence: str, scheduled_at: datetime) -> tuple[date, date]:
    day = scheduled_at.astimezone(timezone.utc).date()
    if cadence == "weekly":
        week_start = day - timedelta(days=day.weekday())
        return week_start - timedelta(days=7), week_start - timedelta(days=1)
    end = day.replace(day=1) - timedelta(days=1)
    return end.replace(day=1), end


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value is not None else None


def preview_schedule(cadence: str, time_zone: str, local_time: str, *, now: datetime | None = None) -> list[dict]:
    zone, wall_time = _validate(cadence, time_zone, local_time)
    upcoming = []
    instant = now or datetime.now(timezone.utc)
    for _ in range(2):
        instant = _next_run(cadence, zone, wall_time, instant)
        start, end = _report_period(cadence, instant)
        upcoming.append({"scheduledAt": _iso(instant), "dateFrom": start.isoformat(), "dateTo": end.isoformat()})
    return upcoming


_SCHEDULES = (
    "SELECT s.*, d.title FROM governance_system_assurance_schedules s "
    "JOIN governance_system_assurance_definitions d ON d.id = s.definition_id "
)
_OCCURRENCE_ROWS = (
    " FROM governance_system_assurance_occurrences o "
    "LEFT JOIN governance_audit_reports r ON r.id = o.report_id AND r.org_id = o.org_id "
    "AND r.system_id = o.system_id AND r.definition_id = o.definition_id "
)
_OCCURRENCES = "SELECT o.*, r.approved_at, r.sha256 AS report_revision" + _OCCURRENCE_ROWS


def _user_id(value: str) -> str | None:
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return None


def _eligible_reviewers(db: Session, org_id: str, user_id: str | None = None, *, lock: bool = False) -> list[dict]:
    rows = db.execute(text(
        "SELECT u.id, COALESCE(NULLIF(TRIM(u.name), ''), u.email) AS name, m.role, o.permissions "
        "FROM org_members m JOIN users u ON u.id = m.user_id "
        "LEFT JOIN org_roles o ON o.org_id = m.org_id AND o.name = m.role "
        "WHERE m.org_id = CAST(:org AS uuid) AND m.status = 'active' AND u.is_active "
        "AND (CAST(:user AS text) IS NULL OR m.user_id IN (:user, :hex)) ORDER BY LOWER(COALESCE(u.name, u.email)), u.id"
        + (" FOR SHARE OF m, u" if lock else "")
    ), {"org": org_id, "user": user_id, "hex": user_id.replace("-", "") if user_id else None})
    reviewers = []
    for row in rows:
        member_id = _user_id(str(row.id))
        permissions = row.permissions
        if lock and row.role not in {"owner", "admin", "editor"}:
            # Custom permissions can be revoked independently of the membership row.
            permissions = db.execute(text(
                "SELECT permissions FROM org_roles WHERE org_id = CAST(:org AS uuid) AND name = :role FOR SHARE"
            ), {"org": org_id, "role": row.role}).scalar_one_or_none()
        if member_id and GovernanceAssuranceService.may_mutate(
            OrgMembership(org_id, member_id, row.role, normalize_org_role_permissions(permissions))
        ):
            reviewers.append({"id": member_id, "name": row.name})
    return reviewers


def list_reviewers(db: Session, *, org_id: str) -> list[dict]:
    return _eligible_reviewers(db, org_id)


def _selected_reviewer(db: Session, org_id: str, reviewer_id: str | None) -> dict:
    if reviewer_id is None:
        return {"id": None, "name": None}
    canonical = _user_id(reviewer_id)
    reviewers = _eligible_reviewers(db, org_id, canonical, lock=True) if canonical else []
    if not reviewers:
        raise ScheduleInputError("Choose an active organization member with report review permission.")
    return reviewers[0]


def _reviewer_payload(row) -> dict | None:
    return {"id": row.reviewer_id, "name": row.reviewer_name} if row.reviewer_id else None


def _occurrence_payload(row) -> dict:
    if row.approved_at:
        review_state = "approved"
    elif row.status != "ready":
        review_state = None
    elif row.returned_revision and row.returned_revision == row.report_revision:
        review_state = "returned"
    else:
        review_state = "awaiting_review"
    return {
        "id": row.id, "definitionId": row.definition_id, "systemId": row.system_id, "assignmentId": row.assignment_id,
        "scheduledAt": _iso(row.scheduled_at), "dateFrom": row.date_from.isoformat(), "dateTo": row.date_to.isoformat(),
        "cadence": row.cadence, "timeZone": row.time_zone, "localTime": row.local_time,
        "status": "approved" if row.approved_at else row.status, "error": row.error, "reportId": row.report_id,
        "attemptedAt": _iso(row.attempted_at), "approvedAt": row.approved_at,
        "reviewer": _reviewer_payload(row), "reviewState": review_state,
        "returned": {"reason": row.returned_reason, "by": row.returned_by, "at": _iso(row.returned_at),
                     "revision": row.returned_revision} if row.returned_at else None,
    }


def _scope(org_id: str, definition_id: str | None) -> dict:
    return {"org": org_id, "definition": definition_id}


def _read_schedule(db: Session, org_id: str, definition_id: str, *, lock: bool = False):
    return db.execute(text(
        _SCHEDULES + "WHERE s.org_id = :org AND s.definition_id = :definition" + (" FOR UPDATE OF s" if lock else "")
    ), _scope(org_id, definition_id)).one_or_none()


def _run_summaries(db: Session, org_id: str, definition_id: str | None = None) -> tuple[dict, dict]:
    select = ("SELECT DISTINCT ON (o.definition_id) o.*, r.approved_at, r.sha256 AS report_revision"
              + _OCCURRENCE_ROWS + "WHERE o.org_id = :org ")
    if definition_id is not None:
        select += "AND o.definition_id = :definition "
    params = _scope(org_id, definition_id)
    latest = db.execute(text(select + "ORDER BY o.definition_id, o.scheduled_at DESC, o.id DESC"), params)
    attention = db.execute(text(
        select + "AND r.approved_at IS NULL AND o.status IN ('failed', 'ready') "
        "ORDER BY o.definition_id, CASE WHEN o.status = 'failed' THEN 0 "
        "WHEN o.returned_revision = r.sha256 THEN 1 ELSE 2 END, o.scheduled_at, o.id"
    ), params)
    return ({row.definition_id: _occurrence_payload(row) for row in latest},
            {row.definition_id: _occurrence_payload(row) for row in attention})


def _schedule_payload(row, summaries: tuple[dict, dict], *, now: datetime | None = None) -> dict:
    latest, attention = summaries
    return {
        "id": row.id, "definitionId": row.definition_id, "systemId": row.system_id, "assignmentId": row.assignment_id,
        "title": row.title, "cadence": row.cadence, "timeZone": row.time_zone, "localTime": row.local_time,
        "active": row.active, "nextRunAt": _iso(row.next_run_at), "createdBy": row.created_by,
        "createdAt": _iso(row.created_at), "updatedAt": _iso(row.updated_at),
        "upcoming": preview_schedule(row.cadence, row.time_zone, row.local_time, now=now) if row.active else [],
        "latestRun": latest.get(row.definition_id), "attentionRun": attention.get(row.definition_id),
        "defaultReviewer": _reviewer_payload(row),
    }


def list_schedules(db: Session, *, org_id: str) -> list[dict]:
    rows = db.execute(text(
        _SCHEDULES + "JOIN governance_ai_systems g ON g.id = s.system_id AND g.org_id = s.org_id "
        "WHERE s.org_id = :org ORDER BY s.created_at DESC, s.id"
    ), {"org": org_id}).all()
    if not rows:
        return []
    summaries = _run_summaries(db, org_id)
    return [_schedule_payload(row, summaries) for row in rows]


def get_schedule(db: Session, *, org_id: str, definition_id: str) -> dict | None:
    row = _read_schedule(db, org_id, definition_id)
    return _schedule_payload(row, _run_summaries(db, org_id, definition_id)) if row else None


def list_occurrences(db: Session, *, org_id: str, definition_id: str) -> list[dict]:
    rows = db.execute(text(
        _OCCURRENCES + "WHERE o.org_id = :org AND o.definition_id = :definition "
        "ORDER BY o.scheduled_at DESC, o.id DESC"
    ), _scope(org_id, definition_id)).all()
    return [_occurrence_payload(row) for row in rows]


def get_occurrence(db: Session, *, org_id: str, occurrence_id: str) -> dict | None:
    row = db.execute(text(_OCCURRENCES + "WHERE o.org_id = :org AND o.id = :id"), {"org": org_id, "id": occurrence_id}).one_or_none()
    return _occurrence_payload(row) if row else None


def _clock(db: Session, now: datetime | None) -> datetime:
    return now if now is not None else db.execute(text("SELECT clock_timestamp()")).scalar_one()


def _queue_occurrence(db: Session, schedule, scheduled_at: datetime) -> None:
    start, end = _report_period(schedule.cadence, scheduled_at)
    db.execute(text(
        "INSERT INTO governance_system_assurance_occurrences "
        "(id, org_id, schedule_id, definition_id, system_id, assignment_id, scheduled_at, date_from, date_to, cadence, time_zone, local_time, status, reviewer_id, reviewer_name) "
        "VALUES (:id, :org, :schedule, :definition, :system, :assignment, :scheduled, :start, :end, :cadence, :zone, :wall, 'pending', :reviewer, :reviewer_name) "
        "ON CONFLICT (schedule_id, scheduled_at) DO NOTHING"
    ), {
        **_scope(schedule.org_id, schedule.definition_id), "id": str(uuid.uuid4()), "schedule": schedule.id,
        "system": schedule.system_id, "assignment": schedule.assignment_id, "scheduled": scheduled_at, "start": start, "end": end,
        "cadence": schedule.cadence, "zone": schedule.time_zone, "wall": schedule.local_time,
        "reviewer": schedule.reviewer_id, "reviewer_name": schedule.reviewer_name,
    })


def _preserve_due_before_edit(db: Session, schedule, now: datetime) -> datetime | None:
    instant = schedule.next_run_at
    if instant is None or instant > now:
        return instant
    zone, wall_time = _validate(schedule.cadence, schedule.time_zone, schedule.local_time)
    for _ in range(EDIT_BACKLOG_LIMIT):
        _queue_occurrence(db, schedule, instant)
        instant = _next_run(schedule.cadence, zone, wall_time, instant)
        if instant > now:
            return instant
    db.rollback()
    raise ScheduleConflict("The schedule has a large preparation backlog. Try the change after pending periods are queued.")


def _save_schedule(db: Session, *, org_id: str, definition_id: str, settings: tuple[str, str, str] | None,
                   active: bool | None, actor: str, now: datetime | None) -> dict:
    scope = _scope(org_id, definition_id)
    definition = db.execute(text(
        "SELECT d.system_id, d.assignment_id, g.lifecycle_stage FROM governance_system_assurance_definitions d "
        "JOIN governance_ai_systems g ON g.id = d.system_id AND g.org_id = d.org_id "
        "WHERE d.id = :definition AND d.org_id = :org FOR NO KEY UPDATE OF d"
    ), scope).one_or_none()
    if definition is None:
        raise ScheduleNotFound("Report definition not found.")
    current = _read_schedule(db, org_id, definition_id, lock=True)
    if settings is None:
        if current is None:
            raise ScheduleNotFound("Report schedule not found.")
        settings = (current.cadence, current.time_zone, current.local_time)
    cadence, time_zone, local_time = settings
    zone, wall_time = _validate(cadence, time_zone, local_time)
    if active is None:
        active = current.active if current else True
    if definition.lifecycle_stage == "retired" and active:
        raise ScheduleConflict("This AI system is retired. Scheduled preparation is unavailable.")
    current_time = _clock(db, now)
    if current and (current.cadence, current.time_zone, current.local_time, current.active) == (*settings, active):
        result = _schedule_payload(current, _run_summaries(db, org_id, definition_id), now=current_time)
        db.commit()
        return result
    if current:
        _preserve_due_before_edit(db, current, current_time)
    db.execute(text(
        "INSERT INTO governance_system_assurance_schedules "
        "(id, org_id, definition_id, system_id, assignment_id, cadence, time_zone, local_time, active, next_run_at, created_by, created_at, updated_at) "
        "VALUES (:id, :org, :definition, :system, :assignment, :cadence, :zone, :wall, :active, :next_run, :actor, :now, :now) "
        "ON CONFLICT (definition_id) DO UPDATE SET cadence = EXCLUDED.cadence, time_zone = EXCLUDED.time_zone, "
        "local_time = EXCLUDED.local_time, active = EXCLUDED.active, next_run_at = EXCLUDED.next_run_at, updated_at = EXCLUDED.updated_at"
    ), {
        **scope, "id": current.id if current else str(uuid.uuid4()), "system": definition.system_id,
        "assignment": definition.assignment_id, "cadence": cadence, "zone": time_zone, "wall": local_time, "active": active,
        "next_run": _next_run(cadence, zone, wall_time, current_time) if active else None, "actor": actor, "now": current_time,
    })
    result = _schedule_payload(_read_schedule(db, org_id, definition_id), _run_summaries(db, org_id, definition_id), now=current_time)
    db.commit()
    return result


def save_schedule(db: Session, *, org_id: str, definition_id: str, cadence: str, time_zone: str, local_time: str,
                  actor: str, active: bool | None = None, now: datetime | None = None) -> dict:
    return _save_schedule(db, org_id=org_id, definition_id=definition_id, settings=(cadence, time_zone, local_time),
                          active=active, actor=actor, now=now)


def set_schedule_active(db: Session, *, org_id: str, definition_id: str, active: bool, actor: str,
                        now: datetime | None = None) -> dict:
    return _save_schedule(db, org_id=org_id, definition_id=definition_id, settings=None, active=active, actor=actor, now=now)


def set_default_reviewer(db: Session, *, org_id: str, definition_id: str, reviewer_id: str | None,
                         now: datetime | None = None) -> dict:
    schedule = _read_schedule(db, org_id, definition_id, lock=True)
    if schedule is None:
        raise ScheduleNotFound("Report schedule not found.")
    reviewer = _selected_reviewer(db, org_id, reviewer_id)
    if reviewer["id"] != schedule.reviewer_id or reviewer["name"] != schedule.reviewer_name:
        now = _clock(db, now)
        next_run = _preserve_due_before_edit(db, schedule, now)
        db.execute(text(
            "UPDATE governance_system_assurance_schedules SET reviewer_id = :reviewer, reviewer_name = :name, "
            "next_run_at = :next, updated_at = :now WHERE id = :id"
        ), {"id": schedule.id, "reviewer": reviewer["id"], "name": reviewer["name"], "now": now, "next": next_run})
    result = get_schedule(db, org_id=org_id, definition_id=definition_id)
    db.commit()
    return result


def may_review(db: Session, *, org_id: str, user_id: str, reviewer_id: str | None, lock: bool = False) -> bool:
    if reviewer_id is None:
        return True  # the caller already checked the existing writer permission
    return _user_id(user_id) == reviewer_id and bool(_eligible_reviewers(db, org_id, reviewer_id, lock=lock))


def list_review_assignments(db: Session, *, org_id: str, user_id: str) -> list[dict]:
    reviewer_id = _user_id(user_id)
    if reviewer_id is None or not _eligible_reviewers(db, org_id, reviewer_id):
        return []
    rows = db.execute(text(
        "SELECT o.*, r.approved_at, r.sha256 AS report_revision, d.title, g.name AS system_name" + _OCCURRENCE_ROWS +
        "JOIN governance_system_assurance_definitions d ON d.id = o.definition_id "
        "JOIN governance_ai_systems g ON g.id = o.system_id AND g.org_id = o.org_id "
        "WHERE o.org_id = :org AND o.reviewer_id = :reviewer AND o.status = 'ready' "
        "AND r.approved_at IS NULL AND r.sha256 IS DISTINCT FROM o.returned_revision "
        "AND g.lifecycle_stage <> 'retired' ORDER BY o.scheduled_at, o.id"
    ), {"org": org_id, "reviewer": reviewer_id}).all()
    return [{"run": _occurrence_payload(row), "title": row.title, "systemName": row.system_name} for row in rows]


def _lock_occurrence(db: Session, org_id: str, occurrence_id: str):
    occurrence = db.execute(text(
        _OCCURRENCES + "WHERE o.org_id = :org AND o.id = :id FOR UPDATE OF o"
    ), {"org": org_id, "id": occurrence_id}).one_or_none()
    if occurrence is None:
        raise ScheduleNotFound("Report preparation run not found.")
    return occurrence


def _lock_report(db: Session, occurrence):
    report = db.execute(text(
        "SELECT approved_at, sha256, created_at FROM governance_audit_reports "
        "WHERE id = :id AND org_id = :org AND system_id = :system AND definition_id = :definition "
        "AND report_type = :type FOR UPDATE"
    ), {**_scope(occurrence.org_id, occurrence.definition_id), "id": occurrence.report_id, "system": occurrence.system_id,
        "type": REPORT_TYPE}).one_or_none()
    if report is None:
        raise ScheduleConflict("The prepared report is unavailable for this scheduled run.")
    return report


def set_occurrence_reviewer(db: Session, *, org_id: str, occurrence_id: str, reviewer_id: str | None) -> dict:
    occurrence = _lock_occurrence(db, org_id, occurrence_id)
    if occurrence.report_id and _lock_report(db, occurrence).approved_at:
        raise ScheduleConflict("An approved report cannot be reassigned.")
    reviewer = _selected_reviewer(db, org_id, reviewer_id)
    db.execute(text(
        "UPDATE governance_system_assurance_occurrences SET reviewer_id = :reviewer, reviewer_name = :name WHERE id = :id"
    ), {"id": occurrence_id, "reviewer": reviewer["id"], "name": reviewer["name"]})
    result = get_occurrence(db, org_id=org_id, occurrence_id=occurrence_id)
    db.commit()
    return result


def _require_review_permission(db: Session, occurrence, user_id: str) -> None:
    if not may_review(db, org_id=occurrence.org_id, user_id=user_id, reviewer_id=occurrence.reviewer_id, lock=True):
        raise ScheduleDenied("Only the assigned, eligible reviewer can review this scheduled report.")


def check_scheduled_approval(db: Session, *, org_id: str, report_id: str, user_id: str, revision: str) -> bool:
    occurrence = db.execute(text(
        _OCCURRENCES + "WHERE o.org_id = :org AND o.report_id = :report FOR UPDATE OF o"
    ), {"org": org_id, "report": report_id}).one_or_none()
    if occurrence is None:
        return False
    report = _lock_report(db, occurrence)
    _require_review_permission(db, occurrence, user_id)
    if report.sha256 != revision:
        raise ScheduleConflict("The preview was superseded. Review the current revision.")
    if not report.approved_at and (occurrence.status != "ready" or occurrence.returned_revision == revision):
        raise ScheduleConflict("The scheduled run must be prepared again before approval.")
    return True


def return_occurrence(db: Session, *, org_id: str, occurrence_id: str, user_id: str, actor: str,
                      revision: str, reason: str) -> dict:
    occurrence = _lock_occurrence(db, org_id, occurrence_id)
    if not occurrence.reviewer_id:
        raise ScheduleDenied("Assign an eligible reviewer before returning this scheduled report.")
    if occurrence.status != "ready" or not occurrence.report_id:
        raise ScheduleConflict("Only a prepared report can be returned.")
    report = _lock_report(db, occurrence)
    _require_review_permission(db, occurrence, user_id)
    if report.approved_at or report.sha256 != revision or occurrence.returned_revision == revision:
        raise ScheduleConflict("This report revision is no longer awaiting review.")
    db.execute(text(
        "UPDATE governance_system_assurance_occurrences SET returned_reason = :reason, returned_revision = :revision, "
        "returned_by = :actor, returned_at = clock_timestamp() WHERE id = :id"
    ), {"id": occurrence_id, "reason": reason, "revision": revision, "actor": actor})
    result = get_occurrence(db, org_id=org_id, occurrence_id=occurrence_id)
    db.commit()
    return result


def _prepare_preview(db: Session, occurrence, actor: str, now: datetime) -> str:
    definition = db.execute(text(
        "SELECT d.title, g.lifecycle_stage FROM governance_system_assurance_definitions d "
        "JOIN governance_ai_systems g ON g.id = d.system_id AND g.org_id = d.org_id "
        "WHERE d.id = :definition AND d.org_id = :org AND d.system_id = :system AND d.assignment_id = :assignment "
        "FOR SHARE OF g"
    ), {**_scope(occurrence.org_id, occurrence.definition_id), "system": occurrence.system_id,
        "assignment": occurrence.assignment_id}).one_or_none()
    if definition is None or definition.lifecycle_stage == "retired":
        raise ScheduleConflict("The selected system or framework assignment is unavailable for scheduled preparation.")
    result = build_system_assurance_report(
        db, org_id=occurrence.org_id, system_id=occurrence.system_id, assignment_id=occurrence.assignment_id,
        date_from=occurrence.date_from, date_to=occurrence.date_to, generated_at=_iso(now),
    )
    if result is None:
        raise ScheduleConflict("The selected framework assignment is unavailable for scheduled preparation.")
    _, config, data = result
    config["definitionId"] = occurrence.definition_id
    report_id = occurrence.report_id or str(uuid.uuid4())
    params = {
        **_scope(occurrence.org_id, occurrence.definition_id), "id": report_id, "system": occurrence.system_id,
        "type": REPORT_TYPE, "title": definition.title, "actor": actor, "config": json.dumps(config), "data": json.dumps(data),
        "now": _iso(now), "revision": report_revision(definition.title, config, data, None),
    }
    if occurrence.report_id:
        updated = db.execute(text(
            "UPDATE governance_audit_reports SET title = :title, generated_by = :actor, config_json = :config, data_json = :data, "
            "created_at = :now, sha256 = :revision "
            "WHERE id = :id AND org_id = :org AND system_id = :system AND definition_id = :definition "
            "AND report_type = :type AND approved_at IS NULL"
        ), params)
        if updated.rowcount != 1:
            raise ScheduleConflict("The scheduled draft is unavailable for refresh.")
    else:
        db.execute(text(
            "INSERT INTO governance_audit_reports "
            "(id, org_id, system_id, definition_id, report_type, title, generated_by, config_json, data_json, created_at, sha256) "
            "VALUES (:id, :org, :system, :definition, :type, :title, :actor, :config, :data, :now, :revision)"
        ), params)
    return report_id


def _attempt(db: Session, occurrence, actor: str, now: datetime) -> None:
    report_id = occurrence.report_id
    error = None
    try:
        with db.begin_nested():
            report_id = _prepare_preview(db, occurrence, actor, now)
    except ScheduleConflict as reason:
        error = str(reason)
    except Exception:
        logger.exception("System assurance preparation failed for occurrence %s", occurrence.id)
        error = "Report preparation failed. Retry this occurrence to prepare the same period."
    db.execute(text(
        "UPDATE governance_system_assurance_occurrences SET status = :status, error = :error, report_id = :report, "
        "attempted_at = :now WHERE id = :id"
    ), {"id": occurrence.id, "status": "failed" if error else "ready", "error": error, "report": report_id, "now": now})


def retry_occurrence(db: Session, *, org_id: str, definition_id: str, occurrence_id: str, actor: str,
                     now: datetime | None = None) -> dict:
    occurrence = _lock_occurrence(db, org_id, occurrence_id)
    if occurrence.definition_id != definition_id:
        raise ScheduleNotFound("Report preparation run not found.")
    if occurrence.status == "pending":
        raise ScheduleConflict("This occurrence is waiting for preparation.")
    current_time = _clock(db, now)
    if occurrence.report_id:
        saved = _lock_report(db, occurrence)
        if saved.approved_at:
            raise ScheduleConflict("An approved report version cannot be refreshed.")
        current_time = max(current_time, datetime.fromisoformat(saved.created_at) + timedelta(microseconds=1))
    _attempt(db, occurrence, actor, current_time)
    result = get_occurrence(db, org_id=org_id, occurrence_id=occurrence_id)
    db.commit()
    return result


def run_due_schedules(session_factory, *, now: datetime | None = None, limit: int = TICK_LIMIT) -> int:
    """Process bounded due work using independent transactions and row locks."""
    processed = 0
    for _ in range(min(limit, TICK_LIMIT)):
        with session_factory() as db:
            current_time = _clock(db, now)
            occurrence = db.execute(text(
                _OCCURRENCES + "WHERE o.status = 'pending' AND o.scheduled_at <= :now "
                "ORDER BY o.scheduled_at, o.id LIMIT 1 FOR UPDATE OF o SKIP LOCKED"
            ), {"now": current_time}).one_or_none()
            if occurrence is None:
                schedule = db.execute(text(
                    _SCHEDULES + "WHERE s.active AND s.next_run_at <= :now "
                    "ORDER BY s.next_run_at, s.id LIMIT 1 FOR UPDATE OF s SKIP LOCKED"
                ), {"now": current_time}).one_or_none()
                if schedule is None:
                    break
                _queue_occurrence(db, schedule, schedule.next_run_at)
                zone, wall_time = _validate(schedule.cadence, schedule.time_zone, schedule.local_time)
                db.execute(text("UPDATE governance_system_assurance_schedules SET next_run_at = :next WHERE id = :id"), {
                    "id": schedule.id, "next": _next_run(schedule.cadence, zone, wall_time, schedule.next_run_at),
                })
                occurrence = db.execute(text(
                    _OCCURRENCES + "WHERE o.schedule_id = :schedule AND o.scheduled_at = :scheduled AND o.status = 'pending' FOR UPDATE OF o"
                ), {"schedule": schedule.id, "scheduled": schedule.next_run_at}).one_or_none()
            if occurrence is not None:
                _attempt(db, occurrence, SCHEDULER_ACTOR, current_time)
                processed += 1
            db.commit()
    return processed
