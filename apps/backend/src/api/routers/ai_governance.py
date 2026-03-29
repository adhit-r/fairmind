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
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.connection import get_db


router = APIRouter(tags=["ai-governance"])


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

    Base.metadata.create_all(bind=db_manager.engine)
    _tables_ready = True


class PolicyCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    framework: str = Field(min_length=1)
    description: str = ""
    rules: List[Dict[str, Any]] = Field(default_factory=list)


class PolicyUpdateRequest(BaseModel):
    name: Optional[str] = None
    framework: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = Field(default=None, pattern="^(draft|awaiting_approval|approved|rejected|archived)$")


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
    return {
        "id": row[0],
        "workspaceId": row[1],
        "name": row[2],
        "owner": row[3],
        "riskTier": row[4],
        "lifecycleStage": row[5],
        "metadata": _load_json_value(row[6], {}),
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


def _fetch_risk_dashboard_payload(db: Session, system_id: str) -> Dict[str, Any]:
    rows = db.execute(
        text(
            "SELECT id, system_id, title, severity, status, description, mitigation, likelihood, risk_score, source, categories_json, metadata_json, created_at, updated_at "
            "FROM governance_risks WHERE system_id = :system_id ORDER BY risk_score DESC, created_at DESC"
        ),
        {"system_id": system_id},
    ).fetchall()

    stored_risks = [_serialize_risk_row(row) for row in rows]
    automated_risks = _generate_automated_risks(system_id)

    deduped: Dict[str, Dict[str, Any]] = {}
    for risk in stored_risks + automated_risks:
        key = f"{risk['systemId']}::{risk['title'].strip().lower()}"
        if key not in deduped:
            deduped[key] = risk

    risks = sorted(
        deduped.values(),
        key=lambda item: (_severity_rank(item["severity"]), item.get("riskScore", 0.0)),
        reverse=True,
    )
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for risk in risks:
        severity_counts[risk["severity"]] = severity_counts.get(risk["severity"], 0) + 1

    return {
        "risks": risks,
        "summary": {
            "total": len(risks),
            "open": len([risk for risk in risks if risk["status"] != "accepted"]),
            "automated": len([risk for risk in risks if risk.get("source") in {"mit", "ibm"}]),
            "bySeverity": severity_counts,
        },
    }


def _fetch_stored_risk_summary(db: Session, system_id: str) -> Dict[str, Any]:
    rows = db.execute(
        text(
            "SELECT severity, status FROM governance_risks WHERE system_id = :system_id"
        ),
        {"system_id": system_id},
    ).fetchall()
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    open_count = 0
    for row in rows:
        severity = row[0] if row[0] in severity_counts else "medium"
        severity_counts[severity] += 1
        if row[1] != "accepted":
            open_count += 1
    return {
        "total": len(rows),
        "open": open_count,
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
    elif remediation_summary.get("activeTasks", 0) > 0 or remediation_summary.get("byStatus", {}).get("blocked", 0) > 0:
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
    readiness = stage_base.get(stage, 18)
    readiness += min(int(evidence_summary.get("linkedEvidence", 0)) * 6, 18)
    readiness += 14 if evidence_summary.get("decisionReadiness") == "review_ready" else 0
    readiness += 10 if approval_request and approval_request.get("status") == "approved" else 0
    readiness -= int(risk_summary.get("bySeverity", {}).get("critical", 0)) * 18
    readiness -= int(risk_summary.get("bySeverity", {}).get("high", 0)) * 10
    readiness -= int(remediation_summary.get("activeTasks", 0)) * 8
    readiness -= max(0, len(evidence_summary.get("missingSignals", [])) - 1) * 5
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


def _summarize_evidence(records: List[Dict[str, Any]], system_id: str) -> Dict[str, Any]:
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
async def create_workspace(request: WorkspaceCreateRequest, db: Session = Depends(get_db)):
    _ensure_tables(db)
    workspace_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_workspaces (id, name, owner, created_at, updated_at) "
            "VALUES (:id, :name, :owner, :created_at, :updated_at)"
        ),
        {
            "id": workspace_id,
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
async def list_workspaces(db: Session = Depends(get_db)):
    _ensure_tables(db)
    rows = db.execute(
        text(
            "SELECT id, name, owner, created_at, updated_at "
            "FROM governance_workspaces ORDER BY created_at DESC"
        )
    ).fetchall()
    return [_serialize_workspace_row(row) for row in rows]


@router.post("/systems")
async def create_ai_system(request: AISystemCreateRequest, db: Session = Depends(get_db)):
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
            "INSERT INTO governance_ai_systems (id, workspace_id, name, owner, risk_tier, lifecycle_stage, metadata_json, created_at, updated_at) "
            "VALUES (:id, :workspace_id, :name, :owner, :risk_tier, :lifecycle_stage, :metadata_json, :created_at, :updated_at)"
        ),
        {
            "id": system_id,
            "workspace_id": request.workspace_id,
            "name": request.name,
            "owner": request.owner,
            "risk_tier": request.risk_tier,
            "lifecycle_stage": request.lifecycle_stage,
            "metadata_json": json.dumps(request.metadata),
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()
    return {
        "id": system_id,
        "workspaceId": request.workspace_id,
        "name": request.name,
        "owner": request.owner,
        "riskTier": request.risk_tier,
        "lifecycleStage": request.lifecycle_stage,
        "metadata": request.metadata,
        "createdAt": now,
        "updatedAt": now,
    }


@router.get("/systems")
async def list_ai_systems(
    workspace_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    if workspace_id:
        rows = db.execute(
            text(
                "SELECT id, workspace_id, name, owner, risk_tier, lifecycle_stage, metadata_json, created_at, updated_at "
                "FROM governance_ai_systems WHERE workspace_id = :workspace_id ORDER BY created_at DESC"
            ),
            {"workspace_id": workspace_id},
        ).fetchall()
    else:
        rows = db.execute(
            text(
                "SELECT id, workspace_id, name, owner, risk_tier, lifecycle_stage, metadata_json, created_at, updated_at "
                "FROM governance_ai_systems ORDER BY created_at DESC"
            )
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
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    if system_id:
        return _fetch_risk_dashboard_payload(db, system_id)
    else:
        rows = db.execute(
            text(
                "SELECT id, system_id, title, severity, status, description, mitigation, likelihood, risk_score, source, categories_json, metadata_json, created_at, updated_at "
                "FROM governance_risks ORDER BY risk_score DESC, created_at DESC LIMIT 50"
            )
        ).fetchall()

    stored_risks = [_serialize_risk_row(row) for row in rows]
    automated_risks = _generate_automated_risks(system_id or "org-default")

    deduped: Dict[str, Dict[str, Any]] = {}
    for risk in stored_risks + automated_risks:
        key = f"{risk['systemId']}::{risk['title'].strip().lower()}"
        if key not in deduped:
            deduped[key] = risk

    risks = sorted(
        deduped.values(),
        key=lambda item: (_severity_rank(item["severity"]), item.get("riskScore", 0.0)),
        reverse=True,
    )
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for risk in risks:
        severity_counts[risk["severity"]] = severity_counts.get(risk["severity"], 0) + 1

    return {
        "risks": risks,
        "summary": {
            "total": len(risks),
            "open": len([risk for risk in risks if risk["status"] != "accepted"]),
            "automated": len([risk for risk in risks if risk.get("source") in {"mit", "ibm"}]),
            "bySeverity": severity_counts,
        },
    }


@router.post("/risks/assess")
async def assess_risks(request: RiskAssessmentRequest, db: Session = Depends(get_db)):
    _ensure_tables(db)
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


@router.post("/frameworks/{framework}/controls")
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
async def list_system_evidence(system_id: str, db: Session = Depends(get_db)):
    """List all evidence items linked to an AI system."""
    _ensure_tables(db)
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
    db: Session = Depends(get_db),
):
    """Create an evidence item directly linked to an AI system."""
    _ensure_tables(db)
    # Verify AI system exists
    row = db.execute(
        text("SELECT id FROM governance_ai_systems WHERE id = :id"),
        {"id": system_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="AI system not found")

    evidence_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, system_id, control_id, evidence_type, title, source, content_json, "
            "confidence, status, uploaded_by, metadata_json, captured_at, created_at) "
            "VALUES (:id, :system_id, :control_id, :evidence_type, :title, :source, "
            ":content_json, :confidence, :status, :uploaded_by, :metadata_json, :captured_at, :created_at)"
        ),
        {
            "id": evidence_id,
            "system_id": system_id,
            "control_id": request.control_id,
            "evidence_type": request.evidence_type,
            "title": request.title,
            "source": request.source,
            "content_json": json.dumps(request.content),
            "confidence": request.confidence,
            "status": request.status,
            "uploaded_by": request.uploaded_by,
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
        "uploadedBy": request.uploaded_by,
        "capturedAt": request.captured_at or now,
        "createdAt": now,
    }


@router.get("/systems/{system_id}/approvals")
async def list_system_approvals(system_id: str, db: Session = Depends(get_db)):
    """List all approval requests linked to an AI system."""
    _ensure_tables(db)
    rows = db.execute(
        text(
            "SELECT id, workflow_id, entity_type, entity_id, ai_system_id, requested_by, "
            "status, current_step, decision, decision_notes, decided_by, decided_at, created_at, updated_at "
            "FROM governance_approval_requests "
            "WHERE entity_type = 'ai_system' AND entity_id = :system_id "
            "   OR ai_system_id = :system_id "
            "ORDER BY created_at DESC"
        ),
        {"system_id": system_id},
    ).fetchall()
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
    db: Session = Depends(get_db),
):
    """Create an approval request for an AI system, using the default system workflow."""
    _ensure_tables(db)
    # Verify system exists
    system_row = db.execute(
        text("SELECT id FROM governance_ai_systems WHERE id = :id"),
        {"id": system_id},
    ).fetchone()
    if not system_row:
        raise HTTPException(status_code=404, detail="AI system not found")

    # Find or create a default workflow for ai_system entity type
    workflow_row = db.execute(
        text(
            "SELECT id FROM governance_approval_workflows "
            "WHERE entity_type = 'ai_system' AND is_active = 1 LIMIT 1"
        )
    ).fetchone()

    if not workflow_row:
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
                "name": "AI System Release Approval",
                "entity_type": "ai_system",
                "steps_json": json.dumps([
                    {"step": 1, "name": "Technical Review", "approver_role": "tech_lead"},
                    {"step": 2, "name": "Compliance Review", "approver_role": "compliance_officer"},
                    {"step": 3, "name": "Final Approval", "approver_role": "governance_lead"},
                ]),
                "is_active": 1,
                "created_by": "system",
                "created_at": now,
                "updated_at": now,
            },
        )
    else:
        workflow_id = workflow_row[0]

    request_id = str(uuid.uuid4())
    now = _utc_now_iso()
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
            "requested_by": request.requested_by,
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
        "requestedBy": request.requested_by,
        "status": "pending",
        "currentStep": 0,
        "createdAt": now,
        "updatedAt": now,
    }


@router.get("/policies")
async def list_policies(
    framework: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    if framework:
        rows = db.execute(
            text(
                "SELECT id, name, framework, description, rules_json, status, created_at FROM governance_policies "
                "WHERE framework = :framework ORDER BY created_at DESC"
            ),
            {"framework": framework},
        ).fetchall()
    else:
        rows = db.execute(
            text(
                "SELECT id, name, framework, description, rules_json, status, created_at FROM governance_policies "
                "ORDER BY created_at DESC"
            )
        ).fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "framework": row[2],
            "description": row[3] or "",
            "rules": json.loads(row[4]),
            "status": row[5],
            "createdAt": row[6],
        }
        for row in rows
    ]


@router.post("/policies")
async def create_policy(request: PolicyCreateRequest, db: Session = Depends(get_db)):
    _ensure_tables(db)
    policy_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_policies (id, name, framework, description, rules_json, status, created_at, updated_at) "
            "VALUES (:id, :name, :framework, :description, :rules_json, :status, :created_at, :updated_at)"
        ),
        {
            "id": policy_id,
            "name": request.name,
            "framework": request.framework,
            "description": request.description,
            "rules_json": json.dumps(request.rules),
            "status": "draft",
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()

    return {
        "id": policy_id,
        "name": request.name,
        "framework": request.framework,
        "description": request.description,
        "rules": request.rules,
        "status": "draft",
        "createdAt": now,
    }


@router.get("/policies/{policy_id}")
async def get_policy(policy_id: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
    row = db.execute(
        text(
            "SELECT id, name, framework, description, rules_json, status, created_at, updated_at "
            "FROM governance_policies WHERE id = :id"
        ),
        {"id": policy_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Policy not found")

    return {
        "id": row[0],
        "name": row[1],
        "framework": row[2],
        "description": row[3] or "",
        "rules": json.loads(row[4]),
        "status": row[5],
        "createdAt": row[6],
        "updatedAt": row[7],
    }


@router.put("/policies/{policy_id}")
async def update_policy(
    policy_id: str,
    request: PolicyUpdateRequest,
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    existing = db.execute(
        text("SELECT id, status FROM governance_policies WHERE id = :id"),
        {"id": policy_id},
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Policy not found")

    if existing[1] == "approved":
        raise HTTPException(status_code=409, detail="Approved policies are immutable; create a new version")

    updates = {
        "name": request.name,
        "framework": request.framework,
        "description": request.description,
        "rules_json": json.dumps(request.rules) if request.rules is not None else None,
        "status": request.status,
    }
    set_parts = []
    params: Dict[str, Any] = {"id": policy_id, "updated_at": _utc_now_iso()}
    for key, value in updates.items():
        if value is not None:
            set_parts.append(f"{key} = :{key}")
            params[key] = value

    if not set_parts:
        return await get_policy(policy_id, db)

    set_parts.append("updated_at = :updated_at")
    db.execute(
        text(f"UPDATE governance_policies SET {', '.join(set_parts)} WHERE id = :id"),
        params,
    )
    db.commit()
    return await get_policy(policy_id, db)


@router.delete("/policies/{policy_id}")
async def delete_policy(policy_id: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
    result = db.execute(
        text("DELETE FROM governance_policies WHERE id = :id"),
        {"id": policy_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.commit()
    return {"id": policy_id, "deleted": True}


@router.post("/policies/{policy_id}/submit")
async def submit_policy_for_approval(policy_id: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
    now = _utc_now_iso()
    result = db.execute(
        text(
            "UPDATE governance_policies SET status = :status, updated_at = :updated_at "
            "WHERE id = :id"
        ),
        {"status": "awaiting_approval", "updated_at": now, "id": policy_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.commit()
    return {"id": policy_id, "status": "awaiting_approval", "updatedAt": now}


@router.post("/approval-workflows")
async def create_approval_workflow(
    request: ApprovalWorkflowCreateRequest,
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    workflow_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_approval_workflows (id, name, entity_type, steps_json, is_active, created_at, updated_at) "
            "VALUES (:id, :name, :entity_type, :steps_json, :is_active, :created_at, :updated_at)"
        ),
        {
            "id": workflow_id,
            "name": request.name,
            "entity_type": request.entity_type,
            "steps_json": json.dumps(request.steps),
            "is_active": 1,
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
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    workflow = db.execute(
        text("SELECT id FROM governance_approval_workflows WHERE id = :id AND is_active = 1"),
        {"id": workflow_id},
    ).fetchone()
    if not workflow:
        raise HTTPException(status_code=404, detail="Active workflow not found")

    request_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_approval_requests "
            "(id, workflow_id, entity_type, entity_id, requested_by, status, current_step, decision_notes, created_at, updated_at) "
            "VALUES (:id, :workflow_id, :entity_type, :entity_id, :requested_by, :status, :current_step, :decision_notes, :created_at, :updated_at)"
        ),
        {
            "id": request_id,
            "workflow_id": workflow_id,
            "entity_type": request.entity_type,
            "entity_id": request.entity_id,
            "requested_by": request.requested_by,
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


@router.post("/approval-requests/{request_id}/decision")
async def make_approval_decision(
    request_id: str,
    request: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    new_status = "approved" if request.decision == "approved" else "rejected"
    now = _utc_now_iso()
    result = db.execute(
        text(
            "UPDATE governance_approval_requests "
            "SET status = :status, decision_notes = :notes, updated_at = :updated_at "
            "WHERE id = :id"
        ),
        {
            "status": new_status,
            "notes": request.notes,
            "updated_at": now,
            "id": request_id,
        },
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Approval request not found")

    db.execute(
        text(
            "INSERT INTO governance_approval_decisions (id, request_id, decision, notes, decided_by, created_at) "
            "VALUES (:id, :request_id, :decision, :notes, :decided_by, :created_at)"
        ),
        {
            "id": str(uuid.uuid4()),
            "request_id": request_id,
            "decision": new_status,
            "notes": request.notes,
            "decided_by": request.decided_by,
            "created_at": now,
        },
    )

    db.commit()
    return {
        "id": request_id,
        "status": new_status,
        "notes": request.notes,
        "updatedAt": now,
    }


@router.get("/approval-requests/{request_id}")
async def get_approval_request(request_id: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
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
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    if entity_id:
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

    return [_serialize_approval_request_row(row) for row in rows]


@router.get("/approval-requests/{request_id}/decisions")
async def list_approval_decisions(request_id: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
    return _fetch_approval_decisions(db, request_id)


@router.get("/approval/system/{system_id}")
async def get_system_approval_status(system_id: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
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
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    existing_request = db.execute(
        text(
            "SELECT id, workflow_id, entity_type, entity_id, requested_by, status, current_step, decision_notes, created_at, updated_at "
            "FROM governance_approval_requests WHERE entity_type = :entity_type AND entity_id = :entity_id AND status = :status "
            "ORDER BY created_at DESC LIMIT 1"
        ),
        {"entity_type": "ai_system", "entity_id": system_id, "status": "pending"},
    ).fetchone()
    if existing_request:
        serialized = _serialize_approval_request_row(existing_request)
        return {
            "systemId": system_id,
            "request": serialized,
            "decisions": _fetch_approval_decisions(db, serialized["id"]),
        }

    workflow = db.execute(
        text(
            "SELECT id FROM governance_approval_workflows "
            "WHERE entity_type = :entity_type AND is_active = 1 "
            "ORDER BY created_at DESC LIMIT 1"
        ),
        {"entity_type": "ai_system"},
    ).fetchone()

    workflow_id: str
    now = _utc_now_iso()
    if workflow:
        workflow_id = workflow[0]
    else:
        workflow_id = str(uuid.uuid4())
        db.execute(
            text(
                "INSERT INTO governance_approval_workflows (id, name, entity_type, steps_json, is_active, created_at, updated_at) "
                "VALUES (:id, :name, :entity_type, :steps_json, :is_active, :created_at, :updated_at)"
            ),
            {
                "id": workflow_id,
                "name": "AI System Release Approval",
                "entity_type": "ai_system",
                "steps_json": json.dumps(
                    [
                        {"order": 1, "role": "risk_reviewer"},
                        {"order": 2, "role": "approver"},
                    ]
                ),
                "is_active": 1,
                "created_at": now,
                "updated_at": now,
            },
        )

    request_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_approval_requests "
            "(id, workflow_id, entity_type, entity_id, requested_by, status, current_step, decision_notes, created_at, updated_at) "
            "VALUES (:id, :workflow_id, :entity_type, :entity_id, :requested_by, :status, :current_step, :decision_notes, :created_at, :updated_at)"
        ),
        {
            "id": request_id,
            "workflow_id": workflow_id,
            "entity_type": "ai_system",
            "entity_id": system_id,
            "requested_by": request.requested_by,
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
        "requested_by": request.requested_by,
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


@router.post("/evidence/collect")
async def collect_evidence(request: EvidenceCollectRequest, db: Session = Depends(get_db)):
    _ensure_tables(db)
    evidence_id = str(uuid.uuid4())
    now = _utc_now_iso()
    db.execute(
        text(
            "INSERT INTO governance_evidence (id, system_id, evidence_type, content_json, confidence, metadata_json, created_at) "
            "VALUES (:id, :system_id, :evidence_type, :content_json, :confidence, :metadata_json, :created_at)"
        ),
        {
            "id": evidence_id,
            "system_id": request.system_id,
            "evidence_type": request.type,
            "content_json": json.dumps(request.content),
            "confidence": request.confidence,
            "metadata_json": json.dumps(request.metadata),
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
        "metadata": request.metadata,
        "timestamp": now,
        "linkedEntityCount": 0,
        "linkedEntities": [],
        "metadataSummary": _evidence_metadata_summary(request.metadata, request.content, 0, request.confidence),
        "workflowState": "collected",
    }


@router.post("/evidence/upload")
async def upload_evidence(request: EvidenceCollectRequest, db: Session = Depends(get_db)):
    # Alias to keep frontend contract compatibility.
    return await collect_evidence(request, db)


@router.post("/evidence/collections")
async def link_evidence_to_entity(request: EvidenceLinkRequest, db: Session = Depends(get_db)):
    _ensure_tables(db)

    exists = db.execute(
        text("SELECT id FROM governance_evidence WHERE id = :id"),
        {"id": request.evidence_id},
    ).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="Evidence not found")

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
async def get_evidence_summary(system_id: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
    records = _fetch_evidence_records(db, system_id)
    return _summarize_evidence(records, system_id)


@router.get("/evidence/{system_id}")
async def list_evidence(system_id: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
    return _fetch_evidence_records(db, system_id)


@router.get("/remediation")
async def list_remediation_tasks(
    system_id: str = Query(min_length=1),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
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
async def create_remediation_task(request: RemediationCreateRequest, db: Session = Depends(get_db)):
    _ensure_tables(db)
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


@router.patch("/remediation/{task_id}")
async def update_remediation_task(
    task_id: str,
    request: RemediationUpdateRequest,
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
