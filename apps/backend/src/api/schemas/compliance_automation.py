"""
Compliance Automation API Schemas

Pydantic models for compliance schedule creation, violation tracking,
and remediation planning APIs.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class FrequencyEnum(str, Enum):
    """Schedule frequency options"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class FrameworkEnum(str, Enum):
    """Supported compliance frameworks"""
    DPDP_ACT = "DPDP_ACT_2023"
    NITI_AAYOG = "NITI_AAYOG_PRINCIPLES"
    MEITY_GUIDELINES = "MEITY_GUIDELINES"
    EU_AI_ACT = "EU_AI_ACT"
    GDPR = "GDPR"
    ISO_IEC = "ISO_IEC_42001"
    NIST_AI_RMF = "NIST_AI_RMF"
    IEEE_7000 = "IEEE_7000"


class SeverityEnum(str, Enum):
    """Violation severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ViolationStatusEnum(str, Enum):
    """Violation status"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    IN_REMEDIATION = "in_remediation"
    RESOLVED = "resolved"


# ============================================================================
# SCHEDULE MANAGEMENT SCHEMAS
# ============================================================================

class ScheduleCreateRequest(BaseModel):
    """Request model for creating a compliance schedule"""
    framework: FrameworkEnum
    frequency: FrequencyEnum
    recipients: List[EmailStr] = Field(..., description="Email addresses to receive reports")
    filters: Optional[Dict[str, Any]] = Field(
        default={},
        description="Filtering criteria (model_id, bias_severity, etc.)"
    )
    description: Optional[str] = Field(None, description="Human-readable description")
    is_active: bool = Field(default=True, description="Whether schedule is active")

    class Config:
        schema_extra = {
            "example": {
                "framework": "DPDP_ACT_2023",
                "frequency": "weekly",
                "recipients": ["compliance@example.com", "audit@example.com"],
                "filters": {"bias_severity": "high"},
                "description": "Weekly DPDP compliance report",
                "is_active": True
            }
        }


class ScheduleUpdateRequest(BaseModel):
    """Request model for updating a compliance schedule"""
    frequency: Optional[FrequencyEnum] = None
    recipients: Optional[List[EmailStr]] = None
    filters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        schema_extra = {
            "example": {
                "frequency": "monthly",
                "recipients": ["new-recipient@example.com"]
            }
        }


class ScheduleResponse(BaseModel):
    """Response model for compliance schedule"""
    id: str
    framework: FrameworkEnum
    frequency: FrequencyEnum
    recipients: List[EmailStr]
    filters: Dict[str, Any]
    description: Optional[str]
    is_active: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "schedule-123",
                "framework": "DPDP_ACT_2023",
                "frequency": "weekly",
                "recipients": ["compliance@example.com"],
                "filters": {"bias_severity": "high"},
                "description": "Weekly DPDP compliance report",
                "is_active": True,
                "last_run": "2026-03-20T00:00:00",
                "next_run": "2026-03-27T00:00:00",
                "created_at": "2026-03-15T10:30:00",
                "updated_at": "2026-03-20T00:00:00"
            }
        }


class ScheduleListResponse(BaseModel):
    """Response model for list of schedules"""
    schedules: List[ScheduleResponse]
    total: int
    offset: int
    limit: int


# ============================================================================
# VIOLATION TRACKING SCHEMAS
# ============================================================================

class ViolationResponse(BaseModel):
    """Response model for compliance violation"""
    id: str
    model_id: Optional[str]
    framework: FrameworkEnum
    violation_type: str
    severity: SeverityEnum
    status: ViolationStatusEnum
    description: Optional[str]
    detected_at: datetime
    acknowledged_at: Optional[datetime]
    resolved: bool
    resolved_at: Optional[datetime]
    remediation_plan_id: Optional[str]

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "violation-456",
                "model_id": "model-789",
                "framework": "DPDP_ACT_2023",
                "violation_type": "missing_consent_mechanism",
                "severity": "high",
                "status": "open",
                "description": "Model lacks explicit user consent mechanism",
                "detected_at": "2026-03-20T10:00:00",
                "acknowledged_at": None,
                "resolved": False,
                "resolved_at": None,
                "remediation_plan_id": None
            }
        }


class ViolationAcknowledgeRequest(BaseModel):
    """Request model for acknowledging a violation"""
    notes: Optional[str] = Field(None, description="Acknowledgment notes")


class ViolationListResponse(BaseModel):
    """Response model for list of violations"""
    violations: List[ViolationResponse]
    total: int
    offset: int
    limit: int


class ViolationFilterRequest(BaseModel):
    """Request model for filtering violations"""
    framework: Optional[FrameworkEnum] = None
    severity: Optional[SeverityEnum] = None
    status: Optional[ViolationStatusEnum] = None
    model_id: Optional[str] = None
    offset: int = Field(0, ge=0)
    limit: int = Field(25, ge=1, le=100)


# ============================================================================
# REPORT MANAGEMENT SCHEMAS
# ============================================================================

class ComplianceReportResponse(BaseModel):
    """Response model for compliance report"""
    id: str
    framework: FrameworkEnum
    schedule_id: Optional[str]
    overall_score: float
    status: str
    report_type: str = "pdf"  # pdf, docx, html
    file_path: str
    file_size: int
    generated_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "report-abc",
                "framework": "DPDP_ACT_2023",
                "schedule_id": "schedule-123",
                "overall_score": 85.5,
                "status": "compliant",
                "report_type": "pdf",
                "file_path": "/uploads/reports/dpdp_2026_03_20.pdf",
                "file_size": 245632,
                "generated_at": "2026-03-20T00:15:00",
                "expires_at": "2026-06-20T00:15:00"
            }
        }


class ComplianceReportListResponse(BaseModel):
    """Response model for list of reports"""
    reports: List[ComplianceReportResponse]
    total: int
    offset: int
    limit: int


# ============================================================================
# REMEDIATION SCHEMAS
# ============================================================================

class RemediationStepRequest(BaseModel):
    """Model for a remediation step"""
    step_number: int
    action: str
    description: str
    effort_hours: Optional[float] = None
    owner: Optional[str] = None


class GapRemediationRequest(BaseModel):
    """Request model for getting remediation plan for a gap"""
    framework: FrameworkEnum
    gap_id: str
    model_id: Optional[str] = None


class GapRemediationResponse(BaseModel):
    """Response model for remediation plan"""
    plan_id: str
    framework: FrameworkEnum
    gap_id: str
    gap_description: str
    severity: SeverityEnum
    remediation_steps: List[RemediationStepRequest]
    estimated_effort_hours: float
    legal_citations: List[str]
    success_criteria: List[str]
    generated_by: str = "ai"  # ai or manual
    generated_at: datetime

    class Config:
        schema_extra = {
            "example": {
                "plan_id": "plan-xyz",
                "framework": "DPDP_ACT_2023",
                "gap_id": "gap-001",
                "gap_description": "Missing explicit user consent mechanism",
                "severity": "high",
                "remediation_steps": [
                    {
                        "step_number": 1,
                        "action": "Design consent workflow",
                        "description": "Create user-facing consent form",
                        "effort_hours": 8,
                        "owner": "Frontend Team"
                    },
                    {
                        "step_number": 2,
                        "action": "Implement backend consent tracking",
                        "description": "Add consent records to database",
                        "effort_hours": 12,
                        "owner": "Backend Team"
                    }
                ],
                "estimated_effort_hours": 40,
                "legal_citations": [
                    "DPDP Act Section 6 - Consent Requirements"
                ],
                "success_criteria": [
                    "Explicit user consent required before processing",
                    "Consent logged with timestamp and user ID",
                    "Easy withdrawal mechanism available"
                ],
                "generated_by": "ai",
                "generated_at": "2026-03-20T10:30:00"
            }
        }


class RemediationPlanListResponse(BaseModel):
    """Response model for list of remediation plans"""
    plans: List[GapRemediationResponse]
    total: int
    offset: int
    limit: int


# ============================================================================
# AUTOMATION STATUS SCHEMAS
# ============================================================================

class AutomationStatusResponse(BaseModel):
    """Response model for automation system status"""
    scheduler_running: bool
    active_schedules: int
    pending_jobs: int
    total_violations: int
    critical_violations: int
    reports_generated_today: int
    last_scheduler_check: Optional[datetime]

    class Config:
        schema_extra = {
            "example": {
                "scheduler_running": True,
                "active_schedules": 5,
                "pending_jobs": 2,
                "total_violations": 12,
                "critical_violations": 2,
                "reports_generated_today": 3,
                "last_scheduler_check": "2026-03-20T10:45:00"
            }
        }


# ============================================================================
# ERROR RESPONSES
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "error": "Schedule not found",
                "detail": "No schedule with ID schedule-999 exists",
                "code": "SCHEDULE_NOT_FOUND"
            }
        }
