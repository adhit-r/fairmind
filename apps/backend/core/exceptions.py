"""
Core exception hierarchy for FairMind backend.

Provides a structured exception system with domain-specific exceptions
and consistent error handling across the application.
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for the application."""
    
    # General errors (1xxx)
    INTERNAL_ERROR = "1000"
    VALIDATION_ERROR = "1001"
    NOT_FOUND = "1002"
    ALREADY_EXISTS = "1003"
    PERMISSION_DENIED = "1004"
    
    # Authentication errors (2xxx)
    AUTH_FAILED = "2000"
    INVALID_TOKEN = "2001"
    TOKEN_EXPIRED = "2002"
    INSUFFICIENT_PERMISSIONS = "2003"
    
    # Service errors (3xxx)
    SERVICE_UNAVAILABLE = "3000"
    EXTERNAL_SERVICE_ERROR = "3001"
    TIMEOUT = "3002"
    
    # Data errors (4xxx)
    INVALID_DATA = "4000"
    DATABASE_ERROR = "4001"
    CACHE_ERROR = "4002"
    
    # Business logic errors (5xxx)
    BIAS_DETECTION_FAILED = "5000"
    COMPLIANCE_CHECK_FAILED = "5001"
    MODEL_LOAD_FAILED = "5002"
    INFERENCE_FAILED = "5003"


class AppException(Exception):
    """Base exception for all application exceptions."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code.value,
            "details": self.details
        }


# Validation Exceptions
class ValidationError(AppException):
    """Raised when validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details=details
        )


class NotFoundError(AppException):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code=ErrorCode.NOT_FOUND,
            status_code=404,
            details={"resource": resource, "identifier": str(identifier)}
        )


class AlreadyExistsError(AppException):
    """Raised when a resource already exists."""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} already exists: {identifier}",
            code=ErrorCode.ALREADY_EXISTS,
            status_code=409,
            details={"resource": resource, "identifier": str(identifier)}
        )


# Authentication Exceptions
class AuthenticationError(AppException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code=ErrorCode.AUTH_FAILED,
            status_code=401
        )


class InvalidTokenError(AppException):
    """Raised when token is invalid."""
    
    def __init__(self, message: str = "Invalid or malformed token"):
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_TOKEN,
            status_code=401
        )


class TokenExpiredError(AppException):
    """Raised when token has expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(
            message=message,
            code=ErrorCode.TOKEN_EXPIRED,
            status_code=401
        )


class InsufficientPermissionsError(AppException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, required_permission: str):
        super().__init__(
            message=f"Insufficient permissions. Required: {required_permission}",
            code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            status_code=403,
            details={"required_permission": required_permission}
        )


# Service Exceptions
class ServiceUnavailableError(AppException):
    """Raised when a service is unavailable."""
    
    def __init__(self, service: str, reason: Optional[str] = None):
        message = f"Service unavailable: {service}"
        if reason:
            message += f" - {reason}"
        super().__init__(
            message=message,
            code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=503,
            details={"service": service, "reason": reason}
        )


class ExternalServiceError(AppException):
    """Raised when an external service call fails."""
    
    def __init__(self, service: str, error: str):
        super().__init__(
            message=f"External service error ({service}): {error}",
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=502,
            details={"service": service, "error": error}
        )


class TimeoutError(AppException):
    """Raised when an operation times out."""
    
    def __init__(self, operation: str, timeout: float):
        super().__init__(
            message=f"Operation timed out: {operation} (timeout: {timeout}s)",
            code=ErrorCode.TIMEOUT,
            status_code=504,
            details={"operation": operation, "timeout": timeout}
        )


# Data Exceptions
class InvalidDataError(AppException):
    """Raised when data is invalid."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_DATA,
            status_code=400,
            details=details
        )


class DatabaseError(AppException):
    """Raised when a database operation fails."""
    
    def __init__(self, operation: str, error: str):
        super().__init__(
            message=f"Database error during {operation}: {error}",
            code=ErrorCode.DATABASE_ERROR,
            status_code=500,
            details={"operation": operation, "error": error}
        )


class CacheError(AppException):
    """Raised when a cache operation fails."""
    
    def __init__(self, operation: str, error: str):
        super().__init__(
            message=f"Cache error during {operation}: {error}",
            code=ErrorCode.CACHE_ERROR,
            status_code=500,
            details={"operation": operation, "error": error}
        )


# Business Logic Exceptions
class BiasDetectionError(AppException):
    """Raised when bias detection fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Bias detection failed: {message}",
            code=ErrorCode.BIAS_DETECTION_FAILED,
            status_code=500,
            details=details
        )


class ComplianceCheckError(AppException):
    """Raised when compliance check fails."""
    
    def __init__(self, framework: str, error: str):
        super().__init__(
            message=f"Compliance check failed for {framework}: {error}",
            code=ErrorCode.COMPLIANCE_CHECK_FAILED,
            status_code=500,
            details={"framework": framework, "error": error}
        )


class ModelLoadError(AppException):
    """Raised when model loading fails."""
    
    def __init__(self, model_name: str, error: str):
        super().__init__(
            message=f"Failed to load model '{model_name}': {error}",
            code=ErrorCode.MODEL_LOAD_FAILED,
            status_code=500,
            details={"model": model_name, "error": error}
        )


class InferenceError(AppException):
    """Raised when model inference fails."""
    
    def __init__(self, model_name: str, error: str):
        super().__init__(
            message=f"Inference failed for model '{model_name}': {error}",
            code=ErrorCode.INFERENCE_FAILED,
            status_code=500,
            details={"model": model_name, "error": error}
        )
