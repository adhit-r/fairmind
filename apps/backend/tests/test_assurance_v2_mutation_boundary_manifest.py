"""Conformance guard for the V2 assurance mutation boundary.

This is deliberately a small static/runtime composition guard rather than a
20-scenario persistence suite.  Endpoint handlers require request-scoped
database state that belongs in their focused contract tests.  Here we freeze
the enabled mutation surface and prove every declared operation reaches a
service method composed with the shared SQLAlchemy mutation unit of work.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from api.composition.evaluation_workbench import (
    build_evaluation_workbench_service,
    build_evaluation_workbench_services,
)
from api.composition.evaluator_catalog import build_evaluator_catalog_service
from api.composition.governance_decision import build_governance_decision_service
from api.composition.imported_evidence import build_imported_evidence_service
from api.composition.trust_administration import build_trust_administration_service
from api.composition.verified_evidence_admission import (
    build_verified_evidence_admission_service,
)
from api.composition.verified_evidence_link import build_verified_evidence_link_service
from api.composition.verified_evidence_review import build_verified_evidence_review_service
from api.routes.evaluation_workbench import (
    governance_decision_router,
    governance_decision_override_router,
    plans_router,
    runs_router,
    suite_versions_router,
    target_versions_router,
    verified_evidence_review_router,
    verified_evidence_link_router,
    verified_evidence_router,
)
from api.routes.imported_evidence import imported_evidence_router
from api.routes.evaluator_catalog import (
    _transition as evaluator_catalog_transition,
    evaluator_catalog_router,
)
from api.routes.trust_administration import trust_administration_router
from src.application.services.evaluation_workbench_service import EvaluationWorkbenchService
from src.application.services.evaluation_catalog_versions_service import (
    EvaluationCatalogVersionsService,
)
from src.application.services.evaluation_plan_service import EvaluationPlanService
from src.application.services.evaluation_run_service import EvaluationRunService
from src.application.ports.evidence_admission import EvidenceAdmissionRepository
from src.application.ports.evaluation_worker import EvaluationWorkerPort
from src.application.services.evaluator_catalog_service import EvaluatorCatalogService
from src.application.services.governance_decision_service import GovernanceDecisionService
from src.application.services.imported_evidence_service import ImportedEvidenceService
from src.application.services.trust_administration_service import TrustAdministrationService
from src.application.services.verified_evidence_admission_service import (
    VerifiedEvidenceAdmissionService,
)
from src.application.services.verified_evidence_link_service import VerifiedEvidenceLinkService
from src.application.services.verified_evidence_review_service import (
    VerifiedEvidenceReviewService,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchRepository,
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
    SqlAlchemyEvaluatorCatalogUnitOfWork,
)
from src.infrastructure.db.repositories.trust_administration_repository import (
    SqlAlchemyTrustAdministrationUnitOfWork,
)


API_PREFIX = "/api/v1/ai-governance"


@dataclass(frozen=True)
class MutationRoute:
    """One enabled V2 HTTP mutation and its audited application operation."""

    path: str
    endpoint: str
    service: type[Any]
    service_method: str
    operation: str
    composition: str
    operation_helper: str | None = None
    mutation_helper: str | None = None


_CORE = f"{API_PREFIX}/organizations/{{org_id}}"
_SYSTEM = _CORE + "/systems/{system_id}/evaluation-v2"
_RUN = _CORE + "/workspaces/{workspace_id}/systems/{system_id}/evaluation-v2/runs/{run_id}"
_CATALOG = _CORE + "/evaluation-v2/evaluator-catalog/registrations"
_TRUST = _CORE + "/evaluation-v2/trust"


def test_workbench_specialized_services_share_one_request_scoped_uow() -> None:
    """The V2 catalog, plan, and run boundaries must retain one atomic UoW."""

    session = Session()
    try:
        services = build_evaluation_workbench_services(session)

        assert isinstance(services.catalog_versions, EvaluationCatalogVersionsService)
        assert isinstance(services.planning, EvaluationPlanService)
        assert isinstance(services.runs, EvaluationRunService)
        assert services.catalog_versions.unit_of_work is services.planning.unit_of_work
        assert services.planning.unit_of_work is services.runs.unit_of_work
        assert isinstance(
            services.runs.unit_of_work,
            SqlAlchemyEvaluationWorkbenchUnitOfWork,
        )

        facade = EvaluationWorkbenchService(services.runs.unit_of_work)
        assert facade.catalog_versions.unit_of_work is services.runs.unit_of_work
        assert facade.planning.unit_of_work is services.runs.unit_of_work
        assert facade.runs.unit_of_work is services.runs.unit_of_work
    finally:
        session.close()


# This list is intentionally exact.  Adding a V2 mutation must add one line
# here and prove it reaches the same idempotency/audit boundary.
MUTATION_MANIFEST = (
    MutationRoute(
        _SYSTEM + "/target-versions",
        "create_target",
        EvaluationCatalogVersionsService,
        "create_target_version",
        "evaluation-v2.target.create",
        "workbench",
        operation_helper="_command",
    ),
    MutationRoute(
        _CORE + "/evaluation-v2/suite-versions",
        "create_suite",
        EvaluationCatalogVersionsService,
        "create_suite_version",
        "evaluation-v2.suite.create",
        "workbench",
        operation_helper="_command",
    ),
    MutationRoute(
        _CORE + "/evaluation-v2/suite-versions/{suite_version_id}/activate",
        "activate_suite",
        EvaluationCatalogVersionsService,
        "activate_suite_version",
        "evaluation-v2.suite.activate",
        "workbench",
        operation_helper="_command",
    ),
    MutationRoute(
        _SYSTEM + "/plans",
        "create_plan",
        EvaluationPlanService,
        "create_plan",
        "evaluation-v2.plan.create",
        "workbench",
        operation_helper="_command",
    ),
    MutationRoute(
        _SYSTEM + "/plans/{plan_id}/activate",
        "activate_plan",
        EvaluationPlanService,
        "activate_plan",
        "evaluation-v2.plan.activate",
        "workbench",
        operation_helper="_command",
    ),
    MutationRoute(
        _SYSTEM + "/plans/{plan_id}/runs",
        "create_run",
        EvaluationRunService,
        "create_run",
        "evaluation-v2.run.create",
        "workbench",
        operation_helper="_command",
    ),
    MutationRoute(
        _CATALOG,
        "submit_evaluator_registration",
        EvaluatorCatalogService,
        "submit",
        "evaluation-v2.evaluator-catalog.submit",
        "catalog",
    ),
    MutationRoute(
        _CATALOG + "/{registration_id}/approve",
        "approve_evaluator_registration",
        EvaluatorCatalogService,
        "approve",
        "evaluation-v2.evaluator-catalog.approve",
        "catalog",
        operation_helper="_transition",
        mutation_helper="_transition",
    ),
    MutationRoute(
        _CATALOG + "/{registration_id}/reject",
        "reject_evaluator_registration",
        EvaluatorCatalogService,
        "reject",
        "evaluation-v2.evaluator-catalog.reject",
        "catalog",
        operation_helper="_transition",
        mutation_helper="_transition",
    ),
    MutationRoute(
        _CATALOG + "/{registration_id}/revoke",
        "revoke_evaluator_registration",
        EvaluatorCatalogService,
        "revoke",
        "evaluation-v2.evaluator-catalog.revoke",
        "catalog",
        operation_helper="_transition",
        mutation_helper="_transition",
    ),
    MutationRoute(
        _RUN + "/suite-executions/{suite_execution_id}/evidence",
        "submit_verified_evidence",
        VerifiedEvidenceAdmissionService,
        "submit_verified_passport_v2",
        "evaluation-v2.evidence.verified-submit",
        "workbench",
        operation_helper="_mutate_verified_passport_v2",
        mutation_helper="_mutate_verified_passport_v2",
    ),
    MutationRoute(
        _RUN
        + "/suite-executions/{suite_execution_id}/evidence-admissions/{admission_id}"
        + "/passport-revisions/{passport_revision_id}/link",
        "link_verified_evidence",
        VerifiedEvidenceLinkService,
        "link_verified_evidence",
        "evaluation-v2.evidence.verified-link",
        "link",
    ),
    MutationRoute(
        _RUN + "/suite-executions/{suite_execution_id}/evidence-imports",
        "import_unverified_evidence",
        ImportedEvidenceService,
        "import_unverified_report",
        "evaluation-v2.evidence.unverified-import",
        "import",
    ),
    MutationRoute(
        _RUN
        + "/suite-executions/{suite_execution_id}/evidence-admissions/{admission_id}"
        + "/passport-revisions/{passport_revision_id}/review",
        "review_verified_evidence",
        VerifiedEvidenceReviewService,
        "review_verified_evidence",
        "evaluation-v2.evidence.review",
        "workbench",
    ),
    MutationRoute(
        _RUN + "/decisions",
        "create_governance_decision",
        GovernanceDecisionService,
        "decide",
        "evaluation-v2.governance-decision.create",
        "workbench",
    ),
    MutationRoute(
        _RUN + "/decisions/owner-override",
        "create_owner_decision_override",
        GovernanceDecisionService,
        "decide_owner_override",
        "evaluation-v2.governance-decision.owner-override",
        "workbench",
    ),
    MutationRoute(
        _RUN + "/separation-override-grants",
        "create_separation_override_grant",
        GovernanceDecisionService,
        "create_separation_override_grant",
        "evaluation-v2.governance-decision.separation-override-grant.create",
        "workbench",
    ),
    MutationRoute(
        _RUN + "/separation-override-grants/{grant_id}/decision",
        "create_delegated_separation_override_decision",
        GovernanceDecisionService,
        "decide_delegated_override",
        "evaluation-v2.governance-decision.delegated-separation-override",
        "workbench",
    ),
    MutationRoute(
        _TRUST + "/issuers",
        "create_issuer",
        TrustAdministrationService,
        "create_issuer",
        "evaluation-v2.trust.issuer.create",
        "trust",
    ),
    MutationRoute(
        _TRUST + "/issuers/{issuer_id}/revoke",
        "revoke_issuer",
        TrustAdministrationService,
        "revoke_issuer",
        "evaluation-v2.trust.issuer.revoke",
        "trust",
    ),
    MutationRoute(
        _TRUST + "/issuers/{issuer_id}/keys",
        "create_signing_key",
        TrustAdministrationService,
        "create_signing_key",
        "evaluation-v2.trust.signing-key.create",
        "trust",
    ),
    MutationRoute(
        _TRUST + "/issuers/{issuer_id}/keys/{signing_key_id}/revoke",
        "revoke_signing_key",
        TrustAdministrationService,
        "revoke_signing_key",
        "evaluation-v2.trust.signing-key.revoke",
        "trust",
    ),
    MutationRoute(
        _TRUST + "/policies",
        "create_policy",
        TrustAdministrationService,
        "create_policy",
        "evaluation-v2.trust.policy.create",
        "trust",
    ),
    MutationRoute(
        _TRUST + "/policies/{policy_id}/activate",
        "activate_policy",
        TrustAdministrationService,
        "activate_policy",
        "evaluation-v2.trust.policy.activate",
        "trust",
    ),
    MutationRoute(
        _TRUST + "/policies/{policy_id}/retire",
        "retire_policy",
        TrustAdministrationService,
        "retire_policy",
        "evaluation-v2.trust.policy.retire",
        "trust",
    ),
)


def _mounted_mutation_routes() -> tuple[APIRoute, ...]:
    """Mount the V2 child routers exactly as ``api.main`` does when enabled."""

    app = FastAPI()
    for route_router in (
        target_versions_router,
        suite_versions_router,
        plans_router,
        runs_router,
        verified_evidence_router,
        verified_evidence_link_router,
        imported_evidence_router,
        verified_evidence_review_router,
        governance_decision_router,
        governance_decision_override_router,
        evaluator_catalog_router,
        trust_administration_router,
    ):
        app.include_router(route_router, prefix=API_PREFIX)
    return tuple(
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path.startswith(f"{API_PREFIX}/organizations/{{org_id}}")
        and route.methods == {"POST"}
    )


def _function_node(function: Callable[..., Any]) -> ast.FunctionDef | ast.AsyncFunctionDef:
    parsed = ast.parse(textwrap.dedent(inspect.getsource(function)))
    node = parsed.body[0]
    assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    return node


def _string_constants(function: Callable[..., Any], node: ast.AST) -> dict[str, str]:
    module = inspect.getmodule(function)
    constants = {
        name: value
        for name, value in vars(module).items()
        if isinstance(value, str)
    }
    for assignment in ast.walk(node):
        if (
            isinstance(assignment, ast.Assign)
            and len(assignment.targets) == 1
            and isinstance(assignment.targets[0], ast.Name)
            and isinstance(assignment.value, ast.Constant)
            and isinstance(assignment.value.value, str)
        ):
            constants[assignment.targets[0].id] = assignment.value.value
    return constants


def _call_operation(
    node: ast.AST,
    *,
    callee: str,
    function: Callable[..., Any],
) -> set[str]:
    constants = _string_constants(function, node)
    operations: set[str] = set()
    for call in ast.walk(node):
        if not isinstance(call, ast.Call):
            continue
        name = (
            call.func.id
            if isinstance(call.func, ast.Name)
            else call.func.attr
            if isinstance(call.func, ast.Attribute)
            else None
        )
        if name != callee:
            continue
        for keyword in call.keywords:
            if keyword.arg != "operation":
                continue
            if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                operations.add(keyword.value.value)
            elif isinstance(keyword.value, ast.Name) and keyword.value.id in constants:
                operations.add(constants[keyword.value.id])
    return operations


def _calls_attribute(node: ast.AST, attribute: str) -> bool:
    return any(
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == attribute
        for call in ast.walk(node)
    )


def _calls_service_method(node: ast.AST, *, receiver: str, method: str) -> bool:
    """Require the handler to call the declared service, not an equal-named helper."""

    for call in ast.walk(node):
        if (
            not isinstance(call, ast.Call)
            or not isinstance(call.func, ast.Attribute)
            or call.func.attr != method
        ):
            continue
        owner = call.func.value
        if isinstance(owner, ast.Name) and owner.id == receiver:
            return True
        if (
            isinstance(owner, ast.Call)
            and isinstance(owner.func, ast.Name)
            and owner.func.id == receiver
        ):
            return True
    return False


def _route_service_reference(item: MutationRoute) -> str:
    if item.service is EvaluationCatalogVersionsService:
        return "_catalog_versions_service"
    if item.service is EvaluationPlanService:
        return "_planning_service"
    if item.service is EvaluationRunService:
        return "_run_service"
    if item.service is EvaluatorCatalogService:
        return "catalog_service"
    if item.service is VerifiedEvidenceAdmissionService:
        return "admission_service"
    if item.service is VerifiedEvidenceLinkService:
        return "link_service"
    if item.service is VerifiedEvidenceReviewService:
        return "review_service"
    if item.service is GovernanceDecisionService:
        return "decision_service"
    if item.service is ImportedEvidenceService:
        return "import_service"
    if item.service is TrustAdministrationService:
        return "service"
    raise AssertionError(f"Unhandled assurance service: {item.service!r}")


def _mutation_command_uses_operation_parameter(node: ast.AST) -> bool:
    for call in ast.walk(node):
        if not isinstance(call, ast.Call):
            continue
        if not isinstance(call.func, ast.Name) or call.func.id != "MutationCommand":
            continue
        for keyword in call.keywords:
            if (
                keyword.arg == "operation"
                and isinstance(keyword.value, ast.Name)
                and keyword.value.id == "operation"
            ):
                return True
    return False


def _route_by_endpoint() -> dict[str, APIRoute]:
    return {route.endpoint.__name__: route for route in _mounted_mutation_routes()}


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            if node.module == "src.application.services":
                modules.update(f"{node.module}.{alias.name}" for alias in node.names)
            else:
                modules.add(node.module)
    return modules


def test_infrastructure_depends_on_ports_and_contracts_not_application_services() -> None:
    """Persistence may use ports and neutral contracts, never application services."""

    infrastructure = Path(__file__).parents[1] / "src" / "infrastructure"
    imported = {
        module
        for path in infrastructure.rglob("*.py")
        for module in _imported_modules(path)
    }
    forbidden = sorted(
        module for module in imported if module.startswith("src.application.services.")
    )
    assert not forbidden, forbidden
    assert "src.application.evaluation_workbench_contracts" in imported


def test_contracts_module_has_no_workbench_compatibility_facade() -> None:
    """Moving helpers cannot leave a second copy of V2 business orchestration."""

    contracts = (
        Path(__file__).parents[1]
        / "src"
        / "application"
        / "evaluation_workbench_contracts.py"
    )
    tree = ast.parse(contracts.read_text(encoding="utf-8"), filename=str(contracts))
    assert not any(
        isinstance(node, ast.ClassDef) and node.name == "EvaluationWorkbenchService"
        for node in tree.body
    )


def test_worker_port_is_reserved_without_a_mounted_v2_execution_route() -> None:
    """The P0 worker port cannot become a P1 executor through this split."""

    assert EvaluationWorkerPort.__name__ == "EvaluationWorkerPort"
    assert {"capabilities", "execute"} <= set(EvaluationWorkerPort.__dict__)
    assert not any(
        "/evaluation-v2/workers" in route.path
        or "/evaluation-v2/worker" in route.path
        for route in _mounted_mutation_routes()
    )


def test_verified_evidence_has_no_legacy_atomic_admit_and_link_capability() -> None:
    """Submission and linking must remain separately authorized capabilities."""

    assert "admit_verified_passport_v2" not in VerifiedEvidenceAdmissionService.__dict__
    assert "persist_verified_passport_v2" not in EvidenceAdmissionRepository.__dict__
    assert "persist_verified_passport_v2" not in SqlAlchemyEvaluationWorkbenchRepository.__dict__


def test_assurance_v2_mutation_manifest_is_the_exact_enabled_post_surface() -> None:
    """A new enabled V2 mutation cannot silently escape the central manifest."""

    actual = {
        ("POST", route.path, route.endpoint.__name__)
        for route in _mounted_mutation_routes()
    }
    expected = {
        ("POST", item.path, item.endpoint) for item in MUTATION_MANIFEST
    }

    assert len(MUTATION_MANIFEST) == 25
    assert len({item.operation for item in MUTATION_MANIFEST}) == 25
    assert actual == expected


def test_each_manifest_route_dispatches_to_its_declared_service_method() -> None:
    """A route must keep its application service boundary instead of writing directly."""

    routes = _route_by_endpoint()
    catalog_transition = _function_node(evaluator_catalog_transition)

    for item in MUTATION_MANIFEST:
        endpoint = routes[item.endpoint].endpoint
        endpoint_node = _function_node(endpoint)
        if item.service is EvaluatorCatalogService and item.service_method != "submit":
            # The endpoint has a literal transition name and the helper owns the
            # actual service dispatch.  Check both links without invoking a
            # stateful route fixture for every transition.
            transition_names = {
                keyword.value.value
                for call in ast.walk(endpoint_node)
                if isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == "_transition"
                for keyword in call.keywords
                if keyword.arg == "transition"
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
            }
            assert transition_names == {item.service_method}
            assert _calls_service_method(
                catalog_transition,
                receiver="catalog_service",
                method=item.service_method,
            )
        else:
            assert _calls_service_method(
                endpoint_node,
                receiver=_route_service_reference(item),
                method=item.service_method,
            )


def test_every_manifest_operation_reaches_a_shared_sqlalchemy_mutation_uow() -> None:
    """All declared operations construct their command then delegate to ``mutate``."""

    for item in MUTATION_MANIFEST:
        service_method = getattr(item.service, item.service_method)
        method_node = _function_node(service_method)
        operation_node = method_node
        operation_function = service_method
        mutation_node = method_node

        if item.service is GovernanceDecisionService:
            operation_function = item.service._decide
            operation_node = _function_node(operation_function)
            mutation_node = operation_node
            assert item.operation in _string_constants(
                operation_function, operation_node
            ).values()
        elif item.operation_helper is not None:
            assert item.operation in _call_operation(
                method_node,
                callee=item.operation_helper,
                function=service_method,
            )
            helper = getattr(item.service, item.operation_helper)
            operation_node = _function_node(helper)
            operation_function = helper
            if item.mutation_helper is not None:
                mutation_node = operation_node

        if item.service is GovernanceDecisionService:
            pass
        elif item.operation_helper is None:
            assert item.operation in _call_operation(
                operation_node,
                callee="MutationCommand",
                function=operation_function,
            )
        else:
            assert _mutation_command_uses_operation_parameter(operation_node)

        assert _calls_attribute(mutation_node, "mutate")

    session = Session()
    try:
        compositions = {
            "workbench": (
                build_evaluation_workbench_service(session),
                "unit_of_work",
                SqlAlchemyEvaluationWorkbenchUnitOfWork,
            ),
            "catalog": (
                build_evaluator_catalog_service(session),
                "_unit_of_work",
                SqlAlchemyEvaluatorCatalogUnitOfWork,
            ),
            "trust": (
                build_trust_administration_service(session),
                "_unit_of_work",
                SqlAlchemyTrustAdministrationUnitOfWork,
            ),
            "admission": (
                build_verified_evidence_admission_service(session),
                "_unit_of_work",
                SqlAlchemyEvaluationWorkbenchUnitOfWork,
            ),
            "link": (
                build_verified_evidence_link_service(session),
                "_unit_of_work",
                SqlAlchemyEvaluationWorkbenchUnitOfWork,
            ),
            "review": (
                build_verified_evidence_review_service(session),
                "unit_of_work",
                SqlAlchemyEvaluationWorkbenchUnitOfWork,
            ),
            "decision": (
                build_governance_decision_service(session),
                "unit_of_work",
                SqlAlchemyEvaluationWorkbenchUnitOfWork,
            ),
            "import": (
                build_imported_evidence_service(session),
                "_unit_of_work",
                SqlAlchemyEvaluationWorkbenchUnitOfWork,
            ),
        }
        assert {item.composition for item in MUTATION_MANIFEST} == {
            "workbench",
            "catalog",
            "trust",
            "import",
            "link",
        }
        for service, attribute, expected_type in compositions.values():
            unit_of_work = getattr(service, attribute)
            assert type(unit_of_work) is expected_type
            assert isinstance(unit_of_work, SqlAlchemyEvaluationWorkbenchUnitOfWork)
    finally:
        session.close()

    # Catalog inherits the common boundary unchanged.  Trust adds a PostgreSQL
    # release gate but must still delegate to the common implementation.
    assert (
        SqlAlchemyEvaluatorCatalogUnitOfWork.mutate
        is SqlAlchemyEvaluationWorkbenchUnitOfWork.mutate
    )
    trust_mutate = _function_node(SqlAlchemyTrustAdministrationUnitOfWork.mutate)
    assert any(
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "mutate"
        and isinstance(call.func.value, ast.Call)
        and isinstance(call.func.value.func, ast.Name)
        and call.func.value.func.id == "super"
        for call in ast.walk(trust_mutate)
    )
