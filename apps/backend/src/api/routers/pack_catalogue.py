"""Static catalogue of agentic packs and their workflows.

Constants only: nothing here is written to the database. The raw dicts are
parsed into pydantic models and cross-checked at import, so a journey that
names an unknown workflow or a step whose `next` names an unknown step stops
the app from starting instead of surfacing as a broken page.
"""

from typing import Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field

StepKind = Literal["trigger", "collect", "check", "suggest", "ask", "act", "file"]


class Edge(BaseModel):
    to: str
    label: Optional[str] = None


class Step(BaseModel):
    id: str
    kind: StepKind
    title: str
    detail: str
    systems: List[str] = Field(default_factory=list)
    next: List[Edge] = Field(default_factory=list)


class Control(BaseModel):
    framework: str
    control: str
    relation: Literal["satisfies", "supports"]


class Workflow(BaseModel):
    id: str
    name: str
    version: str
    stage: str
    description: str
    pack_id: str
    steps: List[Step]
    controls: List[Control]


class Clause(BaseModel):
    number: str
    name: str
    workflow_ids: List[str] = Field(default_factory=list)


class Pack(BaseModel):
    id: str
    name: str
    version: str
    description: str
    journey: Optional[List[Clause]] = None


def _edges(*targets: str) -> List[dict]:
    return [{"to": t} for t in targets]


def _gate(approved: str, revise: str) -> List[dict]:
    return [{"to": approved, "label": "approved"}, {"to": revise, "label": "changes asked"}]


_PACKS: List[dict] = [
    {
        "id": "iso_42001",
        "name": "ISO/IEC 42001",
        "version": "1",
        "description": (
            "Workflows that produce the records an ISO/IEC 42001 AI management system audit asks for, "
            "organised by the standard's clauses."
        ),
        "journey": [
            {"number": "4", "name": "Context of the organization"},
            {"number": "5", "name": "Leadership", "workflow_ids": ["ai_policy_review"]},
            {
                "number": "6",
                "name": "Planning",
                "workflow_ids": ["ai_risk_assessment", "ai_system_impact_assessment"],
            },
            {"number": "7", "name": "Support"},
            {"number": "8", "name": "Operation"},
            {"number": "9", "name": "Performance evaluation"},
            {"number": "10", "name": "Improvement"},
        ],
    },
    {
        "id": "security_controls",
        "name": "Security Controls",
        "version": "1",
        "description": "Workflows that check security controls over AI systems and file the evidence.",
    },
]

_WORKFLOWS: List[dict] = [
    {
        "id": "ai_policy_review",
        "name": "AI policy review",
        "version": "1",
        "stage": "govern",
        "pack_id": "iso_42001",
        "description": (
            "Reviews the organization's AI policy against ISO/IEC 42001 clause 5.2 and control A.2.2, "
            "proposes changes, and files the owner's decision as evidence."
        ),
        "controls": [
            {"framework": "ISO/IEC 42001", "control": "5.2", "relation": "satisfies"},
            {"framework": "ISO/IEC 42001", "control": "A.2.2", "relation": "satisfies"},
        ],
        "steps": [
            {
                "id": "trigger",
                "kind": "trigger",
                "title": "Start the review",
                "detail": "Starts when a policy review is requested for the organization.",
                "next": _edges("collect-policy"),
            },
            {
                "id": "collect-policy",
                "kind": "collect",
                "title": "Collect the current AI policy",
                "detail": "Reads the active AI policy and its version history from the policy library.",
                "systems": ["Policy library"],
                "next": _edges("check-policy"),
            },
            {
                "id": "check-policy",
                "kind": "check",
                "title": "Check the policy against 5.2",
                "detail": (
                    "Checks that the policy fits the organization's purpose, gives a framework for AI objectives, "
                    "commits to meeting applicable requirements and to continual improvement, and is documented "
                    "and available as control A.2.2 requires."
                ),
                "next": _edges("suggest"),
            },
            {
                "id": "suggest",
                "kind": "suggest",
                "title": "Suggest changes",
                "detail": "Lists each gap against clause 5.2 with the wording change that would close it.",
                "next": _edges("ask"),
            },
            {
                "id": "ask",
                "kind": "ask",
                "title": "Ask the policy owner",
                "detail": "Sends the suggested changes to the policy owner for approval before anything is recorded.",
                "next": _gate("record", "suggest-revise"),
            },
            {
                "id": "record",
                "kind": "act",
                "title": "Record the approved policy",
                "detail": "Saves the approved wording as a new version of the policy.",
                "next": _edges("file-evidence"),
            },
            {
                "id": "suggest-revise",
                "kind": "suggest",
                "title": "Revise",
                "detail": "Reworks the suggested changes using the owner's comments.",
                "next": _edges("ask"),
            },
            {
                "id": "file-evidence",
                "kind": "file",
                "title": "File evidence",
                "detail": "Files the reviewed policy, the findings and the owner's decision against clause 5.2 and A.2.2.",
            },
        ],
    },
    {
        "id": "ai_risk_assessment",
        "name": "AI risk assessment",
        "version": "1",
        "stage": "assess",
        "pack_id": "iso_42001",
        "description": (
            "Identifies and rates the risks of an AI system against the organization's risk criteria, "
            "as ISO/IEC 42001 clause 6.1.2 requires, and files the approved risk record."
        ),
        "controls": [
            {"framework": "ISO/IEC 42001", "control": "6.1.2", "relation": "satisfies"},
            {"framework": "ISO/IEC 42001", "control": "8.2", "relation": "supports"},
        ],
        "steps": [
            {
                "id": "trigger",
                "kind": "trigger",
                "title": "Start the assessment",
                "detail": "Starts when an assessment is requested for an AI system, or when one is due again.",
                "next": _edges("collect-context"),
            },
            {
                "id": "collect-context",
                "kind": "collect",
                "title": "Collect the system context",
                "detail": "Reads the system's purpose, owner, risk tier, linked model and earlier risk records.",
                "systems": ["AI system inventory", "Model registry"],
                "next": _edges("check-criteria"),
            },
            {
                "id": "check-criteria",
                "kind": "check",
                "title": "Identify risks against the criteria",
                "detail": (
                    "Identifies risks to the system's objectives and applies the organization's risk acceptance "
                    "criteria to each one."
                ),
                "next": _edges("suggest"),
            },
            {
                "id": "suggest",
                "kind": "suggest",
                "title": "Rate and treat each risk",
                "detail": "Proposes a likelihood, a consequence and a treatment for every risk found.",
                "next": _edges("ask"),
            },
            {
                "id": "ask",
                "kind": "ask",
                "title": "Ask the risk owner",
                "detail": "Sends the rated risks to the risk owner to accept or send back.",
                "next": _gate("record", "suggest-revise"),
            },
            {
                "id": "record",
                "kind": "act",
                "title": "Record the risks",
                "detail": "Saves the approved risks and treatments to the system's risk register.",
                "next": _edges("file-evidence"),
            },
            {
                "id": "suggest-revise",
                "kind": "suggest",
                "title": "Revise",
                "detail": "Reworks the ratings and treatments using the owner's comments.",
                "next": _edges("ask"),
            },
            {
                "id": "file-evidence",
                "kind": "file",
                "title": "File evidence",
                "detail": "Files the assessment, the criteria used and the owner's decision against 6.1.2 and 8.2.",
            },
        ],
    },
    {
        "id": "ai_system_impact_assessment",
        "name": "AI system impact assessment",
        "version": "1",
        "stage": "assess",
        "pack_id": "iso_42001",
        "description": (
            "Assesses the consequences of an AI system for individuals, groups and society, as ISO/IEC 42001 "
            "clause 6.1.4 and control A.5.2 require, and files the approved assessment."
        ),
        "controls": [
            {"framework": "ISO/IEC 42001", "control": "6.1.4", "relation": "satisfies"},
            {"framework": "ISO/IEC 42001", "control": "A.5.2", "relation": "satisfies"},
        ],
        "steps": [
            {
                "id": "trigger",
                "kind": "trigger",
                "title": "Start the assessment",
                "detail": "Starts when an impact assessment is requested for a new or changed AI system.",
                "next": _edges("collect-context"),
            },
            {
                "id": "collect-context",
                "kind": "collect",
                "title": "Describe the system and who it affects",
                "detail": "Reads the intended use, the people and groups the system's outputs reach, and its deployment context.",
                "systems": ["AI system inventory", "Model registry"],
                "next": _edges("check-impact"),
            },
            {
                "id": "check-impact",
                "kind": "check",
                "title": "Assess the impact",
                "detail": (
                    "Assesses the foreseeable consequences of intended use and reasonably foreseeable misuse "
                    "for individuals, groups and society."
                ),
                "next": _edges("suggest"),
            },
            {
                "id": "suggest",
                "kind": "suggest",
                "title": "Suggest mitigations",
                "detail": "Proposes a mitigation or monitoring measure for each impact found.",
                "next": _edges("ask"),
            },
            {
                "id": "ask",
                "kind": "ask",
                "title": "Ask the assessment owner",
                "detail": "Sends the assessment to its owner to approve or send back.",
                "next": _gate("record", "suggest-revise"),
            },
            {
                "id": "record",
                "kind": "act",
                "title": "Record the assessment",
                "detail": "Saves the approved assessment against the AI system.",
                "next": _edges("file-evidence"),
            },
            {
                "id": "suggest-revise",
                "kind": "suggest",
                "title": "Revise",
                "detail": "Reworks the impacts and mitigations using the owner's comments.",
                "next": _edges("ask"),
            },
            {
                "id": "file-evidence",
                "kind": "file",
                "title": "File evidence",
                "detail": "Files the assessment and the owner's decision against 6.1.4 and A.5.2.",
            },
        ],
    },
    {
        "id": "access_control_review",
        "name": "Access control review",
        "version": "1",
        "stage": "govern",
        "pack_id": "security_controls",
        "description": (
            "Finds who can reach an AI system and its model, matches them to current staff, checks the result "
            "against the access policy, and files the owner's decision as evidence."
        ),
        "controls": [
            {"framework": "ISO 27001", "control": "A.5.15", "relation": "satisfies"},
            {"framework": "ISO 27001", "control": "A.5.18", "relation": "satisfies"},
            {"framework": "ISO 27001", "control": "A.8.2", "relation": "satisfies"},
            {"framework": "SOC 2", "control": "CC6.1", "relation": "satisfies"},
            {"framework": "SOC 2", "control": "CC6.2", "relation": "satisfies"},
            {"framework": "SOC 2", "control": "CC6.3", "relation": "satisfies"},
        ],
        "steps": [
            {
                "id": "trigger",
                "kind": "trigger",
                "title": "Start the review",
                "detail": "Starts when an access review is requested or comes due.",
                "next": _edges("collect-access"),
            },
            {
                "id": "collect-access",
                "kind": "collect",
                "title": "Find who has access",
                "detail": "Lists every account with access to the system, its data and its model.",
                "systems": ["Okta", "AWS IAM", "Model registry"],
                "next": _edges("collect-hr"),
            },
            {
                "id": "collect-hr",
                "kind": "collect",
                "title": "Match to HR",
                "detail": "Matches each account to a current employee or contractor and their role.",
                "systems": ["HRIS"],
                "next": _edges("check-policy"),
            },
            {
                "id": "check-policy",
                "kind": "check",
                "title": "Check the policy",
                "detail": (
                    "Flags accounts with no matching person, access beyond the person's role, and "
                    "privileged access without a recorded approval."
                ),
                "next": _edges("suggest"),
            },
            {
                "id": "suggest",
                "kind": "suggest",
                "title": "Suggest fixes",
                "detail": "Proposes the access to remove or reduce for each flagged account.",
                "next": _edges("ask"),
            },
            {
                "id": "ask",
                "kind": "ask",
                "title": "Ask the owner",
                "detail": "Sends the proposed access changes to the system owner to approve or send back.",
                "next": _gate("act", "suggest-revise"),
            },
            {
                "id": "act",
                "kind": "act",
                "title": "Make changes",
                "detail": "Applies the approved access changes.",
                "next": _edges("file-evidence"),
            },
            {
                "id": "suggest-revise",
                "kind": "suggest",
                "title": "Revise",
                "detail": "Reworks the proposed changes using the owner's comments.",
                "next": _edges("ask"),
            },
            {
                "id": "file-evidence",
                "kind": "file",
                "title": "File evidence",
                "detail": "Files the access list, the findings, the owner's decision and the changes made.",
            },
        ],
    },
]


def load(raw_packs: List[dict], raw_workflows: List[dict]) -> Tuple[Dict[str, Pack], Dict[str, Workflow]]:
    """Parse and cross-check a catalogue. Raises ValueError on any dangling reference."""
    packs = {p["id"]: Pack(**p) for p in raw_packs}
    workflows = {w["id"]: Workflow(**w) for w in raw_workflows}
    if len(packs) != len(raw_packs) or len(workflows) != len(raw_workflows):
        raise ValueError("duplicate pack or workflow id")
    for wf in workflows.values():
        if wf.pack_id not in packs:
            raise ValueError(f"workflow {wf.id} names unknown pack {wf.pack_id}")
        step_ids = [s.id for s in wf.steps]
        if len(set(step_ids)) != len(step_ids):
            raise ValueError(f"workflow {wf.id} has duplicate step ids")
        for step in wf.steps:
            for edge in step.next:
                if edge.to not in step_ids:
                    raise ValueError(f"workflow {wf.id} step {step.id} leads to unknown step {edge.to}")
    for pack in packs.values():
        for clause in pack.journey or []:
            for workflow_id in clause.workflow_ids:
                if workflow_id not in workflows:
                    raise ValueError(f"pack {pack.id} clause {clause.number} names unknown workflow {workflow_id}")
                if workflows[workflow_id].pack_id != pack.id:
                    raise ValueError(f"pack {pack.id} lists workflow {workflow_id} that belongs to another pack")
    return packs, workflows


PACKS, WORKFLOWS = load(_PACKS, _WORKFLOWS)
