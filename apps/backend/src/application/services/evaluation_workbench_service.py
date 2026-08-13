"""Compatibility facade for the split Assurance V2 application services."""

from __future__ import annotations

from typing import Mapping

from src.application.ports.evaluation_workbench import MutationResult
from src.application import evaluation_workbench_contracts as _contracts
from src.application.services.evaluation_catalog_versions_service import (
    EvaluationCatalogVersionsService,
)
from src.application.services.evaluation_plan_service import EvaluationPlanService
from src.application.services.evaluation_run_service import EvaluationRunService

EvaluationWorkbenchError = _contracts.EvaluationWorkbenchError
EvaluationWorkbenchInputError = _contracts.EvaluationWorkbenchInputError
assurance_request_hash = _contracts.assurance_request_hash
canonical_assurance_json = _contracts.canonical_assurance_json
verify_stored_suite_link_projection = _contracts.verify_stored_suite_link_projection
verify_run_record_binding = _contracts.verify_run_record_binding


class EvaluationWorkbenchService:
    """Compatibility delegation only; business rules live in focused services."""

    def __init__(self, unit_of_work: object) -> None:
        self.unit_of_work = unit_of_work
        self.repository = unit_of_work.repository
        self.catalog_versions = EvaluationCatalogVersionsService(unit_of_work)
        self.planning = EvaluationPlanService(unit_of_work)
        self.runs = EvaluationRunService(unit_of_work)

    def create_target_version(self, **kwargs: object) -> MutationResult:
        return self.catalog_versions.create_target_version(**kwargs)

    def list_target_versions(self, **kwargs: object) -> list[Mapping[str, object]] | None:
        return self.catalog_versions.list_target_versions(**kwargs)

    def get_target_version(self, **kwargs: object) -> Mapping[str, object] | None:
        return self.catalog_versions.get_target_version(**kwargs)

    def create_suite_version(self, **kwargs: object) -> MutationResult:
        return self.catalog_versions.create_suite_version(**kwargs)

    def list_suite_versions(self, **kwargs: object) -> list[Mapping[str, object]]:
        return self.catalog_versions.list_suite_versions(**kwargs)

    def get_suite_version(self, **kwargs: object) -> Mapping[str, object] | None:
        return self.catalog_versions.get_suite_version(**kwargs)

    def activate_suite_version(self, **kwargs: object) -> MutationResult | None:
        return self.catalog_versions.activate_suite_version(**kwargs)

    def create_plan(self, **kwargs: object) -> MutationResult:
        return self.planning.create_plan(**kwargs)

    def list_plans(self, **kwargs: object) -> list[dict[str, object]] | None:
        return self.planning.list_plans(**kwargs)

    def get_plan(self, **kwargs: object) -> dict[str, object] | None:
        return self.planning.get_plan(**kwargs)

    def activate_plan(self, **kwargs: object) -> MutationResult | None:
        return self.planning.activate_plan(**kwargs)

    def preflight(self, **kwargs: object) -> dict[str, object] | None:
        return self.planning.preflight(**kwargs)

    def create_run(self, **kwargs: object) -> MutationResult:
        return self.runs.create_run(**kwargs)

    def list_runs(self, **kwargs: object) -> list[dict[str, object]] | None:
        return self.runs.list_runs(**kwargs)

    def get_run(self, **kwargs: object) -> dict[str, object] | None:
        return self.runs.get_run(**kwargs)


__all__ = [
    "EvaluationWorkbenchError",
    "EvaluationWorkbenchInputError",
    "EvaluationWorkbenchService",
    "assurance_request_hash",
    "canonical_assurance_json",
    "verify_run_record_binding",
    "verify_stored_suite_link_projection",
]
