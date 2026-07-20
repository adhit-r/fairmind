"""Framework-free application ports for the assurance workbench."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
import json
from types import MappingProxyType
from typing import Callable, Mapping, Protocol, TypeAlias

JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | tuple["JsonValue", ...] | Mapping[str, "JsonValue"]


def _freeze_json(value: object) -> JsonValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json(child) for key, child in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(child) for child in value)
    raise TypeError(f"Unsupported JSON value: {type(value).__name__}")


def _thaw_json(value: JsonValue) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(child) for child in value]
    return value


@dataclass(frozen=True, slots=True)
class FrozenJsonObject(Mapping[str, JsonValue]):
    """Deeply immutable JSON object used across the application port."""

    _value: Mapping[str, JsonValue]

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "FrozenJsonObject":
        frozen = _freeze_json(value)
        if not isinstance(frozen, Mapping):
            raise TypeError("JSON object required")
        return cls(frozen)

    @classmethod
    def from_json(cls, value: str) -> "FrozenJsonObject":
        decoded = json.loads(value)
        if not isinstance(decoded, dict):
            raise TypeError("JSON object required")
        return cls.from_mapping(decoded)

    def to_dict(self) -> dict[str, object]:
        return {key: _thaw_json(child) for key, child in self._value.items()}

    def __getitem__(self, key: str) -> JsonValue:
        return self._value[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._value)

    def __len__(self) -> int:
        return len(self._value)


class EvaluationWorkbenchError(ValueError):
    """Stable application-port failure shared with persistence adapters."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 422,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

    def detail(self) -> dict[str, object]:
        result: dict[str, object] = {"code": self.code, "message": self.message}
        if self.details is not None:
            result["details"] = self.details
        return result


@dataclass(frozen=True, slots=True)
class MutationResult:
    _body: FrozenJsonObject
    status: int
    replayed: bool = False

    @property
    def body(self) -> dict[str, object]:
        """Return an isolated transport copy without exposing mutable DTO state."""
        return self._body.to_dict()

    @classmethod
    def create(
        cls,
        *,
        body: Mapping[str, object],
        status: int,
        replayed: bool = False,
    ) -> "MutationResult":
        return cls(
            _body=FrozenJsonObject.from_mapping(body),
            status=status,
            replayed=replayed,
        )


@dataclass(frozen=True, slots=True)
class MutationCommand:
    organization_id: str
    actor_id: str
    operation: str
    idempotency_key: str
    request_hash: str


@dataclass(frozen=True, slots=True)
class MutationOutcome:
    body: FrozenJsonObject
    status: int
    resource_type: str
    resource_id: str
    audit_action: str | None
    audit_details: FrozenJsonObject


@dataclass(frozen=True, slots=True)
class SystemScopeRecord:
    organization_id: str
    workspace_id: str
    system_id: str


@dataclass(frozen=True, slots=True)
class TargetBindingRecord:
    id: str
    organization_id: str
    workspace_id: str
    system_id: str
    target_key: str
    target_kind: str
    version: str
    system_version: str
    subject_kind: str
    subject_id: str
    subject_version: str
    subject_digest: str
    deployment_id: str | None
    connector_binding_id: str | None
    manifest: FrozenJsonObject
    manifest_digest: str
    status: str
    supersedes_id: str | None
    created_by: str
    created_at: str


@dataclass(frozen=True, slots=True)
class TrustPolicyBindingRecord:
    id: str
    organization_id: str
    version: str
    policy: FrozenJsonObject
    policy_hash: str
    status: str


@dataclass(frozen=True, slots=True)
class SuiteBindingRecord:
    id: str
    owner_organization_id: str | None
    owner_scope: str
    namespace: str
    name: str
    version: str
    suite_ref: str
    manifest: FrozenJsonObject
    manifest_digest: str
    target_kinds: tuple[str, ...]
    subject_kinds: tuple[str, ...]
    lifecycle_phases: tuple[str, ...]
    execution_depths: tuple[str, ...]
    delivery_modes: tuple[str, ...]
    worker_type: str
    runner_image_digest: str | None
    adapter_name: str
    adapter_version: str
    configuration_schema: FrozenJsonObject
    configuration_defaults: FrozenJsonObject
    required_input_roles: tuple[str, ...]
    budgets: FrozenJsonObject
    result_contract_version: str
    status: str
    created_by: str
    created_at: str


@dataclass(frozen=True, slots=True)
class PlanSuiteBindingRecord:
    suite: SuiteBindingRecord
    ordinal: int
    configuration: FrozenJsonObject
    configuration_hash: str


@dataclass(frozen=True, slots=True)
class PlanBindingRecord:
    id: str
    organization_id: str
    workspace_id: str
    system_id: str
    name: str
    contract_version: str
    target_version_id: str
    target_kind: str
    lifecycle_phases: tuple[str, ...]
    execution_depth: str
    enforcement_mode: str
    delivery_mode: str
    trust_policy_version_id: str
    plan_content_hash: str
    status: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class PlanGraphRecord:
    scope: SystemScopeRecord
    plan: PlanBindingRecord
    target: TargetBindingRecord
    trust_policy: TrustPolicyBindingRecord
    suites: tuple[PlanSuiteBindingRecord, ...]


@dataclass(frozen=True, slots=True)
class PlanCreationBindings:
    scope: SystemScopeRecord
    target: TargetBindingRecord
    trust_policy: TrustPolicyBindingRecord
    suites: tuple[SuiteBindingRecord, ...]


@dataclass(frozen=True, slots=True)
class PersistTargetCommand:
    target_id: str
    actor_id: str
    requested: FrozenJsonObject
    scope: SystemScopeRecord
    created_at: str


@dataclass(frozen=True, slots=True)
class PersistSuiteCommand:
    suite_id: str
    actor_id: str
    organization_id: str
    requested: FrozenJsonObject
    created_at: str


@dataclass(frozen=True, slots=True)
class PersistPlanCommand:
    plan_id: str
    actor_id: str
    requested: FrozenJsonObject
    plan_content_hash: str
    bindings: PlanCreationBindings
    suites: tuple[PlanSuiteBindingRecord, ...]
    created_at: str


@dataclass(frozen=True, slots=True)
class PersistRunSuiteCommand:
    execution_id: str
    suite_version_id: str
    suite_owner_scope: str
    ordinal: int


@dataclass(frozen=True, slots=True)
class PersistRunCommand:
    run_id: str
    envelope_id: str
    envelope_nonce: str
    envelope: FrozenJsonObject
    envelope_hash: str
    actor_id: str
    trigger: str
    lifecycle_phase: str
    technical_status: str
    evidence_outcome: str
    overall_verdict: str
    layer_verdicts: FrozenJsonObject
    created_at: str
    graph: PlanGraphRecord
    suites: tuple[PersistRunSuiteCommand, ...]


@dataclass(frozen=True, slots=True)
class SuiteExecutionRecord:
    id: str
    suite_version_id: str
    owner_scope: str
    ordinal: int
    technical_status: str
    evidence_result_status: str
    admission_status: str
    review_status: str
    freshness_status: str
    limitations: JsonValue
    failure_code: str | None
    failure_message: str | None
    started_at: str | None
    completed_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class RunRecord:
    id: str
    organization_id: str
    workspace_id: str
    system_id: str
    plan_id: str
    contract_version: str
    trigger: str
    lifecycle_phase: str
    technical_status: str
    evidence_outcome: str
    overall_verdict: str
    layer_verdicts: FrozenJsonObject
    suite_executions: tuple[SuiteExecutionRecord, ...]
    envelope_id: str
    envelope_nonce: str
    envelope: FrozenJsonObject
    envelope_hash: str
    verdict_version: int
    requested_by: str
    started_at: str | None
    completed_at: str | None
    failure_code: str | None
    failure_message: str | None
    created_at: str
    updated_at: str


MutationCallback: TypeAlias = Callable[[datetime], MutationOutcome]


class EvaluationWorkbenchRepository(Protocol):
    def load_system_scope(
        self,
        *,
        org_id: str,
        system_id: str,
        lock: bool,
    ) -> SystemScopeRecord | None: ...

    def target_identity_exists(
        self,
        *,
        scope: SystemScopeRecord,
        target_key: str,
        version: str,
    ) -> bool: ...

    def load_target_binding(
        self,
        *,
        scope: SystemScopeRecord,
        target_version_id: str,
        lock: bool,
    ) -> TargetBindingRecord | None: ...

    def cas_supersede_target(self, target: TargetBindingRecord) -> None: ...

    def persist_target(self, command: PersistTargetCommand) -> TargetBindingRecord: ...

    def list_target_bindings(
        self,
        *,
        org_id: str,
        system_id: str,
    ) -> list[TargetBindingRecord] | None: ...

    def suite_identity_exists(
        self,
        *,
        org_id: str,
        namespace: str,
        name: str,
        version: str,
    ) -> bool: ...

    def persist_suite(self, command: PersistSuiteCommand) -> SuiteBindingRecord: ...

    def list_suite_bindings(self, *, org_id: str) -> list[SuiteBindingRecord]: ...

    def load_suite_binding(
        self,
        *,
        org_id: str,
        suite_version_id: str,
        lock: bool,
    ) -> SuiteBindingRecord | None: ...

    def cas_activate_suite(
        self,
        *,
        suite: SuiteBindingRecord,
    ) -> SuiteBindingRecord: ...

    def load_plan_creation_bindings(
        self,
        *,
        org_id: str,
        system_id: str,
        target_version_id: str,
        trust_policy_version_id: str,
        suite_version_ids: tuple[str, ...],
        lock: bool,
    ) -> PlanCreationBindings | None: ...

    def persist_plan(self, command: PersistPlanCommand) -> PlanGraphRecord: ...

    def load_plan_graph(
        self,
        *,
        org_id: str,
        system_id: str,
        plan_id: str,
        lock: bool,
    ) -> PlanGraphRecord | None: ...

    def cas_activate_plan(
        self,
        *,
        graph: PlanGraphRecord,
        actor_id: str,
        updated_at: str,
    ) -> PlanGraphRecord: ...

    def list_plan_graphs(
        self,
        *,
        org_id: str,
        system_id: str,
    ) -> list[PlanGraphRecord] | None: ...

    def get_plan_graph(
        self,
        *,
        org_id: str,
        system_id: str,
        plan_id: str,
    ) -> PlanGraphRecord | None: ...

    def persist_run(self, command: PersistRunCommand) -> RunRecord: ...

    def list_run_records(
        self,
        *,
        org_id: str,
        system_id: str,
    ) -> list[RunRecord] | None: ...

    def get_run_record(
        self,
        *,
        org_id: str,
        system_id: str,
        run_id: str,
    ) -> RunRecord | None: ...


class EvaluationWorkbenchUnitOfWork(Protocol):
    @property
    def repository(self) -> EvaluationWorkbenchRepository: ...

    def mutate(
        self,
        command: MutationCommand,
        callback: MutationCallback,
    ) -> MutationResult: ...
