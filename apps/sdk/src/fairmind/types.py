"""Response shapes, as the API returns them (camelCase keys where the API uses them)."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict

Verdict = Literal["go", "conditional_go", "no_go"]
CheckState = Literal["proven", "attested", "open"]
AttestableCheck = Literal["data_governance", "human_oversight", "monitoring", "environmental"]


class System(TypedDict, total=False):
    id: str
    name: str
    owner: str
    riskTier: str
    lifecycleStage: str
    workspaceId: str


class GateCheck(TypedDict):
    key: str
    label: str
    state: CheckState
    confidence: float
    evidenceId: Optional[str]
    detail: Optional[Dict[str, Any]]


class Gate(TypedDict, total=False):
    verdict: Verdict
    confidence: float
    band: str
    checks: List[GateCheck]
    reasons: List[str]
    proven: int
    attested: int
    open: int
    systemId: str
    riskTier: str


class ClauseCheck(TypedDict):
    check: str
    label: str
    state: CheckState
    confidence: float
    evidenceId: Optional[str]
    relation: str


class Clause(TypedDict):
    key: str
    control: str
    title: str
    group: Optional[str]
    checks: List[ClauseCheck]
    state: CheckState


class Framework(TypedDict):
    key: str
    name: str
    clauses: List[Clause]
    counts: Dict[str, int]


class ClauseMap(TypedDict):
    verdict: Verdict
    confidence: float
    frameworks: List[Framework]
    systemId: str


class FairnessRun(TypedDict):
    """Result of POST /fairness-runs. `result` holds per-attribute metrics and `all_checks_pass`."""

    runId: str
    evidenceId: str
    systemId: str
    title: str
    result: Dict[str, Any]
    gate: Gate


class MonitoringRun(TypedDict):
    """Result of POST /monitoring-runs. `result` holds drift, impact ratio and score PSI per attribute."""

    evidenceId: str
    systemId: str
    title: str
    result: Dict[str, Any]
    gate: Gate


class Attestation(TypedDict):
    evidenceId: str
    systemId: str
    check: AttestableCheck
    gate: Gate
