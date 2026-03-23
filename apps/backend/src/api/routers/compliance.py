"""
Compliance and Audit Report Endpoints

Provides compliance reporting endpoints for audit logs and regulatory documentation.
Supports JSON, CSV, and PDF export formats.

Requires organization admin authorization for all endpoints.
"""

import logging
from datetime import datetime
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config.database import get_db_connection
from config.auth import get_current_active_user, TokenData
from src.services.compliance_report_service import ComplianceReportGenerator

logger = logging.getLogger("fairmind.compliance")
router = APIRouter(prefix="/api/v1/organizations", tags=["compliance"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class ComplianceReportRequest(BaseModel):
    """Request parameters for compliance report generation."""
    start_date: str  # ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ
    end_date: str    # ISO 8601 format
    format: Literal['json', 'csv', 'pdf'] = 'json'
    action_filter: Optional[str] = None
    resource_type_filter: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "start_date": "2026-03-01",
                "end_date": "2026-03-15",
                "format": "pdf",
                "action_filter": None,
                "resource_type_filter": "member"
            }
        }


# ── Helper Functions ─────────────────────────────────────────────────────────

async def _check_org_admin(org_id: str, user_id: str, db) -> bool:
    """Check if user is an admin of the organization."""
    admin = await db.fetch_one(
        "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id AND role IN ('admin', 'owner')",
        {"org_id": org_id, "user_id": user_id}
    )
    return admin is not None


def _parse_iso_date(date_str: str) -> datetime:
    """Parse ISO 8601 date string to datetime."""
    try:
        # Try full datetime format first
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # Try date-only format
        else:
            return datetime.fromisoformat(date_str)
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)")


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/{org_id}/compliance/audit-report")
async def get_org_audit_report(
    org_id: str,
    start_date: str,
    end_date: str,
    format: Literal['json', 'csv', 'pdf'] = 'json',
    request: Request = None,
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Generate organization compliance audit report.

    Requires: Organization admin authorization
    Returns: Compliance report in specified format (JSON, CSV, or PDF)

    Query Parameters:
    - start_date: ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
    - end_date: ISO 8601 format
    - format: Export format (json|csv|pdf), default: json

    Response:
    - JSON: Complete report with metrics and full audit log
    - CSV: File download with tabular audit trail
    - PDF: Professional compliance report document
    """
    try:
        async with get_db_connection() as db:
            # Verify admin authorization
            is_admin = await _check_org_admin(org_id, current_user.user_id, db)
            if not is_admin:
                logger.warning(
                    f"Unauthorized audit report access: user={current_user.user_id}, org={org_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required to view audit reports"
                )

        # Parse dates
        try:
            parsed_start = _parse_iso_date(start_date)
            parsed_end = _parse_iso_date(end_date)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        # Validate date range
        if parsed_start >= parsed_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before end_date"
            )

        if (parsed_end - parsed_start).days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date range cannot exceed 365 days"
            )

        # Generate report
        generator = ComplianceReportGenerator()
        report = await generator.generate_org_audit_report(
            org_id=org_id,
            start_date=parsed_start,
            end_date=parsed_end,
            format=format,
        )

        # Return based on format
        if format == 'json':
            return report
        elif format == 'csv':
            return FileResponse(
                iter([report]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=audit-report-{org_id}-{start_date}.csv"
                }
            )
        elif format == 'pdf':
            return FileResponse(
                iter([report]),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=audit-report-{org_id}-{start_date}.pdf"
                }
            )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in audit report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating audit report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate compliance report"
        )


@router.post("/{org_id}/compliance/audit-report")
async def generate_org_audit_report_post(
    org_id: str,
    payload: ComplianceReportRequest,
    request: Request = None,
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Generate organization compliance audit report (POST alternative).

    Requires: Organization admin authorization
    Returns: Compliance report in specified format (JSON, CSV, or PDF)

    Request Body:
    - start_date: ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
    - end_date: ISO 8601 format
    - format: Export format (json|csv|pdf), default: json
    - action_filter: Optional filter by action type
    - resource_type_filter: Optional filter by resource type

    Response:
    - JSON: Complete report with metrics and full audit log
    - CSV: File download with tabular audit trail
    - PDF: Professional compliance report document
    """
    try:
        async with get_db_connection() as db:
            # Verify admin authorization
            is_admin = await _check_org_admin(org_id, current_user.user_id, db)
            if not is_admin:
                logger.warning(
                    f"Unauthorized audit report access: user={current_user.user_id}, org={org_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required to view audit reports"
                )

        # Parse dates
        try:
            parsed_start = _parse_iso_date(payload.start_date)
            parsed_end = _parse_iso_date(payload.end_date)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        # Validate date range
        if parsed_start >= parsed_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before end_date"
            )

        if (parsed_end - parsed_start).days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date range cannot exceed 365 days"
            )

        # Generate report
        generator = ComplianceReportGenerator()
        report = await generator.generate_org_audit_report(
            org_id=org_id,
            start_date=parsed_start,
            end_date=parsed_end,
            format=payload.format,
            action_filter=payload.action_filter,
            resource_type_filter=payload.resource_type_filter,
        )

        # Return based on format
        if payload.format == 'json':
            return report
        elif payload.format == 'csv':
            return FileResponse(
                iter([report]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=audit-report-{org_id}-{payload.start_date}.csv"
                }
            )
        elif payload.format == 'pdf':
            return FileResponse(
                iter([report]),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=audit-report-{org_id}-{payload.start_date}.pdf"
                }
            )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in audit report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating audit report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate compliance report"
        )
