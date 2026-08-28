"""Rejected mutation audit-chain behavior for the evaluation workbench UoW."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event, func, select, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base
from database.governance_models import (
    GovernanceEvaluationAuditEvent,
    GovernanceIdempotencyRecord,
    GovernanceWorkspace,
)
from database.models import Organization, OrganizationMember, User
from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationCommand,
    MutationOutcome,
)
from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256
from src.infrastructure.db.repositories import (
    evaluation_workbench_repository as workbench_repository_module,
)
from src.infrastructure.db.repositories.evaluation_audit_chain import (
    EvaluationAuditAppend,
    append_evaluation_audit_event,
    verify_evaluation_audit_chain,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)
from tests.evaluation_workbench_sqlite import (
    install_authoritative_assurance_fixtures_for_application_verifier_harness,
)

ORG = str(uuid.uuid4())
OTHER_ORG = str(uuid.uuid4())
ACTOR = str(uuid.uuid4())


@pytest.fixture
def audit_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys = ON")

    Base.metadata.create_all(engine)
    install_authoritative_assurance_fixtures_for_application_verifier_harness(engine)
    session = sessionmaker(bind=engine)()
    actor_uuid = uuid.UUID(ACTOR)
    session.execute(
        User.__table__.insert().values(
            id=actor_uuid,
            email="audit-actor@example.test",
            username=ACTOR,
        )
    )
    for organization_id in (ORG, OTHER_ORG):
        session.execute(
            Organization.__table__.insert().values(
                id=uuid.UUID(organization_id),
                name=organization_id,
                slug=organization_id,
                owner_id=actor_uuid,
            )
        )
        session.execute(
            OrganizationMember.__table__.insert().values(
                id=uuid.uuid4(),
                org_id=uuid.UUID(organization_id),
                user_id=actor_uuid,
                role="admin",
                status="active",
            )
        )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _command(
    *,
    org_id: str = ORG,
    key: str = "rejected-key",
    request_hash: str = "a" * 64,
) -> MutationCommand:
    return MutationCommand(
        organization_id=org_id,
        actor_id=ACTOR,
        operation="evaluation-v2.test.mutation",
        idempotency_key=key,
        request_hash=request_hash,
    )


def _success_outcome(
    *,
    resource_id: str = "success-resource",
    audit_action: str | None = "evaluation_v2.test.succeeded",
    body: dict[str, object] | None = None,
    audit_details: dict[str, object] | None = None,
) -> MutationOutcome:
    return MutationOutcome(
        body=FrozenJsonObject.from_mapping(body or {"id": resource_id}),
        status=201,
        resource_type="evaluation_test_resource",
        resource_id=resource_id,
        audit_action=audit_action,
        audit_details=FrozenJsonObject.from_mapping(audit_details or {"kind": "test"}),
    )


def _rejected_callback(
    session,
    *,
    org_id: str = ORG,
    workspace_id: str = "rolled-back-workspace",
):
    def callback(_now):
        session.execute(
            GovernanceWorkspace.__table__.insert().values(
                id=workspace_id,
                org_id=org_id,
                name="Must roll back",
            )
        )
        raise EvaluationWorkbenchError(
            "test_rejected",
            "Sensitive message must not enter the audit payload.",
            status_code=422,
            details={"secret": "never-audit", "submitted": {"token": "never"}},
        )

    return callback


def _events(session, org_id: str = ORG):
    return (
        session.execute(
            select(GovernanceEvaluationAuditEvent.__table__)
            .where(GovernanceEvaluationAuditEvent.org_id == org_id)
            .order_by(GovernanceEvaluationAuditEvent.sequence_number)
        )
        .mappings()
        .all()
    )


def _idempotency_record(session, *, key: str):
    return (
        session.execute(
            select(GovernanceIdempotencyRecord.__table__).where(
                GovernanceIdempotencyRecord.key_hash
                == hashlib.sha256(key.encode("ascii")).hexdigest()
            )
        )
        .mappings()
        .one()
    )


def test_success_replay_is_bound_to_the_exact_success_audit_receipt(
    audit_session,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command(key="bound-success")

    created = unit_of_work.mutate(command, lambda _now: _success_outcome())
    replay = unit_of_work.mutate(
        command,
        lambda _now: pytest.fail("bound success replay must not execute callback"),
    )

    assert replay.body == created.body == {"id": "success-resource"}
    assert replay.status == created.status == 201
    assert replay.replayed is True
    record = _idempotency_record(audit_session, key="bound-success")
    event_row = _events(audit_session)[0]
    assert record["resource_type"] == "evaluation_test_resource"
    assert record["resource_id"] == "success-resource"
    assert event_row["resource_type"] == "evaluation_test_resource"
    assert event_row["resource_id"] == "success-resource"
    assert json.loads(record["response_body_json"]) == {
        "_fairmindEvaluationMutationSucceeded": True,
        "auditEventId": event_row["id"],
        "responseBody": {"id": "success-resource"},
    }
    assert json.loads(event_row["details_json"]) == {
        "_fairmindEvaluationSuccessBinding": {
            "schemaVersion": "evaluation-v2.success-idempotency-audit/v1",
            "auditEventId": event_row["id"],
            "idempotencyRecordId": record["id"],
            "idempotencyKeyHash": hashlib.sha256(b"bound-success").hexdigest(),
            "operation": "evaluation-v2.test.mutation",
            "requestHash": "a" * 64,
            "claimedAt": record["created_at"],
            "expiresAt": record["expires_at"],
            "resourceType": "evaluation_test_resource",
            "resourceId": "success-resource",
            "responseStatus": 201,
            "responseHash": canonical_sha256(
                {
                    "schemaVersion": "evaluation-v2.success-idempotency-response/v1",
                    "auditEventId": event_row["id"],
                    "claimedAt": record["created_at"],
                    "expiresAt": record["expires_at"],
                    "resourceType": "evaluation_test_resource",
                    "resourceId": "success-resource",
                    "responseStatus": 201,
                    "responseBody": {"id": "success-resource"},
                }
            ),
            "action": "evaluation_v2.test.succeeded",
            "domainDetails": {"kind": "test"},
        },
    }


def test_preclaim_idempotency_conflict_appends_redacted_audit_without_rebinding_record(
    audit_session,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    key = "preclaim-conflict-secret-key"
    original_command = _command(key=key, request_hash="a" * 64)
    unit_of_work.mutate(original_command, lambda _now: _success_outcome())
    original_record = dict(_idempotency_record(audit_session, key=key))

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(
            _command(key=key, request_hash="b" * 64),
            lambda _now: pytest.fail("conflicting request must not execute callback"),
        )

    assert caught.value.code == "idempotency_conflict"
    assert dict(_idempotency_record(audit_session, key=key)) == original_record
    rows = _events(audit_session)
    assert len(rows) == 2
    assert rows[1]["previous_hash"] == rows[0]["event_hash"]
    assert rows[1]["action"] == "evaluation_v2.mutation.rejected"
    assert rows[1]["outcome"] == "rejected"
    assert rows[1]["resource_type"] == "evaluation_idempotency_key_hash"
    assert rows[1]["resource_id"] == hashlib.sha256(key.encode("ascii")).hexdigest()
    assert json.loads(rows[1]["details_json"]) == {
        "schemaVersion": "evaluation-v2.preclaim-rejection-audit/v1",
        "operation": "evaluation-v2.test.mutation",
        "requestHash": "b" * 64,
        "errorCode": "idempotency_conflict",
        "statusCode": 409,
    }
    assert key not in rows[1]["details_json"]
    assert "different request" not in rows[1]["details_json"]
    verify_evaluation_audit_chain(audit_session, org_id=ORG)


def test_preclaim_idempotency_in_progress_appends_redacted_audit_without_rebinding_record(
    audit_session,
) -> None:
    key = "preclaim-in-progress-secret-key"
    claimed_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    audit_session.execute(
        GovernanceIdempotencyRecord.__table__.insert().values(
            id=str(uuid.uuid4()),
            org_id=ORG,
            actor_id=ACTOR,
            operation="evaluation-v2.test.mutation",
            key_hash=hashlib.sha256(key.encode("ascii")).hexdigest(),
            request_hash="a" * 64,
            status="in_progress",
            created_at=claimed_at.isoformat(),
            updated_at=claimed_at.isoformat(),
            expires_at=(claimed_at + timedelta(days=30)).isoformat(),
        )
    )
    audit_session.commit()
    original_record = dict(_idempotency_record(audit_session, key=key))

    with pytest.raises(EvaluationWorkbenchError) as caught:
        SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session).mutate(
            _command(key=key, request_hash="a" * 64),
            lambda _now: pytest.fail("in-progress request must not execute callback"),
        )

    assert caught.value.code == "idempotency_in_progress"
    assert dict(_idempotency_record(audit_session, key=key)) == original_record
    rows = _events(audit_session)
    assert len(rows) == 1
    assert rows[0]["action"] == "evaluation_v2.mutation.rejected"
    assert rows[0]["outcome"] == "rejected"
    assert rows[0]["resource_type"] == "evaluation_idempotency_key_hash"
    assert rows[0]["resource_id"] == hashlib.sha256(key.encode("ascii")).hexdigest()
    assert json.loads(rows[0]["details_json"]) == {
        "schemaVersion": "evaluation-v2.preclaim-rejection-audit/v1",
        "operation": "evaluation-v2.test.mutation",
        "requestHash": "a" * 64,
        "errorCode": "idempotency_in_progress",
        "statusCode": 409,
    }
    assert key not in rows[0]["details_json"]
    assert "still in progress" not in rows[0]["details_json"]
    verify_evaluation_audit_chain(audit_session, org_id=ORG)


def test_success_replay_accepts_a_domain_valid_response_above_binding_item_limit(
    audit_session,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command(key="large-domain-valid-success")
    body = {"checks": [False] * 10_001}

    created = unit_of_work.mutate(
        command,
        lambda _now: _success_outcome(body=body),
    )
    replay = unit_of_work.mutate(
        command,
        lambda _now: pytest.fail("large bound success must replay without callback"),
    )

    assert created.body == body
    assert replay.body == body
    assert replay.status == 201
    assert replay.replayed is True


def test_success_with_unreplayable_domain_details_rolls_back_atomically(
    audit_session,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(
            _command(key="unreplayable-domain-details"),
            lambda _now: _success_outcome(
                audit_details={"checks": [False] * 10_001},
            ),
        )

    assert caught.value.code == "evaluation_persistence_failed"
    assert audit_session.scalar(select(func.count()).select_from(GovernanceIdempotencyRecord)) == 0
    assert (
        audit_session.scalar(select(func.count()).select_from(GovernanceEvaluationAuditEvent)) == 0
    )


@pytest.mark.parametrize("outcome", ["success", "rejected"])
def test_replay_requires_event_time_to_equal_claim_time(
    audit_session,
    outcome: str,
) -> None:
    command = _command(key=f"mismatched-event-time-{outcome}")
    record_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    claimed_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    expires_at = claimed_at + timedelta(days=30)
    event_time = claimed_at + timedelta(seconds=1)
    key_hash = hashlib.sha256(command.idempotency_key.encode("ascii")).hexdigest()

    if outcome == "success":
        response_status = 201
        response_body = {"id": "chronology-resource"}
        response_hash = canonical_sha256(
            {
                "schemaVersion": "evaluation-v2.success-idempotency-response/v1",
                "auditEventId": event_id,
                "claimedAt": claimed_at.isoformat(),
                "expiresAt": expires_at.isoformat(),
                "resourceType": "evaluation_test_resource",
                "resourceId": "chronology-resource",
                "responseStatus": response_status,
                "responseBody": response_body,
            }
        )
        stored_body = canonical_json(
            {
                "_fairmindEvaluationMutationSucceeded": True,
                "auditEventId": event_id,
                "responseBody": response_body,
            }
        )
        resource_type = "evaluation_test_resource"
        resource_id = "chronology-resource"
        action = "evaluation_v2.test.succeeded"
        event_outcome = "success"
        event_resource_type = resource_type
        event_resource_id = resource_id
        details = {
            "_fairmindEvaluationSuccessBinding": {
                "schemaVersion": "evaluation-v2.success-idempotency-audit/v1",
                "auditEventId": event_id,
                "idempotencyRecordId": record_id,
                "idempotencyKeyHash": key_hash,
                "operation": command.operation,
                "requestHash": command.request_hash,
                "claimedAt": claimed_at.isoformat(),
                "expiresAt": expires_at.isoformat(),
                "resourceType": resource_type,
                "resourceId": resource_id,
                "responseStatus": response_status,
                "responseHash": response_hash,
                "action": action,
                "domainDetails": {"kind": "test"},
            }
        }
    else:
        response_status = 422
        error_body = {
            "code": "test_rejected",
            "message": "The test mutation was rejected.",
        }
        response_body = {
            "_fairmindEvaluationMutationRejected": True,
            "error": error_body,
        }
        response_hash = canonical_sha256(
            {
                "schemaVersion": "evaluation-v2.rejected-idempotency-response/v2",
                "claimedAt": claimed_at.isoformat(),
                "expiresAt": expires_at.isoformat(),
                "responseStatus": response_status,
                "responseBody": response_body,
            }
        )
        stored_body = canonical_json(response_body)
        resource_type = "evaluation_rejected_audit_event"
        resource_id = event_id
        action = "evaluation_v2.mutation.rejected"
        event_outcome = "rejected"
        event_resource_type = "evaluation_idempotency_key_hash"
        event_resource_id = key_hash
        details = {
            "schemaVersion": "evaluation-v2.rejected-mutation-audit/v2",
            "operation": command.operation,
            "requestHash": command.request_hash,
            "claimedAt": claimed_at.isoformat(),
            "expiresAt": expires_at.isoformat(),
            "errorCode": "test_rejected",
            "statusCode": response_status,
            "responseHash": response_hash,
        }

    append_evaluation_audit_event(
        audit_session,
        event=EvaluationAuditAppend(
            organization_id=command.organization_id,
            actor_id=command.actor_id,
            action=action,
            outcome=event_outcome,
            resource_type=event_resource_type,
            resource_id=event_resource_id,
            details=details,
            created_at=event_time.isoformat(),
            event_id=event_id,
        ),
    )
    audit_session.execute(
        GovernanceIdempotencyRecord.__table__.insert().values(
            id=record_id,
            org_id=command.organization_id,
            actor_id=command.actor_id,
            operation=command.operation,
            key_hash=key_hash,
            request_hash=command.request_hash,
            status="completed",
            response_status=response_status,
            response_body_json=stored_body,
            resource_type=resource_type,
            resource_id=resource_id,
            created_at=claimed_at.isoformat(),
            updated_at=claimed_at.isoformat(),
            expires_at=expires_at.isoformat(),
        )
    )
    audit_session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session).mutate(
            command,
            lambda _now: pytest.fail("chronology mismatch must not replay"),
        )

    assert caught.value.code == "idempotency_response_invalid"


@pytest.mark.parametrize(
    ("column", "value"),
    [
        (
            "response_body_json",
            canonical_json(
                {
                    "_fairmindEvaluationMutationSucceeded": True,
                    "auditEventId": "00000000-0000-0000-0000-000000000000",
                    "responseBody": {"id": "forged-success"},
                }
            ),
        ),
        ("response_status", 200),
        ("resource_type", "evaluation_other_resource"),
        ("resource_id", str(uuid.uuid4())),
    ],
)
def test_safe_success_response_or_receipt_tampering_cannot_replay(
    audit_session,
    column: str,
    value: object,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command(key="tampered-success")
    unit_of_work.mutate(command, lambda _now: _success_outcome())
    record = _idempotency_record(audit_session, key="tampered-success")
    audit_session.execute(
        update(GovernanceIdempotencyRecord.__table__)
        .where(GovernanceIdempotencyRecord.id == record["id"])
        .values(**{column: value})
    )
    audit_session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(
            command,
            lambda _now: pytest.fail("tampered success must not execute callback"),
        )

    assert caught.value.code == "idempotency_response_invalid"
    assert len(_events(audit_session)) == 1


def test_success_receipt_cannot_be_rebound_to_another_valid_event(audit_session) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    first_command = _command(key="first-success-binding")
    second_command = _command(key="second-success-binding")
    unit_of_work.mutate(
        first_command,
        lambda _now: _success_outcome(resource_id="first-resource"),
    )
    unit_of_work.mutate(
        second_command,
        lambda _now: _success_outcome(resource_id="second-resource"),
    )
    first_record = _idempotency_record(audit_session, key="first-success-binding")
    second_record = _idempotency_record(audit_session, key="second-success-binding")
    second_wrapper = json.loads(second_record["response_body_json"])
    audit_session.execute(
        update(GovernanceIdempotencyRecord.__table__)
        .where(GovernanceIdempotencyRecord.id == first_record["id"])
        .values(
            response_body_json=canonical_json(
                {
                    "_fairmindEvaluationMutationSucceeded": True,
                    "auditEventId": second_wrapper["auditEventId"],
                    "responseBody": {"id": "first-resource"},
                }
            )
        )
    )
    audit_session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(
            first_command,
            lambda _now: pytest.fail("rebound success must not execute callback"),
        )

    assert caught.value.code == "idempotency_response_invalid"
    assert len(_events(audit_session)) == 2


@pytest.mark.parametrize("expired", [False, True])
def test_legacy_unbound_completed_success_fails_closed(
    audit_session,
    expired: bool,
) -> None:
    command = _command(key=f"legacy-unbound-success-{expired}")
    now = datetime.now(timezone.utc)
    claimed_at = now - timedelta(days=31) if expired else now
    audit_session.execute(
        GovernanceIdempotencyRecord.__table__.insert().values(
            id=str(uuid.uuid4()),
            org_id=command.organization_id,
            actor_id=command.actor_id,
            operation=command.operation,
            key_hash=hashlib.sha256(command.idempotency_key.encode("ascii")).hexdigest(),
            request_hash=command.request_hash,
            status="completed",
            response_status=201,
            response_body_json=canonical_json({"id": "legacy-resource"}),
            resource_type="evaluation_test_resource",
            resource_id="legacy-resource",
            created_at=claimed_at.isoformat(),
            updated_at=claimed_at.isoformat(),
            expires_at=(claimed_at + timedelta(days=30)).isoformat(),
        )
    )
    audit_session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session).mutate(
            command,
            lambda _now: pytest.fail("unbound legacy success must not execute callback"),
        )

    assert caught.value.code == "idempotency_response_invalid"
    assert (
        _idempotency_record(
            audit_session,
            key=f"legacy-unbound-success-{expired}",
        )["status"]
        == "completed"
    )
    assert len(_events(audit_session)) == 0


def test_task10_v1_rejection_fails_closed_without_callback(audit_session) -> None:
    command = _command(key="task10-v1-rejection")
    record_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    claimed_at = datetime.now(timezone.utc)
    expires_at = claimed_at + timedelta(days=30)
    key_hash = hashlib.sha256(command.idempotency_key.encode("ascii")).hexdigest()
    response_status = 422
    response_body = {
        "_fairmindEvaluationMutationRejected": True,
        "error": {
            "code": "evaluation_rejected",
            "message": "The assurance mutation was rejected.",
        },
    }
    response_hash = canonical_sha256(
        {
            "schemaVersion": "evaluation-v2.rejected-idempotency-response/v1",
            "responseStatus": response_status,
            "responseBody": response_body,
        }
    )
    append_evaluation_audit_event(
        audit_session,
        event=EvaluationAuditAppend(
            organization_id=command.organization_id,
            actor_id=command.actor_id,
            action="evaluation_v2.mutation.rejected",
            outcome="rejected",
            resource_type="evaluation_idempotency_key_hash",
            resource_id=key_hash,
            details={
                "schemaVersion": "evaluation-v2.rejected-mutation-audit/v1",
                "operation": command.operation,
                "requestHash": command.request_hash,
                "claimedAt": claimed_at.isoformat(),
                "errorCode": "evaluation_rejected",
                "statusCode": response_status,
                "responseHash": response_hash,
            },
            created_at=claimed_at.isoformat(),
            event_id=event_id,
        ),
    )
    audit_session.execute(
        GovernanceIdempotencyRecord.__table__.insert().values(
            id=record_id,
            org_id=command.organization_id,
            actor_id=command.actor_id,
            operation=command.operation,
            key_hash=key_hash,
            request_hash=command.request_hash,
            status="completed",
            response_status=response_status,
            response_body_json=canonical_json(response_body),
            resource_type="evaluation_rejected_audit_event",
            resource_id=event_id,
            created_at=claimed_at.isoformat(),
            updated_at=claimed_at.isoformat(),
            expires_at=expires_at.isoformat(),
        )
    )
    audit_session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session).mutate(
            command,
            lambda _now: pytest.fail("legacy rejection must not execute callback"),
        )

    assert caught.value.code == "idempotency_response_invalid"
    assert len(_events(audit_session)) == 1


def test_successful_noop_receives_a_distinct_integrity_event(audit_session) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command(key="successful-noop")

    created = unit_of_work.mutate(
        command,
        lambda _now: _success_outcome(audit_action=None),
    )
    replay = unit_of_work.mutate(
        command,
        lambda _now: pytest.fail("successful no-op must replay without callback"),
    )

    assert created.body == replay.body == {"id": "success-resource"}
    assert replay.replayed is True
    event_row = _events(audit_session)[0]
    assert event_row["action"] == "evaluation_v2.mutation.noop"
    assert event_row["outcome"] == "success"
    record = _idempotency_record(audit_session, key="successful-noop")
    assert record["resource_id"] == "success-resource"
    assert json.loads(record["response_body_json"])["auditEventId"] == event_row["id"]


@pytest.mark.parametrize(
    "outcome",
    [
        _success_outcome(
            body={
                "id": "success-resource",
                "_fairmindEvaluationMutationRejected": True,
            }
        ),
        _success_outcome(
            body={
                "id": "success-resource",
                "_fairmindEvaluationMutationSucceeded": True,
            }
        ),
        _success_outcome(
            audit_details={
                "kind": "test",
                "_fairmindEvaluationSuccessBinding": {"forged": True},
            }
        ),
    ],
)
def test_success_rejects_reserved_internal_binding_members(
    audit_session,
    outcome: MutationOutcome,
) -> None:
    with pytest.raises(EvaluationWorkbenchError) as caught:
        SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session).mutate(
            _command(key=f"reserved-success-{uuid.uuid4()}"),
            lambda _now: outcome,
        )

    assert caught.value.code == "evaluation_persistence_failed"
    assert len(_events(audit_session)) == 0
    assert audit_session.scalar(select(func.count()).select_from(GovernanceIdempotencyRecord)) == 0


def test_rejected_callback_rolls_back_business_work_and_commits_one_redacted_event(
    audit_session,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(_command(), _rejected_callback(audit_session))

    assert caught.value.detail() == {
        "code": "evaluation_rejected",
        "message": "The assurance mutation was rejected.",
    }
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert (
        audit_session.execute(
            select(GovernanceWorkspace.__table__).where(
                GovernanceWorkspace.id == "rolled-back-workspace"
            )
        )
        .mappings()
        .one_or_none()
        is None
    )
    rows = _events(audit_session)
    assert len(rows) == 1
    assert rows[0]["outcome"] == "rejected"
    assert rows[0]["action"] == "evaluation_v2.mutation.rejected"
    assert rows[0]["resource_type"] == "evaluation_idempotency_key_hash"
    assert rows[0]["resource_id"] == hashlib.sha256(b"rejected-key").hexdigest()
    expected_response_body = {
        "_fairmindEvaluationMutationRejected": True,
        "error": {
            "code": "evaluation_rejected",
            "message": "The assurance mutation was rejected.",
        },
    }
    record = audit_session.execute(select(GovernanceIdempotencyRecord.__table__)).mappings().one()
    assert json.loads(rows[0]["details_json"]) == {
        "schemaVersion": "evaluation-v2.rejected-mutation-audit/v2",
        "operation": "evaluation-v2.test.mutation",
        "requestHash": "a" * 64,
        "claimedAt": record["created_at"],
        "expiresAt": record["expires_at"],
        "errorCode": "evaluation_rejected",
        "statusCode": 422,
        "responseHash": canonical_sha256(
            {
                "schemaVersion": "evaluation-v2.rejected-idempotency-response/v2",
                "claimedAt": record["created_at"],
                "expiresAt": record["expires_at"],
                "responseStatus": 422,
                "responseBody": expected_response_body,
            }
        ),
    }
    assert record["status"] == "completed"
    assert record["resource_type"] == "evaluation_rejected_audit_event"
    assert record["resource_id"] == rows[0]["id"]
    assert "Sensitive message" not in record["response_body_json"]
    assert "never-audit" not in record["response_body_json"]
    assert "token" not in record["response_body_json"]


def test_rejected_idempotency_replay_reraises_same_error_without_second_event(
    audit_session,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command()

    with pytest.raises(EvaluationWorkbenchError) as first:
        unit_of_work.mutate(command, _rejected_callback(audit_session))
    with pytest.raises(EvaluationWorkbenchError) as replay:
        unit_of_work.mutate(
            command,
            lambda _now: pytest.fail("rejected idempotency callback must not replay"),
        )

    assert replay.value.detail() == first.value.detail()
    assert len(_events(audit_session)) == 1


def test_expired_rejected_key_can_be_reclaimed_then_successfully_replayed(
    audit_session,
    monkeypatch,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command()
    with pytest.raises(EvaluationWorkbenchError):
        unit_of_work.mutate(command, _rejected_callback(audit_session))
    original_claimed_at = audit_session.scalar(
        select(GovernanceIdempotencyRecord.__table__.c.created_at)
    )
    original_expiry = audit_session.scalar(
        select(GovernanceIdempotencyRecord.__table__.c.expires_at)
    )
    after_expiry = datetime.fromisoformat(original_expiry) + timedelta(seconds=1)
    monkeypatch.setattr(workbench_repository_module, "_now", lambda: after_expiry)

    next_command = _command(key="rejected-key", request_hash="b" * 64)
    created = unit_of_work.mutate(next_command, lambda _now: _success_outcome())
    replay = unit_of_work.mutate(
        next_command,
        lambda _now: pytest.fail("completed success must replay without callback"),
    )

    assert created.status == 201
    assert replay.status == 201
    assert replay.body == created.body
    assert replay.replayed is True
    reclaimed_at = audit_session.scalar(select(GovernanceIdempotencyRecord.__table__.c.created_at))
    assert reclaimed_at != original_claimed_at
    record = _idempotency_record(audit_session, key="rejected-key")
    assert datetime.fromisoformat(record["expires_at"]) == (
        datetime.fromisoformat(record["created_at"]) + timedelta(days=30)
    )
    assert [row["outcome"] for row in _events(audit_session)] == [
        "rejected",
        "success",
    ]


def test_expired_success_can_be_reclaimed_as_a_rejection_without_old_replay(
    audit_session,
    monkeypatch,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command(key="success-then-rejected")
    created = unit_of_work.mutate(command, lambda _now: _success_outcome())
    original_record = dict(_idempotency_record(audit_session, key="success-then-rejected"))
    original_wrapper = json.loads(original_record["response_body_json"])
    after_expiry = datetime.fromisoformat(original_record["expires_at"]) + timedelta(seconds=1)
    monkeypatch.setattr(workbench_repository_module, "_now", lambda: after_expiry)

    next_command = _command(key="success-then-rejected", request_hash="b" * 64)
    with pytest.raises(EvaluationWorkbenchError) as reclaimed:
        unit_of_work.mutate(next_command, _rejected_callback(audit_session))
    with pytest.raises(EvaluationWorkbenchError) as replay:
        unit_of_work.mutate(
            next_command,
            lambda _now: pytest.fail("latest rejected generation must replay"),
        )

    assert created.body == {"id": "success-resource"}
    assert reclaimed.value.code == replay.value.code == "evaluation_rejected"
    current_record = _idempotency_record(audit_session, key="success-then-rejected")
    assert current_record["created_at"] > original_record["created_at"]
    assert current_record["resource_type"] == "evaluation_rejected_audit_event"
    rows = _events(audit_session)
    assert [row["outcome"] for row in rows] == ["success", "rejected"]
    assert original_wrapper["auditEventId"] == rows[0]["id"]
    assert current_record["resource_id"] == rows[1]["id"]


@pytest.mark.parametrize("lifecycle", ["success", "rejected"])
def test_tampered_completed_expiry_cannot_force_callback_reexecution(
    audit_session,
    lifecycle: str,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command(key=f"tampered-expiry-{lifecycle}")
    if lifecycle == "success":
        unit_of_work.mutate(command, lambda _now: _success_outcome())
    else:
        with pytest.raises(EvaluationWorkbenchError):
            unit_of_work.mutate(command, _rejected_callback(audit_session))
    record = _idempotency_record(audit_session, key=f"tampered-expiry-{lifecycle}")
    audit_session.execute(
        update(GovernanceIdempotencyRecord.__table__)
        .where(GovernanceIdempotencyRecord.id == record["id"])
        .values(expires_at="2000-01-01T00:00:00+00:00")
    )
    audit_session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(
            command,
            lambda _now: pytest.fail("tampered expiry must not re-execute callback"),
        )

    assert caught.value.code == "idempotency_response_invalid"
    assert len(_events(audit_session)) == 1


def test_tampered_in_progress_expiry_cannot_force_callback_execution(
    audit_session,
    monkeypatch,
) -> None:
    command = _command(key="tampered-in-progress-expiry")
    observed_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    previous_claim = datetime(2025, 12, 31, tzinfo=timezone.utc)
    audit_session.execute(
        GovernanceIdempotencyRecord.__table__.insert().values(
            id=str(uuid.uuid4()),
            org_id=command.organization_id,
            actor_id=command.actor_id,
            operation=command.operation,
            key_hash=hashlib.sha256(command.idempotency_key.encode("ascii")).hexdigest(),
            request_hash="c" * 64,
            status="in_progress",
            created_at=previous_claim.isoformat(),
            updated_at=previous_claim.isoformat(),
            expires_at="2000-01-01T00:00:00+00:00",
        )
    )
    audit_session.commit()
    monkeypatch.setattr(workbench_repository_module, "_now", lambda: observed_now)

    with pytest.raises(EvaluationWorkbenchError) as caught:
        SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session).mutate(
            command,
            lambda _claimed_at: pytest.fail("tampered expiry must not execute callback"),
        )

    assert caught.value.code == "idempotency_response_invalid"
    assert _events(audit_session) == []


def test_expired_in_progress_generation_is_reclaimed_for_exactly_thirty_days(
    audit_session,
    monkeypatch,
) -> None:
    command = _command(key="expired-in-progress-generation")
    previous_claim = datetime(2025, 1, 1, tzinfo=timezone.utc)
    observed_now = previous_claim + timedelta(days=31)
    audit_session.execute(
        GovernanceIdempotencyRecord.__table__.insert().values(
            id=str(uuid.uuid4()),
            org_id=command.organization_id,
            actor_id=command.actor_id,
            operation=command.operation,
            key_hash=hashlib.sha256(command.idempotency_key.encode("ascii")).hexdigest(),
            request_hash="c" * 64,
            status="in_progress",
            created_at=previous_claim.isoformat(),
            updated_at=previous_claim.isoformat(),
            expires_at=(previous_claim + timedelta(days=30)).isoformat(),
        )
    )
    audit_session.commit()
    monkeypatch.setattr(workbench_repository_module, "_now", lambda: observed_now)

    result = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session).mutate(
        command,
        lambda _claimed_at: _success_outcome(),
    )

    record = _idempotency_record(audit_session, key="expired-in-progress-generation")
    assert result.status == 201
    assert record["created_at"] == observed_now.isoformat()
    assert record["expires_at"] == (observed_now + timedelta(days=30)).isoformat()


def test_tampered_rejected_idempotency_response_fails_closed_without_secret_replay(
    audit_session,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command()
    with pytest.raises(EvaluationWorkbenchError):
        unit_of_work.mutate(command, _rejected_callback(audit_session))
    record_id = audit_session.scalar(select(GovernanceIdempotencyRecord.__table__.c.id))
    audit_session.execute(
        update(GovernanceIdempotencyRecord.__table__)
        .where(GovernanceIdempotencyRecord.id == record_id)
        .values(
            response_body_json=canonical_json(
                {
                    "_fairmindEvaluationMutationRejected": True,
                    "error": {
                        "code": "evaluation_rejected",
                        "message": "A different safe canonical rejection is replayed.",
                    },
                }
            )
        )
    )
    audit_session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(
            command,
            lambda _now: pytest.fail("tampered replay must not execute callback"),
        )

    assert caught.value.detail() == {
        "code": "idempotency_response_invalid",
        "message": "The stored idempotency response is invalid.",
    }
    assert "different safe canonical" not in str(caught.value)
    assert len(_events(audit_session)) == 1


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("response_status", 409),
        (
            "response_body_json",
            canonical_json(
                {
                    "_fairmindEvaluationMutationRejected": True,
                    "error": {
                        "code": "altered_safe_code",
                        "message": "The assurance mutation was rejected.",
                    },
                }
            ),
        ),
        (
            "response_body_json",
            canonical_json(
                {
                    "_fairmindEvaluationMutationRejected": True,
                    "error": {
                        "code": "evaluation_rejected",
                        "message": "The assurance mutation was rejected.",
                        "details": {"reason": "benign-looking private prose"},
                    },
                }
            ),
        ),
        ("resource_type", "evaluation_test_resource"),
        ("resource_id", str(uuid.uuid4())),
    ],
)
def test_safe_semantic_rejection_tampering_cannot_replay(
    audit_session,
    column: str,
    value: object,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command()
    with pytest.raises(EvaluationWorkbenchError):
        unit_of_work.mutate(command, _rejected_callback(audit_session))
    record_id = audit_session.scalar(select(GovernanceIdempotencyRecord.__table__.c.id))
    audit_session.execute(
        update(GovernanceIdempotencyRecord.__table__)
        .where(GovernanceIdempotencyRecord.id == record_id)
        .values(**{column: value})
    )
    audit_session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(
            command,
            lambda _now: pytest.fail("tampered replay must not execute callback"),
        )

    assert caught.value.code == "idempotency_response_invalid"
    assert len(_events(audit_session)) == 1


def test_rejected_record_cannot_be_reclassified_as_a_success_replay(audit_session) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command()
    with pytest.raises(EvaluationWorkbenchError):
        unit_of_work.mutate(command, _rejected_callback(audit_session))
    audit_session.execute(
        update(GovernanceIdempotencyRecord.__table__).values(
            response_status=201,
            response_body_json=canonical_json({"id": "forged-success"}),
            resource_type="evaluation_test_resource",
            resource_id="forged-success",
        )
    )
    audit_session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(
            command,
            lambda _now: pytest.fail("forged success must not execute callback"),
        )

    assert caught.value.code == "idempotency_response_invalid"
    assert len(_events(audit_session)) == 1


@pytest.mark.parametrize(
    "stored_body",
    [
        None,
        7,
        "{",
        (
            '{"_fairmindEvaluationMutationRejected":true,"error":'
            '{"code":"evaluation_rejected","code":"duplicate",'
            '"message":"The assurance mutation was rejected."}}'
        ),
        '{"value":Infinity}',
        '{"value":9007199254740992}',
        '{"_fairmindEvaluationMutationRejected": true,"error":{}}',
        "{" + '"value":' + "[" * 40 + "0" + "]" * 40 + "}",
        canonical_json({"value": [0] * 4097}),
        canonical_json(
            {
                "_fairmindEvaluationMutationRejected": True,
                "error": {
                    "code": "evaluation_rejected",
                    "message": "x" * (33 * 1024),
                },
            }
        ),
    ],
)
def test_rejected_replay_rejects_malformed_or_unbounded_persisted_json(
    audit_session,
    stored_body: object,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command()
    with pytest.raises(EvaluationWorkbenchError):
        unit_of_work.mutate(command, _rejected_callback(audit_session))
    audit_session.execute(
        update(GovernanceIdempotencyRecord.__table__).values(
            response_body_json=stored_body,
        )
    )
    audit_session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(
            command,
            lambda _now: pytest.fail("invalid replay must not execute callback"),
        )

    assert caught.value.code == "idempotency_response_invalid"
    assert len(_events(audit_session)) == 1


@pytest.mark.parametrize(
    "stored_body",
    [
        "[]",
        '{"id":"first","id":"second"}',
        '{"value":NaN}',
        '{"id": "noncanonical"}',
        '{"value":9007199254740992}',
        "{" + '"value":' + "[" * 40 + "0" + "]" * 40 + "}",
    ],
)
def test_completed_success_replay_rejects_invalid_persisted_json(
    audit_session,
    stored_body: str,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command(key="successful-replay")
    unit_of_work.mutate(command, lambda _now: _success_outcome())
    audit_session.execute(
        update(GovernanceIdempotencyRecord.__table__).values(
            response_body_json=stored_body,
        )
    )
    audit_session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(
            command,
            lambda _now: pytest.fail("invalid success replay must not execute callback"),
        )

    assert caught.value.code == "idempotency_response_invalid"


def test_completed_success_replay_rejects_invalid_status(audit_session) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    command = _command(key="successful-status-replay")
    unit_of_work.mutate(command, lambda _now: _success_outcome())
    audit_session.execute(update(GovernanceIdempotencyRecord.__table__).values(response_status=999))
    audit_session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(
            command,
            lambda _now: pytest.fail("invalid status must not execute callback"),
        )

    assert caught.value.code == "idempotency_response_invalid"


def test_success_after_rejection_extends_the_same_organization_chain(audit_session) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    with pytest.raises(EvaluationWorkbenchError):
        unit_of_work.mutate(_command(), _rejected_callback(audit_session))

    unit_of_work.mutate(
        _command(key="success-key"),
        lambda _now: _success_outcome(),
    )

    rows = _events(audit_session)
    assert [(row["sequence_number"], row["outcome"]) for row in rows] == [
        (1, "rejected"),
        (2, "success"),
    ]
    assert rows[1]["previous_hash"] == rows[0]["event_hash"]


def test_rejected_events_are_organization_scoped(audit_session) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    with pytest.raises(EvaluationWorkbenchError):
        unit_of_work.mutate(_command(), _rejected_callback(audit_session))
    with pytest.raises(EvaluationWorkbenchError):
        unit_of_work.mutate(
            _command(org_id=OTHER_ORG, key="other-key"),
            _rejected_callback(
                audit_session,
                org_id=OTHER_ORG,
                workspace_id="other-rolled-back",
            ),
        )

    assert len(_events(audit_session, ORG)) == 1
    assert len(_events(audit_session, OTHER_ORG)) == 1


def test_rejected_audit_details_do_not_contain_error_message_or_details(audit_session) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    with pytest.raises(EvaluationWorkbenchError):
        unit_of_work.mutate(_command(), _rejected_callback(audit_session))

    stored_details = _events(audit_session)[0]["details_json"]
    assert "Sensitive message" not in stored_details
    assert "never-audit" not in stored_details
    assert "token" not in stored_details
    assert "rejected-key" not in stored_details


@pytest.mark.parametrize("failure_stage", ["append", "complete"])
def test_rejected_audit_failure_rolls_back_everything_and_surfaces_persistence_error(
    audit_session, monkeypatch, failure_stage: str
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)

    def fail_rejection_transaction(**_kwargs):
        raise RuntimeError("audit unavailable")

    method = (
        "_append_rejected_audit" if failure_stage == "append" else "_complete_rejected_idempotency"
    )
    monkeypatch.setattr(
        unit_of_work,
        method,
        fail_rejection_transaction,
        raising=False,
    )
    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(_command(), _rejected_callback(audit_session))

    assert caught.value.code == "evaluation_persistence_failed"
    assert (
        audit_session.execute(
            select(GovernanceWorkspace.__table__).where(
                GovernanceWorkspace.id == "rolled-back-workspace"
            )
        )
        .mappings()
        .one_or_none()
        is None
    )
    assert audit_session.scalar(select(func.count()).select_from(GovernanceIdempotencyRecord)) == 0
    assert (
        audit_session.scalar(select(func.count()).select_from(GovernanceEvaluationAuditEvent)) == 0
    )


def test_unexpected_callback_failure_rolls_back_without_mislabeling_a_rejection(
    audit_session,
) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)

    def fail_unexpectedly(_now):
        audit_session.execute(
            GovernanceWorkspace.__table__.insert().values(
                id="unexpected-rolled-back-workspace",
                org_id=ORG,
                name="Must roll back",
            )
        )
        raise RuntimeError("sk-proj-internal-database-detail")

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(_command(), fail_unexpectedly)

    assert caught.value.detail() == {
        "code": "evaluation_persistence_failed",
        "message": "The assurance workflow could not be persisted atomically.",
    }
    assert "sk-proj-internal-database-detail" not in str(caught.value)
    assert (
        audit_session.execute(
            select(GovernanceWorkspace.__table__).where(
                GovernanceWorkspace.id == "unexpected-rolled-back-workspace"
            )
        )
        .mappings()
        .one_or_none()
        is None
    )
    assert audit_session.scalar(select(func.count()).select_from(GovernanceIdempotencyRecord)) == 0
    assert (
        audit_session.scalar(select(func.count()).select_from(GovernanceEvaluationAuditEvent)) == 0
    )


def test_tampered_chain_blocks_the_next_append(audit_session) -> None:
    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(audit_session)
    unit_of_work.mutate(_command(key="first"), lambda _now: _success_outcome())
    audit_session.execute(
        update(GovernanceEvaluationAuditEvent.__table__)
        .where(GovernanceEvaluationAuditEvent.org_id == ORG)
        .values(details_json='{"tampered":true}')
    )
    audit_session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        unit_of_work.mutate(
            _command(key="second"),
            lambda _now: _success_outcome(resource_id="second-resource"),
        )

    assert caught.value.code == "evaluation_persistence_failed"
    assert len(_events(audit_session)) == 1
