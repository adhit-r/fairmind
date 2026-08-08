"""Framework-free authority and persistence contracts for governance decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Mapping, Protocol

from src.application.ports.evaluation_workbench import (
    FrozenJsonObject,
    MutationCallback,
    MutationCommand,
    MutationResult,
)

UuidFactory = Callable[[], object]


@dataclass(frozen=True, slots=True)
class GovernanceDecisionScope:
    organization_id: str
    workspace_id: str
    system_id: str
    run_id: str


@dataclass(frozen=True, slots=True)
class GovernanceDecisionAuthorityRecord:
    scope: GovernanceDecisionScope
    run_contract_version: str
    envelope_id: str
    envelope_hash: str
    technical_status: str
    current_verdict_version: int
    current_overall_verdict: str
    current_layer_verdicts: FrozenJsonObject
    requested_by: str
    evidence_submitters: tuple[str, ...]
    suite_execution_ids: tuple[str, ...]
    evidence_set: FrozenJsonObject
    evidence_set_hash: str

    @classmethod
    def create(
        cls,
        *,
        scope: GovernanceDecisionScope,
        run_contract_version: str,
        envelope_id: str,
        envelope_hash: str,
        technical_status: str,
        current_verdict_version: int,
        current_overall_verdict: str,
        current_layer_verdicts: Mapping[str, object],
        requested_by: str,
        evidence_submitters: tuple[str, ...],
        suite_execution_ids: tuple[str, ...],
        evidence_set: Mapping[str, object],
        evidence_set_hash: str,
    ) -> "GovernanceDecisionAuthorityRecord":
        return cls(
            scope=scope,
            run_contract_version=run_contract_version,
            envelope_id=envelope_id,
            envelope_hash=envelope_hash,
            technical_status=technical_status,
            current_verdict_version=current_verdict_version,
            current_overall_verdict=current_overall_verdict,
            current_layer_verdicts=FrozenJsonObject.from_mapping(current_layer_verdicts),
            requested_by=requested_by,
            evidence_submitters=tuple(evidence_submitters),
            suite_execution_ids=tuple(suite_execution_ids),
            evidence_set=FrozenJsonObject.from_mapping(evidence_set),
            evidence_set_hash=evidence_set_hash,
        )


@dataclass(frozen=True, slots=True)
class PersistGovernanceDecisionCommand:
    scope: GovernanceDecisionScope
    authority: GovernanceDecisionAuthorityRecord
    decision_id: str
    actor_id: str
    expected_verdict_version: int
    next_verdict_version: int
    overall_verdict: str
    layer_verdicts: FrozenJsonObject
    rationale: str
    owner_override_reason: None
    decided_at: datetime


@dataclass(frozen=True, slots=True)
class GovernanceDecisionRecord:
    decision_id: str
    scope: GovernanceDecisionScope
    run_contract_version: str
    envelope_id: str
    envelope_hash: str
    verdict_version: int
    overall_verdict: str
    layer_verdicts: FrozenJsonObject
    rationale: str
    decided_by: str
    evidence_set_hash: str
    decided_at: datetime

    @classmethod
    def create(
        cls,
        *,
        decision_id: str,
        scope: GovernanceDecisionScope,
        run_contract_version: str,
        envelope_id: str,
        envelope_hash: str,
        verdict_version: int,
        overall_verdict: str,
        layer_verdicts: Mapping[str, object],
        rationale: str,
        decided_by: str,
        evidence_set_hash: str,
        decided_at: datetime,
    ) -> "GovernanceDecisionRecord":
        return cls(
            decision_id=decision_id,
            scope=scope,
            run_contract_version=run_contract_version,
            envelope_id=envelope_id,
            envelope_hash=envelope_hash,
            verdict_version=verdict_version,
            overall_verdict=overall_verdict,
            layer_verdicts=FrozenJsonObject.from_mapping(layer_verdicts),
            rationale=rationale,
            decided_by=decided_by,
            evidence_set_hash=evidence_set_hash,
            decided_at=decided_at,
        )


class GovernanceDecisionRepository(Protocol):
    def read_fresh_utc_now(self) -> datetime: ...

    def load_governance_decision_authority_for_update(
        self,
        *,
        scope: GovernanceDecisionScope,
    ) -> GovernanceDecisionAuthorityRecord | None: ...

    def persist_governance_decision(
        self,
        command: PersistGovernanceDecisionCommand,
    ) -> GovernanceDecisionRecord: ...


class GovernanceDecisionUnitOfWork(Protocol):
    @property
    def repository(self) -> GovernanceDecisionRepository: ...

    def mutate(
        self,
        command: MutationCommand,
        callback: MutationCallback,
    ) -> MutationResult: ...


__all__ = [
    "GovernanceDecisionAuthorityRecord",
    "GovernanceDecisionRecord",
    "GovernanceDecisionRepository",
    "GovernanceDecisionScope",
    "GovernanceDecisionUnitOfWork",
    "PersistGovernanceDecisionCommand",
    "UuidFactory",
]
