"""Tasks: work assigned to a person or an AI agent in an organisation, about a system, requirement or finding.

GET    /tasks?org_id=                       open and recent tasks; ?mine=true, ?status=, ?subject_type=, ?system_id=
GET    /tasks/agents?org_id=                the agents a task can be assigned to, and what each can do
POST   /tasks?org_id=                       create (editor or above); assigning an agent starts it at once
GET    /tasks/{id}?org_id=                  the task with its comments and activity
PATCH  /tasks/{id}?org_id=                  edit (editor or above); the assignee may change the status of their own task
POST   /tasks/{id}/comments?org_id=         comment (any member)
POST   /tasks/{id}/run?org_id=              run the assigned agent again (editor or above)

An agent does real work and reports it on the task: the release autopilot re-runs the fairness check or takes a
monitoring snapshot from the system's data source, records measured evidence, then marks the task done, or
blocked with the reason it could not run.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.routes.packs import _manager, _member
from config.settings import settings
from database.connection import get_db
from src.application.services.governance_assurance_service import GovernanceAssuranceService, OrgMembership

logger = logging.getLogger("fairmind.tasks")
router = APIRouter(tags=["tasks"])

STATUSES = ("open", "in_progress", "blocked", "done")
PRIORITIES = ("high", "medium", "low")
SUBJECTS = ("requirement", "system", "finding", "source", "none")
# Agents a task can go to. Each action names the autopilot runner and the system data source it needs.
AGENTS: Dict[str, Dict[str, Any]] = {
    "autopilot": {
        "name": "Release autopilot",
        "actions": {
            "fairness_run": "Re-run the fairness check from the system's fairness data source",
            "monitoring_snapshot": "Take a monitoring snapshot from the system's monitoring data source",
        },
    },
}
AGENT_ACTOR = "agent:autopilot"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
COLS = ("id, number, title, description, status, priority, assignee_user_id, assignee_agent, agent_action, created_by, "
        "due_date, subject_type, subject_id, subject_label, system_id, created_at, updated_at, completed_at")


class TaskBody(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=10000)
    priority: Literal["high", "medium", "low"] = "medium"
    due_date: Optional[str] = None
    assignee_user_id: Optional[str] = None
    assignee_agent: Optional[str] = None
    agent_action: Optional[str] = None
    subject_type: Literal["requirement", "system", "finding", "source", "none"] = "none"
    subject_id: Optional[str] = Field(default=None, max_length=300)
    subject_label: Optional[str] = Field(default=None, max_length=300)
    system_id: Optional[str] = None
    notify: bool = True


class TaskPatch(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    description: Optional[str] = Field(default=None, max_length=10000)
    status: Optional[Literal["open", "in_progress", "blocked", "done"]] = None
    priority: Optional[Literal["high", "medium", "low"]] = None
    due_date: Optional[str] = None  # "" clears it
    assignee_user_id: Optional[str] = None  # "" unassigns
    assignee_agent: Optional[str] = None
    agent_action: Optional[str] = None


class CommentBody(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _out(row) -> Dict[str, Any]:
    r = dict(row._mapping)
    return {
        "id": r["id"], "number": r["number"], "title": r["title"], "description": r["description"], "status": r["status"],
        "priority": r["priority"], "assigneeUserId": r["assignee_user_id"], "assigneeAgent": r["assignee_agent"],
        "agentAction": r["agent_action"], "createdBy": r["created_by"], "dueDate": r["due_date"],
        "subject": {"type": r["subject_type"], "id": r["subject_id"], "label": r["subject_label"]},
        "systemId": r["system_id"], "createdAt": r["created_at"], "updatedAt": r["updated_at"], "completedAt": r["completed_at"],
    }


def _task(db: Session, org_id: str, task_id: str):
    row = db.execute(text(f"SELECT {COLS} FROM org_tasks WHERE id = :id AND org_id = :org"), {"id": task_id, "org": org_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


def _event(db: Session, org_id: str, task_id: str, actor: str, kind: str, **detail) -> None:
    db.execute(
        text("INSERT INTO org_task_events (id, task_id, org_id, actor_user_id, kind, detail_json, created_at) "
             "VALUES (:id, :t, :o, :a, :k, :d, :now)"),
        {"id": str(uuid.uuid4()), "t": task_id, "o": org_id, "a": actor, "k": kind, "d": json.dumps(detail), "now": _now()},
    )


def _comment(db: Session, org_id: str, task_id: str, author: str, body: str) -> None:
    db.execute(
        text("INSERT INTO org_task_comments (id, task_id, org_id, author_user_id, body, created_at) VALUES (:id, :t, :o, :a, :b, :now)"),
        {"id": str(uuid.uuid4()), "t": task_id, "o": org_id, "a": author, "b": body, "now": _now()},
    )


def _require_member(db: Session, org_id: str, user_id: str) -> Dict[str, Any]:
    """An assignee must be an active member of this org; returns their email and name for the notice."""
    row = db.execute(
        text("SELECT u.email, u.name FROM org_members m JOIN users u ON CAST(u.id AS TEXT) = CAST(m.user_id AS TEXT) "
             "WHERE CAST(m.org_id AS TEXT) = :org AND CAST(m.user_id AS TEXT) = :uid AND m.status = 'active'"),
        {"org": org_id, "uid": user_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="The assignee must be an active member of this organisation")
    return {"email": row[0], "name": row[1]}


def _require_agent(agent: Optional[str], action: Optional[str], system_id: Optional[str]) -> None:
    if agent not in AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent; choose one of {', '.join(AGENTS)}")
    if action not in AGENTS[agent]["actions"]:
        raise HTTPException(status_code=400, detail=f"{AGENTS[agent]['name']} can: {', '.join(AGENTS[agent]['actions'])}")
    if not system_id:
        raise HTTPException(status_code=400, detail="An agent task needs the AI system it works on")


def _require_system(db: Session, org_id: str, system_id: Optional[str]) -> None:
    if system_id and not db.execute(
        text("SELECT 1 FROM governance_ai_systems WHERE id = :id AND org_id = :org"), {"id": system_id, "org": org_id}
    ).fetchone():
        raise HTTPException(status_code=404, detail="System not found")


def _check_date(value: Optional[str]) -> Optional[str]:
    if value in (None, ""):
        return None
    if not DATE.match(value):
        raise HTTPException(status_code=400, detail="Due date must be YYYY-MM-DD")
    return value


async def _notify(task: Dict[str, Any], person: Dict[str, Any]) -> None:
    try:
        from src.application.services.api_boundary_dependencies import email_service

        await email_service.send_task_assigned(
            person["email"], task["title"], task.get("subject_label"), task.get("due_date"), f"{settings.frontend_url}/tasks?task={task['id']}"
        )
    except Exception as exc:  # a failed notice never fails the assignment
        logger.warning("Task assignment email failed: %s", exc)


async def _run_agent(db: Session, org_id: str, task_id: str) -> None:
    """The agent works the task now and reports on it: done with the evidence, or blocked with why."""
    from api.routes import autopilot

    row = _task(db, org_id, task_id)
    action, system_id = row.agent_action, row.system_id
    _event(db, org_id, task_id, AGENT_ACTOR, "status", to="in_progress")
    db.execute(text("UPDATE org_tasks SET status = 'in_progress', updated_at = :now WHERE id = :id"), {"id": task_id, "now": _now()})
    db.commit()
    purpose = autopilot.AGENT_ACTIONS[action]
    with autopilot._system_lock(db.get_bind(), system_id) as got:  # never overlaps an autopilot run on the system
        if not got:
            status, note = "blocked", f"I could not run this: {autopilot.RUN_IN_PROGRESS}. Run the task again when it is done."
        elif not autopilot._sources(db, system_id)[purpose]:
            status, note = "blocked", f"I need a {purpose} data source on this system before I can run this. Add one on the system's Autopilot tab."
        else:
            try:
                evidence_id, detail = await autopilot.RUNNERS[action](db, org_id, system_id)
                autopilot._event(db, org_id, system_id, purpose, action, "done", detail, AGENT_ACTOR, evidence_id)
                status, note = "done", f"Done. {detail} Evidence {evidence_id} is on the system."
            except autopilot.AutopilotError as exc:
                db.rollback()
                status, note = "blocked", f"I could not run this: {exc}"
    now = _now()
    db.execute(
        text("UPDATE org_tasks SET status = :s, updated_at = :now, completed_at = :done WHERE id = :id"),
        {"s": status, "now": now, "done": now if status == "done" else None, "id": task_id},
    )
    _comment(db, org_id, task_id, AGENT_ACTOR, note)
    _event(db, org_id, task_id, AGENT_ACTOR, "status", to=status)
    db.commit()


@router.get("/tasks/agents")
def list_agents(_m: OrgMembership = Depends(_member)):
    return [{"key": k, "name": a["name"], "actions": [{"key": ak, "label": al} for ak, al in a["actions"].items()]} for k, a in AGENTS.items()]


@router.get("/tasks")
def list_tasks(
    m: OrgMembership = Depends(_member),
    db: Session = Depends(get_db),
    mine: bool = Query(default=False),
    status: Optional[str] = Query(default=None),
    subject_type: Optional[str] = Query(default=None),
    system_id: Optional[str] = Query(default=None),
):
    where, params = ["org_id = :org"], {"org": m.org_id}
    if mine:
        where.append("assignee_user_id = :me")
        params["me"] = str(m.user_id)
    if status == "open":
        where.append("status <> 'done'")
    elif status in STATUSES:
        where.append("status = :status")
        params["status"] = status
    if subject_type in SUBJECTS:
        where.append("subject_type = :st")
        params["st"] = subject_type
    if system_id:
        where.append("system_id = :sys")
        params["sys"] = system_id
    rows = db.execute(
        text(f"SELECT {COLS} FROM org_tasks WHERE {' AND '.join(where)} "
             "ORDER BY (status = 'done'), due_date IS NULL, due_date, number DESC LIMIT 500"),
        params,
    ).fetchall()
    return {"tasks": [_out(r) for r in rows]}


@router.post("/tasks", status_code=201)
async def create_task(body: TaskBody, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    if body.assignee_user_id and body.assignee_agent:
        raise HTTPException(status_code=400, detail="Assign a person or an agent, not both")
    due = _check_date(body.due_date)
    _require_system(db, m.org_id, body.system_id)
    person = _require_member(db, m.org_id, body.assignee_user_id) if body.assignee_user_id else None
    if body.assignee_agent:
        _require_agent(body.assignee_agent, body.agent_action, body.system_id)
    task_id, now = str(uuid.uuid4()), _now()
    for _attempt in range(3):  # two creates racing for the next number: the loser takes the one after
        number = (db.execute(text("SELECT COALESCE(MAX(number), 0) + 1 FROM org_tasks WHERE org_id = :org"), {"org": m.org_id}).scalar())
        try:
            db.execute(
                text("INSERT INTO org_tasks (id, org_id, number, title, description, status, priority, assignee_user_id, assignee_agent, "
                     "agent_action, created_by, due_date, subject_type, subject_id, subject_label, system_id, created_at, updated_at) "
                     "VALUES (:id, :org, :n, :title, :desc, 'open', :pri, :uid, :agent, :action, :by, :due, :st, :sid, :slabel, :sys, :now, :now)"),
                {"id": task_id, "org": m.org_id, "n": number, "title": body.title.strip(), "desc": body.description, "pri": body.priority,
                 "uid": body.assignee_user_id, "agent": body.assignee_agent, "action": body.agent_action if body.assignee_agent else None,
                 "by": str(m.user_id), "due": due, "st": body.subject_type, "sid": body.subject_id, "slabel": body.subject_label,
                 "sys": body.system_id, "now": now},
            )
            break
        except IntegrityError:
            db.rollback()
    else:
        raise HTTPException(status_code=409, detail="Could not number the task; try again")
    _event(db, m.org_id, task_id, str(m.user_id), "created")
    if body.assignee_user_id or body.assignee_agent:
        _event(db, m.org_id, task_id, str(m.user_id), "assigned", to=body.assignee_user_id or f"agent:{body.assignee_agent}", due=due)
    db.commit()
    if person and body.notify and str(body.assignee_user_id) != str(m.user_id):
        await _notify({"id": task_id, "title": body.title, "subject_label": body.subject_label, "due_date": due}, person)
    if body.assignee_agent:
        await _run_agent(db, m.org_id, task_id)
    return _out(_task(db, m.org_id, task_id))


@router.get("/tasks/{task_id}")
def get_task(task_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    task = _out(_task(db, m.org_id, task_id))
    task["comments"] = [
        {"id": r[0], "author": r[1], "body": r[2], "createdAt": r[3]}
        for r in db.execute(text("SELECT id, author_user_id, body, created_at FROM org_task_comments WHERE task_id = :t ORDER BY created_at"), {"t": task_id})
    ]
    task["events"] = [
        {"actor": r[0], "kind": r[1], "detail": json.loads(r[2] or "{}"), "createdAt": r[3]}
        for r in db.execute(text("SELECT actor_user_id, kind, detail_json, created_at FROM org_task_events WHERE task_id = :t ORDER BY created_at DESC"), {"t": task_id})
    ]
    return task


@router.patch("/tasks/{task_id}")
async def update_task(task_id: str, body: TaskPatch, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    row = _task(db, m.org_id, task_id)
    changes = body.model_dump(exclude_unset=True)
    editor = GovernanceAssuranceService.may_mutate(m)
    own = row.assignee_user_id is not None and str(row.assignee_user_id) == str(m.user_id)
    if not editor and not (own and set(changes) <= {"status"}):
        raise HTTPException(status_code=403, detail="Only editors and above change tasks; the assignee may change the status of their own")
    sets, params, person, actor = [], {"id": task_id}, None, str(m.user_id)
    if "assignee_user_id" in changes or "assignee_agent" in changes:
        uid, agent = changes.get("assignee_user_id") or None, changes.get("assignee_agent") or None
        if uid and agent:
            raise HTTPException(status_code=400, detail="Assign a person or an agent, not both")
        if uid:
            person = _require_member(db, m.org_id, uid)
        if agent:
            _require_agent(agent, changes.get("agent_action") or row.agent_action, row.system_id)
        sets += ["assignee_user_id = :uid", "assignee_agent = :agent", "agent_action = :action"]
        params.update(uid=uid, agent=agent, action=(changes.get("agent_action") or row.agent_action) if agent else None)
        _event(db, m.org_id, task_id, actor, "assigned", to=uid or (f"agent:{agent}" if agent else None))
    for field in ("title", "description", "priority"):
        if field in changes and changes[field] is not None:
            sets.append(f"{field} = :{field}")
            params[field] = changes[field]
            if field == "priority":
                _event(db, m.org_id, task_id, actor, "priority", to=changes[field])
    if "due_date" in changes:
        params["due"] = _check_date(changes["due_date"])
        sets.append("due_date = :due")
        _event(db, m.org_id, task_id, actor, "due", to=params["due"])
    if changes.get("status"):
        sets += ["status = :status", "completed_at = :done"]
        params.update(status=changes["status"], done=_now() if changes["status"] == "done" else None)
        _event(db, m.org_id, task_id, actor, "status", to=changes["status"])
    if sets:
        params["now"] = _now()
        db.execute(text(f"UPDATE org_tasks SET {', '.join(sets)}, updated_at = :now WHERE id = :id"), params)
        db.commit()
    if person and str(changes.get("assignee_user_id")) != actor:
        await _notify({"id": task_id, "title": params.get("title", row.title), "subject_label": row.subject_label, "due_date": row.due_date}, person)
    if changes.get("assignee_agent"):
        await _run_agent(db, m.org_id, task_id)
    return _out(_task(db, m.org_id, task_id))


@router.post("/tasks/{task_id}/comments", status_code=201)
def add_comment(task_id: str, body: CommentBody, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _task(db, m.org_id, task_id)
    _comment(db, m.org_id, task_id, str(m.user_id), body.body.strip())
    db.execute(text("UPDATE org_tasks SET updated_at = :now WHERE id = :id"), {"now": _now(), "id": task_id})
    db.commit()
    return {"status": "added"}


@router.post("/tasks/{task_id}/run")
async def run_task_agent(task_id: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    row = _task(db, m.org_id, task_id)
    if not row.assignee_agent:
        raise HTTPException(status_code=400, detail="This task is assigned to a person, not an agent")
    await _run_agent(db, m.org_id, task_id)
    return _out(_task(db, m.org_id, task_id))
