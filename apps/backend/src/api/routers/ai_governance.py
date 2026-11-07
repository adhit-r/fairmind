"""
AI Governance endpoints (Phase 1 MVP)

Provides practical governance primitives:
- Policy management
- Approval workflows and requests
- Evidence collection and linking
- Basic framework/controls discovery for UI contracts
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from config.auth import TokenData, UserRole, get_current_active_user, require_admin
from config.settings import settings

logger = logging.getLogger(__name__)
from database.connection import get_db
from database.models import OrganizationMember
from src.application.services.governance_assurance_service import (
    GovernanceAssuranceService,
    OrgMembership,
    member_user_matches,
)


def _caller_org(request: Request) -> str:
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        raise HTTPException(status_code=403, detail="Your account is not assigned to an organization")
    return org_id


def _resolve_caller_org(request: Request, db: Session) -> None:
    """Fill request.state.org_id when the token carried no org claim.

    An explicit ?org_id= wins when the caller is an active member of it;
    otherwise the caller's first active membership is used. Tokens with an
    org claim are already resolved by OrgIsolationMiddleware.
    """
    if getattr(request.state, "org_id", None):
        return
    user_id = getattr(getattr(request.state, "user", None), "user_id", None)
    try:
        user_uuid = uuid.UUID(str(user_id))
    except (TypeError, ValueError):
        return
    requested = request.query_params.get("org_id")
    if requested:
        if GovernanceAssuranceService(db).membership(requested, str(user_id)):
            request.state.org_id = requested
        return
    members = OrganizationMember.__table__.c
    org = db.execute(
        select(members.org_id)
        .where(member_user_matches(members.user_id, user_uuid), members.status == "active")
        .order_by(members.created_at)
        .limit(1)
    ).scalar_one_or_none()
    if org:
        request.state.org_id = str(org)


_SCOPED_IDS = {
    "system_id": "governance_ai_systems",
    "systemId": "governance_ai_systems",
    "workspace_id": "governance_workspaces",
    "workspaceId": "governance_workspaces",
}


async def _enforce_org_scope(request: Request, db: Session = Depends(get_db)) -> None:
    """Every system or workspace id a request names must belong to the caller's org.

    Checked once here for path, query and JSON body ids, so individual routes
    cannot forget it. A foreign id answers 404, never 403, to avoid confirming
    that it exists.
    """
    _resolve_caller_org(request, db)
    org_id = _caller_org(request)
    sources = [request.path_params, request.query_params]
    if request.method in ("POST", "PUT", "PATCH") and "json" in request.headers.get("content-type", ""):
        try:
            body = await request.json()
        except ValueError:
            body = None
        if isinstance(body, dict):
            sources.append(body)
    for source in sources:
        for key, table in _SCOPED_IDS.items():
            value = source.get(key)
            if not value:
                continue
            _ensure_tables(db)
            row = db.execute(
                text(f"SELECT org_id FROM {table} WHERE id = :id"), {"id": str(value)}
            ).fetchone()
            # Unknown ids pass through here; routes that store or read records
            # under a system id resolve it with _require_system_access.
            # A registered id must belong to the caller's org.
            if row is not None and str(row[0] or "") != str(org_id):
                raise HTTPException(status_code=404, detail="Not found")


def _membership(request, current_user: TokenData, db: Session) -> OrgMembership:
    org_id = _caller_org(request)
    membership = GovernanceAssuranceService(db).membership(org_id, current_user.user_id)
    if not membership and settings.is_development and current_user.org_id and str(current_user.org_id) == org_id:
        # Same local-development allowance as _require_system_access.
        membership = OrgMembership(
            org_id, current_user.user_id, current_user.role.value, tuple(current_user.permissions)
        )
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this organization")
    return membership


async def org_member(
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> OrgMembership:
    """The caller's active membership in their organisation, else 403."""
    # Some prefixes skip the auth middleware in local development, so the
    # identity is taken from the bearer token here rather than from request state.
    if getattr(request.state, "user", None) is None:
        request.state.user = current_user
    if not getattr(request.state, "org_id", None) and current_user.org_id:
        request.state.org_id = str(current_user.org_id)
    await _enforce_org_scope(request, db)
    return _membership(request, current_user, db)


async def org_mutator(membership: OrgMembership = Depends(org_member)) -> OrgMembership:
    """``org_member`` plus the organisation's mutation permission."""
    if not GovernanceAssuranceService.may_mutate(membership):
        raise HTTPException(status_code=403, detail="Organization mutation permission required")
    return membership


# Records addressed by their own ids are scoped by their route: through the
# system they belong to (approval requests, evidence items, remediation tasks,
# reports). Approval workflows and framework controls are a platform catalogue
# that only platform admins write.
router = APIRouter(tags=["ai-governance"], dependencies=[Depends(_enforce_org_scope)])

SYSTEM_APPROVAL_WORKFLOW_ID = "fairmind-system-release-v1"
SYSTEM_APPROVAL_WORKFLOW_STEPS = [
    {"order": 1, "role": "organization_mutator", "permission": "model:write"}
]

UNTRUSTED_EXTERNAL_EVIDENCE_LINKING_DISABLED_DETAIL = {
    "code": "untrusted_external_evidence_linking_disabled",
    "message": "Untrusted external evidence linking is disabled.",
    "nextAction": (
        "Remove the external URL or direct entity link, or use the Assurance V2 "
        "evidence-admission workflow."
    ),
}


def _require_untrusted_external_evidence_linking_enabled() -> None:
    if not settings.untrusted_external_evidence_linking_enabled:
        raise HTTPException(
            status_code=409,
            detail=UNTRUSTED_EXTERNAL_EVIDENCE_LINKING_DISABLED_DETAIL,
        )


def _has_nonblank_external_url(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _requests_external_url_artifact(
    *,
    artifact_kind: Any,
    file_url: Any,
    content: Dict[str, Any],
) -> bool:
    return _has_nonblank_external_url(file_url) or (
        artifact_kind == "url"
        and _has_nonblank_external_url(content.get("url"))
    )


FRAMEWORKS: List[Dict[str, Any]] = [
    {
        "id": "eu_ai_act",
        "name": "EU AI Act",
        "description": "European Union AI regulation",
        "controls": ["risk_management", "transparency", "human_oversight", "incident_reporting"],
    },
    {
        "id": "iso_42001",
        "name": "ISO/IEC 42001",
        "description": "AI management system standard",
        "controls": ["governance", "policy", "monitoring", "continuous_improvement"],
    },
    {
        "id": "nist_ai_rmf",
        "name": "NIST AI RMF",
        "description": "NIST AI Risk Management Framework",
        "controls": ["govern", "map", "measure", "manage"],
    },
]

def _resolve_risk_library_files() -> List[tuple[str, Path]]:
    """
    Resolve risk library paths robustly across local/dev and container layouts.
    """
    current = Path(__file__).resolve()
    for parent in current.parents:
        risks_dir = parent / "risks"
        mit_path = risks_dir / "MITAIRISKDB.json"
        ibm_path = risks_dir / "IBMAIRISKDB.json"
        if mit_path.exists() and ibm_path.exists():
            return [("mit", mit_path), ("ibm", ibm_path)]

    # Fallback to expected app-root layout in deployments.
    return [
        ("mit", Path("/app/risks/MITAIRISKDB.json")),
        ("ibm", Path("/app/risks/IBMAIRISKDB.json")),
    ]


RISK_LIBRARY_FILES = _resolve_risk_library_files()

RISK_SEVERITY_MAP = {
    "minor": "low",
    "moderate": "medium",
    "major": "high",
    "critical": "critical",
}

RISK_LIKELIHOOD_WEIGHT = {
    "rare": 0.1,
    "unlikely": 0.2,
    "possible": 0.4,
    "likely": 0.7,
    "almost certain": 0.9,
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_severity(value: Optional[str]) -> str:
    if not value:
        return "medium"
    normalized = value.strip().lower()
    return RISK_SEVERITY_MAP.get(normalized, normalized if normalized in {"low", "medium", "high", "critical"} else "medium")


def _normalize_likelihood(value: Optional[str]) -> str:
    if not value:
        return "possible"
    normalized = value.strip().lower()
    return normalized if normalized in RISK_LIKELIHOOD_WEIGHT else "possible"


def _severity_rank(severity: str) -> int:
    return {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }.get(severity, 2)


def _risk_score(severity: str, likelihood: str) -> float:
    return round((_severity_rank(severity) / 4.0) * RISK_LIKELIHOOD_WEIGHT.get(likelihood, 0.4), 2)


def _load_risk_library() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for source, file_path in RISK_LIBRARY_FILES:
        if not file_path.exists():
            continue
        with file_path.open("r", encoding="utf-8") as handle:
            raw_items = json.load(handle)
        for entry in raw_items:
            severity = _normalize_severity(entry.get("Risk Severity"))
            likelihood = _normalize_likelihood(entry.get("Likelihood"))
            categories = [
                value.strip()
                for value in (entry.get("Risk Category") or "").split(";")
                if value.strip()
            ]
            items.append(
                {
                    "library_id": f"{source}-{entry.get('Id')}",
                    "source": source,
                    "title": entry.get("Summary") or "Untitled risk",
                    "description": entry.get("Description") or "",
                    "severity": severity,
                    "likelihood": likelihood,
                    "risk_categories": categories,
                    "risk_score": _risk_score(severity, likelihood),
                }
            )
    return items


def _generate_automated_risks(system_id: str, risk_type: Optional[str] = None) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    type_filter = (risk_type or "").strip().lower()
    for item in _load_risk_library():
        haystack = " ".join(
            [
                item["title"],
                item["description"],
                " ".join(item["risk_categories"]),
                item["source"],
            ]
        ).lower()
        if type_filter and type_filter not in haystack:
            continue
        selected.append(
            {
                "id": str(uuid.uuid4()),
                "systemId": system_id,
                "title": item["title"],
                "severity": item["severity"],
                "status": "open",
                "description": item["description"],
                "mitigation": (
                    f"Review {item['source'].upper()} library guidance, assign an owner, "
                    "collect evidence, and define monitoring plus release-gate checks."
                ),
                "likelihood": item["likelihood"],
                "risk_score": item["risk_score"],
                "source": item["source"],
                "categories": item["risk_categories"],
                "is_automated": True,
                "timestamp": _utc_now_iso(),
            }
        )
        if len(selected) >= 8:
            break
    return sorted(selected, key=lambda item: (_severity_rank(item["severity"]), item["risk_score"]), reverse=True)


_tables_ready = False


def _ensure_tables(db: Session) -> None:
    """Ensure governance tables exist via ORM metadata (runs once)."""
    global _tables_ready
    if _tables_ready:
        return
    # Import models so Base.metadata is populated, then create all.
    import database.governance_models  # noqa: F401
    from database.connection import Base, db_manager

    db_manager.create_tables()  # every registry, table by table; see connection.create_tables
    _ensure_model_link_column(db)
    _tables_ready = True


def _authenticated_actor(current_user: TokenData) -> str:
    return current_user.email.strip() if current_user.email else current_user.user_id


def _require_platform_workflow_admin(current_user: TokenData) -> None:
    """Global workflow definitions are trusted platform configuration."""
    if (
        current_user.role != UserRole.ADMIN
        and "*" not in current_user.permissions
        and "governance:workflow:manage" not in current_user.permissions
    ):
        raise HTTPException(status_code=403, detail="Platform workflow permission required")


def _ensure_system_approval_workflow(db: Session, now: str) -> str:
    """Restore the immutable catalog workflow before assigning it to a system."""
    steps_json = json.dumps(SYSTEM_APPROVAL_WORKFLOW_STEPS)
    result = db.execute(
        text(
            "UPDATE governance_approval_workflows "
            "SET name = :name, entity_type = 'ai_system', steps_json = :steps_json, "
            "is_active = TRUE, updated_at = :updated_at WHERE id = :id"
        ),
        {
            "id": SYSTEM_APPROVAL_WORKFLOW_ID,
            "name": "AI System Release Approval",
            "steps_json": steps_json,
            "updated_at": now,
        },
    )
    if result.rowcount == 0:
        db.execute(
            text(
                "INSERT INTO governance_approval_workflows "
                "(id, name, entity_type, steps_json, is_active, created_by, created_at, updated_at) "
                "VALUES (:id, :name, 'ai_system', :steps_json, TRUE, :created_by, :created_at, :updated_at)"
            ),
            {
                "id": SYSTEM_APPROVAL_WORKFLOW_ID,
                "name": "AI System Release Approval",
                "steps_json": steps_json,
                "created_by": "fairmind-catalog",
                "created_at": now,
                "updated_at": now,
            },
        )
    return SYSTEM_APPROVAL_WORKFLOW_ID


def _require_system_access(
    db: Session,
    system_id: str,
    current_user: TokenData,
    *,
    mutate: bool = False,
) -> OrgMembership:
    """Resolve a system's tenant and fail closed for missing or legacy unscoped rows."""
    row = db.execute(
        text("SELECT org_id FROM governance_ai_systems WHERE id = :id"),
        {"id": system_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="AI system not found")
    service = GovernanceAssuranceService(db)
    membership = service.membership(str(row[0]), current_user.user_id)
    if not membership and settings.is_development and current_user.org_id and str(current_user.org_id) == str(row[0]):
        # Local development only: accounts signed in without an org_members row
        # (the e2e admin, see config.auth) carry the org in their token. Trust
        # that claim here and in _membership, never outside development.
        membership = OrgMembership(str(row[0]), current_user.user_id, current_user.role.value, tuple(current_user.permissions))
    if not membership:
        raise HTTPException(status_code=404, detail="AI system not found")
    if mutate and not service.may_mutate(membership):
        raise HTTPException(status_code=403, detail="Organization mutation permission required")
    return membership


def _require_approval_request_access(
    db: Session,
    request_id: str,
    current_user: TokenData,
    *,
    mutate: bool = False,
) -> str:
    row = db.execute(
        text(
            "SELECT entity_type, entity_id, ai_system_id "
            "FROM governance_approval_requests WHERE id = :id"
        ),
        {"id": request_id},
    ).fetchone()
    if not row or row[0] != "ai_system":
        raise HTTPException(status_code=404, detail="Approval request not found")
    entity_system_id = str(row[1]) if row[1] else ""
    linked_system_id = str(row[2]) if row[2] else ""
    if linked_system_id and entity_system_id and linked_system_id != entity_system_id:
        raise HTTPException(status_code=404, detail="Approval request not found")
    system_id = linked_system_id or entity_system_id
    if not system_id:
        raise HTTPException(status_code=404, detail="Approval request not found")
    _require_system_access(db, system_id, current_user, mutate=mutate)
    return system_id


def _require_report_access(
    db: Session,
    report_id: str,
    current_user: TokenData,
) -> Any:
    row = db.execute(
        text(
            "SELECT id, system_id, report_type, title, generated_by, config_json, data_json, created_at "
            "FROM governance_audit_reports WHERE id = :id"
        ),
        {"id": report_id},
    ).fetchone()
    if not row or not row.system_id:
        raise HTTPException(status_code=404, detail="Report not found")
    _require_system_access(db, str(row.system_id), current_user)
    return row
# Columns added after the tables first shipped. create_all() does not alter
# existing tables, so this runtime patch keeps already-provisioned dev and test
# databases usable without running the org-scoping migration by hand.
_LATE_COLUMNS = (
    ("governance_ai_systems", "org_id"),
    ("governance_workspaces", "org_id"),
    ("governance_policies", "org_id"),  # also migrations/015_org_scope_legacy_tables.sql
)


def _ensure_model_link_column(db: Session) -> None:
    """Add late columns to databases created before them; the rest is for migrations."""
    try:
        for table, column in _LATE_COLUMNS:
            db.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} VARCHAR(255)"))
            db.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table}_{column} ON {table} ({column})"))
        db.commit()
    except Exception:  # pragma: no cover - never block startup on a patch attempt
        db.rollback()


class ApprovalWorkflowCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    steps: List[Dict[str, Any]] = Field(default_factory=list)


class ApprovalRequestCreateRequest(BaseModel):
    entity_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    requested_by: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    notes: str = ""
    decided_by: Optional[str] = None


class SystemApprovalRequestCreateRequest(BaseModel):
    requested_by: Optional[str] = None


# The release gate trusts these metadata keys; only the server routes that measure something stamp them.
GATE_PROVENANCE_KEYS = ("provenance_class", "provenance")


class EvidenceCollectRequest(BaseModel):
    system_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    content: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceLinkRequest(BaseModel):
    evidence_id: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)


class RiskAssessmentRequest(BaseModel):
    systemId: str = Field(min_length=1)
    riskType: str = Field(min_length=1)
    severity: str = Field(pattern="^(low|medium|high|critical)$")
    description: str = Field(min_length=1)


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    owner: Optional[str] = None


class AISystemCreateRequest(BaseModel):
    workspace_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    owner: Optional[str] = None
    risk_tier: str = Field(pattern="^(low|medium|high|critical)$")
    lifecycle_stage: str = Field(pattern="^(onboard|assess|govern|remediate|operate)$")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RemediationCreateRequest(BaseModel):
    system_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    linked_risk_ids: List[str] = Field(default_factory=list)
    owner: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    due_date: Optional[str] = None
    retest_required: bool = True
    notes: str = ""


class RemediationUpdateRequest(BaseModel):
    status: Optional[str] = Field(
        default=None,
        pattern="^(open|in_progress|blocked|ready_for_retest|resolved|closed)$",
    )
    notes: Optional[str] = None


def _load_json_value(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default
    return parsed if isinstance(parsed, type(default)) else default


def _serialize_risk_row(row: Any) -> Dict[str, Any]:
    return {
        "id": row[0],
        "systemId": row[1],
        "title": row[2],
        "severity": row[3],
        "status": row[4],
        "description": row[5],
        "mitigation": row[6],
        "likelihood": row[7],
        "riskScore": float(row[8]),
        "source": row[9],
        "categories": json.loads(row[10]),
        "metadata": json.loads(row[11]),
        "timestamp": row[12],
        "updatedAt": row[13],
    }


def _evidence_metadata_summary(
    metadata: Dict[str, Any],
    content: Any,
    link_count: int,
    confidence: float,
) -> Dict[str, Any]:
    tags = metadata.get("tags") if isinstance(metadata.get("tags"), list) else []
    source = metadata.get("source") or metadata.get("origin") or metadata.get("collected_from") or "unknown"
    artifact_type = (
        metadata.get("artifact_type")
        or metadata.get("artifactType")
        or metadata.get("kind")
        or metadata.get("evidence_type")
        or "unknown"
    )
    if confidence >= 0.9:
        confidence_band = "high"
    elif confidence >= 0.7:
        confidence_band = "medium"
    else:
        confidence_band = "low"
    return {
        "source": source,
        "artifactType": artifact_type,
        "tags": tags[:5],
        "linkedEntityCount": link_count,
        "hasContent": bool(content),
        "confidenceBand": confidence_band,
    }


def _serialize_evidence_row(row: Any, linked_entities: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    content = _load_json_value(row[3], {})
    metadata = _load_json_value(row[5], {})
    confidence = float(row[4])
    linked_entities = linked_entities or []
    return {
        "id": row[0],
        "systemId": row[1],
        "type": row[2],
        "content": content,
        "confidence": confidence,
        "metadata": metadata,
        "timestamp": row[6],
        "linkedEntityCount": len(linked_entities),
        "linkedEntities": linked_entities,
        "metadataSummary": _evidence_metadata_summary(metadata, content, len(linked_entities), confidence),
        "workflowState": "linked" if linked_entities else "collected",
    }


def _serialize_remediation_task_row(row: Any) -> Dict[str, Any]:
    return {
        "id": row[0],
        "systemId": row[1],
        "title": row[2],
        "description": row[3],
        "sourceType": row[4],
        "sourceId": row[5],
        "linkedRiskIds": _load_json_value(row[6], []),
        "owner": row[7] or None,
        "priority": row[8],
        "dueDate": row[9] or None,
        "status": row[10],
        "retestRequired": bool(row[11]),
        "retestStatus": row[12],
        "notes": row[13] or "",
        "createdAt": row[14],
        "updatedAt": row[15],
    }


ACTIVE_REMEDIATION_STATUSES = ("open", "in_progress", "blocked", "ready_for_retest")
CLOSED_RISK_STATUSES = ("accepted", "closed", "resolved", "mitigated")


def _summarize_remediation_tasks(tasks: List[Dict[str, Any]], system_id: str) -> Dict[str, Any]:
    status_counts = {
        "open": 0,
        "in_progress": 0,
        "blocked": 0,
        "ready_for_retest": 0,
        "resolved": 0,
        "closed": 0,
    }
    priority_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    retest_required = 0
    linked_risk_refs = 0

    for task in tasks:
        status = task.get("status") or "open"
        if status in status_counts:
            status_counts[status] += 1
        priority = task.get("priority") or "medium"
        if priority in priority_counts:
            priority_counts[priority] += 1
        if task.get("retestRequired"):
            retest_required += 1
        linked_risk_refs += len(task.get("linkedRiskIds") or [])

    active = sum(status_counts[key] for key in ACTIVE_REMEDIATION_STATUSES)
    completed = status_counts["resolved"] + status_counts["closed"]

    return {
        "systemId": system_id,
        "totalTasks": len(tasks),
        "activeTasks": active,
        "completedTasks": completed,
        "retestRequiredTasks": retest_required,
        "linkedRiskRefs": linked_risk_refs,
        "byStatus": status_counts,
        "byPriority": priority_counts,
    }


def _serialize_approval_request_row(row: Any) -> Dict[str, Any]:
    return {
        "id": row[0],
        "workflow_id": row[1],
        "entity_type": row[2],
        "entity_id": row[3],
        "requested_by": row[4],
        "status": row[5],
        "current_step": row[6],
        "decision_notes": row[7] or "",
        "createdAt": row[8],
        "updatedAt": row[9],
    }


def _serialize_workspace_row(row: Any) -> Dict[str, Any]:
    return {
        "id": row[0],
        "name": row[1],
        "owner": row[2],
        "createdAt": row[3],
        "updatedAt": row[4],
    }


def _serialize_ai_system_row(row: Any) -> Dict[str, Any]:
    metadata = _load_json_value(row[6], {})
    return {
        "id": row[0],
        "workspaceId": row[1],
        "name": row[2],
        "owner": row[3],
        "riskTier": row[4],
        "lifecycleStage": row[5],
        "metadata": metadata,
        # The confirmed tier and frameworks (routers/applicability.py); None until a person confirms them.
        "applicability": metadata.get("applicability"),
        "createdAt": row[7],
        "updatedAt": row[8],
    }


def _fetch_latest_system_approval(db: Session, system_id: str) -> Optional[Dict[str, Any]]:
    row = db.execute(
        text(
            "SELECT id, workflow_id, entity_type, entity_id, requested_by, status, current_step, decision_notes, created_at, updated_at "
            "FROM governance_approval_requests WHERE entity_type = :entity_type AND entity_id = :entity_id "
            "ORDER BY created_at DESC LIMIT 1"
        ),
        {"entity_type": "ai_system", "entity_id": system_id},
    ).fetchone()
    return _serialize_approval_request_row(row) if row else None


def _fetch_remediation_tasks(db: Session, system_id: str) -> List[Dict[str, Any]]:
    rows = db.execute(
        text(
            "SELECT id, system_id, title, description, source_type, source_id, linked_risk_ids_json, "
            "owner, priority, due_date, status, retest_required, retest_status, notes, created_at, updated_at "
            "FROM governance_remediation_tasks WHERE system_id = :system_id "
            "ORDER BY created_at DESC"
        ),
        {"system_id": system_id},
    ).fetchall()
    return [_serialize_remediation_task_row(row) for row in rows]


def _risk_dashboard(rows: List[Any], system_id: Optional[str]) -> Dict[str, Any]:
    """Recorded findings, counted; taxonomy suggestions listed apart and never counted.

    A suggestion is a MIT or IBM library entry that might apply, not a finding
    about the system, so it is offered for one system only and dropped once a
    recorded risk carries its title.
    """
    risks = sorted(
        (_serialize_risk_row(row) for row in rows),
        key=lambda item: (_severity_rank(item["severity"]), item.get("riskScore", 0.0)),
        reverse=True,
    )
    recorded_titles = {risk["title"].strip().lower() for risk in risks}
    suggested = (
        [s for s in _generate_automated_risks(system_id) if s["title"].strip().lower() not in recorded_titles]
        if system_id
        else []
    )
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for risk in risks:
        severity_counts[risk["severity"]] = severity_counts.get(risk["severity"], 0) + 1

    return {
        "risks": risks,
        "suggested": suggested,
        "summary": {
            "total": len(risks),
            "open": len([risk for risk in risks if risk["status"] not in CLOSED_RISK_STATUSES]),
            # Raised by FairMind itself (drift, environmental impact), not typed in by a person.
            "automated": len([risk for risk in risks if risk.get("source") != "manual_assessment"]),
            "bySeverity": severity_counts,
            "suggested": len(suggested),
        },
    }


def _fetch_risk_dashboard_payload(db: Session, system_id: str) -> Dict[str, Any]:
    rows = db.execute(
        text(
            "SELECT id, system_id, title, severity, status, description, mitigation, likelihood, risk_score, source, categories_json, metadata_json, created_at, updated_at "
            "FROM governance_risks WHERE system_id = :system_id ORDER BY risk_score DESC, created_at DESC"
        ),
        {"system_id": system_id},
    ).fetchall()
    return _risk_dashboard(rows, system_id)


def _fetch_stored_risk_summary(db: Session, system_id: str) -> Dict[str, Any]:
    rows = db.execute(
        text(
            "SELECT severity, status FROM governance_risks WHERE system_id = :system_id"
        ),
        {"system_id": system_id},
    ).fetchall()
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    open_count = 0
    open_high_or_critical = 0
    for row in rows:
        severity = row[0] if row[0] in severity_counts else "medium"
        severity_counts[severity] += 1
        if row[1] not in CLOSED_RISK_STATUSES:
            open_count += 1
            if severity in ("high", "critical"):
                open_high_or_critical += 1
    return {
        "total": len(rows),
        "open": open_count,
        "openHighOrCritical": open_high_or_critical,
        "automated": 0,
        "bySeverity": severity_counts,
    }


def _clamp(number: int, lower: int, upper: int) -> int:
    return max(lower, min(number, upper))


def _derive_lifecycle_status(
    system: Dict[str, Any],
    risk_summary: Dict[str, Any],
    evidence_summary: Dict[str, Any],
    remediation_summary: Dict[str, Any],
    approval_request: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    stored_stage = system.get("lifecycleStage") or "onboard"

    if approval_request and approval_request.get("status") == "approved":
        stage = "operate"
    # SYSTEM_JOURNEY.md: Remediate lasts until no open high or critical risk and no active task.
    elif (
        risk_summary.get("openHighOrCritical", 0) > 0
        or remediation_summary.get("activeTasks", 0) > 0
        or remediation_summary.get("byStatus", {}).get("blocked", 0) > 0
    ):
        stage = "remediate"
    elif (
        risk_summary.get("total", 0) > 0
        or evidence_summary.get("totalEvidence", 0) > 0
        or approval_request is not None
    ):
        stage = "govern"
    else:
        stage = stored_stage

    stage_base = {
        "onboard": 18,
        "assess": 38,
        "govern": 58,
        "remediate": 52,
        "operate": 88,
    }
    # Readiness credits lifecycle progress only once evidence backs it: a system
    # with no evidence reads 0, whatever stage it was registered at.
    if int(evidence_summary.get("totalEvidence", 0)) == 0:
        readiness = 0
    else:
        readiness = stage_base.get(stage, 18)
        readiness += min(int(evidence_summary.get("linkedEvidence", 0)) * 6, 18)
        readiness += 14 if evidence_summary.get("decisionReadiness") == "review_ready" else 0
        readiness += 10 if approval_request and approval_request.get("status") == "approved" else 0
        readiness -= int(risk_summary.get("bySeverity", {}).get("critical", 0)) * 18
        readiness -= int(risk_summary.get("bySeverity", {}).get("high", 0)) * 10
        readiness -= int(remediation_summary.get("activeTasks", 0)) * 8
        readiness -= max(0, len(evidence_summary.get("missingSignals", [])) - 1) * 5
        # Floor of 5 once evidence exists, so 0% only ever means "no evidence yet".
        readiness = _clamp(round(readiness), 5, 100)

    failed_controls = (
        int(risk_summary.get("open", 0))
        + int(remediation_summary.get("activeTasks", 0))
        + (0 if evidence_summary.get("decisionReadiness") == "review_ready" else 1)
    )
    critical_blockers = (
        int(risk_summary.get("bySeverity", {}).get("critical", 0))
        + (1 if approval_request and approval_request.get("status") == "rejected" else 0)
        + (1 if evidence_summary.get("decisionReadiness") == "needs_evidence" else 0)
    )
    recommendation = "Go"
    if (
        int(risk_summary.get("bySeverity", {}).get("critical", 0)) > 0
        or evidence_summary.get("totalEvidence", 0) == 0
        or evidence_summary.get("decisionReadiness") == "needs_evidence"
    ):
        recommendation = "No-Go"
    elif (
        int(risk_summary.get("open", 0)) > 0
        or int(remediation_summary.get("activeTasks", 0)) > 0
        or evidence_summary.get("decisionReadiness") != "review_ready"
    ):
        recommendation = "Conditional Go"

    return {
        "stage": stage,
        "readiness": readiness,
        "failedControls": failed_controls,
        "criticalBlockers": critical_blockers,
        "missingEvidence": len(evidence_summary.get("missingSignals", [])),
        "openRisks": int(risk_summary.get("open", 0)),
        "activeRemediation": int(remediation_summary.get("activeTasks", 0)),
        "approvalStatus": approval_request.get("status") if approval_request else None,
        "releaseRecommendation": recommendation,
    }


def _persist_lifecycle_stage_if_needed(db: Session, system_id: str, stored_stage: str, derived_stage: str) -> None:
    if stored_stage == derived_stage:
        return
    db.execute(
        text(
            "UPDATE governance_ai_systems SET lifecycle_stage = :lifecycle_stage, updated_at = :updated_at "
            "WHERE id = :id"
        ),
        {
            "id": system_id,
            "lifecycle_stage": derived_stage,
            "updated_at": _utc_now_iso(),
        },
    )
    db.commit()


def _build_ai_system_payload(db: Session, row: Any) -> Dict[str, Any]:
    system = _serialize_ai_system_row(row)
    risk_summary = _fetch_stored_risk_summary(db, system["id"])
    evidence_records = _fetch_evidence_records(db, system["id"])
    evidence_summary = _summarize_evidence(evidence_records, system["id"])
    remediation_tasks = _fetch_remediation_tasks(db, system["id"])
    remediation_summary = _summarize_remediation_tasks(remediation_tasks, system["id"])
    approval_request = _fetch_latest_system_approval(db, system["id"])
    lifecycle_summary = _derive_lifecycle_status(
        system,
        risk_summary,
        evidence_summary,
        remediation_summary,
        approval_request,
    )
    _persist_lifecycle_stage_if_needed(db, system["id"], system["lifecycleStage"], lifecycle_summary["stage"])
    system["lifecycleStage"] = lifecycle_summary["stage"]
    system["readiness"] = lifecycle_summary["readiness"]
    system["lifecycleSummary"] = lifecycle_summary
    return system


def _fetch_approval_decisions(db: Session, request_id: str) -> List[Dict[str, Any]]:
    rows = db.execute(
        text(
            "SELECT id, request_id, decision, notes, decided_by, created_at "
            "FROM governance_approval_decisions WHERE request_id = :request_id "
            "ORDER BY created_at ASC"
        ),
        {"request_id": request_id},
    ).fetchall()
    return [
        {
            "id": row[0],
            "request_id": row[1],
            "decision": row[2],
            "notes": row[3] or "",
            "decided_by": row[4],
            "createdAt": row[5],
        }
        for row in rows
    ]
    priority_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    retest_required = 0
    linked_risk_refs = 0

    for task in tasks:
        status = task.get("status") or "open"
        if status in status_counts:
            status_counts[status] += 1
        priority = task.get("priority") or "medium"
        if priority in priority_counts:
            priority_counts[priority] += 1
        if task.get("retestRequired"):
            retest_required += 1
        linked_risk_refs += len(task.get("linkedRiskIds") or [])

    active = sum(status_counts[key] for key in ("open", "in_progress", "blocked", "ready_for_retest"))
    completed = status_counts["resolved"] + status_counts["closed"]

    return {
        "systemId": system_id,
        "totalTasks": len(tasks),
        "activeTasks": active,
        "completedTasks": completed,
        "retestRequiredTasks": retest_required,
        "linkedRiskRefs": linked_risk_refs,
        "byStatus": status_counts,
        "byPriority": priority_counts,
    }


def _fetch_evidence_records(db: Session, system_id: str) -> List[Dict[str, Any]]:
    rows = db.execute(
        text(
            "SELECT id, system_id, evidence_type, content_json, confidence, metadata_json, created_at "
            "FROM governance_evidence WHERE system_id = :system_id ORDER BY created_at DESC"
        ),
        {"system_id": system_id},
    ).fetchall()
    if not rows:
        return []

    link_rows = db.execute(
        text(
            "SELECT ge.id, gel.entity_type, gel.entity_id "
            "FROM governance_evidence_links gel "
            "JOIN governance_evidence ge ON ge.id = gel.evidence_id "
            "WHERE ge.system_id = :system_id "
            "ORDER BY gel.created_at DESC"
        ),
        {"system_id": system_id},
    ).fetchall()
    links_by_evidence_id: Dict[str, List[Dict[str, Any]]] = {}
    for link_row in link_rows:
        links_by_evidence_id.setdefault(link_row[0], []).append(
            {"entityType": link_row[1], "entityId": link_row[2]}
        )

    return [
        _serialize_evidence_row(row, links_by_evidence_id.get(row[0], []))
        for row in rows
    ]


# Decision records stored as evidence so seals hash them; they are not evidence of a control,
# so they neither move the lifecycle stage nor count toward readiness.
RECORD_ONLY_EVIDENCE_TYPES = {"applicability_decision", "applicability_override_accepted"}


def _reject_record_only_type(evidence_type: str) -> None:
    """Only the applicability routes write these types; every generic evidence write refuses them."""
    if evidence_type in RECORD_ONLY_EVIDENCE_TYPES:
        raise HTTPException(status_code=422, detail="Record the tier and rules on the system file, not as uploaded evidence")


def _summarize_evidence(records: List[Dict[str, Any]], system_id: str) -> Dict[str, Any]:
    records = [r for r in records if r.get("type") not in RECORD_ONLY_EVIDENCE_TYPES]
    if not records:
        return {
            "systemId": system_id,
            "totalEvidence": 0,
            "linkedEvidence": 0,
            "averageConfidence": 0.0,
            "highConfidenceEvidence": 0,
            "evidenceTypes": [],
            "metadataSources": [],
            "workflowState": "empty",
            "decisionReadiness": "needs_evidence",
            "missingSignals": [
                "collect monitoring evidence",
                "collect compliance evidence",
                "collect validation evidence",
            ],
            "recommendedNextStep": "Collect the first evidence artifact to begin governance review.",
        }

    evidence_types: Dict[str, int] = {}
    metadata_sources: Dict[str, int] = {}
    linked_evidence = 0
    high_confidence_evidence = 0
    confidence_sum = 0.0

    for record in records:
        confidence = float(record.get("confidence", 0.0))
        confidence_sum += confidence
        if confidence >= 0.9:
            high_confidence_evidence += 1
        if record.get("linkedEntityCount", 0) > 0:
            linked_evidence += 1

        evidence_type = record.get("type") or "unknown"
        evidence_types[evidence_type] = evidence_types.get(evidence_type, 0) + 1

        source = record.get("metadataSummary", {}).get("source") or "unknown"
        metadata_sources[source] = metadata_sources.get(source, 0) + 1

    total = len(records)
    avg_confidence = round(confidence_sum / total, 3) if total else 0.0
    workflow_state = "review_ready" if linked_evidence > 0 else "collecting"
    decision_readiness = "review_ready" if linked_evidence > 0 and total >= 1 else "needs_linking"
    missing_signals = []
    type_set = set(evidence_types)
    if "audit_log" not in type_set:
        missing_signals.append("audit or trace evidence")
    if "monitoring" not in type_set and "monitoring_snapshot" not in type_set:
        missing_signals.append("monitoring evidence")
    if linked_evidence == 0:
        missing_signals.append("link evidence to a risk, policy, or approval request")

    return {
        "systemId": system_id,
        "totalEvidence": total,
        "linkedEvidence": linked_evidence,
        "averageConfidence": avg_confidence,
        "highConfidenceEvidence": high_confidence_evidence,
        "evidenceTypes": [
            {"type": evidence_type, "count": count}
            for evidence_type, count in sorted(evidence_types.items(), key=lambda item: (-item[1], item[0]))
        ],
        "metadataSources": [
            {"source": source, "count": count}
            for source, count in sorted(metadata_sources.items(), key=lambda item: (-item[1], item[0]))
        ],
        "workflowState": workflow_state,
        "decisionReadiness": decision_readiness,
        "missingSignals": missing_signals,
        "recommendedNextStep": (
            "Link evidence to a governance entity before approval review."
            if linked_evidence == 0
            else "Use the evidence bundle for governance review and approval."
        ),
    }


@router.get("/status")
async def governance_status(db: Session = Depends(get_db)):
    _ensure_tables(db)
    return {
        "status": "operational",
        "timestamp": _utc_now_iso(),
        "capabilities": ["policies", "approval-workflows", "evidence-linking"],
    }


@router.post("/workspaces")
async def create_workspace(request: WorkspaceCreateRequest, http: Request, db: Session = Depends(get_db)):
    _ensure_tables(db)
    org_id = _caller_org(http)
    workspace_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_workspaces (id, org_id, name, owner, created_at, updated_at) "
            "VALUES (:id, :org_id, :name, :owner, :created_at, :updated_at)"
        ),
        {
            "id": workspace_id,
            "org_id": org_id,
            "name": request.name,
            "owner": request.owner,
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()
    return {
        "id": workspace_id,
        "name": request.name,
        "owner": request.owner,
        "createdAt": now,
        "updatedAt": now,
    }


@router.get("/workspaces")
async def list_workspaces(http: Request, db: Session = Depends(get_db)):
    _ensure_tables(db)
    rows = db.execute(
        text(
            "SELECT id, name, owner, created_at, updated_at "
            "FROM governance_workspaces WHERE org_id = :org_id ORDER BY created_at DESC"
        ),
        {"org_id": _caller_org(http)},
    ).fetchall()
    return [_serialize_workspace_row(row) for row in rows]


@router.post("/systems")
async def create_ai_system(request: AISystemCreateRequest, http: Request, db: Session = Depends(get_db)):
    _ensure_tables(db)
    workspace = db.execute(
        text("SELECT id FROM governance_workspaces WHERE id = :id"),
        {"id": request.workspace_id},
    ).fetchone()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    system_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_ai_systems (id, org_id, workspace_id, name, owner, risk_tier, lifecycle_stage, metadata_json, created_at, updated_at) "
            "VALUES (:id, :org_id, :workspace_id, :name, :owner, :risk_tier, :lifecycle_stage, :metadata_json, :created_at, :updated_at)"
        ),
        {
            "id": system_id,
            "org_id": _caller_org(http),
            "workspace_id": request.workspace_id,
            "name": request.name,
            "owner": request.owner,
            "risk_tier": request.risk_tier,
            "lifecycle_stage": request.lifecycle_stage,
            # applicability is written only by PUT /systems/{id}/applicability, never taken from the client.
            "metadata_json": json.dumps({k: v for k, v in request.metadata.items() if k != "applicability"}),
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()
    row = db.execute(
        text(
            "SELECT id, workspace_id, name, owner, risk_tier, lifecycle_stage, metadata_json, created_at, updated_at "
            "FROM governance_ai_systems WHERE id = :id"
        ),
        {"id": system_id},
    ).fetchone()
    return _build_ai_system_payload(db, row)


@router.get("/systems")
async def list_ai_systems(
    http: Request,
    workspace_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    org_id = _caller_org(http)
    if workspace_id:
        rows = db.execute(
            text(
                "SELECT id, workspace_id, name, owner, risk_tier, lifecycle_stage, metadata_json, created_at, updated_at "
                "FROM governance_ai_systems WHERE workspace_id = :workspace_id AND org_id = :org_id ORDER BY created_at DESC"
            ),
            {"workspace_id": workspace_id, "org_id": org_id},
        ).fetchall()
    else:
        rows = db.execute(
            text(
                "SELECT id, workspace_id, name, owner, risk_tier, lifecycle_stage, metadata_json, created_at, updated_at "
                "FROM governance_ai_systems WHERE org_id = :org_id ORDER BY created_at DESC"
            ),
            {"org_id": org_id},
        ).fetchall()
    return [_build_ai_system_payload(db, row) for row in rows]


@router.get("/systems/{system_id}")
async def get_ai_system(system_id: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
    row = db.execute(
        text(
            "SELECT id, workspace_id, name, owner, risk_tier, lifecycle_stage, metadata_json, created_at, updated_at "
            "FROM governance_ai_systems WHERE id = :id"
        ),
        {"id": system_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="AI system not found")
    return _build_ai_system_payload(db, row)


@router.get("/lifecycle/{system_id}/summary")
async def get_ai_system_lifecycle_summary(system_id: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
    row = db.execute(
        text(
            "SELECT id, workspace_id, name, owner, risk_tier, lifecycle_stage, metadata_json, created_at, updated_at "
            "FROM governance_ai_systems WHERE id = :id"
        ),
        {"id": system_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="AI system not found")
    payload = _build_ai_system_payload(db, row)
    return {
        "systemId": payload["id"],
        **payload["lifecycleSummary"],
    }


@router.get("/dashboard/risk")
async def get_risk_dashboard(
    system_id: Optional[str] = Query(default=None),
    current_user: TokenData = Depends(get_current_active_user),
    membership: OrgMembership = Depends(org_member),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    if system_id:
        _require_system_access(db, system_id, current_user)
        return _fetch_risk_dashboard_payload(db, system_id)
    else:
        rows = db.execute(
            text(
                "SELECT id, system_id, title, severity, status, description, mitigation, likelihood, risk_score, source, categories_json, metadata_json, created_at, updated_at "
                "FROM governance_risks WHERE system_id IN (SELECT id FROM governance_ai_systems WHERE org_id = :org_id) "
                "ORDER BY risk_score DESC, created_at DESC LIMIT 50"
            ),
            {"org_id": membership.org_id},
        ).fetchall()
        return _risk_dashboard(rows, None)


@router.post("/risks/assess")
async def assess_risks(
    request: RiskAssessmentRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, request.systemId, current_user, mutate=True)
    risk_id = str(uuid.uuid4())
    now = _utc_now_iso()
    severity = _normalize_severity(request.severity)
    likelihood = "possible"
    risk_score = _risk_score(severity, likelihood)
    title = f"{request.riskType.title()} risk"
    mitigation = (
        "Create remediation tasks, attach evaluation evidence, assign owners, "
        "and require a re-test before release approval."
    )

    db.execute(
        text(
            "INSERT INTO governance_risks "
            "(id, system_id, title, severity, status, description, mitigation, likelihood, risk_score, source, categories_json, metadata_json, created_at, updated_at) "
            "VALUES (:id, :system_id, :title, :severity, :status, :description, :mitigation, :likelihood, :risk_score, :source, :categories_json, :metadata_json, :created_at, :updated_at)"
        ),
        {
            "id": risk_id,
            "system_id": request.systemId,
            "title": title,
            "severity": severity,
            "status": "open",
            "description": request.description,
            "mitigation": mitigation,
            "likelihood": likelihood,
            "risk_score": risk_score,
            "source": "manual_assessment",
            "categories_json": json.dumps([request.riskType]),
            "metadata_json": json.dumps({"riskType": request.riskType, "isAutomated": False}),
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()

    automated_matches = _generate_automated_risks(request.systemId, request.riskType)
    top_matches = automated_matches[:3]

    return {
        "id": risk_id,
        "systemId": request.systemId,
        "title": title,
        "severity": severity,
        "status": "open",
        "description": request.description,
        "mitigation": mitigation,
        "likelihood": likelihood,
        "riskScore": risk_score,
        "source": "manual_assessment",
        "categories": [request.riskType],
        "timestamp": now,
        "automation": {
            "recommendedRisks": top_matches,
            "nextActions": [
                "Link the risk to evidence from bias, compliance, and monitoring runs.",
                "Create remediation work for failed controls and owners.",
                "Require re-test and approval workflow completion before release.",
            ],
        },
    }


@router.get("/compliance/frameworks")
async def get_frameworks():
    return FRAMEWORKS


@router.get("/compliance/frameworks/{framework}/controls")
async def get_framework_controls(framework: str):
    found = next((f for f in FRAMEWORKS if f["id"] == framework), None)
    if not found:
        raise HTTPException(status_code=404, detail="Framework not found")
    return {
        "framework": framework,
        "controls": found["controls"],
    }


# ---------------------------------------------------------------------------
# Framework Controls (DB-backed CRUD)
# ---------------------------------------------------------------------------


class FrameworkControlCreateRequest(BaseModel):
    control_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = ""
    status: str = Field(default="not_started")
    owner: Optional[str] = None
    evidence_required: int = Field(default=0, ge=0)


@router.get("/frameworks/{framework}/controls")
async def list_framework_controls(framework: str, db: Session = Depends(get_db)):
    """List all controls stored in the DB for a given framework."""
    _ensure_tables(db)
    rows = db.execute(
        text(
            "SELECT id, framework, control_id, title, description, status, owner, evidence_required, created_at, updated_at "
            "FROM governance_framework_controls WHERE framework = :framework ORDER BY control_id"
        ),
        {"framework": framework},
    ).fetchall()
    return [
        {
            "id": row[0],
            "framework": row[1],
            "controlId": row[2],
            "title": row[3],
            "description": row[4],
            "status": row[5],
            "owner": row[6],
            "evidenceRequired": row[7],
            "createdAt": row[8],
            "updatedAt": row[9],
        }
        for row in rows
    ]


# The control catalogue is shared: every organisation and seed_env_controls read
# it by framework alone, so only a platform admin may add to it.
@router.post("/frameworks/{framework}/controls", dependencies=[Depends(require_admin)])
async def create_framework_control(
    framework: str,
    request: FrameworkControlCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a framework control record in the DB."""
    _ensure_tables(db)
    control_id_pk = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_framework_controls "
            "(id, framework, control_id, title, description, status, owner, evidence_required, created_at, updated_at) "
            "VALUES (:id, :framework, :control_id, :title, :description, :status, :owner, :evidence_required, :created_at, :updated_at)"
        ),
        {
            "id": control_id_pk,
            "framework": framework,
            "control_id": request.control_id,
            "title": request.title,
            "description": request.description,
            "status": request.status,
            "owner": request.owner,
            "evidence_required": request.evidence_required,
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()
    return {
        "id": control_id_pk,
        "framework": framework,
        "controlId": request.control_id,
        "title": request.title,
        "description": request.description,
        "status": request.status,
        "owner": request.owner,
        "evidenceRequired": request.evidence_required,
        "createdAt": now,
        "updatedAt": now,
    }


# ---------------------------------------------------------------------------
# System-scoped evidence and approval endpoints
# ---------------------------------------------------------------------------


@router.get("/systems/{system_id}/evidence")
async def list_system_evidence(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all evidence items linked to an AI system."""
    _ensure_tables(db)
    _require_evidence_system_access(db, system_id, current_user)
    rows = db.execute(
        text(
            "SELECT id, system_id, control_id, evidence_type, title, source, content_json, "
            "confidence, status, uploaded_by, metadata_json, captured_at, created_at "
            "FROM governance_evidence WHERE system_id = :system_id ORDER BY created_at DESC"
        ),
        {"system_id": system_id},
    ).fetchall()
    return [
        {
            "id": row[0],
            "systemId": row[1],
            "controlId": row[2],
            "evidenceType": row[3],
            "title": row[4],
            "source": row[5],
            "content": _load_json_value(row[6], {}),
            "confidence": row[7],
            "status": row[8],
            "uploadedBy": row[9],
            "metadata": _load_json_value(row[10], {}),
            "capturedAt": row[11],
            "createdAt": row[12],
        }
        for row in rows
    ]


class SystemEvidenceCreateRequest(BaseModel):
    control_id: Optional[str] = None
    evidence_type: str = Field(min_length=1)
    title: Optional[str] = None
    source: Optional[str] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    status: str = Field(default="draft")
    uploaded_by: Optional[str] = None
    captured_at: Optional[str] = None


@router.post("/systems/{system_id}/evidence")
async def create_system_evidence(
    system_id: str,
    request: SystemEvidenceCreateRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create an evidence item directly linked to an AI system."""
    _ensure_tables(db)
    membership = _require_evidence_system_access(
        db, system_id, current_user, mutate=True
    )
    _reject_record_only_type(request.evidence_type)
    if request.control_id:
        _require_untrusted_external_evidence_linking_enabled()
        _validate_control_link_scope(
            db, membership, system_id, "control", request.control_id
        )

    evidence_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, system_id, org_id, control_id, evidence_type, title, source, content_json, "
            "confidence, status, uploaded_by, metadata_json, captured_at, created_at) "
            "VALUES (:id, :system_id, :org_id, :control_id, :evidence_type, :title, :source, "
            ":content_json, :confidence, :status, :uploaded_by, :metadata_json, :captured_at, :created_at)"
        ),
        {
            "id": evidence_id,
            "system_id": system_id,
            "org_id": membership.org_id,
            "control_id": request.control_id,
            "evidence_type": request.evidence_type,
            "title": request.title,
            "source": request.source,
            "content_json": json.dumps(request.content),
            "confidence": request.confidence,
            "status": request.status,
            "uploaded_by": current_user.email or current_user.user_id,
            "metadata_json": "{}",
            "captured_at": request.captured_at or now,
            "created_at": now,
        },
    )
    db.commit()
    return {
        "id": evidence_id,
        "systemId": system_id,
        "controlId": request.control_id,
        "evidenceType": request.evidence_type,
        "title": request.title,
        "source": request.source,
        "confidence": request.confidence,
        "status": request.status,
        "uploadedBy": current_user.email or current_user.user_id,
        "capturedAt": request.captured_at or now,
        "createdAt": now,
    }


@router.get("/systems/{system_id}/approvals")
async def list_system_approvals(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all approval requests linked to an AI system."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    rows = db.execute(
        text(
            "SELECT id, workflow_id, entity_type, entity_id, ai_system_id, requested_by, "
            "status, current_step, decision, decision_notes, decided_by, decided_at, created_at, updated_at "
            "FROM governance_approval_requests "
            "WHERE entity_type = 'ai_system' "
            "AND (entity_id = :system_id OR ai_system_id = :system_id) "
            "ORDER BY created_at DESC"
        ),
        {"system_id": system_id},
    ).fetchall()
    for row in rows:
        _require_approval_request_access(db, str(row[0]), current_user)
    return [
        {
            "id": row[0],
            "workflowId": row[1],
            "entityType": row[2],
            "entityId": row[3],
            "aiSystemId": row[4],
            "requestedBy": row[5],
            "status": row[6],
            "currentStep": row[7],
            "decision": row[8],
            "decisionNotes": row[9],
            "decidedBy": row[10],
            "decidedAt": row[11],
            "createdAt": row[12],
            "updatedAt": row[13],
        }
        for row in rows
    ]


@router.post("/systems/{system_id}/approvals")
async def create_system_approval(
    system_id: str,
    request: SystemApprovalRequestCreateRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create an approval request for an AI system, using the default system workflow."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    actor = _authenticated_actor(current_user)

    now = _utc_now_iso()
    workflow_id = _ensure_system_approval_workflow(db, now)
    request_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_approval_requests "
            "(id, workflow_id, entity_type, entity_id, ai_system_id, requested_by, "
            "status, current_step, created_at, updated_at) "
            "VALUES (:id, :workflow_id, :entity_type, :entity_id, :ai_system_id, "
            ":requested_by, :status, :current_step, :created_at, :updated_at)"
        ),
        {
            "id": request_id,
            "workflow_id": workflow_id,
            "entity_type": "ai_system",
            "entity_id": system_id,
            "ai_system_id": system_id,
            "requested_by": actor,
            "status": "pending",
            "current_step": 0,
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()
    return {
        "id": request_id,
        "workflowId": workflow_id,
        "entityType": "ai_system",
        "entityId": system_id,
        "aiSystemId": system_id,
        "requestedBy": actor,
        "status": "pending",
        "currentStep": 0,
        "createdAt": now,
        "updatedAt": now,
    }


@router.post("/approval-workflows")
async def create_approval_workflow(
    request: ApprovalWorkflowCreateRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_platform_workflow_admin(current_user)
    workflow_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_approval_workflows "
            "(id, name, entity_type, steps_json, is_active, created_by, created_at, updated_at) "
            "VALUES (:id, :name, :entity_type, :steps_json, :is_active, :created_by, :created_at, :updated_at)"
        ),
        {
            "id": workflow_id,
            "name": request.name,
            "entity_type": request.entity_type,
            "steps_json": json.dumps(request.steps),
            "is_active": True,
            "created_by": _authenticated_actor(current_user),
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()
    return {
        "id": workflow_id,
        "name": request.name,
        "entity_type": request.entity_type,
        "steps": request.steps,
        "is_active": True,
        "createdAt": now,
    }


@router.get("/approval-workflows")
async def list_approval_workflows(
    entity_type: Optional[str] = Query(default=None),
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    if entity_type:
        rows = db.execute(
            text(
                "SELECT id, name, entity_type, steps_json, is_active, created_at "
                "FROM governance_approval_workflows WHERE entity_type = :entity_type ORDER BY created_at DESC"
            ),
            {"entity_type": entity_type},
        ).fetchall()
    else:
        rows = db.execute(
            text(
                "SELECT id, name, entity_type, steps_json, is_active, created_at "
                "FROM governance_approval_workflows ORDER BY created_at DESC"
            )
        ).fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "entity_type": row[2],
            "steps": json.loads(row[3]),
            "is_active": bool(row[4]),
            "createdAt": row[5],
        }
        for row in rows
    ]


@router.post("/approval-workflows/{workflow_id}/requests")
async def create_approval_request(
    workflow_id: str,
    request: ApprovalRequestCreateRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    if request.entity_type != "ai_system":
        raise HTTPException(status_code=404, detail="Approval target not found")
    _require_system_access(db, request.entity_id, current_user, mutate=True)
    workflow = db.execute(
        text("SELECT id FROM governance_approval_workflows WHERE id = :id AND is_active = TRUE"),
        {"id": workflow_id},
    ).fetchone()
    if not workflow:
        raise HTTPException(status_code=404, detail="Active workflow not found")

    request_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_approval_requests "
            "(id, workflow_id, entity_type, entity_id, ai_system_id, requested_by, status, current_step, decision_notes, created_at, updated_at) "
            "VALUES (:id, :workflow_id, :entity_type, :entity_id, :ai_system_id, :requested_by, :status, :current_step, :decision_notes, :created_at, :updated_at)"
        ),
        {
            "id": request_id,
            "workflow_id": workflow_id,
            "entity_type": request.entity_type,
            "entity_id": request.entity_id,
            "ai_system_id": request.entity_id,
            "requested_by": _authenticated_actor(current_user),
            "status": "pending",
            "current_step": 1,
            "decision_notes": "",
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()
    return {
        "id": request_id,
        "workflow_id": workflow_id,
        "entity_type": request.entity_type,
        "entity_id": request.entity_id,
        "status": "pending",
        "current_step": 1,
        "createdAt": now,
    }


def _gate_decision_block(gate: dict, notes: Optional[str]):
    """Return None when approval may proceed, else (status_code, detail)."""
    verdict = gate.get("verdict")
    if verdict == "no_go":
        open_checks = [c.get("label") for c in gate.get("checks", []) if c.get("state") == "open"]
        reasons = gate.get("reasons") or []
        return 409, {
            "message": "The release gate says no go: " + ("; ".join(reasons) if reasons else "required evidence is missing") + ".",
            "gate": {
                "verdict": verdict,
                "confidence": gate.get("confidence"),
                "reasons": reasons,
                "openChecks": open_checks,
            },
        }
    if verdict == "conditional_go" and not (notes or "").strip():
        return 422, {
            "message": "The release gate is conditional go. State the conditions you accept in the notes to approve.",
            "gate": {"verdict": verdict, "confidence": gate.get("confidence"), "reasons": gate.get("reasons") or []},
        }
    return None


def _release_blockers(db: Session, system_id: str) -> Optional[Dict[str, Any]]:
    """None when nothing blocks approval, else the 409 detail: open high or critical findings, active critical tasks."""
    findings = _fetch_stored_risk_summary(db, system_id)["openHighOrCritical"]
    tasks = sum(
        1 for task in _fetch_remediation_tasks(db, system_id)
        if task.get("priority") == "critical" and (task.get("status") or "open") in ACTIVE_REMEDIATION_STATUSES
    )
    if not findings and not tasks:
        return None
    parts = [
        f"{findings} open high or critical finding{'' if findings == 1 else 's'}" if findings else "",
        f"{tasks} active critical remediation task{'' if tasks == 1 else 's'}" if tasks else "",
    ]
    return {
        "message": "Approval is blocked by " + " and ".join(p for p in parts if p) + ". Close them first; the release can still be rejected.",
        "blockers": {"openHighOrCriticalFindings": findings, "activeCriticalTasks": tasks},
    }


@router.post("/approval-requests/{request_id}/decision")
async def make_approval_decision(
    request_id: str,
    request: ApprovalDecisionRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    approval_system_id = _require_approval_request_access(
        db,
        request_id,
        current_user,
        mutate=True,
    )
    new_status = "approved" if request.decision == "approved" else "rejected"
    now = _utc_now_iso()
    existing = db.execute(
        text(
            "SELECT id, entity_type, entity_id FROM governance_approval_requests WHERE id = :id"
        ),
        {"id": request_id},
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Approval request not found")
    gate = None
    if existing.entity_type == "ai_system" and approval_system_id:
        from api.routes.fairness_runs import _gate_payload  # function-level: that router imports this one

        system = db.execute(text("SELECT risk_tier FROM governance_ai_systems WHERE id = :id"), {"id": approval_system_id}).fetchone()
        # The evidence alone: an earlier rejection must not stop the reviewer approving this request.
        gate = _gate_payload(db, approval_system_id, system[0] if system else "medium", with_decision=False)
        if new_status == "approved":
            blocked = _gate_decision_block(gate, request.notes)
            if blocked:
                raise HTTPException(status_code=blocked[0], detail=blocked[1])
    if new_status == "approved" and existing.entity_type == "ai_system":
        from src.application.services.environmental_service import env_gate_status

        membership = _require_system_access(
            db,
            approval_system_id,
            current_user,
            mutate=True,
        )
        environmental_gate = env_gate_status(
            db,
            approval_system_id,
            org_id=membership.org_id,
        )
        if environmental_gate.get("blocked"):
            raise HTTPException(
                status_code=409,
                detail={
                    "message": environmental_gate.get("reason"),
                    "environmentalGate": environmental_gate,
                },
            )
        blockers = _release_blockers(db, approval_system_id)
        if blockers:
            raise HTTPException(status_code=409, detail=blockers)
    actor = _authenticated_actor(current_user)
    result = db.execute(
        text(
            "UPDATE governance_approval_requests "
            "SET status = :status, decision = :status, decision_notes = :notes, "
            "decided_by = :decided_by, decided_at = :updated_at, updated_at = :updated_at "
            "WHERE id = :id AND status = 'pending'"
        ),
        {
            "status": new_status,
            "notes": request.notes,
            "decided_by": actor,
            "updated_at": now,
            "id": request_id,
        },
    )
    if result.rowcount == 0:
        current = db.execute(
            text("SELECT status FROM governance_approval_requests WHERE id = :id"),
            {"id": request_id},
        ).fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Approval request not found")
        raise HTTPException(
            status_code=409,
            detail=f"Request is already '{current[0]}'; only pending requests can be decided",
        )

    decision_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_approval_decisions (id, request_id, decision, notes, decided_by, created_at) "
            "VALUES (:id, :request_id, :decision, :notes, :decided_by, :created_at)"
        ),
        {
            "id": decision_id,
            "request_id": request_id,
            "decision": new_status,
            "notes": request.notes,
            "decided_by": actor,
            "created_at": now,
        },
    )
    seal = None
    if existing.entity_type == "ai_system" and approval_system_id:
        from src.application.services.decision_seal_service import seal_decision

        seal = seal_decision(
            db,
            system_id=approval_system_id,
            request_id=request_id,
            decision_id=decision_id,
            decision=new_status,
            sealed_by=actor,
            gate=gate,
        )

    db.commit()
    return {
        "id": request_id,
        "status": new_status,
        "notes": request.notes,
        "updatedAt": now,
        "seal": seal,
    }


@router.get("/approval-requests/{request_id}")
async def get_approval_request(
    request_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_approval_request_access(db, request_id, current_user)
    row = db.execute(
        text(
            "SELECT id, workflow_id, entity_type, entity_id, requested_by, status, current_step, decision_notes, created_at, updated_at "
            "FROM governance_approval_requests WHERE id = :id"
        ),
        {"id": request_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Approval request not found")

    return _serialize_approval_request_row(row)


@router.get("/approval-requests")
async def list_approval_requests(
    entity_type: str = Query(min_length=1),
    entity_id: Optional[str] = Query(default=None),
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    if entity_type != "ai_system":
        raise HTTPException(status_code=404, detail="Approval requests not found")
    if entity_id:
        _require_system_access(db, entity_id, current_user)
        rows = db.execute(
            text(
                "SELECT id, workflow_id, entity_type, entity_id, requested_by, status, current_step, decision_notes, created_at, updated_at "
                "FROM governance_approval_requests WHERE entity_type = :entity_type AND entity_id = :entity_id "
                "ORDER BY created_at DESC"
            ),
            {"entity_type": entity_type, "entity_id": entity_id},
        ).fetchall()
    else:
        rows = db.execute(
            text(
                "SELECT id, workflow_id, entity_type, entity_id, requested_by, status, current_step, decision_notes, created_at, updated_at "
                "FROM governance_approval_requests WHERE entity_type = :entity_type "
                "ORDER BY created_at DESC"
            ),
            {"entity_type": entity_type},
        ).fetchall()

    visible = []
    for row in rows:
        try:
            _require_approval_request_access(db, str(row[0]), current_user)
        except HTTPException:
            if entity_id:
                raise
            continue  # ponytail: one access check per row; a join on org membership if the list grows
        visible.append(row)
    return [_serialize_approval_request_row(row) for row in visible]


@router.get("/approval-requests/{request_id}/decisions")
async def list_approval_decisions(
    request_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_approval_request_access(db, request_id, current_user)
    return _fetch_approval_decisions(db, request_id)


@router.get("/approval/system/{system_id}")
async def get_system_approval_status(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    row = db.execute(
        text(
            "SELECT id, workflow_id, entity_type, entity_id, requested_by, status, current_step, decision_notes, created_at, updated_at "
            "FROM governance_approval_requests WHERE entity_type = :entity_type AND entity_id = :entity_id "
            "ORDER BY created_at DESC LIMIT 1"
        ),
        {"entity_type": "ai_system", "entity_id": system_id},
    ).fetchone()

    if not row:
        return {
            "systemId": system_id,
            "request": None,
            "decisions": [],
        }

    _require_approval_request_access(db, str(row[0]), current_user)
    request = _serialize_approval_request_row(row)
    return {
        "systemId": system_id,
        "request": request,
        "decisions": _fetch_approval_decisions(db, request["id"]),
    }


@router.post("/approval/system/{system_id}/request")
async def create_system_approval_request(
    system_id: str,
    request: SystemApprovalRequestCreateRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    actor = _authenticated_actor(current_user)
    existing_request = db.execute(
        text(
            "SELECT id, workflow_id, entity_type, entity_id, requested_by, status, current_step, decision_notes, created_at, updated_at "
            "FROM governance_approval_requests WHERE entity_type = :entity_type AND entity_id = :entity_id AND status = :status "
            "ORDER BY created_at DESC LIMIT 1"
        ),
        {"entity_type": "ai_system", "entity_id": system_id, "status": "pending"},
    ).fetchone()
    if existing_request:
        _require_approval_request_access(db, str(existing_request[0]), current_user, mutate=True)
        serialized = _serialize_approval_request_row(existing_request)
        return {
            "systemId": system_id,
            "request": serialized,
            "decisions": _fetch_approval_decisions(db, serialized["id"]),
        }

    now = _utc_now_iso()
    workflow_id = _ensure_system_approval_workflow(db, now)

    request_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_approval_requests "
            "(id, workflow_id, entity_type, entity_id, ai_system_id, requested_by, status, current_step, decision_notes, created_at, updated_at) "
            "VALUES (:id, :workflow_id, :entity_type, :entity_id, :ai_system_id, :requested_by, :status, :current_step, :decision_notes, :created_at, :updated_at)"
        ),
        {
            "id": request_id,
            "workflow_id": workflow_id,
            "entity_type": "ai_system",
            "entity_id": system_id,
            "ai_system_id": system_id,
            "requested_by": actor,
            "status": "pending",
            "current_step": 1,
            "decision_notes": "",
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()

    created_request = {
        "id": request_id,
        "workflow_id": workflow_id,
        "entity_type": "ai_system",
        "entity_id": system_id,
        "requested_by": actor,
        "status": "pending",
        "current_step": 1,
        "decision_notes": "",
        "createdAt": now,
        "updatedAt": now,
    }
    return {
        "systemId": system_id,
        "request": created_request,
        "decisions": [],
    }


# ---------------------------------------------------------------------------
# Evidence Hub V2 — item-level CRUD and link management
# ---------------------------------------------------------------------------

def _require_evidence_system_access(
    db: Session,
    system_id: str,
    current_user: TokenData,
    *,
    mutate: bool = False,
) -> OrgMembership:
    return _require_system_access(db, system_id, current_user, mutate=mutate)


def _require_evidence_item_access(
    db: Session,
    evidence_id: str,
    current_user: TokenData,
    *,
    mutate: bool = False,
) -> tuple[str, OrgMembership]:
    row = db.execute(
        text("SELECT system_id FROM governance_evidence WHERE id = :id"),
        {"id": evidence_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Evidence not found")
    system_id = str(row[0])
    return system_id, _require_evidence_system_access(
        db, system_id, current_user, mutate=mutate
    )


def _validate_control_link_scope(
    db: Session,
    membership: OrgMembership,
    system_id: str,
    entity_type: str,
    entity_id: str,
) -> None:
    if entity_type != "control":
        return
    assessment = db.execute(
        text(
            "SELECT id FROM governance_control_assessments "
            "WHERE id = :id AND org_id = :org_id AND system_id = :system_id"
        ),
        {
            "id": entity_id,
            "org_id": membership.org_id,
            "system_id": system_id,
        },
    ).fetchone()
    if not assessment:
        raise HTTPException(status_code=404, detail="Control assessment not found")


def _serialize_evidence_item_v2(row: Any, link_rows: List[Any]) -> Dict[str, Any]:
    """Serialize a full evidence row (V2 schema with title, status, tags, folder)."""
    content = _load_json_value(row[3], {})
    metadata = _load_json_value(row[5], {})
    confidence = float(row[4])
    links = [
        {"id": lr[0], "entityType": lr[1], "entityId": lr[2], "createdAt": lr[3]}
        for lr in link_rows
    ]
    tags = metadata.get("tags") if isinstance(metadata.get("tags"), list) else []
    folder = metadata.get("folder") or ""
    artifact_kind = metadata.get("artifact_kind") or "narrative"
    file_url = metadata.get("file_url") or ""
    file_name = metadata.get("file_name") or ""
    file_size = metadata.get("file_size") or 0
    created_at = row[6] or ""
    # Stale = older than 90 days
    stale = False
    try:
        created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - created_dt).days
        stale = age_days > 90
    except Exception:
        pass
    return {
        "id": row[0],
        "systemId": row[1],
        "type": row[2],
        "title": row[7] or "",
        "source": row[8] or "",
        "status": row[9] or "draft",
        "uploadedBy": row[10] or "",
        "capturedAt": row[11] or created_at,
        "content": content,
        "confidence": confidence,
        "metadata": metadata,
        "tags": tags,
        "folder": folder,
        "artifactKind": artifact_kind,
        "fileUrl": file_url,
        "fileName": file_name,
        "fileSize": file_size,
        "timestamp": created_at,
        "stale": stale,
        "linkedEntityCount": len(links),
        "linkedEntities": links,
        "metadataSummary": _evidence_metadata_summary(metadata, content, len(links), confidence),
        "workflowState": "linked" if links else "collected",
    }


def _fetch_evidence_item_v2(db: Session, evidence_id: str) -> Optional[Dict[str, Any]]:
    row = db.execute(
        text(
            "SELECT id, system_id, evidence_type, content_json, confidence, metadata_json, "
            "created_at, title, source, status, uploaded_by, captured_at "
            "FROM governance_evidence WHERE id = :id"
        ),
        {"id": evidence_id},
    ).fetchone()
    if not row:
        return None
    link_rows = db.execute(
        text(
            "SELECT id, entity_type, entity_id, created_at "
            "FROM governance_evidence_links WHERE evidence_id = :eid ORDER BY created_at DESC"
        ),
        {"eid": evidence_id},
    ).fetchall()
    return _serialize_evidence_item_v2(row, link_rows)


def _fetch_evidence_records_v2(db: Session, system_id: str) -> List[Dict[str, Any]]:
    rows = db.execute(
        text(
            "SELECT id, system_id, evidence_type, content_json, confidence, metadata_json, "
            "created_at, title, source, status, uploaded_by, captured_at "
            "FROM governance_evidence WHERE system_id = :system_id ORDER BY created_at DESC"
        ),
        {"system_id": system_id},
    ).fetchall()
    if not rows:
        return []
    evidence_ids = [r[0] for r in rows]
    # Bulk fetch links
    placeholders = ",".join(f":eid{i}" for i in range(len(evidence_ids)))
    link_rows = db.execute(
        text(
            f"SELECT evidence_id, id, entity_type, entity_id, created_at "
            f"FROM governance_evidence_links WHERE evidence_id IN ({placeholders}) "
            f"ORDER BY created_at DESC"
        ),
        {f"eid{i}": eid for i, eid in enumerate(evidence_ids)},
    ).fetchall()
    links_by_evidence_id: Dict[str, List[Any]] = {}
    for lr in link_rows:
        links_by_evidence_id.setdefault(lr[0], []).append((lr[1], lr[2], lr[3], lr[4]))
    return [
        _serialize_evidence_item_v2(row, links_by_evidence_id.get(row[0], []))
        for row in rows
    ]


class EvidenceUpdateRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    folder: Optional[str] = None
    artifact_kind: Optional[str] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None


class EvidenceLinkItemRequest(BaseModel):
    entity_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)


class EvidenceCollectV2Request(BaseModel):
    system_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    title: Optional[str] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)
    folder: str = ""
    artifact_kind: str = "narrative"
    file_url: str = ""
    file_name: str = ""
    file_size: int = 0
    uploaded_by: Optional[str] = None


@router.get("/evidence-v2/{system_id}")
async def list_evidence_v2(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List evidence for a system with V2 schema (tags, folder, stale, full links)."""
    _ensure_tables(db)
    _require_evidence_system_access(db, system_id, current_user)
    return _fetch_evidence_records_v2(db, system_id)


@router.get("/evidence-item/{evidence_id}")
async def get_evidence_item(
    evidence_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Fetch a single evidence item by ID."""
    _ensure_tables(db)
    _require_evidence_item_access(db, evidence_id, current_user)
    item = _fetch_evidence_item_v2(db, evidence_id)
    if not item:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return item


@router.patch("/evidence-item/{evidence_id}")
async def update_evidence_item(
    evidence_id: str,
    request: EvidenceUpdateRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update evidence title, status, tags, folder, or artifact metadata."""
    _ensure_tables(db)
    _require_evidence_item_access(db, evidence_id, current_user, mutate=True)
    row = db.execute(
        text(
            "SELECT id, metadata_json, content_json "
            "FROM governance_evidence WHERE id = :id"
        ),
        {"id": evidence_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Evidence not found")

    metadata = _load_json_value(row[1], {})
    content = _load_json_value(row[2], {})
    if _has_nonblank_external_url(request.file_url) or (
        request.artifact_kind == "url"
        and _has_nonblank_external_url(content.get("url"))
    ):
        _require_untrusted_external_evidence_linking_enabled()
    if request.tags is not None:
        metadata["tags"] = request.tags
    if request.folder is not None:
        metadata["folder"] = request.folder
    if request.artifact_kind is not None:
        metadata["artifact_kind"] = request.artifact_kind
    if request.file_url is not None:
        metadata["file_url"] = request.file_url
    if request.file_name is not None:
        metadata["file_name"] = request.file_name
    if request.file_size is not None:
        metadata["file_size"] = request.file_size

    updates: Dict[str, Any] = {"id": evidence_id, "metadata_json": json.dumps(metadata)}
    set_clauses = ["metadata_json = :metadata_json"]
    if request.title is not None:
        updates["title"] = request.title
        set_clauses.append("title = :title")
    if request.status is not None:
        updates["status"] = request.status
        set_clauses.append("status = :status")

    db.execute(
        text(f"UPDATE governance_evidence SET {', '.join(set_clauses)} WHERE id = :id"),
        updates,
    )
    db.commit()
    return _fetch_evidence_item_v2(db, evidence_id)


@router.post("/evidence-item/{evidence_id}/links")
async def add_evidence_item_link(
    evidence_id: str,
    request: EvidenceLinkItemRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add a cross-entity link to an evidence item."""
    _ensure_tables(db)
    system_id, membership = _require_evidence_item_access(
        db, evidence_id, current_user, mutate=True
    )
    _require_untrusted_external_evidence_linking_enabled()
    _validate_control_link_scope(
        db, membership, system_id, request.entity_type, request.entity_id
    )
    link_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_evidence_links (id, evidence_id, entity_type, entity_id, created_at) "
            "VALUES (:id, :evidence_id, :entity_type, :entity_id, :created_at)"
        ),
        {
            "id": link_id,
            "evidence_id": evidence_id,
            "entity_type": request.entity_type,
            "entity_id": request.entity_id,
            "created_at": now,
        },
    )
    db.commit()
    return {"id": link_id, "evidenceId": evidence_id, "entityType": request.entity_type, "entityId": request.entity_id, "createdAt": now}


@router.delete("/evidence-item/{evidence_id}/links/{link_id}")
async def remove_evidence_item_link(
    evidence_id: str,
    link_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Remove a cross-entity link from an evidence item."""
    _ensure_tables(db)
    _require_evidence_item_access(db, evidence_id, current_user, mutate=True)
    result = db.execute(
        text("DELETE FROM governance_evidence_links WHERE id = :link_id AND evidence_id = :evidence_id"),
        {"link_id": link_id, "evidence_id": evidence_id},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"deleted": True, "id": link_id}


@router.post("/evidence/collect-v2")
async def collect_evidence_v2(
    request: EvidenceCollectV2Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Collect evidence with V2 schema support (tags, folder, artifact_kind, file_url)."""
    _ensure_tables(db)
    membership = _require_evidence_system_access(
        db, request.system_id, current_user, mutate=True
    )
    _reject_record_only_type(request.type)
    if _requests_external_url_artifact(
        artifact_kind=request.artifact_kind,
        file_url=request.file_url,
        content=request.content,
    ):
        _require_untrusted_external_evidence_linking_enabled()
    evidence_id = str(uuid.uuid4())
    now = _utc_now_iso()
    metadata: Dict[str, Any] = {
        "tags": request.tags,
        "folder": request.folder,
        "artifact_kind": request.artifact_kind,
        "file_url": request.file_url,
        "file_name": request.file_name,
        "file_size": request.file_size,
    }
    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, system_id, org_id, evidence_type, title, content_json, confidence, status, uploaded_by, metadata_json, captured_at, created_at) "
            "VALUES (:id, :system_id, :org_id, :evidence_type, :title, :content_json, :confidence, :status, :uploaded_by, :metadata_json, :captured_at, :created_at)"
        ),
        {
            "id": evidence_id,
            "system_id": request.system_id,
            "org_id": membership.org_id,
            "evidence_type": request.type,
            "title": request.title or "",
            "content_json": json.dumps(request.content),
            "confidence": request.confidence,
            "status": "draft",
            "uploaded_by": current_user.email or current_user.user_id,
            "metadata_json": json.dumps(metadata),
            "captured_at": now,
            "created_at": now,
        },
    )
    db.commit()
    item = _fetch_evidence_item_v2(db, evidence_id)
    return item


@router.post("/evidence/collect")
async def collect_evidence(
    request: EvidenceCollectRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    membership = _require_evidence_system_access(
        db, request.system_id, current_user, mutate=True
    )
    _reject_record_only_type(request.type)
    if _requests_external_url_artifact(
        artifact_kind=request.metadata.get("artifact_kind"),
        file_url=request.metadata.get("file_url"),
        content=request.content,
    ):
        _require_untrusted_external_evidence_linking_enabled()
    # A client cannot declare its own record measured; the gate reads what is left as manual.
    metadata = {k: v for k, v in request.metadata.items() if k not in GATE_PROVENANCE_KEYS}
    evidence_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, system_id, org_id, evidence_type, content_json, confidence, status, uploaded_by, "
            "metadata_json, captured_at, created_at) "
            "VALUES (:id, :system_id, :org_id, :evidence_type, :content_json, :confidence, :status, "
            ":uploaded_by, :metadata_json, :captured_at, :created_at)"
        ),
        {
            "id": evidence_id,
            "system_id": request.system_id,
            "org_id": membership.org_id,
            "evidence_type": request.type,
            "content_json": json.dumps(request.content),
            "confidence": request.confidence,
            "status": "draft",
            "uploaded_by": current_user.email or current_user.user_id,
            "metadata_json": json.dumps(metadata),
            "captured_at": now,
            "created_at": now,
        },
    )
    db.commit()
    return {
        "id": evidence_id,
        "systemId": request.system_id,
        "type": request.type,
        "content": request.content,
        "confidence": request.confidence,
        "metadata": metadata,
        "timestamp": now,
        "linkedEntityCount": 0,
        "linkedEntities": [],
        "metadataSummary": _evidence_metadata_summary(metadata, request.content, 0, request.confidence),
        "workflowState": "collected",
    }


@router.post("/evidence/upload")
async def upload_evidence(
    request: EvidenceCollectRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Alias to keep frontend contract compatibility.
    return await collect_evidence(request, current_user, db)


@router.post("/evidence/collections")
async def link_evidence_to_entity(
    request: EvidenceLinkRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    system_id, membership = _require_evidence_item_access(
        db, request.evidence_id, current_user, mutate=True
    )
    _require_untrusted_external_evidence_linking_enabled()
    _validate_control_link_scope(
        db, membership, system_id, request.entity_type, request.entity_id
    )

    link_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_evidence_links (id, evidence_id, entity_type, entity_id, created_at) "
            "VALUES (:id, :evidence_id, :entity_type, :entity_id, :created_at)"
        ),
        {
            "id": link_id,
            "evidence_id": request.evidence_id,
            "entity_type": request.entity_type,
            "entity_id": request.entity_id,
            "created_at": now,
        },
    )
    db.commit()

    return {
        "id": link_id,
        "evidence_id": request.evidence_id,
        "entity_type": request.entity_type,
        "entity_id": request.entity_id,
        "createdAt": now,
    }


@router.get("/evidence/{system_id}/summary")
async def get_evidence_summary(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_evidence_system_access(db, system_id, current_user)
    records = _fetch_evidence_records(db, system_id)
    return _summarize_evidence(records, system_id)


@router.get("/evidence/{system_id}")
async def list_evidence(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_evidence_system_access(db, system_id, current_user)
    return _fetch_evidence_records(db, system_id)


@router.get("/remediation")
async def list_remediation_tasks(
    system_id: str = Query(min_length=1),
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    rows = db.execute(
        text(
            "SELECT id, system_id, title, description, source_type, source_id, linked_risk_ids_json, "
            "owner, priority, due_date, status, retest_required, retest_status, notes, created_at, updated_at "
            "FROM governance_remediation_tasks WHERE system_id = :system_id "
            "ORDER BY created_at DESC"
        ),
        {"system_id": system_id},
    ).fetchall()
    tasks = [_serialize_remediation_task_row(row) for row in rows]
    return {
        "tasks": tasks,
        "summary": _summarize_remediation_tasks(tasks, system_id),
    }


@router.post("/remediation")
async def create_remediation_task(
    request: RemediationCreateRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, request.system_id, current_user, mutate=True)
    task_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_remediation_tasks "
            "(id, system_id, title, description, source_type, source_id, linked_risk_ids_json, owner, priority, due_date, status, retest_required, retest_status, notes, created_at, updated_at) "
            "VALUES (:id, :system_id, :title, :description, :source_type, :source_id, :linked_risk_ids_json, :owner, :priority, :due_date, :status, :retest_required, :retest_status, :notes, :created_at, :updated_at)"
        ),
        {
            "id": task_id,
            "system_id": request.system_id,
            "title": request.title,
            "description": request.description,
            "source_type": request.source_type,
            "source_id": request.source_id,
            "linked_risk_ids_json": json.dumps(request.linked_risk_ids),
            "owner": request.owner,
            "priority": request.priority,
            "due_date": request.due_date,
            "status": "open",
            "retest_required": 1 if request.retest_required else 0,
            "retest_status": "not_started",
            "notes": request.notes,
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()
    return {
        "id": task_id,
        "systemId": request.system_id,
        "title": request.title,
        "description": request.description,
        "sourceType": request.source_type,
        "sourceId": request.source_id,
        "linkedRiskIds": request.linked_risk_ids,
        "owner": request.owner,
        "priority": request.priority,
        "dueDate": request.due_date,
        "status": "open",
        "retestRequired": request.retest_required,
        "retestStatus": "not_started",
        "notes": request.notes,
        "createdAt": now,
        "updatedAt": now,
    }


def _task_risk_ids(task: Dict[str, Any]) -> set:
    ids = set(task.get("linkedRiskIds") or [])
    if task.get("sourceType") == "risk" and task.get("sourceId"):
        ids.add(task["sourceId"])
    return ids


def _sync_task_findings(db: Session, system_id: str, risk_ids: set) -> None:
    """A finding resolves once no remediation task linked to it is active, and opens again while one is.

    Only open or resolved findings move; one accepted, mitigated or closed stays as set.
    """
    tasks = _fetch_remediation_tasks(db, system_id)
    for risk_id in risk_ids:
        active = any(risk_id in _task_risk_ids(t) and (t.get("status") or "open") in ACTIVE_REMEDIATION_STATUSES for t in tasks)
        db.execute(
            text(
                "UPDATE governance_risks SET status = :status, updated_at = :updated_at "
                "WHERE id = :id AND system_id = :system_id AND status IN ('open', 'resolved') AND status != :status"
            ),
            {"status": "open" if active else "resolved", "updated_at": _utc_now_iso(), "id": risk_id, "system_id": system_id},
        )


@router.patch("/remediation/{task_id}")
async def update_remediation_task(
    task_id: str,
    request: RemediationUpdateRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    row = db.execute(
        text(
            "SELECT id, system_id, title, description, source_type, source_id, linked_risk_ids_json, "
            "owner, priority, due_date, status, retest_required, retest_status, notes, created_at, updated_at "
            "FROM governance_remediation_tasks WHERE id = :id"
        ),
        {"id": task_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Remediation task not found")
    _require_system_access(db, str(row[1]), current_user, mutate=True)

    updates: Dict[str, Any] = {"id": task_id, "updated_at": _utc_now_iso()}
    set_parts: List[str] = []
    if request.status is not None:
        set_parts.append("status = :status")
        updates["status"] = request.status
    if request.notes is not None:
        set_parts.append("notes = :notes")
        updates["notes"] = request.notes
    if not set_parts:
        return _serialize_remediation_task_row(row)

    set_parts.append("updated_at = :updated_at")
    db.execute(
        text(f"UPDATE governance_remediation_tasks SET {', '.join(set_parts)} WHERE id = :id"),
        updates,
    )
    if request.status is not None:
        _sync_task_findings(db, str(row[1]), _task_risk_ids(_serialize_remediation_task_row(row)))
    db.commit()

    updated_row = db.execute(
        text(
            "SELECT id, system_id, title, description, source_type, source_id, linked_risk_ids_json, "
            "owner, priority, due_date, status, retest_required, retest_status, notes, created_at, updated_at "
            "FROM governance_remediation_tasks WHERE id = :id"
        ),
        {"id": task_id},
    ).fetchone()
    if not updated_row:
        raise HTTPException(status_code=404, detail="Remediation task not found")
    return _serialize_remediation_task_row(updated_row)


# ---------------------------------------------------------------------------
# Audit Report Generation & History
# ---------------------------------------------------------------------------

def _ensure_audit_report_table(db: Session) -> None:
    """Create governance_audit_reports table if it does not exist."""
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS governance_audit_reports (
            id TEXT PRIMARY KEY,
            workspace_id TEXT,
            system_id TEXT,
            report_type TEXT NOT NULL,
            title TEXT NOT NULL,
            generated_by TEXT,
            config_json TEXT,
            data_json TEXT,
            created_at TEXT NOT NULL
        )
    """))
    db.commit()


def _serialize_audit_report_row(row: Any) -> Dict[str, Any]:
    config = {}
    data = {}
    try:
        config = json.loads(row.config_json or "{}")
    except Exception:
        pass
    try:
        data = json.loads(row.data_json or "{}")
    except Exception:
        pass
    return {
        "id": row.id,
        "systemId": row.system_id,
        "reportType": row.report_type,
        "title": row.title,
        "generatedBy": row.generated_by,
        "config": config,
        "data": data,
        "createdAt": row.created_at,
    }


class AuditReportGenerateRequest(BaseModel):
    system_id: str
    report_type: str  # compliance | bias | governance
    title: Optional[str] = None
    frameworks: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    sections: Optional[List[str]] = None
    generated_by: Optional[str] = None


@router.post("/reports/generate")
async def generate_audit_report(
    request: AuditReportGenerateRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate and persist a governance audit report snapshot."""
    _ensure_tables(db)
    _ensure_audit_report_table(db)

    system_id = request.system_id
    _require_system_access(db, system_id, current_user, mutate=True)

    # --- collect data snapshot ---
    # Risks
    risk_rows = db.execute(
        text(
            "SELECT id, title, severity, status, description, mitigation, likelihood, risk_score "
            "FROM governance_risks WHERE system_id = :sid"
        ),
        {"sid": system_id},
    ).fetchall()
    risks_data = [
        {
            "id": r.id,
            "title": r.title,
            "severity": r.severity,
            "status": r.status,
            "description": r.description or "",
            "mitigation": r.mitigation or "",
            "likelihood": r.likelihood or "",
            "riskScore": r.risk_score or 0,
        }
        for r in risk_rows
    ]

    # Evidence
    evidence_rows = db.execute(
        text(
            "SELECT id, evidence_type, title, status, confidence, captured_at "
            "FROM governance_evidence WHERE system_id = :sid"
        ),
        {"sid": system_id},
    ).fetchall()
    evidence_data = [
        {
            "id": e.id,
            "type": e.evidence_type,
            "title": e.title or "",
            "status": e.status or "",
            "confidence": e.confidence or 0,
            "capturedAt": e.captured_at or "",
        }
        for e in evidence_rows
    ]

    # Remediation
    remediation_rows = db.execute(
        text(
            "SELECT id, title, status, priority, owner, due_date, created_at, updated_at "
            "FROM governance_remediation_tasks WHERE system_id = :sid"
        ),
        {"sid": system_id},
    ).fetchall()
    remediation_data = [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": t.priority or "",
            "owner": t.owner or "",
            "dueDate": t.due_date or "",
        }
        for t in remediation_rows
    ]

    # Approvals
    approval_rows = db.execute(
        text(
            "SELECT id, status, requested_by, decision_notes, created_at "
            "FROM governance_approval_requests "
            "WHERE entity_type = :entity_type AND entity_id = :sid ORDER BY created_at DESC"
        ),
        {"entity_type": "ai_system", "sid": system_id},
    ).fetchall()
    approvals_data = [
        {
            "id": a.id,
            "status": a.status,
            "requestedBy": a.requested_by or "",
            "decisionNotes": a.decision_notes or "",
            "createdAt": a.created_at,
        }
        for a in approval_rows
    ]

    # System info
    sys_row = db.execute(
        text(
            "SELECT id, name, owner, risk_tier, lifecycle_stage, created_at, updated_at "
            "FROM governance_ai_systems WHERE id = :sid"
        ),
        {"sid": system_id},
    ).fetchone()
    system_data = {}
    if sys_row:
        system_data = {
            "id": sys_row.id,
            "name": sys_row.name,
            "owner": sys_row.owner or "",
            "riskTier": sys_row.risk_tier,
            "lifecycleStage": sys_row.lifecycle_stage,
            "readiness": None,
        }

    from api.routes.fairness_runs import _gate_payload  # function-level: that router imports this one
    from src.application.services.clause_map_service import clause_map, framework_keys

    gate = _gate_payload(db, system_id, sys_row.risk_tier if sys_row else "medium")
    data_snapshot = {
        "system": system_data,
        "risks": risks_data,
        "evidence": evidence_data,
        "remediation": remediation_data,
        "approvals": approvals_data,
        "gate": {"verdict": gate.get("verdict"), "confidence": gate.get("confidence"), "checks": gate.get("checks", []), "reasons": gate.get("reasons", [])},
        "clauseMap": clause_map(gate, frameworks=framework_keys(request.frameworks)),
        "generatedAt": _utc_now_iso(),
    }

    config_snapshot = {
        "frameworks": request.frameworks or [],
        "dateFrom": request.date_from or "",
        "dateTo": request.date_to or "",
        "sections": request.sections or [],
    }

    type_labels = {
        "compliance": "Compliance Audit Report",
        "bias": "Bias Assessment Report",
        "governance": "Governance Summary Report",
    }
    title = request.title or type_labels.get(request.report_type, "Audit Report")

    report_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_audit_reports (id, system_id, report_type, title, generated_by, config_json, data_json, created_at) "
            "VALUES (:id, :system_id, :report_type, :title, :generated_by, :config_json, :data_json, :created_at)"
        ),
        {
            "id": report_id,
            "system_id": system_id,
            "report_type": request.report_type,
            "title": title,
            "generated_by": _authenticated_actor(current_user),
            "config_json": json.dumps(config_snapshot),
            "data_json": json.dumps(data_snapshot),
            "created_at": now,
        },
    )
    db.commit()

    row = db.execute(
        text("SELECT id, system_id, report_type, title, generated_by, config_json, data_json, created_at FROM governance_audit_reports WHERE id = :id"),
        {"id": report_id},
    ).fetchone()
    return _serialize_audit_report_row(row)


@router.get("/reports")
async def list_audit_reports(
    system_id: str = Query(min_length=1),
    report_type: Optional[str] = Query(None),
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List previously generated audit reports."""
    _ensure_tables(db)
    _ensure_audit_report_table(db)
    _require_system_access(db, system_id, current_user)

    conditions = ["system_id = :system_id"]
    params: Dict[str, Any] = {"system_id": system_id}
    if report_type:
        conditions.append("report_type = :report_type")
        params["report_type"] = report_type

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = db.execute(
        text(
            f"SELECT id, system_id, report_type, title, generated_by, config_json, data_json, created_at "
            f"FROM governance_audit_reports {where} ORDER BY created_at DESC LIMIT 50"
        ),
        params,
    ).fetchall()
    return [_serialize_audit_report_row(r) for r in rows]


@router.get("/reports/{report_id}")
async def get_audit_report(
    report_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific audit report with full data snapshot."""
    _ensure_tables(db)
    _ensure_audit_report_table(db)

    row = _require_report_access(db, report_id, current_user)
    return _serialize_audit_report_row(row)
