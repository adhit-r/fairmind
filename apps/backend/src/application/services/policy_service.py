"""Organization AI policies: drafting, distribution, framework mapping and enforcement.

A policy is a written document plus a list of rules (policy as code). Each rule
is plain JSON, never executed code:

    {
      "id": "high-risk-approval",
      "title": "High-risk systems need a release approval",
      "severity": "high",                 # low | medium | high | critical
      "enforcement": "block",             # block fails the policy gate, warn only reports
      "when":  {"fact": "system.risk_tier", "op": "in", "value": ["high", "unacceptable"]},
      "check": {"fact": "approval.status", "op": "eq", "value": "approved"},
      "controls": ["aiuc-1:A001.1"]       # framework_key:control external id
    }

Conditions nest with {"all": [...]}, {"any": [...]} and {"not": {...}}. Facts are
read per AI system from the governance tables (see FACTS).
"""

from __future__ import annotations

import asyncio
import html
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from database.governance_models import (
    GovernanceAISystem,
    GovernanceApprovalRequest,
    GovernanceControlDefinition,
    GovernanceEvidenceRun,
    GovernanceFrameworkAssignment,
    GovernanceFrameworkVersion,
    GovernanceRemediationTask,
    GovernanceRisk,
    OrgPolicy,
    OrgPolicyAcknowledgement,
    OrgPolicyAlert,
    OrgPolicyEvaluation,
    OrgPolicyVersion,
)
from database.models import OrganizationMember, User
from src.application.services.governance_assurance_service import GovernanceAssuranceService

SEVERITIES = ("low", "medium", "high", "critical")
ENFORCEMENTS = ("block", "warn")
OPS = ("eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "contains", "exists")
FACTS = {
    "system.risk_tier": "Risk tier recorded for the system",
    "system.lifecycle_stage": "Lifecycle stage of the system",
    "system.status": "Operational status of the system",
    "system.owner": "Named owner of the system",
    "system.system_type": "Kind of system",
    "approval.status": "Latest release approval: none, pending, approved or rejected",
    "risks.open": "Open risks on the system",
    "risks.open_high": "Open high-severity risks",
    "risks.open_critical": "Open critical risks",
    "remediation.open": "Remediation tasks not yet resolved",
    "evidence.total": "Evidence runs recorded",
    "evidence.passed": "Evidence runs that passed",
    "evidence.failed": "Evidence runs that failed",
    "evidence.expired": "Evidence runs past their expiry",
    "evidence.sources_passed": "Evidence source types with a passing run",
    "frameworks.assigned": "Framework keys assigned to the system",
    "controls.applicable": "Applicable controls across assigned frameworks",
    "controls.accepted": "Controls accepted",
    "controls.accepted_ratio": "Accepted share of applicable controls, 0 to 1",
    "controls.missing_evidence": "Applicable controls with no accepted passing evidence",
    "controls.stale_evidence": "Controls whose evidence is past its review frequency",
    "controls.blocking_findings": "Controls rejected by a reviewer",
}
METADATA_PREFIX = "system.metadata."
STATUSES = ("draft", "in_review", "approved", "published", "retired")
TRANSITIONS = {
    "submit": ({"draft"}, "in_review"),
    "reject": ({"in_review"}, "draft"),
    "approve": ({"in_review"}, "approved"),
    "publish": ({"approved"}, "published"),
    "revise": ({"published"}, "draft"),
    "retire": ({"draft", "in_review", "approved", "published"}, "retired"),
}
_CLOSED = {"resolved", "closed", "mitigated", "accepted"}


class PolicyStateError(ValueError):
    """Raised when a lifecycle action is not allowed from the current status."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _same_id(value: Any) -> str:
    """One spelling for a user id stored dashed, as plain hex, or as a UUID."""
    try:
        return uuid.UUID(str(value)).hex
    except ValueError:
        return str(value)


# ---------------------------------------------------------------------------
# Rules: validation and evaluation (pure)
# ---------------------------------------------------------------------------


def _validate_condition(cond: Any, where: str) -> None:
    if not isinstance(cond, dict):
        raise ValueError(f"{where}: condition must be an object")
    if "all" in cond or "any" in cond:
        key = "all" if "all" in cond else "any"
        items = cond[key]
        if not isinstance(items, list) or not items:
            raise ValueError(f"{where}: '{key}' needs a non-empty list")
        for index, child in enumerate(items):
            _validate_condition(child, f"{where}.{key}[{index}]")
        return
    if "not" in cond:
        _validate_condition(cond["not"], f"{where}.not")
        return
    fact, op = cond.get("fact"), cond.get("op")
    if fact not in FACTS and not (isinstance(fact, str) and fact.startswith(METADATA_PREFIX) and len(fact) > len(METADATA_PREFIX)):
        raise ValueError(f"{where}: unknown fact {fact!r}")
    if op not in OPS:
        raise ValueError(f"{where}: unknown op {op!r}, use one of {', '.join(OPS)}")
    if op != "exists" and "value" not in cond:
        raise ValueError(f"{where}: op '{op}' needs a value")
    if op in ("in", "not_in") and not isinstance(cond["value"], list):
        raise ValueError(f"{where}: op '{op}' needs a list value")


def validate_rules(rules: Any) -> list[dict]:
    """Return the rules normalized, or raise ValueError naming the first problem."""
    if not isinstance(rules, list):
        raise ValueError("rules must be a list")
    seen: set[str] = set()
    normalized = []
    for index, rule in enumerate(rules):
        where = f"rules[{index}]"
        if not isinstance(rule, dict):
            raise ValueError(f"{where}: rule must be an object")
        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise ValueError(f"{where}: id is required")
        if rule_id in seen:
            raise ValueError(f"{where}: duplicate id {rule_id!r}")
        seen.add(rule_id)
        if not isinstance(rule.get("title"), str) or not rule["title"].strip():
            raise ValueError(f"{where}: title is required")
        severity = rule.get("severity", "medium")
        enforcement = rule.get("enforcement", "warn")
        if severity not in SEVERITIES:
            raise ValueError(f"{where}: severity must be one of {', '.join(SEVERITIES)}")
        if enforcement not in ENFORCEMENTS:
            raise ValueError(f"{where}: enforcement must be block or warn")
        if "check" not in rule:
            raise ValueError(f"{where}: check is required")
        _validate_condition(rule["check"], f"{where}.check")
        if rule.get("when") is not None:
            _validate_condition(rule["when"], f"{where}.when")
        controls = rule.get("controls", [])
        if not isinstance(controls, list) or not all(isinstance(c, str) and ":" in c for c in controls):
            raise ValueError(f"{where}: controls must be a list of 'framework:control' references")
        normalized.append(
            {
                "id": rule_id,
                "title": rule["title"],
                "severity": severity,
                "enforcement": enforcement,
                **({"when": rule["when"]} if rule.get("when") is not None else {}),
                "check": rule["check"],
                "controls": controls,
            }
        )
    return normalized


def _fact(facts: dict, path: str) -> Any:
    if path.startswith(METADATA_PREFIX):
        value: Any = facts.get("system.metadata", {})
        for key in path[len(METADATA_PREFIX):].split("."):
            value = value.get(key) if isinstance(value, dict) else None
        return value
    return facts.get(path)


def _compare(actual: Any, op: str, expected: Any) -> bool:
    if op == "exists":
        return actual not in (None, "", [], {})
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "in":
        return actual in expected
    if op == "not_in":
        return actual not in expected
    if op == "contains":
        return isinstance(actual, (list, str)) and expected in actual
    try:
        a, b = float(actual), float(expected)
    except (TypeError, ValueError):
        return False
    return {"gt": a > b, "gte": a >= b, "lt": a < b, "lte": a <= b}[op]


def evaluate_condition(cond: dict, facts: dict, notes: list[str]) -> bool:
    """Evaluate a validated condition; failing leaves append what was observed."""
    if "all" in cond:
        return all([evaluate_condition(c, facts, notes) for c in cond["all"]])
    if "any" in cond:
        branch: list[str] = []
        passed = any([evaluate_condition(c, facts, branch) for c in cond["any"]])
        if not passed:
            notes.append("none of: " + "; ".join(branch))
        return passed
    if "not" in cond:
        inner: list[str] = []
        passed = not evaluate_condition(cond["not"], facts, inner)
        if not passed:
            notes.append(f"expected the opposite of {cond['not']}")
        return passed
    actual = _fact(facts, cond["fact"])
    passed = _compare(actual, cond["op"], cond.get("value"))
    if not passed:
        expected = "" if cond["op"] == "exists" else f" {json.dumps(cond.get('value'))}"
        notes.append(f"{cond['fact']} is {json.dumps(actual)}, expected {cond['op']}{expected}")
    return passed


def evaluate_rule(rule: dict, facts: dict) -> tuple[str, str]:
    """Return (outcome, detail) for one rule against one system's facts."""
    if rule.get("when") is not None and not evaluate_condition(rule["when"], facts, []):
        return "not_applicable", "Rule does not apply to this system"
    notes: list[str] = []
    if evaluate_condition(rule["check"], facts, notes):
        return "pass", "All conditions met"
    return "fail", "; ".join(notes)


def _conditions(items: Any) -> dict | None:
    """A model's flat list of conditions as one condition: all of them must hold."""
    if not isinstance(items, list):
        return None
    conds = [
        {k: v for k, v in c.items() if not (k == "value" and c.get("op") == "exists")}
        for c in items
        if isinstance(c, dict)
    ]
    if not conds:
        return None
    return conds[0] if len(conds) == 1 else {"all": conds}


_CONDITION_SCHEMA = {
    "type": "object",
    "properties": {
        "fact": {"type": "string"},
        "op": {"type": "string", "enum": list(OPS)},
        "value": {
            "anyOf": [
                {"type": "string"},
                {"type": "number"},
                {"type": "boolean"},
                {"type": "array", "items": {"anyOf": [{"type": "string"}, {"type": "number"}]}},
                {"type": "null"},
            ]
        },
    },
    "required": ["fact", "op", "value"],
    "additionalProperties": False,
}
DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "summary": {"type": "string"},
        "body": {"type": "string"},
        "rules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "severity": {"type": "string", "enum": list(SEVERITIES)},
                    "enforcement": {"type": "string", "enum": list(ENFORCEMENTS)},
                    "when": {"type": "array", "items": _CONDITION_SCHEMA},
                    "check": {"type": "array", "items": _CONDITION_SCHEMA},
                    "controls": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id", "title", "severity", "enforcement", "when", "check", "controls"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["name", "summary", "body", "rules"],
    "additionalProperties": False,
}
DRAFT_SYSTEM = """You draft AI governance policies for an organization.
Write the policy text in plain Markdown: purpose, scope, the requirements, roles and responsibilities,
and exceptions. Keep it specific to the brief and the organization's AI systems; do not invent facts
about the organization.
Then turn each requirement that the platform can check into a rule. A rule has:
- id: short kebab-case, unique; title: one plain sentence
- severity: low, medium, high or critical; enforcement: block (stops a release approval) or warn
- when: conditions that decide whether the rule applies to a system (empty list: every system)
- check: conditions that must all hold for the system to pass
- controls: references from the controls list that the rule gives evidence for (only listed refs)
A condition is {fact, op, value}. Use only the listed facts, or system.metadata.<key> for a value
recorded in the system's metadata. Use null as the value for the exists op, a list for in and not_in.
Only write rules for requirements these facts can express; leave the rest as policy text."""


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


class PolicyService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- reading ------------------------------------------------------------

    def _row(self, org_id: str, policy_id: str) -> dict | None:
        p = OrgPolicy.__table__
        row = self.db.execute(select(p).where(p.c.id == policy_id, p.c.org_id == org_id)).mappings().first()
        return dict(row) if row else None

    def _member_count(self, org_id: str) -> int:
        m = OrganizationMember.__table__.c
        return self.db.execute(
            select(func.count()).select_from(OrganizationMember.__table__).where(
                m.org_id == uuid.UUID(org_id), m.status == "active"
            )
        ).scalar_one()

    def _serialize(self, row: dict, user_id: str, members: int) -> dict:
        a = OrgPolicyAcknowledgement.__table__.c
        acked: list[str] = []
        if row["published_version"]:
            acked = list(
                self.db.execute(
                    select(a.user_id).where(a.policy_id == row["id"], a.version == row["published_version"])
                ).scalars()
            )
        rules = json.loads(row["rules_json"])
        return {
            "id": row["id"],
            "name": row["name"],
            "summary": row["summary"],
            "body": row["body"],
            "owner": row["owner"],
            "status": row["status"],
            "version": row["version"],
            "publishedVersion": row["published_version"],
            "enforced": row["status"] != "retired" and row["published_version"] is not None,
            "rules": rules,
            "controlRefs": sorted({ref for rule in rules for ref in rule.get("controls", [])}),
            "createdBy": row["created_by"],
            "submittedBy": row["submitted_by"],
            "approvedBy": row["approved_by"],
            "approvedAt": row["approved_at"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "acknowledgement": {
                "required": members if row["published_version"] else 0,
                "acknowledged": len(acked),
                "mine": user_id in acked,
            },
        }

    def list(self, org_id: str, user_id: str) -> list[dict]:
        p = OrgPolicy.__table__
        members = self._member_count(org_id)
        rows = self.db.execute(select(p).where(p.c.org_id == org_id).order_by(p.c.updated_at.desc())).mappings()
        return [self._serialize(dict(r), user_id, members) for r in rows]

    def get(self, org_id: str, policy_id: str, user_id: str) -> dict | None:
        row = self._row(org_id, policy_id)
        return self._serialize(row, user_id, self._member_count(org_id)) if row else None

    def versions(self, org_id: str, policy_id: str) -> list[dict] | None:
        if not self._row(org_id, policy_id):
            return None
        v = OrgPolicyVersion.__table__
        rows = self.db.execute(
            select(v).where(v.c.policy_id == policy_id, v.c.org_id == org_id).order_by(v.c.version.desc())
        ).mappings()
        return [
            {
                "version": r["version"],
                "name": r["name"],
                "summary": r["summary"],
                "body": r["body"],
                "rules": json.loads(r["rules_json"]),
                "approvedBy": r["approved_by"],
                "publishedBy": r["published_by"],
                "publishedAt": r["published_at"],
            }
            for r in rows
        ]

    def acknowledgements(self, org_id: str, policy_id: str) -> list[dict] | None:
        row = self._row(org_id, policy_id)
        if not row:
            return None
        m, u, a = OrganizationMember.__table__.c, User.__table__.c, OrgPolicyAcknowledgement.__table__.c
        acked = {
            _same_id(r["user_id"]): r["acknowledged_at"]
            for r in self.db.execute(
                select(a.user_id, a.acknowledged_at).where(
                    a.policy_id == policy_id, a.version == (row["published_version"] or -1)
                )
            ).mappings()
        }
        members = self.db.execute(
            select(m.user_id, m.role, u.email, u.name)
            .outerjoin(User.__table__, u.id == m.user_id)
            .where(m.org_id == uuid.UUID(org_id), m.status == "active")
            .order_by(u.email)
        ).mappings()
        return [
            {
                "userId": str(r["user_id"]),
                "email": r["email"] or str(r["user_id"]),
                "name": r["name"],
                "role": r["role"],
                "acknowledgedAt": acked.get(_same_id(r["user_id"])),
            }
            for r in members
        ]

    # -- framework mapping --------------------------------------------------

    def _latest_versions(self) -> list[dict]:
        fv = GovernanceFrameworkVersion.__table__
        latest: dict[str, dict] = {}
        for row in self.db.execute(select(fv).order_by(fv.c.imported_at.desc())).mappings():
            latest.setdefault(row["framework_key"], dict(row))
        return list(latest.values())

    def _controls_by_ref(self) -> dict[str, dict]:
        cd = GovernanceControlDefinition.__table__
        refs: dict[str, dict] = {}
        for version in self._latest_versions():
            for row in self.db.execute(
                select(cd.c.external_id, cd.c.title, cd.c.parent_requirement_id, cd.c.parent_requirement_title)
                .where(cd.c.framework_version_id == version["id"], cd.c.active == 1)
                .order_by(cd.c.external_id)
            ).mappings():
                refs[f"{version['framework_key']}:{row['external_id']}"] = {
                    **dict(row),
                    "framework_key": version["framework_key"],
                }
        return refs

    def _check_refs(self, rules: list[dict]) -> None:
        known = self._controls_by_ref()
        for rule in rules:
            unknown = [ref for ref in rule["controls"] if ref not in known]
            if unknown:
                raise ValueError(f"rule {rule['id']!r}: unknown framework control {unknown[0]!r}")

    def coverage(self, org_id: str) -> list[dict]:
        """Each framework control, the published rules mapped to it, and whether they hold.

        A control is failing when any mapped rule fails on any system, passing when
        mapped rules pass and none fail, and unchecked when no system was assessed.
        Drafts do not count: only the published, enforced version of a policy does.
        """
        outcomes: dict[tuple, list[str]] = {}
        for r in self.current_results(org_id):
            outcomes.setdefault((r["policyId"], r["policyVersion"], r["ruleId"]), []).append(r["outcome"])
        covering: dict[str, list[dict]] = {}
        for policy in self._enforced(org_id, None):
            for rule in json.loads(policy["rules_json"]):
                seen = outcomes.get((policy["id"], policy["version"], rule["id"]), [])
                entry = {
                    "policyId": policy["id"],
                    "policyName": policy["name"],
                    "policyVersion": policy["version"],
                    "ruleId": rule["id"],
                    "ruleTitle": rule["title"],
                    "enforcement": rule["enforcement"],
                    "passingSystems": seen.count("pass"),
                    "failingSystems": seen.count("fail"),
                }
                for ref in rule.get("controls", []):
                    covering.setdefault(ref, []).append(entry)
        controls = self._controls_by_ref()
        out = []
        for version in self._latest_versions():
            key = version["framework_key"]
            items = []
            for ref, c in controls.items():
                if c["framework_key"] != key:
                    continue
                rules = covering.get(ref, [])
                if any(r["failingSystems"] for r in rules):
                    status = "failing"
                elif any(r["passingSystems"] for r in rules):
                    status = "passing"
                else:
                    status = "unchecked" if rules else "unmapped"
                items.append(
                    {
                        "ref": ref,
                        "externalId": c["external_id"],
                        "title": c["title"],
                        "requirementId": c["parent_requirement_id"],
                        "requirementTitle": c["parent_requirement_title"],
                        "status": status,
                        "coveredBy": rules,
                    }
                )
            count = lambda status: sum(1 for i in items if i["status"] == status)  # noqa: E731
            out.append(
                {
                    "frameworkKey": key,
                    "name": version["name"],
                    "versionLabel": version["version_label"],
                    "totalControls": len(items),
                    "coveredControls": len(items) - count("unmapped"),
                    "passingControls": count("passing"),
                    "failingControls": count("failing"),
                    "uncheckedControls": count("unchecked"),
                    "controls": items,
                }
            )
        return out

    def draft_context(self, org_id: str, brief: str) -> str:
        """What the model may know to draft a policy: the brief, the rule language, controls, systems."""
        s = GovernanceAISystem.__table__
        systems = [
            dict(r)
            for r in self.db.execute(
                select(s.c.name, s.c.system_type, s.c.risk_tier, s.c.lifecycle_stage)
                .where(s.c.org_id == org_id)
                .order_by(s.c.name)
                .limit(50)
            ).mappings()
        ]
        p = OrgPolicy.__table__
        existing = list(self.db.execute(select(p.c.name).where(p.c.org_id == org_id, p.c.status != "retired")).scalars())
        controls = [
            {"ref": ref, "title": c["title"], "requirement": c["parent_requirement_title"]}
            for ref, c in self._controls_by_ref().items()
        ]
        return json.dumps(
            {
                "brief": brief,
                "facts": FACTS,
                "ops": list(OPS),
                "controls": controls,
                "aiSystems": systems,
                "existingPolicies": existing,
            },
            default=str,
        )

    def create_from_draft(self, org_id: str, actor: str, data: dict) -> tuple[dict, list[str]]:
        """Save a model's draft as a draft policy, keeping only rules that pass validation."""
        known = self._controls_by_ref()
        rules, dropped, seen = [], [], set()
        for raw in data.get("rules") or []:
            if not isinstance(raw, dict):
                continue
            label = str(raw.get("title") or raw.get("id") or "Untitled rule")
            when = _conditions(raw.get("when"))
            candidate = {
                "id": raw.get("id"),
                "title": raw.get("title"),
                "severity": raw.get("severity", "medium"),
                "enforcement": raw.get("enforcement", "warn"),
                "check": _conditions(raw.get("check")),
                **({"when": when} if when else {}),
                "controls": [c for c in raw.get("controls") or [] if c in known],
            }
            if candidate["check"] is None:
                candidate.pop("check")
            try:
                rule = validate_rules([candidate])[0]
            except ValueError as error:
                dropped.append(f"{label}: {str(error).removeprefix('rules[0]').lstrip('.: ')}")
                continue
            if rule["id"] in seen:
                dropped.append(f"{label}: duplicate id {rule['id']!r}")
                continue
            seen.add(rule["id"])
            rules.append(rule)
        name = str(data.get("name") or "").strip()[:200] or "Untitled AI policy"
        policy = self.create(
            org_id,
            actor,
            {
                "name": name,
                "summary": str(data.get("summary") or "")[:2000],
                "body": str(data.get("body") or "")[:200_000],
                "owner": None,
                "rules": rules,
            },
        )
        return policy, dropped

    # -- writing ------------------------------------------------------------

    def create(self, org_id: str, actor: str, values: dict) -> dict:
        rules = validate_rules(values.get("rules", []))
        self._check_refs(rules)
        now, policy_id = _now(), str(uuid.uuid4())
        self.db.execute(
            insert(OrgPolicy.__table__).values(
                id=policy_id,
                org_id=org_id,
                name=values["name"],
                summary=values.get("summary") or "",
                body=values.get("body") or "",
                owner=values.get("owner"),
                status="draft",
                version=1,
                rules_json=json.dumps(rules),
                created_by=actor,
                created_at=now,
                updated_at=now,
            )
        )
        self.db.commit()
        return self.get(org_id, policy_id, actor)

    def update(self, org_id: str, policy_id: str, actor: str, values: dict) -> dict | None:
        row = self._row(org_id, policy_id)
        if not row:
            return None
        if row["status"] != "draft":
            raise PolicyStateError("Only draft policies can be edited; revise a published policy first")
        changes = {k: values[k] for k in ("name", "summary", "body", "owner") if k in values and values[k] is not None}
        if values.get("rules") is not None:
            rules = validate_rules(values["rules"])
            self._check_refs(rules)
            changes["rules_json"] = json.dumps(rules)
        if changes:
            p = OrgPolicy.__table__
            self.db.execute(update(p).where(p.c.id == policy_id).values(**changes, updated_at=_now()))
            self.db.commit()
        return self.get(org_id, policy_id, actor)

    def transition(self, org_id: str, policy_id: str, actor: str, action: str) -> dict | None:
        row = self._row(org_id, policy_id)
        if not row:
            return None
        allowed_from, target = TRANSITIONS[action]
        if row["status"] not in allowed_from:
            raise PolicyStateError(f"Cannot {action} a policy that is {row['status']}")
        now = _now()
        values: dict[str, Any] = {"status": target, "updated_at": now}
        if action == "submit":
            if not json.loads(row["rules_json"]) and not row["body"].strip():
                raise PolicyStateError("Write the policy text or add a rule before submitting")
            values["submitted_by"] = actor
        elif action == "approve":
            values.update(approved_by=actor, approved_at=now)
        elif action == "revise":
            values.update(version=row["version"] + 1, submitted_by=None, approved_by=None, approved_at=None)
        elif action == "publish":
            values["published_version"] = row["version"]
            self.db.execute(
                insert(OrgPolicyVersion.__table__).values(
                    id=str(uuid.uuid4()),
                    org_id=org_id,
                    policy_id=policy_id,
                    version=row["version"],
                    name=row["name"],
                    summary=row["summary"],
                    body=row["body"],
                    rules_json=row["rules_json"],
                    approved_by=row["approved_by"],
                    published_by=actor,
                    published_at=now,
                )
            )
        p = OrgPolicy.__table__
        self.db.execute(update(p).where(p.c.id == policy_id).values(**values))
        self.db.commit()
        if action == "publish":
            self.enforce(org_id, policy_id=policy_id)
        return self.get(org_id, policy_id, actor)

    def delete(self, org_id: str, policy_id: str) -> bool:
        row = self._row(org_id, policy_id)
        if not row:
            return False
        if row["published_version"] is not None:
            raise PolicyStateError("A policy that was published is part of the audit record; retire it instead")
        self.db.execute(delete(OrgPolicy.__table__).where(OrgPolicy.__table__.c.id == policy_id))
        self.db.commit()
        return True

    def acknowledge(self, org_id: str, policy_id: str, user_id: str) -> dict | None:
        row = self._row(org_id, policy_id)
        if not row:
            return None
        if not row["published_version"] or row["status"] == "retired":
            raise PolicyStateError("Only a published policy can be acknowledged")
        a = OrgPolicyAcknowledgement.__table__
        exists = self.db.execute(
            select(a.c.id).where(a.c.policy_id == policy_id, a.c.version == row["published_version"], a.c.user_id == user_id)
        ).first()
        if not exists:
            self.db.execute(
                insert(a).values(
                    id=str(uuid.uuid4()),
                    org_id=org_id,
                    policy_id=policy_id,
                    version=row["published_version"],
                    user_id=user_id,
                    acknowledged_at=_now(),
                )
            )
            self.db.commit()
        return self.get(org_id, policy_id, user_id)

    # -- enforcement --------------------------------------------------------

    def system_facts(self, org_id: str, system: dict) -> dict:
        system_id = system["id"]
        ar = GovernanceApprovalRequest.__table__.c
        approval = self.db.execute(
            select(ar.status)
            .where(ar.entity_type == "ai_system", ar.entity_id == system_id)
            .order_by(ar.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        r = GovernanceRisk.__table__.c
        open_risks = [
            s
            for s, status in self.db.execute(select(r.severity, r.status).where(r.system_id == system_id))
            if (status or "").lower() not in _CLOSED
        ]
        rt = GovernanceRemediationTask.__table__.c
        open_tasks = sum(
            1 for (status,) in self.db.execute(select(rt.status).where(rt.system_id == system_id)) if (status or "").lower() not in _CLOSED
        )
        ev = GovernanceEvidenceRun.__table__.c
        runs = list(
            self.db.execute(
                select(ev.result, ev.source_type, ev.expires_at).where(ev.org_id == org_id, ev.system_id == system_id)
            ).mappings()
        )
        now = _now()
        fa, fv = GovernanceFrameworkAssignment.__table__.c, GovernanceFrameworkVersion.__table__.c
        assignments = list(
            self.db.execute(
                select(fa.id, fv.framework_key)
                .join(GovernanceFrameworkVersion.__table__, fv.id == fa.framework_version_id)
                .where(fa.org_id == org_id, fa.system_id == system_id)
            ).mappings()
        )
        totals = {"applicable": 0, "accepted": 0, "missingEvidence": 0, "staleEvidence": 0, "blockingFindings": 0}
        assurance = GovernanceAssuranceService(self.db)
        for assignment in assignments:
            counts = assurance.readiness(org_id, assignment["id"], include_policy=False) or {}
            for key in totals:
                totals[key] += counts.get(key, 0)
        try:
            metadata = json.loads(system.get("metadata_json") or "{}")
        except ValueError:
            metadata = {}
        return {
            "system.risk_tier": system.get("risk_tier"),
            "system.lifecycle_stage": system.get("lifecycle_stage"),
            "system.status": system.get("status"),
            "system.owner": system.get("owner"),
            "system.system_type": system.get("system_type"),
            "system.metadata": metadata if isinstance(metadata, dict) else {},
            "approval.status": approval or "none",
            "risks.open": len(open_risks),
            "risks.open_high": sum(1 for s in open_risks if s == "high"),
            "risks.open_critical": sum(1 for s in open_risks if s == "critical"),
            "remediation.open": open_tasks,
            "evidence.total": len(runs),
            "evidence.passed": sum(1 for x in runs if x["result"] == "passed"),
            "evidence.failed": sum(1 for x in runs if x["result"] == "failed"),
            "evidence.expired": sum(1 for x in runs if x["expires_at"] and x["expires_at"] < now),
            "evidence.sources_passed": sorted({x["source_type"] for x in runs if x["result"] == "passed"}),
            "frameworks.assigned": sorted({a["framework_key"] for a in assignments}),
            "controls.applicable": totals["applicable"],
            "controls.accepted": totals["accepted"],
            "controls.accepted_ratio": round(totals["accepted"] / totals["applicable"], 4) if totals["applicable"] else 0.0,
            "controls.missing_evidence": totals["missingEvidence"],
            "controls.stale_evidence": totals["staleEvidence"],
            "controls.blocking_findings": totals["blockingFindings"],
        }

    def _enforced(self, org_id: str, policy_id: str | None) -> list[dict]:
        p, v = OrgPolicy.__table__, OrgPolicyVersion.__table__
        query = (
            select(p.c.id, p.c.name, v.c.version, v.c.rules_json)
            .join(v, (v.c.policy_id == p.c.id) & (v.c.version == p.c.published_version))
            .where(p.c.org_id == org_id, p.c.status != "retired")
        )
        if policy_id:
            query = query.where(p.c.id == policy_id)
        return [dict(r) for r in self.db.execute(query).mappings()]

    def _evaluate(
        self, org_id: str, policy_id: str | None = None, system_id: str | None = None, assume: dict | None = None
    ) -> tuple[list[dict], list[dict], list[dict]] | None:
        """Evaluate published policies against the org's systems now, recording nothing.

        ``assume`` overrides facts, so a release check can ask "would this pass once approved?".
        """
        s = GovernanceAISystem.__table__
        query = select(s).where(s.c.org_id == org_id)
        if system_id:
            query = query.where(s.c.id == system_id)
        systems = [dict(r) for r in self.db.execute(query).mappings()]
        if system_id and not systems:
            return None
        policies = self._enforced(org_id, policy_id)
        results = []
        for system in systems if policies else []:
            facts = {**self.system_facts(org_id, system), **(assume or {})}
            for policy in policies:
                for rule in json.loads(policy["rules_json"]):
                    outcome, detail = evaluate_rule(rule, facts)
                    results.append(
                        {
                            "policyId": policy["id"],
                            "policyName": policy["name"],
                            "policyVersion": policy["version"],
                            "systemId": system["id"],
                            "systemName": system["name"],
                            "ruleId": rule["id"],
                            "ruleTitle": rule["title"],
                            "severity": rule["severity"],
                            "enforcement": rule["enforcement"],
                            "controls": rule.get("controls", []),
                            "outcome": outcome,
                            "detail": detail,
                        }
                    )
        return systems, policies, results

    def current_results(self, org_id: str, policy_id: str | None = None, system_id: str | None = None) -> list[dict]:
        """Each published rule's outcome on each system (or one system) as the data stands now."""
        # ponytail: re-evaluates every system per read; cache by data version if orgs reach hundreds of systems.
        evaluated = self._evaluate(org_id, policy_id, system_id)
        now = _now()
        return [{**r, "evaluatedAt": now} for r in evaluated[2]] if evaluated else []

    def release_check(self, org_id: str, system_id: str) -> dict | None:
        """Published rules that fail for a system once its release is approved: blocking and warnings."""
        evaluated = self._evaluate(org_id, system_id=system_id, assume={"approval.status": "approved"})
        if evaluated is None:
            return None
        failed = [r for r in evaluated[2] if r["outcome"] == "fail"]
        return {
            "blocking": [r for r in failed if r["enforcement"] == "block"],
            "warnings": [r for r in failed if r["enforcement"] == "warn"],
        }

    def enforce(self, org_id: str, policy_id: str | None = None, system_id: str | None = None) -> dict | None:
        """Evaluate published policies against the org's systems and record each result."""
        evaluated = self._evaluate(org_id, policy_id, system_id)
        if evaluated is None:
            return None
        systems, policies, results = evaluated
        run_id, now = str(uuid.uuid4()), _now()
        if results:
            self.db.execute(
                insert(OrgPolicyEvaluation.__table__),
                [
                    {
                        "id": str(uuid.uuid4()),
                        "org_id": org_id,
                        "run_id": run_id,
                        "policy_id": r["policyId"],
                        "policy_version": r["policyVersion"],
                        "system_id": r["systemId"],
                        "rule_id": r["ruleId"],
                        "outcome": r["outcome"],
                        "severity": r["severity"],
                        "enforcement": r["enforcement"],
                        "detail": r["detail"],
                        "evaluated_at": now,
                    }
                    for r in results
                ],
            )
            self.db.commit()
        failed = [r for r in results if r["outcome"] == "fail"]
        return {
            "runId": run_id,
            "evaluatedAt": now,
            "systems": len(systems),
            "policies": len(policies),
            "passed": sum(1 for r in results if r["outcome"] == "pass"),
            "failed": len(failed),
            "notApplicable": sum(1 for r in results if r["outcome"] == "not_applicable"),
            "blocking": sum(1 for r in failed if r["enforcement"] == "block"),
            "results": results,
        }

    def gate(self, org_id: str, system_id: str) -> dict | None:
        """Evaluate one system now; it may proceed only if no blocking rule fails."""
        run = self.enforce(org_id, system_id=system_id)
        if run is None:
            return None
        failed = [r for r in run["results"] if r["outcome"] == "fail"]
        return {
            "systemId": system_id,
            "allowed": not any(r["enforcement"] == "block" for r in failed),
            "blocking": [r for r in failed if r["enforcement"] == "block"],
            "warnings": [r for r in failed if r["enforcement"] == "warn"],
            "runId": run["runId"],
            "evaluatedAt": run["evaluatedAt"],
        }

    # -- alerts ---------------------------------------------------------------

    def enforcing_orgs(self) -> list[str]:
        """Organizations with at least one published policy."""
        p = OrgPolicy.__table__
        return list(
            self.db.execute(
                select(p.c.org_id).where(p.c.published_version.is_not(None), p.c.status != "retired").distinct()
            ).scalars()
        )

    def sync_alerts(self, org_id: str) -> int:
        """Open an alert for each published rule newly failing on a system, resolve those no longer failing.

        Returns how many alerts were opened.
        """
        a = OrgPolicyAlert.__table__
        failing = {
            (r["policyId"], r["ruleId"], r["systemId"]): r for r in self.current_results(org_id) if r["outcome"] == "fail"
        }
        now, still_open = _now(), set()
        for row in self.db.execute(select(a).where(a.c.org_id == org_id, a.c.status == "open")).mappings():
            key = (row["policy_id"], row["rule_id"], row["system_id"])
            if key in failing:
                still_open.add(key)
            else:
                self.db.execute(
                    update(a).where(a.c.id == row["id"], a.c.status == "open").values(status="resolved", resolved_at=now)
                )
        opened = 0
        for key, r in failing.items():
            if key in still_open:
                continue
            result = self.db.execute(
                pg_insert(a)
                .values(
                    id=str(uuid.uuid4()),
                    org_id=org_id,
                    policy_id=r["policyId"],
                    policy_version=r["policyVersion"],
                    system_id=r["systemId"],
                    rule_id=r["ruleId"],
                    severity=r["severity"],
                    enforcement=r["enforcement"],
                    detail=r["detail"],
                    status="open",
                    opened_at=now,
                )
                .on_conflict_do_nothing()  # another sweep opened it first
            )
            opened += result.rowcount or 0
        self.db.commit()
        return opened

    def alerts(self, org_id: str, include_resolved: bool = False) -> list[dict]:
        a, p, s = OrgPolicyAlert.__table__, OrgPolicy.__table__, GovernanceAISystem.__table__
        query = (
            select(a, p.c.name.label("policy_name"), p.c.rules_json, s.c.name.label("system_name"))
            .join(p, p.c.id == a.c.policy_id)
            .outerjoin(s, s.c.id == a.c.system_id)
            .where(a.c.org_id == org_id)
            .order_by(a.c.opened_at.desc())
        )
        if not include_resolved:
            query = query.where(a.c.status == "open")
        out = []
        for r in self.db.execute(query).mappings():
            titles = {rule["id"]: rule["title"] for rule in json.loads(r["rules_json"] or "[]")}
            out.append(
                {
                    "id": r["id"],
                    "policyId": r["policy_id"],
                    "policyName": r["policy_name"],
                    "policyVersion": r["policy_version"],
                    "systemId": r["system_id"],
                    "systemName": r["system_name"] or r["system_id"],
                    "ruleId": r["rule_id"],
                    "ruleTitle": titles.get(r["rule_id"], r["rule_id"]),
                    "severity": r["severity"],
                    "enforcement": r["enforcement"],
                    "detail": r["detail"],
                    "status": r["status"],
                    "openedAt": r["opened_at"],
                    "resolvedAt": r["resolved_at"],
                    "notifiedAt": r["notified_at"],
                    "acknowledgedBy": r["acknowledged_by"],
                    "acknowledgedAt": r["acknowledged_at"],
                }
            )
        return out

    def acknowledge_alert(self, org_id: str, alert_id: str, user_id: str) -> dict | None:
        a = OrgPolicyAlert.__table__
        self.db.execute(
            update(a)
            .where(a.c.id == alert_id, a.c.org_id == org_id, a.c.acknowledged_at.is_(None))
            .values(acknowledged_by=str(user_id), acknowledged_at=_now())
        )
        self.db.commit()
        return next((x for x in self.alerts(org_id, include_resolved=True) if x["id"] == alert_id), None)

    def _recipient(self, org_id: str, policy: dict) -> str | None:
        """The policy owner when it is an email address, otherwise the member who created the policy."""
        owner = (policy.get("owner") or "").strip()
        if _EMAIL.fullmatch(owner):
            return owner
        creator = _same_id(policy.get("created_by"))
        for member in self.acknowledgements(org_id, policy["id"]) or []:
            if _same_id(member["userId"]) == creator and _EMAIL.fullmatch(member["email"] or ""):
                return member["email"]
        return None

    def unnotified_alerts(self) -> list[dict]:
        """Open alerts nobody has been told about yet, each with the address to tell."""
        a, p = OrgPolicyAlert.__table__, OrgPolicy.__table__
        org_ids = self.db.execute(
            select(a.c.org_id).where(a.c.status == "open", a.c.notified_at.is_(None)).distinct()
        ).scalars()
        pending = []
        for org_id in list(org_ids):
            policies = {
                r["id"]: dict(r)
                for r in self.db.execute(
                    select(p.c.id, p.c.owner, p.c.created_by).where(p.c.org_id == org_id)
                ).mappings()
            }
            for alert in self.alerts(org_id):
                if alert["notifiedAt"] is None and alert["policyId"] in policies:
                    pending.append({**alert, "recipient": self._recipient(org_id, policies[alert["policyId"]])})
        return pending

    def mark_notified(self, alert_id: str) -> None:
        a = OrgPolicyAlert.__table__
        self.db.execute(update(a).where(a.c.id == alert_id).values(notified_at=_now()))
        self.db.commit()


_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def alert_email(alert: dict, frontend_url: str) -> tuple[str, str]:
    """Subject and HTML for a newly failing rule. Every value from the database is escaped."""
    e = lambda value: html.escape(str(value))  # noqa: E731
    action = "It blocks release approval for this system." if alert["enforcement"] == "block" else "It is a warning."
    subject = f"Policy rule failing on {alert['systemName']}: {alert['ruleTitle']}"
    body = (
        f"<p>A published rule of <b>{e(alert['policyName'])}</b> (version {e(alert['policyVersion'])}) "
        f"started failing on <b>{e(alert['systemName'])}</b>.</p>"
        f"<p><b>{e(alert['ruleTitle'])}</b><br>{e(alert['detail'])}</p>"
        f"<p>{e(action)}</p>"
        f'<p><a href="{e(frontend_url.rstrip("/"))}/policies/{e(alert["policyId"])}">Open the policy</a></p>'
    )
    return subject, body


async def sweep_policy_alerts(
    session_factory: Callable[[], Session],
    send_email: Callable[[str, str, str], Awaitable[bool]],
    frontend_url: str,
) -> int:
    """Raise alerts for newly failing rules in every enforcing organization and email each new one once."""

    def collect() -> list[dict]:
        db = session_factory()
        try:
            service = PolicyService(db)
            for org_id in service.enforcing_orgs():
                service.sync_alerts(org_id)
            return service.unnotified_alerts()
        finally:
            db.close()

    pending = await asyncio.to_thread(collect)
    sent = 0
    for alert in pending:
        if alert["recipient"]:
            if not await send_email(alert["recipient"], *alert_email(alert, frontend_url)):
                continue  # try again on the next sweep
            sent += 1
        db = session_factory()
        try:
            PolicyService(db).mark_notified(alert["id"])
        finally:
            db.close()
    return sent
