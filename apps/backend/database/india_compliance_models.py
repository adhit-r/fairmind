"""
SQLAlchemy ORM models for India-specific AI compliance
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Enum, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import enum
import uuid

from .connection import Base


class IndiaFrameworkEnum(enum.Enum):
    """Supported India-specific compliance frameworks"""
    DPDP_ACT_2023 = "dpdp_act_2023"
    NITI_AAYOG_PRINCIPLES = "niti_aayog_principles"
    MEITY_GUIDELINES = "meity_guidelines"
    DIGITAL_INDIA_ACT = "digital_india_act"


class ComplianceStatusEnum(enum.Enum):
    """Compliance status values"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    PARTIAL = "partial"


class SeverityLevelEnum(enum.Enum):
    """Severity levels for compliance gaps"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BiasTypeEnum(enum.Enum):
    """Types of bias to detect in Indian context"""
    CASTE_BIAS = "caste_bias"
    RELIGIOUS_BIAS = "religious_bias"
    LINGUISTIC_BIAS = "linguistic_bias"
    REGIONAL_BIAS = "regional_bias"
    GENDER_BIAS = "gender_bias"
    INTERSECTIONAL_BIAS = "intersectional_bias"


class IntegrationStatusEnum(enum.Enum):
    """Integration connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"


# ============================================================================
# India Compliance Evidence Model
# ============================================================================

class IndiaComplianceEvidence(Base):
    """Model for India compliance evidence"""
    __tablename__ = "india_compliance_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    system_id = Column(String(255), nullable=False, index=True)
    control_id = Column(String(50), nullable=False, index=True)
    evidence_type = Column(String(100), nullable=False)
    evidence_data = Column(JSON, nullable=False)
    evidence_hash = Column(String(64), nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String(100), nullable=True, index=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_india_compliance_evidence_system_id', 'system_id'),
        Index('idx_india_compliance_evidence_control_id', 'control_id'),
        Index('idx_india_compliance_evidence_collected_at', 'collected_at'),
        Index('idx_india_compliance_evidence_source', 'source'),
    )

    def __repr__(self):
        return f"<IndiaComplianceEvidence(id={self.id}, system_id={self.system_id}, control_id={self.control_id})>"


# ============================================================================
# India Compliance Results Model
# ============================================================================

class IndiaComplianceResults(Base):
    """Model for India compliance check results"""
    __tablename__ = "india_compliance_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    system_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    framework = Column(Enum(IndiaFrameworkEnum), nullable=False, index=True)
    overall_score = Column(Float, nullable=False)
    status = Column(Enum(ComplianceStatusEnum), nullable=False, index=True)
    requirements_met = Column(Integer, nullable=False)
    total_requirements = Column(Integer, nullable=False)
    evidence_count = Column(Integer, nullable=False, default=0)
    results = Column(JSON, nullable=False)
    gaps = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_india_compliance_results_system_id', 'system_id'),
        Index('idx_india_compliance_results_user_id', 'user_id'),
        Index('idx_india_compliance_results_framework', 'framework'),
        Index('idx_india_compliance_results_status', 'status'),
        Index('idx_india_compliance_results_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f"<IndiaComplianceResults(id={self.id}, system_id={self.system_id}, framework={self.framework.value})>"


# ============================================================================
# India Bias Test Results Model
# ============================================================================

class IndiaBiasTestResults(Base):
    """Model for India-specific bias test results"""
    __tablename__ = "india_bias_test_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    test_id = Column(String(255), unique=True, nullable=False)
    system_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    model_id = Column(String(255), nullable=False, index=True)
    bias_type = Column(Enum(BiasTypeEnum), nullable=False, index=True)
    bias_detected = Column(Boolean, nullable=False)
    severity = Column(Enum(SeverityLevelEnum), nullable=True)
    affected_groups = Column(JSON, nullable=True)
    fairness_metrics = Column(JSON, nullable=False)
    recommendations = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_india_bias_test_results_system_id', 'system_id'),
        Index('idx_india_bias_test_results_user_id', 'user_id'),
        Index('idx_india_bias_test_results_model_id', 'model_id'),
        Index('idx_india_bias_test_results_bias_type', 'bias_type'),
        Index('idx_india_bias_test_results_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f"<IndiaBiasTestResults(id={self.id}, test_id={self.test_id}, bias_type={self.bias_type.value})>"


# ============================================================================
# India Compliance Reports Model
# ============================================================================

class IndiaComplianceReports(Base):
    """Model for India compliance reports"""
    __tablename__ = "india_compliance_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    report_id = Column(String(255), unique=True, nullable=False)
    system_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    frameworks = Column(JSON, nullable=False)
    overall_score = Column(Float, nullable=False)
    report_data = Column(JSON, nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_india_compliance_reports_system_id', 'system_id'),
        Index('idx_india_compliance_reports_user_id', 'user_id'),
        Index('idx_india_compliance_reports_generated_at', 'generated_at'),
    )

    def __repr__(self):
        return f"<IndiaComplianceReports(id={self.id}, report_id={self.report_id}, system_id={self.system_id})>"


# ============================================================================
# Integration Credentials Model
# ============================================================================

class IntegrationCredentials(Base):
    """Model for integration credentials"""
    __tablename__ = "integration_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    integration_name = Column(String(100), nullable=False, index=True)
    credentials = Column(JSON, nullable=False)
    status = Column(Enum(IntegrationStatusEnum), nullable=False, index=True)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_integration_credentials_user_id', 'user_id'),
        Index('idx_integration_credentials_integration_name', 'integration_name'),
        Index('idx_integration_credentials_status', 'status'),
    )

    def __repr__(self):
        return f"<IntegrationCredentials(id={self.id}, user_id={self.user_id}, integration_name={self.integration_name})>"
