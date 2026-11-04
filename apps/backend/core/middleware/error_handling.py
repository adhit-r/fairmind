"""
Enhanced error handling middleware.

Integrates with core exception hierarchy for consistent error responses.
"""

from typing import Callable
from fastapi import Request, Response
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_422_UNPROCESSABLE_ENTITY

from core.exceptions import AppException
from core.logging import get_logger
from config.settings import settings


logger = get_logger(__name__)


def public_validation_errors(errors: list) -> list:
    """Field, message and type of each validation error, never the submitted input.

    Pydantic's errors carry `input` and `ctx`, which can hold a password or token,
    so neither goes into a response or a log line.
    """
    return [{"loc": e.get("loc"), "msg": e.get("msg"), "type": e.get("type")} for e in errors]


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware with structured error responses.
    
    Features:
    - Catches all exceptions
    - Formats errors as JSON
    - Includes request context
    - Masks sensitive data in production
    - Integrates with core exception hierarchy
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        
        except AppException as e:
            # Handle our application exceptions
            logger.error(
                "Application exception",
                exception_type=e.__class__.__name__,
                message=e.message,
                code=e.code.value,
                path=request.url.path,
                method=request.method
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content=e.to_dict()
            )
        
        except HTTPException as e:
            # Let FastAPI handle its own HTTP exceptions
            logger.warning(
                "HTTP exception",
                status_code=e.status_code,
                detail=e.detail,
                path=request.url.path,
                method=request.method
            )
            raise
        
        except RequestValidationError as e:
            # Handle validation errors
            errors = public_validation_errors(e.errors())
            logger.warning(
                "Validation error",
                errors=errors,
                path=request.url.path,
                method=request.method
            )

            return JSONResponse(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "Validation Error",
                    "message": "Invalid request data",
                    "details": errors,
                }
            )
        
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(
                "Unhandled exception",
                exception_type=type(e).__name__,
                error=str(e),
                path=request.url.path,
                method=request.method,
                exc_info=True
            )
            
            # Return generic error in production, detailed in development
            if settings.is_production:
                return JSONResponse(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred. Please try again later."
                    }
                )
            else:
                return JSONResponse(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error": "Internal Server Error",
                        "message": str(e),
                        "type": type(e).__name__
                    }
                )
