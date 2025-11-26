"""
India Compliance Alerting Routes

Provides endpoints for managing India compliance alerts:
- /api/v1/compliance/india/alerts: Get alerts
- /api/v1/compliance/india/alerts/{alert_id}/acknowledge: Acknowledge alert

Requirements: 7.8, 8.8
"""

from fastapi import APIRouter, Query, Path, status
from typing import Optional
import logging

from api.services.india_compliance_alerting import india_compliance_alerting_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/compliance/india/alerts", tags=["india-compliance-alerting"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get Compliance Alerts",
    description="Get India compliance alerts with filtering options",
    responses={
        200: {
            "description": "Alerts retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "alerts": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "alert_type": "compliance_status_change",
                                "severity": "high",
                                "system_id": "system-123",
                                "framework": "dpdp_act_2023",
                                "message": "Compliance status changed for dpdp_act_2023: compliant → non_compliant (score: 85.0% → 72.5%)",
                                "created_at": "2025-01-15T10:30:00Z",
                                "acknowledged": False,
                            },
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440001",
                                "alert_type": "integration_failure",
                                "severity": "critical",
                                "system_id": None,
                                "framework": None,
                                "message": "Integration onetrust failed (3 consecutive failures): Connection timeout",
                                "created_at": "2025-01-15T10:25:00Z",
                                "acknowledged": False,
                            },
                        ],
                        "total": 2,
                        "filters": {
                            "alert_type": None,
                            "severity": None,
                            "system_id": None,
                            "hours": 24,
                        },
                    }
                }
            },
        },
    },
)
async def get_alerts(
    alert_type: Optional[str] = Query(
        None,
        description="Filter by alert type (compliance_status_change, integration_failure, regulatory_update, bias_detected, performance_degradation, evidence_collection_failure, threshold_exceeded)",
    ),
    severity: Optional[str] = Query(
        None,
        description="Filter by severity (critical, high, medium, low, info)",
    ),
    system_id: Optional[str] = Query(None, description="Filter by system ID"),
    hours: int = Query(24, ge=1, le=720, description="Time window in hours"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts"),
):
    """
    Get India compliance alerts.

    Provides:
    - Compliance status change alerts
    - Integration failure alerts
    - Regulatory update alerts
    - Bias detection alerts
    - Performance degradation alerts
    - Evidence collection failure alerts

    Args:
        alert_type: Optional alert type filter
        severity: Optional severity filter
        system_id: Optional system ID filter
        hours: Time window in hours (1-720)
        limit: Maximum number of alerts (1-1000)

    Returns:
        List of alerts with filtering applied

    Requirements: 7.8, 8.8
    """
    try:
        alerts = await india_compliance_alerting_service.get_alerts(
            alert_type=alert_type,
            severity=severity,
            system_id=system_id,
            hours=hours,
            limit=limit,
        )
        return alerts
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}", exc_info=True)
        return {
            "error": str(e),
            "alerts": [],
            "total": 0,
        }


@router.post(
    "/{alert_id}/acknowledge",
    status_code=status.HTTP_200_OK,
    summary="Acknowledge Alert",
    description="Mark an alert as acknowledged",
    responses={
        200: {
            "description": "Alert acknowledged successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Alert acknowledged",
                        "alert_id": "550e8400-e29b-41d4-a716-446655440000",
                    }
                }
            },
        },
        404: {
            "description": "Alert not found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "Alert not found",
                    }
                }
            },
        },
    },
)
async def acknowledge_alert(
    alert_id: str = Path(..., description="Alert ID"),
):
    """
    Acknowledge an alert.

    Marks an alert as acknowledged to indicate it has been reviewed.

    Args:
        alert_id: Alert ID to acknowledge

    Returns:
        Success status

    Requirements: 7.8
    """
    try:
        success = await india_compliance_alerting_service.acknowledge_alert(alert_id)

        if success:
            return {
                "success": True,
                "message": "Alert acknowledged",
                "alert_id": alert_id,
            }
        else:
            return {
                "success": False,
                "error": "Failed to acknowledge alert",
                "alert_id": alert_id,
            }

    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "alert_id": alert_id,
        }
