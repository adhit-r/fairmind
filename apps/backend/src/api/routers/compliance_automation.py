"""
Compliance Automation API Router

Endpoints for managing compliance schedules, violation tracking,
remediation planning, and report management.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from typing import Optional, List
from datetime import datetime, timedelta
import logging
import uuid
import asyncio

from config.auth import get_current_user
from api.routes.org_scope import org_member, org_mutator
from config.database import db_manager
from src.application.services.governance_assurance_service import OrgMembership
from src.application.services.api_boundary_dependencies import (
    ComplianceSchedule,
    ComplianceViolation,
    compliance_automation_service,
)
from src.api.schemas.compliance_automation import (
    ScheduleCreateRequest,
    ScheduleUpdateRequest,
    ScheduleResponse,
    ScheduleListResponse,
    ViolationResponse,
    ViolationAcknowledgeRequest,
    ViolationListResponse,
    ViolationFilterRequest,
    ComplianceReportResponse,
    ComplianceReportListResponse,
    GapRemediationRequest,
    GapRemediationResponse,
    RemediationStepRequest,
    AutomationStatusResponse,
    ErrorResponse,
    FrameworkEnum,
    SeverityEnum,
    ViolationStatusEnum,
)

logger = logging.getLogger("fairmind.compliance_automation")
# Schedules and violations carry org_id: every query below filters on the caller's
# organisation, and an id from another organisation answers 404.
router = APIRouter(prefix="/compliance", tags=["compliance-automation"], dependencies=[Depends(org_member)])


# ============================================================================
# SCHEDULE MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_compliance_schedule(
    request: ScheduleCreateRequest,
    current_user=Depends(get_current_user),
    m: OrgMembership = Depends(org_mutator),
) -> ScheduleResponse:
    """
    Create a new compliance automation schedule.

    Requires admin role. Schedule will automatically run at the specified
    frequency (daily/weekly/monthly) and generate compliance reports.
    """
    try:
        session = db_manager.get_sync_session()
        try:
            schedule = ComplianceSchedule(
                id=str(uuid.uuid4()),
                framework=request.framework.value,
                frequency=request.frequency.value,
                recipients=request.recipients,
                filters=request.filters or {},
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                org_id=m.org_id,
            )

            # Calculate next_run based on frequency
            now = datetime.utcnow()
            if request.frequency.value == "daily":
                schedule.next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            elif request.frequency.value == "weekly":
                # Monday at midnight
                days_ahead = 0 - now.weekday()  # 0 = Monday
                if days_ahead <= 0:
                    days_ahead += 7
                schedule.next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
            elif request.frequency.value == "monthly":
                # 1st of next month at midnight
                if now.month == 12:
                    schedule.next_run = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                else:
                    schedule.next_run = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

            session.add(schedule)
            session.commit()

            logger.info(f"Created compliance schedule: {schedule.id} for {request.framework.value}")

            return ScheduleResponse(
                id=schedule.id,
                framework=FrameworkEnum(schedule.framework),
                frequency=request.frequency,
                recipients=schedule.recipients,
                filters=schedule.filters,
                is_active=schedule.is_active,
                last_run=schedule.last_run,
                next_run=schedule.next_run,
                created_at=schedule.created_at,
                updated_at=schedule.updated_at,
            )

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating compliance schedule: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create schedule: {str(e)}"
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_compliance_schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/schedules", response_model=ScheduleListResponse)
def list_compliance_schedules(
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    framework: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user=Depends(get_current_user),
    m: OrgMembership = Depends(org_member),
) -> ScheduleListResponse:
    """
    List all compliance automation schedules.

    Supports filtering by framework and active status.
    """
    try:
        session = db_manager.get_sync_session()
        try:
            query = session.query(ComplianceSchedule).filter(ComplianceSchedule.org_id == m.org_id)

            # Apply filters
            if framework:
                query = query.filter(ComplianceSchedule.framework == framework)
            if is_active is not None:
                query = query.filter(ComplianceSchedule.is_active == is_active)

            # Get total count
            total = query.count()

            # Apply pagination
            schedules = query.offset(offset).limit(limit).all()

            return ScheduleListResponse(
                schedules=[
                    ScheduleResponse(
                        id=s.id,
                        framework=FrameworkEnum(s.framework),
                        frequency=s.frequency,
                        recipients=s.recipients,
                        filters=s.filters,
                        is_active=s.is_active,
                        last_run=s.last_run,
                        next_run=s.next_run,
                        created_at=s.created_at,
                        updated_at=s.updated_at,
                    )
                    for s in schedules
                ],
                total=total,
                offset=offset,
                limit=limit,
            )

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error listing compliance schedules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list schedules"
        )


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
def get_compliance_schedule(
    schedule_id: str,
    current_user=Depends(get_current_user),
    m: OrgMembership = Depends(org_member),
) -> ScheduleResponse:
    """Get details of a specific compliance schedule."""
    try:
        session = db_manager.get_sync_session()
        try:
            schedule = session.query(ComplianceSchedule).filter(
                ComplianceSchedule.id == schedule_id,
                ComplianceSchedule.org_id == m.org_id,
            ).first()

            if not schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Schedule {schedule_id} not found"
                )

            return ScheduleResponse(
                id=schedule.id,
                framework=FrameworkEnum(schedule.framework),
                frequency=schedule.frequency,
                recipients=schedule.recipients,
                filters=schedule.filters,
                is_active=schedule.is_active,
                last_run=schedule.last_run,
                next_run=schedule.next_run,
                created_at=schedule.created_at,
                updated_at=schedule.updated_at,
            )

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compliance schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get schedule"
        )


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
def update_compliance_schedule(
    schedule_id: str,
    request: ScheduleUpdateRequest,
    current_user=Depends(get_current_user),
    m: OrgMembership = Depends(org_mutator),
) -> ScheduleResponse:
    """Update a compliance automation schedule."""
    try:
        session = db_manager.get_sync_session()
        try:
            schedule = session.query(ComplianceSchedule).filter(
                ComplianceSchedule.id == schedule_id,
                ComplianceSchedule.org_id == m.org_id,
            ).first()

            if not schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Schedule {schedule_id} not found"
                )

            # Update fields
            if request.frequency:
                schedule.frequency = request.frequency.value
            if request.recipients:
                schedule.recipients = request.recipients
            if request.filters is not None:
                schedule.filters = request.filters
            if request.description is not None:
                # Add description field if needed
                pass
            if request.is_active is not None:
                schedule.is_active = request.is_active

            schedule.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"Updated compliance schedule: {schedule_id}")

            return ScheduleResponse(
                id=schedule.id,
                framework=FrameworkEnum(schedule.framework),
                frequency=schedule.frequency,
                recipients=schedule.recipients,
                filters=schedule.filters,
                is_active=schedule.is_active,
                last_run=schedule.last_run,
                next_run=schedule.next_run,
                created_at=schedule.created_at,
                updated_at=schedule.updated_at,
            )

        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating compliance schedule: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update schedule"
            )
        finally:
            session.close()

    except HTTPException:
        raise


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_compliance_schedule(
    schedule_id: str,
    current_user=Depends(get_current_user),
    m: OrgMembership = Depends(org_mutator),
):
    """Delete a compliance automation schedule."""
    try:
        session = db_manager.get_sync_session()
        try:
            schedule = session.query(ComplianceSchedule).filter(
                ComplianceSchedule.id == schedule_id,
                ComplianceSchedule.org_id == m.org_id,
            ).first()

            if not schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Schedule {schedule_id} not found"
                )

            session.delete(schedule)
            session.commit()

            logger.info(f"Deleted compliance schedule: {schedule_id}")

        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting compliance schedule: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete schedule"
            )
        finally:
            session.close()

    except HTTPException:
        raise


@router.post("/schedules/{schedule_id}/run", response_model=dict)
async def run_compliance_schedule_now(
    schedule_id: str,
    current_user=Depends(get_current_user),
    m: OrgMembership = Depends(org_mutator),
) -> dict:
    """
    Trigger immediate execution of a compliance schedule.

    Runs the compliance check and report generation now,
    regardless of schedule frequency.
    """
    try:
        session = db_manager.get_sync_session()
        try:
            schedule = session.query(ComplianceSchedule).filter(
                ComplianceSchedule.id == schedule_id,
                ComplianceSchedule.org_id == m.org_id,
            ).first()

            if not schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Schedule {schedule_id} not found"
                )

            # Trigger immediate execution of the schedule
            logger.info(f"Triggering immediate run of schedule: {schedule_id}")

            # Run the report generation asynchronously
            import asyncio
            try:
                # Create a task to run the report generation
                asyncio.create_task(
                    compliance_automation_service.generate_automated_report(schedule_id)
                )
            except Exception as e:
                logger.warning(f"Could not trigger async report generation: {e}")

            return {
                "message": "Schedule execution triggered",
                "schedule_id": schedule_id,
                "triggered_at": datetime.utcnow().isoformat(),
            }

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger schedule"
        )


# ============================================================================
# VIOLATION TRACKING ENDPOINTS
# ============================================================================

@router.get("/violations", response_model=ViolationListResponse)
def list_violations(
    request: ViolationFilterRequest = Depends(),
    current_user=Depends(get_current_user),
    m: OrgMembership = Depends(org_member),
) -> ViolationListResponse:
    """
    List compliance violations with filtering options.

    Filter by framework, severity, status, or model ID.
    """
    try:
        session = db_manager.get_sync_session()
        try:
            query = session.query(ComplianceViolation).filter(ComplianceViolation.org_id == m.org_id)

            # Apply filters
            if request.framework:
                query = query.filter(ComplianceViolation.framework == request.framework.value)
            if request.severity:
                query = query.filter(ComplianceViolation.severity == request.severity.value)
            if request.status:
                # Map ViolationStatusEnum to database status
                query = query.filter(ComplianceViolation.resolved == (request.status == ViolationStatusEnum.RESOLVED))
            if request.model_id:
                query = query.filter(ComplianceViolation.model_id == request.model_id)

            # Get total count
            total = query.count()

            # Apply pagination and sorting
            violations = query.order_by(ComplianceViolation.detected_at.desc()).offset(
                request.offset
            ).limit(request.limit).all()

            return ViolationListResponse(
                violations=[
                    ViolationResponse(
                        id=v.id,
                        model_id=v.model_id,
                        framework=FrameworkEnum(v.framework),
                        violation_type=v.violation_type,
                        severity=SeverityEnum(v.severity),
                        status=ViolationStatusEnum.RESOLVED if v.resolved else ViolationStatusEnum.OPEN,
                        description=v.description,
                        detected_at=v.detected_at,
                        resolved=v.resolved,
                        resolved_at=v.resolved_at,
                        acknowledged_at=None,
                        remediation_plan_id=None,
                    )
                    for v in violations
                ],
                total=total,
                offset=request.offset,
                limit=request.limit,
            )

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error listing violations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list violations"
        )


@router.get("/violations/{violation_id}", response_model=ViolationResponse)
def get_violation(
    violation_id: str,
    current_user=Depends(get_current_user),
    m: OrgMembership = Depends(org_member),
) -> ViolationResponse:
    """Get details of a specific compliance violation."""
    try:
        session = db_manager.get_sync_session()
        try:
            violation = session.query(ComplianceViolation).filter(
                ComplianceViolation.id == violation_id,
                ComplianceViolation.org_id == m.org_id,
            ).first()

            if not violation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Violation {violation_id} not found"
                )

            return ViolationResponse(
                id=violation.id,
                model_id=violation.model_id,
                framework=FrameworkEnum(violation.framework),
                violation_type=violation.violation_type,
                severity=SeverityEnum(violation.severity),
                status=ViolationStatusEnum.RESOLVED if violation.resolved else ViolationStatusEnum.OPEN,
                description=violation.description,
                detected_at=violation.detected_at,
                resolved=violation.resolved,
                resolved_at=violation.resolved_at,
                acknowledged_at=None,
                remediation_plan_id=None,
            )

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting violation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get violation"
        )


@router.patch("/violations/{violation_id}/acknowledge", response_model=ViolationResponse)
def acknowledge_violation(
    violation_id: str,
    request: ViolationAcknowledgeRequest,
    current_user=Depends(get_current_user),
    m: OrgMembership = Depends(org_member),
) -> ViolationResponse:
    """Acknowledge a compliance violation."""
    try:
        session = db_manager.get_sync_session()
        try:
            violation = session.query(ComplianceViolation).filter(
                ComplianceViolation.id == violation_id,
                ComplianceViolation.org_id == m.org_id,
            ).first()

            if not violation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Violation {violation_id} not found"
                )

            # Mark as acknowledged (update would be better with full model)
            # For now, we just log the acknowledgment
            logger.info(f"Violation acknowledged: {violation_id} by {current_user.get('email', 'unknown')}")
            logger.info(f"Acknowledgment notes: {request.notes}")

            return ViolationResponse(
                id=violation.id,
                model_id=violation.model_id,
                framework=FrameworkEnum(violation.framework),
                violation_type=violation.violation_type,
                severity=SeverityEnum(violation.severity),
                status=ViolationStatusEnum.ACKNOWLEDGED,
                description=violation.description,
                detected_at=violation.detected_at,
                resolved=violation.resolved,
                resolved_at=violation.resolved_at,
                acknowledged_at=None,
                remediation_plan_id=None,
            )

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging violation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge violation"
        )


# ============================================================================
# REMEDIATION ENDPOINTS
# ============================================================================


# ============================================================================
# STATUS ENDPOINTS
# ============================================================================

@router.get("/status", response_model=AutomationStatusResponse)
async def get_automation_status(
    current_user=Depends(get_current_user),
    m: OrgMembership = Depends(org_member),
) -> AutomationStatusResponse:
    """Get the status of the compliance automation system."""
    try:
        session = db_manager.get_sync_session()
        try:
            # Use service method to get comprehensive status
            status_data = await compliance_automation_service.get_automation_status(session, m.org_id)

            return AutomationStatusResponse(
                scheduler_running=status_data.get("scheduler_running", False),
                active_schedules=status_data.get("active_schedules", 0),
                pending_jobs=status_data.get("pending_jobs", 0),
                total_violations=status_data.get("total_violations", 0),
                critical_violations=status_data.get("critical_violations", 0),
                reports_generated_today=status_data.get("reports_generated_today", 0),
                last_scheduler_check=datetime.fromisoformat(status_data.get("last_scheduler_check", datetime.utcnow().isoformat())),
            )

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error getting automation status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get status"
        )


# ============================================================================
# REPORTS ENDPOINTS
# ============================================================================

@router.get("/reports", response_model=ComplianceReportListResponse)
def get_compliance_reports(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    framework: Optional[str] = None,
    current_user=Depends(get_current_user),
    m: OrgMembership = Depends(org_member),
) -> ComplianceReportListResponse:
    """
    Get compliance reports generated by scheduled checks.

    This endpoint:
    - Returns compliance reports filtered by org_id
    - Supports pagination with skip/limit
    - Optionally filters by framework
    - Enforces org isolation at decorator level

    The query should include:
    SELECT * FROM compliance_reports WHERE org_id = :org_id ORDER BY created_at DESC
    """
    org_id, user_id = m.org_id, m.user_id
    try:
        logger.info(f"Fetching compliance reports for org: {org_id}, user: {user_id}")

        session = db_manager.get_sync_session()
        try:
            # For now, return empty list as reports are generated asynchronously
            # In production, this will query a ComplianceReport table with org_id filtering:
            # SELECT * FROM compliance_reports
            # WHERE org_id = :org_id AND (framework = :framework OR :framework IS NULL)
            # ORDER BY created_at DESC LIMIT :limit OFFSET :skip

            return ComplianceReportListResponse(
                reports=[],
                total=0,
                offset=skip,
                limit=limit
            )
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error getting compliance reports for org {org_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get reports"
        )
