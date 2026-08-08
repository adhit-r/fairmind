"""Native PostgreSQL 14 adversarial contracts for verified Passport V2 admission.

The suite provisions one isolated schema from the production migration chain
and gives every test its own UUID-scoped organization graph.  It intentionally
uses separate database sessions for concurrency and trust-revocation races.
Nothing here relies on ORM-created DDL, fake signature verification, or
process-local clocks for admission decisions.
"""

from __future__ import annotations

import base64
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier, Event
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import sessionmaker

from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.ports.evidence_admission import EvidenceAdmissionScope
from src.application.services.evaluation_workbench_service import (
    EvaluationWorkbenchService,
)
from src.application.services.evidence_authenticity_service import (
    EvidenceAuthenticityService,
)
from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256
from src.domain.assurance.evidence_passport_v2 import (
    evidence_passport_v2_content_hash,
    evidence_passport_v2_signature_bytes,
    expected_execution_binding_v2,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchRepository,
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)
from src.infrastructure.security import Ed25519EvidenceVerifier
from tests.evaluation_result_contract_cases import TERMINAL_RESULT_AXIS_CASES

POSTGRES_URL = os.getenv("FAIRMIND_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14",
)

MIGRATIONS = Path(__file__).parents[1] / "migrations"
MIGRATION_CHAIN = (
    "001_initial_schema.sql",
    "007_org_rbac_schema_CORRECTED.sql",
    "008_governance_canonical.sql",
    "011_governance_assurance.sql",
    "012_evaluation_runs.sql",
    "013_evaluation_assurance_contract_v2.sql",
    "013a_evaluation_binding_integrity.sql",
    "013b_evaluation_assurance_trust_integrity.sql",
    "013c_evidence_verification_receipt.sql",
)
ADMISSION_OPERATION = "evaluation-v2.evidence.verified-admit"
ADMISSION_SUCCESS_ACTION = "evaluation_v2.evidence.verified_admitted"
MIGRATION_OCCUPANCY_CONSTRAINTS = (
    ("governance_evidence_runs", "uq_governance_evidence_run"),
    (
        "governance_evidence_passport_revisions",
        "uq_evidence_passport_number",
    ),
    (
        "governance_evidence_passport_revisions",
        "uq_evidence_run_passport_number",
    ),
    (
        "governance_evidence_passport_revisions",
        "uq_evidence_run_canonical_hash",
    ),
    (
        "governance_evidence_admissions",
        "uq_governance_evidence_admission_policy",
    ),
    (
        "governance_evidence_verification_receipts",
        "uq_governance_evidence_verification_receipt_admission",
    ),
    (
        "governance_evidence_nonce_claims",
        "uq_governance_evidence_nonce_claim_admission",
    ),
    (
        "governance_evidence_nonce_claims",
        "uq_governance_evidence_nonce_claim_replay",
    ),
    (
        "governance_evaluation_suite_evidence_links",
        "uq_governance_evaluation_suite_evidence_link_suite_execution",
    ),
    (
        "governance_evaluation_suite_evidence_links",
        "uq_governance_evaluation_suite_evidence_link_admission",
    ),
    (
        "governance_evaluation_suite_evidence_links",
        "uq_governance_evaluation_suite_evidence_link_nonce_claim",
    ),
)


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise AssertionError("test fixture timestamp lost its timezone")
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


@dataclass(frozen=True)
class SigningMaterial:
    issuer_row_id: str
    issuer_key: str
    signing_key_row_id: str
    key_id: str
    private_key: Ed25519PrivateKey
    public_jwk: dict[str, str]


@dataclass(frozen=True)
class AdmissionScenario:
    org_id: str
    actor_id: str
    workspace_id: str
    system_id: str
    trust_policy_id: str
    target_version_id: str
    plan_id: str
    suite_version_ids: tuple[str, ...]
    run: dict[str, Any]
    signing: SigningMaterial

    @property
    def run_id(self) -> str:
        return str(self.run["id"])

    @property
    def suite_executions(self) -> list[dict[str, Any]]:
        return list(self.run["suiteExecutions"])


@pytest.fixture(scope="module")
def postgres_session_factory():
    """Create one disposable schema using only the release migration chain."""
    assert POSTGRES_URL is not None
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_verified_admission_{uuid.uuid4().hex}"
    migration_connection = psycopg2.connect(POSTGRES_URL)
    try:
        if migration_connection.server_version // 10000 != 14:
            pytest.fail(
                "verified admission native suite requires PostgreSQL 14; "
                f"server_version={migration_connection.server_version}"
            )
        with migration_connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name)))
            cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema_name)))
            for migration_name in MIGRATION_CHAIN:
                if migration_name in {
                    "013a_evaluation_binding_integrity.sql",
                    "013b_evaluation_assurance_trust_integrity.sql",
                    "013c_evidence_verification_receipt.sql",
                }:
                    cursor.execute(
                        "SELECT pg_catalog.set_config" "('fairmind.migration_schema', %s, false)",
                        (schema_name,),
                    )
                cursor.execute((MIGRATIONS / migration_name).read_text(encoding="utf-8"))
        migration_connection.commit()
    finally:
        migration_connection.close()

    engine = create_engine(
        POSTGRES_URL,
        connect_args={"options": f"-csearch_path={schema_name}"},
        pool_pre_ping=True,
        pool_size=32,
        max_overflow=0,
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        engine.dispose()
        cleanup_connection = psycopg2.connect(POSTGRES_URL)
        cleanup_connection.autocommit = True
        try:
            with cleanup_connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema_name))
                )
        finally:
            cleanup_connection.close()


def _workbench_service(session) -> EvaluationWorkbenchService:
    return EvaluationWorkbenchService(SqlAlchemyEvaluationWorkbenchUnitOfWork(session))


@pytest.mark.parametrize(
    ("technical_status", "evidence_result_status", "expected_valid"),
    TERMINAL_RESULT_AXIS_CASES,
)
def test_postgres_terminal_result_axis_matrix_is_the_release_authority(
    postgres_session_factory,
    technical_status: str,
    evidence_result_status: str,
    expected_valid: bool,
) -> None:
    """Catches PostgreSQL result coherence drifting from Passport/application rules."""

    session = postgres_session_factory()
    try:
        observed = session.scalar(
            text(
                "SELECT fairmind_suite_result_coherent"
                "(:technical_status, :evidence_result_status)"
            ),
            {
                "technical_status": technical_status,
                "evidence_result_status": evidence_result_status,
            },
        )
    finally:
        session.close()
    assert observed is expected_valid


def _target_payload(target_key: str) -> dict[str, Any]:
    return {
        "targetKey": target_key,
        "targetKind": "agent",
        "version": "1.0.0",
        "systemVersion": "2026.08",
        "subjectKind": "agent",
        "subjectId": target_key,
        "subjectVersion": "sha-1",
        "subjectDigest": "b" * 64,
        "deploymentId": "deployment-postgres-001",
        "connectorBindingId": "connector-postgres-001",
        "manifest": {
            "schemaVersion": "2.0.0",
            "inputs": {"scenario_set": {"kind": "content_digest", "sha256": "c" * 64}},
        },
    }


def _suite_payload(name: str) -> dict[str, Any]:
    return {
        "namespace": "fairmind",
        "name": name,
        "version": "1.0.0",
        "supportedTargetKinds": ["agent"],
        "supportedSubjectKinds": ["agent"],
        "lifecyclePhases": ["pre_deploy"],
        "executionDepths": ["deep"],
        "deliveryModes": ["external_provider"],
        "workerType": "external_provider",
        "adapterName": "inspect",
        "adapterVersion": "0.3.0",
        "configurationSchema": {
            "type": "object",
            "required": ["threshold"],
            "properties": {"threshold": {"type": "number", "minimum": 0, "maximum": 1}},
            "additionalProperties": False,
        },
        "configurationDefaults": {"threshold": 0.5},
        "requiredInputRoles": ["scenario_set"],
        "budgets": {"maxCases": 200},
        "resultContractVersion": "1.0.0",
    }


def _insert_identity_and_scope(
    session,
    *,
    org_id: str,
    actor_id: str,
    workspace_id: str,
    system_id: str,
    trust_policy_id: str,
) -> None:
    now = _iso(datetime.now(timezone.utc))
    session.execute(
        text(
            "INSERT INTO users "
            "(id, email, username, password_hash, role, permissions) "
            "VALUES (:id, :email, :username, :password_hash, 'admin', '[]'::jsonb)"
        ),
        {
            "id": actor_id,
            "email": f"{actor_id}@example.test",
            "username": actor_id,
            "password_hash": "test-only-invalid-password-hash",
        },
    )
    session.execute(
        text(
            "INSERT INTO organizations (id, name, slug, owner_id) "
            "VALUES (:id, :name, :slug, :owner_id)"
        ),
        {
            "id": org_id,
            "name": f"Verified admission {org_id}",
            "slug": org_id,
            "owner_id": actor_id,
        },
    )
    session.execute(
        text(
            "INSERT INTO org_members (id, org_id, user_id, role, status) "
            "VALUES (:id, :org_id, :user_id, 'admin', 'active')"
        ),
        {"id": str(uuid.uuid4()), "org_id": org_id, "user_id": actor_id},
    )
    session.execute(
        text(
            "INSERT INTO governance_workspaces "
            "(id, org_id, name, created_at, updated_at) "
            "VALUES (:id, :org_id, :name, :created_at, :updated_at)"
        ),
        {
            "id": workspace_id,
            "org_id": org_id,
            "name": workspace_id,
            "created_at": now,
            "updated_at": now,
        },
    )
    session.execute(
        text(
            "INSERT INTO governance_ai_systems "
            "(id, workspace_id, org_id, name, created_at, updated_at) "
            "VALUES (:id, :workspace_id, :org_id, :name, :created_at, :updated_at)"
        ),
        {
            "id": system_id,
            "workspace_id": workspace_id,
            "org_id": org_id,
            "name": system_id,
            "created_at": now,
            "updated_at": now,
        },
    )
    policy = {
        "schemaVersion": "2.0.0",
        "purpose": "verified-admission-postgres-contract",
    }
    session.execute(
        text(
            "INSERT INTO governance_evidence_trust_policy_versions "
            "(id, org_id, version, policy_json, policy_hash, "
            "maximum_evidence_age_seconds, unsigned_import_policy, status, "
            "created_by, created_at) "
            "VALUES (:id, :org_id, '1.0.0', :policy_json, :policy_hash, "
            "86400, 'manual_review', 'active', :created_by, :created_at)"
        ),
        {
            "id": trust_policy_id,
            "org_id": org_id,
            "policy_json": canonical_json(policy),
            "policy_hash": canonical_sha256(policy),
            "created_by": actor_id,
            "created_at": now,
        },
    )
    session.commit()


def _insert_signing_authority(
    session,
    *,
    scenario_ids: tuple[str, str],
    org_id: str,
    actor_id: str,
    reference_time: datetime,
    private_key: Ed25519PrivateKey | None = None,
    issuer_key: str | None = None,
    key_id: str | None = None,
) -> SigningMaterial:
    issuer_row_id, signing_key_row_id = scenario_ids
    private_key = private_key or Ed25519PrivateKey.generate()
    issuer_key = issuer_key or str(uuid.uuid4())
    key_id = key_id or str(uuid.uuid4())
    public_raw = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    public_jwk = {"crv": "Ed25519", "kty": "OKP", "x": _b64url(public_raw)}
    created_at = _iso(reference_time - timedelta(seconds=1))
    session.execute(
        text(
            "INSERT INTO governance_evidence_issuers "
            "(id, org_id, issuer_key, name, issuer_type, "
            "source_restrictions_json, suite_restrictions_json, "
            "target_restrictions_json, status, created_by, created_at, updated_at) "
            "VALUES (:id, :org_id, :issuer_key, :name, 'external_provider', "
            "'[]', '[]', '[]', 'active', :created_by, :created_at, :created_at)"
        ),
        {
            "id": issuer_row_id,
            "org_id": org_id,
            "issuer_key": issuer_key,
            "name": issuer_key,
            "created_by": actor_id,
            "created_at": created_at,
        },
    )
    session.execute(
        text(
            "INSERT INTO governance_evidence_signing_keys "
            "(id, org_id, issuer_id, key_id, algorithm, public_jwk_json, "
            "valid_from, valid_until, created_by, created_at) "
            "VALUES (:id, :org_id, :issuer_id, :key_id, 'Ed25519', :jwk, "
            ":valid_from, :valid_until, :created_by, :created_at)"
        ),
        {
            "id": signing_key_row_id,
            "org_id": org_id,
            "issuer_id": issuer_row_id,
            "key_id": key_id,
            "jwk": canonical_json(public_jwk),
            "valid_from": _iso(reference_time - timedelta(days=1)),
            "valid_until": _iso(reference_time + timedelta(days=2)),
            "created_by": actor_id,
            "created_at": created_at,
        },
    )
    session.commit()
    return SigningMaterial(
        issuer_row_id=issuer_row_id,
        issuer_key=issuer_key,
        signing_key_row_id=signing_key_row_id,
        key_id=key_id,
        private_key=private_key,
        public_jwk=public_jwk,
    )


def _seed_scenario(factory: sessionmaker, *, suite_count: int = 2) -> AdmissionScenario:
    org_id = str(uuid.uuid4())
    actor_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())
    system_id = str(uuid.uuid4())
    trust_policy_id = str(uuid.uuid4())
    target_key = "postgres-agent"
    session = factory()
    try:
        _insert_identity_and_scope(
            session,
            org_id=org_id,
            actor_id=actor_id,
            workspace_id=workspace_id,
            system_id=system_id,
            trust_policy_id=trust_policy_id,
        )
        service = _workbench_service(session)
        target = service.create_target_version(
            org_id=org_id,
            system_id=system_id,
            actor_id=actor_id,
            idempotency_key=f"target-{uuid.uuid4()}",
            payload=_target_payload(target_key),
        ).body
        suite_ids: list[str] = []
        for ordinal in range(suite_count):
            suite = service.create_suite_version(
                org_id=org_id,
                actor_id=actor_id,
                idempotency_key=f"suite-{uuid.uuid4()}",
                payload=_suite_payload(f"postgres-agent-safety-{ordinal}"),
            ).body
            service.activate_suite_version(
                org_id=org_id,
                suite_version_id=str(suite["id"]),
                actor_id=actor_id,
                idempotency_key=f"activate-suite-{uuid.uuid4()}",
            )
            suite_ids.append(str(suite["id"]))
        plan = service.create_plan(
            org_id=org_id,
            system_id=system_id,
            actor_id=actor_id,
            idempotency_key=f"plan-{uuid.uuid4()}",
            payload={
                "contractVersion": "2.0.0",
                "name": "Verified evidence admission PG14",
                "targetVersionId": str(target["id"]),
                "lifecyclePhases": ["pre_deploy"],
                "executionDepth": "deep",
                "enforcementMode": "human_approval",
                "deliveryMode": "external_provider",
                "trustPolicyVersionId": trust_policy_id,
                "suites": [{"suiteVersionId": suite_id} for suite_id in suite_ids],
            },
        ).body
        service.activate_plan(
            org_id=org_id,
            system_id=system_id,
            plan_id=str(plan["id"]),
            actor_id=actor_id,
            idempotency_key=f"activate-plan-{uuid.uuid4()}",
        )
        run = service.create_run(
            org_id=org_id,
            system_id=system_id,
            plan_id=str(plan["id"]),
            actor_id=actor_id,
            idempotency_key=f"run-{uuid.uuid4()}",
            payload={"trigger": "manual", "lifecyclePhase": "pre_deploy"},
        ).body
        requested_at = _parse_timestamp(str(run["envelope"]["requestedAt"]))
        signing = _insert_signing_authority(
            session,
            scenario_ids=(str(uuid.uuid4()), str(uuid.uuid4())),
            org_id=org_id,
            actor_id=actor_id,
            reference_time=requested_at,
        )
        return AdmissionScenario(
            org_id=org_id,
            actor_id=actor_id,
            workspace_id=workspace_id,
            system_id=system_id,
            trust_policy_id=trust_policy_id,
            target_version_id=str(target["id"]),
            plan_id=str(plan["id"]),
            suite_version_ids=tuple(suite_ids),
            run=dict(run),
            signing=signing,
        )
    finally:
        session.close()


def _signed_passport(
    scenario: AdmissionScenario,
    *,
    suite_ordinal: int = 0,
    passport_id: str | None = None,
    passport_revision: int = 1,
    signing: SigningMaterial | None = None,
    result: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bytes]:
    signing = signing or scenario.signing
    execution = scenario.suite_executions[suite_ordinal]
    requested_at_text = str(scenario.run["envelope"]["requestedAt"])
    requested_at = _parse_timestamp(requested_at_text)
    # Keep the exact requestedAt precision. Truncating to seconds can make a
    # capture appear earlier than a microsecond-bearing server request.
    captured_at = requested_at
    signed_at = requested_at
    payload: dict[str, Any] = {
        "schemaVersion": "2.0.0",
        "passportId": passport_id or str(uuid.uuid4()),
        "passportRevision": passport_revision,
        "claimBoundary": "supporting_evidence_only",
        "organizationId": scenario.org_id,
        "workspaceId": scenario.workspace_id,
        "systemId": scenario.system_id,
        "executionBinding": expected_execution_binding_v2(
            scenario.run["envelope"], str(execution["id"])
        ),
        "evaluator": {
            "issuerId": signing.issuer_key,
            "evaluatorId": "inspect-postgres-evaluator",
            "sourceType": "external_provider",
            "adapterName": "inspect",
            "adapterVersion": "0.3.0",
            "resultContractVersion": "1.0.0",
        },
        "result": result
        or {
            "technicalStatus": "succeeded",
            "evidenceResultStatus": "failed",
            "summary": {"caseCount": 200, "attackSuccessRate": 0.17},
        },
        "artifacts": [
            {
                "artifactId": str(uuid.uuid4()),
                "role": "report",
                "sha256": "f" * 64,
                "mediaType": "application/json",
                "sizeBytes": 4096,
            }
        ],
        "limitations": ["PostgreSQL adversarial fixture; supporting evidence only."],
        "capturedAt": _iso(captured_at),
        "expiresAt": _iso(captured_at + timedelta(hours=12)),
        "signature": {
            "algorithm": "Ed25519",
            "issuerId": signing.issuer_key,
            "keyId": signing.key_id,
            "signedAt": _iso(signed_at),
            "value": _b64url(bytes(64)),
        },
    }
    payload["contentHash"] = evidence_passport_v2_content_hash(payload)
    payload["signature"]["value"] = _b64url(
        signing.private_key.sign(evidence_passport_v2_signature_bytes(payload))
    )
    raw = canonical_json(payload).encode("utf-8")
    return payload, raw


def _resign(payload: dict[str, Any], signing: SigningMaterial) -> bytes:
    payload["contentHash"] = evidence_passport_v2_content_hash(payload)
    payload["signature"]["value"] = _b64url(
        signing.private_key.sign(evidence_passport_v2_signature_bytes(payload))
    )
    return canonical_json(payload).encode("utf-8")


def _scalar(factory: sessionmaker, statement: str, **parameters: object) -> Any:
    session = factory()
    try:
        return session.scalar(text(statement), parameters)
    finally:
        session.close()


def _graph_counts(factory: sessionmaker, scenario: AdmissionScenario) -> dict[str, int]:
    tables = {
        "evidence_runs": "governance_evidence_runs",
        "revisions": "governance_evidence_passport_revisions",
        "receipts": "governance_evidence_verification_receipts",
        "admissions": "governance_evidence_admissions",
        "nonce_claims": "governance_evidence_nonce_claims",
        "suite_links": "governance_evaluation_suite_evidence_links",
    }
    return {
        label: int(
            _scalar(
                factory,
                f"SELECT count(*) FROM {table} WHERE org_id = :org_id",
                org_id=scenario.org_id,
            )
        )
        for label, table in tables.items()
    }


def _operation_idempotency_count(factory: sessionmaker, scenario: AdmissionScenario) -> int:
    return int(
        _scalar(
            factory,
            "SELECT count(*) FROM governance_idempotency_records "
            "WHERE org_id = :org_id AND operation = :operation",
            org_id=scenario.org_id,
            operation=ADMISSION_OPERATION,
        )
    )


def _admission_audit_count(factory: sessionmaker, scenario: AdmissionScenario) -> int:
    return int(
        _scalar(
            factory,
            "SELECT count(*) FROM governance_evaluation_audit_events "
            "WHERE org_id = :org_id AND ("
            "details_json::jsonb #>> "
            "'{_fairmindEvaluationSuccessBinding,operation}' = :operation "
            "OR details_json::jsonb ->> 'operation' = :operation)",
            org_id=scenario.org_id,
            operation=ADMISSION_OPERATION,
        )
    )


def _successful_admission_audit_count(
    factory: sessionmaker,
    scenario: AdmissionScenario,
) -> int:
    return int(
        _scalar(
            factory,
            "SELECT count(*) FROM governance_evaluation_audit_events "
            "WHERE org_id = :org_id AND action = :action AND outcome = 'success'",
            org_id=scenario.org_id,
            action=ADMISSION_SUCCESS_ACTION,
        )
    )


def _verified_service(
    session,
    *,
    verifier: object | None = None,
    repository: SqlAlchemyEvaluationWorkbenchRepository | None = None,
):
    from src.application.services.verified_evidence_admission_service import (
        VerifiedEvidenceAdmissionService,
    )
    from src.application.services.evaluator_registry import (
        EvaluatorRegistration,
        StaticEvaluatorRegistry,
    )

    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(
        session,
        repository=repository,
    )
    return VerifiedEvidenceAdmissionService(
        unit_of_work,
        EvidenceAuthenticityService(verifier or Ed25519EvidenceVerifier()),
        StaticEvaluatorRegistry(
            catalog_version="2026.08.1",
            registrations=(
                EvaluatorRegistration(
                    evaluator_id="inspect-postgres-evaluator",
                    adapter_name="inspect",
                    adapter_version="0.3.0",
                    result_contract_version="1.0.0",
                    source_types=frozenset({"external_provider"}),
                ),
            ),
        ),
    )


def _scope(
    scenario: AdmissionScenario,
    *,
    suite_ordinal: int = 0,
    organization_id: str | None = None,
    system_id: str | None = None,
    run_id: str | None = None,
    suite_execution_id: str | None = None,
) -> EvidenceAdmissionScope:
    return EvidenceAdmissionScope(
        organization_id=organization_id or scenario.org_id,
        system_id=system_id or scenario.system_id,
        run_id=run_id or scenario.run_id,
        suite_execution_id=suite_execution_id
        or str(scenario.suite_executions[suite_ordinal]["id"]),
    )


def _admit(
    session,
    scenario: AdmissionScenario,
    *,
    raw: bytes,
    idempotency_key: str,
    scope: EvidenceAdmissionScope | None = None,
    actor_id: str | None = None,
    verifier: object | None = None,
    repository: SqlAlchemyEvaluationWorkbenchRepository | None = None,
):
    return _verified_service(
        session,
        verifier=verifier,
        repository=repository,
    ).admit_verified_passport_v2(
        scope=scope or _scope(scenario),
        actor_id=actor_id or scenario.actor_id,
        idempotency_key=idempotency_key,
        raw_passport=raw,
    )


def _insert_additional_signing_key(
    session,
    *,
    scenario: AdmissionScenario,
    private_key: Ed25519PrivateKey | None = None,
) -> SigningMaterial:
    private_key = private_key or Ed25519PrivateKey.generate()
    signing_key_row_id = str(uuid.uuid4())
    key_id = str(uuid.uuid4())
    requested_at = _parse_timestamp(str(scenario.run["envelope"]["requestedAt"]))
    public_raw = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    public_jwk = {"crv": "Ed25519", "kty": "OKP", "x": _b64url(public_raw)}
    session.execute(
        text(
            "INSERT INTO governance_evidence_signing_keys "
            "(id, org_id, issuer_id, key_id, algorithm, public_jwk_json, "
            "valid_from, valid_until, created_by, created_at) "
            "VALUES (:id, :org_id, :issuer_id, :key_id, 'Ed25519', :jwk, "
            ":valid_from, :valid_until, :created_by, :created_at)"
        ),
        {
            "id": signing_key_row_id,
            "org_id": scenario.org_id,
            "issuer_id": scenario.signing.issuer_row_id,
            "key_id": key_id,
            "jwk": canonical_json(public_jwk),
            "valid_from": _iso(requested_at - timedelta(days=1)),
            "valid_until": _iso(requested_at + timedelta(days=2)),
            "created_by": scenario.actor_id,
            "created_at": _iso(requested_at - timedelta(seconds=1)),
        },
    )
    session.commit()
    return SigningMaterial(
        issuer_row_id=scenario.signing.issuer_row_id,
        issuer_key=scenario.signing.issuer_key,
        signing_key_row_id=signing_key_row_id,
        key_id=key_id,
        private_key=private_key,
        public_jwk=public_jwk,
    )


def _assert_empty_graph(factory: sessionmaker, scenario: AdmissionScenario) -> None:
    assert _graph_counts(factory, scenario) == {
        "evidence_runs": 0,
        "revisions": 0,
        "receipts": 0,
        "admissions": 0,
        "nonce_claims": 0,
        "suite_links": 0,
    }


def _assert_one_graph(factory: sessionmaker, scenario: AdmissionScenario) -> None:
    assert _graph_counts(factory, scenario) == {
        "evidence_runs": 1,
        "revisions": 1,
        "receipts": 1,
        "admissions": 1,
        "nonce_claims": 1,
        "suite_links": 1,
    }


def test_fixture_uses_uuid_identity_and_preserves_requested_at_precision(
    postgres_session_factory,
) -> None:
    """A timestamp truncation or synthetic identity fixture invalidates later race tests."""
    scenario = _seed_scenario(postgres_session_factory)
    uuid.UUID(scenario.org_id)
    uuid.UUID(scenario.actor_id)
    payload, _raw = _signed_passport(scenario)

    assert payload["capturedAt"] == scenario.run["envelope"]["requestedAt"]
    assert _parse_timestamp(str(payload["capturedAt"])) >= _parse_timestamp(
        str(scenario.run["envelope"]["requestedAt"])
    )
    assert _graph_counts(postgres_session_factory, scenario) == {
        "evidence_runs": 0,
        "revisions": 0,
        "receipts": 0,
        "admissions": 0,
        "nonce_claims": 0,
        "suite_links": 0,
    }


@pytest.mark.parametrize(
    ("relation_name", "constraint_name"),
    MIGRATION_OCCUPANCY_CONSTRAINTS,
)
def test_native_unique_diagnostics_match_the_migration_occupancy_allowlist(
    postgres_session_factory,
    relation_name: str,
    constraint_name: str,
) -> None:
    """ORM-only names or broad 23505 handling cannot satisfy this contract."""

    session = postgres_session_factory()
    probe_name = f"fairmind_occupancy_diag_{uuid.uuid4().hex}"
    try:
        observed_relation = session.scalar(
            text(
                "SELECT relation.relname "
                "FROM pg_catalog.pg_constraint AS constraint_entry "
                "JOIN pg_catalog.pg_class AS relation "
                "ON relation.oid = constraint_entry.conrelid "
                "JOIN pg_catalog.pg_namespace AS namespace "
                "ON namespace.oid = relation.relnamespace "
                "WHERE namespace.nspname = current_schema() "
                "AND relation.relname = :relation_name "
                "AND constraint_entry.conname = :constraint_name "
                "AND constraint_entry.contype = 'u'"
            ),
            {
                "relation_name": relation_name,
                "constraint_name": constraint_name,
            },
        )
        assert observed_relation == relation_name
        session.execute(
            text(
                f'CREATE TEMP TABLE "{probe_name}" '
                f'(value INTEGER, CONSTRAINT "{constraint_name}" UNIQUE (value))'
            )
        )
        session.execute(text(f'INSERT INTO "{probe_name}" (value) VALUES (1)'))

        with pytest.raises(IntegrityError) as caught:
            with session.begin_nested():
                session.execute(text(f'INSERT INTO "{probe_name}" (value) VALUES (1)'))

        assert caught.value.orig.pgcode == "23505"
        assert caught.value.orig.diag.constraint_name == constraint_name
        assert (
            SqlAlchemyEvaluationWorkbenchRepository._evidence_database_error_kind(caught.value)
            == "occupied"
        )
    finally:
        session.rollback()
        session.close()


def test_twenty_identical_concurrent_requests_persist_exactly_one_graph_audit_and_key(
    postgres_session_factory,
) -> None:
    """Removing the org/idempotency lock would duplicate signed evidence graphs."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    _payload, raw = _signed_passport(scenario)
    key = f"admit-{uuid.uuid4()}"
    barrier = Barrier(20)

    def submit_once(_index: int):
        session = factory()
        try:
            barrier.wait(timeout=30)
            return _admit(session, scenario, raw=raw, idempotency_key=key)
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(submit_once, range(20)))

    assert {result.status for result in results} == {201}
    assert sum(not result.replayed for result in results) == 1
    assert len({canonical_json(result.body) for result in results}) == 1
    _assert_one_graph(factory, scenario)
    assert _operation_idempotency_count(factory, scenario) == 1
    assert _admission_audit_count(factory, scenario) == 1


def test_response_loss_replay_returns_the_bound_success_without_writing_again(
    postgres_session_factory,
) -> None:
    """A lost response must replay its committed graph, not execute admission twice."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    _payload, raw = _signed_passport(scenario)
    key = f"admit-{uuid.uuid4()}"

    first_session = factory()
    try:
        first = _admit(first_session, scenario, raw=raw, idempotency_key=key)
    finally:
        first_session.close()

    replay_session = factory()
    try:
        replay = _admit(replay_session, scenario, raw=raw, idempotency_key=key)
    finally:
        replay_session.close()

    assert first.status == replay.status == 201
    assert first.replayed is False
    assert replay.replayed is True
    assert replay.body == first.body
    _assert_one_graph(factory, scenario)
    assert _operation_idempotency_count(factory, scenario) == 1
    assert _admission_audit_count(factory, scenario) == 1


def test_same_key_with_changed_exact_signed_bytes_is_an_idempotency_conflict(
    postgres_session_factory,
) -> None:
    """Hashing only normalized content would accept a changed signature/request body."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    payload_a, raw_a = _signed_passport(scenario)
    payload_b = deepcopy(payload_a)
    original_signed_at = _parse_timestamp(str(payload_b["signature"]["signedAt"]))
    payload_b["signature"]["signedAt"] = _iso(original_signed_at + timedelta(microseconds=1))
    raw_b = _resign(payload_b, scenario.signing)
    assert payload_b["contentHash"] == payload_a["contentHash"]
    assert payload_b["signature"]["value"] != payload_a["signature"]["value"]
    assert raw_a != raw_b
    key = f"admit-{uuid.uuid4()}"

    session = factory()
    try:
        _admit(session, scenario, raw=raw_a, idempotency_key=key)
    finally:
        session.close()

    conflict_session = factory()
    try:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            _admit(conflict_session, scenario, raw=raw_b, idempotency_key=key)
        assert caught.value.code == "idempotency_conflict"
        assert caught.value.status_code == 409
    finally:
        conflict_session.close()

    _assert_one_graph(factory, scenario)
    assert _operation_idempotency_count(factory, scenario) == 1
    assert _admission_audit_count(factory, scenario) == 1


def test_new_key_cannot_overwrite_an_occupied_suite_projection(
    postgres_session_factory,
) -> None:
    """A second key must not turn immutable suite evidence into last-write-wins state."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    _payload_a, raw_a = _signed_passport(scenario)
    _payload_b, raw_b = _signed_passport(scenario)
    first_key = f"admit-{uuid.uuid4()}"
    second_key = f"admit-{uuid.uuid4()}"

    session = factory()
    try:
        _admit(session, scenario, raw=raw_a, idempotency_key=first_key)
    finally:
        session.close()

    occupied_session = factory()
    try:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            _admit(occupied_session, scenario, raw=raw_b, idempotency_key=second_key)
        assert caught.value.code == "evidence_admission_occupied"
        assert caught.value.status_code == 409
    finally:
        occupied_session.close()

    _assert_one_graph(factory, scenario)
    assert _operation_idempotency_count(factory, scenario) == 2
    assert _admission_audit_count(factory, scenario) == 2


def test_two_distinct_concurrent_passports_for_one_suite_have_one_winner(
    postgres_session_factory,
) -> None:
    """The suite occupancy decision must serialize before any evidence graph write."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    _payload_a, raw_a = _signed_passport(scenario)
    _payload_b, raw_b = _signed_passport(scenario)
    barrier = Barrier(2)

    def submit(raw: bytes):
        session = factory()
        try:
            barrier.wait(timeout=30)
            try:
                result = _admit(
                    session,
                    scenario,
                    raw=raw,
                    idempotency_key=f"admit-{uuid.uuid4()}",
                )
                return ("success", result.status)
            except EvaluationWorkbenchError as error:
                return (error.code, error.status_code)
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(submit, (raw_a, raw_b)))

    assert sorted(outcomes) == [
        ("evidence_admission_occupied", 409),
        ("success", 201),
    ]
    _assert_one_graph(factory, scenario)
    assert _operation_idempotency_count(factory, scenario) == 2
    assert _admission_audit_count(factory, scenario) == 2


def test_wrong_organization_system_run_and_suite_scopes_create_no_graph(
    postgres_session_factory,
) -> None:
    """Dropping any caller-scope predicate would admit cross-scope evidence."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    _payload, raw = _signed_passport(scenario)
    wrong_scopes = (
        _scope(scenario, organization_id=str(uuid.uuid4())),
        _scope(scenario, system_id=str(uuid.uuid4())),
        _scope(scenario, run_id=str(uuid.uuid4())),
        _scope(scenario, suite_execution_id=str(uuid.uuid4())),
    )

    for wrong_scope in wrong_scopes:
        session = factory()
        try:
            with pytest.raises(EvaluationWorkbenchError) as caught:
                _admit(
                    session,
                    scenario,
                    raw=raw,
                    idempotency_key=f"admit-{uuid.uuid4()}",
                    scope=wrong_scope,
                )
            assert 400 <= caught.value.status_code < 500
        finally:
            session.close()
        _assert_empty_graph(factory, scenario)


def test_real_foreign_tenant_scope_catalog_and_signer_identities_create_no_graph(
    postgres_session_factory,
) -> None:
    """Dropping any tenant authority predicate would admit a real foreign graph."""

    factory = postgres_session_factory
    local = _seed_scenario(factory)
    foreign = _seed_scenario(factory)
    assert local.org_id != foreign.org_id
    assert local.workspace_id != foreign.workspace_id
    assert local.system_id != foreign.system_id
    assert local.target_version_id != foreign.target_version_id
    assert local.suite_version_ids[0] != foreign.suite_version_ids[0]
    assert local.run_id != foreign.run_id
    assert local.trust_policy_id != foreign.trust_policy_id
    assert local.signing.issuer_row_id != foreign.signing.issuer_row_id
    assert local.signing.signing_key_row_id != foreign.signing.signing_key_row_id

    session = factory()
    try:
        repository = SqlAlchemyEvaluationWorkbenchRepository(session)
        assert (
            session.scalar(
                text(
                    "SELECT owner_scope FROM governance_evaluation_suite_versions "
                    "WHERE id = :suite_id"
                ),
                {"suite_id": foreign.suite_version_ids[0]},
            )
            == foreign.org_id
        )
        assert not repository.restriction_references_exist(
            scope=_scope(local),
            suite_version_ids=(foreign.suite_version_ids[0],),
            target_version_ids=(),
        )
        assert not repository.restriction_references_exist(
            scope=_scope(local),
            suite_version_ids=(),
            target_version_ids=(foreign.target_version_id,),
        )
        assert not repository.restriction_references_exist(
            scope=_scope(local),
            suite_version_ids=(foreign.suite_version_ids[0],),
            target_version_ids=(foreign.target_version_id,),
        )
    finally:
        session.close()

    _payload, local_raw = _signed_passport(local)
    _foreign_selector_payload, foreign_selector_raw = _signed_passport(
        local,
        signing=foreign.signing,
    )
    local_execution_id = str(local.suite_executions[0]["id"])
    foreign_execution_id = str(foreign.suite_executions[0]["id"])
    attempts = (
        (
            "foreign-organization-reverse-hybrid",
            EvidenceAdmissionScope(
                organization_id=foreign.org_id,
                system_id=local.system_id,
                run_id=local.run_id,
                suite_execution_id=local_execution_id,
            ),
            local_raw,
        ),
        (
            "foreign-system",
            EvidenceAdmissionScope(
                organization_id=local.org_id,
                system_id=foreign.system_id,
                run_id=local.run_id,
                suite_execution_id=local_execution_id,
            ),
            local_raw,
        ),
        (
            "foreign-run",
            EvidenceAdmissionScope(
                organization_id=local.org_id,
                system_id=local.system_id,
                run_id=foreign.run_id,
                suite_execution_id=local_execution_id,
            ),
            local_raw,
        ),
        (
            "foreign-suite-execution",
            EvidenceAdmissionScope(
                organization_id=local.org_id,
                system_id=local.system_id,
                run_id=local.run_id,
                suite_execution_id=foreign_execution_id,
            ),
            local_raw,
        ),
        (
            "foreign-system-run-suite-hybrid",
            EvidenceAdmissionScope(
                organization_id=local.org_id,
                system_id=foreign.system_id,
                run_id=foreign.run_id,
                suite_execution_id=foreign_execution_id,
            ),
            local_raw,
        ),
        (
            "local-signer-under-complete-foreign-scope",
            _scope(foreign),
            local_raw,
        ),
        (
            "foreign-signer-under-local-scope",
            _scope(local),
            foreign_selector_raw,
        ),
    )

    for label, scope, raw in attempts:
        session = factory()
        try:
            with pytest.raises(EvaluationWorkbenchError) as caught:
                _admit(
                    session,
                    local,
                    raw=raw,
                    idempotency_key=f"foreign-scope-{uuid.uuid4()}",
                    scope=scope,
                )
            assert 400 <= caught.value.status_code < 500, label
        finally:
            session.close()
        _assert_empty_graph(factory, local)
        _assert_empty_graph(factory, foreign)
        assert _successful_admission_audit_count(factory, local) == 0, label
        assert _successful_admission_audit_count(factory, foreign) == 0, label


class _FalseVerifier:
    def __call__(self, **_kwargs: object) -> bool:
        return False


class _CrashingVerifier:
    def __call__(self, **_kwargs: object) -> bool:
        raise RuntimeError("private-verifier-crash-material")


@pytest.mark.parametrize("verifier", (_FalseVerifier(), _CrashingVerifier()))
def test_invalid_or_crashing_signature_verifier_never_creates_false_success(
    postgres_session_factory,
    verifier,
) -> None:
    """Verifier false/exception paths must become bounded rejection, never a pass."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    _payload, raw = _signed_passport(scenario)
    session = factory()
    try:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            _admit(
                session,
                scenario,
                raw=raw,
                idempotency_key=f"admit-{uuid.uuid4()}",
                verifier=verifier,
            )
        assert 400 <= caught.value.status_code < 500
        assert "private-verifier-crash-material" not in str(caught.value.detail())
    finally:
        session.close()

    _assert_empty_graph(factory, scenario)
    assert _operation_idempotency_count(factory, scenario) == 1
    assert _admission_audit_count(factory, scenario) == 1


_BINDING_MUTATIONS: tuple[tuple[tuple[str, ...], object], ...] = (
    (("organizationId",), "00000000-0000-0000-0000-000000000001"),
    (("workspaceId",), "workspace-mutated"),
    (("systemId",), "system-mutated"),
    (("runId",), "run-mutated"),
    (("envelopeId",), "envelope-mutated"),
    (("envelopeHash",), "1" * 64),
    (("nonce",), _b64url(bytes(reversed(range(32))))),
    (("planId",), "plan-mutated"),
    (("planContentHash",), "2" * 64),
    (("target", "targetVersionId"), "target-mutated"),
    (("target", "subjectDigest"), "3" * 64),
    (("target", "manifestDigest"), "4" * 64),
    (("suite", "suiteExecutionId"), "execution-mutated"),
    (("suite", "suiteVersionId"), "suite-mutated"),
    (("suite", "manifestDigest"), "5" * 64),
    (("suite", "configurationHash"), "6" * 64),
    (("lifecyclePhase",), "post_deploy"),
    (("executionDepth",), "hybrid"),
    (("enforcementMode",), "advisory"),
    (("deliveryMode",), "fairmind_worker"),
    (("trustPolicy", "trustPolicyVersionId"), "policy-mutated"),
    (("trustPolicy", "policyHash"), "7" * 64),
)
_EVALUATOR_MUTATIONS: tuple[tuple[str, object], ...] = (
    ("issuerId", "issuer-mutated"),
    ("sourceType", "fairmind_worker"),
    ("adapterName", "garak"),
    ("adapterVersion", "9.9.9"),
    ("resultContractVersion", "9.9.9"),
)


def _set_path(mapping: dict[str, Any], path: tuple[str, ...], value: object) -> None:
    cursor = mapping
    for member in path[:-1]:
        child = cursor[member]
        assert isinstance(child, dict)
        cursor = child
    cursor[path[-1]] = value


def test_every_signed_binding_and_evaluator_authority_mutation_is_rejected(
    postgres_session_factory,
) -> None:
    """Removing any exact binding/evaluator comparison must make this matrix fail."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    mutations: list[tuple[str, tuple[str, ...], object]] = [
        ("binding", path, value) for path, value in _BINDING_MUTATIONS
    ] + [("evaluator", (field,), value) for field, value in _EVALUATOR_MUTATIONS]

    for index, (section, path, value) in enumerate(mutations):
        payload, _raw = _signed_passport(
            scenario,
            passport_id=str(uuid.uuid4()),
        )
        target = payload["executionBinding"] if section == "binding" else payload["evaluator"]
        assert isinstance(target, dict)
        _set_path(target, path, value)
        raw = _resign(payload, scenario.signing)
        session = factory()
        try:
            with pytest.raises(EvaluationWorkbenchError) as caught:
                _admit(
                    session,
                    scenario,
                    raw=raw,
                    idempotency_key=f"admit-mutation-{index}-{uuid.uuid4()}",
                )
            assert 400 <= caught.value.status_code < 500
        finally:
            session.close()
        _assert_empty_graph(factory, scenario)

    assert _operation_idempotency_count(factory, scenario) == len(mutations)
    assert _admission_audit_count(factory, scenario) == len(mutations)


def test_service_rejects_an_authentically_resigned_nonce_rebinding(
    postgres_session_factory,
) -> None:
    """A valid signature over a foreign nonce must not override server authority."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    second_run_session = factory()
    try:
        second_run = (
            _workbench_service(second_run_session)
            .create_run(
                org_id=scenario.org_id,
                system_id=scenario.system_id,
                plan_id=scenario.plan_id,
                actor_id=scenario.actor_id,
                idempotency_key=f"second-run-{uuid.uuid4()}",
                payload={"trigger": "manual", "lifecyclePhase": "pre_deploy"},
            )
            .body
        )
    finally:
        second_run_session.close()
    payload, _raw = _signed_passport(scenario)
    foreign_nonce = second_run["envelope"]["nonce"]
    assert foreign_nonce != scenario.run["envelope"]["nonce"]
    payload["executionBinding"]["nonce"] = foreign_nonce
    raw = _resign(payload, scenario.signing)

    session = factory()
    try:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            _admit(
                session,
                scenario,
                raw=raw,
                idempotency_key=f"admit-{uuid.uuid4()}",
            )
        assert 400 <= caught.value.status_code < 500
    finally:
        session.close()

    _assert_empty_graph(factory, scenario)


def test_key_rotation_resolves_the_exact_signed_key_and_never_falls_back(
    postgres_session_factory,
) -> None:
    """An active replacement key must not make a Passport from a revoked key valid."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    session = factory()
    try:
        replacement = _insert_additional_signing_key(session, scenario=scenario)
        _old_payload, old_raw = _signed_passport(scenario, signing=scenario.signing)
        revoked_at = _iso(datetime.now(timezone.utc))
        session.execute(
            text(
                "UPDATE governance_evidence_signing_keys "
                "SET revoked_at = :revoked_at, revocation_reason = 'rotation' "
                "WHERE id = :key_id AND org_id = :org_id"
            ),
            {
                "revoked_at": revoked_at,
                "key_id": scenario.signing.signing_key_row_id,
                "org_id": scenario.org_id,
            },
        )
        session.commit()
    finally:
        session.close()

    rejected_session = factory()
    try:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            _admit(
                rejected_session,
                scenario,
                raw=old_raw,
                idempotency_key=f"admit-old-{uuid.uuid4()}",
            )
        assert 400 <= caught.value.status_code < 500
    finally:
        rejected_session.close()
    _assert_empty_graph(factory, scenario)

    _new_payload, new_raw = _signed_passport(scenario, signing=replacement)
    accepted_session = factory()
    try:
        result = _admit(
            accepted_session,
            scenario,
            raw=new_raw,
            idempotency_key=f"admit-new-{uuid.uuid4()}",
        )
        assert result.status == 201
    finally:
        accepted_session.close()
    _assert_one_graph(factory, scenario)


def test_cross_suite_passport_revision_collision_rolls_back_the_second_graph(
    postgres_session_factory,
) -> None:
    """A repeated org/passport/revision identity cannot split across two suites."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory, suite_count=2)
    passport_id = str(uuid.uuid4())
    _first_payload, first_raw = _signed_passport(
        scenario,
        suite_ordinal=0,
        passport_id=passport_id,
    )
    _second_payload, second_raw = _signed_passport(
        scenario,
        suite_ordinal=1,
        passport_id=passport_id,
    )

    first_session = factory()
    try:
        first = _admit(
            first_session,
            scenario,
            raw=first_raw,
            idempotency_key=f"admit-first-{uuid.uuid4()}",
            scope=_scope(scenario, suite_ordinal=0),
        )
        assert first.status == 201
    finally:
        first_session.close()

    second_session = factory()
    try:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            _admit(
                second_session,
                scenario,
                raw=second_raw,
                idempotency_key=f"admit-second-{uuid.uuid4()}",
                scope=_scope(scenario, suite_ordinal=1),
            )
        assert caught.value.status_code == 409
    finally:
        second_session.close()

    _assert_one_graph(factory, scenario)
    unlinked = int(
        _scalar(
            factory,
            "SELECT count(*) FROM governance_evaluation_run_suite_executions "
            "WHERE org_id = :org_id AND run_id = :run_id "
            "AND evidence_run_id IS NULL",
            org_id=scenario.org_id,
            run_id=scenario.run_id,
        )
    )
    assert unlinked == 1


def test_mixed_technical_and_evidence_axes_remain_independent_at_run_level(
    postgres_session_factory,
) -> None:
    """A failed evaluator plus a successful evaluator/model-fail cannot collapse axes."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory, suite_count=2)
    _failed_payload, failed_raw = _signed_passport(
        scenario,
        suite_ordinal=0,
        result={
            "technicalStatus": "failed",
            "evidenceResultStatus": "error",
            "summary": {"failureStage": "provider"},
        },
    )
    _model_failed_payload, model_failed_raw = _signed_passport(
        scenario,
        suite_ordinal=1,
        result={
            "technicalStatus": "succeeded",
            "evidenceResultStatus": "failed",
            "summary": {"attackSuccessRate": 0.40},
        },
    )

    for ordinal, raw in enumerate((failed_raw, model_failed_raw)):
        session = factory()
        try:
            result = _admit(
                session,
                scenario,
                raw=raw,
                idempotency_key=f"admit-axis-{ordinal}-{uuid.uuid4()}",
                scope=_scope(scenario, suite_ordinal=ordinal),
            )
            assert result.status == 201
        finally:
            session.close()

    verification = factory()
    try:
        run = (
            verification.execute(
                text(
                    "SELECT technical_status, evidence_outcome, overall_verdict, "
                    "verdict_version, layer_verdicts_json "
                    "FROM governance_evaluation_runs "
                    "WHERE id = :run_id AND org_id = :org_id"
                ),
                {"run_id": scenario.run_id, "org_id": scenario.org_id},
            )
            .mappings()
            .one()
        )
        suites = (
            verification.execute(
                text(
                    "SELECT ordinal, technical_status, evidence_result_status, "
                    "admission_status, review_status "
                    "FROM governance_evaluation_run_suite_executions "
                    "WHERE run_id = :run_id AND org_id = :org_id ORDER BY ordinal"
                ),
                {"run_id": scenario.run_id, "org_id": scenario.org_id},
            )
            .mappings()
            .all()
        )
    finally:
        verification.close()

    assert [(row["technical_status"], row["evidence_result_status"]) for row in suites] == [
        ("failed", "error"),
        ("succeeded", "failed"),
    ]
    assert {row["admission_status"] for row in suites} == {"verified"}
    assert {row["review_status"] for row in suites} == {"pending"}
    assert run["technical_status"] == "failed"
    assert run["evidence_outcome"] == "failed"
    assert run["overall_verdict"] == "insufficient"
    assert run["verdict_version"] == 0
    layer_verdicts = json.loads(run["layer_verdicts_json"])
    assert set(layer_verdicts["suites"].values()) == {"insufficient"}
    assert _graph_counts(factory, scenario) == {
        "evidence_runs": 2,
        "revisions": 2,
        "receipts": 2,
        "admissions": 2,
        "nonce_claims": 2,
        "suite_links": 2,
    }


def _set_terminal_but_unlinked(
    session,
    scenario: AdmissionScenario,
    *,
    suite_ordinal: int,
    technical_status: str,
    evidence_result_status: str,
) -> None:
    execution_id = str(scenario.suite_executions[suite_ordinal]["id"])
    updated_at = session.scalar(text("SELECT clock_timestamp() AT TIME ZONE 'UTC'")).replace(
        tzinfo=timezone.utc
    )
    updated_text = _iso(updated_at)
    session.execute(
        text(
            "UPDATE governance_evaluation_run_suite_executions SET "
            "technical_status = :technical_status, "
            "evidence_result_status = :evidence_result_status, "
            "started_at = created_at, completed_at = :completed_at, "
            "updated_at = :updated_at "
            "WHERE id = :execution_id AND org_id = :org_id"
        ),
        {
            "technical_status": technical_status,
            "evidence_result_status": evidence_result_status,
            "completed_at": updated_text,
            "updated_at": updated_text,
            "execution_id": execution_id,
            "org_id": scenario.org_id,
        },
    )


def test_all_terminal_but_unlinked_siblings_can_each_admit_exact_evidence(
    postgres_session_factory,
) -> None:
    """Authority resolution must not reject legal terminal evaluator state before link."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory, suite_count=2)
    state_session = factory()
    try:
        _set_terminal_but_unlinked(
            state_session,
            scenario,
            suite_ordinal=0,
            technical_status="succeeded",
            evidence_result_status="failed",
        )
        _set_terminal_but_unlinked(
            state_session,
            scenario,
            suite_ordinal=1,
            technical_status="failed",
            evidence_result_status="error",
        )
        state_session.commit()
    finally:
        state_session.close()

    _first_payload, first_raw = _signed_passport(
        scenario,
        suite_ordinal=0,
        result={
            "technicalStatus": "succeeded",
            "evidenceResultStatus": "failed",
            "summary": {"attackSuccessRate": 0.25},
        },
    )
    _second_payload, second_raw = _signed_passport(
        scenario,
        suite_ordinal=1,
        result={
            "technicalStatus": "failed",
            "evidenceResultStatus": "error",
            "summary": {"failureStage": "provider"},
        },
    )
    for ordinal, raw in enumerate((first_raw, second_raw)):
        session = factory()
        try:
            result = _admit(
                session,
                scenario,
                raw=raw,
                idempotency_key=f"admit-terminal-{ordinal}-{uuid.uuid4()}",
                scope=_scope(scenario, suite_ordinal=ordinal),
            )
            assert result.status == 201
        finally:
            session.close()
        if ordinal == 0:
            parent_after_first = factory()
            try:
                parent_state = (
                    parent_after_first.execute(
                        text(
                            "SELECT technical_status, evidence_outcome "
                            "FROM governance_evaluation_runs "
                            "WHERE id = :run_id AND org_id = :org_id"
                        ),
                        {"run_id": scenario.run_id, "org_id": scenario.org_id},
                    )
                    .mappings()
                    .one()
                )
            finally:
                parent_after_first.close()
            assert dict(parent_state) == {
                "technical_status": "awaiting_evidence",
                "evidence_outcome": "pending",
            }

    assert _graph_counts(factory, scenario) == {
        "evidence_runs": 2,
        "revisions": 2,
        "receipts": 2,
        "admissions": 2,
        "nonce_claims": 2,
        "suite_links": 2,
    }
    assert (
        _scalar(
            factory,
            "SELECT count(*) FROM governance_evaluation_run_suite_executions "
            "WHERE run_id = :run_id AND org_id = :org_id "
            "AND admission_status = 'verified' AND evidence_run_id IS NOT NULL",
            run_id=scenario.run_id,
            org_id=scenario.org_id,
        )
        == 2
    )
    final_parent = factory()
    try:
        final_state = (
            final_parent.execute(
                text(
                    "SELECT technical_status, evidence_outcome "
                    "FROM governance_evaluation_runs "
                    "WHERE id = :run_id AND org_id = :org_id"
                ),
                {"run_id": scenario.run_id, "org_id": scenario.org_id},
            )
            .mappings()
            .one()
        )
    finally:
        final_parent.close()
    assert dict(final_state) == {
        "technical_status": "failed",
        "evidence_outcome": "failed",
    }


def _revoke_authority(session, scenario: AdmissionScenario, resource: str) -> None:
    now = _iso(datetime.now(timezone.utc))
    if resource == "policy":
        session.execute(
            text(
                "UPDATE governance_evidence_trust_policy_versions "
                "SET status = 'retired' WHERE id = :id AND org_id = :org_id"
            ),
            {"id": scenario.trust_policy_id, "org_id": scenario.org_id},
        )
    elif resource == "issuer":
        session.execute(
            text(
                "UPDATE governance_evidence_issuers SET status = 'revoked', "
                "updated_at = :updated_at WHERE id = :id AND org_id = :org_id"
            ),
            {
                "updated_at": now,
                "id": scenario.signing.issuer_row_id,
                "org_id": scenario.org_id,
            },
        )
    elif resource == "key":
        session.execute(
            text(
                "UPDATE governance_evidence_signing_keys SET revoked_at = :revoked_at, "
                "revocation_reason = 'adversarial race' "
                "WHERE id = :id AND org_id = :org_id"
            ),
            {
                "revoked_at": now,
                "id": scenario.signing.signing_key_row_id,
                "org_id": scenario.org_id,
            },
        )
    else:
        raise AssertionError(resource)
    session.commit()


@pytest.mark.parametrize("resource", ("policy", "issuer", "key"))
def test_revocation_committed_before_admission_rejects_without_a_graph(
    postgres_session_factory,
    resource: str,
) -> None:
    """A stale or unlocked authority read would admit after committed revocation."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    _payload, raw = _signed_passport(scenario)
    revoke_session = factory()
    try:
        _revoke_authority(revoke_session, scenario, resource)
    finally:
        revoke_session.close()

    admission_session = factory()
    try:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            _admit(
                admission_session,
                scenario,
                raw=raw,
                idempotency_key=f"admit-revoked-{resource}-{uuid.uuid4()}",
            )
        assert 400 <= caught.value.status_code < 500
    finally:
        admission_session.close()
    _assert_empty_graph(factory, scenario)


class _BlockingRealVerifier:
    def __init__(self) -> None:
        self.entered = Event()
        self.release = Event()
        self._inner = Ed25519EvidenceVerifier()

    def __call__(self, **kwargs: object) -> bool:
        self.entered.set()
        if not self.release.wait(timeout=30):
            raise RuntimeError("blocking verifier timed out")
        return self._inner(**kwargs)


@pytest.mark.parametrize("resource", ("policy", "issuer", "key"))
def test_admission_lock_wins_then_revocation_commits_after_the_verified_graph(
    postgres_session_factory,
    resource: str,
) -> None:
    """The second authority check and write must serialize against revocation."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    _payload, raw = _signed_passport(scenario)
    verifier = _BlockingRealVerifier()
    revoke_attempted = Event()

    def admit_in_thread():
        session = factory()
        try:
            return _admit(
                session,
                scenario,
                raw=raw,
                idempotency_key=f"admit-race-{resource}-{uuid.uuid4()}",
                verifier=verifier,
            )
        finally:
            session.close()

    def revoke_in_thread():
        session = factory()
        try:
            revoke_attempted.set()
            _revoke_authority(session, scenario, resource)
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        admission_future = executor.submit(admit_in_thread)
        assert verifier.entered.wait(timeout=30)
        revocation_future = executor.submit(revoke_in_thread)
        assert revoke_attempted.wait(timeout=30)
        verifier.release.set()
        admission_result = admission_future.result(timeout=30)
        revocation_future.result(timeout=30)

    assert admission_result.status == 201
    _assert_one_graph(factory, scenario)


class _CorruptDeferredReceiptRepository(SqlAlchemyEvaluationWorkbenchRepository):
    failure_class: str | None = None
    driver_failure_class: str | None = None
    sqlstate: str | None = None

    def persist_verified_passport_v2(self, command):
        return super().persist_verified_passport_v2(
            replace(command, execution_binding_hash="0" * 64)
        )

    def _raise_evidence_database_error(self, error: DBAPIError) -> None:
        self.failure_class = type(error).__name__
        self.driver_failure_class = type(error.orig).__name__
        self.sqlstate = getattr(error.orig, "pgcode", None)
        super()._raise_evidence_database_error(error)


def test_deferred_receipt_corruption_is_one_durable_rejection_and_exact_replay(
    postgres_session_factory,
) -> None:
    """A deferred relational mismatch must reject atomically and replay once."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    _payload, raw = _signed_passport(scenario)
    key = f"admit-corrupt-{uuid.uuid4()}"
    corrupt_session = factory()
    repository = _CorruptDeferredReceiptRepository(corrupt_session)
    try:
        with pytest.raises(EvaluationWorkbenchError) as first_caught:
            _admit(
                corrupt_session,
                scenario,
                raw=raw,
                idempotency_key=key,
                repository=repository,
            )
        assert first_caught.value.status_code == 409
        first_detail = first_caught.value.detail()
    finally:
        corrupt_session.close()

    assert repository.failure_class == "InternalError"
    assert repository.sqlstate == "P0001"
    assert repository.driver_failure_class == "RaiseException"
    _assert_empty_graph(factory, scenario)

    replay_session = factory()
    try:
        with pytest.raises(EvaluationWorkbenchError) as replay_caught:
            _admit(
                replay_session,
                scenario,
                raw=raw,
                idempotency_key=key,
            )
        assert replay_caught.value.detail() == first_detail
    finally:
        replay_session.close()

    _assert_empty_graph(factory, scenario)
    assert _operation_idempotency_count(factory, scenario) == 1
    assert _admission_audit_count(factory, scenario) == 1


class _RaiseAfterGraphRepository(SqlAlchemyEvaluationWorkbenchRepository):
    def persist_verified_passport_v2(self, command):
        super().persist_verified_passport_v2(command)
        raise RuntimeError("injected-operational-persistence-failure")


def test_unexpected_failure_after_writes_rolls_back_graph_audit_and_idempotency(
    postgres_session_factory,
) -> None:
    """An unexpected post-write exception must leave no committed mutation trace."""
    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    _payload, raw = _signed_passport(scenario)
    session = factory()
    repository = _RaiseAfterGraphRepository(session)
    try:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            _admit(
                session,
                scenario,
                raw=raw,
                idempotency_key=f"admit-operational-{uuid.uuid4()}",
                repository=repository,
            )
        assert caught.value.code == "evaluation_persistence_failed"
        assert caught.value.status_code == 500
        assert "injected-operational-persistence-failure" not in str(caught.value.detail())
    finally:
        session.close()

    _assert_empty_graph(factory, scenario)
    assert _operation_idempotency_count(factory, scenario) == 0
    assert _admission_audit_count(factory, scenario) == 0


class _RaiseUnrelatedConstraintAfterGraphRepository(SqlAlchemyEvaluationWorkbenchRepository):
    def __init__(self, session, failure_statement: str) -> None:
        super().__init__(session)
        self._failure_statement = failure_statement
        self.sqlstate: str | None = None
        self.constraint_name: str | None = None

    def persist_verified_passport_v2(self, command):
        super().persist_verified_passport_v2(command)
        try:
            self.db.execute(text(self._failure_statement))
        except DBAPIError as error:
            self.sqlstate = getattr(error.orig, "pgcode", None)
            self.constraint_name = getattr(error.orig.diag, "constraint_name", None)
            raise


@pytest.mark.parametrize(
    ("failure_kind", "expected_sqlstate", "expected_constraint"),
    (
        ("check", "23514", "ck_unrelated_verified_evidence_probe"),
        ("foreign_key", "23503", "fk_unrelated_verified_evidence_probe"),
    ),
)
def test_unrelated_native_integrity_after_graph_is_a_500_and_total_rollback(
    postgres_session_factory,
    failure_kind: str,
    expected_sqlstate: str,
    expected_constraint: str,
) -> None:
    """Unrelated 23xxx failures must never become durable domain rejections."""

    factory = postgres_session_factory
    scenario = _seed_scenario(factory)
    _payload, raw = _signed_passport(scenario)
    session = factory()
    suffix = uuid.uuid4().hex
    if failure_kind == "check":
        table_name = f"fairmind_unrelated_check_{suffix}"
        session.execute(
            text(
                f'CREATE TABLE "{table_name}" '
                "(value INTEGER, "
                f'CONSTRAINT "{expected_constraint}" CHECK (value > 0))'
            )
        )
        failure_statement = f'INSERT INTO "{table_name}" (value) VALUES (-1)'
    else:
        parent_name = f"fairmind_unrelated_parent_{suffix}"
        table_name = f"fairmind_unrelated_child_{suffix}"
        session.execute(text(f'CREATE TABLE "{parent_name}" (id INTEGER PRIMARY KEY)'))
        session.execute(
            text(
                f'CREATE TABLE "{table_name}" '
                "(parent_id INTEGER, "
                f'CONSTRAINT "{expected_constraint}" FOREIGN KEY (parent_id) '
                f'REFERENCES "{parent_name}" (id))'
            )
        )
        failure_statement = f'INSERT INTO "{table_name}" (parent_id) VALUES (404)'
    session.commit()
    repository = _RaiseUnrelatedConstraintAfterGraphRepository(
        session,
        failure_statement,
    )
    try:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            _admit(
                session,
                scenario,
                raw=raw,
                idempotency_key=f"admit-unrelated-{failure_kind}-{uuid.uuid4()}",
                repository=repository,
            )
        assert caught.value.code == "evaluation_persistence_failed"
        assert caught.value.status_code == 500
        assert expected_constraint not in str(caught.value.detail())
    finally:
        session.close()

    assert repository.sqlstate == expected_sqlstate
    assert repository.constraint_name == expected_constraint
    _assert_empty_graph(factory, scenario)
    assert _operation_idempotency_count(factory, scenario) == 0
    assert _admission_audit_count(factory, scenario) == 0
