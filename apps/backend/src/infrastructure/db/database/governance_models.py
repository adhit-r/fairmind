"""
Canonical governance data models for AI system management.

Tables: governance_workspaces, governance_ai_systems, governance_framework_controls,
governance_evidence, governance_evidence_links, governance_approval_workflows,
governance_approval_requests, governance_approval_decisions, governance_policies,
governance_risks, governance_remediation_tasks, governance_audit_reports.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .connection import Base


def _new_id() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _lower_hex64(column: str) -> str:
    """Portable SQLite/PostgreSQL predicate for exactly 64 lower-hex characters."""
    stripped = column
    for character in "0123456789abcdef":
        stripped = f"replace({stripped}, '{character}', '')"
    return f"length({column}) = 64 AND length({stripped}) = 0"


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
    org_id = Column(String, nullable=True, index=True)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    ai_systems = relationship(
        "GovernanceAISystem",
        back_populates="workspace",
        cascade="all, delete-orphan",
        foreign_keys="GovernanceAISystem.workspace_id",
    )

    __table_args__ = (UniqueConstraint("id", "org_id", name="uq_governance_workspace_org"),)

    def __repr__(self) -> str:
        return f"<GovernanceWorkspace(id={self.id}, name={self.name})>"


class GovernanceFrameworkVersion(Base):
    """An immutable version of a governance framework."""

    __tablename__ = "governance_framework_versions"

    id = Column(String, primary_key=True, default=_new_id)
    framework_key = Column(String, nullable=False)
    name = Column(String, nullable=False)
    version_label = Column(String, nullable=False)
    source_hash = Column(String, nullable=False)
    source_filename = Column(String, nullable=False, default="")
    source_uri = Column(Text, nullable=True)
    imported_by = Column(String, nullable=False, default="")
    imported_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    requirements_json = Column(Text, nullable=False, default="[]")
    metadata_json = Column(Text, nullable=False, default="{}")
    status = Column(String, nullable=False, default="draft")
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    __table_args__ = (
        UniqueConstraint(
            "framework_key",
            "version_label",
            "source_hash",
            name="uq_governance_framework_version",
        ),
    )


class GovernanceControlDefinition(Base):
    """A control defined by a specific framework version."""

    __tablename__ = "governance_control_definitions"

    id = Column(String, primary_key=True, default=_new_id)
    framework_version_id = Column(
        String,
        ForeignKey("governance_framework_versions.id"),
        nullable=False,
        index=True,
    )
    external_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    statement = Column(Text, nullable=False)
    parent_requirement_id = Column(String, nullable=False, default="")
    parent_requirement_title = Column(Text, nullable=False, default="")
    principle = Column(String, nullable=False, default="")
    obligation = Column(String, nullable=False, default="")
    application = Column(String, nullable=False, default="")
    frequency = Column(String, nullable=False, default="")
    capabilities_json = Column(Text, nullable=False, default="[]")
    evidence_kind = Column(String, nullable=False, default="")
    evidence_title = Column(Text, nullable=False, default="")
    evidence_guidance = Column(Text, nullable=False, default="")
    evidence_category = Column(String, nullable=False, default="")
    locations_json = Column(Text, nullable=False, default="[]")
    source_cell = Column(String, nullable=False, default="")
    metadata_json = Column(Text, nullable=False, default="{}")
    active = Column(Integer, nullable=False, default=1)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    __table_args__ = (
        UniqueConstraint(
            "framework_version_id",
            "external_id",
            name="uq_governance_control_definition",
        ),
    )


class GovernanceFrameworkAssignment(Base):
    """A framework version assigned to an AI system within an organization."""

    __tablename__ = "governance_framework_assignments"

    id = Column(String, primary_key=True, default=_new_id)
    org_id = Column(String, nullable=False, index=True)
    system_id = Column(
        String,
        ForeignKey("governance_ai_systems.id"),
        nullable=False,
        index=True,
    )
    framework_version_id = Column(
        String,
        ForeignKey("governance_framework_versions.id"),
        nullable=False,
        index=True,
    )
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    __table_args__ = (
        UniqueConstraint("id", "system_id", "org_id", name="uq_governance_assignment_tenant"),
        UniqueConstraint(
            "org_id",
            "system_id",
            "framework_version_id",
            name="uq_governance_framework_assignment",
        ),
        ForeignKeyConstraint(
            ["system_id", "org_id"],
            ["governance_ai_systems.id", "governance_ai_systems.org_id"],
        ),
    )


class GovernanceControlAssessment(Base):
    """The organization-specific assessment state for a control."""

    __tablename__ = "governance_control_assessments"

    id = Column(String, primary_key=True, default=_new_id)
    org_id = Column(String, nullable=False, index=True)
    system_id = Column(
        String,
        ForeignKey("governance_ai_systems.id"),
        nullable=False,
        index=True,
    )
    framework_assignment_id = Column(
        String,
        ForeignKey("governance_framework_assignments.id"),
        nullable=False,
        index=True,
    )
    control_definition_id = Column(
        String,
        ForeignKey("governance_control_definitions.id"),
        nullable=False,
        index=True,
    )
    applicability = Column(String, nullable=False, default="applicable")
    status = Column(String, nullable=False, default="not_started")
    owner = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    __table_args__ = (
        UniqueConstraint("id", "system_id", "org_id", name="uq_governance_assessment_tenant"),
        UniqueConstraint(
            "framework_assignment_id",
            "control_definition_id",
            name="uq_governance_control_assessment",
        ),
        ForeignKeyConstraint(
            ["framework_assignment_id", "system_id", "org_id"],
            [
                "governance_framework_assignments.id",
                "governance_framework_assignments.system_id",
                "governance_framework_assignments.org_id",
            ],
        ),
    )


class GovernanceEvidenceRun(Base):
    """A deduplicated evidence-collection run for an organization."""

    __tablename__ = "governance_evidence_runs"

    id = Column(String, primary_key=True, default=_new_id)
    org_id = Column(String, nullable=False, index=True)
    system_id = Column(
        String,
        ForeignKey("governance_ai_systems.id"),
        nullable=False,
        index=True,
    )
    source_type = Column(String, nullable=False)
    source_identifier = Column(String, nullable=False)
    run_id = Column(String, nullable=False)
    content_hash = Column(String, nullable=False)
    workspace_id = Column(String, nullable=False, index=True)
    passport_id = Column(String, nullable=False, index=True)
    schema_version = Column(String, nullable=False, index=True)
    capability_state = Column(String, nullable=False, index=True)
    assurance_source = Column(String, nullable=False, index=True)
    result = Column(String, nullable=False, default="unknown")
    provenance_json = Column(Text, nullable=False, default="{}")
    artifact_refs_json = Column(Text, nullable=False, default="[]")
    limitations_json = Column(Text, nullable=False, default="[]")
    captured_at = Column(String, nullable=True)
    expires_at = Column(String, nullable=True)
    evidence_id = Column(String, nullable=True, index=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    __table_args__ = (
        UniqueConstraint("id", "system_id", "org_id", name="uq_governance_evidence_run_tenant"),
        UniqueConstraint(
            "id",
            "workspace_id",
            "system_id",
            "org_id",
            name="uq_governance_evidence_run_workspace_tenant",
        ),
        UniqueConstraint(
            "org_id",
            "system_id",
            "source_type",
            "source_identifier",
            "run_id",
            name="uq_governance_evidence_run",
        ),
        ForeignKeyConstraint(
            ["system_id", "org_id"],
            ["governance_ai_systems.id", "governance_ai_systems.org_id"],
        ),
        ForeignKeyConstraint(
            ["workspace_id", "org_id"],
            ["governance_workspaces.id", "governance_workspaces.org_id"],
        ),
        CheckConstraint(
            _lower_hex64("content_hash"), name="ck_governance_evidence_run_content_hash"
        ),
    )


class GovernanceEvidenceArtifact(Base):
    """Ordered immutable metadata pointer for one evidence run artifact."""

    __tablename__ = "governance_evidence_artifacts"

    id = Column(String, primary_key=True, default=_new_id)
    org_id = Column(String, nullable=False, index=True)
    system_id = Column(String, nullable=False, index=True)
    evidence_run_id = Column(String, nullable=False, index=True)
    artifact_id = Column(String, nullable=False)
    ordinal = Column(Integer, nullable=False)
    role = Column(String, nullable=False)
    uri = Column(Text, nullable=False)
    sha256 = Column(String, nullable=False)
    media_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=True)
    contains_sensitive_data = Column(Boolean, nullable=False, default=False)
    retention_policy = Column(String, nullable=True)
    redaction_note = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    __table_args__ = (
        UniqueConstraint(
            "evidence_run_id", "artifact_id", name="uq_governance_evidence_artifact_id"
        ),
        UniqueConstraint(
            "evidence_run_id", "ordinal", name="uq_governance_evidence_artifact_ordinal"
        ),
        CheckConstraint(
            "ordinal >= 0 AND ordinal <= 49", name="ck_governance_evidence_artifact_ordinal"
        ),
        CheckConstraint(
            "size_bytes IS NULL OR size_bytes >= 0", name="ck_governance_evidence_artifact_size"
        ),
        CheckConstraint(_lower_hex64("sha256"), name="ck_governance_evidence_artifact_sha256"),
        ForeignKeyConstraint(
            ["evidence_run_id", "system_id", "org_id"],
            [
                "governance_evidence_runs.id",
                "governance_evidence_runs.system_id",
                "governance_evidence_runs.org_id",
            ],
        ),
    )


class GovernanceEvidencePassportRevision(Base):
    """Append-only complete canonical Evidence Passport snapshot."""

    __tablename__ = "governance_evidence_passport_revisions"

    id = Column(String, primary_key=True, default=_new_id)
    org_id = Column(String, nullable=False, index=True)
    system_id = Column(String, nullable=False, index=True)
    evidence_run_id = Column(String, nullable=False, index=True)
    passport_id = Column(String, nullable=False, index=True)
    passport_revision = Column(Integer, nullable=False)
    previous_revision_hash = Column(String, nullable=True)
    canonical_content_hash = Column(String, nullable=False)
    snapshot_json = Column(Text, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    __table_args__ = (
        UniqueConstraint(
            "id",
            "evidence_run_id",
            "system_id",
            "org_id",
            name="uq_governance_passport_revision_tenant",
        ),
        UniqueConstraint(
            "org_id",
            "passport_id",
            "passport_revision",
            name="uq_governance_passport_revision",
        ),
        UniqueConstraint(
            "evidence_run_id",
            "passport_revision",
            name="uq_governance_passport_run_revision",
        ),
        UniqueConstraint(
            "evidence_run_id",
            "canonical_content_hash",
            name="uq_governance_passport_run_hash",
        ),
        CheckConstraint("passport_revision >= 1", name="ck_governance_passport_revision_positive"),
        CheckConstraint(
            "(passport_revision = 1 AND previous_revision_hash IS NULL) OR "
            f"(passport_revision > 1 AND previous_revision_hash IS NOT NULL AND "
            f"{_lower_hex64('previous_revision_hash')})",
            name="ck_governance_passport_revision_link",
        ),
        CheckConstraint(
            _lower_hex64("canonical_content_hash"),
            name="ck_governance_passport_canonical_hash",
        ),
        ForeignKeyConstraint(
            ["evidence_run_id", "system_id", "org_id"],
            [
                "governance_evidence_runs.id",
                "governance_evidence_runs.system_id",
                "governance_evidence_runs.org_id",
            ],
        ),
    )


class GovernanceEvaluationPlan(Base):
    """Tenant-bound configuration for a versioned evaluation suite."""

    __tablename__ = "governance_evaluation_plans"

    id = Column(String, primary_key=True, default=_new_id)
    org_id = Column(String, nullable=False, index=True)
    workspace_id = Column(String, nullable=False, index=True)
    system_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    target_kind = Column(String, nullable=False)
    lifecycle_phases_json = Column(Text, nullable=False)
    execution_depth = Column(String, nullable=False, default="hybrid")
    enforcement_mode = Column(String, nullable=False, default="human_approval")
    delivery_mode = Column(String, nullable=False)
    suite_refs_json = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="draft")
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=False)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    __table_args__ = (
        UniqueConstraint(
            "id",
            "workspace_id",
            "system_id",
            "org_id",
            name="uq_governance_evaluation_plan_tenant",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "org_id"],
            ["governance_workspaces.id", "governance_workspaces.org_id"],
        ),
        ForeignKeyConstraint(
            ["system_id", "workspace_id", "org_id"],
            [
                "governance_ai_systems.id",
                "governance_ai_systems.workspace_id",
                "governance_ai_systems.org_id",
            ],
        ),
        CheckConstraint(
            "target_kind IN ('predictive_model', 'llm_application', 'agent', "
            "'code_generator', 'image_generator', 'audio_model', 'video_model', "
            "'multimodal_system')",
            name="ck_governance_evaluation_plan_target_kind",
        ),
        CheckConstraint(
            "execution_depth IN ('inline', 'deep', 'hybrid')",
            name="ck_governance_evaluation_plan_execution_depth",
        ),
        CheckConstraint(
            "enforcement_mode IN ('advisory', 'human_approval', 'automatic')",
            name="ck_governance_evaluation_plan_enforcement_mode",
        ),
        CheckConstraint(
            "delivery_mode IN ('fairmind_worker', 'external_provider', 'imported_report')",
            name="ck_governance_evaluation_plan_delivery_mode",
        ),
        CheckConstraint(
            "status IN ('draft', 'active', 'archived')",
            name="ck_governance_evaluation_plan_status",
        ),
        Index("idx_governance_evaluation_plans_scope_status", "org_id", "system_id", "status"),
    )


class GovernanceEvaluationRun(Base):
    """Mutable execution state linked to one exact Evidence Passport revision."""

    __tablename__ = "governance_evaluation_runs"

    id = Column(String, primary_key=True, default=_new_id)
    org_id = Column(String, nullable=False, index=True)
    workspace_id = Column(String, nullable=False, index=True)
    system_id = Column(String, nullable=False, index=True)
    plan_id = Column(String, nullable=False, index=True)
    trigger = Column(String, nullable=False)
    technical_status = Column(String, nullable=False, default="awaiting_evidence")
    overall_verdict = Column(String, nullable=False, default="insufficient")
    layer_verdicts_json = Column(Text, nullable=False, default="{}")
    linked_evidence_run_id = Column(String, nullable=True)
    linked_passport_revision_id = Column(String, nullable=True)
    linked_by = Column(String, nullable=True)
    linked_at = Column(String, nullable=True)
    requested_by = Column(String, nullable=False)
    started_at = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)
    failure_code = Column(String, nullable=True)
    failure_message = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    __table_args__ = (
        UniqueConstraint(
            "id",
            "workspace_id",
            "system_id",
            "org_id",
            name="uq_governance_evaluation_run_tenant",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "org_id"],
            ["governance_workspaces.id", "governance_workspaces.org_id"],
        ),
        ForeignKeyConstraint(
            ["system_id", "workspace_id", "org_id"],
            [
                "governance_ai_systems.id",
                "governance_ai_systems.workspace_id",
                "governance_ai_systems.org_id",
            ],
        ),
        ForeignKeyConstraint(
            ["plan_id", "workspace_id", "system_id", "org_id"],
            [
                "governance_evaluation_plans.id",
                "governance_evaluation_plans.workspace_id",
                "governance_evaluation_plans.system_id",
                "governance_evaluation_plans.org_id",
            ],
        ),
        ForeignKeyConstraint(
            ["linked_evidence_run_id", "workspace_id", "system_id", "org_id"],
            [
                "governance_evidence_runs.id",
                "governance_evidence_runs.workspace_id",
                "governance_evidence_runs.system_id",
                "governance_evidence_runs.org_id",
            ],
        ),
        ForeignKeyConstraint(
            [
                "linked_passport_revision_id",
                "linked_evidence_run_id",
                "system_id",
                "org_id",
            ],
            [
                "governance_evidence_passport_revisions.id",
                "governance_evidence_passport_revisions.evidence_run_id",
                "governance_evidence_passport_revisions.system_id",
                "governance_evidence_passport_revisions.org_id",
            ],
        ),
        CheckConstraint(
            "trigger IN ('manual', 'ci', 'scheduled', 'release_gate', 'incident', "
            "'integration_sync')",
            name="ck_governance_evaluation_run_trigger",
        ),
        CheckConstraint(
            "technical_status IN ('awaiting_evidence', 'running', 'succeeded', "
            "'failed', 'cancelled')",
            name="ck_governance_evaluation_run_technical_status",
        ),
        CheckConstraint(
            "overall_verdict IN ('approved', 'conditional', 'review', 'blocked', "
            "'insufficient')",
            name="ck_governance_evaluation_run_overall_verdict",
        ),
        CheckConstraint(
            "(linked_passport_revision_id IS NULL AND linked_evidence_run_id IS NULL) OR "
            "(linked_passport_revision_id IS NOT NULL AND linked_evidence_run_id IS NOT NULL)",
            name="ck_governance_evaluation_run_complete_passport_link",
        ),
        CheckConstraint(
            "(technical_status = 'succeeded' AND linked_passport_revision_id IS NOT NULL "
            "AND linked_evidence_run_id IS NOT NULL AND linked_by IS NOT NULL "
            "AND linked_at IS NOT NULL AND started_at IS NOT NULL "
            "AND completed_at IS NOT NULL) OR "
            "(technical_status <> 'succeeded' AND linked_passport_revision_id IS NULL "
            "AND linked_evidence_run_id IS NULL AND linked_by IS NULL AND linked_at IS NULL)",
            name="ck_governance_evaluation_run_succeeded_link",
        ),
        CheckConstraint(
            "(technical_status = 'awaiting_evidence' AND started_at IS NULL "
            "AND completed_at IS NULL) OR "
            "(technical_status = 'running' AND started_at IS NOT NULL "
            "AND completed_at IS NULL) OR "
            "(technical_status = 'succeeded' AND started_at IS NOT NULL "
            "AND completed_at IS NOT NULL) OR "
            "(technical_status IN ('failed', 'cancelled') AND completed_at IS NOT NULL)",
            name="ck_governance_evaluation_run_timestamps",
        ),
        Index("idx_governance_evaluation_runs_scope_created", "org_id", "system_id", "created_at"),
        Index(
            "idx_governance_evaluation_runs_status_verdict",
            "org_id",
            "technical_status",
            "overall_verdict",
        ),
    )


class GovernanceControlEvidence(Base):
    """A reviewable mapping between evidence and a control assessment."""

    __tablename__ = "governance_control_evidence"

    id = Column(String, primary_key=True, default=_new_id)
    org_id = Column(String, nullable=False, index=True)
    system_id = Column(
        String,
        ForeignKey("governance_ai_systems.id"),
        nullable=False,
        index=True,
    )
    evidence_id = Column(
        String,
        ForeignKey("governance_evidence_runs.id"),
        nullable=False,
        index=True,
    )
    control_assessment_id = Column(
        String,
        ForeignKey("governance_control_assessments.id"),
        nullable=False,
        index=True,
    )
    state = Column(String, nullable=False, default="candidate")
    mapping_rationale = Column(Text, nullable=True)
    artifact_evidence_id = Column(String, nullable=True, index=True)
    passport_revision_id = Column(String, nullable=True, index=True)
    source_mapping_id = Column(String, nullable=True)
    relation = Column(String, nullable=False, default="supports")
    suggested_by_json = Column(Text, nullable=False, default="{}")
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(String, nullable=True)
    review_history_json = Column(Text, nullable=False, default="[]")
    review_version = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    __table_args__ = (
        UniqueConstraint(
            "evidence_id",
            "control_assessment_id",
            name="uq_governance_control_evidence",
        ),
        UniqueConstraint(
            "evidence_id",
            "source_mapping_id",
            name="uq_governance_control_evidence_source_mapping",
        ),
        ForeignKeyConstraint(
            ["system_id", "org_id"],
            ["governance_ai_systems.id", "governance_ai_systems.org_id"],
        ),
        ForeignKeyConstraint(
            ["evidence_id", "system_id", "org_id"],
            [
                "governance_evidence_runs.id",
                "governance_evidence_runs.system_id",
                "governance_evidence_runs.org_id",
            ],
        ),
        ForeignKeyConstraint(
            ["control_assessment_id", "system_id", "org_id"],
            [
                "governance_control_assessments.id",
                "governance_control_assessments.system_id",
                "governance_control_assessments.org_id",
            ],
        ),
        ForeignKeyConstraint(
            ["passport_revision_id", "evidence_id", "system_id", "org_id"],
            [
                "governance_evidence_passport_revisions.id",
                "governance_evidence_passport_revisions.evidence_run_id",
                "governance_evidence_passport_revisions.system_id",
                "governance_evidence_passport_revisions.org_id",
            ],
        ),
    )


class GovernanceAISystem(Base):
    """A registered AI system/model within a workspace."""

    __tablename__ = "governance_ai_systems"

    id = Column(String, primary_key=True, default=_new_id)
    workspace_id = Column(
        String, ForeignKey("governance_workspaces.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True, index=True)
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
    workspace = relationship(
        "GovernanceWorkspace",
        back_populates="ai_systems",
        foreign_keys=[workspace_id],
    )
    evidence_items = relationship(
        "GovernanceEvidence",
        back_populates="ai_system",
        cascade="all, delete-orphan",
        foreign_keys="GovernanceEvidence.system_id",
    )
    environmental_assessments = relationship(
        "GovernanceEnvironmentalAssessment",
        back_populates="ai_system",
        cascade="all, delete-orphan",
    )
    risks = relationship("GovernanceRisk", back_populates="ai_system", cascade="all, delete-orphan")
    remediation_tasks = relationship(
        "GovernanceRemediationTask", back_populates="ai_system", cascade="all, delete-orphan"
    )
    incidents = relationship(
        "GovernanceIncident", back_populates="ai_system", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_governance_ai_systems_workspace_id", "workspace_id"),
        UniqueConstraint("id", "org_id", name="uq_governance_ai_system_tenant"),
        UniqueConstraint(
            "id",
            "workspace_id",
            "org_id",
            name="uq_governance_ai_system_workspace_tenant",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "org_id"],
            ["governance_workspaces.id", "governance_workspaces.org_id"],
        ),
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
    org_id = Column(String, nullable=True, index=True)
    control_id = Column(String, nullable=True, index=True)
    evidence_type = Column(String, nullable=False)
    title = Column(String, nullable=True)
    source = Column(String, nullable=True)
    content_json = Column(Text, nullable=False, default="{}")
    confidence = Column(Float, nullable=False, default=1.0)
    status = Column(String, nullable=False, default="draft")
    uploaded_by = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    source_run_id = Column(
        String, ForeignKey("governance_evidence_runs.id"), nullable=True, index=True
    )
    captured_at = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    ai_system = relationship(
        "GovernanceAISystem",
        back_populates="evidence_items",
        foreign_keys=[system_id],
    )
    evidence_links = relationship(
        "GovernanceEvidenceLink", back_populates="evidence", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_governance_evidence_system_id", "system_id"),
        Index("idx_governance_evidence_control_id", "control_id"),
        ForeignKeyConstraint(
            ["system_id", "org_id"],
            ["governance_ai_systems.id", "governance_ai_systems.org_id"],
        ),
    )

    def __repr__(self) -> str:
        return f"<GovernanceEvidence(id={self.id}, system_id={self.system_id})>"


class GovernanceEnvironmentalAssessment(Base):
    """Append-only FairMind-E environmental assessment versions."""

    __tablename__ = "governance_environmental_assessments"

    id = Column(String, primary_key=True, default=_new_id)
    system_id = Column(String, ForeignKey("governance_ai_systems.id"), nullable=False, index=True)
    evidence_id = Column(String, ForeignKey("governance_evidence.id"), nullable=True, index=True)
    version = Column(Integer, nullable=False, default=1)
    boundary_json = Column(Text, nullable=False, default="{}")
    period_start = Column(String, nullable=True)
    period_end = Column(String, nullable=True)
    lifecycle_phase = Column(String, nullable=False, default="inference")
    functional_unit = Column(String, nullable=False, default="1000_requests")
    impact_type = Column(String, nullable=False, default="carbon")
    total_kwh = Column(Float, nullable=True)
    total_kg_co2e_location = Column(Float, nullable=True)
    total_kg_co2e_market = Column(Float, nullable=True)
    kg_co2e_per_1000_requests = Column(Float, nullable=True)
    kg_co2e_per_1m_tokens = Column(Float, nullable=True)
    measurement_source = Column(String, nullable=False, default="unknown")
    provenance_class = Column(String, nullable=False, default="unknown")
    uncertainty_pct = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=False, default=0.0)
    intensity_vs_baseline = Column(Float, nullable=True)
    risk_tier = Column(String, nullable=False, default="high")
    recommendation = Column(String, nullable=False, default="no_go")
    mitigation_readiness = Column(String, nullable=False, default="missing")
    mitigations_json = Column(Text, nullable=False, default="[]")
    evidence_refs_json = Column(Text, nullable=False, default="[]")
    controls_json = Column(Text, nullable=False, default="{}")
    blockers_json = Column(Text, nullable=False, default="[]")
    reviewer_state = Column(String, nullable=False, default="draft")
    exception_json = Column(Text, nullable=False, default="{}")
    payload_json = Column(Text, nullable=False, default="{}")
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    ai_system = relationship("GovernanceAISystem", back_populates="environmental_assessments")

    __table_args__ = (
        Index("idx_governance_env_assessments_system_version", "system_id", "version", unique=True),
        Index("idx_governance_env_assessments_recommendation", "recommendation"),
    )

    def __repr__(self) -> str:
        return f"<GovernanceEnvironmentalAssessment(system_id={self.system_id}, version={self.version})>"


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
    versions = relationship(
        "GovernancePolicyVersion", back_populates="policy", cascade="all, delete-orphan"
    )

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

    __table_args__ = (Index("idx_gpv_policy_id", "policy_id"),)

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
    requests = relationship(
        "GovernanceApprovalRequest", back_populates="workflow", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GovernanceApprovalWorkflow(id={self.id}, name={self.name})>"


class GovernanceApprovalRequest(Base):
    """An approval request instance tied to a workflow and an entity."""

    __tablename__ = "governance_approval_requests"

    id = Column(String, primary_key=True, default=_new_id)
    workflow_id = Column(
        String, ForeignKey("governance_approval_workflows.id"), nullable=False, index=True
    )
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
    decisions = relationship(
        "GovernanceApprovalDecision", back_populates="request", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GovernanceApprovalRequest(id={self.id}, status={self.status})>"


class GovernanceApprovalDecision(Base):
    """Individual decision record for an approval request."""

    __tablename__ = "governance_approval_decisions"

    id = Column(String, primary_key=True, default=_new_id)
    request_id = Column(
        String, ForeignKey("governance_approval_requests.id"), nullable=False, index=True
    )
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
    ai_system_id = Column(
        String, ForeignKey("governance_ai_systems.id"), nullable=False, index=True
    )
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
    remediation_task_id = Column(
        String, ForeignKey("governance_remediation_tasks.id"), nullable=True
    )
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    # Relationships
    ai_system = relationship("GovernanceAISystem", back_populates="incidents")
    history = relationship(
        "GovernanceIncidentHistory", back_populates="incident", cascade="all, delete-orphan"
    )

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

    __table_args__ = (Index("idx_governance_incident_history_incident_id", "incident_id"),)

    def __repr__(self) -> str:
        return f"<GovernanceIncidentHistory(id={self.id}, incident_id={self.incident_id})>"


class GovernanceAuditReport(Base):
    """Generated audit reports with config snapshot and export history."""

    __tablename__ = "governance_audit_reports"

    id = Column(String, primary_key=True, default=_new_id)
    workspace_id = Column(String, ForeignKey("governance_workspaces.id"), nullable=True, index=True)
    system_id = Column(String, ForeignKey("governance_ai_systems.id"), nullable=True, index=True)
    report_type = Column(String, nullable=False)  # compliance | bias | governance
    title = Column(String, nullable=False)
    generated_by = Column(String, nullable=True)
    config_json = Column(Text, nullable=True)  # JSON: frameworks, date_range, sections
    data_json = Column(Text, nullable=True)  # Full snapshot of report data at generation time
    created_at = Column(String, nullable=False, default=lambda: _utc_now().isoformat())

    __table_args__ = (
        Index("idx_governance_audit_reports_system_id", "system_id"),
        Index("idx_governance_audit_reports_type", "report_type"),
    )

    def __repr__(self) -> str:
        return f"<GovernanceAuditReport(id={self.id}, type={self.report_type})>"
