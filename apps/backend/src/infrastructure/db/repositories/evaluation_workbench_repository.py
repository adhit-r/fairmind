"""SQLAlchemy adapter for the immutable assurance-contract v2 workbench."""

from __future__ import annotations

import hashlib
import json
import threading
import uuid
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping

from sqlalchemy import insert, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.governance_models import (
    GovernanceAISystem,
    GovernanceEvaluationAuditEvent,
    GovernanceEvaluationPlan,
    GovernanceEvaluationPlanSuite,
    GovernanceEvaluationRun,
    GovernanceEvaluationRunSuiteExecution,
    GovernanceEvaluationSuiteVersion,
    GovernanceEvaluationTargetVersion,
    GovernanceEvidenceTrustPolicyVersion,
    GovernanceIdempotencyRecord,
    GovernanceWorkspace,
)
from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationCommand,
    MutationOutcome,
    MutationResult,
    PersistPlanCommand,
    PersistRunCommand,
    PersistSuiteCommand,
    PersistTargetCommand,
    PlanBindingRecord,
    PlanCreationBindings,
    PlanGraphRecord,
    PlanSuiteBindingRecord,
    RunRecord,
    SuiteBindingRecord,
    SuiteExecutionRecord,
    SystemScopeRecord,
    TargetBindingRecord,
    TrustPolicyBindingRecord,
)
from src.domain.assurance.evaluation_v2 import (
    CONTRACT_VERSION,
    LAYER_VERDICTS_SCHEMA_VERSION,
    MAX_BUDGETS_BYTES,
    MAX_CONFIGURATION_DEFAULTS_BYTES,
    MAX_CONFIGURATION_SCHEMA_BYTES,
    MAX_EXECUTION_ENVELOPE_BYTES,
    MAX_MUTATION_DETAIL_BODY_BYTES,
    MAX_SAFE_ARRAY_ITEMS,
    MAX_SUITE_CONFIGURATION_BYTES,
    MAX_SUITE_LIMITATIONS_BYTES,
    MAX_SUITE_MANIFEST_BYTES,
    MAX_TARGET_MANIFEST_BYTES,
    AssuranceContractValidationError,
    canonical_json,
    canonical_sha256,
    reject_sensitive_keys,
    validate_public_safe_values,
)
from src.infrastructure.db.repositories.evaluation_audit_chain import (
    EvaluationAuditAppend,
    EvaluationAuditChainIntegrityError,
    EvaluationAuditReceipt,
    append_evaluation_audit_event,
    verify_evaluation_audit_chain,
)

_SQLITE_WRITE_LOCK = threading.RLock()
_BINDING_INTEGRITY_MESSAGE = "Stored assurance bindings failed integrity verification."
_AUDIT_CHAIN_INTEGRITY_MESSAGE = "Stored evaluation audit chain failed integrity verification."
_REJECTED_IDEMPOTENCY_MARKER = "_fairmindEvaluationMutationRejected"
_REJECTED_AUDIT_SCHEMA_VERSION = "evaluation-v2.rejected-mutation-audit/v2"
_REJECTED_RESPONSE_SCHEMA_VERSION = "evaluation-v2.rejected-idempotency-response/v2"
_REJECTED_AUDIT_ACTION = "evaluation_v2.mutation.rejected"
_REJECTED_AUDIT_RESOURCE_TYPE = "evaluation_idempotency_key_hash"
_REJECTED_IDEMPOTENCY_RESOURCE_TYPE = "evaluation_rejected_audit_event"
_SUCCESS_IDEMPOTENCY_MARKER = "_fairmindEvaluationMutationSucceeded"
_SUCCESS_AUDIT_BINDING_KEY = "_fairmindEvaluationSuccessBinding"
_SUCCESS_AUDIT_SCHEMA_VERSION = "evaluation-v2.success-idempotency-audit/v1"
_SUCCESS_RESPONSE_SCHEMA_VERSION = "evaluation-v2.success-idempotency-response/v1"
_SUCCESS_NOOP_AUDIT_ACTION = "evaluation_v2.mutation.noop"
_GENERIC_REJECTION_CODE = "evaluation_rejected"
_GENERIC_REJECTION_MESSAGE = "The assurance mutation was rejected."
_MAX_REJECTION_RESPONSE_BYTES = 32 * 1024
_MAX_IDEMPOTENCY_RESPONSE_BODY_BYTES = MAX_MUTATION_DETAIL_BODY_BYTES
_MAX_IDEMPOTENCY_RESPONSE_BYTES = _MAX_IDEMPOTENCY_RESPONSE_BODY_BYTES + 4 * 1024
_MAX_LAYER_VERDICTS_BYTES = 8 * 1024
_MAX_SUITE_RESULT_SUMMARY_BYTES = 64 * 1024
_MAX_BINDING_LIST_BYTES = 8 * 1024
_MAX_TRUST_POLICY_BYTES = 64 * 1024
_MAX_STORED_JSON_DEPTH = 32
_MAX_STORED_JSON_ITEMS = MAX_SAFE_ARRAY_ITEMS
_MAX_IDEMPOTENCY_RESPONSE_ITEMS = (
    (_MAX_IDEMPOTENCY_RESPONSE_BYTES // 2) + _MAX_STORED_JSON_DEPTH + 16
)
_IDEMPOTENCY_RETENTION = timedelta(days=30)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None = None) -> str:
    return (value or _now()).isoformat()


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _json_load(value: str | None, fallback: Any) -> Any:
    if value is None:
        return fallback
    return json.loads(value)


def _audit_safe_code(value: object) -> str:
    if (
        isinstance(value, str)
        and 1 <= len(value) <= 128
        and value.isascii()
        and all(character.isalnum() or character in "_.-" for character in value)
    ):
        return value
    return "evaluation_rejected"


def _audit_safe_operation(value: object) -> str:
    if (
        isinstance(value, str)
        and 1 <= len(value) <= 160
        and value.isascii()
        and all(character.isalnum() or character in "_.-" for character in value)
    ):
        return value
    return "evaluation-v2.unknown"


def _audit_safe_request_hash(value: object) -> str:
    if (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    ):
        return value
    return hashlib.sha256(b"invalid-request-hash").hexdigest()


def _idempotency_key_hash(value: str) -> str:
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def _safe_rejection_status(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and 400 <= value <= 499:
        return value
    return 500


def _safe_rejection_error(error: EvaluationWorkbenchError) -> EvaluationWorkbenchError:
    """Return an isolated public/idempotency-safe rejection without secret context."""

    try:
        if _audit_safe_code(error.code) != error.code:
            raise ValueError("unsafe rejection code")
        if (
            not isinstance(error.status_code, int)
            or isinstance(error.status_code, bool)
            or not 400 <= error.status_code <= 499
        ):
            raise ValueError("unsafe rejection status")
        status_code = error.status_code
        body = error.detail()
        reject_sensitive_keys(body)
        validate_public_safe_values(body)
        encoded = canonical_json(body)
        if len(encoded.encode("utf-8")) > _MAX_REJECTION_RESPONSE_BYTES:
            raise ValueError("rejection response exceeds its bounded contract")
        isolated = json.loads(encoded)
        if not isinstance(isolated, dict):
            raise ValueError("rejection response is not an object")
        code = isolated.get("code")
        message = isolated.get("message")
        details = isolated.get("details")
        if (
            not isinstance(code, str)
            or not isinstance(message, str)
            or (details is not None and not isinstance(details, dict))
        ):
            raise ValueError("rejection response has an invalid shape")
        safe = EvaluationWorkbenchError(
            code,
            message,
            status_code=status_code,
            details=details,
        )
    except (
        AssuranceContractValidationError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        safe = EvaluationWorkbenchError(
            _GENERIC_REJECTION_CODE,
            _GENERIC_REJECTION_MESSAGE,
            status_code=_safe_rejection_status(error.status_code),
        )
    safe.__cause__ = None
    safe.__context__ = None
    safe.__suppress_context__ = True
    return safe


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object name")
        result[key] = value
    return result


def _reject_json_constant(_value: str) -> None:
    raise ValueError("non-finite JSON number")


def _validate_stored_json_shape(
    value: object,
    *,
    maximum_items: int = _MAX_STORED_JSON_ITEMS,
) -> None:
    if not isinstance(maximum_items, int) or isinstance(maximum_items, bool) or maximum_items < 1:
        raise ValueError("stored JSON item limit is invalid")
    pending: list[tuple[object, int]] = [(value, 1)]
    item_count = -1
    while pending:
        current, depth = pending.pop()
        if depth > _MAX_STORED_JSON_DEPTH:
            raise ValueError("stored JSON exceeds its depth limit")
        item_count += 1
        if item_count > maximum_items:
            raise ValueError("stored JSON exceeds its aggregate item limit")
        if isinstance(current, dict):
            pending.extend((child, depth + 1) for child in current.values())
        elif isinstance(current, list):
            pending.extend((child, depth + 1) for child in current)


def _exact_canonical_json_value(
    raw: object,
    *,
    maximum_bytes: int,
    expected_type: type[dict] | type[list],
    maximum_items: int = _MAX_STORED_JSON_ITEMS,
) -> dict[str, Any] | list[Any]:
    """Decode bounded persisted JSON without accepting alternate serializations."""

    if not isinstance(raw, str) or maximum_bytes < 1:
        raise ValueError("stored JSON must be bounded text")
    encoded = raw.encode("utf-8")
    if len(encoded) > maximum_bytes:
        raise ValueError("stored JSON exceeds its byte budget")
    decoded = json.loads(
        encoded,
        object_pairs_hook=_unique_json_object,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(decoded, expected_type):
        raise ValueError("stored JSON has the wrong root type")
    _validate_stored_json_shape(decoded, maximum_items=maximum_items)
    if canonical_json(decoded) != raw:
        raise ValueError("stored JSON is not exact canonical JSON")
    return decoded


def _validate_idempotency_generation(*, claimed_at: str, expires_at: str) -> None:
    if not isinstance(claimed_at, str) or not isinstance(expires_at, str):
        raise ValueError("idempotency generation timestamps must be text")
    claimed = _parse_timestamp(claimed_at)
    expiry = _parse_timestamp(expires_at)
    if (
        claimed.utcoffset() != timedelta(0)
        or expiry.utcoffset() != timedelta(0)
        or claimed.isoformat() != claimed_at
        or expiry.isoformat() != expires_at
        or expiry != claimed + _IDEMPOTENCY_RETENTION
    ):
        raise ValueError("idempotency generation timestamps are not exact")


def _rejected_response_material(
    error: EvaluationWorkbenchError,
    *,
    claimed_at: str,
    expires_at: str,
) -> tuple[dict[str, object], str, str]:
    _validate_idempotency_generation(
        claimed_at=claimed_at,
        expires_at=expires_at,
    )
    body: dict[str, object] = {
        _REJECTED_IDEMPOTENCY_MARKER: True,
        "error": error.detail(),
    }
    body_json = canonical_json(body)
    if len(body_json.encode("utf-8")) > _MAX_REJECTION_RESPONSE_BYTES:
        raise ValueError("rejection response exceeds its bounded contract")
    response_hash = canonical_sha256(
        {
            "schemaVersion": _REJECTED_RESPONSE_SCHEMA_VERSION,
            "claimedAt": claimed_at,
            "expiresAt": expires_at,
            "responseStatus": error.status_code,
            "responseBody": body,
        }
    )
    return body, body_json, response_hash


def _success_response_material(
    *,
    body: Mapping[str, object],
    status: object,
    audit_event_id: str,
    claimed_at: str,
    expires_at: str,
    resource_type: object,
    resource_id: object,
) -> tuple[dict[str, Any], str]:
    """Return one bounded public response and its semantic success digest."""

    try:
        if str(uuid.UUID(audit_event_id)) != audit_event_id:
            raise ValueError("success audit-event identity is not canonical")
    except (AttributeError, TypeError, ValueError):
        raise ValueError("success audit-event identity is invalid") from None
    _validate_idempotency_generation(
        claimed_at=claimed_at,
        expires_at=expires_at,
    )
    if (
        not isinstance(resource_type, str)
        or not resource_type
        or not isinstance(resource_id, str)
        or not resource_id
    ):
        raise ValueError("success resource identity is invalid")
    if not isinstance(status, int) or isinstance(status, bool) or not 200 <= status <= 299:
        raise ValueError("success response status is invalid")
    isolated_json = canonical_json(dict(body))
    isolated = _exact_canonical_json_value(
        isolated_json,
        maximum_bytes=_MAX_IDEMPOTENCY_RESPONSE_BODY_BYTES,
        expected_type=dict,
        maximum_items=_MAX_IDEMPOTENCY_RESPONSE_ITEMS,
    )
    if _REJECTED_IDEMPOTENCY_MARKER in isolated or _SUCCESS_IDEMPOTENCY_MARKER in isolated:
        raise ValueError("success response contains a reserved member")
    response_hash = canonical_sha256(
        {
            "schemaVersion": _SUCCESS_RESPONSE_SCHEMA_VERSION,
            "auditEventId": audit_event_id,
            "claimedAt": claimed_at,
            "expiresAt": expires_at,
            "resourceType": resource_type,
            "resourceId": resource_id,
            "responseStatus": status,
            "responseBody": isolated,
        }
    )
    return isolated, response_hash


def _success_idempotency_wrapper(
    *,
    response_body: Mapping[str, object],
    audit_event_id: str,
) -> tuple[dict[str, object], str]:
    try:
        if str(uuid.UUID(audit_event_id)) != audit_event_id:
            raise ValueError("success audit-event identity is not canonical")
    except (AttributeError, TypeError, ValueError):
        raise ValueError("success audit-event identity is invalid")
    wrapper: dict[str, object] = {
        _SUCCESS_IDEMPOTENCY_MARKER: True,
        "auditEventId": audit_event_id,
        "responseBody": dict(response_body),
    }
    wrapper_json = canonical_json(wrapper)
    _exact_canonical_json_value(
        wrapper_json,
        maximum_bytes=_MAX_IDEMPOTENCY_RESPONSE_BYTES,
        expected_type=dict,
        maximum_items=_MAX_IDEMPOTENCY_RESPONSE_ITEMS,
    )
    return wrapper, wrapper_json


class SqlAlchemyEvaluationWorkbenchRepository:
    """Implements scoped loads, CAS transitions, and atomic graph inserts."""

    def __init__(self, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("SQLAlchemy Session required")
        self.db = session

    # ------------------------------------------------------------------
    # Shared transaction, idempotency, audit, and integrity primitives.
    # ------------------------------------------------------------------

    def _error(
        self,
        code: str,
        message: str,
        status_code: int,
        *,
        details: dict[str, Any] | None = None,
    ) -> EvaluationWorkbenchError:
        return EvaluationWorkbenchError(code, message, status_code=status_code, details=details)

    def _system_scope(
        self, org_id: str, system_id: str, *, lock: bool = False
    ) -> Mapping[str, Any] | None:
        systems = GovernanceAISystem.__table__
        workspaces = GovernanceWorkspace.__table__
        statement = (
            select(
                systems.c.id.label("system_id"),
                systems.c.workspace_id,
                systems.c.org_id,
            )
            .select_from(
                systems.join(
                    workspaces,
                    (workspaces.c.id == systems.c.workspace_id)
                    & (workspaces.c.org_id == systems.c.org_id),
                )
            )
            .where(
                systems.c.id == system_id,
                systems.c.org_id == org_id,
                workspaces.c.org_id == org_id,
            )
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.execute(statement).mappings().one_or_none()

    # --------------------------------------------------------------
    # Target catalog.
    # --------------------------------------------------------------

    def load_system_scope(
        self,
        *,
        org_id: str,
        system_id: str,
        lock: bool,
    ) -> SystemScopeRecord | None:
        row = self._system_scope(org_id, system_id, lock=lock)
        return self._scope_record(row) if row is not None else None

    def target_identity_exists(
        self,
        *,
        scope: SystemScopeRecord,
        target_key: str,
        version: str,
    ) -> bool:
        targets = GovernanceEvaluationTargetVersion.__table__
        return (
            self.db.execute(
                select(targets.c.id).where(
                    targets.c.org_id == scope.organization_id,
                    targets.c.workspace_id == scope.workspace_id,
                    targets.c.system_id == scope.system_id,
                    targets.c.target_key == target_key,
                    targets.c.version == version,
                )
            ).scalar_one_or_none()
            is not None
        )

    def load_target_binding(
        self,
        *,
        scope: SystemScopeRecord,
        target_version_id: str,
        lock: bool,
    ) -> TargetBindingRecord | None:
        row = self._target_row(
            org_id=scope.organization_id,
            workspace_id=scope.workspace_id,
            system_id=scope.system_id,
            target_id=target_version_id,
            lock=lock,
        )
        return self._target_binding(row) if row is not None else None

    def cas_supersede_target(self, target: TargetBindingRecord) -> None:
        targets = GovernanceEvaluationTargetVersion.__table__
        result = self.db.execute(
            update(targets)
            .where(
                targets.c.id == target.id,
                targets.c.org_id == target.organization_id,
                targets.c.workspace_id == target.workspace_id,
                targets.c.system_id == target.system_id,
                targets.c.status == "active",
            )
            .values(status="superseded")
        )
        if result.rowcount != 1:
            raise self._error(
                "supersedes_state_conflict",
                "The prior target is no longer active and cannot be superseded.",
                409,
            )

    def persist_target(self, command: PersistTargetCommand) -> TargetBindingRecord:
        target = command.requested.to_dict()
        scope = command.scope
        targets = GovernanceEvaluationTargetVersion.__table__
        self.db.execute(
            insert(targets).values(
                id=command.target_id,
                org_id=scope.organization_id,
                workspace_id=scope.workspace_id,
                system_id=scope.system_id,
                target_key=target["targetKey"],
                target_kind=target["targetKind"],
                version=target["version"],
                system_version=target["systemVersion"],
                subject_kind=target["subjectKind"],
                subject_id=target["subjectId"],
                subject_version=target["subjectVersion"],
                subject_digest=target["subjectDigest"],
                deployment_id=target.get("deploymentId"),
                connector_binding_id=target.get("connectorBindingId"),
                manifest_json=target["manifestJson"],
                manifest_digest=target["manifestDigest"],
                status="active",
                supersedes_id=target.get("supersedesId"),
                created_by=command.actor_id,
                created_at=command.created_at,
            )
        )
        row = (
            self.db.execute(
                select(targets).where(
                    targets.c.id == command.target_id,
                    targets.c.org_id == scope.organization_id,
                    targets.c.workspace_id == scope.workspace_id,
                    targets.c.system_id == scope.system_id,
                )
            )
            .mappings()
            .one()
        )
        return self._target_binding(row)

    def list_target_bindings(
        self,
        *,
        org_id: str,
        system_id: str,
    ) -> list[TargetBindingRecord] | None:
        scope = self._system_scope(org_id, system_id)
        if scope is None:
            return None
        targets = GovernanceEvaluationTargetVersion.__table__
        rows = (
            self.db.execute(
                select(targets)
                .where(
                    targets.c.org_id == org_id,
                    targets.c.workspace_id == scope["workspace_id"],
                    targets.c.system_id == system_id,
                )
                .order_by(targets.c.created_at.desc(), targets.c.id.desc())
            )
            .mappings()
            .all()
        )
        return [self._target_binding(row) for row in rows]

    # --------------------------------------------------------------
    # Suite catalog.
    # --------------------------------------------------------------

    def suite_identity_exists(
        self,
        *,
        org_id: str,
        namespace: str,
        name: str,
        version: str,
    ) -> bool:
        suites = GovernanceEvaluationSuiteVersion.__table__
        return (
            self.db.execute(
                select(suites.c.id).where(
                    suites.c.owner_scope == org_id,
                    suites.c.namespace == namespace,
                    suites.c.name == name,
                    suites.c.version == version,
                )
            ).scalar_one_or_none()
            is not None
        )

    def persist_suite(self, command: PersistSuiteCommand) -> SuiteBindingRecord:
        suite = command.requested.to_dict()
        suites = GovernanceEvaluationSuiteVersion.__table__
        self.db.execute(
            insert(suites).values(
                id=command.suite_id,
                owner_org_id=command.organization_id,
                owner_scope=command.organization_id,
                namespace=suite["namespace"],
                name=suite["name"],
                version=suite["version"],
                suite_ref=suite["suiteRef"],
                manifest_json=suite["manifestJson"],
                manifest_digest=suite["manifestDigest"],
                target_kinds_json=canonical_json(suite["supportedTargetKinds"]),
                subject_kinds_json=canonical_json(suite["supportedSubjectKinds"]),
                lifecycle_phases_json=canonical_json(suite["lifecyclePhases"]),
                execution_depths_json=canonical_json(suite["executionDepths"]),
                delivery_modes_json=canonical_json(suite["deliveryModes"]),
                worker_type=suite["workerType"],
                runner_image_digest=suite.get("runnerImageDigest"),
                adapter_name=suite["adapterName"],
                adapter_version=suite["adapterVersion"],
                configuration_schema_json=canonical_json(suite["configurationSchema"]),
                configuration_defaults_json=canonical_json(suite["configurationDefaults"]),
                required_input_roles_json=canonical_json(suite["requiredInputRoles"]),
                default_budgets_json=canonical_json(suite["budgets"]),
                result_contract_version=suite["resultContractVersion"],
                status="draft",
                created_by=command.actor_id,
                created_at=command.created_at,
            )
        )
        row = (
            self.db.execute(
                select(suites).where(
                    suites.c.id == command.suite_id,
                    suites.c.owner_scope == command.organization_id,
                )
            )
            .mappings()
            .one()
        )
        return self._suite_binding(row)

    def list_suite_bindings(self, *, org_id: str) -> list[SuiteBindingRecord]:
        suites = GovernanceEvaluationSuiteVersion.__table__
        rows = (
            self.db.execute(
                select(suites)
                .where(suites.c.owner_scope.in_(["platform", org_id]))
                .order_by(suites.c.namespace, suites.c.name, suites.c.version)
            )
            .mappings()
            .all()
        )
        return [self._suite_binding(row) for row in rows]

    def _suite_row(self, *, org_id: str, suite_version_id: str, lock: bool = False):
        suites = GovernanceEvaluationSuiteVersion.__table__
        statement = select(suites).where(
            suites.c.id == suite_version_id,
            suites.c.owner_scope.in_(["platform", org_id]),
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.execute(statement).mappings().one_or_none()

    def load_suite_binding(
        self,
        *,
        org_id: str,
        suite_version_id: str,
        lock: bool,
    ) -> SuiteBindingRecord | None:
        row = self._suite_row(
            org_id=org_id,
            suite_version_id=suite_version_id,
            lock=lock,
        )
        return self._suite_binding(row) if row is not None else None

    def cas_activate_suite(
        self,
        *,
        suite: SuiteBindingRecord,
    ) -> SuiteBindingRecord:
        if suite.status == "draft":
            result = self.db.execute(
                update(GovernanceEvaluationSuiteVersion.__table__)
                .where(
                    GovernanceEvaluationSuiteVersion.id == suite.id,
                    GovernanceEvaluationSuiteVersion.owner_scope == suite.owner_scope,
                    GovernanceEvaluationSuiteVersion.status == "draft",
                )
                .values(status="active")
            )
            if result.rowcount != 1:
                raise self._error(
                    "suite_state_changed",
                    "Suite state changed concurrently.",
                    409,
                )
        updated = self._suite_row(
            org_id=suite.owner_scope,
            suite_version_id=suite.id,
            lock=True,
        )
        if updated is None:
            raise RuntimeError("activated suite could not be reloaded")
        return self._suite_binding(updated)

    # --------------------------------------------------------------
    # Bound plans and preflight.
    # --------------------------------------------------------------

    def _target_row(
        self, *, org_id: str, workspace_id: str, system_id: str, target_id: str, lock=False
    ):
        targets = GovernanceEvaluationTargetVersion.__table__
        statement = select(targets).where(
            targets.c.id == target_id,
            targets.c.org_id == org_id,
            targets.c.workspace_id == workspace_id,
            targets.c.system_id == system_id,
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.execute(statement).mappings().one_or_none()

    def _trust_row(self, *, org_id: str, trust_id: str, lock=False):
        policies = GovernanceEvidenceTrustPolicyVersion.__table__
        statement = select(policies).where(policies.c.id == trust_id, policies.c.org_id == org_id)
        if lock:
            statement = statement.with_for_update()
        return self.db.execute(statement).mappings().one_or_none()

    def _plan_row(
        self, *, org_id: str, workspace_id: str, system_id: str, plan_id: str, lock=False
    ):
        plans = GovernanceEvaluationPlan.__table__
        statement = select(plans).where(
            plans.c.id == plan_id,
            plans.c.org_id == org_id,
            plans.c.workspace_id == workspace_id,
            plans.c.system_id == system_id,
            plans.c.contract_version == CONTRACT_VERSION,
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.execute(statement).mappings().one_or_none()

    def _bound_suites(
        self,
        plan_id: str,
        org_id: str,
        workspace_id: str,
        system_id: str,
        *,
        lock=False,
    ):
        selections = GovernanceEvaluationPlanSuite.__table__
        suites = GovernanceEvaluationSuiteVersion.__table__
        statement = (
            select(
                selections.c.ordinal,
                selections.c.configuration_json,
                selections.c.configuration_hash,
                *[column for column in suites.c],
            )
            .select_from(
                selections.join(
                    suites,
                    (suites.c.id == selections.c.suite_version_id)
                    & (suites.c.owner_scope == selections.c.suite_owner_scope),
                )
            )
            .where(
                selections.c.plan_id == plan_id,
                selections.c.org_id == org_id,
                selections.c.workspace_id == workspace_id,
                selections.c.system_id == system_id,
                selections.c.suite_owner_scope.in_(["platform", org_id]),
            )
            .order_by(selections.c.ordinal)
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.execute(statement).mappings().all()

    @staticmethod
    def _scope_record(row: Mapping[str, Any]) -> SystemScopeRecord:
        return SystemScopeRecord(
            organization_id=row["org_id"],
            workspace_id=row["workspace_id"],
            system_id=row["system_id"],
        )

    def _target_binding(self, row: Mapping[str, Any]) -> TargetBindingRecord:
        return TargetBindingRecord(
            id=row["id"],
            organization_id=row["org_id"],
            workspace_id=row["workspace_id"],
            system_id=row["system_id"],
            target_key=row["target_key"],
            target_kind=row["target_kind"],
            version=row["version"],
            system_version=row["system_version"],
            subject_kind=row["subject_kind"],
            subject_id=row["subject_id"],
            subject_version=row["subject_version"],
            subject_digest=row["subject_digest"],
            deployment_id=row["deployment_id"],
            connector_binding_id=row["connector_binding_id"],
            manifest=self._stored_json_object(
                row["manifest_json"],
                maximum_bytes=MAX_TARGET_MANIFEST_BYTES,
            ),
            manifest_digest=row["manifest_digest"],
            status=row["status"],
            supersedes_id=row["supersedes_id"],
            created_by=row["created_by"],
            created_at=row["created_at"],
        )

    def _trust_binding(self, row: Mapping[str, Any]) -> TrustPolicyBindingRecord:
        return TrustPolicyBindingRecord(
            id=row["id"],
            organization_id=row["org_id"],
            version=row["version"],
            policy=self._stored_json_object(
                row["policy_json"],
                maximum_bytes=_MAX_TRUST_POLICY_BYTES,
            ),
            policy_hash=row["policy_hash"],
            status=row["status"],
        )

    def _suite_binding(self, row: Mapping[str, Any]) -> SuiteBindingRecord:
        return SuiteBindingRecord(
            id=row["id"],
            owner_organization_id=row["owner_org_id"],
            owner_scope=row["owner_scope"],
            namespace=row["namespace"],
            name=row["name"],
            version=row["version"],
            suite_ref=row["suite_ref"],
            manifest=self._stored_json_object(
                row["manifest_json"],
                maximum_bytes=MAX_SUITE_MANIFEST_BYTES,
            ),
            manifest_digest=row["manifest_digest"],
            target_kinds=self._stored_string_array(
                row["target_kinds_json"], maximum_bytes=_MAX_BINDING_LIST_BYTES
            ),
            subject_kinds=self._stored_string_array(
                row["subject_kinds_json"], maximum_bytes=_MAX_BINDING_LIST_BYTES
            ),
            lifecycle_phases=self._stored_string_array(
                row["lifecycle_phases_json"], maximum_bytes=_MAX_BINDING_LIST_BYTES
            ),
            execution_depths=self._stored_string_array(
                row["execution_depths_json"], maximum_bytes=_MAX_BINDING_LIST_BYTES
            ),
            delivery_modes=self._stored_string_array(
                row["delivery_modes_json"], maximum_bytes=_MAX_BINDING_LIST_BYTES
            ),
            worker_type=row["worker_type"],
            runner_image_digest=row["runner_image_digest"],
            adapter_name=row["adapter_name"],
            adapter_version=row["adapter_version"],
            configuration_schema=self._stored_json_object(
                row["configuration_schema_json"],
                maximum_bytes=MAX_CONFIGURATION_SCHEMA_BYTES,
            ),
            configuration_defaults=self._stored_json_object(
                row["configuration_defaults_json"],
                maximum_bytes=MAX_CONFIGURATION_DEFAULTS_BYTES,
            ),
            required_input_roles=self._stored_string_array(
                row["required_input_roles_json"],
                maximum_bytes=_MAX_BINDING_LIST_BYTES,
                allow_empty=True,
            ),
            budgets=self._stored_json_object(
                row["default_budgets_json"],
                maximum_bytes=MAX_BUDGETS_BYTES,
            ),
            result_contract_version=row["result_contract_version"],
            status=row["status"],
            created_by=row["created_by"],
            created_at=row["created_at"],
        )

    def _plan_suite_binding(self, row: Mapping[str, Any]) -> PlanSuiteBindingRecord:
        return PlanSuiteBindingRecord(
            suite=self._suite_binding(row),
            ordinal=row["ordinal"],
            configuration=self._stored_json_object(
                row["configuration_json"],
                maximum_bytes=MAX_SUITE_CONFIGURATION_BYTES,
            ),
            configuration_hash=row["configuration_hash"],
        )

    def _plan_binding(self, row: Mapping[str, Any]) -> PlanBindingRecord:
        return PlanBindingRecord(
            id=row["id"],
            organization_id=row["org_id"],
            workspace_id=row["workspace_id"],
            system_id=row["system_id"],
            name=row["name"],
            contract_version=row["contract_version"],
            target_version_id=row["target_version_id"],
            target_kind=row["target_kind"],
            lifecycle_phases=self._stored_string_array(
                row["lifecycle_phases_json"],
                maximum_bytes=_MAX_BINDING_LIST_BYTES,
            ),
            execution_depth=row["execution_depth"],
            enforcement_mode=row["enforcement_mode"],
            delivery_mode=row["delivery_mode"],
            trust_policy_version_id=row["trust_policy_version_id"],
            plan_content_hash=row["plan_content_hash"],
            status=row["status"],
            created_by=row["created_by"],
            updated_by=row["updated_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def load_plan_creation_bindings(
        self,
        *,
        org_id: str,
        system_id: str,
        target_version_id: str,
        trust_policy_version_id: str,
        suite_version_ids: tuple[str, ...],
        lock: bool,
    ) -> PlanCreationBindings | None:
        scope = self._system_scope(org_id, system_id, lock=lock)
        if scope is None:
            return None
        target = self._target_row(
            org_id=org_id,
            workspace_id=scope["workspace_id"],
            system_id=system_id,
            target_id=target_version_id,
            lock=lock,
        )
        trust = self._trust_row(
            org_id=org_id,
            trust_id=trust_policy_version_id,
            lock=lock,
        )
        if target is None or trust is None:
            return None
        suites: list[SuiteBindingRecord] = []
        for suite_version_id in suite_version_ids:
            suite = self._suite_row(
                org_id=org_id,
                suite_version_id=suite_version_id,
                lock=lock,
            )
            if suite is None:
                return None
            suites.append(self._suite_binding(suite))
        return PlanCreationBindings(
            scope=self._scope_record(scope),
            target=self._target_binding(target),
            trust_policy=self._trust_binding(trust),
            suites=tuple(suites),
        )

    def load_plan_graph(
        self,
        *,
        org_id: str,
        system_id: str,
        plan_id: str,
        lock: bool,
    ) -> PlanGraphRecord | None:
        scope = self._system_scope(org_id, system_id, lock=lock)
        if scope is None:
            return None
        plan = self._plan_row(
            org_id=org_id,
            workspace_id=scope["workspace_id"],
            system_id=system_id,
            plan_id=plan_id,
            lock=lock,
        )
        if plan is None:
            return None
        target = self._target_row(
            org_id=org_id,
            workspace_id=scope["workspace_id"],
            system_id=system_id,
            target_id=plan["target_version_id"],
            lock=lock,
        )
        trust = self._trust_row(
            org_id=org_id,
            trust_id=plan["trust_policy_version_id"],
            lock=lock,
        )
        if target is None or trust is None:
            return None
        suites = self._bound_suites(
            plan_id,
            org_id,
            scope["workspace_id"],
            system_id,
            lock=lock,
        )
        return PlanGraphRecord(
            scope=self._scope_record(scope),
            plan=self._plan_binding(plan),
            target=self._target_binding(target),
            trust_policy=self._trust_binding(trust),
            suites=tuple(self._plan_suite_binding(suite) for suite in suites),
        )

    def persist_plan(self, command: PersistPlanCommand) -> PlanGraphRecord:
        requested = command.requested.to_dict()
        scope = command.bindings.scope
        target = command.bindings.target
        trust = command.bindings.trust_policy
        self.db.execute(
            insert(GovernanceEvaluationPlan.__table__).values(
                id=command.plan_id,
                org_id=scope.organization_id,
                workspace_id=scope.workspace_id,
                system_id=scope.system_id,
                name=requested["name"],
                target_kind=target.target_kind,
                lifecycle_phases_json=canonical_json(requested["lifecyclePhases"]),
                execution_depth=requested["executionDepth"],
                enforcement_mode=requested["enforcementMode"],
                delivery_mode=requested["deliveryMode"],
                suite_refs_json=canonical_json(
                    [selection.suite.suite_ref for selection in command.suites]
                ),
                status="draft",
                created_by=command.actor_id,
                updated_by=command.actor_id,
                created_at=command.created_at,
                updated_at=command.created_at,
                contract_version=CONTRACT_VERSION,
                target_version_id=target.id,
                plan_content_hash=command.plan_content_hash,
                trust_policy_version_id=trust.id,
            )
        )
        for selection in command.suites:
            self.db.execute(
                insert(GovernanceEvaluationPlanSuite.__table__).values(
                    id=str(uuid.uuid4()),
                    org_id=scope.organization_id,
                    workspace_id=scope.workspace_id,
                    system_id=scope.system_id,
                    plan_id=command.plan_id,
                    suite_version_id=selection.suite.id,
                    suite_owner_scope=selection.suite.owner_scope,
                    ordinal=selection.ordinal,
                    configuration_json=canonical_json(selection.configuration.to_dict()),
                    configuration_hash=selection.configuration_hash,
                    created_at=command.created_at,
                )
            )
        graph = self.load_plan_graph(
            org_id=scope.organization_id,
            system_id=scope.system_id,
            plan_id=command.plan_id,
            lock=True,
        )
        if graph is None:
            raise RuntimeError("persisted plan graph could not be reloaded")
        return graph

    def cas_activate_plan(
        self,
        *,
        graph: PlanGraphRecord,
        actor_id: str,
        updated_at: str,
    ) -> PlanGraphRecord:
        if graph.plan.status == "draft":
            result = self.db.execute(
                update(GovernanceEvaluationPlan.__table__)
                .where(
                    GovernanceEvaluationPlan.id == graph.plan.id,
                    GovernanceEvaluationPlan.org_id == graph.scope.organization_id,
                    GovernanceEvaluationPlan.workspace_id == graph.scope.workspace_id,
                    GovernanceEvaluationPlan.system_id == graph.scope.system_id,
                    GovernanceEvaluationPlan.contract_version == CONTRACT_VERSION,
                    GovernanceEvaluationPlan.status == "draft",
                )
                .values(status="active", updated_by=actor_id, updated_at=updated_at)
            )
            if result.rowcount != 1:
                raise self._error(
                    "plan_state_changed",
                    "Plan state changed concurrently.",
                    409,
                )
        updated = self.load_plan_graph(
            org_id=graph.scope.organization_id,
            system_id=graph.scope.system_id,
            plan_id=graph.plan.id,
            lock=True,
        )
        if updated is None:
            raise RuntimeError("activated plan graph could not be reloaded")
        return updated

    def list_plan_graphs(
        self,
        *,
        org_id: str,
        system_id: str,
    ) -> list[PlanGraphRecord] | None:
        scope = self._system_scope(org_id, system_id)
        if scope is None:
            return None
        plans = GovernanceEvaluationPlan.__table__
        plan_ids = (
            self.db.execute(
                select(plans.c.id)
                .where(
                    plans.c.org_id == org_id,
                    plans.c.workspace_id == scope["workspace_id"],
                    plans.c.system_id == system_id,
                    plans.c.contract_version == CONTRACT_VERSION,
                )
                .order_by(plans.c.created_at.desc())
            )
            .scalars()
            .all()
        )
        result: list[PlanGraphRecord] = []
        for plan_id in plan_ids:
            graph = self.load_plan_graph(
                org_id=org_id,
                system_id=system_id,
                plan_id=plan_id,
                lock=False,
            )
            if graph is not None:
                result.append(graph)
        return result

    def get_plan_graph(
        self,
        *,
        org_id: str,
        system_id: str,
        plan_id: str,
    ) -> PlanGraphRecord | None:
        return self.load_plan_graph(
            org_id=org_id,
            system_id=system_id,
            plan_id=plan_id,
            lock=False,
        )

    # --------------------------------------------------------------
    # Runs and immutable envelopes.
    # --------------------------------------------------------------

    def _suite_execution_record(self, row: Mapping[str, Any]) -> SuiteExecutionRecord:
        frozen_result_summary = (
            None
            if row["result_summary_json"] is None
            else self._stored_json_object(
                row["result_summary_json"],
                maximum_bytes=_MAX_SUITE_RESULT_SUMMARY_BYTES,
            )
        )
        frozen_limitations = (
            None
            if row["limitations_json"] is None
            else self._stored_json_array(
                row["limitations_json"],
                maximum_bytes=MAX_SUITE_LIMITATIONS_BYTES,
            )
        )
        return SuiteExecutionRecord(
            id=row["id"],
            suite_version_id=row["suite_version_id"],
            owner_scope=row["suite_owner_scope"],
            ordinal=row["ordinal"],
            technical_status=row["technical_status"],
            evidence_result_status=row["evidence_result_status"],
            admission_status=row["admission_status"],
            review_status=row["review_status"],
            freshness_status=row["freshness_status"],
            evidence_run_id=row["evidence_run_id"],
            passport_revision_id=row["passport_revision_id"],
            linked_by=row["linked_by"],
            linked_at=row["linked_at"],
            result_summary=frozen_result_summary,
            limitations=frozen_limitations,
            failure_code=row["failure_code"],
            failure_message=row["failure_message"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _stored_json_value(
        self,
        raw: Any,
        *,
        maximum_bytes: int,
        expected_type: type[dict] | type[list],
    ) -> Any:
        try:
            return _exact_canonical_json_value(
                raw,
                maximum_bytes=maximum_bytes,
                expected_type=expected_type,
            )
        except (
            AssuranceContractValidationError,
            OverflowError,
            RecursionError,
            TypeError,
            UnicodeError,
            ValueError,
        ) as error:
            raise self._error(
                "binding_integrity_error",
                _BINDING_INTEGRITY_MESSAGE,
                409,
            ) from error

    def _stored_json_object(
        self,
        raw: Any,
        *,
        maximum_bytes: int,
    ) -> FrozenJsonObject:
        decoded = self._stored_json_value(
            raw,
            maximum_bytes=maximum_bytes,
            expected_type=dict,
        )
        return FrozenJsonObject.from_mapping(decoded)

    def _stored_json_array(
        self,
        raw: Any,
        *,
        maximum_bytes: int,
    ) -> tuple[Any, ...]:
        decoded = self._stored_json_value(
            raw,
            maximum_bytes=maximum_bytes,
            expected_type=list,
        )
        frozen = FrozenJsonObject.from_mapping({"items": decoded})["items"]
        if not isinstance(frozen, tuple):
            raise self._error(
                "binding_integrity_error",
                _BINDING_INTEGRITY_MESSAGE,
                409,
            )
        return frozen

    def _stored_string_array(
        self,
        raw: Any,
        *,
        maximum_bytes: int,
        allow_empty: bool = False,
    ) -> tuple[str, ...]:
        values = self._stored_json_array(raw, maximum_bytes=maximum_bytes)
        try:
            if (
                (not values and not allow_empty)
                or len(values) > 64
                or any(
                    not isinstance(value, str) or not value or len(value.encode("utf-8")) > 200
                    for value in values
                )
                or len(set(values)) != len(values)
            ):
                raise ValueError("stored string array violates its closed contract")
        except (TypeError, UnicodeError, ValueError) as error:
            raise self._error(
                "binding_integrity_error",
                _BINDING_INTEGRITY_MESSAGE,
                409,
            ) from error
        return values

    def _stored_envelope(self, raw: Any) -> FrozenJsonObject:
        return self._stored_json_object(
            raw,
            maximum_bytes=MAX_EXECUTION_ENVELOPE_BYTES,
        )

    def _run_record(self, row: Mapping[str, Any]) -> RunRecord:
        executions = (
            self.db.execute(
                select(GovernanceEvaluationRunSuiteExecution.__table__)
                .where(
                    GovernanceEvaluationRunSuiteExecution.run_id == row["id"],
                    GovernanceEvaluationRunSuiteExecution.org_id == row["org_id"],
                    GovernanceEvaluationRunSuiteExecution.workspace_id == row["workspace_id"],
                    GovernanceEvaluationRunSuiteExecution.system_id == row["system_id"],
                )
                .order_by(GovernanceEvaluationRunSuiteExecution.ordinal)
            )
            .mappings()
            .all()
        )
        return RunRecord(
            id=row["id"],
            organization_id=row["org_id"],
            workspace_id=row["workspace_id"],
            system_id=row["system_id"],
            plan_id=row["plan_id"],
            contract_version=row["contract_version"],
            trigger=row["trigger"],
            lifecycle_phase=row["lifecycle_phase"],
            technical_status=row["technical_status"],
            evidence_outcome=row["evidence_outcome"],
            overall_verdict=row["overall_verdict"],
            layer_verdicts_schema_version=row["layer_verdicts_schema_version"],
            layer_verdicts=self._stored_json_object(
                row["layer_verdicts_json"],
                maximum_bytes=_MAX_LAYER_VERDICTS_BYTES,
            ),
            suite_executions=tuple(
                self._suite_execution_record(execution) for execution in executions
            ),
            envelope_id=row["envelope_id"],
            envelope_nonce=row["envelope_nonce"],
            envelope=self._stored_envelope(row["envelope_json"]),
            envelope_hash=row["envelope_hash"],
            verdict_version=row["verdict_version"],
            requested_by=row["requested_by"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            failure_code=row["failure_code"],
            failure_message=row["failure_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def persist_run(self, command: PersistRunCommand) -> RunRecord:
        scope = command.graph.scope
        if command.layer_verdicts_schema_version != LAYER_VERDICTS_SCHEMA_VERSION:
            raise self._error(
                "binding_integrity_error",
                _BINDING_INTEGRITY_MESSAGE,
                409,
            )
        self.db.execute(
            insert(GovernanceEvaluationRun.__table__).values(
                id=command.run_id,
                org_id=scope.organization_id,
                workspace_id=scope.workspace_id,
                system_id=scope.system_id,
                plan_id=command.graph.plan.id,
                contract_version=CONTRACT_VERSION,
                trigger=command.trigger,
                technical_status=command.technical_status,
                overall_verdict=command.overall_verdict,
                layer_verdicts_schema_version=command.layer_verdicts_schema_version,
                layer_verdicts_json=canonical_json(command.layer_verdicts.to_dict()),
                requested_by=command.actor_id,
                created_at=command.created_at,
                updated_at=command.created_at,
                lifecycle_phase=command.lifecycle_phase,
                envelope_id=command.envelope_id,
                envelope_nonce=command.envelope_nonce,
                envelope_json=canonical_json(command.envelope.to_dict()),
                envelope_hash=command.envelope_hash,
                evidence_outcome=command.evidence_outcome,
                verdict_version=0,
            )
        )
        for execution in command.suites:
            self.db.execute(
                insert(GovernanceEvaluationRunSuiteExecution.__table__).values(
                    id=execution.execution_id,
                    org_id=scope.organization_id,
                    workspace_id=scope.workspace_id,
                    system_id=scope.system_id,
                    run_id=command.run_id,
                    suite_version_id=execution.suite_version_id,
                    suite_owner_scope=execution.suite_owner_scope,
                    ordinal=execution.ordinal,
                    technical_status=command.technical_status,
                    evidence_result_status=command.evidence_outcome,
                    admission_status="pending",
                    review_status="pending",
                    freshness_status="current",
                    created_at=command.created_at,
                    updated_at=command.created_at,
                )
            )
        row = (
            self.db.execute(
                select(GovernanceEvaluationRun.__table__).where(
                    GovernanceEvaluationRun.id == command.run_id,
                    GovernanceEvaluationRun.org_id == scope.organization_id,
                    GovernanceEvaluationRun.workspace_id == scope.workspace_id,
                    GovernanceEvaluationRun.system_id == scope.system_id,
                    GovernanceEvaluationRun.contract_version == CONTRACT_VERSION,
                )
            )
            .mappings()
            .one()
        )
        return self._run_record(row)

    def list_run_records(
        self,
        *,
        org_id: str,
        system_id: str,
    ) -> list[RunRecord] | None:
        scope = self._system_scope(org_id, system_id)
        if scope is None:
            return None
        self._verify_audit_chain(org_id=org_id)
        rows = (
            self.db.execute(
                select(GovernanceEvaluationRun.__table__)
                .where(
                    GovernanceEvaluationRun.org_id == org_id,
                    GovernanceEvaluationRun.workspace_id == scope["workspace_id"],
                    GovernanceEvaluationRun.system_id == system_id,
                    GovernanceEvaluationRun.contract_version == CONTRACT_VERSION,
                )
                .order_by(GovernanceEvaluationRun.created_at.desc())
            )
            .mappings()
            .all()
        )
        return [self._run_record(row) for row in rows]

    def get_run_record(
        self,
        *,
        org_id: str,
        system_id: str,
        run_id: str,
    ) -> RunRecord | None:
        scope = self._system_scope(org_id, system_id)
        if scope is None:
            return None
        self._verify_audit_chain(org_id=org_id)
        row = (
            self.db.execute(
                select(GovernanceEvaluationRun.__table__).where(
                    GovernanceEvaluationRun.id == run_id,
                    GovernanceEvaluationRun.org_id == org_id,
                    GovernanceEvaluationRun.workspace_id == scope["workspace_id"],
                    GovernanceEvaluationRun.system_id == system_id,
                    GovernanceEvaluationRun.contract_version == CONTRACT_VERSION,
                )
            )
            .mappings()
            .one_or_none()
        )
        return self._run_record(row) if row else None

    def _verify_audit_chain(self, *, org_id: str) -> None:
        try:
            verify_evaluation_audit_chain(self.db, org_id=org_id)
        except EvaluationAuditChainIntegrityError:
            raise self._error(
                "audit_chain_integrity_error",
                _AUDIT_CHAIN_INTEGRITY_MESSAGE,
                409,
            ) from None


class SqlAlchemyEvaluationWorkbenchUnitOfWork:
    """SQLAlchemy transaction adapter for one application-orchestrated mutation."""

    def __init__(
        self,
        session: Session,
        *,
        repository: SqlAlchemyEvaluationWorkbenchRepository | None = None,
    ) -> None:
        if not isinstance(session, Session):
            raise TypeError("SQLAlchemy Session required")
        self.db = session
        self._repository = repository or SqlAlchemyEvaluationWorkbenchRepository(session)

    @property
    def repository(self) -> SqlAlchemyEvaluationWorkbenchRepository:
        return self._repository

    @staticmethod
    def _error(
        code: str,
        message: str,
        status_code: int,
    ) -> EvaluationWorkbenchError:
        return EvaluationWorkbenchError(code, message, status_code=status_code)

    def _lock_org(self, org_id: str) -> None:
        if self.db.bind is not None and self.db.bind.dialect.name == "postgresql":
            self.db.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:org_id, 0))"),
                {"org_id": org_id},
            )

    def _mutation_lock(self):
        if self.db.bind is not None and self.db.bind.dialect.name == "sqlite":
            return _SQLITE_WRITE_LOCK
        return nullcontext()

    def _invalid_idempotency_response(self) -> EvaluationWorkbenchError:
        return self._error(
            "idempotency_response_invalid",
            "The stored idempotency response is invalid.",
            409,
        )

    def _verified_rejected_replay(
        self,
        *,
        command: MutationCommand,
        row: Mapping[str, Any],
        body: Mapping[str, Any],
    ) -> EvaluationWorkbenchError:
        """Return a rejection bound to the row's exact audit-event receipt."""

        key_hash = _idempotency_key_hash(command.idempotency_key)
        request_hash = _audit_safe_request_hash(command.request_hash)
        operation = _audit_safe_operation(command.operation)
        try:
            if row["resource_type"] != _REJECTED_IDEMPOTENCY_RESOURCE_TYPE or not isinstance(
                row["resource_id"], str
            ):
                raise ValueError("rejected receipt identity is invalid")
            event = (
                self.db.execute(
                    select(GovernanceEvaluationAuditEvent.__table__).where(
                        GovernanceEvaluationAuditEvent.org_id == command.organization_id,
                        GovernanceEvaluationAuditEvent.id == row["resource_id"],
                    )
                )
                .mappings()
                .one_or_none()
            )
            if event is None:
                raise ValueError("bound rejected audit event is missing")
            details = _exact_canonical_json_value(
                event["details_json"],
                maximum_bytes=_MAX_REJECTION_RESPONSE_BYTES,
                expected_type=dict,
            )
            if (
                set(body) != {_REJECTED_IDEMPOTENCY_MARKER, "error"}
                or body.get(_REJECTED_IDEMPOTENCY_MARKER) is not True
                or not isinstance(body.get("error"), Mapping)
            ):
                raise ValueError("rejected response wrapper is invalid")
            error_body = body["error"]
            assert isinstance(error_body, Mapping)
            if set(error_body) not in (
                {"code", "message"},
                {"code", "message", "details"},
            ):
                raise ValueError("rejected error body is invalid")
            code = error_body.get("code")
            message = error_body.get("message")
            error_details = error_body.get("details")
            status = row["response_status"]
            if (
                not isinstance(code, str)
                or not isinstance(message, str)
                or (error_details is not None and not isinstance(error_details, dict))
                or not isinstance(status, int)
                or isinstance(status, bool)
            ):
                raise ValueError("rejected error fields are invalid")
            stored_error = EvaluationWorkbenchError(
                code,
                message,
                status_code=status,
                details=error_details,
            )
            safe_error = _safe_rejection_error(stored_error)
            expected_body, expected_body_json, response_hash = _rejected_response_material(
                safe_error,
                claimed_at=row["created_at"],
                expires_at=row["expires_at"],
            )
            expected_audit_details = {
                "schemaVersion": _REJECTED_AUDIT_SCHEMA_VERSION,
                "operation": operation,
                "requestHash": request_hash,
                "claimedAt": row["created_at"],
                "expiresAt": row["expires_at"],
                "errorCode": _audit_safe_code(safe_error.code),
                "statusCode": safe_error.status_code,
                "responseHash": response_hash,
            }
            if (
                safe_error.detail() != stored_error.detail()
                or dict(body) != expected_body
                or row["response_body_json"] != expected_body_json
                or event["actor_id"] != command.actor_id
                or event["action"] != _REJECTED_AUDIT_ACTION
                or event["outcome"] != "rejected"
                or event["resource_type"] != _REJECTED_AUDIT_RESOURCE_TYPE
                or event["resource_id"] != key_hash
                or event["created_at"] != row["created_at"]
                or dict(details) != expected_audit_details
            ):
                raise ValueError("rejected response binding does not match")
            return safe_error
        except (
            AssuranceContractValidationError,
            OverflowError,
            RecursionError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            raise self._invalid_idempotency_response() from None

    def _verified_success_replay(
        self,
        *,
        command: MutationCommand,
        row: Mapping[str, Any],
        wrapper: Mapping[str, Any],
    ) -> MutationResult:
        """Return a response bound to one exact, chain-verified success event."""

        try:
            if (
                set(wrapper) != {_SUCCESS_IDEMPOTENCY_MARKER, "auditEventId", "responseBody"}
                or wrapper.get(_SUCCESS_IDEMPOTENCY_MARKER) is not True
                or not isinstance(wrapper.get("auditEventId"), str)
                or not isinstance(wrapper.get("responseBody"), Mapping)
            ):
                raise ValueError("success response wrapper is invalid")
            audit_event_id = wrapper["auditEventId"]
            response_body_value = wrapper["responseBody"]
            assert isinstance(audit_event_id, str)
            assert isinstance(response_body_value, Mapping)
            response_body, response_hash = _success_response_material(
                body=response_body_value,
                status=row["response_status"],
                audit_event_id=audit_event_id,
                claimed_at=row["created_at"],
                expires_at=row["expires_at"],
                resource_type=row["resource_type"],
                resource_id=row["resource_id"],
            )
            expected_wrapper, expected_wrapper_json = _success_idempotency_wrapper(
                response_body=response_body,
                audit_event_id=audit_event_id,
            )
            if (
                dict(wrapper) != expected_wrapper
                or row["response_body_json"] != expected_wrapper_json
            ):
                raise ValueError("success response wrapper is not exact")

            event = (
                self.db.execute(
                    select(GovernanceEvaluationAuditEvent.__table__).where(
                        GovernanceEvaluationAuditEvent.org_id == command.organization_id,
                        GovernanceEvaluationAuditEvent.id == audit_event_id,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if event is None:
                raise ValueError("bound success audit event is missing")
            details = _exact_canonical_json_value(
                event["details_json"],
                maximum_bytes=_MAX_IDEMPOTENCY_RESPONSE_BYTES,
                expected_type=dict,
            )
            if set(details) != {_SUCCESS_AUDIT_BINDING_KEY} or not isinstance(
                details.get(_SUCCESS_AUDIT_BINDING_KEY), Mapping
            ):
                raise ValueError("success audit details are not bound")
            binding = details[_SUCCESS_AUDIT_BINDING_KEY]
            assert isinstance(binding, Mapping)
            required_binding_members = {
                "schemaVersion",
                "auditEventId",
                "idempotencyRecordId",
                "idempotencyKeyHash",
                "operation",
                "requestHash",
                "claimedAt",
                "expiresAt",
                "resourceType",
                "resourceId",
                "responseStatus",
                "responseHash",
                "action",
                "domainDetails",
            }
            if set(binding) != required_binding_members or not isinstance(
                binding.get("domainDetails"), Mapping
            ):
                raise ValueError("success audit binding is invalid")
            expected_action = event["action"]
            expected_binding = {
                "schemaVersion": _SUCCESS_AUDIT_SCHEMA_VERSION,
                "auditEventId": audit_event_id,
                "idempotencyRecordId": row["id"],
                "idempotencyKeyHash": _idempotency_key_hash(command.idempotency_key),
                "operation": _audit_safe_operation(command.operation),
                "requestHash": _audit_safe_request_hash(command.request_hash),
                "claimedAt": row["created_at"],
                "expiresAt": row["expires_at"],
                "resourceType": row["resource_type"],
                "resourceId": row["resource_id"],
                "responseStatus": row["response_status"],
                "responseHash": response_hash,
                "action": expected_action,
                "domainDetails": dict(binding["domainDetails"]),
            }
            if (
                dict(binding) != expected_binding
                or event["actor_id"] != command.actor_id
                or event["outcome"] != "success"
                or event["resource_type"] != row["resource_type"]
                or event["resource_id"] != row["resource_id"]
                or event["created_at"] != row["created_at"]
                or not isinstance(expected_action, str)
                or not expected_action
            ):
                raise ValueError("success response binding does not match")
            return MutationResult.create(
                body=response_body,
                status=row["response_status"],
                replayed=True,
            )
        except (
            AssuranceContractValidationError,
            OverflowError,
            RecursionError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            raise self._invalid_idempotency_response() from None

    def _validated_completed_replay(
        self,
        *,
        command: MutationCommand,
        row: Mapping[str, Any],
    ) -> MutationResult | EvaluationWorkbenchError:
        try:
            response_status = row["response_status"]
            if (
                not isinstance(response_status, int)
                or isinstance(response_status, bool)
                or not 100 <= response_status <= 599
            ):
                raise ValueError("stored response status is invalid")
            body = _exact_canonical_json_value(
                row["response_body_json"],
                maximum_bytes=_MAX_IDEMPOTENCY_RESPONSE_BYTES,
                expected_type=dict,
                maximum_items=_MAX_IDEMPOTENCY_RESPONSE_ITEMS,
            )
        except (
            AssuranceContractValidationError,
            OverflowError,
            RecursionError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            raise self._invalid_idempotency_response() from None
        try:
            verify_evaluation_audit_chain(
                self.db,
                org_id=command.organization_id,
            )
        except EvaluationAuditChainIntegrityError:
            raise self._error(
                "audit_chain_integrity_error",
                _AUDIT_CHAIN_INTEGRITY_MESSAGE,
                409,
            ) from None
        if (
            set(body) in ({_REJECTED_IDEMPOTENCY_MARKER, "error"},)
            and body.get(_REJECTED_IDEMPOTENCY_MARKER) is True
        ):
            return self._verified_rejected_replay(
                command=command,
                row=row,
                body=body,
            )
        if (
            set(body) == {_SUCCESS_IDEMPOTENCY_MARKER, "auditEventId", "responseBody"}
            and body.get(_SUCCESS_IDEMPOTENCY_MARKER) is True
        ):
            return self._verified_success_replay(
                command=command,
                row=row,
                wrapper=body,
            )
        raise self._invalid_idempotency_response()

    def _claim_idempotency(
        self,
        *,
        command: MutationCommand,
        now: datetime,
    ) -> tuple[
        str,
        MutationResult | EvaluationWorkbenchError | None,
        datetime,
        datetime,
    ]:
        records = GovernanceIdempotencyRecord.__table__
        key_hash = _idempotency_key_hash(command.idempotency_key)

        def existing_row(lock: bool = False):
            statement = select(records).where(
                records.c.org_id == command.organization_id,
                records.c.actor_id == command.actor_id,
                records.c.operation == command.operation,
                records.c.key_hash == key_hash,
            )
            if lock:
                statement = statement.with_for_update()
            return self.db.execute(statement).mappings().one_or_none()

        row = existing_row(lock=True)
        if row is None:
            record_id = str(uuid.uuid4())
            try:
                if self.db.bind is not None and self.db.bind.dialect.name == "sqlite":
                    self.db.execute(
                        update(records)
                        .where(records.c.id == "__fairmind_never__")
                        .values(updated_at=records.c.updated_at)
                    )
                with self.db.begin_nested():
                    self.db.execute(
                        insert(records).values(
                            id=record_id,
                            org_id=command.organization_id,
                            actor_id=command.actor_id,
                            operation=command.operation,
                            key_hash=key_hash,
                            request_hash=command.request_hash,
                            status="in_progress",
                            created_at=_iso(now),
                            updated_at=_iso(now),
                            expires_at=_iso(now + _IDEMPOTENCY_RETENTION),
                        )
                    )
                    self.db.flush()
                return record_id, None, now, now + _IDEMPOTENCY_RETENTION
            except IntegrityError:
                row = existing_row(lock=True)
                if row is None:
                    raise
        assert row is not None
        try:
            previous_claimed_at = _parse_timestamp(row["created_at"])
            previous_expires_at = _parse_timestamp(row["expires_at"])
        except (AttributeError, TypeError, ValueError):
            raise self._invalid_idempotency_response() from None
        expired = previous_expires_at <= now
        if row["status"] == "completed" and expired:
            stored_request_hash = row["request_hash"]
            if not isinstance(stored_request_hash, str):
                raise self._invalid_idempotency_response()
            historical_command = MutationCommand(
                organization_id=command.organization_id,
                actor_id=command.actor_id,
                operation=command.operation,
                idempotency_key=command.idempotency_key,
                request_hash=stored_request_hash,
            )
            self._validated_completed_replay(
                command=historical_command,
                row=row,
            )
        if expired:
            claimed_at = max(
                now,
                previous_claimed_at + timedelta(microseconds=1),
            )
            expires_at = claimed_at + _IDEMPOTENCY_RETENTION
            result = self.db.execute(
                update(records)
                .where(
                    records.c.id == row["id"],
                    records.c.updated_at == row["updated_at"],
                )
                .values(
                    request_hash=command.request_hash,
                    status="in_progress",
                    response_status=None,
                    response_body_json=None,
                    resource_type=None,
                    resource_id=None,
                    created_at=_iso(claimed_at),
                    updated_at=_iso(claimed_at),
                    expires_at=_iso(expires_at),
                )
            )
            if result.rowcount != 1:
                raise self._error(
                    "idempotency_in_progress",
                    "Another request is reclaiming this expired idempotency key.",
                    409,
                )
            return row["id"], None, claimed_at, expires_at
        if row["request_hash"] != command.request_hash:
            raise self._error(
                "idempotency_conflict",
                "This Idempotency-Key is already bound to a different request.",
                409,
            )
        if row["status"] == "completed":
            return (
                row["id"],
                self._validated_completed_replay(
                    command=command,
                    row=row,
                ),
                previous_claimed_at,
                previous_expires_at,
            )
        raise self._error(
            "idempotency_in_progress",
            "A request with this Idempotency-Key is still in progress.",
            409,
        )

    def _complete_idempotency(
        self,
        *,
        record_id: str,
        outcome: MutationOutcome,
        audit_receipt: EvaluationAuditReceipt,
        claimed_at: datetime,
        expires_at: datetime,
        now: datetime,
    ) -> None:
        response_body, _ = _success_response_material(
            body=outcome.body.to_dict(),
            status=outcome.status,
            audit_event_id=audit_receipt.event_id,
            claimed_at=_iso(claimed_at),
            expires_at=_iso(expires_at),
            resource_type=outcome.resource_type,
            resource_id=outcome.resource_id,
        )
        _, response_body_json = _success_idempotency_wrapper(
            response_body=response_body,
            audit_event_id=audit_receipt.event_id,
        )
        result = self.db.execute(
            update(GovernanceIdempotencyRecord.__table__)
            .where(
                GovernanceIdempotencyRecord.id == record_id,
                GovernanceIdempotencyRecord.status == "in_progress",
            )
            .values(
                status="completed",
                response_status=outcome.status,
                response_body_json=response_body_json,
                resource_type=outcome.resource_type,
                resource_id=outcome.resource_id,
                updated_at=_iso(now),
            )
        )
        if result.rowcount != 1:
            raise self._error(
                "idempotency_state_changed",
                "The idempotency record changed before completion.",
                409,
            )

    def _complete_rejected_idempotency(
        self,
        *,
        record_id: str,
        error: EvaluationWorkbenchError,
        response_body_json: str,
        audit_receipt: EvaluationAuditReceipt,
        now: datetime,
    ) -> None:
        result = self.db.execute(
            update(GovernanceIdempotencyRecord.__table__)
            .where(
                GovernanceIdempotencyRecord.id == record_id,
                GovernanceIdempotencyRecord.status == "in_progress",
            )
            .values(
                status="completed",
                response_status=error.status_code,
                response_body_json=response_body_json,
                resource_type=_REJECTED_IDEMPOTENCY_RESOURCE_TYPE,
                resource_id=audit_receipt.event_id,
                updated_at=_iso(now),
            )
        )
        if result.rowcount != 1:
            raise self._error(
                "idempotency_state_changed",
                "The idempotency record changed before completion.",
                409,
            )

    def _append_audit(
        self,
        *,
        command: MutationCommand,
        record_id: str,
        outcome: MutationOutcome,
        claimed_at: datetime,
        expires_at: datetime,
    ) -> EvaluationAuditReceipt:
        action = outcome.audit_action or _SUCCESS_NOOP_AUDIT_ACTION
        domain_details = outcome.audit_details.to_dict()
        if _SUCCESS_AUDIT_BINDING_KEY in domain_details:
            raise ValueError("success audit details contain a reserved member")
        audit_event_id = str(uuid.uuid4())
        _, response_hash = _success_response_material(
            body=outcome.body.to_dict(),
            status=outcome.status,
            audit_event_id=audit_event_id,
            claimed_at=_iso(claimed_at),
            expires_at=_iso(expires_at),
            resource_type=outcome.resource_type,
            resource_id=outcome.resource_id,
        )
        details = {
            _SUCCESS_AUDIT_BINDING_KEY: {
                "schemaVersion": _SUCCESS_AUDIT_SCHEMA_VERSION,
                "auditEventId": audit_event_id,
                "idempotencyRecordId": record_id,
                "idempotencyKeyHash": _idempotency_key_hash(command.idempotency_key),
                "operation": _audit_safe_operation(command.operation),
                "requestHash": _audit_safe_request_hash(command.request_hash),
                "claimedAt": _iso(claimed_at),
                "expiresAt": _iso(expires_at),
                "resourceType": outcome.resource_type,
                "resourceId": outcome.resource_id,
                "responseStatus": outcome.status,
                "responseHash": response_hash,
                "action": action,
                "domainDetails": domain_details,
            }
        }
        _exact_canonical_json_value(
            canonical_json(details),
            maximum_bytes=_MAX_IDEMPOTENCY_RESPONSE_BYTES,
            expected_type=dict,
        )
        receipt = append_evaluation_audit_event(
            self.db,
            event=EvaluationAuditAppend(
                organization_id=command.organization_id,
                actor_id=command.actor_id,
                action=action,
                outcome="success",
                resource_type=outcome.resource_type,
                resource_id=outcome.resource_id,
                details=details,
                created_at=_iso(claimed_at),
                event_id=audit_event_id,
            ),
        )
        if receipt.event_id != audit_event_id:
            raise ValueError("success audit receipt identity changed")
        return receipt

    def _append_rejected_audit(
        self,
        *,
        command: MutationCommand,
        error: EvaluationWorkbenchError,
        response_hash: str,
        claimed_at: datetime,
        expires_at: datetime,
    ) -> EvaluationAuditReceipt:
        request_hash = _audit_safe_request_hash(command.request_hash)
        return append_evaluation_audit_event(
            self.db,
            event=EvaluationAuditAppend(
                organization_id=command.organization_id,
                actor_id=command.actor_id,
                action=_REJECTED_AUDIT_ACTION,
                outcome="rejected",
                resource_type=_REJECTED_AUDIT_RESOURCE_TYPE,
                resource_id=_idempotency_key_hash(command.idempotency_key),
                details={
                    "schemaVersion": _REJECTED_AUDIT_SCHEMA_VERSION,
                    "operation": _audit_safe_operation(command.operation),
                    "requestHash": request_hash,
                    "claimedAt": _iso(claimed_at),
                    "expiresAt": _iso(expires_at),
                    "errorCode": _audit_safe_code(error.code),
                    "statusCode": error.status_code,
                    "responseHash": response_hash,
                },
                created_at=_iso(claimed_at),
            ),
        )

    def mutate(
        self,
        command: MutationCommand,
        callback: Callable[[datetime], MutationOutcome],
    ) -> MutationResult:
        with self._mutation_lock():
            try:
                self._lock_org(command.organization_id)
                request_now = _now()
                record_id, replay, claimed_at, expires_at = self._claim_idempotency(
                    command=command,
                    now=request_now,
                )
                if replay is not None:
                    self.db.rollback()
                    if isinstance(replay, EvaluationWorkbenchError):
                        raise replay
                    return replay
                now = claimed_at
                rejected_error: EvaluationWorkbenchError | None = None
                try:
                    with self.db.begin_nested():
                        outcome = callback(now)
                except EvaluationWorkbenchError as error:
                    safe_error = _safe_rejection_error(error)
                    try:
                        _, response_body_json, response_hash = _rejected_response_material(
                            safe_error,
                            claimed_at=_iso(claimed_at),
                            expires_at=_iso(expires_at),
                        )
                        audit_receipt = self._append_rejected_audit(
                            command=command,
                            error=safe_error,
                            response_hash=response_hash,
                            claimed_at=claimed_at,
                            expires_at=expires_at,
                        )
                        self._complete_rejected_idempotency(
                            record_id=record_id,
                            error=safe_error,
                            response_body_json=response_body_json,
                            audit_receipt=audit_receipt,
                            now=now,
                        )
                        self.db.commit()
                    except Exception:
                        self.db.rollback()
                        raise self._error(
                            "evaluation_persistence_failed",
                            "The assurance workflow could not be persisted atomically.",
                            500,
                        ) from None
                    rejected_error = safe_error
                if rejected_error is not None:
                    raise rejected_error from None
                audit_receipt = self._append_audit(
                    command=command,
                    record_id=record_id,
                    outcome=outcome,
                    claimed_at=claimed_at,
                    expires_at=expires_at,
                )
                self._complete_idempotency(
                    record_id=record_id,
                    outcome=outcome,
                    audit_receipt=audit_receipt,
                    claimed_at=claimed_at,
                    expires_at=expires_at,
                    now=now,
                )
                self.db.commit()
                return MutationResult.create(
                    body=outcome.body.to_dict(),
                    status=outcome.status,
                )
            except EvaluationWorkbenchError:
                self.db.rollback()
                raise
            except Exception:
                self.db.rollback()
                raise self._error(
                    "evaluation_persistence_failed",
                    "The assurance workflow could not be persisted atomically.",
                    500,
                ) from None
