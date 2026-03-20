"""
India Compliance Request Validation and Error Handling Middleware

Provides comprehensive request validation, error handling, and detailed error responses
for India compliance endpoints.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError, BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)


# ============================================================================
# Error Response Models
# ============================================================================

class ValidationErrorDetail(BaseModel):
    """Detail of a validation error"""
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")
    value: Optional[Any] = Field(None, description="Invalid value")


class IndiaComplianceErrorResponse(BaseModel):
    """Standard error response for India compliance endpoints"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[List[ValidationErrorDetail]] = Field(None, description="Validation details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    trace_id: Optional[str] = Field(None, description="Trace ID for debugging")


# ============================================================================
# Validation Functions
# ============================================================================

def validate_system_id(system_id: str) -> bool:
    """Validate system ID format"""
    if not system_id or not isinstance(system_id, str):
        return False
    if len(system_id) < 3 or len(system_id) > 255:
        return False
    # Allow alphanumeric, hyphens, underscores
    return all(c.isalnum() or c in '-_' for c in system_id)


def validate_framework(framework: str) -> bool:
    """Validate framework name"""
    valid_frameworks = [
        "dpdp_act_2023",
        "niti_aayog_principles",
        "meity_guidelines",
        "digital_india_act"
    ]
    return framework.lower() in valid_frameworks


def validate_bias_type(bias_type: str) -> bool:
    """Validate bias type"""
    valid_types = [
        "caste_bias",
        "religious_bias",
        "linguistic_bias",
        "regional_bias",
        "gender_bias",
        "intersectional_bias"
    ]
    return bias_type.lower() in valid_types


def validate_integration_name(integration_name: str) -> bool:
    """Validate integration name"""
    valid_integrations = [
        "onetrust",
        "securiti",
        "sprinto",
        "vanta",
        "custom_api",
        "mlflow",
        "aws",
        "azure",
        "gcp"
    ]
    return integration_name.lower() in valid_integrations


def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """Validate URL format"""
    import re
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None


# ============================================================================
# Error Handlers
# ============================================================================

async def handle_validation_error(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error for {request.url.path}: {exc.error_count()} errors")
    
    details = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"][1:])
        details.append(
            ValidationErrorDetail(
                field=field,
                message=error["msg"],
                type=error["type"],
                value=error.get("input")
            )
        )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=IndiaComplianceErrorResponse(
            error="validation_error",
            message="Request validation failed",
            status_code=422,
            details=details,
            request_id=request.headers.get("x-request-id"),
        ).dict()
    )


async def handle_india_compliance_error(request: Request, exc: Exception):
    """Handle India compliance specific errors"""
    logger.error(f"India compliance error: {str(exc)}", exc_info=True)
    
    # Determine error type and status code
    error_type = type(exc).__name__
    
    if "NotFound" in error_type:
        status_code = status.HTTP_404_NOT_FOUND
        error_message = "Resource not found"
    elif "Unauthorized" in error_type or "Forbidden" in error_type:
        status_code = status.HTTP_403_FORBIDDEN
        error_message = "Access denied"
    elif "BadRequest" in error_type or "ValueError" in error_type:
        status_code = status.HTTP_400_BAD_REQUEST
        error_message = "Invalid request"
    elif "Timeout" in error_type:
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
        error_message = "Request timeout"
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_message = "Internal server error"
    
    return JSONResponse(
        status_code=status_code,
        content=IndiaComplianceErrorResponse(
            error=error_type,
            message=error_message,
            status_code=status_code,
            request_id=request.headers.get("x-request-id"),
        ).dict()
    )


# ============================================================================
# Request Validators
# ============================================================================

class ComplianceCheckValidator:
    """Validator for compliance check requests"""
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate compliance check request"""
        
        # Validate system_id
        if "system_id" not in data:
            return False, "system_id is required"
        
        if not validate_system_id(data["system_id"]):
            return False, "Invalid system_id format"
        
        # Validate frameworks
        if "frameworks" not in data:
            return False, "frameworks is required"
        
        if not isinstance(data["frameworks"], list) or len(data["frameworks"]) == 0:
            return False, "frameworks must be a non-empty list"
        
        for framework in data["frameworks"]:
            if not validate_framework(framework):
                return False, f"Invalid framework: {framework}"
        
        # Validate optional fields
        if "include_evidence" in data and not isinstance(data["include_evidence"], bool):
            return False, "include_evidence must be boolean"
        
        if "include_gaps" in data and not isinstance(data["include_gaps"], bool):
            return False, "include_gaps must be boolean"
        
        return True, None


class BiasDetectionValidator:
    """Validator for bias detection requests"""
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate bias detection request"""
        
        # Validate system_id
        if "system_id" not in data:
            return False, "system_id is required"
        
        if not validate_system_id(data["system_id"]):
            return False, "Invalid system_id format"
        
        # Validate model_id
        if "model_id" not in data:
            return False, "model_id is required"
        
        if not isinstance(data["model_id"], str) or len(data["model_id"]) == 0:
            return False, "model_id must be a non-empty string"
        
        # Validate bias_types
        if "bias_types" not in data:
            return False, "bias_types is required"
        
        if not isinstance(data["bias_types"], list) or len(data["bias_types"]) == 0:
            return False, "bias_types must be a non-empty list"
        
        for bias_type in data["bias_types"]:
            if not validate_bias_type(bias_type):
                return False, f"Invalid bias_type: {bias_type}"
        
        return True, None


class IntegrationValidator:
    """Validator for integration requests"""
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate integration request"""
        
        # Validate integration_name
        if "integration_name" not in data:
            return False, "integration_name is required"
        
        if not validate_integration_name(data["integration_name"]):
            return False, f"Invalid integration_name: {data['integration_name']}"
        
        # Validate credentials
        if "credentials" not in data:
            return False, "credentials is required"
        
        if not isinstance(data["credentials"], dict) or len(data["credentials"]) == 0:
            return False, "credentials must be a non-empty dictionary"
        
        # Validate required credentials based on integration type
        integration_name = data["integration_name"].lower()
        required_fields = {
            "onetrust": ["api_key", "org_id"],
            "securiti": ["api_key", "tenant_id"],
            "sprinto": ["api_key"],
            "vanta": ["api_key"],
            "custom_api": ["webhook_url", "api_key"],
            "mlflow": ["tracking_uri", "api_key"],
            "aws": ["access_key_id", "secret_access_key", "region"],
            "azure": ["subscription_id", "client_id", "client_secret", "tenant_id"],
            "gcp": ["project_id", "service_account_json"],
        }
        
        required = required_fields.get(integration_name, [])
        for field in required:
            if field not in data["credentials"]:
                return False, f"Missing required credential: {field}"
        
        # Validate URL fields if present
        if "webhook_url" in data["credentials"]:
            if not validate_url(data["credentials"]["webhook_url"]):
                return False, "Invalid webhook_url format"
        
        if "tracking_uri" in data["credentials"]:
            if not validate_url(data["credentials"]["tracking_uri"]):
                return False, "Invalid tracking_uri format"
        
        return True, None


class PolicyGenerationValidator:
    """Validator for policy generation requests"""
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate policy generation request"""
        
        # Validate system_id
        if "system_id" not in data:
            return False, "system_id is required"
        
        if not validate_system_id(data["system_id"]):
            return False, "Invalid system_id format"
        
        # Validate system_name
        if "system_name" not in data:
            return False, "system_name is required"
        
        if not isinstance(data["system_name"], str) or len(data["system_name"]) == 0:
            return False, "system_name must be a non-empty string"
        
        if len(data["system_name"]) > 255:
            return False, "system_name must be less than 255 characters"
        
        # Validate system_description
        if "system_description" not in data:
            return False, "system_description is required"
        
        if not isinstance(data["system_description"], str) or len(data["system_description"]) == 0:
            return False, "system_description must be a non-empty string"
        
        # Validate data_types
        if "data_types" not in data:
            return False, "data_types is required"
        
        if not isinstance(data["data_types"], list) or len(data["data_types"]) == 0:
            return False, "data_types must be a non-empty list"
        
        for data_type in data["data_types"]:
            if not isinstance(data_type, str) or len(data_type) == 0:
                return False, "Each data_type must be a non-empty string"
        
        # Validate framework if present
        if "framework" in data:
            if not validate_framework(data["framework"]):
                return False, f"Invalid framework: {data['framework']}"
        
        # Validate policy_type if present
        if "policy_type" in data:
            valid_types = ["privacy_policy", "consent_form", "data_processing_agreement", "retention_policy"]
            if data["policy_type"] not in valid_types:
                return False, f"Invalid policy_type. Must be one of: {', '.join(valid_types)}"
        
        return True, None


# ============================================================================
# Response Formatters
# ============================================================================

def format_error_response(
    error_type: str,
    message: str,
    status_code: int,
    details: Optional[List[ValidationErrorDetail]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Format error response"""
    return IndiaComplianceErrorResponse(
        error=error_type,
        message=message,
        status_code=status_code,
        details=details,
        request_id=request_id,
    ).dict()


def format_success_response(
    data: Dict[str, Any],
    status_code: int = 200,
    message: str = "Success",
) -> Dict[str, Any]:
    """Format success response"""
    return {
        "status": "success",
        "message": message,
        "status_code": status_code,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
    }
