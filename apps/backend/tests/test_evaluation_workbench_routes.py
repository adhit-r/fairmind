"""HTTP contract tests for additive evaluation-v2 routes."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from config.auth import TokenData, TokenType, UserRole, get_current_active_user
from database.connection import Base, get_db
from database.governance_models import (
    GovernanceAISystem,
    GovernanceEvaluationAuditEvent,
    GovernanceEvaluationPlan,
    GovernanceEvaluationRun,
    GovernanceEvaluationRunSuiteExecution,
    GovernanceEvaluationTargetVersion,
    GovernanceEvidenceTrustPolicyVersion,
    GovernanceIdempotencyRecord,
    GovernanceWorkspace,
)
from database.models import Organization, OrganizationMember, User
from src.domain.assurance.evaluation_v2 import canonical_sha256

ORG = str(uuid.uuid4())
FOREIGN_ORG = str(uuid.uuid4())
USER = str(uuid.uuid4())
VIEWER = str(uuid.uuid4())
BASE = f"/api/v1/ai-governance/organizations/{ORG}"
FOREIGN_BASE = f"/api/v1/ai-governance/organizations/{FOREIGN_ORG}"


def _token(user_id: str) -> TokenData:
    now = datetime.now(timezone.utc)
    return TokenData(
        user_id=user_id,
        email=f"{user_id}@example.test",
        role=UserRole.ANALYST,
        token_type=TokenType.ACCESS,
        iat=now,
        exp=now,
    )


@pytest.fixture
def workbench_client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys = ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    for user_id in (USER, VIEWER):
        session.execute(
            User.__table__.insert().values(
                id=uuid.UUID(user_id), email=f"{user_id}@example.test", username=user_id
            )
        )
    session.execute(
        Organization.__table__.insert().values(
            id=uuid.UUID(ORG), name="Org", slug=ORG, owner_id=uuid.UUID(USER)
        )
    )
    session.execute(
        Organization.__table__.insert().values(
            id=uuid.UUID(FOREIGN_ORG),
            name="Foreign Org",
            slug=FOREIGN_ORG,
            owner_id=uuid.UUID(USER),
        )
    )
    for user_id, role in ((USER, "admin"), (VIEWER, "viewer")):
        session.execute(
            OrganizationMember.__table__.insert().values(
                id=uuid.uuid4(),
                org_id=uuid.UUID(ORG),
                user_id=uuid.UUID(user_id),
                role=role,
                status="active",
            )
        )
    session.execute(
        OrganizationMember.__table__.insert().values(
            id=uuid.uuid4(),
            org_id=uuid.UUID(FOREIGN_ORG),
            user_id=uuid.UUID(USER),
            role="admin",
            status="active",
        )
    )
    session.execute(
        GovernanceWorkspace.__table__.insert().values(
            id="workspace-a", org_id=ORG, name="workspace-a"
        )
    )
    session.execute(
        GovernanceAISystem.__table__.insert().values(
            id="system-a", workspace_id="workspace-a", org_id=ORG, name="system-a"
        )
    )
    session.execute(
        GovernanceWorkspace.__table__.insert().values(
            id="workspace-b", org_id=FOREIGN_ORG, name="workspace-b"
        )
    )
    session.execute(
        GovernanceAISystem.__table__.insert().values(
            id="system-b",
            workspace_id="workspace-b",
            org_id=FOREIGN_ORG,
            name="system-b",
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
            created_at=now_iso(),
        )
    )
    session.execute(
        GovernanceEvidenceTrustPolicyVersion.__table__.insert().values(
            id="trust-b",
            org_id=FOREIGN_ORG,
            version="1.0.0",
            policy_json="{}",
            policy_hash=canonical_sha256({}),
            maximum_evidence_age_seconds=86400,
            unsigned_import_policy="manual_review",
            status="active",
            created_by=USER,
            created_at=now_iso(),
        )
    )
    session.commit()
    session.close()
    active = {"token": _token(USER)}

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    async def override_user():
        return active["token"]

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_active_user] = override_user
    try:
        with TestClient(app) as client:
            yield client, active
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


def _target_payload() -> dict:
    return {
        "targetKey": "agent-prod",
        "targetKind": "agent",
        "version": "1.0.0",
        "systemVersion": "2026.07",
        "subjectKind": "agent",
        "subjectId": "agent-prod",
        "subjectVersion": "sha-1",
        "subjectDigest": "b" * 64,
        "manifest": {"inputs": {"scenario_set": {"sha256": "c" * 64}}},
    }


def _suite_payload() -> dict:
    return {
        "namespace": "fairmind",
        "name": "agent-safety",
        "version": "1.0.0",
        "supportedTargetKinds": ["agent"],
        "supportedSubjectKinds": ["agent"],
        "lifecyclePhases": ["pre_deploy"],
        "executionDepths": ["deep"],
        "deliveryModes": ["external_provider"],
        "workerType": "external_provider",
        "adapterName": "inspect",
        "adapterVersion": "0.3.0",
        "configurationSchema": {"type": "object", "additionalProperties": False},
        "configurationDefaults": {},
        "requiredInputRoles": ["scenario_set"],
        "budgets": {"maxCases": 200},
        "resultContractVersion": "1.0.0",
    }


def _bootstrap(
    client: TestClient,
    *,
    base: str = BASE,
    system_id: str = "system-a",
):
    target = client.post(
        f"{base}/systems/{system_id}/evaluation-v2/target-versions",
        headers=_headers("target"),
        json=_target_payload(),
    )
    assert target.status_code == 201, target.text
    suite = client.post(
        f"{base}/evaluation-v2/suite-versions",
        headers=_headers("suite"),
        json=_suite_payload(),
    )
    assert suite.status_code == 201, suite.text
    activation = client.post(
        f"{base}/evaluation-v2/suite-versions/{suite.json()['id']}/activate",
        headers=_headers("suite-activate"),
    )
    assert activation.status_code == 200, activation.text
    return target.json(), suite.json()


def _create_active_v2_plan_and_run(
    client: TestClient,
    *,
    base: str = BASE,
    system_id: str = "system-a",
    trust_policy_id: str = "trust-a",
) -> tuple[dict, dict]:
    target, suite = _bootstrap(client, base=base, system_id=system_id)
    plans_url = f"{base}/systems/{system_id}/evaluation-v2/plans"
    created = client.post(
        plans_url,
        headers=_headers("plan"),
        json={
            "contractVersion": "2.0.0",
            "name": "Bound plan",
            "targetVersionId": target["id"],
            "lifecyclePhases": ["pre_deploy"],
            "executionDepth": "deep",
            "enforcementMode": "human_approval",
            "deliveryMode": "external_provider",
            "trustPolicyVersionId": trust_policy_id,
            "suites": [{"suiteVersionId": suite["id"]}],
        },
    )
    assert created.status_code == 201, created.text
    plan = created.json()
    activation = client.post(
        f"{plans_url}/{plan['id']}/activate",
        headers=_headers("plan-activate"),
    )
    assert activation.status_code == 200, activation.text
    created_run = client.post(
        f"{plans_url}/{plan['id']}/runs",
        headers=_headers("run"),
        json={"trigger": "manual", "lifecyclePhase": "pre_deploy"},
    )
    assert created_run.status_code == 201, created_run.text
    return plan, created_run.json()


def test_complete_additive_route_flow_and_three_axis_run(workbench_client) -> None:
    client, _ = workbench_client
    target, suite = _bootstrap(client)
    plan_payload = {
        "contractVersion": "2.0.0",
        "name": "Agent release assurance",
        "targetVersionId": target["id"],
        "lifecyclePhases": ["pre_deploy"],
        "executionDepth": "deep",
        "enforcementMode": "human_approval",
        "deliveryMode": "external_provider",
        "trustPolicyVersionId": "trust-a",
        "suites": [{"suiteVersionId": suite["id"]}],
    }
    plans_url = f"{BASE}/systems/system-a/evaluation-v2/plans"
    created = client.post(plans_url, headers=_headers("plan"), json=plan_payload)
    assert created.status_code == 201, created.text
    assert created.json()["targetVersionId"] == target["id"]
    assert client.get(plans_url).json()[0]["id"] == created.json()["id"]
    preflight_draft = client.get(
        f"{plans_url}/{created.json()['id']}/preflight",
        params={"lifecyclePhase": "pre_deploy"},
    )
    assert preflight_draft.status_code == 200
    assert preflight_draft.json()["canCreateRun"] is False
    assert preflight_draft.json()["blockers"][0]["code"] == "plan_inactive"
    activated = client.post(
        f"{plans_url}/{created.json()['id']}/activate",
        headers=_headers("plan-activate"),
    )
    assert activated.status_code == 200, activated.text
    run = client.post(
        f"{plans_url}/{created.json()['id']}/runs",
        headers=_headers("run"),
        json={"trigger": "release_gate", "lifecyclePhase": "pre_deploy"},
    )
    assert run.status_code == 201, run.text
    body = run.json()
    assert body["technicalStatus"] == "awaiting_evidence"
    assert body["evidenceOutcome"] == "pending"
    assert body["overallVerdict"] == "insufficient"
    assert len(body["suiteExecutions"]) == 1
    runs_url = f"{BASE}/systems/system-a/evaluation-v2/runs"
    assert client.get(runs_url).json()[0]["id"] == body["id"]
    assert client.get(f"{runs_url}/{body['id']}").json()["envelopeHash"] == body["envelopeHash"]


def test_missing_or_malformed_idempotency_key_and_viewer_mutation_are_rejected(
    workbench_client,
) -> None:
    client, active = workbench_client
    url = f"{BASE}/systems/system-a/evaluation-v2/target-versions"
    assert client.post(url, json=_target_payload()).status_code == 422
    malformed = client.post(
        url, headers={"Idempotency-Key": "contains space"}, json=_target_payload()
    )
    assert malformed.status_code == 422
    assert malformed.json()["detail"]["code"] == "invalid_idempotency_key"
    active["token"] = _token(VIEWER)
    assert client.post(url, headers=_headers("viewer"), json=_target_payload()).status_code == 403


def test_idempotency_replay_header_and_conflict(workbench_client) -> None:
    client, _ = workbench_client
    url = f"{BASE}/systems/system-a/evaluation-v2/target-versions"
    first = client.post(url, headers=_headers("target"), json=_target_payload())
    replay = client.post(url, headers=_headers("target"), json=_target_payload())
    assert first.status_code == replay.status_code == 201
    assert first.content == replay.content
    assert replay.headers["Idempotency-Replayed"] == "true"
    changed = {**_target_payload(), "targetKey": "other"}
    conflict = client.post(url, headers=_headers("target"), json=changed)
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "idempotency_conflict"


@pytest.mark.parametrize(
    ("body", "expected_status"),
    [
        (b'{"targetKey":"a","targetKey":"b"}', 422),
        (
            b'{"targetKey":"agent-prod","targetKind":"agent","version":"1.0.0",'
            b'"systemVersion":"2026.07","subjectKind":"agent","subjectId":"agent-prod",'
            b'"subjectVersion":"sha-1","subjectDigest":"'
            + b"b" * 64
            + b'","manifest":{"inputs":{"scenario_set":{"sha256":"'
            + b"c" * 64
            + b'"}},"nested":{"key":1,"key":2}}}',
            422,
        ),
        (b'{"targetKey":1e400}', 422),
        ((b'{"targetKey":"a","manifest":' + b'{"x":' * 40 + b"0" + b"}" * 40 + b"}"), 422),
        (b'{"targetKey":"' + b"a" * (1024 * 1024) + b'"}', 413),
    ],
)
def test_raw_http_strict_json_rejections(
    workbench_client, body: bytes, expected_status: int
) -> None:
    client, _ = workbench_client
    response = client.post(
        f"{BASE}/systems/system-a/evaluation-v2/target-versions",
        headers={**_headers("raw"), "Content-Type": "application/json"},
        content=body,
    )
    assert response.status_code == expected_status
    session_iterator = app.dependency_overrides[get_db]()
    session = next(session_iterator)
    try:
        assert (
            session.scalar(
                select(func.count()).select_from(GovernanceEvaluationTargetVersion.__table__)
            )
            == 0
        )
        assert (
            session.scalar(select(func.count()).select_from(GovernanceIdempotencyRecord.__table__))
            == 0
        )
        assert (
            session.scalar(
                select(func.count()).select_from(GovernanceEvaluationAuditEvent.__table__)
            )
            == 0
        )
    finally:
        session_iterator.close()


def test_request_boundary_accepts_aliases_only_and_rejects_derived_fields(
    workbench_client,
) -> None:
    client, _ = workbench_client
    target_url = f"{BASE}/systems/system-a/evaluation-v2/target-versions"
    snake_case = _target_payload()
    snake_case["target_key"] = snake_case.pop("targetKey")
    response = client.post(
        target_url,
        headers=_headers("snake-case-target"),
        json=snake_case,
    )
    assert response.status_code == 422

    target, suite = _bootstrap(client)
    plans_url = f"{BASE}/systems/system-a/evaluation-v2/plans"
    valid_plan = {
        "contractVersion": "2.0.0",
        "name": "Bound plan",
        "targetVersionId": target["id"],
        "lifecyclePhases": ["pre_deploy"],
        "executionDepth": "deep",
        "enforcementMode": "human_approval",
        "deliveryMode": "external_provider",
        "trustPolicyVersionId": "trust-a",
        "suites": [{"suiteVersionId": suite["id"]}],
    }
    session_iterator = app.dependency_overrides[get_db]()
    session = next(session_iterator)
    try:
        baseline_idempotency = session.scalar(
            select(func.count()).select_from(GovernanceIdempotencyRecord.__table__)
        )
        baseline_audit = session.scalar(
            select(func.count()).select_from(GovernanceEvaluationAuditEvent.__table__)
        )
    finally:
        session_iterator.close()

    for index, derived in enumerate(
        (
            {"targetKind": "agent"},
            {"ownerScope": ORG},
            {"planContentHash": "a" * 64},
            {"status": "active"},
            {"id": "caller-controlled"},
        )
    ):
        rejected = client.post(
            plans_url,
            headers=_headers(f"derived-{index}"),
            json={**valid_plan, **derived},
        )
        assert rejected.status_code == 422

    session_iterator = app.dependency_overrides[get_db]()
    session = next(session_iterator)
    try:
        assert (
            session.scalar(select(func.count()).select_from(GovernanceEvaluationPlan.__table__))
            == 0
        )
        assert (
            session.scalar(select(func.count()).select_from(GovernanceIdempotencyRecord.__table__))
            == baseline_idempotency
        )
        assert (
            session.scalar(
                select(func.count()).select_from(GovernanceEvaluationAuditEvent.__table__)
            )
            == baseline_audit
        )
    finally:
        session_iterator.close()


def test_validation_errors_never_reflect_rejected_secret_values(
    workbench_client,
) -> None:
    client, _ = workbench_client
    sentinel = "FAIRMIND-SENTINEL-SECRET-DO-NOT-ECHO"
    response = client.post(
        f"{BASE}/systems/system-a/evaluation-v2/target-versions",
        headers=_headers("secret-error"),
        json={**_target_payload(), "password": sentinel},
    )
    assert response.status_code == 422
    assert sentinel not in response.text


def test_openapi_exposes_strict_request_and_response_contracts() -> None:
    app.openapi_schema = None
    document = app.openapi()
    prefix = "/api/v1/ai-governance/organizations/{org_id}"
    target_path = f"{prefix}/systems/{{system_id}}/evaluation-v2/target-versions"
    plan_path = f"{prefix}/systems/{{system_id}}/evaluation-v2/plans"
    run_path = f"{prefix}/systems/{{system_id}}/evaluation-v2/plans/{{plan_id}}/runs"

    target_operation = document["paths"][target_path]["post"]
    target_request = target_operation["requestBody"]["content"]["application/json"]["schema"]
    assert target_request["additionalProperties"] is False
    assert "targetKey" in target_request["required"]
    assert "target_key" not in target_request["properties"]
    for derived in ("id", "manifestDigest", "status", "ownerScope"):
        assert derived not in target_request["properties"]
    assert target_operation["responses"]["201"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/TargetVersionResponse"
    }

    plan_request = document["paths"][plan_path]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    assert plan_request["additionalProperties"] is False
    assert {
        "contractVersion",
        "targetVersionId",
        "lifecyclePhases",
        "suites",
    }.issubset(plan_request["required"])
    for derived in ("targetKind", "ownerScope", "planContentHash", "status", "id"):
        assert derived not in plan_request["properties"]
    suite_selection = plan_request["properties"]["suites"]["items"]
    assert "configuration" not in suite_selection["required"]
    assert suite_selection["properties"]["configuration"]["type"] == "object"

    run_operation = document["paths"][run_path]["post"]
    run_request = run_operation["requestBody"]["content"]["application/json"]["schema"]
    assert run_request["additionalProperties"] is False
    assert set(run_request["required"]) == {"trigger", "lifecyclePhase"}
    assert run_operation["responses"]["201"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/EvaluationRunV2Response"
    }

    schemas = document["components"]["schemas"]
    run_response = schemas["EvaluationRunV2Response"]
    assert run_response["additionalProperties"] is False
    assert {
        "technicalStatus",
        "evidenceOutcome",
        "overallVerdict",
        "layerVerdicts",
        "suiteExecutions",
        "envelopeHash",
        "verdictVersion",
    }.issubset(run_response["required"])
    suite_execution = schemas["SuiteExecutionResponse"]
    assert suite_execution["properties"]["admissionStatus"]["enum"] == [
        "pending",
        "verified",
        "unverified",
        "expired",
        "superseded",
        "rejected",
        "trust_error",
    ]
    assert suite_execution["properties"]["reviewStatus"]["enum"] == [
        "pending",
        "accepted",
        "rejected",
    ]

    def assert_refs_resolve(value) -> None:
        if isinstance(value, dict):
            reference = value.get("$ref")
            if reference is not None:
                assert reference.startswith("#/")
                resolved = document
                for part in reference.removeprefix("#/").split("/"):
                    resolved = resolved[part.replace("~1", "/").replace("~0", "~")]
                assert resolved is not None
            for child in value.values():
                assert_refs_resolve(child)
        elif isinstance(value, list):
            for child in value:
                assert_refs_resolve(child)

    for operation in (
        target_operation,
        document["paths"][f"{prefix}/evaluation-v2/suite-versions"]["post"],
        document["paths"][plan_path]["post"],
        run_operation,
    ):
        assert_refs_resolve(operation["requestBody"])
        assert_refs_resolve(operation["responses"])


def test_suite_configuration_is_omittable_but_never_nullable(workbench_client) -> None:
    client, _ = workbench_client
    target, suite = _bootstrap(client)
    response = client.post(
        f"{BASE}/systems/system-a/evaluation-v2/plans",
        headers=_headers("null-suite-configuration"),
        json={
            "contractVersion": "2.0.0",
            "name": "Null configuration must fail",
            "targetVersionId": target["id"],
            "lifecyclePhases": ["pre_deploy"],
            "executionDepth": "deep",
            "enforcementMode": "human_approval",
            "deliveryMode": "external_provider",
            "trustPolicyVersionId": "trust-a",
            "suites": [{"suiteVersionId": suite["id"], "configuration": None}],
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_request"
    assert client.get(f"{BASE}/systems/system-a/evaluation-v2/plans").json() == []


def test_response_contract_keeps_execution_evidence_and_governance_axes_distinct(
    workbench_client,
) -> None:
    client, _ = workbench_client
    _, run = _create_active_v2_plan_and_run(client)
    timestamp = now_iso()
    session_iterator = app.dependency_overrides[get_db]()
    session = next(session_iterator)
    try:
        session.execute(
            GovernanceEvaluationRunSuiteExecution.__table__.update()
            .where(GovernanceEvaluationRunSuiteExecution.run_id == run["id"])
            .values(
                technical_status="succeeded",
                evidence_result_status="failed",
                started_at=timestamp,
                completed_at=timestamp,
            )
        )
        session.execute(
            GovernanceEvaluationRun.__table__.update()
            .where(GovernanceEvaluationRun.id == run["id"])
            .values(
                technical_status="succeeded",
                evidence_outcome="failed",
                overall_verdict="insufficient",
                started_at=timestamp,
                completed_at=timestamp,
            )
        )
        session.commit()
    finally:
        session_iterator.close()

    response = client.get(f"{BASE}/systems/system-a/evaluation-v2/runs/{run['id']}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["technicalStatus"] == "succeeded"
    assert body["evidenceOutcome"] == "failed"
    assert body["suiteExecutions"][0]["technicalStatus"] == "succeeded"
    assert body["suiteExecutions"][0]["evidenceResultStatus"] == "failed"
    assert body["overallVerdict"] == "insufficient"


def test_v2_plan_is_hidden_from_every_v1_plan_read_and_run_creation_surface(
    workbench_client,
) -> None:
    client, _ = workbench_client
    plan, _ = _create_active_v2_plan_and_run(client)
    v1_url = f"{BASE}/systems/system-a/evaluation-plans"

    assert client.get(v1_url).json() == []

    preflight = client.get(f"{v1_url}/{plan['id']}/preflight")
    assert preflight.status_code == 404
    assert preflight.json() == {
        "detail": {
            "code": "passport_scope_mismatch",
            "message": "Evaluation plan not found in this AI system scope.",
            "nextAction": "Refresh the plan list and select an available plan.",
        }
    }

    expected_contract_error = {
        "detail": {
            "code": "contract_version_requires_v2",
            "message": "Assurance-contract v2 records must use the evaluation-v2 workflow.",
            "nextAction": "Use the corresponding evaluation-v2 endpoint for this scoped record.",
        }
    }
    activation = client.post(f"{v1_url}/{plan['id']}/activate")
    assert activation.status_code == 409
    assert activation.json() == expected_contract_error

    run_creation = client.post(
        f"{v1_url}/{plan['id']}/runs",
        json={"trigger": "manual"},
    )
    assert run_creation.status_code == 409
    assert run_creation.json() == expected_contract_error


def test_v2_run_is_hidden_from_v1_reads_and_rejected_by_v1_passport_link(
    workbench_client,
) -> None:
    client, _ = workbench_client
    _, run = _create_active_v2_plan_and_run(client)
    v1_runs_url = f"{BASE}/systems/system-a/evaluation-runs"

    assert client.get(v1_runs_url).json() == []
    detail = client.get(f"{v1_runs_url}/{run['id']}")
    assert detail.status_code == 404
    assert detail.json() == {
        "detail": {
            "code": "passport_scope_mismatch",
            "message": "Evaluation run not found in this AI system scope.",
            "nextAction": "Refresh the run list and select an available run.",
        }
    }

    link = client.post(
        f"{v1_runs_url}/{run['id']}/evidence-passport-link",
        json={
            "evidenceRunId": "evidence-v1",
            "passportRevisionId": "passport-revision-v1",
        },
    )
    assert link.status_code == 409
    assert link.json() == {
        "detail": {
            "code": "contract_version_requires_v2",
            "message": "Assurance-contract v2 records must use the evaluation-v2 workflow.",
            "nextAction": "Use the corresponding evaluation-v2 endpoint for this scoped record.",
        }
    }


def test_foreign_tenant_v2_plan_and_run_ids_are_not_found_by_v1_routes(
    workbench_client,
) -> None:
    client, _ = workbench_client
    foreign_plan, foreign_run = _create_active_v2_plan_and_run(
        client,
        base=FOREIGN_BASE,
        system_id="system-b",
        trust_policy_id="trust-b",
    )
    local_plans_url = f"{BASE}/systems/system-a/evaluation-plans"
    local_runs_url = f"{BASE}/systems/system-a/evaluation-runs"

    foreign_plan_preflight = client.get(f"{local_plans_url}/{foreign_plan['id']}/preflight")
    foreign_plan_activation = client.post(f"{local_plans_url}/{foreign_plan['id']}/activate")
    foreign_run_creation = client.post(
        f"{local_plans_url}/{foreign_plan['id']}/runs",
        json={"trigger": "manual"},
    )
    foreign_run_detail = client.get(f"{local_runs_url}/{foreign_run['id']}")
    foreign_run_link = client.post(
        f"{local_runs_url}/{foreign_run['id']}/evidence-passport-link",
        json={
            "evidenceRunId": "foreign-evidence",
            "passportRevisionId": "foreign-passport-revision",
        },
    )

    for response in (
        foreign_plan_preflight,
        foreign_plan_activation,
        foreign_run_creation,
        foreign_run_detail,
        foreign_run_link,
    ):
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "passport_scope_mismatch"
