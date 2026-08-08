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
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from database.governance_models import (
    GovernanceAISystem,
    GovernanceEvaluationAuditEvent,
    GovernanceEvaluationPlan,
    GovernanceEvaluationPlanSuite,
    GovernanceEvaluationRun,
    GovernanceEvaluationDecision,
    GovernanceEvaluationRunSuiteExecution,
    GovernanceEvaluationSuiteEvidenceLink,
    GovernanceEvaluationSuiteVersion,
    GovernanceEvaluationTargetVersion,
    GovernanceEvidenceAdmission,
    GovernanceEvidenceIssuer,
    GovernanceEvidenceNonceClaim,
    GovernanceEvidencePassportRevision,
    GovernanceEvidenceReview,
    GovernanceEvidenceRun,
    GovernanceEvidenceSigningKey,
    GovernanceEvidenceTrustPolicyVersion,
    GovernanceEvidenceVerificationReceipt,
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
from src.application.ports.evidence_admission import (
    EvidenceAdmissionAuthorityRecord,
    EvidenceAdmissionScope,
    PersistVerifiedPassportV2Command,
    VerifiedPassportV2Record,
)
from src.application.ports.evidence_review import (
    EvidenceReviewAuthorityRecord,
    EvidenceReviewScope,
    PersistEvidenceReviewCommand,
    ReviewedEvidenceRecord,
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
_MAX_PUBLIC_JWK_BYTES = 4 * 1024
_MAX_STORED_JSON_DEPTH = 32
_MAX_STORED_JSON_ITEMS = MAX_SAFE_ARRAY_ITEMS
_MAX_IDEMPOTENCY_RESPONSE_ITEMS = (
    (_MAX_IDEMPOTENCY_RESPONSE_BYTES // 2) + _MAX_STORED_JSON_DEPTH + 16
)
_IDEMPOTENCY_RETENTION = timedelta(days=30)
_EVIDENCE_OCCUPIED_MESSAGE = "The suite execution or evidence identity is already occupied."
_EVIDENCE_INTEGRITY_MESSAGE = "The verified evidence graph failed its relational integrity checks."
_SUITE_PROJECTION_CONFLICT_MESSAGE = "The suite execution changed before evidence could be linked."
_RUN_PROJECTION_CONFLICT_MESSAGE = "The evaluation run changed before evidence could be linked."
_EVIDENCE_OCCUPANCY_CONSTRAINTS = frozenset(
    {
        "uq_governance_evidence_run",
        "uq_evidence_passport_number",
        "uq_evidence_run_passport_number",
        "uq_evidence_run_canonical_hash",
        "uq_governance_evidence_admission_policy",
        "uq_governance_evidence_verification_receipt_admission",
        "uq_governance_evidence_nonce_claim_admission",
        "uq_governance_evidence_nonce_claim_replay",
        "uq_governance_evaluation_suite_evidence_link_suite_execution",
        "uq_governance_evaluation_suite_evidence_link_admission",
        "uq_governance_evaluation_suite_evidence_link_nonce_claim",
    }
)
_EVIDENCE_P0001_INTEGRITY_MESSAGES = frozenset(
    {
        "verified admission trust eligibility failed",
        "nonce claim requires an eligible exact admission",
        "nonce claim admission is not policy-eligible",
        "nonce claim timestamp is not causal",
        "evidence link requires an eligible claimed admission",
        "evidence link timestamp is not causal",
        "verification receipt relational binding failed",
        "verified admission requires exact verification receipt",
        "verification receipt requires exact verified admission",
    }
)
_EVIDENCE_REVIEW_VERSION_CONSTRAINTS = frozenset(
    {
        "uq_governance_evidence_review_version",
        "uq_governance_evidence_review_admission_version",
    }
)
_EVIDENCE_REVIEW_TRIGGER_MESSAGES = {
    "reviews are frozen after governance decision": (
        "evidence_review_frozen",
        "Evidence reviews are frozen after a governance decision.",
    ),
    "reviewer must differ from submitter": (
        "evidence_review_separation_required",
        "The reviewer must be independent from submission, linking, and run request.",
    ),
    "review must use the next review version": (
        "evidence_review_version_conflict",
        "The evidence review version is stale.",
    ),
    "review requires an exact linked admission": (
        "evidence_review_integrity_conflict",
        "The evidence-review authority changed before persistence.",
    ),
    "review timestamp is not causal": (
        "evidence_review_chronology_invalid",
        "The evidence-review chronology is invalid.",
    ),
}


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


def _thaw_json_array(values: tuple[Any, ...]) -> list[Any]:
    thawed = FrozenJsonObject.from_mapping({"items": values}).to_dict()["items"]
    if not isinstance(thawed, list):
        raise TypeError("frozen JSON array required")
    return thawed


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

    def read_fresh_utc_now(self) -> datetime:
        """Read the authority timestamp from the current database transaction."""

        dialect = self.db.get_bind().dialect.name
        if dialect == "postgresql":
            value = self.db.execute(
                text("SELECT clock_timestamp() AT TIME ZONE 'UTC'")
            ).scalar_one()
            if isinstance(value, datetime):
                return value.replace(tzinfo=timezone.utc)
        else:
            value = self.db.execute(
                text("SELECT strftime('%Y-%m-%dT%H:%M:%f000+00:00', " "'now', '+0 seconds')")
            ).scalar_one()
        if not isinstance(value, str):
            raise TypeError("database UTC timestamp required")
        return _parse_timestamp(value).astimezone(timezone.utc)

    def load_admission_authority_for_update(
        self,
        *,
        scope: EvidenceAdmissionScope,
        issuer_key: str,
        signer_key_id: str,
    ) -> EvidenceAdmissionAuthorityRecord | None:
        """Lock and reconstruct the complete authority graph in deterministic order."""

        scope_row = self._system_scope(
            scope.organization_id,
            scope.system_id,
            lock=True,
        )
        if scope_row is None:
            return None
        workspace_id = scope_row["workspace_id"]
        runs = GovernanceEvaluationRun.__table__
        run_row = (
            self.db.execute(
                select(runs)
                .where(
                    runs.c.id == scope.run_id,
                    runs.c.org_id == scope.organization_id,
                    runs.c.workspace_id == workspace_id,
                    runs.c.system_id == scope.system_id,
                    runs.c.contract_version == CONTRACT_VERSION,
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if run_row is None:
            return None

        executions = GovernanceEvaluationRunSuiteExecution.__table__
        execution_rows = (
            self.db.execute(
                select(executions)
                .where(
                    executions.c.run_id == scope.run_id,
                    executions.c.org_id == scope.organization_id,
                    executions.c.workspace_id == workspace_id,
                    executions.c.system_id == scope.system_id,
                )
                .order_by(executions.c.ordinal, executions.c.id)
                .with_for_update()
            )
            .mappings()
            .all()
        )
        if sum(row["id"] == scope.suite_execution_id for row in execution_rows) != 1:
            return None

        plan_row = self._plan_row(
            org_id=scope.organization_id,
            workspace_id=workspace_id,
            system_id=scope.system_id,
            plan_id=run_row["plan_id"],
            lock=True,
        )
        if plan_row is None:
            return None
        target_row = self._target_row(
            org_id=scope.organization_id,
            workspace_id=workspace_id,
            system_id=scope.system_id,
            target_id=plan_row["target_version_id"],
            lock=True,
        )
        trust_row = self._trust_row(
            org_id=scope.organization_id,
            trust_id=plan_row["trust_policy_version_id"],
            lock=True,
        )
        suite_rows = self._bound_suites(
            plan_row["id"],
            scope.organization_id,
            workspace_id,
            scope.system_id,
            lock=True,
        )
        if target_row is None or trust_row is None:
            return None

        issuers = GovernanceEvidenceIssuer.__table__
        issuer_row = (
            self.db.execute(
                select(issuers)
                .where(
                    issuers.c.org_id == scope.organization_id,
                    issuers.c.issuer_key == issuer_key,
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if issuer_row is None:
            return None
        signing_keys = GovernanceEvidenceSigningKey.__table__
        signing_key_row = (
            self.db.execute(
                select(signing_keys)
                .where(
                    signing_keys.c.org_id == scope.organization_id,
                    signing_keys.c.issuer_id == issuer_row["id"],
                    signing_keys.c.key_id == signer_key_id,
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if signing_key_row is None:
            return None

        graph = PlanGraphRecord(
            scope=self._scope_record(scope_row),
            plan=self._plan_binding(plan_row),
            target=self._target_binding(target_row),
            trust_policy=self._trust_binding(trust_row),
            suites=tuple(self._plan_suite_binding(row) for row in suite_rows),
        )
        run = self._run_record_from_rows(run_row, execution_rows)
        try:
            key_valid_from = _parse_timestamp(signing_key_row["valid_from"]).astimezone(
                timezone.utc
            )
            key_valid_until = _parse_timestamp(signing_key_row["valid_until"]).astimezone(
                timezone.utc
            )
            key_revoked_at = (
                None
                if signing_key_row["revoked_at"] is None
                else _parse_timestamp(signing_key_row["revoked_at"]).astimezone(timezone.utc)
            )
        except (AttributeError, TypeError, ValueError) as error:
            raise self._error(
                "binding_integrity_error",
                _BINDING_INTEGRITY_MESSAGE,
                409,
            ) from error
        return EvidenceAdmissionAuthorityRecord(
            scope=scope,
            plan_graph=graph,
            run=run,
            maximum_evidence_age_seconds=trust_row["maximum_evidence_age_seconds"],
            unsigned_import_policy=trust_row["unsigned_import_policy"],
            issuer_internal_id=issuer_row["id"],
            issuer_key=issuer_row["issuer_key"],
            issuer_type=issuer_row["issuer_type"],
            issuer_status=issuer_row["status"],
            source_restrictions=self._stored_string_array(
                issuer_row["source_restrictions_json"],
                maximum_bytes=_MAX_BINDING_LIST_BYTES,
                allow_empty=True,
            ),
            suite_restrictions=self._stored_string_array(
                issuer_row["suite_restrictions_json"],
                maximum_bytes=_MAX_BINDING_LIST_BYTES,
                allow_empty=True,
            ),
            target_restrictions=self._stored_string_array(
                issuer_row["target_restrictions_json"],
                maximum_bytes=_MAX_BINDING_LIST_BYTES,
                allow_empty=True,
            ),
            signing_key_internal_id=signing_key_row["id"],
            signer_key_id=signing_key_row["key_id"],
            signer_algorithm=signing_key_row["algorithm"],
            public_jwk=self._stored_json_object(
                signing_key_row["public_jwk_json"],
                maximum_bytes=_MAX_PUBLIC_JWK_BYTES,
            ),
            key_valid_from=key_valid_from,
            key_valid_until=key_valid_until,
            key_revoked_at=key_revoked_at,
        )

    def restriction_references_exist(
        self,
        *,
        scope: EvidenceAdmissionScope,
        suite_version_ids: tuple[str, ...],
        target_version_ids: tuple[str, ...],
    ) -> bool:
        """Confirm every issuer restriction references a catalog identity in scope."""

        if len(set(suite_version_ids)) != len(suite_version_ids) or len(
            set(target_version_ids)
        ) != len(target_version_ids):
            return False
        scope_row = self._system_scope(scope.organization_id, scope.system_id)
        if scope_row is None:
            return False
        runs = GovernanceEvaluationRun.__table__
        executions = GovernanceEvaluationRunSuiteExecution.__table__
        scoped_execution = self.db.execute(
            select(executions.c.id)
            .select_from(
                executions.join(
                    runs,
                    (runs.c.id == executions.c.run_id)
                    & (runs.c.org_id == executions.c.org_id)
                    & (runs.c.workspace_id == executions.c.workspace_id)
                    & (runs.c.system_id == executions.c.system_id),
                )
            )
            .where(
                runs.c.id == scope.run_id,
                runs.c.contract_version == CONTRACT_VERSION,
                runs.c.org_id == scope.organization_id,
                runs.c.workspace_id == scope_row["workspace_id"],
                runs.c.system_id == scope.system_id,
                executions.c.id == scope.suite_execution_id,
            )
        ).scalar_one_or_none()
        if scoped_execution is None:
            return False

        if suite_version_ids:
            suites = GovernanceEvaluationSuiteVersion.__table__
            observed_suites = set(
                self.db.execute(
                    select(suites.c.id).where(
                        suites.c.id.in_(suite_version_ids),
                        suites.c.owner_scope.in_(["platform", scope.organization_id]),
                    )
                ).scalars()
            )
            if observed_suites != set(suite_version_ids):
                return False
        if target_version_ids:
            targets = GovernanceEvaluationTargetVersion.__table__
            observed_targets = set(
                self.db.execute(
                    select(targets.c.id).where(
                        targets.c.id.in_(target_version_ids),
                        targets.c.org_id == scope.organization_id,
                        targets.c.workspace_id == scope_row["workspace_id"],
                        targets.c.system_id == scope.system_id,
                    )
                ).scalars()
            )
            if observed_targets != set(target_version_ids):
                return False
        return True

    @staticmethod
    def _evidence_database_error_kind(error: DBAPIError) -> str | None:
        """Classify only known relational failures; operational errors propagate."""

        original = getattr(error, "orig", None)
        sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        constraint_name = getattr(getattr(original, "diag", None), "constraint_name", None)
        first_line = str(original).partition("\n")[0].strip().lower()
        if (
            sqlstate == "23505"
            and isinstance(constraint_name, str)
            and constraint_name in _EVIDENCE_OCCUPANCY_CONSTRAINTS
        ):
            return "occupied"
        if sqlstate == "P0001" and first_line in _EVIDENCE_P0001_INTEGRITY_MESSAGES:
            return "integrity"
        return None

    def _raise_evidence_database_error(self, error: DBAPIError) -> None:
        kind = self._evidence_database_error_kind(error)
        if kind == "occupied":
            raise self._error(
                "evidence_admission_occupied",
                _EVIDENCE_OCCUPIED_MESSAGE,
                409,
            ) from error
        if kind == "integrity":
            raise self._error(
                "evidence_admission_integrity_conflict",
                _EVIDENCE_INTEGRITY_MESSAGE,
                409,
            ) from error
        raise error

    def _verified_graph_is_occupied(
        self,
        command: PersistVerifiedPassportV2Command,
    ) -> bool:
        scope = command.scope
        authority = command.authority
        selected = next(
            (
                execution
                for execution in authority.run.suite_executions
                if execution.id == scope.suite_execution_id
            ),
            None,
        )
        if selected is None:
            return True
        if (
            selected.evidence_run_id is not None
            or selected.passport_revision_id is not None
            or selected.linked_by is not None
            or selected.linked_at is not None
            or selected.admission_status != "pending"
        ):
            return True

        admissions = GovernanceEvidenceAdmission.__table__
        claims = GovernanceEvidenceNonceClaim.__table__
        links = GovernanceEvaluationSuiteEvidenceLink.__table__
        receipts = GovernanceEvidenceVerificationReceipt.__table__
        revisions = GovernanceEvidencePassportRevision.__table__
        evidence_runs = GovernanceEvidenceRun.__table__
        passport = command.passport.to_dict()
        evaluator = passport.get("evaluator")
        if not isinstance(evaluator, dict):
            return True
        checks = (
            select(admissions.c.id).where(
                admissions.c.org_id == scope.organization_id,
                admissions.c.run_id == scope.run_id,
                admissions.c.suite_execution_id == scope.suite_execution_id,
            ),
            select(claims.c.id).where(
                claims.c.org_id == scope.organization_id,
                claims.c.suite_execution_id == scope.suite_execution_id,
                claims.c.envelope_id == authority.run.envelope_id,
                claims.c.envelope_nonce == authority.run.envelope_nonce,
            ),
            select(links.c.id).where(
                links.c.org_id == scope.organization_id,
                links.c.suite_execution_id == scope.suite_execution_id,
            ),
            select(receipts.c.id).where(
                receipts.c.org_id == scope.organization_id,
                receipts.c.run_id == scope.run_id,
                receipts.c.suite_execution_id == scope.suite_execution_id,
            ),
            select(revisions.c.id).where(
                revisions.c.org_id == scope.organization_id,
                revisions.c.passport_id == command.passport_id,
                revisions.c.passport_revision == command.passport_revision,
            ),
            select(evidence_runs.c.id).where(
                evidence_runs.c.org_id == scope.organization_id,
                evidence_runs.c.system_id == scope.system_id,
                evidence_runs.c.source_type == evaluator.get("sourceType"),
                evidence_runs.c.source_identifier == evaluator.get("evaluatorId"),
                evidence_runs.c.run_id == scope.suite_execution_id,
            ),
        )
        return any(self.db.execute(statement).first() is not None for statement in checks)

    @staticmethod
    def _timestamp_value(value: datetime | None) -> str | None:
        return None if value is None else value.astimezone(timezone.utc).isoformat()

    def _exact_run_snapshot_predicates(
        self,
        command: PersistVerifiedPassportV2Command,
    ) -> tuple[Any, ...]:
        run = command.authority.run
        table = GovernanceEvaluationRun.__table__
        return (
            table.c.id == run.id,
            table.c.org_id == run.organization_id,
            table.c.workspace_id == run.workspace_id,
            table.c.system_id == run.system_id,
            table.c.plan_id == run.plan_id,
            table.c.contract_version == run.contract_version,
            table.c.technical_status == run.technical_status,
            table.c.evidence_outcome == run.evidence_outcome,
            table.c.overall_verdict == run.overall_verdict,
            table.c.layer_verdicts_schema_version == run.layer_verdicts_schema_version,
            table.c.layer_verdicts_json == canonical_json(run.layer_verdicts.to_dict()),
            table.c.envelope_id == run.envelope_id,
            table.c.envelope_hash == run.envelope_hash,
            table.c.envelope_nonce == run.envelope_nonce,
            table.c.verdict_version == run.verdict_version,
            table.c.requested_by == run.requested_by,
            table.c.started_at == run.started_at,
            table.c.completed_at == run.completed_at,
            table.c.failure_code == run.failure_code,
            table.c.failure_message == run.failure_message,
            table.c.created_at == run.created_at,
            table.c.updated_at == run.updated_at,
        )

    def persist_verified_passport_v2(
        self,
        command: PersistVerifiedPassportV2Command,
    ) -> VerifiedPassportV2Record:
        """Persist one signed Passport V2 graph and its projections atomically."""

        scope = command.scope
        authority = command.authority
        if (
            authority.scope != scope
            or authority.run.id != scope.run_id
            or authority.run.organization_id != scope.organization_id
            or authority.run.system_id != scope.system_id
            or command.initial_authority_hash != command.verified_authority_hash
            or command.passport_revision != 1
            or command.evidence_id is not None
            or command.previous_revision_hash is not None
            or command.evidence_created_at != command.verified_at
            or command.revision_created_at != command.verified_at
        ):
            raise self._error(
                "evidence_admission_integrity_conflict",
                _EVIDENCE_INTEGRITY_MESSAGE,
                409,
            )
        selected = next(
            (
                execution
                for execution in authority.run.suite_executions
                if execution.id == scope.suite_execution_id
            ),
            None,
        )
        if selected is None:
            raise self._error(
                "suite_projection_conflict",
                _SUITE_PROJECTION_CONFLICT_MESSAGE,
                409,
            )
        if self._verified_graph_is_occupied(command):
            raise self._error(
                "evidence_admission_occupied",
                _EVIDENCE_OCCUPIED_MESSAGE,
                409,
            )

        passport = command.passport.to_dict()
        evaluator = passport["evaluator"]
        assert isinstance(evaluator, dict)
        verified_at = self._timestamp_value(command.verified_at)
        captured_at = self._timestamp_value(command.captured_at)
        signed_at = self._timestamp_value(command.signed_at)
        effective_expires_at = self._timestamp_value(command.effective_expires_at)
        evidence_created_at = self._timestamp_value(command.evidence_created_at)
        revision_created_at = self._timestamp_value(command.revision_created_at)
        assert verified_at is not None
        assert captured_at is not None
        assert signed_at is not None
        assert effective_expires_at is not None
        assert evidence_created_at is not None
        assert revision_created_at is not None

        try:
            self.db.execute(
                insert(GovernanceEvidenceRun.__table__).values(
                    id=command.evidence_run_id,
                    org_id=scope.organization_id,
                    workspace_id=authority.run.workspace_id,
                    system_id=scope.system_id,
                    source_type=evaluator["sourceType"],
                    source_identifier=evaluator["evaluatorId"],
                    run_id=scope.suite_execution_id,
                    content_hash=command.passport_content_hash,
                    passport_id=command.passport_id,
                    schema_version=CONTRACT_VERSION,
                    capability_state="available",
                    assurance_source="evaluation",
                    result=command.evidence_result_status,
                    provenance_json=canonical_json({}),
                    artifact_refs_json=canonical_json(_thaw_json_array(command.artifact_refs)),
                    limitations_json=canonical_json(_thaw_json_array(command.limitations)),
                    captured_at=captured_at,
                    expires_at=effective_expires_at,
                    evidence_id=command.evidence_id,
                    created_at=evidence_created_at,
                )
            )
            self.db.execute(
                insert(GovernanceEvidencePassportRevision.__table__).values(
                    id=command.passport_revision_id,
                    org_id=scope.organization_id,
                    system_id=scope.system_id,
                    evidence_run_id=command.evidence_run_id,
                    passport_id=command.passport_id,
                    passport_revision=command.passport_revision,
                    previous_revision_hash=command.previous_revision_hash,
                    canonical_content_hash=command.passport_content_hash,
                    snapshot_json=canonical_json(passport),
                    created_by=command.actor_id,
                    created_at=revision_created_at,
                )
            )
            self.db.execute(
                insert(GovernanceEvidenceVerificationReceipt.__table__).values(
                    id=command.verification_receipt_id,
                    org_id=scope.organization_id,
                    workspace_id=authority.run.workspace_id,
                    system_id=scope.system_id,
                    run_id=scope.run_id,
                    suite_execution_id=scope.suite_execution_id,
                    evidence_run_id=command.evidence_run_id,
                    passport_revision_id=command.passport_revision_id,
                    admission_id=command.admission_id,
                    admission_contract_version=CONTRACT_VERSION,
                    passport_content_hash=command.passport_content_hash,
                    passport_snapshot_hash=command.passport_snapshot_hash,
                    signature_input_hash=command.signature_input_hash,
                    execution_binding_hash=command.execution_binding_hash,
                    execution_binding_json=canonical_json(command.execution_binding.to_dict()),
                    trust_policy_version_id=authority.plan_graph.trust_policy.id,
                    trust_policy_hash=authority.plan_graph.trust_policy.policy_hash,
                    issuer_id=authority.issuer_internal_id,
                    issuer_key=authority.issuer_key,
                    signing_key_id=authority.signing_key_internal_id,
                    signer_key_id=authority.signer_key_id,
                    signer_algorithm=authority.signer_algorithm,
                    public_jwk_json=canonical_json(authority.public_jwk.to_dict()),
                    public_key_fingerprint=command.public_key_fingerprint,
                    evaluator_issuer_id=evaluator["issuerId"],
                    evaluator_id=evaluator["evaluatorId"],
                    source_type=evaluator["sourceType"],
                    adapter_name=evaluator["adapterName"],
                    adapter_version=evaluator["adapterVersion"],
                    result_contract_version=evaluator["resultContractVersion"],
                    evaluator_projection_json=canonical_json(
                        command.evaluator_projection.to_dict()
                    ),
                    evaluator_projection_hash=command.evaluator_projection_hash,
                    verifier_contract=command.verifier_contract,
                    verifier_version=command.verifier_version,
                    verified_at=verified_at,
                )
            )
            self.db.execute(
                insert(GovernanceEvidenceAdmission.__table__).values(
                    id=command.admission_id,
                    org_id=scope.organization_id,
                    workspace_id=authority.run.workspace_id,
                    system_id=scope.system_id,
                    evidence_run_id=command.evidence_run_id,
                    passport_revision_id=command.passport_revision_id,
                    trust_policy_version_id=authority.plan_graph.trust_policy.id,
                    suite_execution_id=scope.suite_execution_id,
                    envelope_hash=authority.run.envelope_hash,
                    admission_status="verified",
                    freshness_status="current",
                    issuer_id=authority.issuer_internal_id,
                    signing_key_id=authority.signing_key_internal_id,
                    signer_key_id=authority.signer_key_id,
                    signer_algorithm=authority.signer_algorithm,
                    reasons_json=canonical_json([]),
                    checked_by="fairmind/evidence-admission-service",
                    checked_at=verified_at,
                    created_at=verified_at,
                    contract_version=CONTRACT_VERSION,
                    run_id=scope.run_id,
                    envelope_id=authority.run.envelope_id,
                    envelope_nonce=authority.run.envelope_nonce,
                    submitted_by=command.actor_id,
                    captured_at=captured_at,
                    signed_at=signed_at,
                    effective_expires_at=effective_expires_at,
                )
            )
            self.db.execute(
                insert(GovernanceEvidenceNonceClaim.__table__).values(
                    id=command.nonce_claim_id,
                    org_id=scope.organization_id,
                    workspace_id=authority.run.workspace_id,
                    system_id=scope.system_id,
                    run_id=scope.run_id,
                    run_contract_version=CONTRACT_VERSION,
                    suite_execution_id=scope.suite_execution_id,
                    admission_id=command.admission_id,
                    admission_contract_version=CONTRACT_VERSION,
                    evidence_run_id=command.evidence_run_id,
                    passport_revision_id=command.passport_revision_id,
                    envelope_id=authority.run.envelope_id,
                    envelope_hash=authority.run.envelope_hash,
                    envelope_nonce=authority.run.envelope_nonce,
                    claimed_by=command.actor_id,
                    claimed_at=verified_at,
                )
            )
            self.db.execute(
                insert(GovernanceEvaluationSuiteEvidenceLink.__table__).values(
                    id=command.suite_evidence_link_id,
                    org_id=scope.organization_id,
                    workspace_id=authority.run.workspace_id,
                    system_id=scope.system_id,
                    run_id=scope.run_id,
                    suite_execution_id=scope.suite_execution_id,
                    admission_id=command.admission_id,
                    admission_contract_version=CONTRACT_VERSION,
                    evidence_run_id=command.evidence_run_id,
                    passport_revision_id=command.passport_revision_id,
                    nonce_claim_id=command.nonce_claim_id,
                    linked_by=command.actor_id,
                    linked_at=verified_at,
                )
            )

            suites = GovernanceEvaluationRunSuiteExecution.__table__
            suite_result = self.db.execute(
                update(suites)
                .where(
                    suites.c.id == selected.id,
                    suites.c.org_id == authority.run.organization_id,
                    suites.c.workspace_id == authority.run.workspace_id,
                    suites.c.system_id == authority.run.system_id,
                    suites.c.run_id == authority.run.id,
                    suites.c.suite_version_id == selected.suite_version_id,
                    suites.c.suite_owner_scope == selected.owner_scope,
                    suites.c.ordinal == selected.ordinal,
                    suites.c.technical_status == selected.technical_status,
                    suites.c.evidence_result_status == selected.evidence_result_status,
                    suites.c.admission_status == selected.admission_status,
                    suites.c.review_status == selected.review_status,
                    suites.c.freshness_status == selected.freshness_status,
                    suites.c.evidence_run_id == selected.evidence_run_id,
                    suites.c.passport_revision_id == selected.passport_revision_id,
                    suites.c.linked_by == selected.linked_by,
                    suites.c.linked_at == selected.linked_at,
                    suites.c.result_summary_json.is_(None),
                    suites.c.limitations_json.is_(None),
                    suites.c.failure_code == selected.failure_code,
                    suites.c.failure_message == selected.failure_message,
                    suites.c.started_at == selected.started_at,
                    suites.c.completed_at == selected.completed_at,
                    suites.c.created_at == selected.created_at,
                    suites.c.updated_at == selected.updated_at,
                )
                .values(
                    technical_status=command.technical_status,
                    evidence_result_status=command.evidence_result_status,
                    admission_status="verified",
                    review_status="pending",
                    freshness_status="current",
                    evidence_run_id=command.evidence_run_id,
                    passport_revision_id=command.passport_revision_id,
                    linked_by=command.actor_id,
                    linked_at=verified_at,
                    result_summary_json=canonical_json(command.result_summary.to_dict()),
                    limitations_json=canonical_json(_thaw_json_array(command.limitations)),
                    started_at=self._timestamp_value(command.suite_started_at),
                    completed_at=self._timestamp_value(command.suite_completed_at),
                    updated_at=verified_at,
                )
            )
            if suite_result.rowcount != 1:
                raise self._error(
                    "suite_projection_conflict",
                    _SUITE_PROJECTION_CONFLICT_MESSAGE,
                    409,
                )

            run_changed = (
                command.run_technical_status != authority.run.technical_status
                or command.run_evidence_outcome != authority.run.evidence_outcome
                or self._timestamp_value(command.run_started_at) != authority.run.started_at
                or self._timestamp_value(command.run_completed_at) != authority.run.completed_at
            )
            runs = GovernanceEvaluationRun.__table__
            if run_changed:
                run_result = self.db.execute(
                    update(runs)
                    .where(*self._exact_run_snapshot_predicates(command))
                    .values(
                        technical_status=command.run_technical_status,
                        evidence_outcome=command.run_evidence_outcome,
                        started_at=self._timestamp_value(command.run_started_at),
                        completed_at=self._timestamp_value(command.run_completed_at),
                        updated_at=verified_at,
                    )
                )
                if run_result.rowcount != 1:
                    raise self._error(
                        "run_projection_conflict",
                        _RUN_PROJECTION_CONFLICT_MESSAGE,
                        409,
                    )
            else:
                observed_run = self.db.execute(
                    select(runs.c.id).where(*self._exact_run_snapshot_predicates(command))
                ).scalar_one_or_none()
                if observed_run is None:
                    raise self._error(
                        "run_projection_conflict",
                        _RUN_PROJECTION_CONFLICT_MESSAGE,
                        409,
                    )
        except DBAPIError as error:
            self._raise_evidence_database_error(error)

        return VerifiedPassportV2Record(
            organization_id=scope.organization_id,
            workspace_id=authority.run.workspace_id,
            system_id=scope.system_id,
            run_id=scope.run_id,
            suite_execution_id=scope.suite_execution_id,
            evidence_run_id=command.evidence_run_id,
            passport_revision_id=command.passport_revision_id,
            verification_receipt_id=command.verification_receipt_id,
            admission_id=command.admission_id,
            nonce_claim_id=command.nonce_claim_id,
            suite_evidence_link_id=command.suite_evidence_link_id,
            envelope_hash=authority.run.envelope_hash,
            passport_content_hash=command.passport_content_hash,
            technical_status=command.technical_status,
            evidence_result_status=command.evidence_result_status,
            admission_status="verified",
            review_status="pending",
            freshness_status="current",
            run_technical_status=command.run_technical_status,
            run_evidence_outcome=command.run_evidence_outcome,
            overall_verdict=authority.run.overall_verdict,
            verdict_version=authority.run.verdict_version,
            effective_expires_at=command.effective_expires_at,
            verified_at=command.verified_at,
        )

    def force_evidence_admission_constraints(self) -> None:
        """Force all deferred receipt/admission bindings before success is returned."""

        if self.db.get_bind().dialect.name != "postgresql":
            return
        try:
            self.db.execute(
                text(
                    "SET CONSTRAINTS "
                    "fk_governance_evidence_verification_receipt_admission, "
                    "governance_evidence_admissions_require_receipt_013c, "
                    "governance_evidence_receipts_require_verified_admission_013c "
                    "IMMEDIATE"
                )
            )
        except DBAPIError as error:
            self._raise_evidence_database_error(error)

    # ------------------------------------------------------------------
    # Verified evidence review.  Reviews are deliberately narrower than a
    # governance decision: they append one accepted/rejected review and only
    # project that decision to the matching suite execution.
    # ------------------------------------------------------------------

    def load_evidence_review_authority_for_update(
        self,
        *,
        scope: EvidenceReviewScope,
    ) -> EvidenceReviewAuthorityRecord | None:
        """Lock the exact admitted graph required for a four-eyes review."""

        system_scope = self._system_scope(
            scope.organization_id,
            scope.system_id,
            lock=True,
        )
        if system_scope is None or system_scope["workspace_id"] != scope.workspace_id:
            return None

        runs = GovernanceEvaluationRun.__table__
        run = (
            self.db.execute(
                select(runs)
                .where(
                    runs.c.id == scope.run_id,
                    runs.c.org_id == scope.organization_id,
                    runs.c.workspace_id == scope.workspace_id,
                    runs.c.system_id == scope.system_id,
                    runs.c.contract_version == CONTRACT_VERSION,
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if run is None:
            return None

        suites = GovernanceEvaluationRunSuiteExecution.__table__
        suite = (
            self.db.execute(
                select(suites)
                .where(
                    suites.c.id == scope.suite_execution_id,
                    suites.c.org_id == scope.organization_id,
                    suites.c.workspace_id == scope.workspace_id,
                    suites.c.system_id == scope.system_id,
                    suites.c.run_id == scope.run_id,
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if suite is None or suite["evidence_run_id"] is None:
            return None

        admissions = GovernanceEvidenceAdmission.__table__
        admission = (
            self.db.execute(
                select(admissions)
                .where(
                    admissions.c.id == scope.admission_id,
                    admissions.c.org_id == scope.organization_id,
                    admissions.c.workspace_id == scope.workspace_id,
                    admissions.c.system_id == scope.system_id,
                    admissions.c.run_id == scope.run_id,
                    admissions.c.suite_execution_id == scope.suite_execution_id,
                    admissions.c.evidence_run_id == suite["evidence_run_id"],
                    admissions.c.passport_revision_id == scope.passport_revision_id,
                    admissions.c.contract_version == CONTRACT_VERSION,
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if admission is None or suite["passport_revision_id"] != scope.passport_revision_id:
            return None

        links = GovernanceEvaluationSuiteEvidenceLink.__table__
        link = (
            self.db.execute(
                select(links)
                .where(
                    links.c.org_id == scope.organization_id,
                    links.c.workspace_id == scope.workspace_id,
                    links.c.system_id == scope.system_id,
                    links.c.run_id == scope.run_id,
                    links.c.suite_execution_id == scope.suite_execution_id,
                    links.c.admission_id == scope.admission_id,
                    links.c.admission_contract_version == CONTRACT_VERSION,
                    links.c.evidence_run_id == admission["evidence_run_id"],
                    links.c.passport_revision_id == scope.passport_revision_id,
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if link is None:
            return None

        reviews = GovernanceEvidenceReview.__table__
        latest_review = (
            self.db.execute(
                select(reviews)
                .where(
                    reviews.c.org_id == scope.organization_id,
                    reviews.c.workspace_id == scope.workspace_id,
                    reviews.c.system_id == scope.system_id,
                    reviews.c.run_id == scope.run_id,
                    reviews.c.suite_execution_id == scope.suite_execution_id,
                    reviews.c.admission_id == scope.admission_id,
                    reviews.c.admission_contract_version == CONTRACT_VERSION,
                    reviews.c.evidence_run_id == admission["evidence_run_id"],
                    reviews.c.passport_revision_id == scope.passport_revision_id,
                )
                .order_by(reviews.c.review_version.desc(), reviews.c.id.desc())
                .limit(1)
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )

        trust_policies = GovernanceEvidenceTrustPolicyVersion.__table__
        trust_policy = (
            self.db.execute(
                select(trust_policies)
                .where(
                    trust_policies.c.id == admission["trust_policy_version_id"],
                    trust_policies.c.org_id == scope.organization_id,
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        issuer_id = admission["issuer_id"]
        signing_key_id = admission["signing_key_id"]
        signer_key_id = admission["signer_key_id"]
        if (
            trust_policy is None
            or not isinstance(issuer_id, str)
            or not isinstance(signing_key_id, str)
            or not isinstance(signer_key_id, str)
        ):
            raise self._error(
                "binding_integrity_error",
                _BINDING_INTEGRITY_MESSAGE,
                409,
            )
        issuers = GovernanceEvidenceIssuer.__table__
        issuer = (
            self.db.execute(
                select(issuers)
                .where(
                    issuers.c.id == issuer_id,
                    issuers.c.org_id == scope.organization_id,
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        signing_keys = GovernanceEvidenceSigningKey.__table__
        signing_key = (
            self.db.execute(
                select(signing_keys)
                .where(
                    signing_keys.c.id == signing_key_id,
                    signing_keys.c.org_id == scope.organization_id,
                    signing_keys.c.issuer_id == issuer_id,
                    signing_keys.c.key_id == signer_key_id,
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if issuer is None or signing_key is None:
            raise self._error(
                "binding_integrity_error",
                _BINDING_INTEGRITY_MESSAGE,
                409,
            )

        decisions = GovernanceEvaluationDecision.__table__
        governance_decision_exists = (
            self.db.execute(
                select(decisions.c.id).where(
                    decisions.c.org_id == scope.organization_id,
                    decisions.c.workspace_id == scope.workspace_id,
                    decisions.c.system_id == scope.system_id,
                    decisions.c.run_id == scope.run_id,
                    decisions.c.run_contract_version == CONTRACT_VERSION,
                )
            ).scalar_one_or_none()
            is not None
        )

        try:
            current_review_version = 0 if latest_review is None else latest_review["review_version"]
            if (
                isinstance(current_review_version, bool)
                or not isinstance(current_review_version, int)
                or current_review_version < 0
            ):
                raise ValueError("review version is invalid")
            required_strings = (
                admission["evidence_run_id"],
                admission["submitted_by"],
                link["linked_by"],
                run["requested_by"],
                admission["admission_status"],
                admission["freshness_status"],
                suite["review_status"],
                trust_policy["status"],
                issuer["status"],
                suite["technical_status"],
                suite["evidence_result_status"],
                run["technical_status"],
                run["evidence_outcome"],
            )
            if any(not isinstance(value, str) or not value for value in required_strings):
                raise ValueError("review authority strings are invalid")
            effective_expires_at = _parse_timestamp(admission["effective_expires_at"])
            key_valid_from = _parse_timestamp(signing_key["valid_from"])
            key_valid_until = _parse_timestamp(signing_key["valid_until"])
            key_revoked_at = (
                None
                if signing_key["revoked_at"] is None
                else _parse_timestamp(signing_key["revoked_at"])
            )
        except (AttributeError, TypeError, ValueError) as error:
            raise self._error(
                "binding_integrity_error",
                _BINDING_INTEGRITY_MESSAGE,
                409,
            ) from error

        return EvidenceReviewAuthorityRecord(
            scope=scope,
            evidence_run_id=admission["evidence_run_id"],
            admission_contract_version=admission["contract_version"],
            admission_status=admission["admission_status"],
            freshness_status=admission["freshness_status"],
            review_status=suite["review_status"],
            current_review_version=current_review_version,
            submitted_by=admission["submitted_by"],
            linked_by=link["linked_by"],
            run_requested_by=run["requested_by"],
            effective_expires_at=effective_expires_at,
            trust_policy_status=trust_policy["status"],
            issuer_status=issuer["status"],
            key_valid_from=key_valid_from,
            key_valid_until=key_valid_until,
            key_revoked_at=key_revoked_at,
            technical_status=suite["technical_status"],
            evidence_result_status=suite["evidence_result_status"],
            run_technical_status=run["technical_status"],
            run_evidence_outcome=run["evidence_outcome"],
            governance_decision_exists=governance_decision_exists,
        )

    @staticmethod
    def _evidence_review_database_error(error: DBAPIError) -> EvaluationWorkbenchError | None:
        original = getattr(error, "orig", None)
        sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        constraint_name = getattr(getattr(original, "diag", None), "constraint_name", None)
        first_line = str(original).partition("\n")[0].strip().lower()
        if sqlstate == "23505" and constraint_name in _EVIDENCE_REVIEW_VERSION_CONSTRAINTS:
            return EvaluationWorkbenchError(
                "evidence_review_version_conflict",
                "The evidence review version is stale.",
                status_code=409,
            )
        if sqlstate == "P0001" and first_line in _EVIDENCE_REVIEW_TRIGGER_MESSAGES:
            code, message = _EVIDENCE_REVIEW_TRIGGER_MESSAGES[first_line]
            return EvaluationWorkbenchError(code, message, status_code=409)
        return None

    def persist_evidence_review(
        self,
        command: PersistEvidenceReviewCommand,
    ) -> ReviewedEvidenceRecord:
        """Append one review and CAS only the suite's review-status projection."""

        scope = command.scope
        authority = command.authority
        if (
            authority.scope != scope
            or authority.admission_contract_version != CONTRACT_VERSION
            or command.expected_review_version != authority.current_review_version
            or command.next_review_version != authority.current_review_version + 1
            or command.next_review_version != 1
            or command.decision not in {"accepted", "rejected"}
            or authority.admission_status != "verified"
            or authority.freshness_status != "current"
            or authority.review_status != "pending"
            or authority.current_review_version != 0
            or authority.governance_decision_exists
        ):
            raise self._error(
                "evidence_review_integrity_conflict",
                "The evidence-review authority changed before persistence.",
                409,
            )
        reviewed_at = self._timestamp_value(command.reviewed_at)
        if reviewed_at is None:
            raise self._error(
                "evidence_review_chronology_invalid",
                "The evidence-review chronology is invalid.",
                409,
            )

        reviews = GovernanceEvidenceReview.__table__
        suites = GovernanceEvaluationRunSuiteExecution.__table__
        try:
            self.db.execute(
                insert(reviews).values(
                    id=command.review_id,
                    org_id=scope.organization_id,
                    system_id=scope.system_id,
                    evidence_run_id=authority.evidence_run_id,
                    passport_revision_id=scope.passport_revision_id,
                    admission_id=scope.admission_id,
                    decision=command.decision,
                    rationale=command.rationale,
                    reviewed_by=command.actor_id,
                    review_version=command.next_review_version,
                    separation_override_reason=None,
                    reviewed_at=reviewed_at,
                    workspace_id=scope.workspace_id,
                    run_id=scope.run_id,
                    suite_execution_id=scope.suite_execution_id,
                    admission_contract_version=CONTRACT_VERSION,
                )
            )
            updated = self.db.execute(
                update(suites)
                .where(
                    suites.c.id == scope.suite_execution_id,
                    suites.c.org_id == scope.organization_id,
                    suites.c.workspace_id == scope.workspace_id,
                    suites.c.system_id == scope.system_id,
                    suites.c.run_id == scope.run_id,
                    suites.c.evidence_run_id == authority.evidence_run_id,
                    suites.c.passport_revision_id == scope.passport_revision_id,
                    suites.c.admission_status == "verified",
                    suites.c.freshness_status == "current",
                    suites.c.review_status == "pending",
                    suites.c.linked_by == authority.linked_by,
                )
                .values(
                    review_status=command.decision,
                )
            )
            if updated.rowcount != 1:
                raise self._error(
                    "evidence_review_projection_conflict",
                    "The suite execution changed before evidence review could be recorded.",
                    409,
                )
        except DBAPIError as error:
            mapped = self._evidence_review_database_error(error)
            if mapped is not None:
                raise mapped from error
            raise

        return ReviewedEvidenceRecord(
            review_id=command.review_id,
            organization_id=scope.organization_id,
            workspace_id=scope.workspace_id,
            system_id=scope.system_id,
            run_id=scope.run_id,
            suite_execution_id=scope.suite_execution_id,
            admission_id=scope.admission_id,
            passport_revision_id=scope.passport_revision_id,
            evidence_run_id=authority.evidence_run_id,
            decision=command.decision,
            rationale=command.rationale,
            review_version=command.next_review_version,
            reviewed_by=command.actor_id,
            reviewed_at=command.reviewed_at,
            admission_status="verified",
            review_status=command.decision,
            freshness_status="current",
            technical_status=authority.technical_status,
            evidence_result_status=authority.evidence_result_status,
            run_technical_status=authority.run_technical_status,
            run_evidence_outcome=authority.run_evidence_outcome,
        )

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

    def _run_record_from_rows(
        self,
        row: Mapping[str, Any],
        executions: list[Mapping[str, Any]],
    ) -> RunRecord:
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

    def _run_record(self, row: Mapping[str, Any]) -> RunRecord:
        executions = list(
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
        return self._run_record_from_rows(row, executions)

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
