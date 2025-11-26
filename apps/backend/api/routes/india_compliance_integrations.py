"""
India Compliance Integration Management API Routes

Endpoints for managing integrations with external compliance tools:
- OneTrust (consent and privacy data)
- Securiti.ai (data discovery)
- Sprinto (security controls)
- Custom APIs (webhook-based evidence collection)
- MLflow (model metadata)
- Cloud providers (data residency)

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from ..schemas.india_compliance import (
    IntegrationCredentials,
    IntegrationCredentialsCreate,
    IntegrationStatus,
    ErrorResponse,
)
from ..services.compliance_integration_service import ComplianceIntegrationService
from ..middleware.india_compliance_validation import IntegrationValidator
from ..middleware.india_compliance_auth import (
    get_current_user_context,
    AuditLogger,
    CompliancePermission,
    UserContext,
)
from config.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/compliance/india/integrations", tags=["india-compliance-integrations"])

# Initialize service
integration_service = ComplianceIntegrationService()


# ============================================================================
# Request/Response Models
# ============================================================================

class IntegrationListResponse(BaseModel):
    """Response model for integration list"""
    integrations: List[Dict[str, Any]] = Field(..., description="List of integrations")
    total: int = Field(..., description="Total number of integrations")


class IntegrationStatusResponse(BaseModel):
    """Response model for integration status"""
    integration_id: str = Field(..., description="Integration ID")
    integration_name: str = Field(..., description="Integration name")
    status: IntegrationStatus = Field(..., description="Connection status")
    last_sync: Optional[datetime] = Field(None, description="Last sync timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    health_check_passed: bool = Field(..., description="Health check status")
    checked_at: datetime = Field(..., description="Check timestamp")


class SyncResponse(BaseModel):
    """Response model for sync operation"""
    integration_id: str = Field(..., description="Integration ID")
    status: str = Field(..., description="Sync status (success, failed, in_progress)")
    evidence_collected: int = Field(..., description="Number of evidence items collected")
    sync_started_at: datetime = Field(..., description="Sync start time")
    sync_completed_at: Optional[datetime] = Field(None, description="Sync completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class IntegrationConfigResponse(BaseModel):
    """Response model for integration configuration"""
    integration_name: str = Field(..., description="Integration name")
    description: str = Field(..., description="Integration description")
    required_credentials: List[str] = Field(..., description="Required credential fields")
    supported_evidence_types: List[str] = Field(..., description="Types of evidence supported")
    documentation_url: str = Field(..., description="Documentation URL")


# ============================================================================
# Integration Management Endpoints (8.2)
# ============================================================================

@router.get("", response_model=IntegrationListResponse)
async def list_integrations(
    user_context: UserContext = Depends(get_current_user_context)
):
    """
    List all configured integrations for the user
    
    Returns:
        List of integrations with status and last sync time
        
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
    """
    try:
        # Check permission
        if not user_context.has_permission(CompliancePermission.VIEW_INTEGRATIONS):
            logger.warning(f"User {user_context.user_id} denied permission: view_integrations")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: view_integrations"
            )
        
        logger.info(f"Listing integrations for user {user_context.user_id}")
        
        integrations = await integration_service.get_user_integrations(user_context.user_id)
        
        return IntegrationListResponse(
            integrations=integrations,
            total=len(integrations)
        )
    except Exception as e:
        logger.error(f"Error listing integrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=IntegrationCredentials)
async def create_integration(
    request: IntegrationCredentialsCreate,
    user_context: UserContext = Depends(get_current_user_context)
):
    """
    Create a new integration with external compliance tool
    
    Supported integrations:
    - OneTrust: Consent and privacy data
    - Securiti.ai: Data discovery and classification
    - Sprinto: Security controls and audit evidence
    - Custom API: Webhook-based evidence collection
    - MLflow: Model metadata and lineage
    - AWS/Azure/GCP: Data residency verification
    
    Args:
        request: Integration credentials
        
    Returns:
        Created integration with ID and status
        
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8
    """
    try:
        # Check permission
        if not user_context.has_permission(CompliancePermission.MANAGE_INTEGRATIONS):
            logger.warning(f"User {user_context.user_id} denied permission: manage_integrations")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: manage_integrations"
            )
        
        # Validate request
        is_valid, error_msg = IntegrationValidator.validate(request.dict())
        if not is_valid:
            logger.warning(f"Validation error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        logger.info(f"Creating integration {request.integration_name} for user {user_context.user_id}")
        
        # Create integration with encrypted credentials
        integration = await integration_service.create_integration(
            user_id=user_context.user_id,
            integration_name=request.integration_name,
            credentials=request.credentials,
        )
        
        logger.info(f"Integration {request.integration_name} created for user {user_context.user_id}")
        
        # Log audit entry
        await AuditLogger.log_integration_operation(
            user_id=user_context.user_id,
            integration_id=str(integration.id),
            operation="create",
            status="success"
        )
        
        return integration
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating integration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during integration creation"
        )


@router.get("/{integration_id}", response_model=IntegrationStatusResponse)
async def get_integration_status(
    integration_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get status of a specific integration
    
    Performs health check and returns current status.
    
    Args:
        integration_id: Integration identifier
        
    Returns:
        Integration status with health check results
        
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
    """
    try:
        logger.info(f"Getting status for integration {integration_id}")
        
        # Get integration
        integration = await integration_service.get_integration(integration_id, current_user)
        
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        # Perform health check
        health_check = await integration_service.health_check_integration(integration_id)
        
        return IntegrationStatusResponse(
            integration_id=integration_id,
            integration_name=integration["integration_name"],
            status=integration["status"],
            last_sync=integration.get("last_sync"),
            error_message=health_check.get("error_message"),
            health_check_passed=health_check.get("passed", False),
            checked_at=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting integration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{integration_id}", status_code=204)
async def delete_integration(
    integration_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Delete an integration
    
    Removes integration and its encrypted credentials.
    
    Args:
        integration_id: Integration identifier
        
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
    """
    try:
        logger.info(f"Deleting integration {integration_id} for user {current_user}")
        
        success = await integration_service.delete_integration(integration_id, current_user)
        
        if not success:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        logger.info(f"Integration {integration_id} deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/sync", response_model=SyncResponse)
async def sync_integration(
    integration_id: str,
    user_context: UserContext = Depends(get_current_user_context)
):
    """
    Manually trigger sync with external integration
    
    Pulls evidence from the integrated tool and stores it locally.
    
    Args:
        integration_id: Integration identifier
        
    Returns:
        Sync operation results
        
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9
    """
    try:
        # Check permission
        if not user_context.has_permission(CompliancePermission.SYNC_INTEGRATIONS):
            logger.warning(f"User {user_context.user_id} denied permission: sync_integrations")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: sync_integrations"
            )
        
        logger.info(f"Starting sync for integration {integration_id}")
        
        # Get integration
        integration = await integration_service.get_integration(integration_id, user_context.user_id)
        
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        # Start sync
        sync_result = await integration_service.sync_integration(integration_id)
        
        logger.info(f"Sync completed for integration {integration_id}: {sync_result['evidence_collected']} items")
        
        # Log audit entry
        await AuditLogger.log_integration_operation(
            user_id=user_context.user_id,
            integration_id=integration_id,
            operation="sync",
            status=sync_result["status"]
        )
        
        return SyncResponse(
            integration_id=integration_id,
            status=sync_result["status"],
            evidence_collected=sync_result.get("evidence_collected", 0),
            sync_started_at=sync_result["started_at"],
            sync_completed_at=sync_result.get("completed_at"),
            error_message=sync_result.get("error_message"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Integration Configuration Endpoints
# ============================================================================

@router.get("/config/{integration_name}", response_model=IntegrationConfigResponse)
async def get_integration_config(
    integration_name: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get configuration requirements for an integration
    
    Returns required credentials and supported evidence types.
    
    Args:
        integration_name: Integration name (onetrust, securiti, sprinto, etc.)
        
    Returns:
        Integration configuration details
        
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
    """
    try:
        logger.info(f"Getting config for integration {integration_name}")
        
        configs = {
            "onetrust": {
                "description": "OneTrust - Consent and Privacy Management",
                "required_credentials": ["api_key", "org_id"],
                "supported_evidence_types": [
                    "consent_records",
                    "privacy_assessments",
                    "data_mapping",
                    "dpia_results"
                ],
                "documentation_url": "https://docs.onetrust.com/",
            },
            "securiti": {
                "description": "Securiti.ai - Data Discovery and Classification",
                "required_credentials": ["api_key", "tenant_id"],
                "supported_evidence_types": [
                    "data_discovery_results",
                    "classification_tags",
                    "privacy_automation_evidence",
                    "data_inventory"
                ],
                "documentation_url": "https://docs.securiti.ai/",
            },
            "sprinto": {
                "description": "Sprinto - Security Controls and Compliance",
                "required_credentials": ["api_key"],
                "supported_evidence_types": [
                    "security_controls",
                    "audit_evidence",
                    "compliance_status",
                    "control_assessments"
                ],
                "documentation_url": "https://docs.sprinto.com/",
            },
            "vanta": {
                "description": "Vanta - Security Monitoring and Compliance",
                "required_credentials": ["api_key"],
                "supported_evidence_types": [
                    "security_monitoring_data",
                    "control_evidence",
                    "compliance_status",
                    "vulnerability_data"
                ],
                "documentation_url": "https://docs.vanta.com/",
            },
            "custom_api": {
                "description": "Custom API - Webhook-based Evidence Collection",
                "required_credentials": ["webhook_url", "api_key"],
                "supported_evidence_types": [
                    "custom_evidence",
                    "webhook_data",
                    "api_responses"
                ],
                "documentation_url": "https://docs.fairmind.ai/custom-api/",
            },
            "mlflow": {
                "description": "MLflow - Model Metadata and Lineage",
                "required_credentials": ["tracking_uri", "api_key"],
                "supported_evidence_types": [
                    "model_lineage",
                    "model_versioning",
                    "performance_metrics",
                    "experiment_data"
                ],
                "documentation_url": "https://mlflow.org/docs/",
            },
            "aws": {
                "description": "AWS - Data Residency and Storage Verification",
                "required_credentials": ["access_key_id", "secret_access_key", "region"],
                "supported_evidence_types": [
                    "data_residency_evidence",
                    "storage_location",
                    "region_verification",
                    "encryption_status"
                ],
                "documentation_url": "https://docs.aws.amazon.com/",
            },
            "azure": {
                "description": "Azure - Data Residency and Storage Verification",
                "required_credentials": ["subscription_id", "client_id", "client_secret", "tenant_id"],
                "supported_evidence_types": [
                    "data_residency_evidence",
                    "storage_location",
                    "region_verification",
                    "encryption_status"
                ],
                "documentation_url": "https://docs.microsoft.com/azure/",
            },
            "gcp": {
                "description": "GCP - Data Residency and Storage Verification",
                "required_credentials": ["project_id", "service_account_json"],
                "supported_evidence_types": [
                    "data_residency_evidence",
                    "storage_location",
                    "region_verification",
                    "encryption_status"
                ],
                "documentation_url": "https://cloud.google.com/docs/",
            },
        }
        
        config = configs.get(integration_name.lower())
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Integration {integration_name} not found"
            )
        
        return IntegrationConfigResponse(
            integration_name=integration_name,
            **config
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting integration config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint for integration service"""
    return {
        "status": "healthy",
        "service": "india-compliance-integrations",
        "timestamp": datetime.utcnow().isoformat(),
    }
