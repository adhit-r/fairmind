"""Application-level route-gating contract for assurance v2."""

from __future__ import annotations

import importlib

import api.main as main_module
from config.settings import settings


V2_PLAN_PATH = (
    "/api/v1/ai-governance/organizations/{org_id}/systems/{system_id}"
    "/evaluation-v2/plans"
)
VERIFIED_EVIDENCE_PATH = (
    "/api/v1/ai-governance/organizations/{org_id}/workspaces/{workspace_id}"
    "/systems/{system_id}/evaluation-v2/runs/{run_id}"
    "/suite-executions/{suite_execution_id}/evidence"
)
LEGACY_PLAN_PATH = (
    "/api/v1/ai-governance/organizations/{org_id}/systems/{system_id}"
    "/evaluation-plans"
)
LEGACY_RUN_PATH = (
    "/api/v1/ai-governance/organizations/{org_id}/systems/{system_id}"
    "/evaluation-runs"
)


def _route_paths() -> set[str]:
    return {route.path for route in main_module.app.routes}


def _assurance_v2_paths(paths: set[str]) -> set[str]:
    return {path for path in paths if "/evaluation-v2/" in path}


def test_assurance_v2_routes_are_mounted_only_when_enabled() -> None:
    original = settings.assurance_v2_enabled
    original_evidence_submit = settings.assurance_v2_evidence_submit_enabled
    try:
        settings.assurance_v2_enabled = False
        settings.assurance_v2_evidence_submit_enabled = False
        importlib.reload(main_module)
        disabled_paths = _route_paths()

        assert _assurance_v2_paths(disabled_paths) == set()
        assert VERIFIED_EVIDENCE_PATH not in disabled_paths
        assert LEGACY_PLAN_PATH in disabled_paths
        assert LEGACY_RUN_PATH in disabled_paths

        settings.assurance_v2_enabled = True
        settings.assurance_v2_evidence_submit_enabled = False
        importlib.reload(main_module)
        enabled_paths_without_evidence_submit = _route_paths()

        assert V2_PLAN_PATH in _assurance_v2_paths(enabled_paths_without_evidence_submit)
        assert VERIFIED_EVIDENCE_PATH not in enabled_paths_without_evidence_submit
        assert LEGACY_PLAN_PATH in enabled_paths_without_evidence_submit
        assert LEGACY_RUN_PATH in enabled_paths_without_evidence_submit

        settings.assurance_v2_evidence_submit_enabled = True
        importlib.reload(main_module)
        enabled_paths = _route_paths()
        assert VERIFIED_EVIDENCE_PATH in enabled_paths
    finally:
        settings.assurance_v2_enabled = original
        settings.assurance_v2_evidence_submit_enabled = original_evidence_submit
        importlib.reload(main_module)
