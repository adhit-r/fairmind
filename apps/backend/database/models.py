"""
Database models for AI BOM system
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

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
