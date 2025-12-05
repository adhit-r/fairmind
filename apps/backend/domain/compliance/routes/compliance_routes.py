from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from apps.backend.database.connection import get_db
from apps.backend.domain.compliance.services.compliance_automation_service import compliance_automation_service, ComplianceAutomationService

router = APIRouter()

# Pydantic models for request bodies
class ScheduleCreateRequest(BaseModel):
    framework: str
    frequency: str
    recipients: List[str]
    filters: Dict[str, Any] = {}

class ViolationCheckRequest(BaseModel):
    model_id: str

def get_compliance_service() -> ComplianceAutomationService:
    return compliance_automation_service

@router.post("/schedules", response_model=Dict[str, Any])
async def create_schedule(
    request: ScheduleCreateRequest,
    db: Session = Depends(get_db),
    service: ComplianceAutomationService = Depends(get_compliance_service)
):
    """Create a new compliance report schedule"""
    schedule = await service.create_schedule(
        db,
        request.framework,
        request.frequency,
        request.recipients,
        request.filters
    )
    return {
        "id": schedule.id,
        "framework": schedule.framework,
        "frequency": schedule.frequency,
        "next_run": schedule.next_run
    }

@router.get("/schedules", response_model=List[Dict[str, Any]])
async def list_schedules(
    db: Session = Depends(get_db),
    service: ComplianceAutomationService = Depends(get_compliance_service)
):
    """List all active compliance schedules"""
    schedules = await service.list_schedules(db)
    return [
        {
            "id": s.id,
            "framework": s.framework,
            "frequency": s.frequency,
            "recipients": s.recipients,
            "last_run": s.last_run,
            "next_run": s.next_run,
            "is_active": s.is_active
        }
        for s in schedules
    ]

@router.post("/check", response_model=List[Dict[str, Any]])
async def check_compliance(
    request: ViolationCheckRequest,
    db: Session = Depends(get_db),
    service: ComplianceAutomationService = Depends(get_compliance_service)
):
    """Manually trigger a compliance check for a model"""
    violations = await service.check_compliance_violations(db, request.model_id)
    return [
        {
            "id": v.id,
            "violation_type": v.violation_type,
            "severity": v.severity,
            "description": v.description,
            "detected_at": v.detected_at
        }
        for v in violations
    ]

@router.get("/violations", response_model=List[Dict[str, Any]])
async def list_violations(
    db: Session = Depends(get_db),
    service: ComplianceAutomationService = Depends(get_compliance_service)
):
    """List all unresolved compliance violations"""
    violations = await service.list_violations(db)
    return [
        {
            "id": v.id,
            "model_id": v.model_id,
            "framework": v.framework,
            "violation_type": v.violation_type,
            "severity": v.severity,
            "description": v.description,
            "detected_at": v.detected_at
        }
        for v in violations
    ]
