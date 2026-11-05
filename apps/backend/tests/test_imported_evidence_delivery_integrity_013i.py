"""Database contract tests for imported-evidence delivery integrity 013i.

PostgreSQL 14 is the release authority.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = BACKEND_ROOT / "migrations"
HASH_A = "a" * 64
HASH_B = "b" * 64
POSTGRES_URL = os.getenv("FAIRMIND_TEST_POSTGRES_URL")
POSTGRES_DIRECT_CHAIN_THROUGH_013H = (
    "001_initial_schema.sql",
    "007_org_rbac_schema_CORRECTED.sql",
    "008_governance_canonical.sql",
    "010_environmental_governance.sql",
    "011_governance_assurance.sql",
    "012_evaluation_runs.sql",
    "013_evaluation_assurance_contract_v2.sql",
    "013a_evaluation_binding_integrity.sql",
    "013b_evaluation_assurance_trust_integrity.sql",
    "013c_evidence_verification_receipt.sql",
    "013d_evaluator_catalog.sql",
    "013e_environmental_tenant_scope.sql",
    "013f_trust_authority_integrity.sql",
    "013g_operational_evidence_freshness.sql",
    "013h_idempotency_retention_integrity.sql",
)
DIRECT_013I_CHECKSUM = (
    "83c77841beb21dbf96d1e40260534d262dbf21941b21fac4121964a065e36f94"
)


def test_postgresql_013i_payload_declares_exact_admission_guard() -> None:
    """The forward payload owns one narrowly scoped admission INSERT guard."""

    from migrations.imported_evidence_delivery_integrity_migration import sql_for

    source = sql_for("postgresql")

    assert "fairmind_unverified_import_delivery_is_valid_013i" in source
    assert '"000_013i_unverified_import_delivery_guard"' in source
    assert "BEFORE INSERT ON governance_evidence_admissions" in source
    assert "unverified evidence delivery binding failed" in source


def test_013h_to_013i_operator_binds_direct_payload_and_immutable_ledger() -> None:
    operator = (
        MIGRATIONS
        / "upgrade_paths"
        / "013h_to_013i_imported_evidence_delivery_integrity.sql"
    ).read_text(encoding="utf-8")

    assert "\\ir ../013i_imported_evidence_delivery_integrity.sql" in operator
    assert DIRECT_013I_CHECKSUM in operator
    assert "013h-to-013i-imported-evidence-delivery-integrity-v1" in operator
    assert "preexisting 013i catalog exists without its immutable ledger row" in operator


def _create_postgresql_schema_through_013h(
    postgres_url: str,
    schema_name: str,
) -> None:
    import psycopg2
    from psycopg2 import sql

    connection = psycopg2.connect(postgres_url)
    try:
        if connection.server_version // 10000 != 14:
            pytest.fail(
                "013i native suite requires PostgreSQL 14; "
                f"server_version={connection.server_version}"
            )
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name)))
            cursor.execute(
                sql.SQL("REVOKE CREATE ON SCHEMA {} FROM PUBLIC").format(
                    sql.Identifier(schema_name)
                )
            )
            cursor.execute("SET TIME ZONE 'UTC'")
            cursor.execute(
                sql.SQL("SET search_path TO {}, pg_catalog, pg_temp").format(
                    sql.Identifier(schema_name)
                )
            )
            for migration_name in POSTGRES_DIRECT_CHAIN_THROUGH_013H:
                cursor.execute(
                    "SELECT pg_catalog.set_config"
                    "('fairmind.migration_schema', %s, false)",
                    (schema_name,),
                )
                cursor.execute(
                    (MIGRATIONS / migration_name).read_text(encoding="utf-8")
                )
        connection.commit()
    finally:
        connection.close()


def _apply_postgresql_013i(engine: object, schema_name: str) -> None:
    raw_connection = engine.raw_connection()
    try:
        with raw_connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_catalog.set_config"
                "('fairmind.migration_schema', %s, false)",
                (schema_name,),
            )
            cursor.execute(
                (MIGRATIONS / "013i_imported_evidence_delivery_integrity.sql").read_text(
                    encoding="utf-8"
                )
            )
        raw_connection.commit()
    except Exception:
        raw_connection.rollback()
        raise
    finally:
        raw_connection.close()


def _drop_postgresql_schema(postgres_url: str, schema_name: str) -> None:
    import psycopg2
    from psycopg2 import sql

    connection = psycopg2.connect(postgres_url)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                    sql.Identifier(schema_name)
                )
            )
    finally:
        connection.close()


@pytest.fixture(scope="module")
def postgresql_013i_engine() -> Iterator[object]:
    if POSTGRES_URL is None:
        pytest.skip(
            "requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14"
        )

    from sqlalchemy import create_engine

    schema_name = f"fm_import_013i_{uuid.uuid4().hex[:12]}"
    _create_postgresql_schema_through_013h(POSTGRES_URL, schema_name)
    engine = create_engine(
        POSTGRES_URL,
        connect_args={
            "options": f"-csearch_path={schema_name},pg_catalog,pg_temp -ctimezone=UTC"
        },
    )
    try:
        _apply_postgresql_013i(engine, schema_name)
        yield engine
    finally:
        engine.dispose()
        _drop_postgresql_schema(POSTGRES_URL, schema_name)


def _seed_postgresql_run(
    engine: object,
    *,
    delivery_mode: str,
    unsigned_import_policy: str = "manual_review",
) -> dict[str, str]:
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    from src.application.services.evaluation_workbench_service import (
        EvaluationWorkbenchService,
    )
    from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256
    from src.infrastructure.db.repositories.evaluation_workbench_repository import (
        SqlAlchemyEvaluationWorkbenchUnitOfWork,
    )

    token = uuid.uuid4().hex
    org_id = str(uuid.uuid4())
    actor_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())
    system_id = str(uuid.uuid4())
    policy_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    policy = {
        "maximumEvidenceAgeSeconds": 86400,
        "schemaVersion": "1.0.0",
        "unsignedImportPolicy": unsigned_import_policy,
    }
    session = Session(engine, expire_on_commit=False)
    try:
        session.execute(
            text(
                "INSERT INTO users "
                "(id, email, username, password_hash, role, permissions) "
                "VALUES (:id, :email, :username, 'test-only', 'admin', '[]'::jsonb)"
            ),
            {"id": actor_id, "email": f"{token}@example.test", "username": token},
        )
        session.execute(
            text(
                "INSERT INTO organizations (id, name, slug, owner_id) "
                "VALUES (:id, :name, :slug, :owner_id)"
            ),
            {"id": org_id, "name": org_id, "slug": org_id, "owner_id": actor_id},
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
                "VALUES (:id, :org_id, :name, :now, :now)"
            ),
            {"id": workspace_id, "org_id": org_id, "name": workspace_id, "now": now},
        )
        session.execute(
            text(
                "INSERT INTO governance_ai_systems "
                "(id, workspace_id, org_id, name, created_at, updated_at) "
                "VALUES (:id, :workspace_id, :org_id, :name, :now, :now)"
            ),
            {
                "id": system_id,
                "workspace_id": workspace_id,
                "org_id": org_id,
                "name": system_id,
                "now": now,
            },
        )
        session.execute(
            text(
                "INSERT INTO governance_evidence_trust_policy_versions "
                "(id, org_id, version, policy_json, policy_hash, "
                "maximum_evidence_age_seconds, unsigned_import_policy, status, "
                "created_by, created_at) "
                "VALUES (:id, :org_id, '1.0.0', :policy_json, :policy_hash, "
                "86400, :unsigned_import_policy, 'draft', :actor_id, :now)"
            ),
            {
                "id": policy_id,
                "org_id": org_id,
                "policy_json": canonical_json(policy),
                "policy_hash": canonical_sha256(policy),
                "unsigned_import_policy": unsigned_import_policy,
                "actor_id": actor_id,
                "now": now,
            },
        )
        session.execute(
            text(
                "UPDATE governance_evidence_trust_policy_versions "
                "SET status='active', activated_by=:actor_id WHERE id=:policy_id"
            ),
            {"actor_id": actor_id, "policy_id": policy_id},
        )
        session.commit()

        service = EvaluationWorkbenchService(
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session)
        )
        target = service.create_target_version(
            org_id=org_id,
            system_id=system_id,
            actor_id=actor_id,
            idempotency_key=f"target-{token}",
            payload={
                "targetKey": str(uuid.uuid4()),
                "targetKind": "agent",
                "version": "1.0.0",
                "systemVersion": "1.0.0",
                "subjectKind": "agent",
                "subjectId": str(uuid.uuid4()),
                "subjectVersion": "1.0.0",
                "subjectDigest": HASH_A,
                "deploymentId": None,
                "connectorBindingId": None,
                "manifest": {
                    "schemaVersion": "2.0.0",
                    "inputs": {
                        "scenario_set": {
                            "kind": "content_digest",
                            "sha256": HASH_B,
                        }
                    },
                },
            },
        ).body
        suite = service.create_suite_version(
            org_id=org_id,
            actor_id=actor_id,
            idempotency_key=f"suite-{token}",
            payload={
                "namespace": "fairmind",
                "name": "import-report",
                "version": "1.0.0",
                "supportedTargetKinds": ["agent"],
                "supportedSubjectKinds": ["agent"],
                "lifecyclePhases": ["pre_deploy"],
                "executionDepths": ["deep"],
                "deliveryModes": [delivery_mode],
                "workerType": delivery_mode,
                **(
                    {"runnerImageDigest": "sha256:" + HASH_A}
                    if delivery_mode == "fairmind_worker"
                    else {}
                ),
                "adapterName": "report-import",
                "adapterVersion": "1.0.0",
                "configurationSchema": {
                    "type": "object",
                    "required": ["threshold"],
                    "properties": {
                        "threshold": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        }
                    },
                    "additionalProperties": False,
                },
                "configurationDefaults": {"threshold": 0.5},
                "requiredInputRoles": ["scenario_set"],
                "budgets": {"maxCases": 200},
                "resultContractVersion": "1.0.0",
            },
        ).body
        service.activate_suite_version(
            org_id=org_id,
            suite_version_id=str(suite["id"]),
            actor_id=actor_id,
            idempotency_key=f"activate-suite-{token}",
        )
        plan = service.create_plan(
            org_id=org_id,
            system_id=system_id,
            actor_id=actor_id,
            idempotency_key=f"plan-{token}",
            payload={
                "contractVersion": "2.0.0",
                "name": "Imported evidence plan",
                "targetVersionId": str(target["id"]),
                "lifecyclePhases": ["pre_deploy"],
                "executionDepth": "deep",
                "enforcementMode": "human_approval",
                "deliveryMode": delivery_mode,
                "trustPolicyVersionId": policy_id,
                "suites": [{"suiteVersionId": str(suite["id"])}],
            },
        ).body
        service.activate_plan(
            org_id=org_id,
            system_id=system_id,
            plan_id=str(plan["id"]),
            actor_id=actor_id,
            idempotency_key=f"activate-plan-{token}",
        )
        run = service.create_run(
            org_id=org_id,
            system_id=system_id,
            plan_id=str(plan["id"]),
            actor_id=actor_id,
            idempotency_key=f"run-{token}",
            payload={"trigger": "manual", "lifecyclePhase": "pre_deploy"},
        ).body
        return {
            "token": token,
            "org_id": org_id,
            "actor_id": actor_id,
            "workspace_id": workspace_id,
            "system_id": system_id,
            "policy_id": policy_id,
            "run_id": str(run["id"]),
            "execution_id": str(run["suiteExecutions"][0]["id"]),
        }
    finally:
        session.close()


def _insert_postgresql_unverified_import(
    engine: object,
    graph: dict[str, str],
    *,
    capability_state: str = "available",
    assurance_source: str = "evaluation",
    evidence_run_binding: str | None = None,
    evidence_result: str = "passed",
    snapshot_result: str = "passed",
    snapshot_technical_status: str = "succeeded",
    evidence_content_hash: str = HASH_B,
    snapshot_content_hash: str = HASH_B,
    evidence_captured_offset_seconds: int = 0,
    admission_captured_offset_seconds: int = 0,
    evidence_expiry_offset_seconds: int = 0,
    snapshot_expiry_offset_seconds: int = 0,
    admission_expiry_offset_seconds: int = 0,
    revision_hash_override: str | None = None,
    checked_by: str = "fairmind/imported-evidence-service",
    reasons_json: str = '["unverified_import_manual_review"]',
    revision_created_by: str | None = None,
) -> str:
    from sqlalchemy import text

    from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256

    token = graph["token"]
    evidence_id = f"evidence-{token}"
    revision_id = f"revision-{token}"
    admission_id = f"admission-{token}"
    with engine.begin() as connection:
        imported_at = str(
            connection.scalar(text("SELECT fairmind_canonical_clock_utc_013f()"))
        )
        captured_at_value = datetime.fromisoformat(imported_at) + timedelta(
            seconds=evidence_captured_offset_seconds
        )
        captured_at = captured_at_value.isoformat(timespec="microseconds")
        exact_expires_at_value = captured_at_value + timedelta(days=1)
        evidence_expires_at = (
            exact_expires_at_value + timedelta(seconds=evidence_expiry_offset_seconds)
        ).isoformat(timespec="microseconds")
        snapshot_expires_at = (
            exact_expires_at_value + timedelta(seconds=snapshot_expiry_offset_seconds)
        ).isoformat(timespec="microseconds")
        admission_expires_at = (
            exact_expires_at_value + timedelta(seconds=admission_expiry_offset_seconds)
        ).isoformat(timespec="microseconds")
        admission_captured_at = (
            captured_at_value + timedelta(seconds=admission_captured_offset_seconds)
        ).isoformat(timespec="microseconds")
        authority = connection.execute(
            text(
                "SELECT run.envelope_id, run.envelope_hash, run.envelope_nonce, "
                "plan.id AS plan_id, plan.plan_content_hash, target.id AS target_id, "
                "target.subject_digest, target.manifest_digest, "
                "execution.id AS execution_id, execution.suite_version_id, "
                "execution.suite_owner_scope, execution.ordinal, suite.adapter_name, "
                "suite.adapter_version, suite.result_contract_version, "
                "policy.policy_hash, policy.maximum_evidence_age_seconds "
                "FROM governance_evaluation_runs AS run "
                "JOIN governance_evaluation_plans AS plan ON plan.id=run.plan_id "
                "JOIN governance_evaluation_target_versions AS target "
                "ON target.id=plan.target_version_id "
                "JOIN governance_evaluation_run_suite_executions AS execution "
                "ON execution.run_id=run.id "
                "JOIN governance_evaluation_suite_versions AS suite "
                "ON suite.id=execution.suite_version_id "
                "AND suite.owner_scope=execution.suite_owner_scope "
                "JOIN governance_evidence_trust_policy_versions AS policy "
                "ON policy.id=plan.trust_policy_version_id "
                "WHERE run.id=:run_id AND execution.id=:execution_id"
            ),
            graph,
        ).mappings().one()
        snapshot = {
            "schemaVersion": "1.0.0",
            "sourceType": "imported_report",
            "resultAuthority": "claimed",
            "humanReviewOnly": True,
            "decisionEvidenceEligible": False,
            "organizationId": graph["org_id"],
            "workspaceId": graph["workspace_id"],
            "systemId": graph["system_id"],
            "runId": graph["run_id"],
            "envelope": {
                "id": authority["envelope_id"],
                "hash": authority["envelope_hash"],
                "nonce": authority["envelope_nonce"],
            },
            "plan": {
                "id": authority["plan_id"],
                "contentHash": authority["plan_content_hash"],
                "deliveryMode": "imported_report",
            },
            "target": {
                "id": authority["target_id"],
                "subjectDigest": authority["subject_digest"],
                "manifestDigest": authority["manifest_digest"],
            },
            "suite": {
                "executionId": authority["execution_id"],
                "versionId": authority["suite_version_id"],
                "ownerScope": authority["suite_owner_scope"],
                "ordinal": authority["ordinal"],
                "adapterName": authority["adapter_name"],
                "adapterVersion": authority["adapter_version"],
                "resultContractVersion": authority["result_contract_version"],
            },
            "trustPolicy": {
                "id": graph["policy_id"],
                "hash": authority["policy_hash"],
                "maximumEvidenceAgeSeconds": authority[
                    "maximum_evidence_age_seconds"
                ],
                "unsignedImportPolicy": "manual_review",
            },
            "report": {
                "id": f"report-{token}",
                "contentHash": snapshot_content_hash,
                "capturedAt": captured_at,
                "effectiveExpiresAt": snapshot_expires_at,
                "claimedTechnicalStatus": snapshot_technical_status,
                "claimedEvidenceResultStatus": snapshot_result,
                "claimedResultSummary": {},
                "artifactRefs": [],
                "limitations": [],
            },
        }
        snapshot_json = canonical_json(snapshot)
        snapshot_hash = canonical_sha256(snapshot)
        provenance_json = canonical_json(
            {
                "sourceType": "imported_report",
                "resultAuthority": "claimed",
                "humanReviewOnly": True,
                "decisionEvidenceEligible": False,
                "importSnapshotHash": snapshot_hash,
            }
        )
        connection.execute(
            text(
                "INSERT INTO governance_evidence_runs "
                "(id, org_id, system_id, workspace_id, passport_id, schema_version, "
                "capability_state, assurance_source, source_type, source_identifier, "
                "run_id, content_hash, result, provenance_json, artifact_refs_json, "
                "limitations_json, captured_at, expires_at, evidence_id, created_at) "
                "VALUES (:id, :org_id, :system_id, :workspace_id, :passport_id, "
                "'2.0.0', :capability_state, :assurance_source, 'imported_report', "
                ":source_identifier, :source_run_id, :content_hash, :result, "
                ":provenance_json, '[]', '[]', :captured_at, :expires_at, NULL, "
                ":imported_at)"
            ),
            {
                "id": evidence_id,
                "org_id": graph["org_id"],
                "system_id": graph["system_id"],
                "workspace_id": graph["workspace_id"],
                "passport_id": f"passport-{token}",
                "capability_state": capability_state,
                "assurance_source": assurance_source,
                "source_identifier": f"report-{token}",
                "source_run_id": evidence_run_binding or graph["execution_id"],
                "content_hash": evidence_content_hash,
                "result": evidence_result,
                "provenance_json": provenance_json,
                "captured_at": captured_at,
                "expires_at": evidence_expires_at,
                "imported_at": imported_at,
            },
        )
        connection.execute(
            text(
                "INSERT INTO governance_evidence_passport_revisions "
                "(id, org_id, system_id, evidence_run_id, passport_id, "
                "passport_revision, previous_revision_hash, canonical_content_hash, "
                "snapshot_json, created_by, created_at) "
                "VALUES (:id, :org_id, :system_id, :evidence_id, :passport_id, 1, "
                "NULL, :content_hash, :snapshot_json, :actor_id, :imported_at)"
            ),
            {
                "id": revision_id,
                "org_id": graph["org_id"],
                "system_id": graph["system_id"],
                "evidence_id": evidence_id,
                "passport_id": f"passport-{token}",
                "content_hash": revision_hash_override or snapshot_hash,
                "snapshot_json": snapshot_json,
                "actor_id": revision_created_by or graph["actor_id"],
                "imported_at": imported_at,
            },
        )
        connection.execute(
            text(
                "INSERT INTO governance_evidence_admissions "
                "(id, org_id, workspace_id, system_id, evidence_run_id, "
                "passport_revision_id, trust_policy_version_id, suite_execution_id, "
                "envelope_hash, admission_status, freshness_status, issuer_id, "
                "signing_key_id, signer_key_id, signer_algorithm, reasons_json, "
                "checked_by, checked_at, created_at, contract_version, run_id, "
                "envelope_id, envelope_nonce, submitted_by, captured_at, signed_at, "
                "effective_expires_at) "
                "SELECT :admission_id, run.org_id, run.workspace_id, run.system_id, "
                ":evidence_id, :revision_id, :policy_id, :execution_id, "
                "run.envelope_hash, 'unverified', 'current', NULL, NULL, NULL, NULL, "
                ":reasons_json, :checked_by, :checked_at, :checked_at, "
                "'2.0.0', run.id, "
                "run.envelope_id, run.envelope_nonce, :actor_id, :captured_at, NULL, "
                ":expires_at FROM governance_evaluation_runs AS run "
                "WHERE run.id=:run_id AND run.org_id=:org_id "
                "AND run.workspace_id=:workspace_id AND run.system_id=:system_id"
            ),
            {
                "admission_id": admission_id,
                "evidence_id": evidence_id,
                "revision_id": revision_id,
                "policy_id": graph["policy_id"],
                "execution_id": graph["execution_id"],
                "checked_at": imported_at,
                "checked_by": checked_by,
                "reasons_json": reasons_json,
                "actor_id": graph["actor_id"],
                "captured_at": admission_captured_at,
                "expires_at": admission_expires_at,
                "run_id": graph["run_id"],
                "org_id": graph["org_id"],
                "workspace_id": graph["workspace_id"],
                "system_id": graph["system_id"],
            },
        )
    return admission_id


def _project_postgresql_unverified_import(
    engine: object,
    graph: dict[str, str],
    *,
    technical_status: str = "succeeded",
    evidence_result_status: str = "passed",
    claim_actor_override: str | None = None,
) -> None:
    from sqlalchemy import text

    token = graph["token"]
    admission_id = f"admission-{token}"
    evidence_id = f"evidence-{token}"
    revision_id = f"revision-{token}"
    claim_id = f"claim-{token}"
    link_id = f"link-{token}"
    with engine.begin() as connection:
        admission = connection.execute(
            text(
                "SELECT * FROM governance_evidence_admissions "
                "WHERE id=:admission_id"
            ),
            {"admission_id": admission_id},
        ).mappings().one()
        actor_id = admission["submitted_by"]
        linked_at = admission["checked_at"]
        connection.execute(
            text(
                "INSERT INTO governance_evidence_nonce_claims "
                "(id, org_id, workspace_id, system_id, run_id, "
                "run_contract_version, suite_execution_id, admission_id, "
                "admission_contract_version, evidence_run_id, "
                "passport_revision_id, envelope_id, envelope_hash, "
                "envelope_nonce, claimed_by, claimed_at) VALUES "
                "(:id, :org_id, :workspace_id, :system_id, :run_id, '2.0.0', "
                ":execution_id, :admission_id, '2.0.0', :evidence_id, "
                ":revision_id, :envelope_id, :envelope_hash, :envelope_nonce, "
                ":actor_id, :linked_at)"
            ),
            {
                "id": claim_id,
                "org_id": graph["org_id"],
                "workspace_id": graph["workspace_id"],
                "system_id": graph["system_id"],
                "run_id": graph["run_id"],
                "execution_id": graph["execution_id"],
                "admission_id": admission_id,
                "evidence_id": evidence_id,
                "revision_id": revision_id,
                "envelope_id": admission["envelope_id"],
                "envelope_hash": admission["envelope_hash"],
                "envelope_nonce": admission["envelope_nonce"],
                "actor_id": claim_actor_override or actor_id,
                "linked_at": linked_at,
            },
        )
        connection.execute(
            text(
                "INSERT INTO governance_evaluation_suite_evidence_links "
                "(id, org_id, workspace_id, system_id, run_id, "
                "suite_execution_id, admission_id, admission_contract_version, "
                "evidence_run_id, passport_revision_id, nonce_claim_id, linked_by, "
                "linked_at) VALUES (:id, :org_id, :workspace_id, :system_id, "
                ":run_id, :execution_id, :admission_id, '2.0.0', :evidence_id, "
                ":revision_id, :claim_id, :actor_id, :linked_at)"
            ),
            {
                "id": link_id,
                "org_id": graph["org_id"],
                "workspace_id": graph["workspace_id"],
                "system_id": graph["system_id"],
                "run_id": graph["run_id"],
                "execution_id": graph["execution_id"],
                "admission_id": admission_id,
                "evidence_id": evidence_id,
                "revision_id": revision_id,
                "claim_id": claim_id,
                "actor_id": actor_id,
                "linked_at": linked_at,
            },
        )
        updated_at = str(
            connection.scalar(text("SELECT fairmind_canonical_clock_utc_013f()"))
        )
        connection.execute(
            text(
                "UPDATE governance_evaluation_run_suite_executions SET "
                "technical_status=:technical_status, "
                "evidence_result_status=:evidence_result_status, "
                "admission_status='unverified', review_status='pending', "
                "freshness_status='current', evidence_run_id=:evidence_id, "
                "passport_revision_id=:revision_id, linked_by=:actor_id, "
                "linked_at=:linked_at, result_summary_json='{}', "
                "limitations_json='[]', started_at=:updated_at, "
                "completed_at=:updated_at, updated_at=:updated_at "
                "WHERE id=:execution_id"
            ),
            {
                "technical_status": technical_status,
                "evidence_result_status": evidence_result_status,
                "evidence_id": evidence_id,
                "revision_id": revision_id,
                "actor_id": actor_id,
                "linked_at": linked_at,
                "updated_at": updated_at,
                "execution_id": graph["execution_id"],
            },
        )


def test_native_postgresql_013i_rejects_cross_mode_direct_sql(
    postgresql_013i_engine: object,
) -> None:
    from sqlalchemy.exc import DBAPIError

    graph = _seed_postgresql_run(
        postgresql_013i_engine,
        delivery_mode="external_provider",
    )
    with pytest.raises(
        DBAPIError,
        match="unverified evidence delivery binding failed",
    ):
        _insert_postgresql_unverified_import(postgresql_013i_engine, graph)


def test_native_postgresql_013i_allows_exact_import_without_receipt(
    postgresql_013i_engine: object,
) -> None:
    from sqlalchemy import text

    graph = _seed_postgresql_run(
        postgresql_013i_engine,
        delivery_mode="imported_report",
    )
    admission_id = _insert_postgresql_unverified_import(
        postgresql_013i_engine,
        graph,
    )
    with postgresql_013i_engine.connect() as connection:
        assert connection.scalar(
            text(
                "SELECT count(*) FROM governance_evidence_verification_receipts "
                "WHERE admission_id=:admission_id"
            ),
            {"admission_id": admission_id},
        ) == 0


def test_native_postgresql_013i_allows_exact_initial_unverified_projection(
    postgresql_013i_engine: object,
) -> None:
    graph = _seed_postgresql_run(
        postgresql_013i_engine,
        delivery_mode="imported_report",
    )
    _insert_postgresql_unverified_import(postgresql_013i_engine, graph)
    _project_postgresql_unverified_import(postgresql_013i_engine, graph)


def test_native_postgresql_013i_rejects_claimed_technical_projection_mismatch(
    postgresql_013i_engine: object,
) -> None:
    from sqlalchemy.exc import DBAPIError

    graph = _seed_postgresql_run(
        postgresql_013i_engine,
        delivery_mode="imported_report",
    )
    _insert_postgresql_unverified_import(postgresql_013i_engine, graph)
    with pytest.raises(
        DBAPIError,
        match="unverified evidence delivery binding failed",
    ):
        _project_postgresql_unverified_import(
            postgresql_013i_engine,
            graph,
            technical_status="failed",
            evidence_result_status="failed",
        )


@pytest.mark.parametrize(
    ("import_overrides", "case"),
    [
        ({"evidence_run_binding": "foreign-execution"}, "cross execution"),
        ({"evidence_result": "failed"}, "result mismatch"),
        ({"evidence_content_hash": HASH_A}, "content mismatch"),
        ({"admission_captured_offset_seconds": -1}, "captured mismatch"),
        ({"evidence_expiry_offset_seconds": -1}, "expiry mismatch"),
        ({"revision_hash_override": HASH_A}, "snapshot hash mismatch"),
        ({"evidence_captured_offset_seconds": -60}, "pre-execution capture"),
        (
            {
                "evidence_result": "pending",
                "snapshot_result": "pending",
                "snapshot_technical_status": "running",
            },
            "nonterminal claimed result",
        ),
    ],
)
def test_native_postgresql_013i_rejects_snapshot_laundering(
    postgresql_013i_engine: object,
    import_overrides: dict[str, object],
    case: str,
) -> None:
    """Each case is a direct-writer mutation of one otherwise exact import graph."""

    from sqlalchemy.exc import DBAPIError

    graph = _seed_postgresql_run(
        postgresql_013i_engine,
        delivery_mode="imported_report",
    )
    with pytest.raises(
        DBAPIError,
        match="unverified evidence delivery binding failed",
    ):
        _insert_postgresql_unverified_import(
            postgresql_013i_engine,
            graph,
            **import_overrides,
        )


@pytest.mark.parametrize(
    "import_overrides",
    [
        {"checked_by": "direct-writer"},
        {"reasons_json": '["caller_asserted"]'},
        {"revision_created_by": "different-actor"},
    ],
)
def test_native_postgresql_013i_rejects_import_attribution_laundering(
    postgresql_013i_engine: object,
    import_overrides: dict[str, str],
) -> None:
    from sqlalchemy.exc import DBAPIError

    graph = _seed_postgresql_run(
        postgresql_013i_engine,
        delivery_mode="imported_report",
    )
    with pytest.raises(
        DBAPIError,
        match="unverified evidence delivery binding failed",
    ):
        _insert_postgresql_unverified_import(
            postgresql_013i_engine,
            graph,
            **import_overrides,
        )


def test_native_postgresql_013i_rejects_claim_actor_laundering(
    postgresql_013i_engine: object,
) -> None:
    from sqlalchemy.exc import DBAPIError

    graph = _seed_postgresql_run(
        postgresql_013i_engine,
        delivery_mode="imported_report",
    )
    _insert_postgresql_unverified_import(postgresql_013i_engine, graph)
    with pytest.raises(
        DBAPIError,
        match="unverified evidence delivery binding failed",
    ):
        _project_postgresql_unverified_import(
            postgresql_013i_engine,
            graph,
            claim_actor_override="different-actor",
        )


@pytest.mark.parametrize(
    ("evidence_overrides", "case"),
    [
        ({"capability_state": "unavailable"}, "unavailable"),
        ({"assurance_source": "user_asserted"}, "non-evaluation"),
    ],
)
def test_native_postgresql_013i_rejects_non_authoritative_evidence_shape(
    postgresql_013i_engine: object,
    evidence_overrides: dict[str, str],
    case: str,
) -> None:
    from sqlalchemy.exc import DBAPIError

    graph = _seed_postgresql_run(
        postgresql_013i_engine,
        delivery_mode="imported_report",
    )
    with pytest.raises(
        DBAPIError,
        match="unverified evidence delivery binding failed",
    ):
        _insert_postgresql_unverified_import(
            postgresql_013i_engine,
            graph,
            **evidence_overrides,
        )


@pytest.mark.parametrize("authority", ["plan", "target", "suite"])
def test_native_postgresql_013i_rejects_inactive_bound_authority(
    postgresql_013i_engine: object,
    authority: str,
) -> None:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    graph = _seed_postgresql_run(
        postgresql_013i_engine,
        delivery_mode="imported_report",
    )
    with postgresql_013i_engine.begin() as connection:
        ids = connection.execute(
            text(
                "SELECT run.plan_id, plan.target_version_id, "
                "execution.suite_version_id "
                "FROM governance_evaluation_runs AS run "
                "JOIN governance_evaluation_plans AS plan ON plan.id=run.plan_id "
                "JOIN governance_evaluation_run_suite_executions AS execution "
                "ON execution.run_id=run.id WHERE run.id=:run_id"
            ),
            graph,
        ).mappings().one()
        if authority == "plan":
            updated_at = str(
                connection.scalar(
                    text("SELECT fairmind_canonical_clock_utc_013f()")
                )
            )
            connection.execute(
                text(
                    "UPDATE governance_evaluation_plans SET status='archived', "
                    "updated_by=:actor_id, updated_at=:updated_at WHERE id=:id"
                ),
                {
                    "actor_id": graph["actor_id"],
                    "updated_at": updated_at,
                    "id": ids["plan_id"],
                },
            )
        elif authority == "target":
            connection.execute(
                text(
                    "UPDATE governance_evaluation_target_versions "
                    "SET status='retired' WHERE id=:id"
                ),
                {"id": ids["target_version_id"]},
            )
        else:
            connection.execute(
                text(
                    "UPDATE governance_evaluation_suite_versions "
                    "SET status='deprecated' WHERE id=:id"
                ),
                {"id": ids["suite_version_id"]},
            )
    with pytest.raises(
        DBAPIError,
        match="unverified evidence delivery binding failed",
    ):
        _insert_postgresql_unverified_import(postgresql_013i_engine, graph)


def test_native_postgresql_013i_rejects_reject_and_retired_policy(
    postgresql_013i_engine: object,
) -> None:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    reject_graph = _seed_postgresql_run(
        postgresql_013i_engine,
        delivery_mode="imported_report",
        unsigned_import_policy="reject",
    )
    with pytest.raises(DBAPIError):
        _insert_postgresql_unverified_import(postgresql_013i_engine, reject_graph)

    retired_graph = _seed_postgresql_run(
        postgresql_013i_engine,
        delivery_mode="imported_report",
    )
    with postgresql_013i_engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE governance_evidence_trust_policy_versions "
                "SET status='retired', retired_by=:actor_id, "
                "retirement_reason='native 013i inactive-policy proof' "
                "WHERE id=:policy_id AND org_id=:org_id"
            ),
            retired_graph,
        )
    with pytest.raises(DBAPIError):
        _insert_postgresql_unverified_import(postgresql_013i_engine, retired_graph)


def test_native_postgresql_013k_preserves_exact_unverified_import_links(
    postgresql_013i_engine: object,
) -> None:
    """013k must layer verified-link authority without replacing the 013b/013i path."""
    from sqlalchemy import text

    with postgresql_013i_engine.begin() as connection:
        schema_name = str(connection.scalar(text("SELECT current_schema()")))
        for migration_name in (
            "013j_owner_decision_override_integrity.sql",
            "013k_verified_evidence_link_integrity.sql",
        ):
            connection.execute(
                text(
                    "SELECT pg_catalog.set_config"
                    "('fairmind.migration_schema', :schema_name, false)"
                ),
                {"schema_name": schema_name},
            )
            connection.execute(
                text((MIGRATIONS / migration_name).read_text(encoding="utf-8"))
            )

    graph = _seed_postgresql_run(
        postgresql_013i_engine,
        delivery_mode="imported_report",
    )
    _insert_postgresql_unverified_import(postgresql_013i_engine, graph)
    _project_postgresql_unverified_import(postgresql_013i_engine, graph)

    with postgresql_013i_engine.connect() as connection:
        assert connection.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_suite_evidence_links "
                "WHERE suite_execution_id=:execution_id"
            ),
            graph,
        ) == 1
