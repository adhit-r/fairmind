"""
Base Service class for all domain services.

Provides common functionality:
- Dependency injection support
- Structured logging
- Error handling patterns
- Lifecycle management
"""

from typing import Optional, Any, Dict
from abc import ABC

from core.interfaces import IService, ILogger
from core.logging import get_logger
from core.exceptions import AppException


class BaseService(IService, ABC):
    """
    Base class for all domain services.
    
    Features:
    - Automatic logging setup
    - Error handling helpers
    - Dependency injection support
    - Lifecycle hooks
    
    Usage:
        @service(lifetime=ServiceLifetime.SINGLETON)
        class MyService(BaseService):
            def __init__(self, logger: ILogger = None):
                super().__init__(logger)
                # Your initialization
    """
    
    def __init__(self, logger: Optional[ILogger] = None):
        """
        Initialize base service.
        
        Args:
            logger: Logger instance (auto-injected via DI)
        """
        self.logger = logger or get_logger(self.__class__.__name__)
        self._initialized = False
        self._on_init()
    
    def _on_init(self):
        """
        Lifecycle hook called after initialization.
        Override in subclasses for custom initialization logic.
        """
        self.logger.info(f"{self.__class__.__name__} initialized")
        self._initialized = True
    
    def _on_shutdown(self):
        """
        Lifecycle hook for cleanup.
        Override in subclasses for cleanup logic.
        """
        self.logger.info(f"{self.__class__.__name__} shutting down")
    
    def _log_operation(self, operation: str, **kwargs):
        """
        Log a service operation with context.
        
        Args:
            operation: Operation name
            **kwargs: Additional context
        """
        self.logger.info(
            f"{self.__class__.__name__}.{operation}",
            **kwargs
        )
    
    def _log_error(self, operation: str, error: Exception, **kwargs):
        """
        Log a service error with context.
        
        Args:
            operation: Operation name
            error: Exception that occurred
            **kwargs: Additional context
        """
        self.logger.error(
            f"{self.__class__.__name__}.{operation} failed",
            error=str(error),
            error_type=type(error).__name__,
            **kwargs
        )
    
    def _handle_error(
        self,
        operation: str,
        error: Exception,
        raise_as: Optional[type] = None,
        **context
    ):
        """
        Handle and re-raise errors consistently.
        
        Args:
            operation: Operation name
            error: Original exception
            raise_as: Exception class to raise as (if different)
            **context: Additional error context
        """
        self._log_error(operation, error, **context)
        
        if raise_as and isinstance(raise_as, type) and issubclass(raise_as, AppException):
            # Re-raise as domain exception
            raise raise_as(
                message=str(error),
                details={"original_error": type(error).__name__, **context}
            )
        else:
            # Re-raise original
            raise
    
    def _validate_required(self, **kwargs):
        """
        Validate required parameters.
        
        Args:
            **kwargs: Parameters to validate (name: value)
            
        Raises:
            ValidationError: If any parameter is None or empty
        """
        from core.exceptions import ValidationError
        
        missing = []
        for name, value in kwargs.items():
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(name)
        
        if missing:
            raise ValidationError(
                f"Missing required parameters: {', '.join(missing)}",
                details={"missing_fields": missing}
            )
    
    def _validate_type(self, param_name: str, value: Any, expected_type: type):
        """
        Validate parameter type.
        
        Args:
            param_name: Parameter name
            value: Value to check
            expected_type: Expected type
            
        Raises:
            ValidationError: If type doesn't match
        """
        from core.exceptions import ValidationError
        
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Invalid type for {param_name}: expected {expected_type.__name__}, got {type(value).__name__}",
                details={
                    "parameter": param_name,
                    "expected_type": expected_type.__name__,
                    "actual_type": type(value).__name__
                }
            )
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get service information for debugging/monitoring.
        
        Returns:
            Service metadata
        """
        return {
            "service": self.__class__.__name__,
            "module": self.__class__.__module__,
            "initialized": self._initialized
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(initialized={self._initialized})>"


class AsyncBaseService(BaseService):
    """
    Base class for async services.
    
    Extends BaseService with async lifecycle hooks.
    """
    
    async def _on_init_async(self):
        """Async initialization hook."""
        pass
    
    async def _on_shutdown_async(self):
        """Async shutdown hook."""
        pass
