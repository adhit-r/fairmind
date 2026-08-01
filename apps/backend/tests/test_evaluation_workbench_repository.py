"""Persistence and atomicity tests for assurance-contract v2."""

from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import replace
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
from src.application.ports.evaluation_workbench import FrozenJsonObject
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    MAX_EXECUTION_ENVELOPE_BYTES,
    canonical_json,
    canonical_sha256,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchRepository,
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)
from tests.evaluation_workbench_sqlite import (
    allow_deliberate_check_constraint_corruption,
    install_013a_for_application_verifier_harness,
)

ORG = str(uuid.uuid4())
OTHER_ORG = str(uuid.uuid4())
USER = str(uuid.uuid4())
BINDING_INTEGRITY_DETAIL = {
    "code": "binding_integrity_error",
    "message": "Stored assurance bindings failed integrity verification.",
}
AUDIT_CHAIN_INTEGRITY_DETAIL = {
    "code": "audit_chain_integrity_error",
    "message": "Stored evaluation audit chain failed integrity verification.",
}


def test_envelope_nonce_verifier_rejects_standard_base64_alphabet() -> None:
    standard_nonce = base64.b64encode(b"\xfb" * 32).decode("ascii").rstrip("=")
    assert len(standard_nonce) == 43
    assert "+" in standard_nonce or "/" in standard_nonce

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verified_envelope_nonce({"nonce": standard_nonce})

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_envelope_nonce_verifier_rejects_noncanonical_pad_bits() -> None:
    noncanonical_nonce = ("A" * 42) + "B"
    assert base64.urlsafe_b64decode(noncanonical_nonce + "=") == b"\x00" * 32

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verified_envelope_nonce(
            {"nonce": noncanonical_nonce}
        )

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


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
    install_013a_for_application_verifier_harness(engine)
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


def _create_active_plan_and_run(
    service: EvaluationWorkbenchService,
    *,
    suites: int = 1,
    run_key: str = "integrity-run",
):
    target, suite_ids = _create_bound_catalog(service, suites=suites)
    plan = service.create_plan(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="integrity-plan",
        payload=_plan_payload(target["id"], suite_ids),
    ).body
    service.activate_plan(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key="integrity-plan-activate",
    )
    run = service.create_run(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key=run_key,
        payload={"trigger": "manual", "lifecyclePhase": "pre_deploy"},
    ).body
    return plan, run


def _stored_run_and_graph(session, run_id: str):
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    record = repository.get_run_record(
        org_id=ORG,
        system_id="system-a",
        run_id=run_id,
    )
    assert record is not None
    graph = repository.get_plan_graph(
        org_id=ORG,
        system_id="system-a",
        plan_id=record.plan_id,
    )
    assert graph is not None
    return repository, record, graph


def _nested_policy(depth: int) -> str:
    nested: object = "leaf"
    for _ in range(depth):
        nested = {"child": nested}
    return canonical_json({"nested": nested})


def test_created_run_persists_an_independent_nonce_witness(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)

    runs = GovernanceEvaluationRun.__table__
    row_nonce = session.scalar(
        select(runs.c.envelope_nonce).where(runs.c.id == run["id"])
    )
    _, record, _ = _stored_run_and_graph(session, run["id"])

    assert row_nonce == run["envelope"]["nonce"]
    assert record.envelope_nonce == row_nonce
    assert len(base64.urlsafe_b64decode(row_nonce + "=")) == 32


def test_suite_execution_record_preserves_all_authoritative_evidence_projections(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, _ = _stored_run_and_graph(session, run["id"])

    execution = record.suite_executions[0]
    assert execution.evidence_run_id is None
    assert execution.passport_revision_id is None
    assert execution.linked_by is None
    assert execution.linked_at is None
    assert execution.result_summary is None
    assert execution.limitations is None


def test_repository_decodes_canonical_suite_result_and_limitations(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    table = GovernanceEvaluationRunSuiteExecution.__table__
    row = dict(
        session.execute(select(table).where(table.c.run_id == run["id"])).mappings().one()
    )
    row["result_summary_json"] = canonical_json(
        {"metrics": {"failureRate": 0.25}, "sampleCount": 4}
    )
    row["limitations_json"] = canonical_json(["Synthetic cases only."])

    execution = SqlAlchemyEvaluationWorkbenchRepository(
        session
    )._suite_execution_record(row)

    assert execution.result_summary is not None
    assert execution.result_summary.to_dict() == {
        "metrics": {"failureRate": 0.25},
        "sampleCount": 4,
    }
    assert execution.limitations == ("Synthetic cases only.",)


@pytest.mark.parametrize(
    ("column", "raw"),
    [
        ("result_summary_json", '{"score":1}\n'),
        ("result_summary_json", '{"score":1,"score":2}'),
        ("result_summary_json", "[]"),
        (
            "result_summary_json",
            canonical_json({"summary": "x" * (64 * 1024)}),
        ),
        ("limitations_json", '{"limitation":"wrong root"}'),
        ("limitations_json", canonical_json(["x" * (8 * 1024)])),
    ],
)
def test_repository_rejects_malformed_or_unbounded_suite_projection_json(
    repository_fixture,
    column: str,
    raw: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    table = GovernanceEvaluationRunSuiteExecution.__table__
    row = dict(
        session.execute(select(table).where(table.c.run_id == run["id"])).mappings().one()
    )
    row[column] = raw

    with pytest.raises(EvaluationWorkbenchError) as caught:
        SqlAlchemyEvaluationWorkbenchRepository(session)._suite_execution_record(row)

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_run_verifier_rejects_a_rehashed_envelope_with_a_rebound_nonce(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])
    rebound_nonce = base64.urlsafe_b64encode(b"n" * 32).decode("ascii").rstrip("=")
    assert rebound_nonce != record.envelope_nonce
    envelope = record.envelope.to_dict()
    envelope["nonce"] = rebound_nonce
    tampered = replace(
        record,
        envelope=FrozenJsonObject.from_mapping(envelope),
        envelope_hash=canonical_sha256(envelope),
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verify_run_record(tampered, graph)

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


@pytest.mark.parametrize(
    "binding_json",
    [
        "target.manifest_json",
        "trust.policy_json",
        "suite.manifest_json",
        "suite.target_kinds_json",
        "suite.subject_kinds_json",
        "suite.lifecycle_phases_json",
        "suite.execution_depths_json",
        "suite.delivery_modes_json",
        "suite.configuration_schema_json",
        "suite.configuration_defaults_json",
        "suite.required_input_roles_json",
        "suite.default_budgets_json",
        "plan.lifecycle_phases_json",
        "selection.configuration_json",
    ],
)
def test_every_authoritative_binding_json_requires_exact_canonical_storage(
    repository_fixture,
    binding_json: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    plan, run = _create_active_plan_and_run(service)
    target_id = plan["targetVersionId"]
    suite_id = plan["suites"][0]["suiteVersionId"]
    model_name, column_name = binding_json.split(".", 1)
    if model_name == "target":
        table = GovernanceEvaluationTargetVersion.__table__
        predicate = table.c.id == target_id
        read = lambda: service.get_target_version(
            org_id=ORG,
            system_id="system-a",
            target_version_id=target_id,
        )
    elif model_name == "trust":
        table = GovernanceEvidenceTrustPolicyVersion.__table__
        predicate = table.c.id == "trust-a"
        read = lambda: service.get_plan(
            org_id=ORG,
            system_id="system-a",
            plan_id=plan["id"],
        )
    elif model_name == "suite":
        table = GovernanceEvaluationSuiteVersion.__table__
        predicate = table.c.id == suite_id
        read = lambda: service.get_suite_version(
            org_id=ORG,
            suite_version_id=suite_id,
        )
    elif model_name == "plan":
        table = GovernanceEvaluationPlan.__table__
        predicate = table.c.id == plan["id"]
        read = lambda: service.get_plan(
            org_id=ORG,
            system_id="system-a",
            plan_id=plan["id"],
        )
    else:
        table = GovernanceEvaluationPlanSuite.__table__
        predicate = table.c.plan_id == plan["id"]
        read = lambda: service.get_run(
            org_id=ORG,
            system_id="system-a",
            run_id=run["id"],
        )
    raw = session.scalar(select(table.c[column_name]).where(predicate))
    assert isinstance(raw, str)
    session.execute(table.update().where(predicate).values({column_name: raw + "\n"}))
    session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        read()

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


@pytest.mark.parametrize(
    "malformed_policy",
    [
        pytest.param('{"marker":"safe","marker":"safe"}', id="duplicate-name"),
        pytest.param('{"marker":NaN}', id="nonfinite-number"),
        pytest.param(_nested_policy(33), id="depth-limit"),
        pytest.param(
            canonical_json({"items": [None] * 10_001}),
            id="aggregate-item-limit",
        ),
        pytest.param(
            canonical_json({"padding": "x" * (64 * 1024)}),
            id="byte-limit",
        ),
    ],
)
def test_authoritative_binding_decoder_rejects_unsafe_json_before_verification(
    repository_fixture,
    monkeypatch,
    malformed_policy: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    plan, _ = _create_active_plan_and_run(service)
    session.execute(
        GovernanceEvidenceTrustPolicyVersion.__table__.update()
        .where(GovernanceEvidenceTrustPolicyVersion.id == "trust-a")
        .values(policy_json=malformed_policy)
    )
    session.commit()

    def verifier_must_not_run(*_args, **_kwargs):
        raise AssertionError("stored JSON must be rejected before application verification")

    monkeypatch.setattr(
        evaluation_service_module,
        "_verify_plan_graph",
        verifier_must_not_run,
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.get_plan(org_id=ORG, system_id="system-a", plan_id=plan["id"])

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


@pytest.mark.parametrize("encoding_case", ["duplicate-name", "malformed-json"])
def test_suite_manifest_hostile_encoding_is_a_generic_integrity_error(
    repository_fixture,
    encoding_case: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target, suite_ids = _create_bound_catalog(service)
    del target
    suite_id = suite_ids[0]
    table = GovernanceEvaluationSuiteVersion.__table__
    raw = session.scalar(select(table.c.manifest_json).where(table.c.id == suite_id))
    assert isinstance(raw, str)
    if encoding_case == "duplicate-name":
        manifest = json.loads(raw)
        duplicate_key = next(iter(manifest))
        hostile = raw[:-1] + (
            f",{canonical_json(duplicate_key)}:{canonical_json(manifest[duplicate_key])}"
            "}"
        )
    else:
        hostile = "{"
    session.execute(
        table.update().where(table.c.id == suite_id).values(manifest_json=hostile)
    )
    session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.get_suite_version(org_id=ORG, suite_version_id=suite_id)

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_catalog_string_array_rejects_an_object_member_before_verification(
    repository_fixture,
    monkeypatch,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, suite_ids = _create_bound_catalog(service)
    suite_id = suite_ids[0]
    session.execute(
        GovernanceEvaluationSuiteVersion.__table__.update()
        .where(GovernanceEvaluationSuiteVersion.id == suite_id)
        .values(target_kinds_json=canonical_json([{"kind": "agent"}]))
    )
    session.commit()

    monkeypatch.setattr(
        evaluation_service_module,
        "_verify_suite",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("stored string arrays must fail before verification")
        ),
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.get_suite_version(org_id=ORG, suite_version_id=suite_id)

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_catalog_decoder_allows_an_empty_required_input_role_list(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    payload = _suite_payload("no-input-suite")
    payload["requiredInputRoles"] = []
    created = service.create_suite_version(
        org_id=ORG,
        actor_id=USER,
        idempotency_key="no-input-suite",
        payload=payload,
    ).body

    suite = service.get_suite_version(org_id=ORG, suite_version_id=created["id"])

    assert suite is not None
    assert suite["requiredInputRoles"] == []


def test_stored_json_item_limit_accepts_exactly_ten_thousand_array_items(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    raw = canonical_json([None] * 10_000)

    decoded = repository._stored_json_array(
        raw,
        maximum_bytes=len(raw.encode("utf-8")),
    )

    assert len(decoded) == 10_000


def test_stored_json_arrays_are_deeply_immutable(repository_fixture) -> None:
    session, _ = repository_fixture
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    raw = canonical_json([{"status": "safe"}])

    decoded = repository._stored_json_array(
        raw,
        maximum_bytes=len(raw.encode("utf-8")),
    )

    with pytest.raises(TypeError):
        decoded[0]["status"] = "tampered"


def _rehash_plan_graph(graph):
    projection = evaluation_service_module.plan_content_projection(
        org_id=graph.scope.organization_id,
        workspace_id=graph.scope.workspace_id,
        system_id=graph.scope.system_id,
        target=evaluation_service_module._target_domain(graph.target),
        plan=evaluation_service_module._requested_plan_domain(graph),
        trust_policy=evaluation_service_module._trust_domain(graph.trust_policy),
        suites=[
            evaluation_service_module._suite_domain(selection)
            for selection in graph.suites
        ],
    )
    return replace(
        graph,
        plan=replace(graph.plan, plan_content_hash=canonical_sha256(projection)),
    )


def _tamper_plan_graph(graph, case: str):
    if case == "contract_version":
        return replace(graph, plan=replace(graph.plan, contract_version="1.0.0"))
    if case == "plan_scope":
        return replace(graph, plan=replace(graph.plan, workspace_id="workspace-other"))
    if case == "target_scope":
        return replace(graph, target=replace(graph.target, system_id="system-other"))
    if case == "target_id":
        return replace(graph, plan=replace(graph.plan, target_version_id="target-other"))
    if case == "target_kind":
        return replace(graph, plan=replace(graph.plan, target_kind="vision_model"))
    if case == "trust_id":
        return replace(
            graph,
            plan=replace(graph.plan, trust_policy_version_id="trust-other"),
        )
    if case == "trust_scope":
        return replace(
            graph,
            trust_policy=replace(graph.trust_policy, organization_id=OTHER_ORG),
        )
    if case == "suite_ref_identity":
        selection = graph.suites[0]
        changed = replace(selection, suite=replace(selection.suite, namespace="other"))
        return replace(graph, suites=(changed, *graph.suites[1:]))
    if case == "suite_owner_scope":
        selection = graph.suites[0]
        changed = replace(
            selection,
            suite=replace(selection.suite, owner_organization_id=OTHER_ORG),
        )
        return replace(graph, suites=(changed, *graph.suites[1:]))
    if case == "ordinal":
        selection = replace(graph.suites[0], ordinal=1)
        return _rehash_plan_graph(replace(graph, suites=(selection, *graph.suites[1:])))
    raise AssertionError(f"unknown graph tamper case: {case}")


@pytest.mark.parametrize(
    "case",
    [
        "contract_version",
        "plan_scope",
        "target_scope",
        "target_id",
        "target_kind",
        "trust_id",
        "trust_scope",
        "suite_ref_identity",
        "suite_owner_scope",
        "ordinal",
    ],
)
def test_plan_graph_rejects_every_cross_record_binding_before_projection_hash(
    repository_fixture,
    case: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    target, suite_ids = _create_bound_catalog(service)
    plan = service.create_plan(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="plan-graph-integrity",
        payload=_plan_payload(target["id"], suite_ids),
    ).body
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    graph = repository.get_plan_graph(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
    )
    assert graph is not None

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verify_plan_graph(_tamper_plan_graph(graph, case))

    assert caught.value.status_code == 409
    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_create_run_rejects_tampered_persistence_record_and_rolls_back(
    repository_fixture,
    monkeypatch,
) -> None:
    session, _ = repository_fixture
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    service = _service(session, repository)
    target, suite_ids = _create_bound_catalog(service)
    plan = service.create_plan(
        org_id=ORG,
        system_id="system-a",
        actor_id=USER,
        idempotency_key="create-integrity-plan",
        payload=_plan_payload(target["id"], suite_ids),
    ).body
    service.activate_plan(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key="create-integrity-plan-activate",
    )
    idempotency_before = session.scalar(
        select(func.count()).select_from(GovernanceIdempotencyRecord)
    )
    audit_before = session.scalar(
        select(func.count()).select_from(GovernanceEvaluationAuditEvent)
    )
    persist_run = repository.persist_run

    def persist_tampered(command):
        record = persist_run(command)
        envelope = record.envelope.to_dict()
        envelope["systemId"] = "system-tampered"
        return replace(
            record,
            envelope=FrozenJsonObject.from_mapping(envelope),
            envelope_hash=canonical_sha256(envelope),
        )

    monkeypatch.setattr(repository, "persist_run", persist_tampered)

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.create_run(
            org_id=ORG,
            system_id="system-a",
            plan_id=plan["id"],
            actor_id=USER,
            idempotency_key="create-integrity-run",
            payload={"trigger": "manual", "lifecyclePhase": "pre_deploy"},
        )

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL
    assert session.scalar(select(func.count()).select_from(GovernanceEvaluationRun)) == 0
    assert session.scalar(
        select(func.count()).select_from(GovernanceIdempotencyRecord)
    ) == idempotency_before
    assert session.scalar(
        select(func.count()).select_from(GovernanceEvaluationAuditEvent)
    ) == audit_before


@pytest.mark.parametrize("read_method", ["detail", "list"])
def test_run_reads_reject_rehashed_envelope_bound_to_another_scope(
    repository_fixture,
    read_method: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    envelope = deepcopy(run["envelope"])
    envelope["organizationId"] = "FM_SENTINEL_FOREIGN_ORGANIZATION"
    session.execute(
        GovernanceEvaluationRun.__table__.update()
        .where(GovernanceEvaluationRun.id == run["id"])
        .values(
            envelope_json=canonical_json(envelope),
            envelope_hash=canonical_sha256(envelope),
        )
    )
    session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        if read_method == "detail":
            service.get_run(org_id=ORG, system_id="system-a", run_id=run["id"])
        else:
            service.list_runs(org_id=ORG, system_id="system-a")

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL
    assert "FM_SENTINEL" not in caught.value.message


def test_run_read_rejects_envelope_hash_mismatch(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    envelope = deepcopy(run["envelope"])
    envelope["trigger"] = "ci"
    session.execute(
        GovernanceEvaluationRun.__table__.update()
        .where(GovernanceEvaluationRun.id == run["id"])
        .values(envelope_json=canonical_json(envelope))
    )
    session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.get_run(org_id=ORG, system_id="system-a", run_id=run["id"])

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_run_read_rejects_duplicate_names_in_stored_envelope(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    canonical = canonical_json(run["envelope"])
    duplicate = '{"schemaVersion":"2.0.0",' + canonical[1:]
    session.execute(
        GovernanceEvaluationRun.__table__.update()
        .where(GovernanceEvaluationRun.id == run["id"])
        .values(envelope_json=duplicate)
    )
    session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.get_run(org_id=ORG, system_id="system-a", run_id=run["id"])

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


@pytest.mark.parametrize(
    "stored_envelope",
    [
        pytest.param(
            lambda canonical: canonical + "\n",
            id="noncanonical-whitespace",
        ),
        pytest.param(
            lambda canonical: json.dumps(
                dict(reversed(list(json.loads(canonical).items()))),
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            id="noncanonical-key-order",
        ),
        pytest.param(
            lambda _canonical: '{"schemaVersion":NaN}',
            id="nonfinite-number",
        ),
        pytest.param(
            lambda _canonical: '{"padding":"'
            + ("x" * MAX_EXECUTION_ENVELOPE_BYTES)
            + '"}',
            id="oversized-payload",
        ),
    ],
)
def test_run_read_rejects_invalid_stored_envelope_encodings(
    repository_fixture,
    stored_envelope,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    raw = stored_envelope(canonical_json(run["envelope"]))
    with allow_deliberate_check_constraint_corruption(session):
        session.execute(
            GovernanceEvaluationRun.__table__.update()
            .where(GovernanceEvaluationRun.id == run["id"])
            .values(envelope_json=raw)
        )
        session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.get_run(org_id=ORG, system_id="system-a", run_id=run["id"])

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


@pytest.mark.parametrize(
    "encoding_case",
    ["duplicate-name", "noncanonical-whitespace", "oversized-payload"],
)
def test_run_read_rejects_invalid_layer_verdict_encodings_before_verification(
    repository_fixture,
    monkeypatch,
    encoding_case: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    execution_id = run["suiteExecutions"][0]["id"]
    if encoding_case == "duplicate-name":
        raw = (
            "{"
            f'"{execution_id}":"insufficient",'
            f'"{execution_id}":"insufficient"'
            "}"
        )
    elif encoding_case == "noncanonical-whitespace":
        raw = canonical_json(run["layerVerdicts"]) + "\n"
    else:
        raw = canonical_json({"x" * (8 * 1024): "insufficient"})
    session.execute(
        GovernanceEvaluationRun.__table__.update()
        .where(GovernanceEvaluationRun.id == run["id"])
        .values(layer_verdicts_json=raw)
    )
    session.commit()

    def verifier_must_not_run(*_args, **_kwargs):
        raise AssertionError("stored JSON must be rejected before application verification")

    monkeypatch.setattr(
        evaluation_service_module,
        "_verify_run_record",
        verifier_must_not_run,
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.get_run(org_id=ORG, system_id="system-a", run_id=run["id"])

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_run_read_rejects_rehashed_suite_execution_id_rebinding(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    envelope = deepcopy(run["envelope"])
    envelope["suites"][0]["suiteExecutionId"] = str(uuid.uuid4())
    session.execute(
        GovernanceEvaluationRun.__table__.update()
        .where(GovernanceEvaluationRun.id == run["id"])
        .values(
            envelope_json=canonical_json(envelope),
            envelope_hash=canonical_sha256(envelope),
        )
    )
    session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.get_run(org_id=ORG, system_id="system-a", run_id=run["id"])

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


@pytest.mark.parametrize(
    ("record_change", "envelope_change"),
    [
        pytest.param(
            {"trigger": "FM_SENTINEL_TRIGGER"},
            {"trigger": "FM_SENTINEL_TRIGGER"},
            id="unsupported-trigger",
        ),
        pytest.param(
            {"created_at": "2026-07-20T12:00:00+05:30"},
            {"requestedAt": "2026-07-20T12:00:00+05:30"},
            id="non-utc-request-time",
        ),
        pytest.param(
            {"created_at": "2026-07-20 12:00:00+00:00"},
            {"requestedAt": "2026-07-20 12:00:00+00:00"},
            id="noncanonical-request-time",
        ),
    ],
)
def test_run_verifier_rejects_rehashed_invalid_contract_fields(
    repository_fixture,
    record_change: dict[str, str],
    envelope_change: dict[str, str],
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    plan, run = _create_active_plan_and_run(service)
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    graph = repository.get_plan_graph(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
    )
    record = repository.get_run_record(
        org_id=ORG,
        system_id="system-a",
        run_id=run["id"],
    )
    assert graph is not None
    assert record is not None
    envelope = record.envelope.to_dict()
    envelope.update(envelope_change)
    tampered = replace(
        record,
        **record_change,
        envelope=FrozenJsonObject.from_mapping(envelope),
        envelope_hash=canonical_sha256(envelope),
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verify_run_record(tampered, graph)

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL
    assert "FM_SENTINEL" not in caught.value.message


def test_run_verifier_rejects_standard_base64_nonce_with_recomputed_hash(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    plan, run = _create_active_plan_and_run(service)
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    graph = repository.get_plan_graph(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
    )
    record = repository.get_run_record(
        org_id=ORG,
        system_id="system-a",
        run_id=run["id"],
    )
    assert graph is not None
    assert record is not None
    standard_nonce = base64.b64encode(b"\xfb" * 32).decode("ascii").rstrip("=")
    assert len(standard_nonce) == 43
    assert "+" in standard_nonce or "/" in standard_nonce
    envelope = record.envelope.to_dict()
    envelope["nonce"] = standard_nonce
    tampered = replace(
        record,
        envelope=FrozenJsonObject.from_mapping(envelope),
        envelope_hash=canonical_sha256(envelope),
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verify_run_record(tampered, graph)

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_run_read_rejects_missing_suite_execution(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service, suites=2)
    session.execute(
        GovernanceEvaluationRunSuiteExecution.__table__.delete().where(
            GovernanceEvaluationRunSuiteExecution.id == run["suiteExecutions"][1]["id"]
        )
    )
    session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.get_run(org_id=ORG, system_id="system-a", run_id=run["id"])

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_run_read_rejects_rehashed_reordered_suite_envelope(repository_fixture) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service, suites=2)
    envelope = deepcopy(run["envelope"])
    envelope["suites"] = list(reversed(envelope["suites"]))
    session.execute(
        GovernanceEvaluationRun.__table__.update()
        .where(GovernanceEvaluationRun.id == run["id"])
        .values(
            envelope_json=canonical_json(envelope),
            envelope_hash=canonical_sha256(envelope),
        )
    )
    session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.get_run(org_id=ORG, system_id="system-a", run_id=run["id"])

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_run_list_verifies_one_plan_graph_once_per_request(repository_fixture, monkeypatch) -> None:
    session, _ = repository_fixture
    repository = SqlAlchemyEvaluationWorkbenchRepository(session)
    service = _service(session, repository)
    plan, _ = _create_active_plan_and_run(service, run_key="cached-plan-run-one")
    service.create_run(
        org_id=ORG,
        system_id="system-a",
        plan_id=plan["id"],
        actor_id=USER,
        idempotency_key="cached-plan-run-two",
        payload={"trigger": "ci", "lifecyclePhase": "pre_deploy"},
    )
    load_graph = repository.get_plan_graph
    calls = 0

    def count_graph_load(**kwargs):
        nonlocal calls
        calls += 1
        return load_graph(**kwargs)

    monkeypatch.setattr(repository, "get_plan_graph", count_graph_load)
    verify_graph = evaluation_service_module._verify_plan_graph
    verify_calls = 0

    def count_graph_verification(graph):
        nonlocal verify_calls
        verify_calls += 1
        return verify_graph(graph)

    monkeypatch.setattr(
        evaluation_service_module,
        "_verify_plan_graph",
        count_graph_verification,
    )

    records = service.list_runs(org_id=ORG, system_id="system-a")

    assert records is not None and len(records) == 2
    assert calls == 1
    assert verify_calls == 1


def _earlier_than(timestamp: str) -> str:
    return (datetime.fromisoformat(timestamp) - timedelta(seconds=1)).isoformat()


def _later_than(timestamp: str, *, seconds: int = 1) -> str:
    return (datetime.fromisoformat(timestamp) + timedelta(seconds=seconds)).isoformat()


def _tampered_run_state(record, case: str):
    if case == "unknown-technical-status":
        return replace(record, technical_status="unknown-state")
    if case == "unknown-evidence-outcome":
        return replace(record, evidence_outcome="unknown-result-state")
    if case == "incoherent-pending-result":
        return replace(record, evidence_outcome="error")
    if case == "unknown-governance-verdict":
        return replace(record, overall_verdict="unknown-verdict")
    if case == "negative-verdict-version":
        return replace(record, verdict_version=-1)
    if case == "boolean-verdict-version":
        return replace(record, verdict_version=True)
    if case == "v0-overall-decision":
        return replace(record, overall_verdict="approved")
    if case == "noncanonical-updated-time":
        return replace(record, updated_at=record.updated_at.replace("T", " "))
    if case == "updated-before-created":
        return replace(record, updated_at=_earlier_than(record.created_at))
    if case == "queued-with-start-time":
        return replace(record, technical_status="queued", started_at=record.created_at)
    if case == "running-without-start-time":
        return replace(record, technical_status="running")
    if case == "succeeded-without-terminal-times":
        return replace(record, technical_status="succeeded", evidence_outcome="failed")
    if case == "failed-without-completion-time":
        return replace(record, technical_status="failed", evidence_outcome="error")
    if case == "nonfailure-with-failure-code":
        return replace(record, failure_code="unexpected_failure")
    if case == "oversized-failure-message":
        return replace(
            record,
            technical_status="failed",
            evidence_outcome="error",
            completed_at=record.updated_at,
            failure_message="x" * (2 * 1024 + 1),
        )
    raise AssertionError(f"unknown run state tamper: {case}")


@pytest.mark.parametrize(
    "case",
    [
        "unknown-technical-status",
        "unknown-evidence-outcome",
        "incoherent-pending-result",
        "unknown-governance-verdict",
        "negative-verdict-version",
        "boolean-verdict-version",
        "v0-overall-decision",
        "noncanonical-updated-time",
        "updated-before-created",
        "queued-with-start-time",
        "running-without-start-time",
        "succeeded-without-terminal-times",
        "failed-without-completion-time",
        "nonfailure-with-failure-code",
        "oversized-failure-message",
    ],
)
def test_run_verifier_rejects_incoherent_state_version_time_and_failure_fields(
    repository_fixture,
    case: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verify_run_record(
            _tampered_run_state(record, case),
            graph,
        )

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_run_read_maps_raw_malformed_suite_ordinal_to_generic_integrity_error(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    session.execute(
        GovernanceEvaluationRunSuiteExecution.__table__.update()
        .where(
            GovernanceEvaluationRunSuiteExecution.id
            == run["suiteExecutions"][0]["id"]
        )
        .values(ordinal="FM_SENTINEL_ORDINAL")
    )
    session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.get_run(org_id=ORG, system_id="system-a", run_id=run["id"])

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL
    assert "FM_SENTINEL" not in caught.value.message


def _tampered_suite_state(record, case: str):
    execution = record.suite_executions[0]
    if case == "unknown-technical-status":
        changed = replace(execution, technical_status="unknown-state")
    elif case == "unknown-evidence-result":
        changed = replace(execution, evidence_result_status="unknown-result-state")
    elif case == "pending-with-model-result":
        changed = replace(execution, evidence_result_status="failed")
    elif case == "succeeded-with-evaluator-error":
        changed = replace(
            execution,
            technical_status="succeeded",
            evidence_result_status="error",
            started_at=execution.created_at,
            completed_at=execution.updated_at,
        )
    elif case == "failed-with-model-result":
        changed = replace(
            execution,
            technical_status="failed",
            evidence_result_status="passed",
            completed_at=execution.updated_at,
        )
    elif case == "cancelled-with-model-result":
        changed = replace(
            execution,
            technical_status="cancelled",
            evidence_result_status="failed",
            completed_at=execution.updated_at,
        )
    elif case == "unknown-admission":
        changed = replace(execution, admission_status="unknown-admission")
    elif case == "unknown-review":
        changed = replace(execution, review_status="unknown-review")
    elif case == "unknown-freshness":
        changed = replace(execution, freshness_status="unknown-freshness")
    elif case == "pending-admission-with-accepted-review":
        changed = replace(execution, review_status="accepted")
    elif case == "pending-admission-with-stale-freshness":
        changed = replace(execution, freshness_status="stale")
    elif case == "expired-admission-with-accepted-review":
        changed = replace(
            execution,
            admission_status="expired",
            review_status="accepted",
            freshness_status="stale",
        )
    elif case == "superseded-admission-with-current-freshness":
        changed = replace(
            execution,
            admission_status="superseded",
            freshness_status="current",
        )
    elif case == "noncanonical-updated-time":
        changed = replace(execution, updated_at=execution.updated_at.replace("T", " "))
    elif case == "updated-before-created":
        changed = replace(execution, updated_at=_earlier_than(execution.created_at))
    elif case == "queued-with-start-time":
        changed = replace(
            execution,
            technical_status="queued",
            started_at=execution.created_at,
        )
    elif case == "running-without-start-time":
        changed = replace(execution, technical_status="running")
    elif case == "succeeded-without-terminal-times":
        changed = replace(
            execution,
            technical_status="succeeded",
            evidence_result_status="failed",
        )
    elif case == "failed-without-completion-time":
        changed = replace(
            execution,
            technical_status="failed",
            evidence_result_status="error",
        )
    elif case == "nonfailure-with-failure-message":
        changed = replace(execution, failure_message="unexpected failure")
    else:
        raise AssertionError(f"unknown suite state tamper: {case}")
    return replace(record, suite_executions=(changed, *record.suite_executions[1:]))


@pytest.mark.parametrize(
    "case",
    [
        "unknown-technical-status",
        "unknown-evidence-result",
        "pending-with-model-result",
        "succeeded-with-evaluator-error",
        "failed-with-model-result",
        "cancelled-with-model-result",
        "unknown-admission",
        "unknown-review",
        "unknown-freshness",
        "pending-admission-with-accepted-review",
        "pending-admission-with-stale-freshness",
        "expired-admission-with-accepted-review",
        "superseded-admission-with-current-freshness",
        "noncanonical-updated-time",
        "updated-before-created",
        "queued-with-start-time",
        "running-without-start-time",
        "succeeded-without-terminal-times",
        "failed-without-completion-time",
        "nonfailure-with-failure-message",
    ],
)
def test_run_verifier_rejects_incoherent_suite_state_time_and_failure_fields(
    repository_fixture,
    case: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verify_run_record(
            _tampered_suite_state(record, case),
            graph,
        )

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_run_verifier_rejects_partial_suite_evidence_link_tuple(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])
    execution = replace(
        record.suite_executions[0],
        evidence_run_id=str(uuid.uuid4()),
    )
    tampered = replace(record, suite_executions=(execution,))

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verify_run_record(tampered, graph)

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def _with_complete_evidence_link(execution, *, admission_status: str = "verified"):
    return replace(
        execution,
        evidence_run_id=str(uuid.uuid4()),
        passport_revision_id=str(uuid.uuid4()),
        linked_by=USER,
        linked_at=execution.updated_at,
        admission_status=admission_status,
    )


@pytest.mark.parametrize(
    "case",
    [
        "complete-link-pending-admission",
        "admitted-without-link",
        "malformed-link-id",
        "malformed-link-time",
        "link-before-execution",
        "link-after-update",
        "terminal-link-before-completion",
        "pending-result-summary",
        "oversized-result-summary",
        "oversized-limitations",
    ],
)
def test_run_verifier_rejects_incoherent_or_unbounded_suite_evidence_projections(
    repository_fixture,
    case: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])
    execution = record.suite_executions[0]
    if case == "complete-link-pending-admission":
        execution = _with_complete_evidence_link(
            execution,
            admission_status="pending",
        )
    elif case == "admitted-without-link":
        execution = replace(execution, admission_status="verified")
    elif case == "malformed-link-id":
        execution = replace(
            _with_complete_evidence_link(execution),
            evidence_run_id="FM SENTINEL INVALID ID",
        )
    elif case == "malformed-link-time":
        execution = replace(
            _with_complete_evidence_link(execution),
            linked_at="FM_SENTINEL_INVALID_TIME",
        )
    elif case == "link-before-execution":
        execution = replace(
            _with_complete_evidence_link(execution),
            linked_at=_earlier_than(execution.created_at),
        )
    elif case == "link-after-update":
        execution = replace(
            _with_complete_evidence_link(execution),
            linked_at=_later_than(execution.updated_at),
        )
    elif case == "terminal-link-before-completion":
        completed_at = _later_than(execution.created_at)
        execution = replace(
            _with_complete_evidence_link(execution),
            technical_status="succeeded",
            evidence_result_status="failed",
            started_at=execution.created_at,
            completed_at=completed_at,
            updated_at=_later_than(execution.created_at, seconds=2),
        )
    elif case == "pending-result-summary":
        execution = replace(
            execution,
            result_summary=FrozenJsonObject.from_mapping({"status": "pending"}),
        )
    elif case == "oversized-result-summary":
        execution = replace(
            execution,
            result_summary=FrozenJsonObject.from_mapping(
                {"summary": "x" * (64 * 1024)}
            ),
        )
    else:
        execution = replace(execution, limitations=("x" * (8 * 1024),))
    tampered = replace(record, suite_executions=(execution,))

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verify_run_record(tampered, graph)

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_run_verifier_rejects_outcome_that_does_not_match_suite_aggregate(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])
    execution = replace(
        _with_complete_evidence_link(record.suite_executions[0]),
        technical_status="succeeded",
        evidence_result_status="failed",
        result_summary=FrozenJsonObject.from_mapping(
            {"failedCases": 1, "sampleCount": 4}
        ),
        limitations=("Synthetic cases only.",),
        started_at=record.suite_executions[0].created_at,
        completed_at=record.suite_executions[0].updated_at,
    )
    linked = replace(
        record,
        technical_status="succeeded",
        evidence_outcome="pending",
        started_at=record.created_at,
        completed_at=record.updated_at,
        suite_executions=(execution,),
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verify_run_record(linked, graph)

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_suite_evidence_outcome_aggregate_uses_fail_closed_priority(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, _ = _stored_run_and_graph(session, run["id"])
    template = record.suite_executions[0]
    priority = (
        "pending",
        "failed",
        "error",
        "unavailable",
        "insufficient_data",
        "unknown",
        "passed_with_limitations",
        "informational",
        "passed",
    )

    for index, expected in enumerate(priority):
        executions = tuple(
            replace(template, evidence_result_status=outcome)
            for outcome in reversed(priority[index:])
        )
        assert (
            evaluation_service_module._aggregate_suite_evidence_outcome(executions)
            == expected
        )


@pytest.mark.parametrize(
    ("admission_status", "freshness_status"),
    [
        ("verified", "current"),
        ("unverified", "current"),
        ("expired", "stale"),
        ("superseded", "superseded"),
    ],
)
def test_complete_suite_evidence_links_remain_valid_across_admission_history(
    repository_fixture,
    admission_status: str,
    freshness_status: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])
    execution = replace(
        _with_complete_evidence_link(
            record.suite_executions[0],
            admission_status=admission_status,
        ),
        technical_status="succeeded",
        evidence_result_status="failed",
        freshness_status=freshness_status,
        result_summary=FrozenJsonObject.from_mapping({"failedCases": 1}),
        limitations=("Synthetic cases only.",),
        started_at=record.suite_executions[0].created_at,
        completed_at=record.suite_executions[0].updated_at,
    )
    linked = replace(
        record,
        technical_status="succeeded",
        evidence_outcome="failed",
        started_at=record.created_at,
        completed_at=record.updated_at,
        suite_executions=(execution,),
    )

    evaluation_service_module._verify_run_record(linked, graph)


@pytest.mark.parametrize(
    ("admission_status", "freshness_status"),
    [
        ("expired", "stale"),
        ("superseded", "superseded"),
    ],
)
def test_accepted_suite_evidence_remains_readable_after_historical_rollover(
    repository_fixture,
    admission_status: str,
    freshness_status: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])
    execution = replace(
        _with_complete_evidence_link(
            record.suite_executions[0],
            admission_status=admission_status,
        ),
        technical_status="succeeded",
        evidence_result_status="failed",
        review_status="accepted",
        freshness_status=freshness_status,
        result_summary=FrozenJsonObject.from_mapping({"failedCases": 1}),
        limitations=("Synthetic cases only.",),
        started_at=record.suite_executions[0].created_at,
        completed_at=record.suite_executions[0].updated_at,
    )
    historical = replace(
        record,
        technical_status="succeeded",
        evidence_outcome="failed",
        started_at=record.created_at,
        completed_at=record.updated_at,
        suite_executions=(execution,),
    )

    evaluation_service_module._verify_run_record(historical, graph)


@pytest.mark.parametrize(
    ("parent_status", "child_status", "is_exact_aggregate"),
    [
        ("awaiting_evidence", "succeeded", False),
        ("queued", "succeeded", False),
        ("leased", "succeeded", False),
        ("running", "succeeded", False),
        ("failed", "running", True),
        ("timed_out", "succeeded", False),
        ("cancelled", "awaiting_evidence", True),
    ],
)
def test_run_verifier_requires_exact_outcome_during_child_ahead_and_cleanup_states(
    repository_fixture,
    parent_status: str,
    child_status: str,
    is_exact_aggregate: bool,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])
    execution = record.suite_executions[0]
    if child_status == "succeeded":
        execution = replace(
            execution,
            technical_status="succeeded",
            evidence_result_status="failed",
            started_at=execution.created_at,
            completed_at=execution.updated_at,
        )
    elif child_status == "running":
        execution = replace(
            execution,
            technical_status="running",
            started_at=execution.created_at,
        )
    parent_changes = {
        "technical_status": parent_status,
        "evidence_outcome": "pending",
        "suite_executions": (execution,),
    }
    if parent_status == "running":
        parent_changes["started_at"] = record.created_at
    elif parent_status in {"failed", "timed_out", "cancelled"}:
        parent_changes["completed_at"] = record.updated_at
    transitional = replace(record, **parent_changes)

    if is_exact_aggregate:
        evaluation_service_module._verify_run_record(transitional, graph)
    else:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            evaluation_service_module._verify_run_record(transitional, graph)

        assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_succeeded_evaluator_with_failed_model_is_a_valid_forward_compatible_state(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])
    execution = replace(
        record.suite_executions[0],
        technical_status="succeeded",
        evidence_result_status="failed",
        started_at=record.suite_executions[0].created_at,
        completed_at=record.suite_executions[0].updated_at,
    )
    valid = replace(
        record,
        technical_status="succeeded",
        evidence_outcome="failed",
        started_at=record.created_at,
        completed_at=record.updated_at,
        suite_executions=(execution,),
    )

    evaluation_service_module._verify_run_record(valid, graph)


def test_verdict_zero_rejects_succeeded_parent_with_non_succeeded_suite(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])
    impossible = replace(
        record,
        technical_status="succeeded",
        started_at=record.created_at,
        completed_at=record.updated_at,
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verify_run_record(impossible, graph)

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


def test_positive_verdict_version_allows_valid_layered_and_overall_decisions(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])
    execution = replace(
        _with_complete_evidence_link(record.suite_executions[0]),
        technical_status="succeeded",
        evidence_result_status="failed",
        review_status="accepted",
        started_at=record.suite_executions[0].created_at,
        completed_at=record.suite_executions[0].updated_at,
    )
    decided = replace(
        record,
        technical_status="succeeded",
        evidence_outcome="failed",
        verdict_version=1,
        overall_verdict="conditional",
        layer_verdicts=FrozenJsonObject.from_mapping(
            {
                "suites": {execution.id: "review"},
                "modalities": {},
                "components": {},
                "riskDimensions": {},
            }
        ),
        suite_executions=(execution,),
        started_at=record.created_at,
        completed_at=record.updated_at,
    )

    evaluation_service_module._verify_run_record(decided, graph)


def test_positive_verdict_version_rejects_nonterminal_pending_execution(
    repository_fixture,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])
    execution_id = record.suite_executions[0].id
    impossible = replace(
        record,
        verdict_version=1,
        overall_verdict="conditional",
        layer_verdicts=FrozenJsonObject.from_mapping(
            {
                "suites": {execution_id: "review"},
                "modalities": {},
                "components": {},
                "riskDimensions": {},
            }
        ),
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verify_run_record(impossible, graph)

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


@pytest.mark.parametrize(
    "case",
    [
        "failed-terminal",
        "cancelled-terminal",
        "unverified-admission",
        "stale-evidence",
        "expired-accepted-history",
        "superseded-accepted-history",
        "review-pending",
    ],
)
def test_positive_verdict_version_requires_succeeded_verified_current_reviewed_suites(
    repository_fixture,
    case: str,
) -> None:
    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)
    _, record, graph = _stored_run_and_graph(session, run["id"])
    execution = replace(
        _with_complete_evidence_link(record.suite_executions[0]),
        technical_status="succeeded",
        evidence_result_status="failed",
        review_status="accepted",
        freshness_status="current",
        started_at=record.suite_executions[0].created_at,
        completed_at=record.suite_executions[0].updated_at,
    )
    run_changes = {
        "technical_status": "succeeded",
        "evidence_outcome": "failed",
        "started_at": record.created_at,
        "completed_at": record.updated_at,
    }
    if case == "failed-terminal":
        execution = replace(
            execution,
            technical_status="failed",
            evidence_result_status="error",
            started_at=None,
        )
        run_changes.update(
            technical_status="failed",
            evidence_outcome="error",
            started_at=None,
        )
    elif case == "cancelled-terminal":
        execution = replace(
            execution,
            technical_status="cancelled",
            evidence_result_status="unavailable",
            started_at=None,
        )
        run_changes.update(
            technical_status="cancelled",
            evidence_outcome="unavailable",
            started_at=None,
        )
    elif case == "unverified-admission":
        execution = replace(execution, admission_status="unverified")
    elif case == "stale-evidence":
        execution = replace(execution, freshness_status="stale")
    elif case == "expired-accepted-history":
        execution = replace(
            execution,
            admission_status="expired",
            freshness_status="stale",
        )
    elif case == "superseded-accepted-history":
        execution = replace(
            execution,
            admission_status="superseded",
            freshness_status="superseded",
        )
    else:
        execution = replace(execution, review_status="pending")
    impossible = replace(
        record,
        **run_changes,
        verdict_version=1,
        overall_verdict="conditional",
        layer_verdicts=FrozenJsonObject.from_mapping(
            {
                "suites": {execution.id: "review"},
                "modalities": {},
                "components": {},
                "riskDimensions": {},
            }
        ),
        suite_executions=(execution,),
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        evaluation_service_module._verify_run_record(impossible, graph)

    assert caught.value.detail() == BINDING_INTEGRITY_DETAIL


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
        "suites": {
            execution["id"]: "insufficient" for execution in run["suiteExecutions"]
        },
        "modalities": {},
        "components": {},
        "riskDimensions": {},
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
    assert stored_run["layer_verdicts_schema_version"] == "1.0.0"
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


@pytest.mark.parametrize("read_method", ["detail", "list"])
@pytest.mark.parametrize(
    "tamper",
    [
        "event-payload",
        "sequence-gap",
        "previous-hash",
        "head-hash",
    ],
)
def test_run_reads_fail_closed_when_the_audit_chain_is_tampered(
    repository_fixture,
    read_method: str,
    tamper: str,
) -> None:
    """Catch missing runtime digest, continuity, and anchored-head verification."""

    session, _ = repository_fixture
    service = _service(session)
    _, run = _create_active_plan_and_run(service)

    if tamper == "head-hash":
        session.execute(
            text(
                "DROP TRIGGER IF EXISTS "
                "governance_evaluation_audit_chain_heads_guard_update"
            )
        )
        session.execute(
            text(
                "UPDATE governance_evaluation_audit_chain_heads "
                "SET last_event_hash = :tampered_hash WHERE org_id = :org_id"
            ),
            {"org_id": ORG, "tampered_hash": "0" * 64},
        )
    else:
        session.execute(
            text(
                "DROP TRIGGER IF EXISTS "
                "governance_evaluation_audit_events_no_update"
            )
        )
        if tamper == "event-payload":
            session.execute(
                text(
                    "UPDATE governance_evaluation_audit_events "
                    "SET actor_id = 'tampered-actor' "
                    "WHERE org_id = :org_id AND sequence_number = 1"
                ),
                {"org_id": ORG},
            )
        elif tamper == "sequence-gap":
            session.execute(
                text(
                    "UPDATE governance_evaluation_audit_events "
                    "SET sequence_number = 999 "
                    "WHERE org_id = :org_id AND sequence_number = 2"
                ),
                {"org_id": ORG},
            )
        else:
            session.execute(
                text(
                    "UPDATE governance_evaluation_audit_events "
                    "SET previous_hash = :tampered_hash "
                    "WHERE org_id = :org_id AND sequence_number = 2"
                ),
                {"org_id": ORG, "tampered_hash": "0" * 64},
            )
    session.commit()

    with pytest.raises(EvaluationWorkbenchError) as caught:
        if read_method == "detail":
            service.get_run(org_id=ORG, system_id="system-a", run_id=run["id"])
        else:
            service.list_runs(org_id=ORG, system_id="system-a")

    assert caught.value.detail() == AUDIT_CHAIN_INTEGRITY_DETAIL


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
            updated_at=completed_at,
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
            updated_at=completed_at,
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
