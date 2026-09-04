"""PostgreSQL 14 leased queue for isolated evaluation workers."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.application.ports.evaluation_workbench import FrozenJsonObject
from src.application.ports.evaluation_worker_queue import (
    HEARTBEAT_INTERVAL_SECONDS,
    LEASE_DURATION_SECONDS,
    HeartbeatReceipt,
    LeaseCredential,
    WorkerLease,
    WorkerQueueError,
    WorkerQueuePrincipal,
)
from src.domain.assurance.evaluation_v2 import canonical_json


_WORKER_FORBIDDEN = "No active worker identity is bound to this service principal."
_WORKER_INACTIVE = "The bound worker identity is not active."
_LEASE_LOST = "The lease is expired, superseded, foreign, or no longer active."
_PERSISTENCE_ERROR = "The worker queue could not complete the requested operation."


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise WorkerQueueError("binding_integrity_error", _PERSISTENCE_ERROR)
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _as_utc(value).isoformat()


def _stored_datetime(value: object) -> datetime:
    if not isinstance(value, str):
        raise WorkerQueueError("binding_integrity_error", _PERSISTENCE_ERROR)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise WorkerQueueError("binding_integrity_error", _PERSISTENCE_ERROR) from error
    return _as_utc(parsed)


def _stored_envelope(value: object) -> FrozenJsonObject:
    if not isinstance(value, str) or len(value.encode("utf-8")) > 1024 * 1024:
        raise WorkerQueueError("binding_integrity_error", _PERSISTENCE_ERROR)
    try:
        decoded = json.loads(value)
        if not isinstance(decoded, dict) or canonical_json(decoded) != value:
            raise ValueError("stored envelope is not canonical")
        return FrozenJsonObject.from_mapping(decoded)
    except (
        OverflowError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as error:
        raise WorkerQueueError("binding_integrity_error", _PERSISTENCE_ERROR) from error


def _lease_token_hash(raw_token: object) -> str:
    if not isinstance(raw_token, str) or re.fullmatch(r"[A-Za-z0-9_-]{43}", raw_token) is None:
        raise WorkerQueueError("lease_lost", _LEASE_LOST)
    return hashlib.sha256(raw_token.encode("ascii")).hexdigest()


class PostgresEvaluationWorkerQueue:
    """Transaction-owning adapter for claim, heartbeat, and expiry recovery."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _require_postgresql(session: Session) -> None:
        if session.get_bind().dialect.name != "postgresql":
            raise WorkerQueueError(
                "postgres_required",
                "Evaluation worker queues require PostgreSQL.",
            )

    @staticmethod
    def _database_now(session: Session) -> datetime:
        value = session.scalar(text("SELECT pg_catalog.clock_timestamp()"))
        if not isinstance(value, datetime):
            raise WorkerQueueError("binding_integrity_error", _PERSISTENCE_ERROR)
        return _as_utc(value)

    @staticmethod
    def _active_worker(
        session: Session,
        principal: WorkerQueuePrincipal,
    ) -> Mapping[str, Any]:
        row = session.execute(
            text(
                "SELECT id, worker_type, status "
                "FROM governance_evaluation_worker_identities "
                "WHERE org_id=:org_id AND principal_subject=:principal_subject "
                "FOR SHARE"
            ),
            {
                "org_id": principal.organization_id,
                "principal_subject": principal.principal_subject,
            },
        ).mappings().one_or_none()
        if row is None:
            raise WorkerQueueError("worker_forbidden", _WORKER_FORBIDDEN)
        if row["status"] != "active":
            raise WorkerQueueError("worker_inactive", _WORKER_INACTIVE)
        return row

    def claim(self, principal: WorkerQueuePrincipal) -> WorkerLease | None:
        session = self._session_factory()
        try:
            self._require_postgresql(session)
            with session.begin():
                now = self._database_now(session)
                worker = self._active_worker(session, principal)
                self._recover_expired_in_transaction(
                    session,
                    organization_id=principal.organization_id,
                    now=now,
                )
                row = session.execute(
                    text(
                        "SELECT execution.id, execution.workspace_id, "
                        "execution.system_id, execution.run_id, "
                        "execution.attempt_count, "
                        "execution.max_attempts, run.envelope_json "
                        "FROM governance_evaluation_run_suite_executions AS execution "
                        "JOIN governance_evaluation_runs AS run "
                        "ON run.id=execution.run_id "
                        "AND run.workspace_id=execution.workspace_id "
                        "AND run.system_id=execution.system_id "
                        "AND run.org_id=execution.org_id "
                        "JOIN governance_evaluation_suite_versions AS suite "
                        "ON suite.id=execution.suite_version_id "
                        "AND suite.owner_scope=execution.suite_owner_scope "
                        "WHERE execution.org_id=:org_id "
                        "AND execution.technical_status='queued' "
                        "AND execution.available_at::TIMESTAMPTZ <= :now "
                        "AND execution.attempt_count < execution.max_attempts "
                        "AND suite.worker_type=:worker_type "
                        "AND NOT EXISTS ("
                        "SELECT 1 FROM governance_evaluation_cancellations AS cancellation "
                        "WHERE cancellation.org_id=execution.org_id "
                        "AND cancellation.run_id=execution.run_id "
                        "AND (cancellation.suite_execution_id IS NULL "
                        "OR cancellation.suite_execution_id=execution.id)) "
                        "ORDER BY execution.available_at, execution.created_at, execution.id "
                        "LIMIT 1 FOR UPDATE OF execution SKIP LOCKED"
                    ),
                    {
                        "org_id": principal.organization_id,
                        "worker_type": worker["worker_type"],
                        "now": now,
                    },
                ).mappings().one_or_none()
                if row is None:
                    return None

                attempt_number = int(row["attempt_count"]) + 1
                if attempt_number > min(int(row["max_attempts"]), 3):
                    raise WorkerQueueError("binding_integrity_error", _PERSISTENCE_ERROR)
                attempt_id = str(uuid.uuid4())
                raw_token = secrets.token_urlsafe(32)
                token_hash = _lease_token_hash(raw_token)
                expires_at = now + timedelta(seconds=LEASE_DURATION_SECONDS)
                updated = session.execute(
                    text(
                        "UPDATE governance_evaluation_run_suite_executions "
                        "SET technical_status='leased', attempt_count=:attempt_number, "
                        "updated_at=:now "
                        "WHERE id=:execution_id AND org_id=:org_id "
                        "AND technical_status='queued' "
                        "AND attempt_count=:previous_attempt_count"
                    ),
                    {
                        "attempt_number": attempt_number,
                        "previous_attempt_count": row["attempt_count"],
                        "now": _iso(now),
                        "execution_id": row["id"],
                        "org_id": principal.organization_id,
                    },
                )
                if updated.rowcount != 1:
                    raise WorkerQueueError("lease_lost", _LEASE_LOST)
                session.execute(
                    text(
                        "INSERT INTO governance_evaluation_suite_attempts "
                        "(id, org_id, workspace_id, system_id, run_id, "
                        "suite_execution_id, attempt_number, worker_identity_id, "
                        "technical_status, lease_token_hash, leased_at, "
                        "last_heartbeat_at, lease_expires_at, created_at, updated_at) "
                        "VALUES (:id, :org_id, :workspace_id, :system_id, :run_id, "
                        ":suite_execution_id, :attempt_number, :worker_identity_id, "
                        "'leased', :lease_token_hash, :now, :now, :expires_at, :now, :now)"
                    ),
                    {
                        "id": attempt_id,
                        "org_id": principal.organization_id,
                        "workspace_id": row["workspace_id"],
                        "system_id": row["system_id"],
                        "run_id": row["run_id"],
                        "suite_execution_id": row["id"],
                        "attempt_number": attempt_number,
                        "worker_identity_id": worker["id"],
                        "lease_token_hash": token_hash,
                        "now": _iso(now),
                        "expires_at": _iso(expires_at),
                    },
                )
                envelope = _stored_envelope(row["envelope_json"])
            return WorkerLease(
                credential=LeaseCredential(
                    attempt_id=attempt_id,
                    raw_token=raw_token,
                ),
                suite_execution_id=str(row["id"]),
                attempt_number=attempt_number,
                envelope=envelope,
                leased_at=now,
                heartbeat_due_at=now + timedelta(seconds=HEARTBEAT_INTERVAL_SECONDS),
                lease_expires_at=expires_at,
            )
        except WorkerQueueError:
            session.rollback()
            raise
        except SQLAlchemyError as error:
            session.rollback()
            raise WorkerQueueError("queue_persistence_error", _PERSISTENCE_ERROR) from error
        finally:
            session.close()

    def heartbeat(
        self,
        principal: WorkerQueuePrincipal,
        credential: LeaseCredential,
    ) -> HeartbeatReceipt:
        session = self._session_factory()
        try:
            self._require_postgresql(session)
            with session.begin():
                row = session.execute(
                    text(
                        "SELECT attempt.id, attempt.technical_status, "
                        "attempt.lease_token_hash, attempt.lease_expires_at, "
                        "worker.status AS worker_status "
                        "FROM governance_evaluation_suite_attempts AS attempt "
                        "JOIN governance_evaluation_worker_identities AS worker "
                        "ON worker.id=attempt.worker_identity_id "
                        "AND worker.org_id=attempt.org_id "
                        "WHERE attempt.id=:attempt_id AND attempt.org_id=:org_id "
                        "AND worker.principal_subject=:principal_subject "
                        "FOR UPDATE OF attempt FOR SHARE OF worker"
                    ),
                    {
                        "attempt_id": credential.attempt_id,
                        "org_id": principal.organization_id,
                        "principal_subject": principal.principal_subject,
                    },
                ).mappings().one_or_none()
                now = self._database_now(session)
                supplied_hash = _lease_token_hash(credential.raw_token)
                if (
                    row is None
                    or row["technical_status"] != "leased"
                    or not hmac.compare_digest(str(row["lease_token_hash"]), supplied_hash)
                    or _stored_datetime(row["lease_expires_at"]) <= now
                ):
                    raise WorkerQueueError("lease_lost", _LEASE_LOST)
                if row["worker_status"] != "active":
                    raise WorkerQueueError("worker_inactive", _WORKER_INACTIVE)

                expires_at = now + timedelta(seconds=LEASE_DURATION_SECONDS)
                session.execute(
                    text(
                        "UPDATE governance_evaluation_suite_attempts "
                        "SET last_heartbeat_at=:now, lease_expires_at=:expires_at, "
                        "updated_at=:now WHERE id=:attempt_id AND org_id=:org_id"
                    ),
                    {
                        "now": _iso(now),
                        "expires_at": _iso(expires_at),
                        "attempt_id": credential.attempt_id,
                        "org_id": principal.organization_id,
                    },
                )
            return HeartbeatReceipt(
                heartbeat_at=now,
                next_heartbeat_at=now + timedelta(seconds=HEARTBEAT_INTERVAL_SECONDS),
                lease_expires_at=expires_at,
            )
        except WorkerQueueError:
            session.rollback()
            raise
        except SQLAlchemyError as error:
            session.rollback()
            raise WorkerQueueError("queue_persistence_error", _PERSISTENCE_ERROR) from error
        finally:
            session.close()

    @staticmethod
    def _recover_expired_in_transaction(
        session: Session,
        *,
        organization_id: str,
        now: datetime,
    ) -> None:
        rows = session.execute(
            text(
                "SELECT attempt.id AS attempt_id, attempt.attempt_number, "
                "execution.id AS execution_id, execution.attempt_count, "
                "execution.max_attempts "
                "FROM governance_evaluation_suite_attempts AS attempt "
                "JOIN governance_evaluation_run_suite_executions AS execution "
                "ON execution.id=attempt.suite_execution_id "
                "AND execution.run_id=attempt.run_id "
                "AND execution.workspace_id=attempt.workspace_id "
                "AND execution.system_id=attempt.system_id "
                "AND execution.org_id=attempt.org_id "
                "WHERE attempt.org_id=:org_id "
                "AND attempt.technical_status='leased' "
                "AND execution.technical_status='leased' "
                "AND attempt.lease_expires_at::TIMESTAMPTZ <= :now "
                "ORDER BY attempt.lease_expires_at, attempt.id "
                "LIMIT 100 FOR UPDATE OF attempt, execution SKIP LOCKED"
            ),
            {"org_id": organization_id, "now": now},
        ).mappings().all()
        now_text = _iso(now)
        for row in rows:
            attempt_number = int(row["attempt_number"])
            attempt_count = int(row["attempt_count"])
            max_attempts = int(row["max_attempts"])
            if attempt_number != attempt_count or not 1 <= max_attempts <= 3:
                raise WorkerQueueError("binding_integrity_error", _PERSISTENCE_ERROR)
            session.execute(
                text(
                    "UPDATE governance_evaluation_suite_attempts "
                    "SET technical_status='timed_out', completed_at=:now, "
                    "failure_code='lease_expired', "
                    "failure_message='The worker lease expired before completion.', "
                    "updated_at=:now WHERE id=:attempt_id AND org_id=:org_id"
                ),
                {
                    "now": now_text,
                    "attempt_id": row["attempt_id"],
                    "org_id": organization_id,
                },
            )
            if attempt_count < max_attempts:
                session.execute(
                    text(
                        "UPDATE governance_evaluation_run_suite_executions "
                        "SET technical_status='queued', started_at=NULL, updated_at=:now "
                        "WHERE id=:execution_id AND org_id=:org_id "
                        "AND technical_status='leased'"
                    ),
                    {
                        "now": now_text,
                        "execution_id": row["execution_id"],
                        "org_id": organization_id,
                    },
                )
            else:
                session.execute(
                    text(
                        "UPDATE governance_evaluation_run_suite_executions "
                        "SET technical_status='timed_out', "
                        "evidence_result_status='unavailable', completed_at=:now, "
                        "failure_code='lease_expired', "
                        "failure_message='The worker lease retry limit was exhausted.', "
                        "updated_at=:now WHERE id=:execution_id AND org_id=:org_id "
                        "AND technical_status='leased'"
                    ),
                    {
                        "now": now_text,
                        "execution_id": row["execution_id"],
                        "org_id": organization_id,
                    },
                )


__all__ = ["PostgresEvaluationWorkerQueue"]
