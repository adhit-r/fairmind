"""PostgreSQL 14 leased queue and job-state authority for isolated evaluation workers.

Every job mutation serializes on the canonical run arbiter (a run-scoped
advisory transaction lock), then locks the system, run, and sibling suites in
``(ordinal, id)`` order, then the attempt, worker, and cancellation rows. The
database clock is sampled only after those waits. Cancellation terminalizes
affected attempts under the same arbiter, so a start, heartbeat, failure,
completion, or expiry recovery that serializes after it observes the
cancellation and cannot advance the job.
"""

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
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from src.application.ports.evaluation_cancellation import (
    CancellationRecord,
    PersistCancellationCommand,
)
from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
)
from src.application.ports.evaluation_worker_queue import (
    CANCELLED_FAILURE_CODE,
    CANCELLED_FAILURE_MESSAGE,
    HEARTBEAT_INTERVAL_SECONDS,
    LEASE_DURATION_SECONDS,
    LEASE_EXPIRED_PROJECTION,
    WORKER_FAILURE_PROJECTIONS,
    AdmittedWorkerEvidence,
    CompletionReceipt,
    HeartbeatReceipt,
    JobTransitionReceipt,
    LeaseCredential,
    WorkerLease,
    WorkerQueueError,
    WorkerQueuePrincipal,
)
from src.application.ports.evidence_admission import EvidenceAdmissionScope
from src.domain.assurance.evaluation_v2 import canonical_json
from src.domain.assurance.evidence_passport_v2 import MAX_PASSPORT_BYTES
from src.infrastructure.db.repositories.evaluation_audit_chain import (
    EvaluationAuditAppend,
    append_evaluation_audit_event,
)


_WORKER_FORBIDDEN = "No active worker identity is bound to this service principal."
_WORKER_INACTIVE = "The bound worker identity is not active."
_LEASE_LOST = "The lease is expired, superseded, foreign, or no longer active."
_JOB_CANCELLED = "The evaluation job was cancelled."
_EVIDENCE_REJECTED = "The signed completion evidence was rejected."
_PERSISTENCE_ERROR = "The worker queue could not complete the requested operation."
_LEASE_EXPIRED_CODE = "worker_lease_expired"
_TERMINAL = frozenset({"succeeded", "failed", "timed_out", "cancelled"})
_ACTIVE_RUN_PRIORITY = ("running", "leased", "queued", "awaiting_evidence")
_TERMINAL_RUN_PRIORITY = ("failed", "timed_out", "cancelled", "succeeded")
_OUTCOME_PRIORITY = (
    "pending",
    "failed",
    "error",
    "unavailable",
    "insufficient_data",
    "unknown",
    "passed_with_limitations",
    "informational",
)
_AUDIT_RESOURCE = "evaluation_suite_attempt"
_CLAIM_CANDIDATE_RUNS = 10

EvidenceAdmitter = Callable[..., AdmittedWorkerEvidence]


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


def _require_postgresql(session: Session) -> None:
    if session.get_bind().dialect.name != "postgresql":
        raise WorkerQueueError(
            "postgres_required",
            "Evaluation worker queues require PostgreSQL.",
        )


def _database_now(session: Session) -> datetime:
    value = session.scalar(text("SELECT pg_catalog.clock_timestamp()"))
    if not isinstance(value, datetime):
        raise WorkerQueueError("binding_integrity_error", _PERSISTENCE_ERROR)
    return _as_utc(value)


_ARBITER_KEY = (
    "pg_catalog.hashtextextended('fairmind:evaluation-run:v1|' "
    "|| length(:org_id)::text || ':' || :org_id "
    "|| '|' || length(:run_id)::text || ':' || :run_id, 0)"
)


def _lock_run_arbiter(session: Session, org_id: str, run_id: str, *, wait: bool = True) -> bool:
    """Acquire the canonical run arbiter; ``wait=False`` never blocks."""

    function = "pg_advisory_xact_lock" if wait else "pg_try_advisory_xact_lock"
    acquired = session.scalar(
        text(f"SELECT pg_catalog.{function}({_ARBITER_KEY})"),
        {"org_id": org_id, "run_id": run_id},
    )
    return wait or acquired is True


def _lock_siblings(session: Session, scope: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return list(
        session.execute(
            text(
                "SELECT id, technical_status, attempt_count, max_attempts, started_at "
                "FROM governance_evaluation_run_suite_executions "
                "WHERE run_id=:run_id AND org_id=:org_id "
                "AND workspace_id=:workspace_id AND system_id=:system_id "
                "ORDER BY ordinal, id FOR UPDATE"
            ),
            scope,
        ).mappings().all()
    )


def _cancelled_suites(session: Session, scope: Mapping[str, Any]) -> tuple[bool, set[str]]:
    """Return (run cancelled, suite IDs cancelled) under share locks."""

    rows = session.execute(
        text(
            "SELECT suite_execution_id FROM governance_evaluation_cancellations "
            "WHERE org_id=:org_id AND workspace_id=:workspace_id "
            "AND system_id=:system_id AND run_id=:run_id "
            "ORDER BY suite_execution_id NULLS FIRST, id FOR SHARE"
        ),
        scope,
    ).scalars().all()
    return any(row is None for row in rows), {row for row in rows if row is not None}


def _update_attempt(
    session: Session,
    *,
    attempt_id: str,
    org_id: str,
    status: str,
    now: datetime,
    failure: tuple[str, str] | None = None,
) -> None:
    session.execute(
        text(
            "UPDATE governance_evaluation_suite_attempts "
            "SET technical_status=:status, completed_at=:now, updated_at=:now, "
            "failure_code=:code, failure_message=:message "
            "WHERE id=:attempt_id AND org_id=:org_id "
            "AND technical_status IN ('leased', 'running')"
        ),
        {
            "status": status,
            "now": _iso(now),
            "code": failure[0] if failure else None,
            "message": failure[1] if failure else None,
            "attempt_id": attempt_id,
            "org_id": org_id,
        },
    )


def _terminalize_suite(
    session: Session,
    *,
    suite_execution_id: str,
    org_id: str,
    status: str,
    evidence_result: str,
    now: datetime,
    failure: tuple[str, str],
) -> None:
    updated = session.execute(
        text(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status=:status, evidence_result_status=:evidence_result, "
            "completed_at=:now, failure_code=:code, failure_message=:message, "
            "updated_at=:now WHERE id=:suite_execution_id AND org_id=:org_id "
            "AND technical_status NOT IN ('succeeded', 'failed', 'timed_out', 'cancelled')"
        ),
        {
            "status": status,
            "evidence_result": evidence_result,
            "now": _iso(now),
            "code": failure[0],
            "message": failure[1],
            "suite_execution_id": suite_execution_id,
            "org_id": org_id,
        },
    )
    if updated.rowcount != 1:
        raise WorkerQueueError("binding_integrity_error", _PERSISTENCE_ERROR)


def _cancel_suite(
    session: Session,
    *,
    suite_execution_id: str,
    org_id: str,
    now: datetime,
) -> str | None:
    """Cancel one non-terminal suite and its active attempt; return the attempt ID."""

    attempt_id = session.scalar(
        text(
            "SELECT id FROM governance_evaluation_suite_attempts "
            "WHERE suite_execution_id=:suite_execution_id AND org_id=:org_id "
            "AND technical_status IN ('leased', 'running') FOR UPDATE"
        ),
        {"suite_execution_id": suite_execution_id, "org_id": org_id},
    )
    pair = (CANCELLED_FAILURE_CODE, CANCELLED_FAILURE_MESSAGE)
    if attempt_id is not None:
        _update_attempt(
            session,
            attempt_id=attempt_id,
            org_id=org_id,
            status="cancelled",
            now=now,
            failure=pair,
        )
    # ponytail: "pending" keeps the run aggregate legal under the frozen 013b
    # run guard; a non-pending cancelled result needs the 013n guard relaxation.
    _terminalize_suite(
        session,
        suite_execution_id=suite_execution_id,
        org_id=org_id,
        status="cancelled",
        evidence_result="pending",
        now=now,
        failure=pair,
    )
    return attempt_id


def _project_run(session: Session, *, org_id: str, run_id: str, now: datetime) -> str:
    """Recompute the parent run from its locked suites; return its technical status.

    The run is updated only to a projection the frozen 013b run guard accepts.
    """

    run = session.execute(
        text(
            "SELECT technical_status, evidence_outcome, started_at, completed_at, "
            "failure_code, failure_message FROM governance_evaluation_runs "
            "WHERE id=:run_id AND org_id=:org_id"
        ),
        {"run_id": run_id, "org_id": org_id},
    ).mappings().one()
    if run["technical_status"] in _TERMINAL:
        return str(run["technical_status"])
    suites = session.execute(
        text(
            "SELECT technical_status, evidence_result_status, started_at, "
            "failure_code, failure_message, evidence_run_id, admission_status "
            "FROM governance_evaluation_run_suite_executions "
            "WHERE run_id=:run_id AND org_id=:org_id ORDER BY ordinal, id"
        ),
        {"run_id": run_id, "org_id": org_id},
    ).mappings().all()
    states = {row["technical_status"] for row in suites}
    priority = _TERMINAL_RUN_PRIORITY if states <= _TERMINAL else _ACTIVE_RUN_PRIORITY
    technical = next(status for status in priority if status in states)
    results = {row["evidence_result_status"] for row in suites}
    outcome = next((status for status in _OUTCOME_PRIORITY if status in results), "passed")
    unlinked = any(
        row["evidence_run_id"] is None
        or row["admission_status"] in {"pending", "rejected", "trust_error"}
        for row in suites
    )
    # ponytail: under the frozen 013b guard a non-pending outcome needs every
    # suite linked and a started run cannot regress; keep the last legal
    # projection until migration 013n relaxes both rules.
    if (outcome != "pending" and unlinked) or not session.scalar(
        text("SELECT fairmind_run_state_transition_allowed(:old, :new)"),
        {"old": run["technical_status"], "new": technical},
    ):
        return str(run["technical_status"])
    started_at = run["started_at"]
    if technical in {"awaiting_evidence", "queued", "leased"}:
        started_at = None
    elif started_at is None:
        started_at = min(
            (row["started_at"] for row in suites if row["started_at"] is not None),
            key=_stored_datetime,
            default=_iso(now),
        )
    completed_at = _iso(now) if technical in _TERMINAL else None
    failure = next(
        (
            (row["failure_code"], row["failure_message"])
            for row in suites
            if technical in {"failed", "timed_out", "cancelled"}
            and row["technical_status"] == technical
        ),
        (None, None),
    )
    projection = (technical, outcome, started_at, completed_at, *failure)
    current = (
        run["technical_status"],
        run["evidence_outcome"],
        run["started_at"],
        run["completed_at"],
        run["failure_code"],
        run["failure_message"],
    )
    if projection == current:
        return technical
    session.execute(
        text(
            "UPDATE governance_evaluation_runs SET technical_status=:technical, "
            "evidence_outcome=:outcome, started_at=:started_at, "
            "completed_at=:completed_at, failure_code=:code, failure_message=:message, "
            "updated_at=:now WHERE id=:run_id AND org_id=:org_id"
        ),
        {
            "technical": technical,
            "outcome": outcome,
            "started_at": started_at,
            "completed_at": completed_at,
            "code": failure[0],
            "message": failure[1],
            "now": _iso(now),
            "run_id": run_id,
            "org_id": org_id,
        },
    )
    return technical


def _append_worker_audit(
    session: Session,
    *,
    principal: WorkerQueuePrincipal,
    action: str,
    attempt_id: str,
    details: Mapping[str, object],
    now: datetime,
) -> None:
    append_evaluation_audit_event(
        session,
        event=EvaluationAuditAppend(
            organization_id=principal.organization_id,
            actor_id=principal.principal_subject,
            action=action,
            outcome="success",
            resource_type=_AUDIT_RESOURCE,
            resource_id=attempt_id,
            details=dict(details),
            created_at=_iso(now),
        ),
    )


class PostgresEvaluationWorkerQueue:
    """Transaction-owning adapter for every worker job-state transition."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        evidence_admitter: EvidenceAdmitter | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._evidence_admitter = evidence_admitter

    def _transaction(self, operation: Callable[[Session], Any]) -> Any:
        session = self._session_factory()
        try:
            _require_postgresql(session)
            with session.begin():
                return operation(session)
        except WorkerQueueError:
            session.rollback()
            raise
        except SQLAlchemyError as error:
            session.rollback()
            raise WorkerQueueError("queue_persistence_error", _PERSISTENCE_ERROR) from error
        finally:
            session.close()

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

    # ------------------------------------------------------------------ claim

    def claim(self, principal: WorkerQueuePrincipal) -> WorkerLease | None:
        worker_type = self._transaction(
            lambda session: self._active_worker(session, principal)["worker_type"]
        )
        self.recover_expired(principal.organization_id)
        candidates = self._transaction(
            lambda session: session.execute(
                text(
                    "SELECT execution.run_id "
                    "FROM governance_evaluation_run_suite_executions AS execution "
                    "JOIN governance_evaluation_suite_versions AS suite "
                    "ON suite.id=execution.suite_version_id "
                    "AND suite.owner_scope=execution.suite_owner_scope "
                    "WHERE execution.org_id=:org_id "
                    "AND execution.technical_status='queued' "
                    "AND execution.available_at::TIMESTAMPTZ <= pg_catalog.clock_timestamp() "
                    "AND execution.attempt_count < execution.max_attempts "
                    "AND suite.worker_type=:worker_type "
                    "GROUP BY execution.run_id "
                    "ORDER BY min(execution.available_at), min(execution.created_at), "
                    "execution.run_id LIMIT :limit"
                ),
                {
                    "org_id": principal.organization_id,
                    "worker_type": worker_type,
                    "limit": _CLAIM_CANDIDATE_RUNS,
                },
            ).scalars().all()
        )
        for run_id in candidates:
            lease = self._transaction(
                lambda session, run_id=run_id: self._claim_in_run(session, principal, run_id)
            )
            if lease is not None:
                return lease
        return None

    def _claim_in_run(
        self,
        session: Session,
        principal: WorkerQueuePrincipal,
        run_id: str,
    ) -> WorkerLease | None:
        org_id = principal.organization_id
        # A busy run is skipped rather than waited on; one advisory lock per transaction.
        if not _lock_run_arbiter(session, org_id, run_id, wait=False):
            return None
        worker = self._active_worker(session, principal)
        run = session.execute(
            text(
                "SELECT workspace_id, system_id, envelope_json FROM governance_evaluation_runs "
                "WHERE id=:run_id AND org_id=:org_id FOR UPDATE"
            ),
            {"run_id": run_id, "org_id": org_id},
        ).mappings().one_or_none()
        if run is None:
            return None
        now = _database_now(session)
        row = session.execute(
            text(
                "SELECT execution.id, execution.attempt_count, execution.max_attempts "
                "FROM governance_evaluation_run_suite_executions AS execution "
                "JOIN governance_evaluation_suite_versions AS suite "
                "ON suite.id=execution.suite_version_id "
                "AND suite.owner_scope=execution.suite_owner_scope "
                "WHERE execution.org_id=:org_id AND execution.run_id=:run_id "
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
                "org_id": org_id,
                "run_id": run_id,
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
                "org_id": org_id,
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
                "org_id": org_id,
                "workspace_id": run["workspace_id"],
                "system_id": run["system_id"],
                "run_id": run_id,
                "suite_execution_id": row["id"],
                "attempt_number": attempt_number,
                "worker_identity_id": worker["id"],
                "lease_token_hash": _lease_token_hash(raw_token),
                "now": _iso(now),
                "expires_at": _iso(expires_at),
            },
        )
        envelope = _stored_envelope(run["envelope_json"])
        _project_run(session, org_id=org_id, run_id=run_id, now=now)
        return WorkerLease(
            credential=LeaseCredential(attempt_id=attempt_id, raw_token=raw_token),
            suite_execution_id=str(row["id"]),
            attempt_number=attempt_number,
            envelope=envelope,
            leased_at=now,
            heartbeat_due_at=now + timedelta(seconds=HEARTBEAT_INTERVAL_SECONDS),
            lease_expires_at=expires_at,
        )

    # ------------------------------------------------------- attempt authority

    @staticmethod
    def _lock_attempt_scope(
        session: Session,
        principal: WorkerQueuePrincipal,
        credential: LeaseCredential,
    ) -> dict[str, Any]:
        locator = session.execute(
            text(
                "SELECT attempt.org_id, attempt.workspace_id, attempt.system_id, "
                "attempt.run_id, attempt.suite_execution_id, attempt.worker_identity_id "
                "FROM governance_evaluation_suite_attempts AS attempt "
                "JOIN governance_evaluation_worker_identities AS worker "
                "ON worker.id=attempt.worker_identity_id AND worker.org_id=attempt.org_id "
                "WHERE attempt.id=:attempt_id AND attempt.org_id=:org_id "
                "AND worker.principal_subject=:principal_subject"
            ),
            {"attempt_id": credential.attempt_id, "org_id": principal.organization_id,
             "principal_subject": principal.principal_subject},
        ).mappings().one_or_none()
        if locator is None:
            raise WorkerQueueError("lease_lost", _LEASE_LOST)
        scope = dict(locator)
        scope["attempt_id"] = credential.attempt_id
        scope["principal_subject"] = principal.principal_subject
        _lock_run_arbiter(session, scope["org_id"], scope["run_id"])
        # FOR UPDATE matches the evidence-admission lock on the same system row.
        system_id = session.scalar(
            text("SELECT id FROM governance_ai_systems WHERE id=:system_id "
                 "AND org_id=:org_id AND workspace_id=:workspace_id FOR UPDATE"), scope,
        )
        run_id = session.scalar(
            text("SELECT id FROM governance_evaluation_runs WHERE id=:run_id "
                 "AND org_id=:org_id AND workspace_id=:workspace_id "
                 "AND system_id=:system_id FOR UPDATE"), scope,
        )
        if system_id is None or run_id is None:
            raise WorkerQueueError("lease_lost", _LEASE_LOST)
        siblings = _lock_siblings(session, scope)
        suite = next((row for row in siblings if row["id"] == scope["suite_execution_id"]), None)
        attempt = session.execute(
            text("SELECT technical_status, attempt_number, lease_token_hash, "
                 "lease_expires_at, started_at "
                 "FROM governance_evaluation_suite_attempts WHERE id=:attempt_id "
                 "AND org_id=:org_id AND workspace_id=:workspace_id "
                 "AND system_id=:system_id AND run_id=:run_id "
                 "AND suite_execution_id=:suite_execution_id "
                 "AND worker_identity_id=:worker_identity_id FOR UPDATE"), scope,
        ).mappings().one_or_none()
        worker_status = session.scalar(
            text("SELECT status FROM governance_evaluation_worker_identities "
                 "WHERE id=:worker_identity_id AND org_id=:org_id "
                 "AND principal_subject=:principal_subject FOR SHARE"), scope,
        )
        if suite is None or attempt is None or worker_status is None:
            raise WorkerQueueError("lease_lost", _LEASE_LOST)
        run_cancelled, cancelled_suites = _cancelled_suites(session, scope)
        return {**scope, **attempt, "suite_status": suite["technical_status"],
                "attempt_count": suite["attempt_count"], "worker_status": worker_status,
                "cancelled": run_cancelled or scope["suite_execution_id"] in cancelled_suites}

    @staticmethod
    def _require_live(
        row: Mapping[str, Any],
        supplied_hash: str,
        now: datetime,
        statuses: frozenset[str],
    ) -> None:
        """Token first, so only the lease holder learns that its job was cancelled."""

        if not hmac.compare_digest(str(row["lease_token_hash"]), supplied_hash):
            raise WorkerQueueError("lease_lost", _LEASE_LOST)
        if row["cancelled"]:
            raise WorkerQueueError("job_cancelled", _JOB_CANCELLED)
        if (
            row["technical_status"] not in statuses
            or row["suite_status"] != row["technical_status"]
            or row["attempt_count"] != row["attempt_number"]
            or _stored_datetime(row["lease_expires_at"]) <= now
        ):
            raise WorkerQueueError("lease_lost", _LEASE_LOST)
        if row["worker_status"] != "active":
            raise WorkerQueueError("worker_inactive", _WORKER_INACTIVE)

    def _locked_live_attempt(
        self,
        session: Session,
        principal: WorkerQueuePrincipal,
        credential: LeaseCredential,
        statuses: frozenset[str],
    ) -> tuple[dict[str, Any], datetime]:
        supplied_hash = _lease_token_hash(credential.raw_token)
        row = self._lock_attempt_scope(session, principal, credential)
        now = _database_now(session)
        self._require_live(row, supplied_hash, now, statuses)
        return row, now

    def heartbeat(
        self,
        principal: WorkerQueuePrincipal,
        credential: LeaseCredential,
    ) -> HeartbeatReceipt:
        def operation(session: Session) -> HeartbeatReceipt:
            _row, now = self._locked_live_attempt(
                session, principal, credential, frozenset({"leased", "running"})
            )
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

        return self._transaction(operation)

    def start(
        self,
        principal: WorkerQueuePrincipal,
        credential: LeaseCredential,
    ) -> JobTransitionReceipt:
        def operation(session: Session) -> JobTransitionReceipt:
            row, now = self._locked_live_attempt(
                session, principal, credential, frozenset({"leased"})
            )
            values = {
                "now": _iso(now),
                "attempt_id": credential.attempt_id,
                "suite_execution_id": row["suite_execution_id"],
                "org_id": row["org_id"],
            }
            session.execute(
                text(
                    "UPDATE governance_evaluation_suite_attempts "
                    "SET technical_status='running', started_at=:now, updated_at=:now "
                    "WHERE id=:attempt_id AND org_id=:org_id AND technical_status='leased'"
                ),
                values,
            )
            session.execute(
                text(
                    "UPDATE governance_evaluation_run_suite_executions "
                    "SET technical_status='running', started_at=:now, updated_at=:now "
                    "WHERE id=:suite_execution_id AND org_id=:org_id "
                    "AND technical_status='leased'"
                ),
                values,
            )
            _project_run(session, org_id=row["org_id"], run_id=row["run_id"], now=now)
            return JobTransitionReceipt(
                attempt_id=credential.attempt_id,
                suite_execution_id=row["suite_execution_id"],
                technical_status="running",
                transitioned_at=now,
            )

        return self._transaction(operation)

    def fail(
        self,
        principal: WorkerQueuePrincipal,
        credential: LeaseCredential,
        failure_code: str,
    ) -> JobTransitionReceipt:
        projection = WORKER_FAILURE_PROJECTIONS.get(failure_code)
        if projection is None:
            raise WorkerQueueError(
                "failure_code_invalid",
                "The failure code is not an allowed worker failure code.",
            )
        evidence_result, message = projection

        def operation(session: Session) -> JobTransitionReceipt:
            row, now = self._locked_live_attempt(
                session, principal, credential, frozenset({"leased", "running"})
            )
            _update_attempt(
                session,
                attempt_id=credential.attempt_id,
                org_id=row["org_id"],
                status="failed",
                now=now,
                failure=(failure_code, message),
            )
            _terminalize_suite(
                session,
                suite_execution_id=row["suite_execution_id"],
                org_id=row["org_id"],
                status="failed",
                evidence_result=evidence_result,
                now=now,
                failure=(failure_code, message),
            )
            _project_run(session, org_id=row["org_id"], run_id=row["run_id"], now=now)
            _append_worker_audit(
                session,
                principal=principal,
                action="evaluation_v2.worker.attempt_failed",
                attempt_id=credential.attempt_id,
                details={
                    "schemaVersion": "evaluation-v2.worker-attempt-failed/v1",
                    "runId": row["run_id"],
                    "suiteExecutionId": row["suite_execution_id"],
                    "attemptId": credential.attempt_id,
                    "attemptNumber": row["attempt_number"],
                    "workerIdentityId": row["worker_identity_id"],
                    "failureCode": failure_code,
                    "failedAt": _iso(now),
                },
                now=now,
            )
            return JobTransitionReceipt(
                attempt_id=credential.attempt_id,
                suite_execution_id=row["suite_execution_id"],
                technical_status="failed",
                transitioned_at=now,
            )

        return self._transaction(operation)

    def complete(
        self,
        principal: WorkerQueuePrincipal,
        credential: LeaseCredential,
        raw_passport: bytes,
    ) -> CompletionReceipt:
        if self._evidence_admitter is None:
            raise WorkerQueueError(
                "completion_unavailable",
                "Signed worker completion is not configured.",
            )
        if (
            not isinstance(raw_passport, (bytes, bytearray))
            or not 0 < len(raw_passport) <= MAX_PASSPORT_BYTES
        ):
            raise WorkerQueueError("evidence_rejected", _EVIDENCE_REJECTED)
        raw = bytes(raw_passport)

        def operation(session: Session) -> CompletionReceipt:
            row, _now = self._locked_live_attempt(
                session, principal, credential, frozenset({"running"})
            )
            try:
                evidence = self._evidence_admitter(
                    session,
                    scope=EvidenceAdmissionScope(
                        organization_id=row["org_id"],
                        system_id=row["system_id"],
                        run_id=row["run_id"],
                        suite_execution_id=row["suite_execution_id"],
                    ),
                    actor_id=principal.principal_subject,
                    raw_passport=raw,
                    not_before=_stored_datetime(row["started_at"]),
                )
            except EvaluationWorkbenchError as error:
                raise WorkerQueueError("evidence_rejected", _EVIDENCE_REJECTED) from error
            completed_at = _database_now(session)
            # Verification takes time; the lease must still be live at the write.
            if _stored_datetime(row["lease_expires_at"]) <= completed_at:
                raise WorkerQueueError("lease_lost", _LEASE_LOST)
            linked = session.execute(
                text(
                    "SELECT technical_status, evidence_run_id, passport_revision_id "
                    "FROM governance_evaluation_run_suite_executions "
                    "WHERE id=:suite_execution_id AND org_id=:org_id"
                ),
                row,
            ).mappings().one()
            if (
                linked["technical_status"] != "succeeded"
                or linked["evidence_run_id"] != evidence.evidence_run_id
                or linked["passport_revision_id"] != evidence.passport_revision_id
            ):
                raise WorkerQueueError("completion_conflict", _PERSISTENCE_ERROR)
            updated = session.execute(
                text(
                    "UPDATE governance_evaluation_suite_attempts "
                    "SET technical_status='succeeded', completed_at=:now, updated_at=:now, "
                    "evidence_run_id=:evidence_run_id, "
                    "passport_revision_id=:passport_revision_id "
                    "WHERE id=:attempt_id AND org_id=:org_id AND technical_status='running'"
                ),
                {
                    "now": _iso(completed_at),
                    "evidence_run_id": evidence.evidence_run_id,
                    "passport_revision_id": evidence.passport_revision_id,
                    "attempt_id": credential.attempt_id,
                    "org_id": row["org_id"],
                },
            )
            if updated.rowcount != 1:
                raise WorkerQueueError("completion_conflict", _PERSISTENCE_ERROR)
            _append_worker_audit(
                session,
                principal=principal,
                action="evaluation_v2.worker.completion_succeeded",
                attempt_id=credential.attempt_id,
                details={
                    "schemaVersion": "evaluation-v2.worker-completion/v1",
                    "runId": row["run_id"],
                    "suiteExecutionId": row["suite_execution_id"],
                    "attemptId": credential.attempt_id,
                    "attemptNumber": row["attempt_number"],
                    "workerIdentityId": row["worker_identity_id"],
                    "admissionId": evidence.admission_id,
                    "evidenceRunId": evidence.evidence_run_id,
                    "passportRevisionId": evidence.passport_revision_id,
                    "suiteEvidenceLinkId": evidence.suite_evidence_link_id,
                    "passportContentHash": evidence.passport_content_hash,
                    "technicalStatus": "succeeded",
                    "evidenceResultStatus": evidence.evidence_result_status,
                    "completedAt": _iso(completed_at),
                },
                now=completed_at,
            )
            return CompletionReceipt(
                attempt_id=credential.attempt_id,
                suite_execution_id=row["suite_execution_id"],
                admission_id=evidence.admission_id,
                evidence_run_id=evidence.evidence_run_id,
                passport_revision_id=evidence.passport_revision_id,
                suite_evidence_link_id=evidence.suite_evidence_link_id,
                evidence_result_status=evidence.evidence_result_status,
                completed_at=completed_at,
            )

        return self._transaction(operation)

    # ----------------------------------------------------------- expiry sweep

    def recover_expired(self, organization_id: str, *, limit: int = 100) -> int:
        """Terminalize expired leases; requeue below the cap, never past a cancellation."""

        run_ids = self._transaction(
            lambda session: session.execute(
                text(
                    "SELECT run_id FROM governance_evaluation_suite_attempts "
                    "WHERE org_id=:org_id AND technical_status IN ('leased', 'running') "
                    "AND lease_expires_at::TIMESTAMPTZ <= pg_catalog.clock_timestamp() "
                    "GROUP BY run_id ORDER BY min(lease_expires_at), run_id LIMIT :limit"
                ),
                {"org_id": organization_id, "limit": max(1, min(int(limit), 1000))},
            ).scalars().all()
        )
        return sum(
            self._transaction(
                lambda session, run_id=run_id: self._recover_run(
                    session, organization_id, run_id
                )
            )
            for run_id in run_ids
        )

    @staticmethod
    def _recover_run(session: Session, org_id: str, run_id: str) -> int:
        if not _lock_run_arbiter(session, org_id, run_id, wait=False):
            return 0
        run = session.execute(
            text(
                "SELECT id AS run_id, org_id, workspace_id, system_id "
                "FROM governance_evaluation_runs "
                "WHERE id=:run_id AND org_id=:org_id FOR UPDATE"
            ),
            {"run_id": run_id, "org_id": org_id},
        ).mappings().one_or_none()
        if run is None:
            return 0
        siblings = {row["id"]: row for row in _lock_siblings(session, run)}
        run_cancelled, cancelled_suites = _cancelled_suites(session, run)
        now = _database_now(session)
        attempts = session.execute(
            text(
                "SELECT id, suite_execution_id, attempt_number "
                "FROM governance_evaluation_suite_attempts "
                "WHERE run_id=:run_id AND org_id=:org_id "
                "AND technical_status IN ('leased', 'running') "
                "AND lease_expires_at::TIMESTAMPTZ <= :now ORDER BY id FOR UPDATE"
            ),
            {"run_id": run_id, "org_id": org_id, "now": now},
        ).mappings().all()
        for attempt in attempts:
            suite = siblings.get(attempt["suite_execution_id"])
            if (
                suite is None
                or suite["technical_status"] not in {"leased", "running"}
                or int(attempt["attempt_number"]) != int(suite["attempt_count"])
                or not 1 <= int(suite["max_attempts"]) <= 3
            ):
                raise WorkerQueueError("binding_integrity_error", _PERSISTENCE_ERROR)
            if run_cancelled or suite["id"] in cancelled_suites:
                # Finalize the committed cancellation; an expired lease never requeues it.
                _cancel_suite(session, suite_execution_id=suite["id"], org_id=org_id, now=now)
                continue
            _update_attempt(
                session,
                attempt_id=attempt["id"],
                org_id=org_id,
                status="timed_out",
                now=now,
                failure=(_LEASE_EXPIRED_CODE, LEASE_EXPIRED_PROJECTION[1]),
            )
            # ponytail: frozen 013a forbids running -> queued, so an expired
            # running job is terminal; leased jobs requeue below the stored cap.
            if suite["technical_status"] == "leased" and int(suite["attempt_count"]) < int(
                suite["max_attempts"]
            ):
                session.execute(
                    text(
                        "UPDATE governance_evaluation_run_suite_executions "
                        "SET technical_status='queued', updated_at=:now "
                        "WHERE id=:suite_execution_id AND org_id=:org_id "
                        "AND technical_status='leased'"
                    ),
                    {"now": _iso(now), "suite_execution_id": suite["id"], "org_id": org_id},
                )
            else:
                _terminalize_suite(
                    session,
                    suite_execution_id=suite["id"],
                    org_id=org_id,
                    status="timed_out",
                    evidence_result=LEASE_EXPIRED_PROJECTION[0],
                    now=now,
                    failure=(_LEASE_EXPIRED_CODE, LEASE_EXPIRED_PROJECTION[1]),
                )
        if attempts:
            _project_run(session, org_id=org_id, run_id=run_id, now=now)
        return len(attempts)


class PostgresEvaluationCancellationRepository:
    """Cancellation authority bound to the caller's audited mutation session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _error(code: str, message: str, status_code: int) -> EvaluationWorkbenchError:
        return EvaluationWorkbenchError(code, message, status_code=status_code)

    def request_cancellation(
        self,
        command: PersistCancellationCommand,
    ) -> CancellationRecord:
        session = self._session
        if session.get_bind().dialect.name != "postgresql":
            raise self._error(
                "postgres_required",
                "Evaluation cancellation requires PostgreSQL.",
                503,
            )
        scope = {
            "org_id": command.scope.organization_id,
            "workspace_id": command.scope.workspace_id,
            "system_id": command.scope.system_id,
            "run_id": command.scope.run_id,
        }
        not_found = self._error(
            "evaluation_run_not_found",
            "The evaluation run was not found in this scope.",
            404,
        )
        _lock_run_arbiter(session, scope["org_id"], scope["run_id"])
        system_id = session.scalar(
            text("SELECT id FROM governance_ai_systems WHERE id=:system_id "
                 "AND org_id=:org_id AND workspace_id=:workspace_id FOR UPDATE"), scope,
        )
        run_id = session.scalar(
            text("SELECT id FROM governance_evaluation_runs WHERE id=:run_id "
                 "AND org_id=:org_id AND workspace_id=:workspace_id "
                 "AND system_id=:system_id AND contract_version='2.0.0' FOR UPDATE"), scope,
        )
        if system_id is None or run_id is None:
            raise not_found
        siblings = _lock_siblings(session, scope)
        if command.scope_kind == "suite" and not any(
            row["id"] == command.suite_execution_id for row in siblings
        ):
            raise not_found
        run_cancelled, cancelled_suites = _cancelled_suites(session, scope)
        now = _database_now(session)
        targets = [
            row["id"]
            for row in siblings
            if row["technical_status"] not in _TERMINAL
            and (command.scope_kind == "run" or row["id"] == command.suite_execution_id)
        ]
        if not targets:
            raise self._error(
                "evaluation_cancellation_not_applicable",
                "Only a non-terminal evaluation job can be cancelled.",
                409,
            )
        existing = (
            run_cancelled
            if command.scope_kind == "run"
            else command.suite_execution_id in cancelled_suites
        )
        cancellation_id = command.cancellation_id
        if existing:
            # A recorded but unfinalized request is completed, never duplicated.
            cancellation_id = session.scalar(
                text(
                    "SELECT id FROM governance_evaluation_cancellations "
                    "WHERE org_id=:org_id AND run_id=:run_id "
                    "AND suite_execution_id IS NOT DISTINCT FROM :suite_execution_id"
                ),
                {**scope, "suite_execution_id": command.suite_execution_id},
            )
        else:
            try:
                with session.begin_nested():
                    session.execute(
                        text(
                            "INSERT INTO governance_evaluation_cancellations "
                            "(id, org_id, workspace_id, system_id, run_id, "
                            "suite_execution_id, scope_kind, requested_by, requested_at, reason) "
                            "VALUES (:id, :org_id, :workspace_id, :system_id, :run_id, "
                            ":suite_execution_id, :scope_kind, :requested_by, "
                            ":requested_at, :reason)"
                        ),
                        {
                            **scope,
                            "id": cancellation_id,
                            "suite_execution_id": command.suite_execution_id,
                            "scope_kind": command.scope_kind,
                            "requested_by": command.actor_id,
                            "requested_at": _iso(now),
                            "reason": command.reason,
                        },
                    )
            except IntegrityError as error:
                raise self._error(
                    "evaluation_cancellation_conflict",
                    "The cancellation request could not be recorded.",
                    409,
                ) from error
        cancelled_attempts = tuple(
            attempt_id
            for attempt_id in (
                _cancel_suite(session, suite_execution_id=suite_id, org_id=scope["org_id"], now=now)
                for suite_id in targets
            )
            if attempt_id is not None
        )
        run_status = _project_run(session, org_id=scope["org_id"], run_id=scope["run_id"], now=now)
        statuses = session.execute(
            text(
                "SELECT id, technical_status FROM governance_evaluation_run_suite_executions "
                "WHERE run_id=:run_id AND org_id=:org_id ORDER BY ordinal, id"
            ),
            scope,
        ).all()
        return CancellationRecord(
            cancellation_id=str(cancellation_id),
            scope_kind=command.scope_kind,
            suite_execution_id=command.suite_execution_id,
            requested_by=command.actor_id,
            requested_at=now,
            run_technical_status=run_status,
            suite_statuses=tuple((str(row[0]), str(row[1])) for row in statuses),
            cancelled_attempt_ids=cancelled_attempts,
        )


__all__ = [
    "EvidenceAdmitter",
    "PostgresEvaluationCancellationRepository",
    "PostgresEvaluationWorkerQueue",
]
