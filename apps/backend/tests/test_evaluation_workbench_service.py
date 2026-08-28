"""Application-service tests for the v2 evaluation workbench."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter

import pytest

from src.application.evaluation_workbench_contracts import (
    EvaluationWorkbenchError,
    _execution_view,
    _run_view,
    _verify_suite_execution_state,
)
from src.application.services.evaluation_workbench_service import EvaluationWorkbenchService
from src.application.ports.evaluation_workbench import (
    EvidenceTrustMetadataRecord,
    FrozenJsonObject,
    RunRecord,
    SuiteExecutionRecord,
)
from src.application.ports.evidence_freshness import EvidenceFreshnessClassification
import src.domain.assurance.evaluation_v2 as evaluation_v2_module
from src.domain.assurance.evaluation_v2 import (
    build_execution_envelope_v2,
    canonical_sha256,
    evaluate_preflight,
    normalize_suite_create,
)


CANONICAL_NONCE = base64.urlsafe_b64encode(bytes(range(32))).decode("ascii").rstrip("=")
EXECUTABLE_SEMVER_CASES = tuple(
    f"{major}.{minor}.{patch}"
    for major in (0, 1, 12)
    for minor in (0, 2, 34)
    for patch in (0, 3, 56)
) + (
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-0",
    "1.0.0-rc.12+cpu.1",
    "12.34.56+darwin.arm64",
)

assert len(EXECUTABLE_SEMVER_CASES) == 32


@dataclass
class _FakeRepository:
    plan_payload: dict | None = None

    def create_plan(self, **kwargs):
        self.plan_payload = kwargs
        return {"body": {"id": "plan-1", **kwargs["plan"]}, "status": 201, "replayed": False}


@dataclass
class _FakeUnitOfWork:
    repository: _FakeRepository

    def mutate(self, _command, callback):
        return callback(datetime.now(timezone.utc))


def _target(**overrides) -> dict:
    value = {
        "id": "target-1",
        "status": "active",
        "target_kind": "agent",
        "subject_kind": "agent",
        "manifest_json": (
            '{"inputs":{"scenario_set":{"kind":"content_digest","sha256":'
            '"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}},'
            '"schemaVersion":"2.0.0"}'
        ),
    }
    value.update(overrides)
    return value


def _suite(**overrides) -> dict:
    value = {
        "id": "suite-1",
        "ordinal": 0,
        "status": "active",
        "target_kinds": ["agent"],
        "subject_kinds": ["agent"],
        "lifecycle_phases": ["pre_deploy"],
        "execution_depths": ["deep"],
        "delivery_modes": ["external_provider"],
        "worker_type": "external_provider",
        "runner_image_digest": None,
        "configuration": {"threshold": 0.5},
        "configuration_schema": {
            "type": "object",
            "required": ["threshold"],
            "properties": {
                "threshold": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "additionalProperties": False,
        },
        "required_input_roles": ["scenario_set"],
    }
    value.update(overrides)
    return value


def _suite_creation_payload(version: str) -> dict:
    return {
        "namespace": "fairmind",
        "name": "agent-safety",
        "version": version,
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
            "properties": {
                "threshold": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["threshold"],
            "additionalProperties": False,
        },
        "configurationDefaults": {"threshold": 0.5},
        "requiredInputRoles": ["scenario_set"],
        "budgets": {"maxCases": 200},
        "resultContractVersion": "1.0.0",
    }


def _plan(**overrides) -> dict:
    value = {
        "status": "active",
        "lifecycle_phases": ["pre_deploy"],
        "execution_depth": "deep",
        "enforcement_mode": "human_approval",
        "delivery_mode": "external_provider",
    }
    value.update(overrides)
    return value


def test_plan_service_rejects_wrong_contract_version_before_repository() -> None:
    repository = _FakeRepository()
    service = EvaluationWorkbenchService(_FakeUnitOfWork(repository))
    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.create_plan(
            org_id="org-1",
            system_id="system-1",
            actor_id="user-1",
            idempotency_key="key-1",
            payload={"contractVersion": "1.0.0"},
        )
    assert caught.value.code == "invalid_contract_version"
    assert repository.plan_payload is None


def test_suite_execution_projection_keeps_authority_metadata_scoped_and_explicit() -> None:
    execution = SuiteExecutionRecord(
        id="suite-execution-1",
        suite_version_id="suite-version-1",
        owner_scope="org-1",
        ordinal=0,
        technical_status="succeeded",
        evidence_result_status="passed",
        admission_status="superseded",
        review_status="accepted",
        freshness_status="superseded",
        evidence_run_id="evidence-run-1",
        passport_revision_id="passport-revision-1",
        linked_by="operator-1",
        linked_at="2026-08-09T00:00:00+00:00",
        result_summary=None,
        limitations=(),
        failure_code=None,
        failure_message=None,
        started_at="2026-08-09T00:00:00+00:00",
        completed_at="2026-08-09T00:00:00+00:00",
        created_at="2026-08-09T00:00:00+00:00",
        updated_at="2026-08-09T00:00:00+00:00",
        evidence_trust=EvidenceTrustMetadataRecord(
            source_type="external_provider",
            issuer_key="issuer:assurance-lab",
            signing_key_id="key-2026-08",
            signer_key_id="key-2026-08",
            signer_algorithm="Ed25519",
            effective_expires_at="2026-08-30T00:00:00+00:00",
            reviewed_by="reviewer-1",
            reviewed_at="2026-08-09T01:00:00+00:00",
            admission_reasons=("newer passport revision recorded",),
            signing_key_revocation_reason="key rotation",
        ),
        operational_freshness=EvidenceFreshnessClassification(
            classification_status="ok",
            freshness_contract_version="1.0.0",
            recorded_freshness_status="superseded",
            effective_freshness_status="superseded",
            evaluated_at=datetime(2026, 8, 10, tzinfo=timezone.utc),
            effective_at=datetime(2026, 8, 9, tzinfo=timezone.utc),
            expiring_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
            reason_codes=("trust_policy_superseded",),
            decision_eligible=False,
        ),
    )

    view = _execution_view(execution)
    assert view["evidenceTrust"] == {
        "sourceType": "external_provider",
        "issuerKey": "issuer:assurance-lab",
        "signingKeyId": "key-2026-08",
        "signerKeyId": "key-2026-08",
        "signerAlgorithm": "Ed25519",
        "effectiveExpiresAt": "2026-08-30T00:00:00+00:00",
        "reviewedBy": "reviewer-1",
        "reviewedAt": "2026-08-09T01:00:00+00:00",
        "admissionReasons": ["newer passport revision recorded"],
    }
    assert view["freshnessStatus"] == "superseded"
    assert view["recordedFreshnessStatus"] == "superseded"
    assert view["freshnessContractVersion"] == "1.0.0"
    assert view["freshnessEvaluatedAt"] == "2026-08-10T00:00:00+00:00"
    assert view["freshnessEffectiveAt"] == "2026-08-09T00:00:00+00:00"
    assert view["expiringAt"] == "2026-08-29T00:00:00+00:00"
    assert view["freshnessReasonCodes"] == ["trust_policy_superseded"]


def test_unlinked_suite_preserves_recorded_current_without_fabricating_freshness() -> None:
    execution = SuiteExecutionRecord(
        id="suite-execution-1",
        suite_version_id="suite-version-1",
        owner_scope="org-1",
        ordinal=0,
        technical_status="awaiting_evidence",
        evidence_result_status="pending",
        admission_status="pending",
        review_status="pending",
        freshness_status="current",
        evidence_run_id=None,
        passport_revision_id=None,
        linked_by=None,
        linked_at=None,
        result_summary=None,
        limitations=None,
        failure_code=None,
        failure_message=None,
        started_at=None,
        completed_at=None,
        created_at="2026-08-09T00:00:00+00:00",
        updated_at="2026-08-09T00:00:00+00:00",
    )

    view = _execution_view(execution)

    assert view["freshnessStatus"] == "current"
    assert view["evidenceTrust"] is None
    assert "recordedFreshnessStatus" not in view
    assert "freshnessEvaluatedAt" not in view


def test_unlinked_suite_cannot_carry_an_operational_freshness_assessment() -> None:
    execution = SuiteExecutionRecord(
        id="suite-execution-1",
        suite_version_id="suite-version-1",
        owner_scope="org-1",
        ordinal=0,
        technical_status="awaiting_evidence",
        evidence_result_status="pending",
        admission_status="pending",
        review_status="pending",
        freshness_status="current",
        evidence_run_id=None,
        passport_revision_id=None,
        linked_by=None,
        linked_at=None,
        result_summary=None,
        limitations=None,
        failure_code=None,
        failure_message=None,
        started_at=None,
        completed_at=None,
        created_at="2026-08-09T00:00:00+00:00",
        updated_at="2026-08-09T00:00:00+00:00",
        operational_freshness=EvidenceFreshnessClassification(
            classification_status="ok",
            freshness_contract_version="1.0.0",
            recorded_freshness_status="current",
            effective_freshness_status="current",
            evaluated_at=datetime(2026, 8, 13, 12, tzinfo=timezone.utc),
            effective_at=datetime(2026, 8, 13, 11, tzinfo=timezone.utc),
            expiring_at=datetime(2026, 8, 13, 13, tzinfo=timezone.utc),
            reason_codes=(),
            decision_eligible=True,
        ),
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        _verify_suite_execution_state(execution)

    assert caught.value.code == "binding_integrity_error"


def test_historical_approved_verdict_remains_readable_after_evidence_revocation() -> None:
    execution = SuiteExecutionRecord(
        id="suite-execution-1",
        suite_version_id="suite-version-1",
        owner_scope="org-1",
        ordinal=0,
        technical_status="succeeded",
        evidence_result_status="passed",
        admission_status="verified",
        review_status="accepted",
        freshness_status="current",
        evidence_run_id="evidence-run-1",
        passport_revision_id="passport-revision-1",
        linked_by="operator-1",
        linked_at="2026-08-09T00:00:00+00:00",
        result_summary=None,
        limitations=(),
        failure_code=None,
        failure_message=None,
        started_at="2026-08-09T00:00:00+00:00",
        completed_at="2026-08-09T00:00:00+00:00",
        created_at="2026-08-09T00:00:00+00:00",
        updated_at="2026-08-09T01:00:00+00:00",
        evidence_trust=EvidenceTrustMetadataRecord(
            source_type="external_provider",
            issuer_key="issuer:assurance-lab",
            signing_key_id="key-2026-08",
            signer_key_id="key-2026-08",
            signer_algorithm="Ed25519",
            effective_expires_at="2026-08-30T00:00:00+00:00",
            reviewed_by="reviewer-1",
            reviewed_at="2026-08-09T01:00:00+00:00",
            admission_reasons=(),
            signing_key_revocation_reason="internal rationale must not be public",
        ),
        operational_freshness=EvidenceFreshnessClassification(
            classification_status="ok",
            freshness_contract_version="1.0.0",
            recorded_freshness_status="current",
            effective_freshness_status="stale",
            evaluated_at=datetime(2026, 8, 13, 12, tzinfo=timezone.utc),
            effective_at=datetime(2026, 8, 12, 9, tzinfo=timezone.utc),
            expiring_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
            reason_codes=("evaluator_registration_revoked",),
            decision_eligible=False,
        ),
    )
    run = RunRecord(
        id="run-1",
        organization_id="org-1",
        workspace_id="workspace-1",
        system_id="system-1",
        plan_id="plan-1",
        contract_version="2.0.0",
        trigger="manual",
        lifecycle_phase="pre_deploy",
        technical_status="succeeded",
        evidence_outcome="passed",
        overall_verdict="approved",
        layer_verdicts_schema_version="1.0.0",
        layer_verdicts=FrozenJsonObject.from_mapping(
            {
                "suites": {"suite-execution-1": "approved"},
                "modalities": {},
                "components": {},
                "riskDimensions": {},
            }
        ),
        suite_executions=(execution,),
        envelope_id="envelope-1",
        envelope_nonce=CANONICAL_NONCE,
        envelope=FrozenJsonObject.from_mapping({"schemaVersion": "2.0.0"}),
        envelope_hash="a" * 64,
        verdict_version=1,
        requested_by="requester-1",
        started_at="2026-08-09T00:00:00+00:00",
        completed_at="2026-08-09T00:00:00+00:00",
        failure_code=None,
        failure_message=None,
        created_at="2026-08-09T00:00:00+00:00",
        updated_at="2026-08-09T01:00:00+00:00",
    )

    view = _run_view(run)

    assert view["overallVerdict"] == "approved"
    assert view["verdictVersion"] == 1
    assert view["decisionEvidenceCurrentlyEligible"] is False
    assert view["suiteExecutions"][0]["freshnessStatus"] == "stale"
    assert "signingKeyRevocationReason" not in view["suiteExecutions"][0]["evidenceTrust"]


def test_preflight_success_has_no_blockers() -> None:
    plan, target, trust, suites = _fully_bound_preflight_graph()
    result = evaluate_preflight(
        plan=plan,
        target=target,
        trust_policy=trust,
        suites=suites,
        lifecycle_phase="pre_deploy",
    )
    assert result == []


def _fully_bound_preflight_graph(
    *, suite_ref: str = "fairmind/agent-safety@1.0.0"
) -> tuple[dict, dict, dict, list[dict]]:
    target = _target(
        target_key="agent-prod",
        version="1.0.0",
        system_version="2026.07",
        subject_id="agent-prod",
        subject_version="sha-1",
        subject_digest="b" * 64,
        deployment_id="deploy-1",
        connector_binding_id=None,
        manifest_digest="c" * 64,
    )
    trust = {
        "id": "trust-1",
        "version": "1.0.0",
        "policy_hash": "d" * 64,
        "status": "active",
    }
    configuration = {"threshold": 0.5}
    suites = [
        _suite(
            owner_scope="org-1",
            suite_ref=suite_ref,
            manifest_digest="e" * 64,
            adapter_name="inspect",
            adapter_version="0.3.0",
            result_contract_version="1.0.0",
            configuration=configuration,
            configuration_hash=canonical_sha256(configuration),
            budgets={"maxCases": 200},
        )
    ]
    return _plan(), target, trust, suites


def test_preflight_clean_binding_projection_can_build_an_execution_envelope() -> None:
    plan, target, trust, suites = _fully_bound_preflight_graph()

    blockers = evaluate_preflight(
        plan=plan,
        target=target,
        trust_policy=trust,
        suites=suites,
        lifecycle_phase="pre_deploy",
    )
    target_binding, trust_binding, suite_bindings = (
        evaluation_v2_module._preflight_envelope_variable_projection(
            target=target,
            trust_policy=trust,
            suites=suites,
        )
    )

    assert blockers == []
    envelope, _, _ = build_execution_envelope_v2(
        envelope_id="envelope-1",
        run_id="run-1",
        org_id="org-1",
        workspace_id="workspace-1",
        system_id="system-1",
        plan_id="plan-1",
        plan_content_hash="a" * 64,
        target=target_binding,
        trigger="release_gate",
        lifecycle_phase="pre_deploy",
        execution_depth="deep",
        enforcement_mode="human_approval",
        delivery_mode="external_provider",
        trust_policy=trust_binding,
        nonce=CANONICAL_NONCE,
        requester_id="user-1",
        requested_at="2026-07-20T00:00:00+00:00",
        suites=suite_bindings,
    )
    assert envelope["suites"][0]["suiteRef"] == "fairmind/agent-safety@1.0.0"


@pytest.mark.parametrize(
    "version",
    EXECUTABLE_SEMVER_CASES,
)
def test_preflight_clean_suite_ref_uses_the_same_envelope_grammar(
    version: str,
) -> None:
    created_suite = normalize_suite_create(
        _suite_creation_payload(version),
        owner_scope="org-1",
    )
    suite_ref = created_suite["suiteRef"]
    plan, target, trust, suites = _fully_bound_preflight_graph(suite_ref=suite_ref)

    blockers = evaluate_preflight(
        plan=plan,
        target=target,
        trust_policy=trust,
        suites=suites,
        lifecycle_phase="pre_deploy",
    )
    target_binding, trust_binding, suite_bindings = (
        evaluation_v2_module._preflight_envelope_variable_projection(
            target=target,
            trust_policy=trust,
            suites=suites,
        )
    )
    envelope, _, _ = build_execution_envelope_v2(
        envelope_id="envelope-1",
        run_id="run-1",
        org_id="org-1",
        workspace_id="workspace-1",
        system_id="system-1",
        plan_id="plan-1",
        plan_content_hash="a" * 64,
        target=target_binding,
        trigger="release_gate",
        lifecycle_phase="pre_deploy",
        execution_depth="deep",
        enforcement_mode="human_approval",
        delivery_mode="external_provider",
        trust_policy=trust_binding,
        nonce=CANONICAL_NONCE,
        requester_id="user-1",
        requested_at="2026-07-20T00:00:00+00:00",
        suites=suite_bindings,
    )

    assert blockers == []
    assert envelope["suites"][0]["suiteRef"] == suite_ref


def test_preflight_marks_a_binding_invalid_before_run_construction() -> None:
    plan, target, trust, suites = _fully_bound_preflight_graph()
    suites[0]["suite_ref"] = "fairmind/agent-safety@1"

    blockers = evaluate_preflight(
        plan=plan,
        target=target,
        trust_policy=trust,
        suites=suites,
        lifecycle_phase="pre_deploy",
    )

    assert "execution_binding_invalid" in {blocker.code for blocker in blockers}


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (("plan", {"status": "draft"}), "plan_inactive"),
        (("plan", {"lifecycle_phases": ["post_deploy"]}), "lifecycle_phase_not_planned"),
        (("target", {"status": "retired"}), "target_not_active"),
        (("trust", {"status": "retired"}), "trust_policy_not_active"),
        (("suite", {"status": "draft"}), "suite_not_active"),
        (("suite", {"target_kinds": ["llm_application"]}), "suite_target_kind_unsupported"),
        (("suite", {"subject_kinds": ["llm"]}), "suite_subject_kind_unsupported"),
        (("suite", {"lifecycle_phases": ["post_deploy"]}), "suite_lifecycle_phase_unsupported"),
        (("suite", {"execution_depths": ["inline"]}), "suite_execution_depth_unsupported"),
        (("suite", {"delivery_modes": ["imported_report"]}), "suite_delivery_mode_unsupported"),
        (("suite", {"configuration": {}}), "suite_configuration_invalid"),
        (("suite", {"required_input_roles": ["missing"]}), "required_input_role_missing"),
        (("suite", {"worker_type": "fairmind_worker"}), "runner_image_missing"),
        (("plan", {"delivery_mode": "fairmind_worker"}), "worker_unavailable"),
        (("plan", {"enforcement_mode": "automatic"}), "automatic_enforcement_disabled"),
    ],
)
def test_preflight_reports_each_stable_blocker(change, expected) -> None:
    plan, target, trust, suite = _plan(), _target(), {"status": "active"}, _suite()
    scope, values = change
    if scope == "plan":
        plan.update(values)
    elif scope == "target":
        target.update(values)
    elif scope == "trust":
        trust.update(values)
    else:
        suite.update(values)
    codes = [
        blocker.code
        for blocker in evaluate_preflight(
            plan=plan,
            target=target,
            trust_policy=trust,
            suites=[suite],
            lifecycle_phase="pre_deploy",
        )
    ]
    assert expected in codes


def test_preflight_blocker_order_is_global_then_suite_ordinal_then_code() -> None:
    suites = [
        _suite(id="suite-2", ordinal=2, status="draft", target_kinds=[]),
        _suite(id="suite-1", ordinal=1, status="draft", target_kinds=[]),
    ]
    blockers = evaluate_preflight(
        plan=_plan(status="draft", enforcement_mode="automatic"),
        target=_target(status="retired"),
        trust_policy={"status": "retired"},
        suites=suites,
        lifecycle_phase="pre_deploy",
    )
    keys = [
        (item.suite_ordinal if item.suite_ordinal is not None else -1, item.code)
        for item in blockers
    ]
    assert keys == sorted(keys)


def test_any_fairmind_worker_suite_blocks_even_under_external_delivery() -> None:
    blockers = evaluate_preflight(
        plan=_plan(delivery_mode="external_provider"),
        target=_target(),
        trust_policy={"status": "active"},
        suites=[
            _suite(
                worker_type="fairmind_worker",
                runner_image_digest="sha256:" + "a" * 64,
            )
        ],
        lifecycle_phase="pre_deploy",
    )
    assert "worker_unavailable" in [item.code for item in blockers]


def test_preflight_blocks_an_execution_envelope_over_448_kib() -> None:
    roles = [f"input_{index:02d}" for index in range(32)]
    inputs = {
        role: {
            "kind": "content_digest",
            "sha256": "a" * 64,
            "mediaType": "video/mp4",
            "sizeBytes": 2**53 - 1,
        }
        for role in roles
    }
    configuration = {"checks": [False] * 1360}
    configuration_schema = {
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
    target = _target(
        target_key="agent-prod",
        version="1.0.0",
        system_version="2026.07",
        subject_id="agent-prod",
        subject_version="sha-1",
        subject_digest="b" * 64,
        deployment_id=None,
        connector_binding_id=None,
        manifest={"schemaVersion": "2.0.0", "inputs": inputs},
        manifest_digest="c" * 64,
    )
    suites = [
        _suite(
            id=f"suite-{index}",
            ordinal=index,
            owner_scope="org-1",
            suite_ref=f"fairmind/suite-{index}@1.0.0",
            manifest_digest="d" * 64,
            adapter_name="inspect",
            adapter_version="1.0.0",
            result_contract_version="1.0.0",
            configuration=configuration,
            configuration_hash="e" * 64,
            configuration_schema=configuration_schema,
            required_input_roles=roles,
            budgets={"maxCases": 200},
        )
        for index in range(32)
    ]

    blockers = evaluate_preflight(
        plan=_plan(),
        target=target,
        trust_policy={
            "id": "trust-a",
            "version": "1.0.0",
            "policy_hash": "f" * 64,
            "status": "active",
        },
        suites=suites,
        lifecycle_phase="pre_deploy",
    )

    assert "execution_envelope_size_exceeded" in [item.code for item in blockers]


def test_three_phase_preflight_bounds_aggregate_schema_complexity_and_latency() -> None:
    schema = {
        "type": "object",
        "properties": {
            f"flag_{index}": {"type": "boolean"} for index in range(180)
        },
        "additionalProperties": False,
    }
    suites = [
        _suite(
            id=f"suite-{index}",
            ordinal=index,
            lifecycle_phases=["pre_deploy", "realtime", "post_deploy"],
            configuration={},
            configuration_schema=schema,
            required_input_roles=[],
        )
        for index in range(32)
    ]
    plan = _plan(lifecycle_phases=["pre_deploy", "realtime", "post_deploy"])

    started = perf_counter()
    results = [
        evaluate_preflight(
            plan=plan,
            target=_target(),
            trust_policy={"status": "active"},
            suites=suites,
            lifecycle_phase=phase,
        )
        for phase in plan["lifecycle_phases"]
    ]
    elapsed = perf_counter() - started

    assert all(
        "plan_schema_complexity_exceeded" in {blocker.code for blocker in blockers}
        for blockers in results
    )
    assert elapsed < 1.0
