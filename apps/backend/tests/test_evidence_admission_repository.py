"""Repository integration tests for atomic verified Passport V2 admission."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, func, insert, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

import src.infrastructure.db.repositories.evaluation_workbench_repository as repository_module
from database.governance_models import (
    GovernanceEvaluationRun,
    GovernanceEvaluationRunSuiteExecution,
    GovernanceEvaluationSuiteEvidenceLink,
    GovernanceEvidenceAdmission,
    GovernanceEvidenceArtifact,
    GovernanceEvidenceIssuer,
    GovernanceEvidenceNonceClaim,
    GovernanceEvidencePassportRevision,
    GovernanceEvidenceRun,
    GovernanceEvidenceSigningKey,
    GovernanceEvidenceTrustPolicyVersion,
    GovernanceEvidenceVerificationReceipt,
    GovernanceEvaluatorRegistration,
)
from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
)
from src.application.ports.evidence_admission import (
    EvidenceAdmissionAuthorityRecord,
    EvidenceAdmissionScope,
    PersistVerifiedPassportV2Command,
)
from src.application.ports.evidence_freshness import EvidenceFreshnessClassification
from src.application.services.trusted_evidence_admission_resolver import (
    TrustedEvidenceAdmissionResolver,
)
from src.application.services.evaluator_catalog_service import evaluator_binding_hash
from src.application.services.evaluator_registration import EvaluatorIdentityBinding
from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256
from src.domain.assurance.evidence_passport_v2 import (
    evidence_passport_v2_content_hash,
    evidence_passport_v2_signature_bytes,
    expected_execution_binding_v2,
    normalize_evidence_passport_v2,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchRepository,
)
from tests.test_evaluation_workbench_repository import (
    ORG,
    OTHER_ORG,
    USER,
    _create_active_plan_and_run,
    _service,
    _suite_payload,
    _target_payload,
    repository_fixture as base_repository_fixture,
)
from tests.evaluation_workbench_sqlite import (
    active_trust_policy_values_for_verifier_harness,
    public_signing_key_values_for_verifier_harness,
)


@pytest.fixture
def repository_fixture(base_repository_fixture):
    """Exercise repository admission against the installed 013d receipt shape."""

    session, factory = base_repository_fixture
    from migrations.evaluator_catalog_migration import apply_sqlite

    raw_connection = session.connection().connection.driver_connection
    apply_sqlite(raw_connection)
    session.expire_all()
    yield session, factory


def test_sqlite_fresh_clock_is_utc_and_does_not_use_the_process_clock(monkeypatch) -> None:
    """Catches replacing the trusted database clock with the process clock."""

    engine = create_engine("sqlite://")
    process_time = datetime(1999, 12, 31, tzinfo=timezone.utc)
    monkeypatch.setattr(repository_module, "_now", lambda: process_time)

    with Session(engine) as session:
        observed = SqlAlchemyEvaluationWorkbenchRepository(session).read_fresh_utc_now()

    assert observed.tzinfo == timezone.utc
    assert observed.year >= 2026
    assert observed != process_time


class _PostgresFailure(Exception):
    """Minimal psycopg-shaped failure for testing the repository boundary."""

    def __init__(
        self,
        message: str,
        *,
        sqlstate: str,
        constraint_name: str | None = None,
    ) -> None:
        super().__init__(message)
        self.sqlstate = sqlstate
        self.pgcode = sqlstate
        self.diag = SimpleNamespace(constraint_name=constraint_name)


def _postgres_database_error(
    *,
    sqlstate: str,
    message: str,
    constraint_name: str | None = None,
    integrity: bool = False,
) -> DBAPIError:
    original = _PostgresFailure(
        message,
        sqlstate=sqlstate,
        constraint_name=constraint_name,
    )
    error_type = IntegrityError if integrity else DBAPIError
    return error_type("INSERT INTO evidence_graph", {}, original)


@pytest.mark.parametrize(
    "constraint_name",
    (
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
    ),
)
def test_database_error_classifier_bounds_only_named_evidence_occupancy_constraints(
    constraint_name: str,
) -> None:
    error = _postgres_database_error(
        sqlstate="23505",
        message=f'duplicate key violates unique constraint "{constraint_name}"',
        constraint_name=constraint_name,
        integrity=True,
    )

    assert (
        SqlAlchemyEvaluationWorkbenchRepository._evidence_database_error_kind(error) == "occupied"
    )


@pytest.mark.parametrize(
    ("sqlstate", "constraint_name"),
    (
        ("23505", "uq_unrelated_tenant_identity"),
        ("23505", "governance_evidence_runs_pkey"),
        ("23505", "uq_governance_passport_revision"),
        ("23505", "uq_governance_passport_run_revision"),
        ("23505", "uq_governance_passport_run_hash"),
        ("23503", "fk_governance_evidence_verification_receipt_run"),
        ("23514", "ck_governance_evidence_run_result"),
    ),
)
def test_database_error_classifier_propagates_unexpected_integrity_failures(
    sqlstate: str,
    constraint_name: str,
) -> None:
    error = _postgres_database_error(
        sqlstate=sqlstate,
        message="unexpected database integrity failure",
        constraint_name=constraint_name,
        integrity=True,
    )

    assert SqlAlchemyEvaluationWorkbenchRepository._evidence_database_error_kind(error) is None


@pytest.mark.parametrize(
    "message",
    (
        "verified admission trust eligibility failed",
        "nonce claim requires an eligible exact admission",
        "nonce claim admission is not policy-eligible",
        "nonce claim timestamp is not causal",
        "evidence link requires an eligible claimed admission",
        "evidence link timestamp is not causal",
        "verification receipt relational binding failed",
        "verified admission requires exact verification receipt",
        "verification receipt requires exact verified admission",
    ),
)
def test_database_error_classifier_bounds_only_exact_known_trigger_failures(
    message: str,
) -> None:
    error = _postgres_database_error(
        sqlstate="P0001",
        message=f"{message}\nCONTEXT: PL/pgSQL function evidence_guard()",
    )

    assert (
        SqlAlchemyEvaluationWorkbenchRepository._evidence_database_error_kind(error) == "integrity"
    )


@pytest.mark.parametrize(
    "message",
    (
        "unknown evidence trigger failure",
        "prefix verification receipt relational binding failed suffix",
    ),
)
def test_database_error_classifier_propagates_unexpected_raise_exceptions(
    message: str,
) -> None:
    error = _postgres_database_error(sqlstate="P0001", message=message)

    assert SqlAlchemyEvaluationWorkbenchRepository._evidence_database_error_kind(error) is None


def test_database_error_boundary_reraises_the_original_unexpected_integrity_error() -> None:
    engine = create_engine("sqlite://")
    original = _postgres_database_error(
        sqlstate="23514",
        message="unexpected check constraint failure",
        constraint_name="ck_unrelated_state",
        integrity=True,
    )
    with Session(engine) as session:
        repository = SqlAlchemyEvaluationWorkbenchRepository(session)

        with pytest.raises(DBAPIError) as caught:
            repository._raise_evidence_database_error(original)

    assert caught.value is original


def _seed_signing_authority(
    session: Session,
    *,
    org_id: str = ORG,
    actor_id: str = USER,
    issuer_key: str = "issuer-protocol-key",
    signer_key_id: str = "signer-protocol-key",
    public_x: str = "A" * 43,
    suite_restrictions: tuple[str, ...] = (),
    target_restrictions: tuple[str, ...] = (),
) -> tuple[str, str]:
    issuer_internal_id = str(uuid.uuid4())
    signing_key_internal_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    session.execute(
        insert(GovernanceEvidenceIssuer.__table__).values(
            id=issuer_internal_id,
            org_id=org_id,
            issuer_key=issuer_key,
            name="Trusted evaluator",
            issuer_type="external_provider",
            source_restrictions_json=canonical_json(["external_provider"]),
            suite_restrictions_json=canonical_json(list(suite_restrictions)),
            target_restrictions_json=canonical_json(list(target_restrictions)),
            status="active",
            created_by=actor_id,
            created_at=(now - timedelta(minutes=1)).isoformat(),
            updated_at=(now - timedelta(minutes=1)).isoformat(),
        )
    )
    session.execute(
        insert(GovernanceEvidenceSigningKey.__table__).values(
            **public_signing_key_values_for_verifier_harness(
                signing_key_id=signing_key_internal_id,
                organization_id=org_id,
                issuer_id=issuer_internal_id,
                protocol_key_id=signer_key_id,
                actor_id=actor_id,
                created_at=(now - timedelta(minutes=1)).isoformat(),
                valid_from=(now - timedelta(days=1)).isoformat(),
                valid_until=(now + timedelta(days=1)).isoformat(),
                public_x=public_x,
            )
        )
    )
    session.commit()
    return issuer_internal_id, signing_key_internal_id


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None
    return parsed.astimezone(timezone.utc)


def _frozen_array(values: list[object]) -> tuple[object, ...]:
    frozen = FrozenJsonObject.from_mapping({"items": values})["items"]
    assert isinstance(frozen, tuple)
    return frozen


def _verified_after_locked_graph(
    repository: SqlAlchemyEvaluationWorkbenchRepository,
    authority: EvidenceAdmissionAuthorityRecord,
) -> datetime:
    floor = max(
        _parse_utc(authority.run.updated_at),
        *(_parse_utc(execution.updated_at) for execution in authority.run.suite_executions),
    )
    for _attempt in range(5_000):
        observed = repository.read_fresh_utc_now()
        if observed > floor:
            return observed
    raise AssertionError("SQLite database clock did not advance beyond the locked graph")


def _ensure_approved_catalog_registration(
    session: Session,
    *,
    authority: EvidenceAdmissionAuthorityRecord,
    evaluator: dict[str, object],
    submitted_at: datetime,
) -> tuple[str, str]:
    """Seed the durable, exact registration required by direct repo tests."""

    binding = EvaluatorIdentityBinding(
        evaluator_id=str(evaluator["evaluatorId"]),
        source_type=str(evaluator["sourceType"]),
        adapter_name=str(evaluator["adapterName"]),
        adapter_version=str(evaluator["adapterVersion"]),
        result_contract_version=str(evaluator["resultContractVersion"]),
        issuer_id=str(evaluator["issuerId"]),
        key_id=authority.signer_key_id,
    )
    table = GovernanceEvaluatorRegistration.__table__
    existing = session.execute(
        select(table.c.id, table.c.binding_hash).where(
            table.c.org_id == authority.scope.organization_id,
            table.c.evaluator_id == binding.evaluator_id,
            table.c.source_type == binding.source_type,
            table.c.adapter_name == binding.adapter_name,
            table.c.adapter_version == binding.adapter_version,
            table.c.result_contract_version == binding.result_contract_version,
            table.c.issuer_id == binding.issuer_id,
            table.c.signing_key_id == binding.key_id,
        )
    ).one_or_none()
    if existing is not None:
        return str(existing.id), str(existing.binding_hash)
    registration_id = str(uuid.uuid4())
    binding_hash = evaluator_binding_hash(binding)
    session.execute(
        insert(table).values(
            id=registration_id,
            org_id=authority.scope.organization_id,
            evaluator_id=binding.evaluator_id,
            source_type=binding.source_type,
            adapter_name=binding.adapter_name,
            adapter_version=binding.adapter_version,
            result_contract_version=binding.result_contract_version,
            issuer_id=binding.issuer_id,
            signing_key_id=binding.key_id,
            authority_issuer_id=authority.issuer_internal_id,
            authority_signing_key_id=authority.signing_key_internal_id,
            binding_hash=binding_hash,
            status="pending",
            submitted_by=USER,
            submitted_at=(submitted_at - timedelta(seconds=1)).isoformat(),
            reviewed_by=None,
            reviewed_at=None,
            review_rationale=None,
            revoked_by=None,
            revoked_at=None,
            revocation_rationale=None,
        )
    )
    session.execute(
        table.update()
        .where(table.c.id == registration_id, table.c.org_id == authority.scope.organization_id)
        .values(
            status="approved",
            reviewed_by="catalog-reviewer",
            reviewed_at=submitted_at.isoformat(),
            review_rationale="Independent review approved the exact evaluator binding.",
        )
    )
    return registration_id, binding_hash


def _admission_command(
    session: Session,
    run: dict[str, object],
    *,
    execution_index: int = 0,
    technical_status: str = "succeeded",
    evidence_result_status: str = "failed",
    run_technical_status: str | None = None,
    run_evidence_outcome: str | None = None,
) -> PersistVerifiedPassportV2Command:
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    suite_executions = run["suiteExecutions"]
    assert isinstance(suite_executions, list)
    selected = suite_executions[execution_index]
    assert isinstance(selected, dict)
    scope = EvidenceAdmissionScope(
        organization_id=ORG,
        system_id="system-a",
        run_id=str(run["id"]),
        suite_execution_id=str(selected["id"]),
    )
    authority = repository.load_admission_authority_for_update(
        scope=scope,
        issuer_key="issuer-protocol-key",
        signer_key_id="signer-protocol-key",
    )
    assert authority is not None
    envelope = authority.run.envelope.to_dict()
    binding = expected_execution_binding_v2(envelope, scope.suite_execution_id)
    plan_suite = next(
        item for item in authority.plan_graph.suites if item.suite.id == selected["suiteVersionId"]
    )
    captured_at = _parse_utc(str(envelope["requestedAt"]))
    signed_at = captured_at
    verified_at = _verified_after_locked_graph(repository, authority)
    effective_expires_at = min(
        captured_at + timedelta(hours=12),
        captured_at + timedelta(seconds=authority.maximum_evidence_age_seconds),
        authority.key_valid_until,
    )
    result_summary = (
        {"reason": "cancelled by evaluator"}
        if technical_status == "cancelled"
        else {"caseCount": 200, "attackSuccessRate": 0.17}
    )
    artifacts = [
        {
            "artifactId": str(uuid.uuid4()),
            "role": "report",
            "sha256": "f" * 64,
            "mediaType": "application/json",
            "sizeBytes": 4096,
        }
    ]
    limitations = ["Supporting evidence only."]
    evaluator = {
        "issuerId": authority.issuer_key,
        "evaluatorId": "evaluator-a",
        "sourceType": "external_provider",
        "adapterName": plan_suite.suite.adapter_name,
        "adapterVersion": plan_suite.suite.adapter_version,
        "resultContractVersion": plan_suite.suite.result_contract_version,
    }
    evaluator_registration_id, evaluator_registration_binding_hash = (
        _ensure_approved_catalog_registration(
            session,
            authority=authority,
            evaluator=evaluator,
            submitted_at=captured_at,
        )
    )
    passport: dict[str, object] = {
        "schemaVersion": "2.0.0",
        "passportId": str(uuid.uuid4()),
        "passportRevision": 1,
        "claimBoundary": "supporting_evidence_only",
        "organizationId": ORG,
        "workspaceId": authority.run.workspace_id,
        "systemId": scope.system_id,
        "capturedAt": captured_at.isoformat(),
        "contentHash": "0" * 64,
        "executionBinding": binding,
        "evaluator": evaluator,
        "expiresAt": effective_expires_at.isoformat(),
        "result": {
            "technicalStatus": technical_status,
            "evidenceResultStatus": evidence_result_status,
            "summary": result_summary,
        },
        "artifacts": artifacts,
        "limitations": limitations,
        "signature": {
            "algorithm": "Ed25519",
            "issuerId": authority.issuer_key,
            "keyId": authority.signer_key_id,
            "signedAt": signed_at.isoformat(),
            "value": "A" * 86,
        },
    }
    passport["contentHash"] = evidence_passport_v2_content_hash(passport)
    passport = normalize_evidence_passport_v2(passport)
    passport_json = canonical_json(passport)
    binding_json = FrozenJsonObject.from_mapping(binding)
    evaluator_json = FrozenJsonObject.from_mapping(evaluator)
    result_json = FrozenJsonObject.from_mapping(result_summary)

    if run_technical_status is None:
        run_technical_status = (
            technical_status if len(suite_executions) == 1 else authority.run.technical_status
        )
    if run_evidence_outcome is None:
        run_evidence_outcome = (
            evidence_result_status if len(suite_executions) == 1 else authority.run.evidence_outcome
        )
    suite_started_at = None if technical_status == "cancelled" else captured_at
    if run_technical_status in {"awaiting_evidence", "queued", "leased"}:
        run_started_at = None
        run_completed_at = None
    elif run_technical_status == "running":
        run_started_at = captured_at
        run_completed_at = None
    else:
        run_started_at = None if run_technical_status == "cancelled" else captured_at
        run_completed_at = verified_at

    return PersistVerifiedPassportV2Command(
        scope=scope,
        actor_id=USER,
        evidence_run_id=str(uuid.uuid4()),
        passport_revision_id=str(uuid.uuid4()),
        verification_receipt_id=str(uuid.uuid4()),
        admission_id=str(uuid.uuid4()),
        nonce_claim_id=str(uuid.uuid4()),
        suite_evidence_link_id=str(uuid.uuid4()),
        authority=authority,
        initial_authority_hash="a" * 64,
        verified_authority_hash="a" * 64,
        passport=FrozenJsonObject.from_mapping(passport),
        passport_id=str(passport["passportId"]),
        passport_revision=1,
        passport_content_hash=str(passport["contentHash"]),
        passport_snapshot_hash=hashlib.sha256(passport_json.encode("utf-8")).hexdigest(),
        signature_input_hash=hashlib.sha256(
            evidence_passport_v2_signature_bytes(passport)
        ).hexdigest(),
        execution_binding=binding_json,
        execution_binding_hash=canonical_sha256(binding),
        evaluator_projection=evaluator_json,
        evaluator_projection_hash=canonical_sha256(evaluator),
        evaluator_registration_id=evaluator_registration_id,
        evaluator_registration_binding_hash=evaluator_registration_binding_hash,
        public_key_fingerprint=canonical_sha256(authority.public_jwk.to_dict()),
        verifier_contract="fairmind/evidence-passport-v2/verified-admission",
        verifier_version="2.0.0",
        technical_status=technical_status,
        evidence_result_status=evidence_result_status,
        result_summary=result_json,
        artifact_refs=_frozen_array(artifacts),
        limitations=_frozen_array(limitations),
        captured_at=captured_at,
        signed_at=signed_at,
        effective_expires_at=effective_expires_at,
        verified_at=verified_at,
        evidence_id=None,
        previous_revision_hash=None,
        evidence_created_at=verified_at,
        revision_created_at=verified_at,
        suite_started_at=suite_started_at,
        suite_completed_at=verified_at,
        run_technical_status=run_technical_status,
        run_evidence_outcome=run_evidence_outcome,
        run_started_at=run_started_at,
        run_completed_at=run_completed_at,
    )


def _seed_complete_foreign_authority(session: Session) -> SimpleNamespace:
    """Create a real tenant-B target/suite/plan/run/trust/signer authority graph."""

    trust_policy_id = "trust-b"
    now = datetime.now(timezone.utc)
    session.execute(
        insert(GovernanceEvidenceTrustPolicyVersion.__table__).values(
            **active_trust_policy_values_for_verifier_harness(
                policy_id=trust_policy_id,
                organization_id=OTHER_ORG,
                actor_id=USER,
                created_at=now.isoformat(),
            )
        )
    )
    session.commit()

    service = _service(session)
    target = service.create_target_version(
        org_id=OTHER_ORG,
        system_id="system-b",
        actor_id=USER,
        idempotency_key=f"foreign-target-{uuid.uuid4()}",
        payload=_target_payload("foreign-agent-prod"),
    ).body
    suite = service.create_suite_version(
        org_id=OTHER_ORG,
        actor_id=USER,
        idempotency_key=f"foreign-suite-{uuid.uuid4()}",
        payload=_suite_payload("foreign-agent-safety"),
    ).body
    service.activate_suite_version(
        org_id=OTHER_ORG,
        suite_version_id=suite["id"],
        actor_id=USER,
        idempotency_key=f"foreign-suite-activate-{uuid.uuid4()}",
    )
    plan = service.create_plan(
        org_id=OTHER_ORG,
        system_id="system-b",
        actor_id=USER,
        idempotency_key=f"foreign-plan-{uuid.uuid4()}",
        payload={
            "contractVersion": "2.0.0",
            "name": "Foreign tenant admission authority",
            "targetVersionId": target["id"],
            "lifecyclePhases": ["pre_deploy"],
            "executionDepth": "deep",
            "enforcementMode": "human_approval",
            "deliveryMode": "external_provider",
            "trustPolicyVersionId": trust_policy_id,
            "suites": [{"suiteVersionId": suite["id"]}],
        },
    ).body
    service.activate_plan(
        org_id=OTHER_ORG,
        system_id="system-b",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key=f"foreign-plan-activate-{uuid.uuid4()}",
    )
    run = service.create_run(
        org_id=OTHER_ORG,
        system_id="system-b",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key=f"foreign-run-{uuid.uuid4()}",
        payload={"trigger": "manual", "lifecyclePhase": "pre_deploy"},
    ).body
    issuer_internal_id, signing_key_internal_id = _seed_signing_authority(
        session,
        org_id=OTHER_ORG,
        issuer_key="foreign-issuer-protocol-key",
        signer_key_id="foreign-signer-protocol-key",
        public_x=("A" * 42) + "E",
        suite_restrictions=(suite["id"],),
        target_restrictions=(target["id"],),
    )
    return SimpleNamespace(
        org_id=OTHER_ORG,
        workspace_id="workspace-b",
        system_id="system-b",
        target_version_id=target["id"],
        suite_version_id=suite["id"],
        plan_id=plan["id"],
        run_id=run["id"],
        suite_execution_id=run["suiteExecutions"][0]["id"],
        trust_policy_id=trust_policy_id,
        issuer_internal_id=issuer_internal_id,
        issuer_key="foreign-issuer-protocol-key",
        signing_key_internal_id=signing_key_internal_id,
        signer_key_id="foreign-signer-protocol-key",
    )


def _evidence_graph_counts_for_org(session: Session, org_id: str) -> dict[str, int]:
    tables = {
        "evidence_runs": GovernanceEvidenceRun.__table__,
        "revisions": GovernanceEvidencePassportRevision.__table__,
        "receipts": GovernanceEvidenceVerificationReceipt.__table__,
        "admissions": GovernanceEvidenceAdmission.__table__,
        "nonce_claims": GovernanceEvidenceNonceClaim.__table__,
        "suite_links": GovernanceEvaluationSuiteEvidenceLink.__table__,
    }
    return {
        label: int(
            session.scalar(select(func.count()).select_from(table).where(table.c.org_id == org_id))
            or 0
        )
        for label, table in tables.items()
    }


def _assert_no_evidence_graph_in_either_tenant(session: Session) -> None:
    empty = {
        "evidence_runs": 0,
        "revisions": 0,
        "receipts": 0,
        "admissions": 0,
        "nonce_claims": 0,
        "suite_links": 0,
    }
    assert _evidence_graph_counts_for_org(session, ORG) == empty
    assert _evidence_graph_counts_for_org(session, OTHER_ORG) == empty


def test_authority_load_reconstructs_the_complete_locked_multisuite_graph(
    repository_fixture,
) -> None:
    """Catches partial scope loads and internal/protocol signing-ID confusion."""

    session, _factory = repository_fixture
    plan, run = _create_active_plan_and_run(_service(session), suites=2)
    target_id = plan["targetVersionId"]
    suite_ids = tuple(execution["suiteVersionId"] for execution in run["suiteExecutions"])
    issuer_internal_id, signing_key_internal_id = _seed_signing_authority(
        session,
        suite_restrictions=suite_ids,
        target_restrictions=(target_id,),
    )
    scope = EvidenceAdmissionScope(
        organization_id=ORG,
        system_id="system-a",
        run_id=run["id"],
        suite_execution_id=run["suiteExecutions"][1]["id"],
    )
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)

    authority = repository.load_admission_authority_for_update(
        scope=scope,
        issuer_key="issuer-protocol-key",
        signer_key_id="signer-protocol-key",
    )

    assert authority is not None
    assert authority.scope == scope
    assert authority.plan_graph.plan.id == run["planId"]
    assert authority.plan_graph.target.id == target_id
    assert tuple(item.suite.id for item in authority.plan_graph.suites) == suite_ids
    assert tuple(item.id for item in authority.run.suite_executions) == tuple(
        execution["id"] for execution in run["suiteExecutions"]
    )
    assert authority.issuer_internal_id == issuer_internal_id
    assert authority.issuer_key == "issuer-protocol-key"
    assert authority.signing_key_internal_id == signing_key_internal_id
    assert authority.signer_key_id == "signer-protocol-key"
    assert authority.source_restrictions == ("external_provider",)
    assert authority.suite_restrictions == suite_ids
    assert authority.target_restrictions == (target_id,)


def test_restriction_reference_check_is_exactly_tenant_and_system_scoped(
    repository_fixture,
) -> None:
    """Catches accepting unknown or cross-scope catalog restriction identities."""

    session, _factory = repository_fixture
    plan, run = _create_active_plan_and_run(_service(session), suites=2)
    scope = EvidenceAdmissionScope(
        organization_id=ORG,
        system_id="system-a",
        run_id=run["id"],
        suite_execution_id=run["suiteExecutions"][0]["id"],
    )
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    suite_ids = tuple(execution["suiteVersionId"] for execution in run["suiteExecutions"])
    target_id = plan["targetVersionId"]

    assert repository.restriction_references_exist(
        scope=scope,
        suite_version_ids=suite_ids,
        target_version_ids=(target_id,),
    )
    assert not repository.restriction_references_exist(
        scope=scope,
        suite_version_ids=suite_ids + ("unknown-suite",),
        target_version_ids=(target_id,),
    )
    assert not repository.restriction_references_exist(
        scope=scope,
        suite_version_ids=suite_ids,
        target_version_ids=("unknown-target",),
    )


def test_real_foreign_tenant_scope_and_signer_identities_resolve_no_authority_or_graph(
    repository_fixture,
) -> None:
    """Catches dropping any tenant/run/suite/signer predicate from authority loading."""

    session, _factory = repository_fixture
    _plan, run = _create_active_plan_and_run(_service(session))
    _seed_signing_authority(session)
    foreign = _seed_complete_foreign_authority(session)
    local_scope = EvidenceAdmissionScope(
        organization_id=ORG,
        system_id="system-a",
        run_id=run["id"],
        suite_execution_id=run["suiteExecutions"][0]["id"],
    )
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    resolver = TrustedEvidenceAdmissionResolver(repository)
    cases = (
        (
            "foreign-organization-reverse-hybrid",
            EvidenceAdmissionScope(
                organization_id=foreign.org_id,
                system_id=local_scope.system_id,
                run_id=local_scope.run_id,
                suite_execution_id=local_scope.suite_execution_id,
            ),
            "issuer-protocol-key",
            "signer-protocol-key",
        ),
        (
            "foreign-system",
            EvidenceAdmissionScope(
                organization_id=local_scope.organization_id,
                system_id=foreign.system_id,
                run_id=local_scope.run_id,
                suite_execution_id=local_scope.suite_execution_id,
            ),
            "issuer-protocol-key",
            "signer-protocol-key",
        ),
        (
            "foreign-run",
            EvidenceAdmissionScope(
                organization_id=local_scope.organization_id,
                system_id=local_scope.system_id,
                run_id=foreign.run_id,
                suite_execution_id=local_scope.suite_execution_id,
            ),
            "issuer-protocol-key",
            "signer-protocol-key",
        ),
        (
            "foreign-suite-execution",
            EvidenceAdmissionScope(
                organization_id=local_scope.organization_id,
                system_id=local_scope.system_id,
                run_id=local_scope.run_id,
                suite_execution_id=foreign.suite_execution_id,
            ),
            "issuer-protocol-key",
            "signer-protocol-key",
        ),
        (
            "foreign-system-run-suite-hybrid",
            EvidenceAdmissionScope(
                organization_id=local_scope.organization_id,
                system_id=foreign.system_id,
                run_id=foreign.run_id,
                suite_execution_id=foreign.suite_execution_id,
            ),
            "issuer-protocol-key",
            "signer-protocol-key",
        ),
        (
            "foreign-signer-under-local-scope",
            local_scope,
            foreign.issuer_key,
            foreign.signer_key_id,
        ),
        (
            "local-signer-under-complete-foreign-scope",
            EvidenceAdmissionScope(
                organization_id=foreign.org_id,
                system_id=foreign.system_id,
                run_id=foreign.run_id,
                suite_execution_id=foreign.suite_execution_id,
            ),
            "issuer-protocol-key",
            "signer-protocol-key",
        ),
    )

    for label, scope, issuer_key, signer_key_id in cases:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            resolver.resolve(
                scope=scope,
                issuer_key=issuer_key,
                signer_key_id=signer_key_id,
            )
        assert caught.value.code == "evidence_admission_authority_not_found", label
        assert caught.value.status_code == 404, label
        _assert_no_evidence_graph_in_either_tenant(session)


def test_real_foreign_tenant_catalog_restrictions_are_not_available_under_local_scope(
    repository_fixture,
) -> None:
    """Catches treating another tenant's org-owned suite or target as local authority."""

    session, _factory = repository_fixture
    _plan, run = _create_active_plan_and_run(_service(session))
    foreign = _seed_complete_foreign_authority(session)
    scope = EvidenceAdmissionScope(
        organization_id=ORG,
        system_id="system-a",
        run_id=run["id"],
        suite_execution_id=run["suiteExecutions"][0]["id"],
    )
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)

    assert not repository.restriction_references_exist(
        scope=scope,
        suite_version_ids=(foreign.suite_version_id,),
        target_version_ids=(),
    )
    assert not repository.restriction_references_exist(
        scope=scope,
        suite_version_ids=(),
        target_version_ids=(foreign.target_version_id,),
    )
    assert not repository.restriction_references_exist(
        scope=scope,
        suite_version_ids=(foreign.suite_version_id,),
        target_version_ids=(foreign.target_version_id,),
    )
    _assert_no_evidence_graph_in_either_tenant(session)


def test_verified_passport_persistence_writes_one_atomic_receipt_bound_graph(
    repository_fixture,
) -> None:
    """Catches missing graph nodes, wrong signer FKs, and collapsed result axes."""

    session, _factory = repository_fixture
    _plan, run = _create_active_plan_and_run(_service(session))
    issuer_internal_id, signing_key_internal_id = _seed_signing_authority(session)
    command = _admission_command(session, run)
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)

    result = repository.persist_verified_passport_v2(command)
    repository.force_evidence_admission_constraints()
    session.commit()

    assert result.evidence_run_id == command.evidence_run_id
    assert result.passport_revision_id == command.passport_revision_id
    assert result.verification_receipt_id == command.verification_receipt_id
    assert result.admission_id == command.admission_id
    assert result.nonce_claim_id == command.nonce_claim_id
    assert result.suite_evidence_link_id == command.suite_evidence_link_id
    assert result.technical_status == "succeeded"
    assert result.evidence_result_status == "failed"
    assert result.admission_status == "verified"
    assert result.review_status == "pending"
    assert result.freshness_status == "current"
    assert result.run_technical_status == "succeeded"
    assert result.run_evidence_outcome == "failed"
    assert result.overall_verdict == "insufficient"
    assert result.verdict_version == 0

    for table, identity in (
        (GovernanceEvidenceRun.__table__, command.evidence_run_id),
        (GovernanceEvidencePassportRevision.__table__, command.passport_revision_id),
        (GovernanceEvidenceVerificationReceipt.__table__, command.verification_receipt_id),
        (GovernanceEvidenceAdmission.__table__, command.admission_id),
        (GovernanceEvidenceNonceClaim.__table__, command.nonce_claim_id),
        (GovernanceEvaluationSuiteEvidenceLink.__table__, command.suite_evidence_link_id),
    ):
        assert (
            session.scalar(select(func.count()).select_from(table).where(table.c.id == identity))
            == 1
        )

    evidence = (
        session.execute(
            select(GovernanceEvidenceRun.__table__).where(
                GovernanceEvidenceRun.id == command.evidence_run_id
            )
        )
        .mappings()
        .one()
    )
    revision = (
        session.execute(
            select(GovernanceEvidencePassportRevision.__table__).where(
                GovernanceEvidencePassportRevision.id == command.passport_revision_id
            )
        )
        .mappings()
        .one()
    )
    receipt = (
        session.execute(
            select(GovernanceEvidenceVerificationReceipt.__table__).where(
                GovernanceEvidenceVerificationReceipt.id == command.verification_receipt_id
            )
        )
        .mappings()
        .one()
    )
    assert evidence["artifact_refs_json"] == canonical_json(command.passport.to_dict()["artifacts"])
    assert evidence["evidence_id"] is None
    assert evidence["created_at"] == command.verified_at.isoformat()
    assert revision["previous_revision_hash"] is None
    assert revision["created_at"] == command.verified_at.isoformat()
    assert receipt["issuer_id"] == issuer_internal_id
    assert receipt["issuer_key"] == "issuer-protocol-key"
    assert receipt["signing_key_id"] == signing_key_internal_id
    assert receipt["signer_key_id"] == "signer-protocol-key"
    assert (
        session.scalar(
            select(func.count())
            .select_from(GovernanceEvidenceArtifact.__table__)
            .where(GovernanceEvidenceArtifact.evidence_run_id == command.evidence_run_id)
        )
        == 0
    )


def test_partial_multisuite_admission_does_not_touch_an_unchanged_run_timestamp(
    repository_fixture,
) -> None:
    """Catches issuing a forbidden no-op run UPDATE solely to advance updated_at."""

    session, _factory = repository_fixture
    _plan, run = _create_active_plan_and_run(_service(session), suites=2)
    _seed_signing_authority(session)
    command = _admission_command(session, run, execution_index=0)
    before = (
        session.execute(
            select(GovernanceEvaluationRun.__table__).where(GovernanceEvaluationRun.id == run["id"])
        )
        .mappings()
        .one()
    )
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)

    result = repository.persist_verified_passport_v2(command)
    repository.force_evidence_admission_constraints()
    session.commit()

    after = (
        session.execute(
            select(GovernanceEvaluationRun.__table__).where(GovernanceEvaluationRun.id == run["id"])
        )
        .mappings()
        .one()
    )
    assert result.run_technical_status == "awaiting_evidence"
    assert result.run_evidence_outcome == "pending"
    assert after["technical_status"] == before["technical_status"]
    assert after["evidence_outcome"] == before["evidence_outcome"]
    assert after["started_at"] == before["started_at"]
    assert after["completed_at"] == before["completed_at"]
    assert after["updated_at"] == before["updated_at"]


def test_replaying_an_admitted_passport_is_an_occupied_conflict_not_idempotency(
    repository_fixture,
) -> None:
    """Catches treating a unique evidence graph conflict as a successful replay."""

    session, _factory = repository_fixture
    _plan, run = _create_active_plan_and_run(_service(session))
    _seed_signing_authority(session)
    command = _admission_command(session, run)
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    repository.persist_verified_passport_v2(command)
    repository.force_evidence_admission_constraints()
    session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        repository.persist_verified_passport_v2(command)
    session.rollback()

    assert caught.value.code == "evidence_admission_occupied"
    assert caught.value.status_code == 409
    assert (
        session.scalar(
            select(func.count())
            .select_from(GovernanceEvidenceAdmission.__table__)
            .where(GovernanceEvidenceAdmission.org_id == ORG)
        )
        == 1
    )


def test_stale_suite_cas_rolls_back_every_inserted_graph_node(repository_fixture) -> None:
    """Catches leaving orphan evidence when the suite projection changes concurrently."""

    session, _factory = repository_fixture
    _plan, run = _create_active_plan_and_run(_service(session))
    _seed_signing_authority(session)
    command = _admission_command(session, run)
    session.execute(
        update(GovernanceEvaluationRunSuiteExecution.__table__)
        .where(GovernanceEvaluationRunSuiteExecution.id == command.scope.suite_execution_id)
        .values(technical_status="queued")
    )
    session.commit()
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)

    with pytest.raises(EvaluationWorkbenchError) as caught:
        repository.persist_verified_passport_v2(command)
    session.rollback()

    assert caught.value.code == "suite_projection_conflict"
    for table in (
        GovernanceEvidenceRun.__table__,
        GovernanceEvidencePassportRevision.__table__,
        GovernanceEvidenceVerificationReceipt.__table__,
        GovernanceEvidenceAdmission.__table__,
        GovernanceEvidenceNonceClaim.__table__,
        GovernanceEvaluationSuiteEvidenceLink.__table__,
    ):
        assert session.scalar(select(func.count()).select_from(table)) == 0


def test_cancelled_evaluator_keeps_pending_evidence_separate_from_technical_status(
    repository_fixture,
) -> None:
    """Catches converting a cancelled evaluator into false passing or failed evidence."""

    session, _factory = repository_fixture
    _plan, run = _create_active_plan_and_run(_service(session))
    _seed_signing_authority(session)
    command = _admission_command(
        session,
        run,
        technical_status="cancelled",
        evidence_result_status="pending",
    )
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)

    result = repository.persist_verified_passport_v2(command)
    repository.force_evidence_admission_constraints()
    session.commit()

    suite = (
        session.execute(
            select(GovernanceEvaluationRunSuiteExecution.__table__).where(
                GovernanceEvaluationRunSuiteExecution.id == command.scope.suite_execution_id
            )
        )
        .mappings()
        .one()
    )
    assert result.technical_status == "cancelled"
    assert result.evidence_result_status == "pending"
    assert result.run_technical_status == "cancelled"
    assert result.run_evidence_outcome == "pending"
    assert suite["technical_status"] == "cancelled"
    assert suite["evidence_result_status"] == "pending"
    assert suite["admission_status"] == "verified"
    assert suite["review_status"] == "pending"


def test_mixed_suite_axes_preserve_failed_execution_and_failed_model_evidence(
    repository_fixture,
    monkeypatch,
) -> None:
    """Catches collapsing evaluator execution failure into the model evidence axis."""

    session, _factory = repository_fixture

    def classify_synthetic_linked_evidence(
        **values: object,
    ) -> EvidenceFreshnessClassification:
        as_of = values["as_of"]
        recorded_status = values["recorded_freshness_status"]
        assert isinstance(as_of, datetime)
        assert recorded_status == "current"
        return EvidenceFreshnessClassification(
            classification_status="ok",
            freshness_contract_version="1.0.0",
            recorded_freshness_status=recorded_status,
            effective_freshness_status="current",
            evaluated_at=as_of,
            effective_at=as_of - timedelta(seconds=1),
            expiring_at=as_of + timedelta(days=1),
            reason_codes=(),
            decision_eligible=False,
        )

    monkeypatch.setattr(
        SqlAlchemyEvaluationWorkbenchRepository,
        "_acquire_operational_freshness_read_lock",
        lambda self, *, organization_id: None,
    )
    monkeypatch.setattr(
        SqlAlchemyEvaluationWorkbenchRepository,
        "_classify_evidence_freshness",
        lambda self, **values: classify_synthetic_linked_evidence(**values),
    )
    _plan, run = _create_active_plan_and_run(_service(session), suites=2)
    _seed_signing_authority(session)
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    model_failure = _admission_command(session, run, execution_index=0)
    repository.persist_verified_passport_v2(model_failure)
    repository.force_evidence_admission_constraints()
    session.commit()

    evaluator_failure = _admission_command(
        session,
        run,
        execution_index=1,
        technical_status="failed",
        evidence_result_status="error",
        run_technical_status="failed",
        run_evidence_outcome="failed",
    )
    result = repository.persist_verified_passport_v2(evaluator_failure)
    repository.force_evidence_admission_constraints()
    session.commit()

    stored_run = (
        session.execute(
            select(GovernanceEvaluationRun.__table__).where(GovernanceEvaluationRun.id == run["id"])
        )
        .mappings()
        .one()
    )
    suites = (
        session.execute(
            select(GovernanceEvaluationRunSuiteExecution.__table__)
            .where(GovernanceEvaluationRunSuiteExecution.run_id == run["id"])
            .order_by(GovernanceEvaluationRunSuiteExecution.ordinal)
        )
        .mappings()
        .all()
    )
    assert result.run_technical_status == "failed"
    assert result.run_evidence_outcome == "failed"
    assert stored_run["technical_status"] == "failed"
    assert stored_run["evidence_outcome"] == "failed"
    assert [(item["technical_status"], item["evidence_result_status"]) for item in suites] == [
        ("succeeded", "failed"),
        ("failed", "error"),
    ]


def test_unchanged_run_path_still_rejects_a_stale_locked_snapshot(
    repository_fixture,
) -> None:
    """Catches skipping run CAS verification when aggregate projections do not change."""

    session, _factory = repository_fixture
    _plan, run = _create_active_plan_and_run(_service(session), suites=2)
    _seed_signing_authority(session)
    command = _admission_command(session, run, execution_index=0)
    stale_update = (command.verified_at + timedelta(microseconds=1)).isoformat()
    session.execute(
        update(GovernanceEvaluationRun.__table__)
        .where(GovernanceEvaluationRun.id == run["id"])
        .values(updated_at=stale_update)
    )
    session.commit()
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)

    with pytest.raises(EvaluationWorkbenchError) as caught:
        repository.persist_verified_passport_v2(command)
    session.rollback()

    assert caught.value.code == "run_projection_conflict"
    assert (
        session.scalar(
            select(func.count())
            .select_from(GovernanceEvidenceRun.__table__)
            .where(GovernanceEvidenceRun.org_id == ORG)
        )
        == 0
    )
