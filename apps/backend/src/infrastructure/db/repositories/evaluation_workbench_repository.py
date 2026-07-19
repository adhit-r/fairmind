"""SQLAlchemy adapter for the immutable assurance-contract v2 workbench."""

from __future__ import annotations

from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
import hashlib
import json
import threading
from typing import Any, Callable, Mapping
import uuid

from sqlalchemy import insert, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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
from src.application.ports.evaluation_workbench import (
    FrozenJsonObject,
    EvaluationWorkbenchError,
    MutationCommand,
    MutationOutcome,
    MutationResult,
    PersistPlanCommand,
    PersistRunCommand,
    PersistSuiteCommand,
    PersistTargetCommand,
    PlanBindingRecord,
    PlanCreationBindings,
    PlanGraphRecord,
    PlanSuiteBindingRecord,
    RunRecord,
    SuiteBindingRecord,
    SuiteExecutionRecord,
    SystemScopeRecord,
    TargetBindingRecord,
    TrustPolicyBindingRecord,
)
from src.domain.assurance.evaluation_v2 import (
    CONTRACT_VERSION,
    canonical_json,
    canonical_sha256,
)

_SQLITE_WRITE_LOCK = threading.RLock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None = None) -> str:
    return (value or _now()).isoformat()


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _json_load(value: str | None, fallback: Any) -> Any:
    if value is None:
        return fallback
    return json.loads(value)


class SqlAlchemyEvaluationWorkbenchRepository:
    """Implements scoped loads, CAS transitions, and atomic graph inserts."""

    def __init__(self, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("SQLAlchemy Session required")
        self.db = session

    # ------------------------------------------------------------------
    # Shared transaction, idempotency, audit, and integrity primitives.
    # ------------------------------------------------------------------

    def _error(
        self,
        code: str,
        message: str,
        status_code: int,
        *,
        details: dict[str, Any] | None = None,
    ) -> EvaluationWorkbenchError:
        return EvaluationWorkbenchError(code, message, status_code=status_code, details=details)

    def _system_scope(
        self, org_id: str, system_id: str, *, lock: bool = False
    ) -> Mapping[str, Any] | None:
        systems = GovernanceAISystem.__table__
        workspaces = GovernanceWorkspace.__table__
        statement = (
            select(
                systems.c.id.label("system_id"),
                systems.c.workspace_id,
                systems.c.org_id,
            )
            .select_from(
                systems.join(
                    workspaces,
                    (workspaces.c.id == systems.c.workspace_id)
                    & (workspaces.c.org_id == systems.c.org_id),
                )
            )
            .where(
                systems.c.id == system_id,
                systems.c.org_id == org_id,
                workspaces.c.org_id == org_id,
            )
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.execute(statement).mappings().one_or_none()

    # --------------------------------------------------------------
    # Target catalog.
    # --------------------------------------------------------------

    def load_system_scope(
        self,
        *,
        org_id: str,
        system_id: str,
        lock: bool,
    ) -> SystemScopeRecord | None:
        row = self._system_scope(org_id, system_id, lock=lock)
        return self._scope_record(row) if row is not None else None

    def target_identity_exists(
        self,
        *,
        scope: SystemScopeRecord,
        target_key: str,
        version: str,
    ) -> bool:
        targets = GovernanceEvaluationTargetVersion.__table__
        return (
            self.db.execute(
                select(targets.c.id).where(
                    targets.c.org_id == scope.organization_id,
                    targets.c.workspace_id == scope.workspace_id,
                    targets.c.system_id == scope.system_id,
                    targets.c.target_key == target_key,
                    targets.c.version == version,
                )
            ).scalar_one_or_none()
            is not None
        )

    def load_target_binding(
        self,
        *,
        scope: SystemScopeRecord,
        target_version_id: str,
        lock: bool,
    ) -> TargetBindingRecord | None:
        row = self._target_row(
            org_id=scope.organization_id,
            workspace_id=scope.workspace_id,
            system_id=scope.system_id,
            target_id=target_version_id,
            lock=lock,
        )
        return self._target_binding(row) if row is not None else None

    def cas_supersede_target(self, target: TargetBindingRecord) -> None:
        targets = GovernanceEvaluationTargetVersion.__table__
        result = self.db.execute(
            update(targets)
            .where(
                targets.c.id == target.id,
                targets.c.org_id == target.organization_id,
                targets.c.workspace_id == target.workspace_id,
                targets.c.system_id == target.system_id,
                targets.c.status == "active",
            )
            .values(status="superseded")
        )
        if result.rowcount != 1:
            raise self._error(
                "supersedes_state_conflict",
                "The prior target is no longer active and cannot be superseded.",
                409,
            )

    def persist_target(self, command: PersistTargetCommand) -> TargetBindingRecord:
        target = command.requested.to_dict()
        scope = command.scope
        targets = GovernanceEvaluationTargetVersion.__table__
        self.db.execute(
            insert(targets).values(
                id=command.target_id,
                org_id=scope.organization_id,
                workspace_id=scope.workspace_id,
                system_id=scope.system_id,
                target_key=target["targetKey"],
                target_kind=target["targetKind"],
                version=target["version"],
                system_version=target["systemVersion"],
                subject_kind=target["subjectKind"],
                subject_id=target["subjectId"],
                subject_version=target["subjectVersion"],
                subject_digest=target["subjectDigest"],
                deployment_id=target.get("deploymentId"),
                connector_binding_id=target.get("connectorBindingId"),
                manifest_json=target["manifestJson"],
                manifest_digest=target["manifestDigest"],
                status="active",
                supersedes_id=target.get("supersedesId"),
                created_by=command.actor_id,
                created_at=command.created_at,
            )
        )
        row = (
            self.db.execute(
                select(targets).where(
                    targets.c.id == command.target_id,
                    targets.c.org_id == scope.organization_id,
                    targets.c.workspace_id == scope.workspace_id,
                    targets.c.system_id == scope.system_id,
                )
            )
            .mappings()
            .one()
        )
        return self._target_binding(row)

    def list_target_bindings(
        self,
        *,
        org_id: str,
        system_id: str,
    ) -> list[TargetBindingRecord] | None:
        scope = self._system_scope(org_id, system_id)
        if scope is None:
            return None
        targets = GovernanceEvaluationTargetVersion.__table__
        rows = (
            self.db.execute(
                select(targets)
                .where(
                    targets.c.org_id == org_id,
                    targets.c.workspace_id == scope["workspace_id"],
                    targets.c.system_id == system_id,
                )
                .order_by(targets.c.created_at.desc(), targets.c.id.desc())
            )
            .mappings()
            .all()
        )
        return [self._target_binding(row) for row in rows]

    # --------------------------------------------------------------
    # Suite catalog.
    # --------------------------------------------------------------

    def suite_identity_exists(
        self,
        *,
        org_id: str,
        namespace: str,
        name: str,
        version: str,
    ) -> bool:
        suites = GovernanceEvaluationSuiteVersion.__table__
        return (
            self.db.execute(
                select(suites.c.id).where(
                    suites.c.owner_scope == org_id,
                    suites.c.namespace == namespace,
                    suites.c.name == name,
                    suites.c.version == version,
                )
            ).scalar_one_or_none()
            is not None
        )

    def persist_suite(self, command: PersistSuiteCommand) -> SuiteBindingRecord:
        suite = command.requested.to_dict()
        suites = GovernanceEvaluationSuiteVersion.__table__
        self.db.execute(
            insert(suites).values(
                id=command.suite_id,
                owner_org_id=command.organization_id,
                owner_scope=command.organization_id,
                namespace=suite["namespace"],
                name=suite["name"],
                version=suite["version"],
                suite_ref=suite["suiteRef"],
                manifest_json=suite["manifestJson"],
                manifest_digest=suite["manifestDigest"],
                target_kinds_json=canonical_json(suite["supportedTargetKinds"]),
                subject_kinds_json=canonical_json(suite["supportedSubjectKinds"]),
                lifecycle_phases_json=canonical_json(suite["lifecyclePhases"]),
                execution_depths_json=canonical_json(suite["executionDepths"]),
                delivery_modes_json=canonical_json(suite["deliveryModes"]),
                worker_type=suite["workerType"],
                runner_image_digest=suite.get("runnerImageDigest"),
                adapter_name=suite["adapterName"],
                adapter_version=suite["adapterVersion"],
                configuration_schema_json=canonical_json(suite["configurationSchema"]),
                configuration_defaults_json=canonical_json(suite["configurationDefaults"]),
                required_input_roles_json=canonical_json(suite["requiredInputRoles"]),
                default_budgets_json=canonical_json(suite["budgets"]),
                result_contract_version=suite["resultContractVersion"],
                status="draft",
                created_by=command.actor_id,
                created_at=command.created_at,
            )
        )
        row = (
            self.db.execute(
                select(suites).where(
                    suites.c.id == command.suite_id,
                    suites.c.owner_scope == command.organization_id,
                )
            )
            .mappings()
            .one()
        )
        return self._suite_binding(row)

    def list_suite_bindings(self, *, org_id: str) -> list[SuiteBindingRecord]:
        suites = GovernanceEvaluationSuiteVersion.__table__
        rows = (
            self.db.execute(
                select(suites)
                .where(suites.c.owner_scope.in_(["platform", org_id]))
                .order_by(suites.c.namespace, suites.c.name, suites.c.version)
            )
            .mappings()
            .all()
        )
        return [self._suite_binding(row) for row in rows]

    def _suite_row(self, *, org_id: str, suite_version_id: str, lock: bool = False):
        suites = GovernanceEvaluationSuiteVersion.__table__
        statement = select(suites).where(
            suites.c.id == suite_version_id,
            suites.c.owner_scope.in_(["platform", org_id]),
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.execute(statement).mappings().one_or_none()

    def load_suite_binding(
        self,
        *,
        org_id: str,
        suite_version_id: str,
        lock: bool,
    ) -> SuiteBindingRecord | None:
        row = self._suite_row(
            org_id=org_id,
            suite_version_id=suite_version_id,
            lock=lock,
        )
        return self._suite_binding(row) if row is not None else None

    def cas_activate_suite(
        self,
        *,
        suite: SuiteBindingRecord,
    ) -> SuiteBindingRecord:
        if suite.status == "draft":
            result = self.db.execute(
                update(GovernanceEvaluationSuiteVersion.__table__)
                .where(
                    GovernanceEvaluationSuiteVersion.id == suite.id,
                    GovernanceEvaluationSuiteVersion.owner_scope == suite.owner_scope,
                    GovernanceEvaluationSuiteVersion.status == "draft",
                )
                .values(status="active")
            )
            if result.rowcount != 1:
                raise self._error(
                    "suite_state_changed",
                    "Suite state changed concurrently.",
                    409,
                )
        updated = self._suite_row(
            org_id=suite.owner_scope,
            suite_version_id=suite.id,
            lock=True,
        )
        if updated is None:
            raise RuntimeError("activated suite could not be reloaded")
        return self._suite_binding(updated)

    # --------------------------------------------------------------
    # Bound plans and preflight.
    # --------------------------------------------------------------

    def _target_row(
        self, *, org_id: str, workspace_id: str, system_id: str, target_id: str, lock=False
    ):
        targets = GovernanceEvaluationTargetVersion.__table__
        statement = select(targets).where(
            targets.c.id == target_id,
            targets.c.org_id == org_id,
            targets.c.workspace_id == workspace_id,
            targets.c.system_id == system_id,
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.execute(statement).mappings().one_or_none()

    def _trust_row(self, *, org_id: str, trust_id: str, lock=False):
        policies = GovernanceEvidenceTrustPolicyVersion.__table__
        statement = select(policies).where(policies.c.id == trust_id, policies.c.org_id == org_id)
        if lock:
            statement = statement.with_for_update()
        return self.db.execute(statement).mappings().one_or_none()

    def _plan_row(
        self, *, org_id: str, workspace_id: str, system_id: str, plan_id: str, lock=False
    ):
        plans = GovernanceEvaluationPlan.__table__
        statement = select(plans).where(
            plans.c.id == plan_id,
            plans.c.org_id == org_id,
            plans.c.workspace_id == workspace_id,
            plans.c.system_id == system_id,
            plans.c.contract_version == CONTRACT_VERSION,
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.execute(statement).mappings().one_or_none()

    def _bound_suites(
        self,
        plan_id: str,
        org_id: str,
        workspace_id: str,
        system_id: str,
        *,
        lock=False,
    ):
        selections = GovernanceEvaluationPlanSuite.__table__
        suites = GovernanceEvaluationSuiteVersion.__table__
        statement = (
            select(
                selections.c.ordinal,
                selections.c.configuration_json,
                selections.c.configuration_hash,
                *[column for column in suites.c],
            )
            .select_from(
                selections.join(
                    suites,
                    (suites.c.id == selections.c.suite_version_id)
                    & (suites.c.owner_scope == selections.c.suite_owner_scope),
                )
            )
            .where(
                selections.c.plan_id == plan_id,
                selections.c.org_id == org_id,
                selections.c.workspace_id == workspace_id,
                selections.c.system_id == system_id,
                selections.c.suite_owner_scope.in_(["platform", org_id]),
            )
            .order_by(selections.c.ordinal)
        )
        if lock:
            statement = statement.with_for_update()
        rows = self.db.execute(statement).mappings().all()
        result = []
        for row in rows:
            value = dict(row)
            value["configuration"] = _json_load(value["configuration_json"], {})
            value["configuration_schema"] = _json_load(value["configuration_schema_json"], {})
            value["target_kinds"] = _json_load(value["target_kinds_json"], [])
            value["subject_kinds"] = _json_load(value["subject_kinds_json"], [])
            value["lifecycle_phases"] = _json_load(value["lifecycle_phases_json"], [])
            value["execution_depths"] = _json_load(value["execution_depths_json"], [])
            value["delivery_modes"] = _json_load(value["delivery_modes_json"], [])
            value["required_input_roles"] = _json_load(value["required_input_roles_json"], [])
            value["budgets"] = _json_load(value["default_budgets_json"], {})
            result.append(value)
        return result

    @staticmethod
    def _scope_record(row: Mapping[str, Any]) -> SystemScopeRecord:
        return SystemScopeRecord(
            organization_id=row["org_id"],
            workspace_id=row["workspace_id"],
            system_id=row["system_id"],
        )

    @staticmethod
    def _target_binding(row: Mapping[str, Any]) -> TargetBindingRecord:
        return TargetBindingRecord(
            id=row["id"],
            organization_id=row["org_id"],
            workspace_id=row["workspace_id"],
            system_id=row["system_id"],
            target_key=row["target_key"],
            target_kind=row["target_kind"],
            version=row["version"],
            system_version=row["system_version"],
            subject_kind=row["subject_kind"],
            subject_id=row["subject_id"],
            subject_version=row["subject_version"],
            subject_digest=row["subject_digest"],
            deployment_id=row["deployment_id"],
            connector_binding_id=row["connector_binding_id"],
            manifest=FrozenJsonObject.from_json(row["manifest_json"]),
            manifest_digest=row["manifest_digest"],
            status=row["status"],
            supersedes_id=row["supersedes_id"],
            created_by=row["created_by"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _trust_binding(row: Mapping[str, Any]) -> TrustPolicyBindingRecord:
        return TrustPolicyBindingRecord(
            id=row["id"],
            organization_id=row["org_id"],
            version=row["version"],
            policy=FrozenJsonObject.from_json(row["policy_json"]),
            policy_hash=row["policy_hash"],
            status=row["status"],
        )

    @staticmethod
    def _suite_binding(row: Mapping[str, Any]) -> SuiteBindingRecord:
        return SuiteBindingRecord(
            id=row["id"],
            owner_organization_id=row["owner_org_id"],
            owner_scope=row["owner_scope"],
            namespace=row["namespace"],
            name=row["name"],
            version=row["version"],
            suite_ref=row["suite_ref"],
            manifest=FrozenJsonObject.from_json(row["manifest_json"]),
            manifest_digest=row["manifest_digest"],
            target_kinds=tuple(_json_load(row["target_kinds_json"], [])),
            subject_kinds=tuple(_json_load(row["subject_kinds_json"], [])),
            lifecycle_phases=tuple(_json_load(row["lifecycle_phases_json"], [])),
            execution_depths=tuple(_json_load(row["execution_depths_json"], [])),
            delivery_modes=tuple(_json_load(row["delivery_modes_json"], [])),
            worker_type=row["worker_type"],
            runner_image_digest=row["runner_image_digest"],
            adapter_name=row["adapter_name"],
            adapter_version=row["adapter_version"],
            configuration_schema=FrozenJsonObject.from_json(row["configuration_schema_json"]),
            configuration_defaults=FrozenJsonObject.from_json(row["configuration_defaults_json"]),
            required_input_roles=tuple(_json_load(row["required_input_roles_json"], [])),
            budgets=FrozenJsonObject.from_json(row["default_budgets_json"]),
            result_contract_version=row["result_contract_version"],
            status=row["status"],
            created_by=row["created_by"],
            created_at=row["created_at"],
        )

    @classmethod
    def _plan_suite_binding(cls, row: Mapping[str, Any]) -> PlanSuiteBindingRecord:
        return PlanSuiteBindingRecord(
            suite=cls._suite_binding(row),
            ordinal=int(row["ordinal"]),
            configuration=FrozenJsonObject.from_json(row["configuration_json"]),
            configuration_hash=row["configuration_hash"],
        )

    @staticmethod
    def _plan_binding(row: Mapping[str, Any]) -> PlanBindingRecord:
        return PlanBindingRecord(
            id=row["id"],
            organization_id=row["org_id"],
            workspace_id=row["workspace_id"],
            system_id=row["system_id"],
            name=row["name"],
            contract_version=row["contract_version"],
            target_version_id=row["target_version_id"],
            target_kind=row["target_kind"],
            lifecycle_phases=tuple(_json_load(row["lifecycle_phases_json"], [])),
            execution_depth=row["execution_depth"],
            enforcement_mode=row["enforcement_mode"],
            delivery_mode=row["delivery_mode"],
            trust_policy_version_id=row["trust_policy_version_id"],
            plan_content_hash=row["plan_content_hash"],
            status=row["status"],
            created_by=row["created_by"],
            updated_by=row["updated_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def load_plan_creation_bindings(
        self,
        *,
        org_id: str,
        system_id: str,
        target_version_id: str,
        trust_policy_version_id: str,
        suite_version_ids: tuple[str, ...],
        lock: bool,
    ) -> PlanCreationBindings | None:
        scope = self._system_scope(org_id, system_id, lock=lock)
        if scope is None:
            return None
        target = self._target_row(
            org_id=org_id,
            workspace_id=scope["workspace_id"],
            system_id=system_id,
            target_id=target_version_id,
            lock=lock,
        )
        trust = self._trust_row(
            org_id=org_id,
            trust_id=trust_policy_version_id,
            lock=lock,
        )
        if target is None or trust is None:
            return None
        suites: list[SuiteBindingRecord] = []
        for suite_version_id in suite_version_ids:
            suite = self._suite_row(
                org_id=org_id,
                suite_version_id=suite_version_id,
                lock=lock,
            )
            if suite is None:
                return None
            suites.append(self._suite_binding(suite))
        return PlanCreationBindings(
            scope=self._scope_record(scope),
            target=self._target_binding(target),
            trust_policy=self._trust_binding(trust),
            suites=tuple(suites),
        )

    def load_plan_graph(
        self,
        *,
        org_id: str,
        system_id: str,
        plan_id: str,
        lock: bool,
    ) -> PlanGraphRecord | None:
        scope = self._system_scope(org_id, system_id, lock=lock)
        if scope is None:
            return None
        plan = self._plan_row(
            org_id=org_id,
            workspace_id=scope["workspace_id"],
            system_id=system_id,
            plan_id=plan_id,
            lock=lock,
        )
        if plan is None:
            return None
        target = self._target_row(
            org_id=org_id,
            workspace_id=scope["workspace_id"],
            system_id=system_id,
            target_id=plan["target_version_id"],
            lock=lock,
        )
        trust = self._trust_row(
            org_id=org_id,
            trust_id=plan["trust_policy_version_id"],
            lock=lock,
        )
        if target is None or trust is None:
            return None
        suites = self._bound_suites(
            plan_id,
            org_id,
            scope["workspace_id"],
            system_id,
            lock=lock,
        )
        return PlanGraphRecord(
            scope=self._scope_record(scope),
            plan=self._plan_binding(plan),
            target=self._target_binding(target),
            trust_policy=self._trust_binding(trust),
            suites=tuple(self._plan_suite_binding(suite) for suite in suites),
        )

    def persist_plan(self, command: PersistPlanCommand) -> PlanGraphRecord:
        requested = command.requested.to_dict()
        scope = command.bindings.scope
        target = command.bindings.target
        trust = command.bindings.trust_policy
        self.db.execute(
            insert(GovernanceEvaluationPlan.__table__).values(
                id=command.plan_id,
                org_id=scope.organization_id,
                workspace_id=scope.workspace_id,
                system_id=scope.system_id,
                name=requested["name"],
                target_kind=target.target_kind,
                lifecycle_phases_json=canonical_json(requested["lifecyclePhases"]),
                execution_depth=requested["executionDepth"],
                enforcement_mode=requested["enforcementMode"],
                delivery_mode=requested["deliveryMode"],
                suite_refs_json=canonical_json(
                    [selection.suite.suite_ref for selection in command.suites]
                ),
                status="draft",
                created_by=command.actor_id,
                updated_by=command.actor_id,
                created_at=command.created_at,
                updated_at=command.created_at,
                contract_version=CONTRACT_VERSION,
                target_version_id=target.id,
                plan_content_hash=command.plan_content_hash,
                trust_policy_version_id=trust.id,
            )
        )
        for selection in command.suites:
            self.db.execute(
                insert(GovernanceEvaluationPlanSuite.__table__).values(
                    id=str(uuid.uuid4()),
                    org_id=scope.organization_id,
                    workspace_id=scope.workspace_id,
                    system_id=scope.system_id,
                    plan_id=command.plan_id,
                    suite_version_id=selection.suite.id,
                    suite_owner_scope=selection.suite.owner_scope,
                    ordinal=selection.ordinal,
                    configuration_json=canonical_json(selection.configuration.to_dict()),
                    configuration_hash=selection.configuration_hash,
                    created_at=command.created_at,
                )
            )
        graph = self.load_plan_graph(
            org_id=scope.organization_id,
            system_id=scope.system_id,
            plan_id=command.plan_id,
            lock=True,
        )
        if graph is None:
            raise RuntimeError("persisted plan graph could not be reloaded")
        return graph

    def cas_activate_plan(
        self,
        *,
        graph: PlanGraphRecord,
        actor_id: str,
        updated_at: str,
    ) -> PlanGraphRecord:
        if graph.plan.status == "draft":
            result = self.db.execute(
                update(GovernanceEvaluationPlan.__table__)
                .where(
                    GovernanceEvaluationPlan.id == graph.plan.id,
                    GovernanceEvaluationPlan.org_id == graph.scope.organization_id,
                    GovernanceEvaluationPlan.workspace_id == graph.scope.workspace_id,
                    GovernanceEvaluationPlan.system_id == graph.scope.system_id,
                    GovernanceEvaluationPlan.contract_version == CONTRACT_VERSION,
                    GovernanceEvaluationPlan.status == "draft",
                )
                .values(status="active", updated_by=actor_id, updated_at=updated_at)
            )
            if result.rowcount != 1:
                raise self._error(
                    "plan_state_changed",
                    "Plan state changed concurrently.",
                    409,
                )
        updated = self.load_plan_graph(
            org_id=graph.scope.organization_id,
            system_id=graph.scope.system_id,
            plan_id=graph.plan.id,
            lock=True,
        )
        if updated is None:
            raise RuntimeError("activated plan graph could not be reloaded")
        return updated

    def list_plan_graphs(
        self,
        *,
        org_id: str,
        system_id: str,
    ) -> list[PlanGraphRecord] | None:
        scope = self._system_scope(org_id, system_id)
        if scope is None:
            return None
        plans = GovernanceEvaluationPlan.__table__
        plan_ids = (
            self.db.execute(
                select(plans.c.id)
                .where(
                    plans.c.org_id == org_id,
                    plans.c.workspace_id == scope["workspace_id"],
                    plans.c.system_id == system_id,
                    plans.c.contract_version == CONTRACT_VERSION,
                )
                .order_by(plans.c.created_at.desc())
            )
            .scalars()
            .all()
        )
        result: list[PlanGraphRecord] = []
        for plan_id in plan_ids:
            graph = self.load_plan_graph(
                org_id=org_id,
                system_id=system_id,
                plan_id=plan_id,
                lock=False,
            )
            if graph is not None:
                result.append(graph)
        return result

    def get_plan_graph(
        self,
        *,
        org_id: str,
        system_id: str,
        plan_id: str,
    ) -> PlanGraphRecord | None:
        return self.load_plan_graph(
            org_id=org_id,
            system_id=system_id,
            plan_id=plan_id,
            lock=False,
        )

    # --------------------------------------------------------------
    # Runs and immutable envelopes.
    # --------------------------------------------------------------

    @staticmethod
    def _suite_execution_record(row: Mapping[str, Any]) -> SuiteExecutionRecord:
        frozen_limitations = FrozenJsonObject.from_mapping(
            {"items": _json_load(row["limitations_json"], [])}
        )["items"]
        return SuiteExecutionRecord(
            id=row["id"],
            suite_version_id=row["suite_version_id"],
            owner_scope=row["suite_owner_scope"],
            ordinal=int(row["ordinal"]),
            technical_status=row["technical_status"],
            evidence_result_status=row["evidence_result_status"],
            admission_status=row["admission_status"],
            review_status=row["review_status"],
            freshness_status=row["freshness_status"],
            limitations=frozen_limitations,
            failure_code=row["failure_code"],
            failure_message=row["failure_message"],
        )

    def _run_record(self, row: Mapping[str, Any]) -> RunRecord:
        executions = (
            self.db.execute(
                select(GovernanceEvaluationRunSuiteExecution.__table__)
                .where(
                    GovernanceEvaluationRunSuiteExecution.run_id == row["id"],
                    GovernanceEvaluationRunSuiteExecution.org_id == row["org_id"],
                    GovernanceEvaluationRunSuiteExecution.workspace_id == row["workspace_id"],
                    GovernanceEvaluationRunSuiteExecution.system_id == row["system_id"],
                )
                .order_by(GovernanceEvaluationRunSuiteExecution.ordinal)
            )
            .mappings()
            .all()
        )
        return RunRecord(
            id=row["id"],
            organization_id=row["org_id"],
            workspace_id=row["workspace_id"],
            system_id=row["system_id"],
            plan_id=row["plan_id"],
            contract_version=row["contract_version"],
            trigger=row["trigger"],
            lifecycle_phase=row["lifecycle_phase"],
            technical_status=row["technical_status"],
            evidence_outcome=row["evidence_outcome"],
            overall_verdict=row["overall_verdict"],
            layer_verdicts=FrozenJsonObject.from_json(row["layer_verdicts_json"]),
            suite_executions=tuple(
                self._suite_execution_record(execution) for execution in executions
            ),
            envelope_id=row["envelope_id"],
            envelope=FrozenJsonObject.from_json(row["envelope_json"]),
            envelope_hash=row["envelope_hash"],
            verdict_version=int(row["verdict_version"]),
            requested_by=row["requested_by"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            failure_code=row["failure_code"],
            failure_message=row["failure_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def persist_run(self, command: PersistRunCommand) -> RunRecord:
        scope = command.graph.scope
        self.db.execute(
            insert(GovernanceEvaluationRun.__table__).values(
                id=command.run_id,
                org_id=scope.organization_id,
                workspace_id=scope.workspace_id,
                system_id=scope.system_id,
                plan_id=command.graph.plan.id,
                contract_version=CONTRACT_VERSION,
                trigger=command.trigger,
                technical_status=command.technical_status,
                overall_verdict=command.overall_verdict,
                layer_verdicts_json=canonical_json(command.layer_verdicts.to_dict()),
                requested_by=command.actor_id,
                created_at=command.created_at,
                updated_at=command.created_at,
                lifecycle_phase=command.lifecycle_phase,
                envelope_id=command.envelope_id,
                envelope_json=canonical_json(command.envelope.to_dict()),
                envelope_hash=command.envelope_hash,
                evidence_outcome=command.evidence_outcome,
                verdict_version=0,
            )
        )
        for execution in command.suites:
            self.db.execute(
                insert(GovernanceEvaluationRunSuiteExecution.__table__).values(
                    id=execution.execution_id,
                    org_id=scope.organization_id,
                    workspace_id=scope.workspace_id,
                    system_id=scope.system_id,
                    run_id=command.run_id,
                    suite_version_id=execution.suite_version_id,
                    suite_owner_scope=execution.suite_owner_scope,
                    ordinal=execution.ordinal,
                    technical_status=command.technical_status,
                    evidence_result_status=command.evidence_outcome,
                    admission_status="pending",
                    review_status="pending",
                    freshness_status="current",
                    created_at=command.created_at,
                    updated_at=command.created_at,
                )
            )
        row = (
            self.db.execute(
                select(GovernanceEvaluationRun.__table__).where(
                    GovernanceEvaluationRun.id == command.run_id,
                    GovernanceEvaluationRun.org_id == scope.organization_id,
                    GovernanceEvaluationRun.workspace_id == scope.workspace_id,
                    GovernanceEvaluationRun.system_id == scope.system_id,
                    GovernanceEvaluationRun.contract_version == CONTRACT_VERSION,
                )
            )
            .mappings()
            .one()
        )
        return self._run_record(row)

    def list_run_records(
        self,
        *,
        org_id: str,
        system_id: str,
    ) -> list[RunRecord] | None:
        scope = self._system_scope(org_id, system_id)
        if scope is None:
            return None
        rows = (
            self.db.execute(
                select(GovernanceEvaluationRun.__table__)
                .where(
                    GovernanceEvaluationRun.org_id == org_id,
                    GovernanceEvaluationRun.workspace_id == scope["workspace_id"],
                    GovernanceEvaluationRun.system_id == system_id,
                    GovernanceEvaluationRun.contract_version == CONTRACT_VERSION,
                )
                .order_by(GovernanceEvaluationRun.created_at.desc())
            )
            .mappings()
            .all()
        )
        return [self._run_record(row) for row in rows]

    def get_run_record(
        self,
        *,
        org_id: str,
        system_id: str,
        run_id: str,
    ) -> RunRecord | None:
        scope = self._system_scope(org_id, system_id)
        if scope is None:
            return None
        row = (
            self.db.execute(
                select(GovernanceEvaluationRun.__table__).where(
                    GovernanceEvaluationRun.id == run_id,
                    GovernanceEvaluationRun.org_id == org_id,
                    GovernanceEvaluationRun.workspace_id == scope["workspace_id"],
                    GovernanceEvaluationRun.system_id == system_id,
                    GovernanceEvaluationRun.contract_version == CONTRACT_VERSION,
                )
            )
            .mappings()
            .one_or_none()
        )
        return self._run_record(row) if row else None


class SqlAlchemyEvaluationWorkbenchUnitOfWork:
    """SQLAlchemy transaction adapter for one application-orchestrated mutation."""

    def __init__(
        self,
        session: Session,
        *,
        repository: SqlAlchemyEvaluationWorkbenchRepository | None = None,
    ) -> None:
        if not isinstance(session, Session):
            raise TypeError("SQLAlchemy Session required")
        self.db = session
        self._repository = repository or SqlAlchemyEvaluationWorkbenchRepository(session)

    @property
    def repository(self) -> SqlAlchemyEvaluationWorkbenchRepository:
        return self._repository

    @staticmethod
    def _error(
        code: str,
        message: str,
        status_code: int,
    ) -> EvaluationWorkbenchError:
        return EvaluationWorkbenchError(code, message, status_code=status_code)

    def _lock_org(self, org_id: str) -> None:
        if self.db.bind is not None and self.db.bind.dialect.name == "postgresql":
            self.db.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:org_id, 0))"),
                {"org_id": org_id},
            )

    def _mutation_lock(self):
        if self.db.bind is not None and self.db.bind.dialect.name == "sqlite":
            return _SQLITE_WRITE_LOCK
        return nullcontext()

    def _claim_idempotency(
        self,
        *,
        command: MutationCommand,
        now: datetime,
    ) -> tuple[str, MutationResult | None]:
        records = GovernanceIdempotencyRecord.__table__
        key_hash = hashlib.sha256(command.idempotency_key.encode("ascii")).hexdigest()

        def existing_row(lock: bool = False):
            statement = select(records).where(
                records.c.org_id == command.organization_id,
                records.c.actor_id == command.actor_id,
                records.c.operation == command.operation,
                records.c.key_hash == key_hash,
            )
            if lock:
                statement = statement.with_for_update()
            return self.db.execute(statement).mappings().one_or_none()

        row = existing_row(lock=True)
        if row is None:
            record_id = str(uuid.uuid4())
            try:
                if self.db.bind is not None and self.db.bind.dialect.name == "sqlite":
                    self.db.execute(
                        update(records)
                        .where(records.c.id == "__fairmind_never__")
                        .values(updated_at=records.c.updated_at)
                    )
                with self.db.begin_nested():
                    self.db.execute(
                        insert(records).values(
                            id=record_id,
                            org_id=command.organization_id,
                            actor_id=command.actor_id,
                            operation=command.operation,
                            key_hash=key_hash,
                            request_hash=command.request_hash,
                            status="in_progress",
                            created_at=_iso(now),
                            updated_at=_iso(now),
                            expires_at=_iso(now + timedelta(days=30)),
                        )
                    )
                    self.db.flush()
                return record_id, None
            except IntegrityError:
                row = existing_row(lock=True)
                if row is None:
                    raise

        assert row is not None
        if _parse_timestamp(row["expires_at"]) <= now:
            result = self.db.execute(
                update(records)
                .where(
                    records.c.id == row["id"],
                    records.c.updated_at == row["updated_at"],
                )
                .values(
                    request_hash=command.request_hash,
                    status="in_progress",
                    response_status=None,
                    response_body_json=None,
                    resource_type=None,
                    resource_id=None,
                    created_at=_iso(now),
                    updated_at=_iso(now),
                    expires_at=_iso(now + timedelta(days=30)),
                )
            )
            if result.rowcount != 1:
                raise self._error(
                    "idempotency_in_progress",
                    "Another request is reclaiming this expired idempotency key.",
                    409,
                )
            return row["id"], None
        if row["request_hash"] != command.request_hash:
            raise self._error(
                "idempotency_conflict",
                "This Idempotency-Key is already bound to a different request.",
                409,
            )
        if row["status"] == "completed":
            return row["id"], MutationResult.create(
                body=_json_load(row["response_body_json"], {}),
                status=int(row["response_status"]),
                replayed=True,
            )
        raise self._error(
            "idempotency_in_progress",
            "A request with this Idempotency-Key is still in progress.",
            409,
        )

    def _complete_idempotency(
        self,
        *,
        record_id: str,
        outcome: MutationOutcome,
        now: datetime,
    ) -> None:
        result = self.db.execute(
            update(GovernanceIdempotencyRecord.__table__)
            .where(
                GovernanceIdempotencyRecord.id == record_id,
                GovernanceIdempotencyRecord.status == "in_progress",
            )
            .values(
                status="completed",
                response_status=outcome.status,
                response_body_json=canonical_json(outcome.body.to_dict()),
                resource_type=outcome.resource_type,
                resource_id=outcome.resource_id,
                updated_at=_iso(now),
            )
        )
        if result.rowcount != 1:
            raise self._error(
                "idempotency_state_changed",
                "The idempotency record changed before completion.",
                409,
            )

    def _append_audit(
        self,
        *,
        command: MutationCommand,
        outcome: MutationOutcome,
        now: datetime,
    ) -> None:
        assert outcome.audit_action is not None
        events = GovernanceEvaluationAuditEvent.__table__
        previous = (
            self.db.execute(
                select(events.c.sequence_number, events.c.event_hash)
                .where(events.c.org_id == command.organization_id)
                .order_by(events.c.sequence_number.desc())
                .limit(1)
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        sequence = int(previous["sequence_number"]) + 1 if previous else 1
        previous_hash = previous["event_hash"] if previous else None
        event_id = str(uuid.uuid4())
        projection = {
            "eventId": event_id,
            "organizationId": command.organization_id,
            "sequenceNumber": sequence,
            "actorId": command.actor_id,
            "action": outcome.audit_action,
            "outcome": "success",
            "resourceType": outcome.resource_type,
            "resourceId": outcome.resource_id,
            "details": outcome.audit_details.to_dict(),
            "previousHash": previous_hash,
            "createdAt": _iso(now),
        }
        self.db.execute(
            insert(events).values(
                id=event_id,
                org_id=command.organization_id,
                sequence_number=sequence,
                actor_id=command.actor_id,
                action=outcome.audit_action,
                outcome="success",
                resource_type=outcome.resource_type,
                resource_id=outcome.resource_id,
                details_json=canonical_json(outcome.audit_details.to_dict()),
                previous_hash=previous_hash,
                event_hash=canonical_sha256(projection),
                created_at=_iso(now),
            )
        )

    def mutate(
        self,
        command: MutationCommand,
        callback: Callable[[datetime], MutationOutcome],
    ) -> MutationResult:
        with self._mutation_lock():
            try:
                self._lock_org(command.organization_id)
                now = _now()
                record_id, replay = self._claim_idempotency(
                    command=command,
                    now=now,
                )
                if replay is not None:
                    self.db.rollback()
                    return replay
                outcome = callback(now)
                if outcome.audit_action is not None:
                    self._append_audit(command=command, outcome=outcome, now=now)
                self._complete_idempotency(
                    record_id=record_id,
                    outcome=outcome,
                    now=now,
                )
                self.db.commit()
                return MutationResult.create(
                    body=outcome.body.to_dict(),
                    status=outcome.status,
                )
            except EvaluationWorkbenchError:
                self.db.rollback()
                raise
            except Exception as error:
                self.db.rollback()
                raise self._error(
                    "evaluation_persistence_failed",
                    "The assurance workflow could not be persisted atomically.",
                    500,
                ) from error
