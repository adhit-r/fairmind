"""
Canonical governance data models for AI system management.

Tables: governance_workspaces, governance_ai_systems, governance_framework_controls,
governance_evidence, governance_evidence_links, governance_approval_workflows,
governance_approval_requests, governance_approval_decisions, governance_policies,
governance_risks, governance_remediation_tasks.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .connection import Base


def _new_id() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RiskTier(str, enum.Enum):
    UNACCEPTABLE = "unacceptable"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


class LifecycleStage(str, enum.Enum):
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    RETIRED = "retired"


class ControlStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    NOT_APPLICABLE = "not_applicable"


class EvidenceStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class PolicyStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING_APPROVAL = "pending_approval"


class RiskSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RemediationStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DEFERRED = "deferred"


class IncidentSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSource(str, enum.Enum):
    BIAS_SCAN = "bias_scan"
    COMPLIANCE_AUDIT = "compliance_audit"
    MONITORING_ALERT = "monitoring_alert"
    MANUAL = "manual"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class GovernanceWorkspace(Base):
    """Tenant-level container (org/team workspace)."""

    __tablename__ = "governance_workspaces"

    id = Column(String, primary_key=True, default=_new_id)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    ai_systems = relationship("GovernanceAISystem", back_populates="workspace", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GovernanceWorkspace(id={self.id}, name={self.name})>"


class GovernanceAISystem(Base):
    """A registered AI system/model within a workspace."""

    __tablename__ = "governance_ai_systems"

    id = Column(String, primary_key=True, default=_new_id)
    workspace_id = Column(String, ForeignKey("governance_workspaces.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    system_type = Column(String, nullable=True)
    version = Column(String, nullable=True)
    owner = Column(String, nullable=True)
    status = Column(String, nullable=True, default="active")
    risk_tier = Column(String, nullable=False, default="minimal")
    lifecycle_stage = Column(String, nullable=False, default="design")
    framework = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    workspace = relationship("GovernanceWorkspace", back_populates="ai_systems")
    evidence_items = relationship("GovernanceEvidence", back_populates="ai_system", cascade="all, delete-orphan")
    risks = relationship("GovernanceRisk", back_populates="ai_system", cascade="all, delete-orphan")
    remediation_tasks = relationship("GovernanceRemediationTask", back_populates="ai_system", cascade="all, delete-orphan")
    incidents = relationship("GovernanceIncident", back_populates="ai_system", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_governance_ai_systems_workspace_id", "workspace_id"),
    )

    def __repr__(self) -> str:
        return f"<GovernanceAISystem(id={self.id}, name={self.name})>"


class GovernanceFrameworkControl(Base):
    """A compliance control row for a specific framework."""

    __tablename__ = "governance_framework_controls"

    id = Column(String, primary_key=True, default=_new_id)
    framework = Column(String, nullable=False, index=True)
    control_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="not_started")
    owner = Column(String, nullable=True)
    evidence_required = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    __table_args__ = (
        Index("idx_governance_fc_framework", "framework"),
        Index("idx_governance_fc_framework_control", "framework", "control_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<GovernanceFrameworkControl(framework={self.framework}, control_id={self.control_id})>"


class GovernanceEvidence(Base):
    """Evidence artifact linked to an AI system."""

    __tablename__ = "governance_evidence"

    id = Column(String, primary_key=True, default=_new_id)
    system_id = Column(String, ForeignKey("governance_ai_systems.id"), nullable=False, index=True)
    control_id = Column(String, nullable=True, index=True)
    evidence_type = Column(String, nullable=False)
    title = Column(String, nullable=True)
    source = Column(String, nullable=True)
    content_json = Column(Text, nullable=False, default="{}")
    confidence = Column(Float, nullable=False, default=1.0)
    status = Column(String, nullable=False, default="draft")
    uploaded_by = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    captured_at = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    ai_system = relationship("GovernanceAISystem", back_populates="evidence_items")
    evidence_links = relationship("GovernanceEvidenceLink", back_populates="evidence", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_governance_evidence_system_id", "system_id"),
        Index("idx_governance_evidence_control_id", "control_id"),
    )

    def __repr__(self) -> str:
        return f"<GovernanceEvidence(id={self.id}, system_id={self.system_id})>"


class GovernanceEvidenceLink(Base):
    """Links evidence to arbitrary governance entities."""

    __tablename__ = "governance_evidence_links"

    id = Column(String, primary_key=True, default=_new_id)
    evidence_id = Column(String, ForeignKey("governance_evidence.id"), nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    evidence = relationship("GovernanceEvidence", back_populates="evidence_links")

    def __repr__(self) -> str:
        return f"<GovernanceEvidenceLink(evidence_id={self.evidence_id}, entity={self.entity_type}:{self.entity_id})>"


class GovernancePolicy(Base):
    """Policy definition tied to a compliance framework."""

    __tablename__ = "governance_policies"

    id = Column(String, primary_key=True, default=_new_id)
    name = Column(String, nullable=False)
    framework = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    rules_json = Column(Text, nullable=False, default="[]")
    status = Column(String, nullable=False, default="draft")
    version = Column(Integer, nullable=False, default=1)
    owner = Column(String, nullable=True)
    reviewer = Column(String, nullable=True)
    approver = Column(String, nullable=True)
    approved_at = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    versions = relationship("GovernancePolicyVersion", back_populates="policy", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GovernancePolicy(id={self.id}, name={self.name})>"


class GovernancePolicyVersion(Base):
    """Snapshot of a policy at a specific version."""

    __tablename__ = "governance_policy_versions"

    id = Column(String, primary_key=True, default=_new_id)
    policy_id = Column(String, ForeignKey("governance_policies.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    framework = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    rules_json = Column(Text, nullable=False, default="[]")
    status = Column(String, nullable=False)
    changed_by = Column(String, nullable=True)
    change_summary = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    policy = relationship("GovernancePolicy", back_populates="versions")

    __table_args__ = (
        Index("idx_gpv_policy_id", "policy_id"),
    )

    def __repr__(self) -> str:
        return f"<GovernancePolicyVersion(policy_id={self.policy_id}, version={self.version})>"


class GovernanceApprovalWorkflow(Base):
    """Approval workflow definition."""

    __tablename__ = "governance_approval_workflows"

    id = Column(String, primary_key=True, default=_new_id)
    name = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    steps_json = Column(Text, nullable=False, default="[]")
    is_active = Column(Integer, nullable=False, default=1)
    created_by = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    requests = relationship("GovernanceApprovalRequest", back_populates="workflow", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GovernanceApprovalWorkflow(id={self.id}, name={self.name})>"


class GovernanceApprovalRequest(Base):
    """An approval request instance tied to a workflow and an entity."""

    __tablename__ = "governance_approval_requests"

    id = Column(String, primary_key=True, default=_new_id)
    workflow_id = Column(String, ForeignKey("governance_approval_workflows.id"), nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False, index=True)
    ai_system_id = Column(String, ForeignKey("governance_ai_systems.id"), nullable=True, index=True)
    requested_by = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    current_step = Column(Integer, nullable=False, default=0)
    decision = Column(String, nullable=True)
    decision_notes = Column(Text, nullable=True)
    decided_by = Column(String, nullable=True)
    decided_at = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    workflow = relationship("GovernanceApprovalWorkflow", back_populates="requests")
    decisions = relationship("GovernanceApprovalDecision", back_populates="request", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GovernanceApprovalRequest(id={self.id}, status={self.status})>"


class GovernanceApprovalDecision(Base):
    """Individual decision record for an approval request."""

    __tablename__ = "governance_approval_decisions"

    id = Column(String, primary_key=True, default=_new_id)
    request_id = Column(String, ForeignKey("governance_approval_requests.id"), nullable=False, index=True)
    decision = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    decided_by = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    request = relationship("GovernanceApprovalRequest", back_populates="decisions")

    def __repr__(self) -> str:
        return f"<GovernanceApprovalDecision(id={self.id}, decision={self.decision})>"


class GovernanceRisk(Base):
    """Risk record linked to an AI system."""

    __tablename__ = "governance_risks"

    id = Column(String, primary_key=True, default=_new_id)
    system_id = Column(String, ForeignKey("governance_ai_systems.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open")
    description = Column(Text, nullable=False, default="")
    mitigation = Column(Text, nullable=False, default="")
    likelihood = Column(String, nullable=False, default="possible")
    risk_score = Column(Float, nullable=False, default=0.0)
    source = Column(String, nullable=False, default="manual")
    categories_json = Column(Text, nullable=False, default="[]")
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    ai_system = relationship("GovernanceAISystem", back_populates="risks")

    def __repr__(self) -> str:
        return f"<GovernanceRisk(id={self.id}, title={self.title})>"


class GovernanceRemediationTask(Base):
    """Remediation task tied to an AI system."""

    __tablename__ = "governance_remediation_tasks"

    id = Column(String, primary_key=True, default=_new_id)
    system_id = Column(String, ForeignKey("governance_ai_systems.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False, default="")
    source_type = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    linked_risk_ids_json = Column(Text, nullable=False, default="[]")
    owner = Column(String, nullable=True)
    priority = Column(String, nullable=False, default="medium")
    due_date = Column(String, nullable=True)
    status = Column(String, nullable=False, default="open")
    retest_required = Column(Integer, nullable=False, default=0)
    retest_status = Column(String, nullable=False, default="not_started")
    notes = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    ai_system = relationship("GovernanceAISystem", back_populates="remediation_tasks")

    def __repr__(self) -> str:
        return f"<GovernanceRemediationTask(id={self.id}, title={self.title})>"


class GovernanceIncident(Base):
    """Governance incident case linked to an AI system."""

    __tablename__ = "governance_incidents"

    id = Column(String, primary_key=True, default=_new_id)
    ai_system_id = Column(String, ForeignKey("governance_ai_systems.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False, default="")
    severity = Column(String, nullable=False, default="medium")
    status = Column(String, nullable=False, default="open")
    source = Column(String, nullable=False, default="manual")
    source_ref_id = Column(String, nullable=True)
    root_cause = Column(Text, nullable=True)
    impact_summary = Column(Text, nullable=True)
    owner = Column(String, nullable=True)
    reporter = Column(String, nullable=True)
    reported_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    resolved_at = Column(String, nullable=True)
    remediation_task_id = Column(String, ForeignKey("governance_remediation_tasks.id"), nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    ai_system = relationship("GovernanceAISystem", back_populates="incidents")
    history = relationship("GovernanceIncidentHistory", back_populates="incident", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_governance_incidents_ai_system_id", "ai_system_id"),
        Index("idx_governance_incidents_severity", "severity"),
        Index("idx_governance_incidents_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<GovernanceIncident(id={self.id}, title={self.title})>"


class GovernanceIncidentHistory(Base):
    """Append-only status change history for incidents."""

    __tablename__ = "governance_incident_history"

    id = Column(String, primary_key=True, default=_new_id)
    incident_id = Column(String, ForeignKey("governance_incidents.id"), nullable=False, index=True)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    changed_by = Column(String, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    incident = relationship("GovernanceIncident", back_populates="history")

    __table_args__ = (
        Index("idx_governance_incident_history_incident_id", "incident_id"),
    )

    def __repr__(self) -> str:
        return f"<GovernanceIncidentHistory(id={self.id}, incident_id={self.incident_id})>"
