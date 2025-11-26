"""
India Compliance Metrics Routes

Provides endpoints for retrieving India compliance metrics:
- /api/v1/compliance/india/metrics/compliance-checks: Compliance check metrics
- /api/v1/compliance/india/metrics/integrations: Integration metrics
- /api/v1/compliance/india/metrics/ai-automation: AI automation metrics
- /api/v1/compliance/india/metrics/evidence-collection: Evidence collection metrics
- /api/v1/compliance/india/metrics/bias-detection: Bias detection metrics

Requirements: 7.7, 8.6
"""

from fastapi import APIRouter, Query, status
from typing import Optional
import logging

from api.services.india_compliance_metrics import india_compliance_metrics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/compliance/india/metrics", tags=["india-compliance-metrics"])


@router.get(
    "/compliance-checks",
    status_code=status.HTTP_200_OK,
    summary="Compliance Check Metrics",
    description="Get compliance check latency and success metrics",
    responses={
        200: {
            "description": "Metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "metric_type": "compliance_check_latency",
                        "time_window_hours": 24,
                        "data": [
                            {
                                "system_id": "system-123",
                                "framework": "dpdp_act_2023",
                                "avg_latency_ms": 1250.5,
                                "min_latency_ms": 800.0,
                                "max_latency_ms": 2100.0,
                                "avg_score": 85.5,
                                "check_count": 10,
                                "passed_count": 8,
                            }
                        ],
                        "summary": {
                            "total_checks": 10,
                            "avg_latency_ms": 1250.5,
                            "passed_checks": 8,
                            "success_rate": 80.0,
                        },
                    }
                }
            },
        },
    },
)
async def get_compliance_check_metrics(
    system_id: Optional[str] = Query(None, description="Filter by system ID"),
    framework: Optional[str] = Query(None, description="Filter by framework"),
    hours: int = Query(24, ge=1, le=720, description="Time window in hours"),
):
    """
    Get compliance check metrics.

    Provides:
    - Average, min, max latency for compliance checks
    - Compliance scores
    - Success rates
    - Check counts

    Args:
        system_id: Optional system ID filter
        framework: Optional framework filter (dpdp_act_2023, niti_aayog_principles, meity_guidelines)
        hours: Time window in hours (1-720)

    Returns:
        Compliance check metrics with summary

    Requirements: 7.7
    """
    try:
        metrics = await india_compliance_metrics_service.get_compliance_check_metrics(
            system_id=system_id,
            framework=framework,
            hours=hours,
        )
        return metrics
    except Exception as e:
        logger.error(f"Failed to get compliance check metrics: {e}", exc_info=True)
        return {
            "error": str(e),
            "metric_type": "compliance_check_latency",
        }


@router.get(
    "/integrations",
    status_code=status.HTTP_200_OK,
    summary="Integration Metrics",
    description="Get integration sync success/failure rates and latency",
    responses={
        200: {
            "description": "Metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "metric_type": "integration_metrics",
                        "time_window_hours": 24,
                        "data": [
                            {
                                "integration_name": "onetrust",
                                "success": True,
                                "avg_latency_ms": 2500.0,
                                "min_latency_ms": 1800.0,
                                "max_latency_ms": 3200.0,
                                "avg_evidence_count": 45.5,
                                "sync_count": 12,
                            },
                            {
                                "integration_name": "securiti",
                                "success": True,
                                "avg_latency_ms": 1800.0,
                                "min_latency_ms": 1200.0,
                                "max_latency_ms": 2400.0,
                                "avg_evidence_count": 32.0,
                                "sync_count": 10,
                            },
                        ],
                        "summary": {
                            "total_syncs": 22,
                            "successful_syncs": 20,
                            "success_rate": 90.91,
                        },
                    }
                }
            },
        },
    },
)
async def get_integration_metrics(
    integration_name: Optional[str] = Query(
        None,
        description="Filter by integration (onetrust, securiti, sprinto, mlflow, aws, azure, gcp)",
    ),
    hours: int = Query(24, ge=1, le=720, description="Time window in hours"),
):
    """
    Get integration sync metrics.

    Provides:
    - Success/failure rates for each integration
    - Sync latency metrics
    - Evidence collection counts
    - Sync frequency

    Args:
        integration_name: Optional integration filter
        hours: Time window in hours (1-720)

    Returns:
        Integration metrics with summary

    Requirements: 7.7
    """
    try:
        metrics = await india_compliance_metrics_service.get_integration_metrics(
            integration_name=integration_name,
            hours=hours,
        )
        return metrics
    except Exception as e:
        logger.error(f"Failed to get integration metrics: {e}", exc_info=True)
        return {
            "error": str(e),
            "metric_type": "integration_metrics",
        }


@router.get(
    "/ai-automation",
    status_code=status.HTTP_200_OK,
    summary="AI Automation Usage Metrics",
    description="Get AI automation usage, latency, and token consumption",
    responses={
        200: {
            "description": "Metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "metric_type": "ai_automation_usage",
                        "time_window_hours": 24,
                        "data": [
                            {
                                "automation_type": "gap_analysis",
                                "system_id": "system-123",
                                "success": True,
                                "avg_latency_ms": 3500.0,
                                "total_tokens": 45000,
                                "avg_tokens": 4500.0,
                                "usage_count": 10,
                            },
                            {
                                "automation_type": "remediation_plan",
                                "system_id": "system-123",
                                "success": True,
                                "avg_latency_ms": 4200.0,
                                "total_tokens": 52000,
                                "avg_tokens": 5200.0,
                                "usage_count": 10,
                            },
                        ],
                        "summary": {
                            "total_usage": 20,
                            "successful_usage": 19,
                            "success_rate": 95.0,
                            "total_tokens": 97000,
                            "avg_tokens_per_usage": 4850.0,
                        },
                    }
                }
            },
        },
    },
)
async def get_ai_automation_metrics(
    system_id: Optional[str] = Query(None, description="Filter by system ID"),
    automation_type: Optional[str] = Query(
        None,
        description="Filter by automation type (gap_analysis, remediation, policy, qa)",
    ),
    hours: int = Query(24, ge=1, le=720, description="Time window in hours"),
):
    """
    Get AI automation usage metrics.

    Provides:
    - Usage counts by automation type
    - Latency metrics
    - Token consumption
    - Success rates

    Args:
        system_id: Optional system ID filter
        automation_type: Optional automation type filter
        hours: Time window in hours (1-720)

    Returns:
        AI automation metrics with summary

    Requirements: 8.6
    """
    try:
        metrics = await india_compliance_metrics_service.get_ai_automation_metrics(
            system_id=system_id,
            automation_type=automation_type,
            hours=hours,
        )
        return metrics
    except Exception as e:
        logger.error(f"Failed to get AI automation metrics: {e}", exc_info=True)
        return {
            "error": str(e),
            "metric_type": "ai_automation_usage",
        }
