"""Application-service tests for the v2 evaluation workbench."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter

import pytest

from src.application.services.evaluation_workbench_service import (
    EvaluationWorkbenchError,
    EvaluationWorkbenchService,
)
from src.domain.assurance.evaluation_v2 import evaluate_preflight


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


def test_preflight_success_has_no_blockers() -> None:
    result = evaluate_preflight(
        plan=_plan(),
        target=_target(),
        trust_policy={"status": "active"},
        suites=[_suite()],
        lifecycle_phase="pre_deploy",
    )
    assert result == []


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
