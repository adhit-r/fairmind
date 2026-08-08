"""Runtime cryptographic verification for evaluation audit history."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Mapping

from sqlalchemy import insert, literal, select, union_all
from sqlalchemy.orm import Session

from database.governance_models import (
    GovernanceEvaluationAuditChainHead,
    GovernanceEvaluationAuditEvent,
)
from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256


class EvaluationAuditChainIntegrityError(RuntimeError):
    """Stored evaluation audit history is not a valid anchored hash chain."""


@dataclass(frozen=True, slots=True)
class EvaluationAuditAppend:
    """Canonical, already-authorized event facts for one chain append."""

    organization_id: str
    actor_id: str
    action: str
    outcome: str
    resource_type: str
    resource_id: str
    details: Mapping[str, object]
    created_at: str
    event_id: str | None = None


@dataclass(frozen=True, slots=True)
class EvaluationAuditReceipt:
    """Integrity identity of an event appended in the caller's transaction."""

    event_id: str
    event_hash: str
    sequence_number: int


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    decoded: dict[str, Any] = {}
    for key, value in pairs:
        if key in decoded:
            raise ValueError("duplicate audit-detail member")
        decoded[key] = value
    return decoded


def _reject_nonfinite(_value: str) -> None:
    raise ValueError("non-finite audit-detail number")


def _canonical_details(raw: object) -> dict[str, Any]:
    if not isinstance(raw, str):
        raise ValueError("audit details must be text")
    decoded = json.loads(
        raw,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_nonfinite,
    )
    if not isinstance(decoded, dict) or canonical_json(decoded) != raw:
        raise ValueError("audit details must be an exact canonical object")
    return decoded


def verify_evaluation_audit_chain(session: Session, *, org_id: str) -> None:
    """Recompute one organization's event chain and compare its anchored head.

    Events and the chain head are loaded by one compound statement so the
    verifier observes one database-statement snapshot while writers append.
    """

    events = GovernanceEvaluationAuditEvent.__table__
    heads = GovernanceEvaluationAuditChainHead.__table__

    event_rows = select(
        literal(0).label("record_order"),
        literal("event").label("record_kind"),
        events.c.id.label("event_id"),
        events.c.org_id.label("organization_id"),
        events.c.sequence_number,
        events.c.actor_id,
        events.c.action,
        events.c.outcome,
        events.c.resource_type,
        events.c.resource_id,
        events.c.details_json,
        events.c.previous_hash,
        events.c.event_hash,
        events.c.created_at,
        literal(None).label("head_sequence_number"),
        literal(None).label("head_event_hash"),
        literal(None).label("head_updated_at"),
    ).where(events.c.org_id == org_id)
    head_rows = select(
        literal(1).label("record_order"),
        literal("head").label("record_kind"),
        literal(None).label("event_id"),
        heads.c.org_id.label("organization_id"),
        literal(None).label("sequence_number"),
        literal(None).label("actor_id"),
        literal(None).label("action"),
        literal(None).label("outcome"),
        literal(None).label("resource_type"),
        literal(None).label("resource_id"),
        literal(None).label("details_json"),
        literal(None).label("previous_hash"),
        literal(None).label("event_hash"),
        literal(None).label("created_at"),
        heads.c.last_sequence_number.label("head_sequence_number"),
        heads.c.last_event_hash.label("head_event_hash"),
        heads.c.updated_at.label("head_updated_at"),
    ).where(heads.c.org_id == org_id)
    snapshot = union_all(event_rows, head_rows).subquery()
    stored_rows = (
        session.execute(
            select(snapshot).order_by(
                snapshot.c.record_order,
                snapshot.c.sequence_number,
            )
        )
        .mappings()
        .all()
    )

    stored_events = [row for row in stored_rows if row["record_kind"] == "event"]
    stored_heads = [row for row in stored_rows if row["record_kind"] == "head"]

    try:
        if len(stored_heads) > 1:
            raise ValueError("multiple organization audit heads")

        previous_hash: str | None = None
        last_created_at: str | None = None
        for expected_sequence, event in enumerate(stored_events, start=1):
            if event["organization_id"] != org_id:
                raise ValueError("event escaped organization scope")
            if event["sequence_number"] != expected_sequence:
                raise ValueError("audit sequence is not contiguous")
            if event["previous_hash"] != previous_hash:
                raise ValueError("audit previous hash is disconnected")

            projection = {
                "eventId": event["event_id"],
                "organizationId": event["organization_id"],
                "sequenceNumber": event["sequence_number"],
                "actorId": event["actor_id"],
                "action": event["action"],
                "outcome": event["outcome"],
                "resourceType": event["resource_type"],
                "resourceId": event["resource_id"],
                "details": _canonical_details(event["details_json"]),
                "previousHash": event["previous_hash"],
                "createdAt": event["created_at"],
            }
            if event["event_hash"] != canonical_sha256(projection):
                raise ValueError("audit event digest does not match its projection")
            previous_hash = event["event_hash"]
            last_created_at = event["created_at"]

        if not stored_events:
            if stored_heads:
                raise ValueError("empty audit chain has an anchored head")
            return
        if len(stored_heads) != 1:
            raise ValueError("non-empty audit chain has no anchored head")

        head = stored_heads[0]
        if (
            head["organization_id"] != org_id
            or head["head_sequence_number"] != len(stored_events)
            or head["head_event_hash"] != previous_hash
            or head["head_updated_at"] != last_created_at
        ):
            raise ValueError("audit head does not match the verified tail")
    except (
        OverflowError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as error:
        raise EvaluationAuditChainIntegrityError from error


def append_evaluation_audit_event(
    session: Session,
    *,
    event: EvaluationAuditAppend,
) -> EvaluationAuditReceipt:
    """Verify and append exactly one event within the caller's transaction.

    The migration-owned trigger is authoritative for advancing the persisted
    head.  This helper rebuilds the same event projection used by the verifier
    and deliberately does not update that head itself.
    """

    verify_evaluation_audit_chain(session, org_id=event.organization_id)
    events = GovernanceEvaluationAuditEvent.__table__
    previous = (
        session.execute(
            select(events.c.sequence_number, events.c.event_hash)
            .where(events.c.org_id == event.organization_id)
            .order_by(events.c.sequence_number.desc())
            .limit(1)
            .with_for_update()
        )
        .mappings()
        .one_or_none()
    )
    sequence = int(previous["sequence_number"]) + 1 if previous else 1
    previous_hash = previous["event_hash"] if previous else None
    if event.event_id is None:
        event_id = str(uuid.uuid4())
    else:
        try:
            if str(uuid.UUID(event.event_id)) != event.event_id:
                raise ValueError("audit event ID is not canonical")
        except (AttributeError, TypeError, ValueError):
            raise ValueError("audit event ID is invalid") from None
        event_id = event.event_id
    details_json = canonical_json(dict(event.details))
    details = _canonical_details(details_json)
    projection = {
        "eventId": event_id,
        "organizationId": event.organization_id,
        "sequenceNumber": sequence,
        "actorId": event.actor_id,
        "action": event.action,
        "outcome": event.outcome,
        "resourceType": event.resource_type,
        "resourceId": event.resource_id,
        "details": details,
        "previousHash": previous_hash,
        "createdAt": event.created_at,
    }
    event_hash = canonical_sha256(projection)
    session.execute(
        insert(events).values(
            id=event_id,
            org_id=event.organization_id,
            sequence_number=sequence,
            actor_id=event.actor_id,
            action=event.action,
            outcome=event.outcome,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            details_json=details_json,
            previous_hash=previous_hash,
            event_hash=event_hash,
            created_at=event.created_at,
        )
    )
    return EvaluationAuditReceipt(
        event_id=event_id,
        event_hash=event_hash,
        sequence_number=sequence,
    )
