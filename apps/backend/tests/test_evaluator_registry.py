"""Server-owned evaluator catalog bindings fail closed."""

from __future__ import annotations

import pytest

from src.application.services.evaluator_registry import (
    EvaluatorRegistryError,
    EvaluatorRegistration,
    StaticEvaluatorRegistry,
)


def _registry(*, status: str = "active") -> StaticEvaluatorRegistry:
    return StaticEvaluatorRegistry(
        catalog_version="2026.08.1",
        registrations=(
            EvaluatorRegistration(
                evaluator_id="inspect-agent-safety",
                adapter_name="inspect",
                adapter_version="0.3.0",
                result_contract_version="1.0.0",
                source_types=frozenset({"external_provider", "fairmind_worker"}),
                status=status,
            ),
        ),
    )


def test_registry_returns_immutable_authorized_registration_and_catalog_hash() -> None:
    registry = _registry()

    registration = registry.validate_binding(
        evaluator_id="inspect-agent-safety",
        source_type="external_provider",
        adapter_name="inspect",
        adapter_version="0.3.0",
        result_contract_version="1.0.0",
    )

    assert registration.evaluator_id == "inspect-agent-safety"
    assert registration.source_types == frozenset({"external_provider", "fairmind_worker"})
    assert len(registry.catalog_hash) == 64
    assert (
        registry.catalog_hash
        == StaticEvaluatorRegistry(
            catalog_version="2026.08.1",
            registrations=(registration,),
        ).catalog_hash
    )


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    (
        ("evaluator_id", "unknown-evaluator", "evaluator_unregistered"),
        ("source_type", "imported_report", "evaluator_source_not_allowed"),
        ("adapter_name", "garak", "evaluator_binding_mismatch"),
        ("adapter_version", "9.9.9", "evaluator_binding_mismatch"),
        ("result_contract_version", "2.0.0", "evaluator_binding_mismatch"),
    ),
)
def test_registry_rejects_unknown_or_mismatched_binding(
    field: str,
    value: str,
    expected_code: str,
) -> None:
    registry = _registry()
    binding = {
        "evaluator_id": "inspect-agent-safety",
        "source_type": "external_provider",
        "adapter_name": "inspect",
        "adapter_version": "0.3.0",
        "result_contract_version": "1.0.0",
    }
    binding[field] = value

    with pytest.raises(EvaluatorRegistryError) as caught:
        registry.validate_binding(**binding)

    assert caught.value.code == expected_code


def test_registry_rejects_inactive_evaluators_and_duplicate_ids() -> None:
    with pytest.raises(EvaluatorRegistryError, match="not active"):
        _registry(status="revoked").validate_binding(
            evaluator_id="inspect-agent-safety",
            source_type="external_provider",
            adapter_name="inspect",
            adapter_version="0.3.0",
            result_contract_version="1.0.0",
        )

    registration = EvaluatorRegistration(
        evaluator_id="inspect-agent-safety",
        adapter_name="inspect",
        adapter_version="0.3.0",
        result_contract_version="1.0.0",
        source_types=frozenset({"external_provider"}),
    )
    with pytest.raises(EvaluatorRegistryError, match="duplicate"):
        StaticEvaluatorRegistry(
            catalog_version="2026.08.1",
            registrations=(registration, registration),
        )
