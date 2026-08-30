"""Repository integration tests for verified Passport V2 submit/link boundaries."""

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
    PersistVerifiedPassportV2SubmissionCommand,
)
from src.application.ports.evidence_link import (
    EvidenceLinkScope,
    PersistVerifiedEvidenceLinkCommand,
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
        "verified evidence link requires an exact current authority chain",
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
) -> PersistVerifiedPassportV2SubmissionCommand:
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

    return PersistVerifiedPassportV2SubmissionCommand(
        scope=scope,
        actor_id=USER,
        evidence_run_id=str(uuid.uuid4()),
        passport_revision_id=str(uuid.uuid4()),
        verification_receipt_id=str(uuid.uuid4()),
        admission_id=str(uuid.uuid4()),
        nonce_claim_id=str(uuid.uuid4()),
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


def test_verified_submission_and_link_are_independent_authoritative_mutations(
    repository_fixture,
) -> None:
    """Catches hidden projection writes during submit and caller-shaped link authority."""

    session, _factory = repository_fixture
    _plan, run = _create_active_plan_and_run(_service(session))
    _seed_signing_authority(session)
    submission = _admission_command(session, run)
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)

    submitted = repository.persist_verified_passport_v2_submission(submission)

    suite_before = (
        session.execute(
            select(GovernanceEvaluationRunSuiteExecution.__table__).where(
                GovernanceEvaluationRunSuiteExecution.id == submission.scope.suite_execution_id
            )
        )
        .mappings()
        .one()
    )
    assert submitted.admission_id == submission.admission_id
    assert suite_before["admission_status"] == "pending"
    assert suite_before["evidence_run_id"] is None
    assert suite_before["passport_revision_id"] is None
    assert suite_before["linked_by"] is None
    assert session.scalar(
        select(func.count()).select_from(GovernanceEvaluationSuiteEvidenceLink.__table__)
    ) == 0

    link_scope = EvidenceLinkScope(
        organization_id=submission.scope.organization_id,
        system_id=submission.scope.system_id,
        run_id=submission.scope.run_id,
        suite_execution_id=submission.scope.suite_execution_id,
        admission_id=submission.admission_id,
        passport_revision_id=submission.passport_revision_id,
    )
    authority = repository.load_verified_evidence_link_authority_for_update(scope=link_scope)
    assert authority is not None
    assert authority.evidence_run_id == submission.evidence_run_id
    assert authority.verification_receipt_id == submission.verification_receipt_id
    assert authority.nonce_claim_id == submission.nonce_claim_id
    assert authority.passport_content_hash == submission.passport_content_hash
    assert authority.passport_snapshot == submission.passport
    assert authority.evaluator_registration_id == submission.evaluator_registration_id
    assert (
        authority.evaluator_registration_binding_hash
        == submission.evaluator_registration_binding_hash
    )

    linked_at = submission.verified_at + timedelta(seconds=1)
    linked = repository.persist_verified_evidence_link(
        PersistVerifiedEvidenceLinkCommand(
            scope=link_scope,
            actor_id="linker-a",
            suite_evidence_link_id=str(uuid.uuid4()),
            authority=authority,
            technical_status=submission.technical_status,
            evidence_result_status=submission.evidence_result_status,
            result_summary=submission.result_summary,
            limitations=submission.limitations,
            suite_started_at=submission.captured_at,
            suite_completed_at=linked_at,
            run_technical_status=submission.technical_status,
            run_evidence_outcome=submission.evidence_result_status,
            run_started_at=submission.captured_at,
            run_completed_at=linked_at,
            linked_at=linked_at,
        )
    )
    repository.force_evidence_admission_constraints()

    assert linked.admission_id == submission.admission_id
    assert linked.suite_evidence_link_id
    assert linked.linked_by == "linker-a"
    assert linked.linked_at == linked_at
    suite_after = (
        session.execute(
            select(GovernanceEvaluationRunSuiteExecution.__table__).where(
                GovernanceEvaluationRunSuiteExecution.id == submission.scope.suite_execution_id
            )
        )
        .mappings()
        .one()
    )
    assert suite_after["admission_status"] == "verified"
    assert suite_after["evidence_run_id"] == submission.evidence_run_id
    assert suite_after["passport_revision_id"] == submission.passport_revision_id
    assert suite_after["linked_by"] == "linker-a"
    assert session.scalar(
        select(func.count()).select_from(GovernanceEvaluationSuiteEvidenceLink.__table__)
    ) == 1
