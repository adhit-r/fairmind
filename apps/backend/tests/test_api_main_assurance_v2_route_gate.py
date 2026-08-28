"""Application-level route-gating contract for assurance v2."""

from __future__ import annotations

import importlib

import pytest

import api.main as main_module
from config.settings import settings

V2_TARGET_PATHS = {
    "/api/v1/ai-governance/organizations/{org_id}/systems/{system_id}"
    "/evaluation-v2/target-versions",
    "/api/v1/ai-governance/organizations/{org_id}/systems/{system_id}"
    "/evaluation-v2/target-versions/{target_version_id}",
}
V2_SUITE_PATHS = {
    "/api/v1/ai-governance/organizations/{org_id}/evaluation-v2/suite-versions",
    "/api/v1/ai-governance/organizations/{org_id}/evaluation-v2/suite-versions"
    "/{suite_version_id}",
    "/api/v1/ai-governance/organizations/{org_id}/evaluation-v2/suite-versions"
    "/{suite_version_id}/activate",
}
V2_PLAN_PATH = (
    "/api/v1/ai-governance/organizations/{org_id}/systems/{system_id}" "/evaluation-v2/plans"
)
V2_PLAN_PATHS = {
    V2_PLAN_PATH,
    V2_PLAN_PATH + "/{plan_id}",
    V2_PLAN_PATH + "/{plan_id}/activate",
    V2_PLAN_PATH + "/{plan_id}/preflight",
}
V2_RUN_PATHS = {
    V2_PLAN_PATH + "/{plan_id}/runs",
    "/api/v1/ai-governance/organizations/{org_id}/systems/{system_id}"
    "/evaluation-v2/runs",
    "/api/v1/ai-governance/organizations/{org_id}/systems/{system_id}"
    "/evaluation-v2/runs/{run_id}",
}
VERIFIED_EVIDENCE_PATH = (
    "/api/v1/ai-governance/organizations/{org_id}/workspaces/{workspace_id}"
    "/systems/{system_id}/evaluation-v2/runs/{run_id}"
    "/suite-executions/{suite_execution_id}/evidence"
)
VERIFIED_EVIDENCE_REVIEW_PATH = (
    "/api/v1/ai-governance/organizations/{org_id}/workspaces/{workspace_id}"
    "/systems/{system_id}/evaluation-v2/runs/{run_id}"
    "/suite-executions/{suite_execution_id}/evidence-admissions/{admission_id}"
    "/passport-revisions/{passport_revision_id}/review"
)
GOVERNANCE_DECISION_PATH = (
    "/api/v1/ai-governance/organizations/{org_id}/workspaces/{workspace_id}"
    "/systems/{system_id}/evaluation-v2/runs/{run_id}/decisions"
)
OWNER_DECISION_OVERRIDE_PATH = GOVERNANCE_DECISION_PATH + "/owner-override"
IMPORTED_EVIDENCE_PATH = (
    "/api/v1/ai-governance/organizations/{org_id}/workspaces/{workspace_id}"
    "/systems/{system_id}/evaluation-v2/runs/{run_id}"
    "/suite-executions/{suite_execution_id}/evidence-imports"
)
EVALUATOR_CATALOG_PATH = (
    "/api/v1/ai-governance/organizations/{org_id}" "/evaluation-v2/evaluator-catalog/registrations"
)
LEGACY_PLAN_PATH = (
    "/api/v1/ai-governance/organizations/{org_id}/systems/{system_id}" "/evaluation-plans"
)
LEGACY_RUN_PATH = (
    "/api/v1/ai-governance/organizations/{org_id}/systems/{system_id}" "/evaluation-runs"
)

CORE_CAPABILITY_SETTINGS = (
    "assurance_v2_target_versions_enabled",
    "assurance_v2_suite_versions_enabled",
    "assurance_v2_plans_enabled",
    "assurance_v2_runs_enabled",
)
CORE_CAPABILITY_PATHS = {
    "assurance_v2_target_versions_enabled": V2_TARGET_PATHS,
    "assurance_v2_suite_versions_enabled": V2_SUITE_PATHS,
    "assurance_v2_plans_enabled": V2_PLAN_PATHS,
    "assurance_v2_runs_enabled": V2_RUN_PATHS,
}
ALL_CORE_CAPABILITY_PATHS = set().union(*CORE_CAPABILITY_PATHS.values())


def _route_paths() -> set[str]:
    return {route.path for route in main_module.app.routes}


def _assurance_v2_paths(paths: set[str]) -> set[str]:
    return {path for path in paths if "/evaluation-v2/" in path}


def test_core_assurance_capabilities_are_independently_default_off() -> None:
    assert {
        setting_name: getattr(settings, setting_name, None)
        for setting_name in CORE_CAPABILITY_SETTINGS
    } == {setting_name: False for setting_name in CORE_CAPABILITY_SETTINGS}


@pytest.mark.parametrize("enabled_setting", CORE_CAPABILITY_SETTINGS)
def test_core_assurance_capability_routes_mount_independently(
    enabled_setting: str,
) -> None:
    original_master = settings.assurance_v2_enabled
    original_children = {
        setting_name: getattr(settings, setting_name)
        for setting_name in CORE_CAPABILITY_SETTINGS
    }
    try:
        settings.assurance_v2_enabled = True
        for setting_name in CORE_CAPABILITY_SETTINGS:
            setattr(settings, setting_name, setting_name == enabled_setting)

        importlib.reload(main_module)

        assert _route_paths() & ALL_CORE_CAPABILITY_PATHS == CORE_CAPABILITY_PATHS[
            enabled_setting
        ]
    finally:
        settings.assurance_v2_enabled = original_master
        for setting_name, original_value in original_children.items():
            setattr(settings, setting_name, original_value)
        importlib.reload(main_module)


def test_assurance_v2_routes_are_mounted_only_when_enabled() -> None:
    original = settings.assurance_v2_enabled
    original_core_children = {
        setting_name: getattr(settings, setting_name)
        for setting_name in CORE_CAPABILITY_SETTINGS
    }
    original_evidence_submit = settings.assurance_v2_evidence_submit_enabled
    original_evidence_review = settings.assurance_v2_evidence_review_enabled
    original_evidence_import = getattr(settings, "assurance_v2_evidence_import_enabled", False)
    original_governance_decision = settings.assurance_v2_governance_decision_enabled
    original_owner_override = getattr(settings, "assurance_v2_separation_override_enabled", False)
    original_evaluator_catalog = getattr(settings, "assurance_v2_evaluator_catalog_enabled", False)
    try:
        settings.assurance_v2_enabled = False
        for setting_name in CORE_CAPABILITY_SETTINGS:
            setattr(settings, setting_name, True)
        settings.assurance_v2_evidence_submit_enabled = False
        settings.assurance_v2_evidence_review_enabled = False
        settings.assurance_v2_evidence_import_enabled = False
        settings.assurance_v2_governance_decision_enabled = True
        settings.assurance_v2_separation_override_enabled = True
        settings.assurance_v2_evaluator_catalog_enabled = False
        importlib.reload(main_module)
        disabled_paths = _route_paths()

        assert _assurance_v2_paths(disabled_paths) == set()
        assert VERIFIED_EVIDENCE_PATH not in disabled_paths
        assert VERIFIED_EVIDENCE_REVIEW_PATH not in disabled_paths
        assert GOVERNANCE_DECISION_PATH not in disabled_paths
        assert OWNER_DECISION_OVERRIDE_PATH not in disabled_paths
        assert IMPORTED_EVIDENCE_PATH not in disabled_paths
        assert EVALUATOR_CATALOG_PATH not in disabled_paths
        assert LEGACY_PLAN_PATH in disabled_paths
        assert LEGACY_RUN_PATH in disabled_paths

        settings.assurance_v2_enabled = True
        settings.assurance_v2_evidence_submit_enabled = False
        settings.assurance_v2_evidence_review_enabled = False
        settings.assurance_v2_evidence_import_enabled = False
        settings.assurance_v2_governance_decision_enabled = False
        settings.assurance_v2_separation_override_enabled = True
        importlib.reload(main_module)
        enabled_paths_without_evidence_submit = _route_paths()

        assert V2_PLAN_PATH in _assurance_v2_paths(enabled_paths_without_evidence_submit)
        assert VERIFIED_EVIDENCE_PATH not in enabled_paths_without_evidence_submit
        assert VERIFIED_EVIDENCE_REVIEW_PATH not in enabled_paths_without_evidence_submit
        assert GOVERNANCE_DECISION_PATH not in enabled_paths_without_evidence_submit
        assert OWNER_DECISION_OVERRIDE_PATH not in enabled_paths_without_evidence_submit
        assert IMPORTED_EVIDENCE_PATH not in enabled_paths_without_evidence_submit
        assert EVALUATOR_CATALOG_PATH not in enabled_paths_without_evidence_submit
        assert LEGACY_PLAN_PATH in enabled_paths_without_evidence_submit
        assert LEGACY_RUN_PATH in enabled_paths_without_evidence_submit

        settings.assurance_v2_evidence_submit_enabled = True
        importlib.reload(main_module)
        enabled_paths = _route_paths()
        assert VERIFIED_EVIDENCE_PATH in enabled_paths
        assert VERIFIED_EVIDENCE_REVIEW_PATH not in enabled_paths
        assert GOVERNANCE_DECISION_PATH not in enabled_paths
        assert OWNER_DECISION_OVERRIDE_PATH not in enabled_paths
        assert EVALUATOR_CATALOG_PATH not in enabled_paths

        settings.assurance_v2_evidence_submit_enabled = False
        settings.assurance_v2_evidence_import_enabled = True
        importlib.reload(main_module)
        enabled_paths_with_import = _route_paths()
        assert IMPORTED_EVIDENCE_PATH in enabled_paths_with_import
        assert VERIFIED_EVIDENCE_PATH not in enabled_paths_with_import
        assert VERIFIED_EVIDENCE_REVIEW_PATH not in enabled_paths_with_import
        assert GOVERNANCE_DECISION_PATH not in enabled_paths_with_import
        assert OWNER_DECISION_OVERRIDE_PATH not in enabled_paths_with_import

        settings.assurance_v2_evidence_submit_enabled = False
        settings.assurance_v2_evidence_import_enabled = False
        settings.assurance_v2_evidence_review_enabled = True
        importlib.reload(main_module)
        enabled_paths_without_evidence_submit = _route_paths()
        assert VERIFIED_EVIDENCE_PATH not in enabled_paths_without_evidence_submit
        assert VERIFIED_EVIDENCE_REVIEW_PATH in enabled_paths_without_evidence_submit
        assert GOVERNANCE_DECISION_PATH not in enabled_paths_without_evidence_submit
        assert OWNER_DECISION_OVERRIDE_PATH not in enabled_paths_without_evidence_submit

        settings.assurance_v2_evidence_review_enabled = False
        settings.assurance_v2_evaluator_catalog_enabled = True
        importlib.reload(main_module)
        enabled_paths_with_catalog = _route_paths()
        assert EVALUATOR_CATALOG_PATH in enabled_paths_with_catalog
        assert GOVERNANCE_DECISION_PATH not in enabled_paths_with_catalog
        assert OWNER_DECISION_OVERRIDE_PATH not in enabled_paths_with_catalog

        settings.assurance_v2_evaluator_catalog_enabled = False
        settings.assurance_v2_governance_decision_enabled = True
        settings.assurance_v2_separation_override_enabled = False
        importlib.reload(main_module)
        enabled_paths_without_override = _route_paths()
        assert GOVERNANCE_DECISION_PATH in enabled_paths_without_override
        assert OWNER_DECISION_OVERRIDE_PATH not in enabled_paths_without_override

        settings.assurance_v2_separation_override_enabled = True
        importlib.reload(main_module)
        enabled_paths_with_decisions = _route_paths()
        assert GOVERNANCE_DECISION_PATH in enabled_paths_with_decisions
        assert OWNER_DECISION_OVERRIDE_PATH in enabled_paths_with_decisions
        assert VERIFIED_EVIDENCE_PATH not in enabled_paths_with_decisions
        assert VERIFIED_EVIDENCE_REVIEW_PATH not in enabled_paths_with_decisions
        assert EVALUATOR_CATALOG_PATH not in enabled_paths_with_decisions
    finally:
        settings.assurance_v2_enabled = original
        for setting_name, original_value in original_core_children.items():
            setattr(settings, setting_name, original_value)
        settings.assurance_v2_evidence_submit_enabled = original_evidence_submit
        settings.assurance_v2_evidence_review_enabled = original_evidence_review
        settings.assurance_v2_evidence_import_enabled = original_evidence_import
        settings.assurance_v2_governance_decision_enabled = original_governance_decision
        settings.assurance_v2_separation_override_enabled = original_owner_override
        settings.assurance_v2_evaluator_catalog_enabled = original_evaluator_catalog
        importlib.reload(main_module)
