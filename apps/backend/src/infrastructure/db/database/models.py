"""
Database models for AI BOM system
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Enum, Boolean, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid

from .connection import Base

class RiskLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceStatus(enum.Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"

class ComponentType(enum.Enum):
    MODEL = "model"
    DATASET = "dataset"
    FRAMEWORK = "framework"
    LIBRARY = "library"
    INFRASTRUCTURE = "infrastructure"
    TOOL = "tool"

class AIBOMDocument(Base):
    """AI BOM Document model"""
    __tablename__ = "ai_bom_documents"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    project_name = Column(String, nullable=False)
    organization = Column(String, nullable=False)
    overall_risk_level = Column(Enum(RiskLevel), nullable=False)
    overall_compliance_status = Column(Enum(ComplianceStatus), nullable=False)
    total_components = Column(Integer, default=0)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    tags = Column(JSON, default=list)
    risk_assessment = Column(JSON, default=dict)
    compliance_report = Column(JSON, default=dict)
    recommendations = Column(JSON, default=list)
    
    # Layer data
    data_layer = Column(JSON, default=dict)
    model_development_layer = Column(JSON, default=dict)
    infrastructure_layer = Column(JSON, default=dict)
    deployment_layer = Column(JSON, default=dict)
    monitoring_layer = Column(JSON, default=dict)
    security_layer = Column(JSON, default=dict)
    compliance_layer = Column(JSON, default=dict)
    
    # Relationships
    components = relationship("AIBOMComponent", back_populates="document", cascade="all, delete-orphan")
    analyses = relationship("AIBOMAnalysis", back_populates="document", cascade="all, delete-orphan")

class AIBOMComponent(Base):
    """AI BOM Component model"""
    __tablename__ = "ai_bom_components"
    
    id = Column(String, primary_key=True, index=True)
    bom_id = Column(String, ForeignKey("ai_bom_documents.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(Enum(ComponentType), nullable=False)
    version = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    vendor = Column(String)
    license = Column(String)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    compliance_status = Column(Enum(ComplianceStatus), nullable=False)
    dependencies = Column(JSON, default=list)
    component_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    document = relationship("AIBOMDocument", back_populates="components")

class AIBOMAnalysis(Base):
    """AI BOM Analysis model"""
    __tablename__ = "ai_bom_analyses"
    
    id = Column(String, primary_key=True, index=True)
    bom_id = Column(String, ForeignKey("ai_bom_documents.id"), nullable=False)
    analysis_type = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False)
    compliance_score = Column(Float, nullable=False)
    security_score = Column(Float, nullable=False)
    performance_score = Column(Float, nullable=False)
    cost_analysis = Column(JSON, default=dict)
    recommendations = Column(JSON, default=list)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    document = relationship("AIBOMDocument", back_populates="analyses")

class AnalyticsSnapshot(Base):
    """Analytics Snapshot model for time-series data"""
    __tablename__ = "analytics_snapshots"

    id = Column(String, primary_key=True, index=True)
    snapshot_date = Column(DateTime, nullable=False, index=True)
    metric_type = Column(String, nullable=False)  # e.g., "bias_score", "compliance_score"
    metric_value = Column(JSON, nullable=False)   # Stores the actual value/distribution
    model_id = Column(String, nullable=True, index=True) # Optional link to specific model
    created_at = Column(DateTime, default=func.now())

class ComplianceSchedule(Base):
    """Compliance Report Schedule model"""
    __tablename__ = "compliance_schedules"

    id = Column(String, primary_key=True, index=True)
    framework = Column(String, nullable=False) # e.g., "EU_AI_ACT", "GDPR"
    frequency = Column(String, nullable=False) # "daily", "weekly", "monthly"
    recipients = Column(JSON, nullable=False)  # List of email strings
    filters = Column(JSON, default=dict)       # Filtering criteria for the report
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

class ComplianceViolation(Base):
    """Compliance Violation model"""
    __tablename__ = "compliance_violations"

    id = Column(String, primary_key=True, index=True)
    model_id = Column(String, nullable=True, index=True)
    framework = Column(String, nullable=False)
    violation_type = Column(String, nullable=False)
    severity = Column(String, nullable=False) # "low", "medium", "high", "critical"
    description = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=func.now())
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)


class User(Base):
    """User model for persistent user storage with Authentik integration"""
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    authentik_id = Column(String, unique=True, index=True, nullable=True)  # Authentik user UUID
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)

    # Roles and permissions from Authentik
    roles = Column(JSON, default=list)  # ["admin", "analyst", "viewer"]
    groups = Column(JSON, default=list)  # Authentik groups
    permissions = Column(JSON, default=list)  # Computed permissions

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified_email = Column(Boolean, default=False)

    # Organization relationships
    primary_org_id = Column(UUID, ForeignKey('organizations.id'), nullable=True, index=True)
    org_id = Column(UUID, ForeignKey('organizations.id'), nullable=True, index=True)

    # Audit trail
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    last_ip = Column(String, nullable=True)

    # Synchronization with Authentik
    last_sync = Column(DateTime, default=func.now())
    authentik_data = Column(JSON, default=dict)  # Store full Authentik user object

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    primary_organization = relationship("Organization", foreign_keys=[primary_org_id], back_populates="primary_users")
    organizations = relationship("Organization", secondary="org_members", back_populates="users")


class AuditLog(Base):
    """Audit Log model for tracking user actions and compliance"""
    __tablename__ = "audit_logs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)  # "login", "export_report", "create_model", etc.
    resource_type = Column(String, nullable=True, index=True)  # "report", "model", "compliance_check"
    resource_id = Column(String, nullable=True, index=True)

    # Additional context
    details = Column(JSON, default=dict)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # Status tracking
    timestamp = Column(DateTime, default=func.now(), index=True)
    status = Column(String, nullable=False, index=True)  # "success", "failure"
    error_message = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class ComplianceRemediationPlan(Base):
    """Compliance Remediation Plan model for tracking remediation workflows"""
    __tablename__ = "compliance_remediation_plans"

    id = Column(String, primary_key=True, index=True)
    framework = Column(String, nullable=False, index=True)  # Compliance framework
    gap_id = Column(String, nullable=False, index=True)  # ID of the compliance gap
    gap_description = Column(String, nullable=False)  # Description of the gap
    model_id = Column(String, nullable=True, index=True)  # Optional model reference

    # Remediation details
    severity = Column(String, nullable=False)  # "critical", "high", "medium", "low"
    remediation_steps = Column(JSON, nullable=False)  # List of remediation steps
    estimated_effort_hours = Column(Float, nullable=True)  # Estimated effort in hours

    # Legal and compliance references
    legal_citations = Column(JSON, default=list)  # List of law/regulation citations
    success_criteria = Column(JSON, default=list)  # Criteria for successful remediation

    # Plan metadata
    generated_by = Column(String, default="ai")  # "ai" or "manual"
    generated_at = Column(DateTime, default=func.now(), index=True)

    # Tracking
    status = Column(String, default="pending")  # "pending", "in_progress", "completed"
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Implementation evidence
    evidence_links = Column(JSON, default=list)  # Links to evidence of remediation
    notes = Column(String, nullable=True)  # Additional notes

    # Timestamps
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())




# Organization RBAC Models

class Organization(Base):
    """Organization model representing a company/entity with users and resources.

    Organizations are the top-level container for multi-tenancy. Each organization
    has an owner, members with different roles, and can define custom roles.
    """
    __tablename__ = "organizations"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    domain = Column(String(255), nullable=True)
    owner_id = Column(UUID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    org_metadata = Column(JSON, default=dict)

    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("OrganizationInvitation", back_populates="organization", cascade="all, delete-orphan")
    roles = relationship("OrganizationRole", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("OrganizationAuditLog", back_populates="organization", cascade="all, delete-orphan")
    primary_users = relationship("User", foreign_keys="User.primary_org_id", back_populates="primary_organization")
    users = relationship("User", secondary="org_members", back_populates="organizations")


class OrganizationMember(Base):
    """Organization member model mapping users to organizations with roles.

    Tracks membership status, roles, and join dates for audit purposes.
    """
    __tablename__ = "org_members"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="member", index=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    invited_by = Column(UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    joined_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=func.now())

    # Ensure one user per org (composite unique constraint handled at DB level)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User")
    inviter = relationship("User", foreign_keys=[invited_by])


class OrganizationInvitation(Base):
    """Organization invitation model for pending member invitations.

    Tracks invitations sent to email addresses with expiration and status.
    """
    __tablename__ = "org_invitations"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="member")
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    invited_by = Column(UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[invited_by])


class OrganizationRole(Base):
    """Custom role model for organization-level permissions.

    Organizations can define custom roles with specific permissions.
    System roles (admin, member, viewer) are marked as such.
    """
    __tablename__ = "org_roles"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, nullable=False, default=list)
    is_system_role = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="roles")


class OrganizationAuditLog(Base):
    """Organization audit log model for tracking org-level changes.

    Logs all changes to organization membership, roles, and settings
    for compliance and security auditing.
    """
    __tablename__ = "org_audit_logs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    org_id = Column(UUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(UUID, nullable=True)
    changes = Column(JSON, default=dict)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="success")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)

    # Relationships
    organization = relationship("Organization", back_populates="audit_logs")
    user = relationship("User")

