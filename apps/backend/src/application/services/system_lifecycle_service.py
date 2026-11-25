"""Recorded changes and retirement for one AI system.

A change names the parts of the system that changed. Each part reopens the gate checks whose evidence it
makes stale: evidence filed before the newest change that reopens a check no longer counts for that check.
A change that reopens nothing is minor. Retirement freezes the file: the system leaves the live estate and
nothing more can be filed against it. Changes and the retirement share one SHA-256 chain per system, so an
edited or deleted record shows as a broken seal.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.services.fairness_run_service import GATE_CHECKS, _record_time, evaluation_status, gate_check

# part key, label, the gate checks it reopens (in gate order)
PARTS: Tuple[Tuple[str, str, Tuple[str, ...]], ...] = (
    ("data", "Data", ("fairness", "data_governance")),
    ("model", "Model", ("fairness", "monitoring", "environmental")),
    ("tools", "Prompts and tools", ("fairness", "human_oversight")),
    ("threshold", "Threshold", ("fairness",)),
    ("use", "Who it is used on", ("fairness", "data_governance", "human_oversight", "monitoring", "environmental")),
    ("docs", "Docs or owner", ()),
)
PART_KEYS = tuple(p[0] for p in PARTS)
_CHECK_ORDER = [c[0] for c in GATE_CHECKS]

REASONS = ("replaced", "not_needed", "failed_review", "rule_changed")

# key, label, who checks it, column on the retire screen. "fairmind" tasks are worked out from records; the
# rest a named person confirms. Nothing here is ticked unless a record or a person says so.
RETIREMENT_TASKS: Tuple[Tuple[str, str, str, str], ...] = (
    ("stopped", "Stopped serving decisions", "person", "wind_down"),
    ("no_pending", "No release request waiting", "fairmind", "wind_down"),
    ("personal_data", "Personal data deleted or kept on a stated basis", "person", "clean_up"),
    ("disconnected", "Removed from registries and integrations", "person", "clean_up"),
    ("told", "People affected are told", "person", "close_out"),
    ("replacement", "Replacement is in the inventory", "fairmind", "close_out"),
)
PERSON_TASKS = tuple(t[0] for t in RETIREMENT_TASKS if t[2] == "person")

# EU AI Act Art. 18: a high-risk system's provider keeps its documentation for 10 years.
HIGH_RISK_RETENTION = (10, "EU AI Act Art. 18: 10 years for a high-risk system")


def reopens(parts: Iterable[str], include_environmental: bool = True) -> List[str]:
    """The gate checks the changed parts reopen, in gate order."""
    hit = {check for key, _, checks in PARTS if key in set(parts) for check in checks}
    return [c for c in _CHECK_ORDER if c in hit and (include_environmental or c != "environmental")]


def suggested_retention(risk_tier: str) -> Optional[Dict[str, Any]]:
    """10 years for a high or critical system; None otherwise, since no rule here sets it and a person must."""
    if str(risk_tier).lower() in ("high", "critical"):
        return {"years": HIGH_RISK_RETENTION[0], "basis": HIGH_RISK_RETENTION[1]}
    return None


def add_years(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year + years)
    except ValueError:  # 29 February
        return day.replace(year=day.year + years, day=28)


def seal(payload: Dict[str, Any], prev: Optional[str]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(f"{prev or ''}|{body}".encode()).hexdigest()


def _parse(raw: Any) -> Optional[datetime]:
    return _record_time({"createdAt": raw}) if raw else None


# ---------------------------------------------------------------------------
# Changes
# ---------------------------------------------------------------------------

_CHANGE_COLS = "id, number, parts_json, reopens_json, material, from_version, to_version, note, gate_before_json, recorded_by, created_at, prev_seal, seal"


def _change_payload(row: Any) -> Dict[str, Any]:
    return {
        "kind": "change", "number": row.number, "parts": json.loads(row.parts_json or "[]"), "reopens": json.loads(row.reopens_json or "[]"),
        "material": bool(row.material), "fromVersion": row.from_version, "toVersion": row.to_version, "note": row.note,
        "gateBefore": json.loads(row.gate_before_json or "[]"), "recordedBy": row.recorded_by, "createdAt": row.created_at,
    }


def list_changes(db: Session, system_id: str) -> List[Any]:
    return db.execute(
        text(f"SELECT {_CHANGE_COLS} FROM governance_system_changes WHERE system_id = :id ORDER BY number"), {"id": system_id}
    ).fetchall()


def reopened_since(db: Session, system_id: str) -> Dict[str, Tuple[datetime, int]]:
    """Per check, the time and number of the newest change that reopened it."""
    out: Dict[str, Tuple[datetime, int]] = {}
    rows = db.execute(
        text("SELECT number, reopens_json, created_at FROM governance_system_changes WHERE system_id = :id AND material ORDER BY number"),
        {"id": system_id},
    ).fetchall()
    for number, reopens_json, created_at in rows:
        at = _parse(created_at)
        if at:
            for check in json.loads(reopens_json or "[]"):
                out[check] = (at, number)
    return out


def drop_superseded(records: List[Dict[str, Any]], since: Dict[str, datetime]) -> List[Dict[str, Any]]:
    """Evidence filed before the change that reopened its check no longer counts; undated evidence goes with it.

    An evaluation run goes stale at the newest material change of any kind, as evaluation_results reads it.
    """
    if not since:
        return records
    newest = max(since.values())
    kept = []
    for record in records:
        cut = newest if evaluation_status(record) else since.get(gate_check(record))
        if cut is not None:
            at = _record_time(record)
            if at is None or at < cut:
                continue
        kept.append(record)
    return kept


def last_seal(db: Session, system_id: str) -> Optional[str]:
    row = db.execute(
        text("SELECT seal FROM governance_system_changes WHERE system_id = :id ORDER BY number DESC LIMIT 1"), {"id": system_id}
    ).fetchone()
    return row[0] if row else None


def record_change(
    db: Session, system_id: str, org_id: Optional[str], *, parts: List[str], to_version: Optional[str], note: Optional[str],
    gate_before: List[Dict[str, Any]], recorded_by: str, include_environmental: bool, now: Optional[datetime] = None,
) -> Dict[str, Any]:
    from src.infrastructure.db.database.governance_models import _new_id

    current = db.execute(text("SELECT version FROM governance_ai_systems WHERE id = :id"), {"id": system_id}).fetchone()
    number = (db.execute(text("SELECT COALESCE(MAX(number), 0) FROM governance_system_changes WHERE system_id = :id"), {"id": system_id}).scalar() or 0) + 1
    reopened = reopens(parts, include_environmental)
    values = {
        "id": _new_id(), "system_id": system_id, "org_id": org_id, "number": number,
        "parts_json": json.dumps([p for p in PART_KEYS if p in set(parts)]), "reopens_json": json.dumps(reopened), "material": bool(reopened),
        "from_version": current[0] if current else None, "to_version": to_version, "note": note,
        "gate_before_json": json.dumps(gate_before), "recorded_by": recorded_by,
        "created_at": (now or datetime.now(timezone.utc)).isoformat(), "prev_seal": last_seal(db, system_id),
    }

    row = SimpleNamespace(**values)  # the shape list_changes returns, so the seal is computed one way
    values["seal"] = seal(_change_payload(row), values["prev_seal"])
    db.execute(
        text(
            "INSERT INTO governance_system_changes (id, system_id, org_id, number, parts_json, reopens_json, material, from_version, to_version, "
            "note, gate_before_json, recorded_by, created_at, prev_seal, seal) VALUES (:id, :system_id, :org_id, :number, :parts_json, :reopens_json, "
            ":material, :from_version, :to_version, :note, :gate_before_json, :recorded_by, :created_at, :prev_seal, :seal)"
        ),
        values,
    )
    if to_version:
        db.execute(text("UPDATE governance_ai_systems SET version = :v, updated_at = :at WHERE id = :id"), {"v": to_version, "at": values["created_at"], "id": system_id})
    db.commit()
    return {**_change_payload(row), "seal": values["seal"]}


# ---------------------------------------------------------------------------
# Retirement
# ---------------------------------------------------------------------------

_RET_COLS = "reason, replaced_by, last_day, tasks_json, retain_until, retain_basis, note, gate_snapshot_json, retired_by, retired_at, prev_seal, seal"


def _retirement_payload(row: Any) -> Dict[str, Any]:
    return {
        "kind": "retirement", "reason": row.reason, "replacedBy": row.replaced_by, "lastDay": row.last_day, "tasks": json.loads(row.tasks_json or "[]"),
        "retainUntil": row.retain_until, "retainBasis": row.retain_basis, "note": row.note, "gateSnapshot": json.loads(row.gate_snapshot_json or "[]"),
        "retiredBy": row.retired_by, "retiredAt": row.retired_at,
    }


def get_retirement(db: Session, system_id: str) -> Optional[Any]:
    return db.execute(text(f"SELECT {_RET_COLS} FROM governance_system_retirements WHERE system_id = :id"), {"id": system_id}).fetchone()


def computed_tasks(db: Session, system_id: str, org_id: Optional[str], reason: Optional[str], replaced_by: Optional[str]) -> Dict[str, Optional[bool]]:
    """The tasks FairMind works out from records. None means the task does not apply."""
    pending = db.execute(
        text("SELECT 1 FROM governance_approval_requests WHERE entity_type = 'ai_system' AND entity_id = :id AND status = 'pending' LIMIT 1"),
        {"id": system_id},
    ).fetchone()
    replacement: Optional[bool] = None
    if reason == "replaced":
        replacement = bool(replaced_by) and replaced_by != system_id and bool(db.execute(
            text("SELECT 1 FROM governance_ai_systems WHERE id = :r AND org_id = :org AND COALESCE(lifecycle_stage, '') <> 'retired'"),
            {"r": replaced_by, "org": org_id},
        ).fetchone())
    return {"no_pending": pending is None, "replacement": replacement}


def verify_chain(db: Session, system_id: str) -> Dict[str, Any]:
    """Recompute every seal in order; one edited, deleted or reordered record breaks the chain from there on."""
    prev = None
    for row in list_changes(db, system_id):
        if row.prev_seal != prev or seal(_change_payload(row), prev) != row.seal:
            return {"status": "broken", "at": f"change {row.number}"}
        prev = row.seal
    ret = get_retirement(db, system_id)
    if ret is not None and (ret.prev_seal != prev or seal(_retirement_payload(ret), prev) != ret.seal):
        return {"status": "broken", "at": "retirement"}
    return {"status": "intact", "head": ret.seal if ret is not None else prev}


def retire(
    db: Session, system_id: str, org_id: Optional[str], *, reason: str, replaced_by: Optional[str], last_day: date, retain_years: int,
    retain_basis: Optional[str], note: Optional[str], gate_snapshot: List[Dict[str, Any]], tasks: List[Dict[str, Any]], retired_by: str,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    values = {
        "system_id": system_id, "org_id": org_id, "reason": reason, "replaced_by": replaced_by, "last_day": last_day.isoformat(),
        "tasks_json": json.dumps(tasks), "retain_until": add_years(last_day, retain_years).isoformat(), "retain_basis": retain_basis, "note": note,
        "gate_snapshot_json": json.dumps(gate_snapshot), "retired_by": retired_by, "retired_at": (now or datetime.now(timezone.utc)).isoformat(),
        "prev_seal": last_seal(db, system_id),
    }

    row = SimpleNamespace(**values)
    values["seal"] = seal(_retirement_payload(row), values["prev_seal"])
    db.execute(
        text(
            "INSERT INTO governance_system_retirements (system_id, org_id, reason, replaced_by, last_day, tasks_json, retain_until, retain_basis, note, "
            "gate_snapshot_json, retired_by, retired_at, prev_seal, seal) VALUES (:system_id, :org_id, :reason, :replaced_by, :last_day, :tasks_json, "
            ":retain_until, :retain_basis, :note, :gate_snapshot_json, :retired_by, :retired_at, :prev_seal, :seal)"
        ),
        values,
    )
    db.execute(
        text("UPDATE governance_ai_systems SET lifecycle_stage = 'retired', status = 'retired', updated_at = :at WHERE id = :id"),
        {"at": values["retired_at"], "id": system_id},
    )
    db.commit()
    return {**_retirement_payload(row), "seal": values["seal"]}
