"""Static catalogue of agentic packs, patterns, workflows and evaluations.

Read once from pack_catalogue_data/catalogue.json (exported from the product
spreadsheet by scripts/export_pack_catalogue.py). Constants only: nothing here
is written to the database. The JSON is parsed into pydantic models and every
cross-reference is checked at import, so a pattern that names an unknown
workflow or a mapping to an unknown requirement stops the app from starting
instead of surfacing as a broken page.
"""

import json
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Optional

from pydantic import BaseModel, Field

DATA_FILE = Path(__file__).parent / "pack_catalogue_data" / "catalogue.json"

StepKind = Literal[
    "trigger", "collect", "check", "suggest", "preflight", "ask", "exception", "decide", "act", "verify", "escalate", "file"
]
Relation = Literal["Satisfies", "Partially satisfies", "Aligns with", "Supports"]
Engine = Literal["Engine exists", "Partial", "Not found"]

# A workflow with one of these relations covers the requirement; Supports does not.
COVERING = ("Satisfies", "Partially satisfies", "Aligns with")
# Step kinds a run can pause on for a human decision.
GATE_KINDS = ("ask", "exception", "decide")


class Edge(BaseModel):
    to: str
    label: Optional[str] = None


class Step(BaseModel):
    id: str
    kind: StepKind
    type: Optional[str] = None
    title: str
    detail: str
    systems: List[str] = Field(default_factory=list)
    permission: Optional[str] = None
    runsWithoutApproval: Optional[str] = None
    next: List[Edge] = Field(default_factory=list)
    failure: Optional[str] = None
    output: Optional[str] = None


class Mapping(BaseModel):
    key: str
    relation: Relation
    note: Optional[str] = None


class Workflow(BaseModel):
    id: str
    name: str
    pattern: str
    pillar: str
    commonControl: Optional[str] = None
    stage: str
    scope: Optional[str] = None
    description: str
    schedule: Optional[str] = None
    triggers: List[str] = Field(default_factory=list)
    autonomy: str
    gate: Optional[str] = None
    gateConditions: Optional[str] = None
    approver: Optional[str] = None
    separationOfDuties: Optional[str] = None
    externalWrite: bool = False
    systems: List[str] = Field(default_factory=list)
    evidence: Optional[str] = None
    agentRisks: List[str] = Field(default_factory=list)
    steps: List[Step]
    mappings: List[Mapping] = Field(default_factory=list)


class Evaluation(BaseModel):
    id: str
    name: str
    measures: Optional[str] = None
    metric: Optional[str] = None
    threshold: Optional[str] = None
    thresholdSource: Optional[str] = None
    appliesTo: Optional[str] = None
    inputs: Optional[str] = None
    commonControl: Optional[str] = None
    pattern: str
    pillar: str
    engine: Engine
    codeLocation: Optional[str] = None
    tests: List[str] = Field(default_factory=list)


class Pattern(BaseModel):
    id: str
    pillar: str
    name: str
    objective: Optional[str] = None
    agentic: bool
    pack: str
    workflows: List[str] = Field(default_factory=list)
    evaluations: List[str] = Field(default_factory=list)


class Pack(BaseModel):
    id: str
    name: str
    pillar: str
    description: str
    patterns: List[str]


class Bundle(BaseModel):
    id: str
    name: str
    for_: str = Field(alias="for")
    packs: List[str]
    targets: List[str]


class Pillar(BaseModel):
    id: str
    name: str
    description: str


class Framework(BaseModel):
    key: str
    name: str
    pillar: str
    version: Optional[str] = None
    type: Optional[str] = None
    binding: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class Requirement(BaseModel):
    key: str
    framework: str
    control: str
    title: str
    group: Optional[str] = None
    active: bool


def _need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _index(items: list, attr: str, what: str) -> dict:
    out = {getattr(i, attr): i for i in items}
    _need(len(out) == len(items), f"duplicate {what} id")
    return out


def _owners(parents: dict, parent_kind: str, list_attr: str, children: dict, kind: str, back_attr: str) -> Dict[str, str]:
    """Each child is listed by exactly one parent, and that parent is the one the child names."""
    owner: Dict[str, str] = {}
    for parent in parents.values():
        for child_id in getattr(parent, list_attr):
            _need(child_id in children, f"{parent_kind} {parent.id} names unknown {kind} {child_id}")
            _need(child_id not in owner, f"{kind} {child_id} is listed by more than one {parent_kind}")
            owner[child_id] = parent.id
    for child_id, child in children.items():
        _need(child_id in owner, f"{kind} {child_id} is in no {parent_kind}")
        _need(getattr(child, back_attr) == owner[child_id], f"{kind} {child_id} disagrees with its {parent_kind}")
    return owner


class Catalogue:
    """Parsed, cross-checked catalogue plus the coverage sets the coverage rules need."""

    def __init__(self, raw: dict):
        self.version = str(raw["version"])
        self.pillars = _index([Pillar(**p) for p in raw["pillars"]], "id", "pillar")
        self.frameworks = _index([Framework(**f) for f in raw["frameworks"]], "key", "framework")
        self.requirements = _index([Requirement(**r) for r in raw["requirements"]], "key", "requirement")
        self.workflows = _index([Workflow(**w) for w in raw["workflows"]], "id", "workflow")
        self.evaluations = _index([Evaluation(**e) for e in raw["evaluations"]], "id", "evaluation")
        self.patterns = _index([Pattern(**p) for p in raw["patterns"]], "id", "pattern")
        self.packs = _index([Pack(**p) for p in raw["packs"]], "id", "pack")
        self.bundles = _index([Bundle(**b) for b in raw["bundles"]], "id", "bundle")
        self._check()
        self._derive()

    def _check(self) -> None:
        for r in self.requirements.values():
            _need(r.framework in self.frameworks, f"requirement {r.key} names unknown framework {r.framework}")
        for kind, items in (("pattern", self.patterns), ("pack", self.packs), ("workflow", self.workflows), ("evaluation", self.evaluations)):
            for item in items.values():
                _need(item.pillar in self.pillars, f"{kind} {item.id} names unknown pillar {item.pillar}")
        for fw in self.frameworks.values():
            _need(fw.pillar in self.pillars, f"framework {fw.key} names unknown pillar {fw.pillar}")
        for wf in self.workflows.values():
            step_ids = [s.id for s in wf.steps]
            _need(len(set(step_ids)) == len(step_ids), f"workflow {wf.id} has duplicate step ids")
            for step in wf.steps:
                for edge in step.next:
                    _need(edge.to in step_ids, f"workflow {wf.id} step {step.id} leads to unknown step {edge.to}")
            for m in wf.mappings:
                _need(m.key in self.requirements, f"workflow {wf.id} maps unknown requirement {m.key}")
        for ev in self.evaluations.values():
            for key in ev.tests:
                _need(key in self.requirements, f"evaluation {ev.id} tests unknown requirement {key}")
        for b in self.bundles.values():
            for pack_id in b.packs:
                _need(pack_id in self.packs, f"bundle {b.id} names unknown pack {pack_id}")
            for key in b.targets:
                _need(key in self.frameworks, f"bundle {b.id} targets unknown framework {key}")
        _owners(self.patterns, "pattern", "workflows", self.workflows, "workflow", "pattern")
        _owners(self.patterns, "pattern", "evaluations", self.evaluations, "evaluation", "pattern")
        _owners(self.packs, "pack", "patterns", self.patterns, "pattern", "pack")

    def _derive(self) -> None:
        active = frozenset(k for k, r in self.requirements.items() if r.active)
        self.framework_keys = {
            fk: frozenset(k for k in active if self.requirements[k].framework == fk) for fk in self.frameworks
        }
        self.covers = {
            w.id: frozenset(m.key for m in w.mappings if m.relation in COVERING) & active for w in self.workflows.values()
        }
        self.supports = {
            w.id: frozenset(m.key for m in w.mappings if m.relation == "Supports") & active for w in self.workflows.values()
        }
        self.tests = {e.id: frozenset(e.tests) & active for e in self.evaluations.values()}
        self.pack_workflows = {p.id: [w for pid in p.patterns for w in self.patterns[pid].workflows] for p in self.packs.values()}
        self.pack_evaluations = {p.id: [e for pid in p.patterns for e in self.patterns[pid].evaluations] for p in self.packs.values()}
        self.workflow_pack = {w: p for p, ws in self.pack_workflows.items() for w in ws}
        self.evaluation_pack = {e: p for p, es in self.pack_evaluations.items() for e in es}
        union = frozenset().union
        self.pack_covers = {p: union(*(self.covers[w] for w in ws)) for p, ws in self.pack_workflows.items()}
        self.pack_tests = {p: union(*(self.tests[e] for e in es)) for p, es in self.pack_evaluations.items()}
        self.pack_done = {p: self.pack_covers[p] | self.pack_tests[p] for p in self.packs}
        self.pack_touched = {
            p: self.pack_done[p] | union(*(self.supports[w] for w in ws)) for p, ws in self.pack_workflows.items()
        }
        self.supported = union(*self.supports.values())
        self.requirement_workflows: Dict[str, List[tuple]] = {}
        for w in self.workflows.values():
            for m in w.mappings:
                if m.key in active:
                    self.requirement_workflows.setdefault(m.key, []).append((w.id, m.relation))
        self.requirement_evaluations: Dict[str, List[str]] = {}
        for e in self.evaluations.values():
            for key in self.tests[e.id]:
                self.requirement_evaluations.setdefault(key, []).append(e.id)


def load(raw: dict) -> Catalogue:
    """Parse and cross-check a catalogue. Raises ValueError on any dangling reference."""
    return Catalogue(raw)


_C = load(json.loads(DATA_FILE.read_text(encoding="utf-8")))

VERSION = _C.version
PILLARS, FRAMEWORKS, REQUIREMENTS = _C.pillars, _C.frameworks, _C.requirements
PACKS, PATTERNS, WORKFLOWS, EVALUATIONS, BUNDLES = _C.packs, _C.patterns, _C.workflows, _C.evaluations, _C.bundles
FRAMEWORK_KEYS = _C.framework_keys
PACK_WORKFLOWS, PACK_EVALUATIONS = _C.pack_workflows, _C.pack_evaluations
WORKFLOW_PACK, EVALUATION_PACK = _C.workflow_pack, _C.evaluation_pack
PACK_TOUCHED, PACK_DONE = _C.pack_touched, _C.pack_done
REQUIREMENT_WORKFLOWS, REQUIREMENT_EVALUATIONS = _C.requirement_workflows, _C.requirement_evaluations


class Coverage:
    """What a set of packs covers. Pack ids that are not in the catalogue (retired ids) are ignored.

    tested_by None: what the packs' evaluations could test once they pass (for what-if counts).
    tested_by a list of evaluation ids with a passing result: what is tested now.
    """

    def __init__(self, pack_ids: Iterable[str], tested_by: Optional[Iterable[str]] = None):
        ids = [p for p in pack_ids if p in PACKS]
        self.covered = frozenset().union(*(_C.pack_covers[p] for p in ids))
        if tested_by is None:
            self.tested = frozenset().union(*(_C.pack_tests[p] for p in ids))
        else:
            self.tested = frozenset().union(*(_C.tests[e] for e in tested_by if e in _C.tests))

    def count(self, framework_key: str) -> int:
        """Active requirements of the framework that are covered or tested."""
        return len(FRAMEWORK_KEYS[framework_key] & (self.covered | self.tested))


EVERY_PACK = Coverage(PACKS)


def requirement_status(key: str, installed: Coverage) -> str:
    """covered | tested | available | supported | gap, for one requirement given an org's installed packs."""
    if key in installed.covered:
        return "covered"
    if key in installed.tested:
        return "tested"
    if key in EVERY_PACK.covered or key in EVERY_PACK.tested:
        return "available"
    return "supported" if key in _C.supported else "gap"
