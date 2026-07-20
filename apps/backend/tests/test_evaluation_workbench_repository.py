"""Persistence and atomicity tests for assurance-contract v2."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import uuid

import pytest
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base, DatabaseManager
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
from database.models import Organization, OrganizationMember, User
import src.application.services.evaluation_workbench_service as evaluation_service_module
import src.domain.assurance.evaluation_v2 as evaluation_v2_module
from src.application.services.evaluation_workbench_service import (
    EvaluationWorkbenchError,
    EvaluationWorkbenchService,
    assurance_request_hash,
)
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    canonical_sha256,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchRepository,
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)

ORG = str(uuid.uuid4())
OTHER_ORG = str(uuid.uuid4())
USER = str(uuid.uuid4())


def _service(
    session,
    repository: SqlAlchemyEvaluationWorkbenchRepository | None = None,
) -> EvaluationWorkbenchService:
    return EvaluationWorkbenchService(
        SqlAlchemyEvaluationWorkbenchUnitOfWork(
            session,
            repository=repository,
        )
    )


@pytest.fixture
def repository_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys = ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    user_uuid = uuid.UUID(USER)
    session.execute(
        User.__table__.insert().values(id=user_uuid, email="actor@example.test", username=USER)
    )
    for org_id, workspace_id, system_id in (
        (ORG, "workspace-a", "system-a"),
        (OTHER_ORG, "workspace-b", "system-b"),
    ):
        session.execute(
            Organization.__table__.insert().values(
                id=uuid.UUID(org_id), name=org_id, slug=org_id, owner_id=user_uuid
            )
        )
        session.execute(
            OrganizationMember.__table__.insert().values(
                id=uuid.uuid4(),
                org_id=uuid.UUID(org_id),
                user_id=user_uuid,
                role="admin",
                status="active",
            )
        )
        session.execute(
            GovernanceWorkspace.__table__.insert().values(
                id=workspace_id, org_id=org_id, name=workspace_id
            )
        )
        session.execute(
            GovernanceAISystem.__table__.insert().values(
                id=system_id,
                workspace_id=workspace_id,
                org_id=org_id,
                name=system_id,
            )
        )
    session.execute(
        GovernanceEvidenceTrustPolicyVersion.__table__.insert().values(
            id="trust-a",
            org_id=ORG,
            version="1.0.0",
            policy_json="{}",
            policy_hash=canonical_sha256({}),
            maximum_evidence_age_seconds=86400,
            unsigned_import_policy="manual_review",
            status="active",
            created_by=USER,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )
    session.commit()
    try:
        yield session, factory
    finally:
        session.close()
        engine.dispose()


def _target_payload(key: str = "agent-prod") -> dict:
    return {
        "targetKey": key,
        "targetKind": "agent",
        "version": "1.0.0",
        "systemVersion": "2026.07",
        "subjectKind": "agent",
        "subjectId": key,
        "subjectVersion": "sha-1",
        "subjectDigest": "b" * 64,
        "deploymentId": "deploy-1",
        "connectorBindingId": "connector-1",
        "manifest": {
            "schemaVersion": "2.0.0",
            "inputs": {
                "scenario_set": {"kind": "content_digest", "sha256": "c" * 64}
            },
        },
    }


def _suite_payload(name: str = "agent-safety") -> dict:
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
            "properties": {
                "threshold": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "additionalProperties": False,
        },
        "configurationDefaults": {"threshold": 0.5},
        "requiredInputRoles": ["scenario_set"],
        "budgets": {"maxCases": 200},
        "resultContractVersion": "1.0.0",
    }


def _plan_payload(target_id: str, suite_ids: list[str]) -> dict:
    return {
        "contractVersion": "2.0.0",
        "name": "Agent release assurance",
        "targetVersionId": target_id,
        "lifecyclePhases": ["pre_deploy"],
        "executionDepth": "deep",
        "enforcementMode": "human_approval",
        "deliveryMode": "external_provider",
        "trustPolicyVersionId": "trust-a",
        "suites": [{"suiteVersionId": suite_id} for suite_id in suite_ids],
    }


def _create_bound_catalog(service: EvaluationWorkbenchService, *, suites: int = 1):
    target = service.create_target_version(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="target-key",
        payload=_target_payload(),
    ).body
    suite_ids = []
    for index in range(suites):
        suite = service.create_suite_version(
            org_id=ORG,
            actor_id=USER,
            idempotency_key=f"suite-key-{index}",
            payload=_suite_payload(f"suite-{index}"),
        ).body
        activated = service.activate_suite_version(
            org_id=ORG,
            suite_version_id=suite["id"],
            actor_id=USER,
            idempotency_key=f"suite-activate-{index}",
        )
        assert activated and activated.body["status"] == "active"
        suite_ids.append(suite["id"])
    return target, suite_ids


def test_plan_and_run_are_bound_atomically_to_exact_suite_versions(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target, suite_ids = _create_bound_catalog(service, suites=2)
    plan_result = service.create_plan(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="plan-key",
        payload=_plan_payload(target["id"], suite_ids),
    )
    plan = plan_result.body
    assert plan_result.status == 201
    assert plan["contractVersion"] == "2.0.0"
    assert len(plan["suites"]) == 2
    assert len(plan["planContentHash"]) == 64
    service.activate_plan(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key="plan-activate",
    )
    run = service.create_run(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key="run-key",
        payload={"trigger": "release_gate", "lifecyclePhase": "pre_deploy"},
    ).body
    assert run["technicalStatus"] == "awaiting_evidence"
    assert run["evidenceOutcome"] == "pending"
    assert run["overallVerdict"] == "insufficient"
    assert len(run["suiteExecutions"]) == 2
    assert len({item["id"] for item in run["suiteExecutions"]}) == 2
    assert run["layerVerdicts"] == {
        execution["id"]: "insufficient" for execution in run["suiteExecutions"]
    }
    assert len(run["envelopeHash"]) == 64
    assert run["envelope"]["runId"] == run["id"]
    assert [item["ordinal"] for item in run["suiteExecutions"]] == [0, 1]
    stored_run = (
        session.execute(
            select(GovernanceEvaluationRun.__table__).where(
                GovernanceEvaluationRun.__table__.c.id == run["id"]
            )
        )
        .mappings()
        .one()
    )
    assert stored_run["contract_version"] == "2.0.0"
    assert stored_run["linked_passport_revision_id"] is None


def test_activation_does_not_repeat_phase_independent_configuration_validation(
    repository_fixture,
    monkeypatch,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target = service.create_target_version(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="three-phase-target",
        payload=_target_payload("three-phase-agent"),
    ).body
    suite_payload = _suite_payload("three-phase-suite")
    suite_payload["lifecyclePhases"] = ["pre_deploy", "realtime", "post_deploy"]
    suite = service.create_suite_version(
        org_id=ORG,
        actor_id=USER,
        idempotency_key="three-phase-suite",
        payload=suite_payload,
    ).body
    service.activate_suite_version(
        org_id=ORG,
        suite_version_id=suite["id"],
        actor_id=USER,
        idempotency_key="three-phase-suite-activate",
    )
    plan_payload = _plan_payload(target["id"], [suite["id"]])
    plan_payload["lifecyclePhases"] = ["pre_deploy", "realtime", "post_deploy"]
    plan = service.create_plan(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="three-phase-plan",
        payload=plan_payload,
    ).body
    calls = 0
    original_validate = evaluation_v2_module.validate_suite_configuration

    def counting_validate(schema, configuration):
        nonlocal calls
        calls += 1
        return original_validate(schema, configuration)

    monkeypatch.setattr(
        evaluation_v2_module,
        "validate_suite_configuration",
        counting_validate,
    )

    service.activate_plan(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key="three-phase-plan-activate",
    )

    assert calls == 0


def test_plan_schema_complexity_is_rejected_before_plan_persistence(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target = service.create_target_version(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="complexity-target",
        payload=_target_payload("complexity-agent"),
    ).body
    schema = {
        "type": "object",
        "properties": {
            f"flag_{index}": {"type": "boolean"} for index in range(180)
        },
        "additionalProperties": False,
    }
    suite_ids = []
    for index in range(32):
        suite_payload = _suite_payload(f"complexity-suite-{index}")
        suite_payload["configurationSchema"] = schema
        suite_payload["configurationDefaults"] = {}
        suite = service.create_suite_version(
            org_id=ORG,
            actor_id=USER,
            idempotency_key=f"complexity-suite-{index}",
            payload=suite_payload,
        ).body
        service.activate_suite_version(
            org_id=ORG,
            suite_version_id=suite["id"],
            actor_id=USER,
            idempotency_key=f"complexity-suite-activate-{index}",
        )
        suite_ids.append(suite["id"])
    idempotency_before = session.scalar(
        select(func.count()).select_from(GovernanceIdempotencyRecord.__table__)
    )
    audit_before = session.scalar(
        select(func.count()).select_from(GovernanceEvaluationAuditEvent.__table__)
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.create_plan(
            org_id=ORG,
            system_id="system-a",
            actor_id=USER,
            idempotency_key="complexity-plan",
            payload=_plan_payload(target["id"], suite_ids),
        )

    assert caught.value.code == "plan_schema_complexity_exceeded"
    assert caught.value.status_code == 422
    assert session.scalar(
        select(func.count()).select_from(GovernanceEvaluationPlan.__table__)
    ) == 0
    assert session.scalar(
        select(func.count()).select_from(GovernanceIdempotencyRecord.__table__)
    ) == idempotency_before
    assert session.scalar(
        select(func.count()).select_from(GovernanceEvaluationAuditEvent.__table__)
    ) == audit_before


def test_envelope_size_preflight_blocks_activation_and_run_before_persistence(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    roles = [f"input_{index:02d}" for index in range(32)]
    target_payload = _target_payload("large-envelope-agent")
    target_payload["manifest"]["inputs"] = {
        role: {
            "kind": "content_digest",
            "sha256": "c" * 64,
            "mediaType": "video/mp4",
            "sizeBytes": 2**53 - 1,
        }
        for role in roles
    }
    target = service.create_target_version(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="large-envelope-target",
        payload=target_payload,
    ).body
    schema = {
        "type": "object",
        "properties": {
            "checks": {
                "type": "array",
                "maxItems": 1360,
                "items": {"type": "boolean"},
            }
        },
        "required": ["checks"],
        "additionalProperties": False,
    }
    configuration = {"checks": [False] * 1360}
    suite_ids = []
    for index in range(32):
        suite_payload = _suite_payload(f"large-envelope-{index}")
        suite_payload.update(
            {
                "configurationSchema": schema,
                "configurationDefaults": {"checks": []},
                "requiredInputRoles": roles,
            }
        )
        suite = service.create_suite_version(
            org_id=ORG,
            actor_id=USER,
            idempotency_key=f"large-envelope-suite-{index}",
            payload=suite_payload,
        ).body
        service.activate_suite_version(
            org_id=ORG,
            suite_version_id=suite["id"],
            actor_id=USER,
            idempotency_key=f"large-envelope-suite-activate-{index}",
        )
        suite_ids.append(suite["id"])

    plan_payload = _plan_payload(target["id"], suite_ids)
    plan_payload["suites"] = [
        {"suiteVersionId": suite_id, "configuration": configuration}
        for suite_id in suite_ids
    ]
    plan = service.create_plan(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="large-envelope-plan",
        payload=plan_payload,
    ).body
    idempotency_before_activation = session.scalar(
        select(func.count()).select_from(GovernanceIdempotencyRecord)
    )

    with pytest.raises(EvaluationWorkbenchError) as activation_error:
        service.activate_plan(
            org_id=ORG,
            system_id="system-a",
            plan_id=plan["id"],
            actor_id=USER,
            idempotency_key="large-envelope-plan-activate",
        )
    assert activation_error.value.code == "preflight_failed"
    assert "execution_envelope_size_exceeded" in {
        blocker["code"] for blocker in activation_error.value.details["blockers"]
    }
    assert session.scalar(
        select(GovernanceEvaluationPlan.__table__.c.status).where(
            GovernanceEvaluationPlan.__table__.c.id == plan["id"]
        )
    ) == "draft"
    assert session.scalar(
        select(func.count()).select_from(GovernanceIdempotencyRecord)
    ) == idempotency_before_activation

    session.execute(
        GovernanceEvaluationPlan.__table__.update()
        .where(GovernanceEvaluationPlan.__table__.c.id == plan["id"])
        .values(status="active")
    )
    session.commit()
    idempotency_before_run = session.scalar(
        select(func.count()).select_from(GovernanceIdempotencyRecord)
    )
    with pytest.raises(EvaluationWorkbenchError) as run_error:
        service.create_run(
            org_id=ORG,
            system_id="system-a",
            plan_id=plan["id"],
            actor_id=USER,
            idempotency_key="large-envelope-run",
            payload={"trigger": "manual", "lifecyclePhase": "pre_deploy"},
        )
    assert run_error.value.code == "preflight_failed"
    assert "execution_envelope_size_exceeded" in {
        blocker["code"] for blocker in run_error.value.details["blockers"]
    }
    assert (
        session.scalar(
            select(func.count()).select_from(GovernanceEvaluationRun.__table__)
        )
        == 0
    )
    assert session.scalar(
        select(func.count()).select_from(GovernanceIdempotencyRecord)
    ) == idempotency_before_run


def test_actual_envelope_overflow_returns_compact_409_without_persistence(
    repository_fixture,
    monkeypatch,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target, suite_ids = _create_bound_catalog(service)
    plan = service.create_plan(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="actual-overflow-plan",
        payload=_plan_payload(target["id"], suite_ids),
    ).body
    service.activate_plan(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key="actual-overflow-activate",
    )
    idempotency_before = session.scalar(
        select(func.count()).select_from(GovernanceIdempotencyRecord.__table__)
    )

    def reject_actual_overflow(**_kwargs):
        raise AssuranceContractValidationError(
            "execution_envelope_too_large",
            "sensitive internal size detail",
        )

    monkeypatch.setattr(
        evaluation_service_module,
        "build_execution_envelope_v2",
        reject_actual_overflow,
    )
    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.create_run(
            org_id=ORG,
            system_id="system-a",
            plan_id=plan["id"],
            actor_id=USER,
            idempotency_key="actual-overflow-run",
            payload={"trigger": "manual", "lifecyclePhase": "pre_deploy"},
        )

    assert caught.value.detail() == {
        "code": "execution_envelope_size_exceeded",
        "message": "The execution envelope exceeds the bounded assurance contract.",
    }
    assert caught.value.status_code == 409
    assert (
        session.scalar(
            select(func.count()).select_from(GovernanceEvaluationRun.__table__)
        )
        == 0
    )
    assert (
        session.scalar(
            select(func.count()).select_from(GovernanceIdempotencyRecord.__table__)
        )
        == idempotency_before
    )


def test_exact_idempotency_replay_returns_original_and_conflict_is_rejected(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    first = service.create_target_version(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="same-key",
        payload=_target_payload(),
    )
    replay = service.create_target_version(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="same-key",
        payload=_target_payload(),
    )
    assert replay.replayed is True
    assert replay.body == first.body
    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.create_target_version(
            org_id=ORG,
            system_id="system-a",
            actor_id=USER,
            idempotency_key="same-key",
            payload=_target_payload("different-target"),
        )
    assert caught.value.code == "idempotency_conflict"
    assert session.scalar(select(func.count()).select_from(GovernanceEvaluationTargetVersion)) == 1
    assert session.scalar(select(func.count()).select_from(GovernanceIdempotencyRecord)) == 1
    assert session.scalar(select(func.count()).select_from(GovernanceEvaluationAuditEvent)) == 1


def test_scope_isolation_hides_other_organization_catalog(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target = service.create_target_version(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="target-key",
        payload=_target_payload(),
    ).body
    assert (
        service.get_target_version(
            org_id=OTHER_ORG, system_id="system-b", target_version_id=target["id"]
        )
        is None
    )
    assert service.list_target_versions(org_id=OTHER_ORG, system_id="system-b") == []


def test_audit_failure_rolls_back_resource_idempotency_and_chain(
    repository_fixture, monkeypatch
) -> None:
    session, _ = repository_fixture
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)

    def fail_audit(**_kwargs):
        raise RuntimeError("audit unavailable")

    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(
        session,
        repository=repository,
    )
    monkeypatch.setattr(unit_of_work, "_append_audit", fail_audit)
    service = EvaluationWorkbenchService(unit_of_work)
    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.create_target_version(
            org_id=ORG,
            system_id="system-a",
            actor_id=USER,
            idempotency_key="target-key",
            payload=_target_payload(),
        )
    assert caught.value.code == "evaluation_persistence_failed"
    assert session.scalar(select(func.count()).select_from(GovernanceEvaluationTargetVersion)) == 0
    assert session.scalar(select(func.count()).select_from(GovernanceIdempotencyRecord)) == 0
    assert session.scalar(select(func.count()).select_from(GovernanceEvaluationAuditEvent)) == 0


def test_plan_scope_and_foreign_keys_reject_cross_system_bindings(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target, suite_ids = _create_bound_catalog(service)
    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.create_plan(
            org_id=OTHER_ORG,
            system_id="system-b",
            actor_id=USER,
            idempotency_key="cross-scope-plan",
            payload={
                **_plan_payload(target["id"], suite_ids),
                "trustPolicyVersionId": "trust-a",
            },
        )
    assert caught.value.code == "binding_scope_mismatch"
    assert session.scalar(select(func.count()).select_from(GovernanceEvaluationPlan)) == 0
    assert session.scalar(select(func.count()).select_from(GovernanceEvaluationPlanSuite)) == 0


def test_target_supersession_blocks_old_plan_and_enforces_lineage(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target, suite_ids = _create_bound_catalog(service)
    plan = service.create_plan(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="superseded-plan",
        payload=_plan_payload(target["id"], suite_ids),
    ).body
    service.activate_plan(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key="superseded-plan-activate",
    )

    replacement_payload = {
        **_target_payload(),
        "version": "2.0.0",
        "subjectVersion": "sha-2",
        "subjectDigest": "d" * 64,
        "supersedesId": target["id"],
    }
    replacement = service.create_target_version(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="replacement-target",
        payload=replacement_payload,
    ).body

    assert replacement["supersedesId"] == target["id"]
    stored_prior = (
        session.execute(
            select(GovernanceEvaluationTargetVersion.__table__).where(
                GovernanceEvaluationTargetVersion.id == target["id"]
            )
        )
        .mappings()
        .one()
    )
    assert stored_prior["status"] == "superseded"
    preflight = service.preflight(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        lifecycle_phase="pre_deploy",
    )
    assert preflight is not None
    assert preflight["canCreateRun"] is False
    assert "target_not_active" in {blocker["code"] for blocker in preflight["blockers"]}

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.create_target_version(
            org_id=ORG,
            system_id="system-a",
            actor_id=USER,
            idempotency_key="wrong-lineage-target",
            payload={
                **_target_payload("different-target"),
                "version": "3.0.0",
                "supersedesId": replacement["id"],
            },
        )
    assert caught.value.code == "supersedes_lineage_mismatch"
    assert caught.value.status_code == 422


def test_catalog_identity_conflicts_return_stable_409(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    service.create_target_version(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="target-first",
        payload=_target_payload(),
    )
    with pytest.raises(EvaluationWorkbenchError) as target_conflict:
        service.create_target_version(
            org_id=ORG,
            system_id="system-a",
            actor_id=USER,
            idempotency_key="target-second",
            payload=_target_payload(),
        )
    assert target_conflict.value.code == "immutable_version_conflict"
    assert target_conflict.value.status_code == 409

    service.create_suite_version(
        org_id=ORG,
        actor_id=USER,
        idempotency_key="suite-first",
        payload=_suite_payload(),
    )
    with pytest.raises(EvaluationWorkbenchError) as suite_conflict:
        service.create_suite_version(
            org_id=ORG,
            actor_id=USER,
            idempotency_key="suite-second",
            payload=_suite_payload(),
        )
    assert suite_conflict.value.code == "immutable_version_conflict"
    assert suite_conflict.value.status_code == 409


def test_audit_hash_chain_recomputes_from_stored_rows(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    service.create_target_version(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="audit-target-one",
        payload=_target_payload("target-one"),
    )
    service.create_target_version(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="audit-target-two",
        payload=_target_payload("target-two"),
    )

    events = (
        session.execute(
            select(GovernanceEvaluationAuditEvent.__table__)
            .where(GovernanceEvaluationAuditEvent.org_id == ORG)
            .order_by(GovernanceEvaluationAuditEvent.sequence_number)
        )
        .mappings()
        .all()
    )
    previous_hash = None
    for expected_sequence, event_row in enumerate(events, start=1):
        projection = {
            "eventId": event_row["id"],
            "organizationId": event_row["org_id"],
            "sequenceNumber": event_row["sequence_number"],
            "actorId": event_row["actor_id"],
            "action": event_row["action"],
            "outcome": event_row["outcome"],
            "resourceType": event_row["resource_type"],
            "resourceId": event_row["resource_id"],
            "details": json.loads(event_row["details_json"]),
            "previousHash": previous_hash,
            "createdAt": event_row["created_at"],
        }
        assert event_row["sequence_number"] == expected_sequence
        assert event_row["previous_hash"] == previous_hash
        assert event_row["event_hash"] == canonical_sha256(projection)
        previous_hash = event_row["event_hash"]


def test_live_and_expired_idempotency_records_are_handled_transactionally(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    service = _service(session, repository)
    operation = "evaluation-v2.target.create"
    request_hash = assurance_request_hash(
        method="POST",
        operation=operation,
        scope={"organizationId": ORG, "systemId": "system-a"},
        body=_target_payload(),
    )
    now = datetime.now(timezone.utc)

    def insert_record(key: str, *, expires_at: datetime) -> None:
        session.execute(
            GovernanceIdempotencyRecord.__table__.insert().values(
                id=str(uuid.uuid4()),
                org_id=ORG,
                actor_id=USER,
                operation=operation,
                key_hash=hashlib.sha256(key.encode("ascii")).hexdigest(),
                request_hash=request_hash,
                status="in_progress",
                created_at=now.isoformat(),
                updated_at=now.isoformat(),
                expires_at=expires_at.isoformat(),
            )
        )
        session.commit()

    insert_record("live-key", expires_at=now + timedelta(minutes=5))
    with pytest.raises(EvaluationWorkbenchError) as live:
        service.create_target_version(
            org_id=ORG,
            system_id="system-a",
            actor_id=USER,
            idempotency_key="live-key",
            payload=_target_payload(),
        )
    assert live.value.code == "idempotency_in_progress"

    insert_record("expired-key", expires_at=now - timedelta(seconds=1))
    created = service.create_target_version(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="expired-key",
        payload=_target_payload(),
    )
    assert created.status == 201
    expired_row = (
        session.execute(
            select(GovernanceIdempotencyRecord.__table__).where(
                GovernanceIdempotencyRecord.key_hash == hashlib.sha256(b"expired-key").hexdigest()
            )
        )
        .mappings()
        .one()
    )
    assert expired_row["status"] == "completed"
    assert session.scalar(select(func.count()).select_from(GovernanceEvaluationTargetVersion)) == 1


def test_corrupted_stored_binding_returns_stable_integrity_conflict(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target, suite_ids = _create_bound_catalog(service)
    plan = service.create_plan(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="integrity-plan",
        payload=_plan_payload(target["id"], suite_ids),
    ).body
    session.execute(
        GovernanceEvaluationTargetVersion.__table__.update()
        .where(GovernanceEvaluationTargetVersion.id == target["id"])
        .values(manifest_json='{"inputs":{},"apiCredentials":"leaked"}')
    )
    session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.preflight(
            org_id=ORG,
            system_id="system-a",
            plan_id=plan["id"],
            lifecycle_phase="pre_deploy",
        )
    assert caught.value.code == "binding_integrity_error"
    assert caught.value.status_code == 409


def test_non_catalog_integrity_error_remains_atomic_persistence_failure(
    repository_fixture,
    monkeypatch,
) -> None:
    session, _ = repository_fixture
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)

    def fail_completion(**_kwargs):
        raise IntegrityError(
            "UPDATE governance_idempotency_records",
            {},
            RuntimeError("injected non-catalog constraint failure"),
        )

    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(
        session,
        repository=repository,
    )
    monkeypatch.setattr(unit_of_work, "_complete_idempotency", fail_completion)
    service = EvaluationWorkbenchService(unit_of_work)
    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.create_target_version(
            org_id=ORG,
            system_id="system-a",
            actor_id=USER,
            idempotency_key="non-catalog-integrity",
            payload=_target_payload(),
        )

    assert caught.value.code == "evaluation_persistence_failed"
    assert caught.value.status_code == 500
    assert session.scalar(select(func.count()).select_from(GovernanceEvaluationTargetVersion)) == 0
    assert session.scalar(select(func.count()).select_from(GovernanceIdempotencyRecord)) == 0
    assert session.scalar(select(func.count()).select_from(GovernanceEvaluationAuditEvent)) == 0


def test_database_manager_enables_sqlite_foreign_keys(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    manager = DatabaseManager()
    try:
        with manager.engine.connect() as connection:
            assert connection.scalar(text("PRAGMA foreign_keys")) == 1
    finally:
        manager.engine.dispose()


def test_successful_evaluator_can_report_failed_model_without_governance_autodecision(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target, suite_ids = _create_bound_catalog(service)
    plan = service.create_plan(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="axis-plan",
        payload=_plan_payload(target["id"], suite_ids),
    ).body
    service.activate_plan(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key="axis-plan-activate",
    )
    run = service.create_run(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key="axis-run",
        payload={"trigger": "manual", "lifecyclePhase": "pre_deploy"},
    ).body
    completed_at = datetime.now(timezone.utc).isoformat()
    session.execute(
        GovernanceEvaluationRunSuiteExecution.__table__.update()
        .where(GovernanceEvaluationRunSuiteExecution.run_id == run["id"])
        .values(
            technical_status="succeeded",
            evidence_result_status="failed",
            started_at=completed_at,
            completed_at=completed_at,
        )
    )
    session.execute(
        GovernanceEvaluationRun.__table__.update()
        .where(GovernanceEvaluationRun.id == run["id"])
        .values(
            technical_status="succeeded",
            evidence_outcome="failed",
            overall_verdict="insufficient",
            started_at=completed_at,
            completed_at=completed_at,
        )
    )
    session.commit()

    result = service.get_run(
        org_id=ORG,
        system_id="system-a",
        run_id=run["id"],
    )
    assert result is not None
    assert result["technicalStatus"] == "succeeded"
    assert result["evidenceOutcome"] == "failed"
    assert result["suiteExecutions"][0]["technicalStatus"] == "succeeded"
    assert result["suiteExecutions"][0]["evidenceResultStatus"] == "failed"
    assert result["overallVerdict"] == "insufficient"


@pytest.mark.parametrize(
    ("resource", "child_table_name"),
    [
        ("plan", "governance_evaluation_plan_suites"),
        ("run", "governance_evaluation_run_suite_executions"),
    ],
)
def test_second_child_insert_failure_rolls_back_entire_multi_suite_mutation(
    repository_fixture,
    monkeypatch,
    resource: str,
    child_table_name: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target, suite_ids = _create_bound_catalog(service, suites=2)
    plan = None
    if resource == "run":
        plan = service.create_plan(
            org_id=ORG,
            system_id="system-a",
            actor_id=USER,
            idempotency_key="atomic-plan-setup",
            payload=_plan_payload(target["id"], suite_ids),
        ).body
        service.activate_plan(
            org_id=ORG,
            system_id="system-a",
            plan_id=plan["id"],
            actor_id=USER,
            idempotency_key="atomic-plan-setup-activate",
        )

    baseline_idempotency = session.scalar(
        select(func.count()).select_from(GovernanceIdempotencyRecord)
    )
    baseline_audit = session.scalar(
        select(func.count()).select_from(GovernanceEvaluationAuditEvent)
    )
    original_execute = session.execute
    child_inserts = 0

    def fail_second_child(statement, *args, **kwargs):
        nonlocal child_inserts
        table = getattr(statement, "table", None)
        if table is not None and table.name == child_table_name:
            child_inserts += 1
            if child_inserts == 2:
                raise RuntimeError("injected second child insert failure")
        return original_execute(statement, *args, **kwargs)

    monkeypatch.setattr(session, "execute", fail_second_child)
    with pytest.raises(EvaluationWorkbenchError) as caught:
        if resource == "plan":
            service.create_plan(
                org_id=ORG,
                system_id="system-a",
                actor_id=USER,
                idempotency_key="atomic-plan-fail",
                payload=_plan_payload(target["id"], suite_ids),
            )
        else:
            assert plan is not None
            service.create_run(
                org_id=ORG,
                system_id="system-a",
                plan_id=plan["id"],
                actor_id=USER,
                idempotency_key="atomic-run-fail",
                payload={"trigger": "manual", "lifecyclePhase": "pre_deploy"},
            )
    assert caught.value.code == "evaluation_persistence_failed"
    monkeypatch.setattr(session, "execute", original_execute)

    if resource == "plan":
        assert session.scalar(select(func.count()).select_from(GovernanceEvaluationPlan)) == 0
        assert session.scalar(select(func.count()).select_from(GovernanceEvaluationPlanSuite)) == 0
    else:
        assert session.scalar(select(func.count()).select_from(GovernanceEvaluationRun)) == 0
        assert (
            session.scalar(select(func.count()).select_from(GovernanceEvaluationRunSuiteExecution))
            == 0
        )
    assert (
        session.scalar(select(func.count()).select_from(GovernanceIdempotencyRecord))
        == baseline_idempotency
    )
    assert (
        session.scalar(select(func.count()).select_from(GovernanceEvaluationAuditEvent))
        == baseline_audit
    )


def test_plan_replay_preserves_ordered_children_and_single_audit(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target, suite_ids = _create_bound_catalog(service, suites=2)
    payload = _plan_payload(target["id"], suite_ids)

    first = service.create_plan(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="plan-replay",
        payload=payload,
    )
    replay = service.create_plan(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="plan-replay",
        payload=payload,
    )

    assert replay.replayed is True
    assert replay.body == first.body
    assert session.scalar(select(func.count()).select_from(GovernanceEvaluationPlan)) == 1
    rows = (
        session.execute(
            select(GovernanceEvaluationPlanSuite.__table__)
            .where(GovernanceEvaluationPlanSuite.plan_id == first.body["id"])
            .order_by(GovernanceEvaluationPlanSuite.ordinal)
        )
        .mappings()
        .all()
    )
    assert [row["ordinal"] for row in rows] == [0, 1]
    assert [row["suite_version_id"] for row in rows] == suite_ids
    assert (
        session.scalar(
            select(func.count())
            .select_from(GovernanceEvaluationAuditEvent)
            .where(GovernanceEvaluationAuditEvent.action == "evaluation_v2.plan.created")
        )
        == 1
    )


def test_reactivation_with_fresh_key_is_idempotent_noop_without_duplicate_audit(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target, suite_ids = _create_bound_catalog(service)
    suite_id = suite_ids[0]
    suite_result = service.activate_suite_version(
        org_id=ORG,
        suite_version_id=suite_id,
        actor_id=USER,
        idempotency_key="suite-reactivate-fresh",
    )
    assert suite_result is not None
    assert suite_result.status == 200
    assert suite_result.body["status"] == "active"
    assert (
        session.scalar(
            select(func.count())
            .select_from(GovernanceEvaluationAuditEvent)
            .where(GovernanceEvaluationAuditEvent.action == "evaluation_v2.suite.activated")
        )
        == 1
    )

    plan = service.create_plan(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="reactivation-plan",
        payload=_plan_payload(target["id"], suite_ids),
    ).body
    service.activate_plan(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key="reactivation-plan-first",
    )
    plan_result = service.activate_plan(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key="reactivation-plan-fresh",
    )
    assert plan_result is not None
    assert plan_result.status == 200
    assert plan_result.body["status"] == "active"
    assert (
        session.scalar(
            select(func.count())
            .select_from(GovernanceEvaluationAuditEvent)
            .where(GovernanceEvaluationAuditEvent.action == "evaluation_v2.plan.activated")
        )
        == 1
    )
