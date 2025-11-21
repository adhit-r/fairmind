"""
JWT Exception Handling System

Custom exceptions and error handlers for JWT operations.
Provides clear error messages and proper HTTP status codes.
"""

from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class JWTException(Exception):
    """Base JWT exception class."""
    
    def __init__(self, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class TokenExpiredException(JWTException):
    """Exception raised when JWT token has expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class InvalidTokenException(JWTException):
    """Exception raised when JWT token is invalid or malformed."""
    
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class TokenMissingException(JWTException):
    """Exception raised when JWT token is missing from request."""
    
    def __init__(self, message: str = "Token missing"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class TokenCreationException(JWTException):
    """Exception raised when JWT token creation fails."""
    
    def __init__(self, message: str = "Token creation failed"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class InsufficientPermissionsException(JWTException):
    """Exception raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


def handle_jwt_exception(request: Request, exc: JWTException) -> JSONResponse:
    """
    Convert JWT exception to FastAPI JSONResponse.
    """
    logger.warning(f"JWT Exception: {exc.message}")
    
    headers = {"WWW-Authenticate": "Bearer"}
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
        headers=headers if exc.status_code == status.HTTP_401_UNAUTHORIZED else None
    )


def handle_token_expired_exception(request: Request, exc: TokenExpiredException) -> JSONResponse:
    """Handle expired token exception with specific messaging."""
    logger.warning("JWT token expired")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Token has expired. Please login again."},
        headers={"WWW-Authenticate": "Bearer"},
    )


def handle_invalid_token_exception(request: Request, exc: InvalidTokenException) -> JSONResponse:
    """Handle invalid token exception with specific messaging."""
    logger.warning("Invalid JWT token provided")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid token. Please login again."},
        headers={"WWW-Authenticate": "Bearer"},
    )


def handle_token_missing_exception(request: Request, exc: TokenMissingException) -> JSONResponse:
    """Handle missing token exception with specific messaging."""
    logger.warning("JWT token missing from request")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Authentication required. Please provide a valid token."},
        headers={"WWW-Authenticate": "Bearer"},
    )


def handle_token_creation_exception(request: Request, exc: TokenCreationException) -> JSONResponse:
    """Handle token creation exception with specific messaging."""
    logger.error("JWT token creation failed")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Authentication service temporarily unavailable. Please try again later."},
    )


def handle_insufficient_permissions_exception(request: Request, exc: InsufficientPermissionsException) -> JSONResponse:
    """Handle insufficient permissions exception with specific messaging."""
    logger.warning("User lacks required permissions")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": "You do not have permission to access this resource."},
    )


def create_jwt_error_response(
    error_type: str, 
    message: Optional[str] = None,
    status_code: int = status.HTTP_401_UNAUTHORIZED
) -> HTTPException:
    """
    Create a standardized JWT error response.
    
    Args:
        error_type: Type of JWT error (expired, invalid, missing, etc.)
        message: Optional custom error message
        status_code: HTTP status code to return
        
    Returns:
        HTTPException with standardized error format
    """
    error_messages = {
        "expired": "Token has expired. Please login again.",
        "invalid": "Invalid token. Please login again.",
        "missing": "Authentication required. Please provide a valid token.",
        "malformed": "Token format is invalid. Please login again.",
        "creation_failed": "Authentication service temporarily unavailable.",
        "insufficient_permissions": "You do not have permission to access this resource."
    }
    
    detail = message or error_messages.get(error_type, "Authentication error occurred.")
    headers = {"WWW-Authenticate": "Bearer"} if status_code == status.HTTP_401_UNAUTHORIZED else None
    
    logger.warning(f"JWT Error - Type: {error_type}, Message: {detail}")
    
    return HTTPException(
        status_code=status_code,
        detail=detail,
        headers=headers
    )


def log_jwt_security_event(event_type: str, details: dict, user_id: Optional[str] = None):
    """
    Log JWT-related security events for monitoring and auditing.
    
    Args:
        event_type: Type of security event
        details: Additional event details
        user_id: Optional user ID associated with the event
    """
    log_data = {
        "event_type": f"jwt_{event_type}",
        "user_id": user_id,
        "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
            logger.name, logging.WARNING, "", 0, "", (), None
        )) if logger.handlers else None,
        **details
    }
    
    logger.warning(f"JWT Security Event: {log_data}")


# Exception handler mapping for FastAPI exception handlers
JWT_EXCEPTION_HANDLERS = {
    TokenExpiredException: handle_token_expired_exception,
    InvalidTokenException: handle_invalid_token_exception,
    TokenMissingException: handle_token_missing_exception,
    TokenCreationException: handle_token_creation_exception,
    InsufficientPermissionsException: handle_insufficient_permissions_exception,
    JWTException: handle_jwt_exception,
}