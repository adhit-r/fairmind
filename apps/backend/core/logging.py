"""
Enhanced centralized logging for FairMind backend.

Provides structured logging with context, sensitive data masking,
and integration with the core logging system.
"""

import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
import re

from core.interfaces import ILogger


# Patterns for sensitive data masking
SENSITIVE_PATTERNS = [
    (re.compile(r'(password["\']?\s*[:=]\s*["\']?)([^"\']+)', re.IGNORECASE), r'\1***MASKED***'),
    (re.compile(r'(token["\']?\s*[:=]\s*["\']?)([^"\']+)', re.IGNORECASE), r'\1***MASKED***'),
    (re.compile(r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([^"\']+)', re.IGNORECASE), r'\1***MASKED***'),
    (re.compile(r'(secret["\']?\s*[:=]\s*["\']?)([^"\']+)', re.IGNORECASE), r'\1***MASKED***'),
    (re.compile(r'(authorization["\']?\s*[:=]\s*["\']?)([^"\']+)', re.IGNORECASE), r'\1***MASKED***'),
]


def mask_sensitive_data(data: Any) -> Any:
    """Mask sensitive data in strings, dicts, and lists."""
    if isinstance(data, str):
        masked = data
        for pattern, replacement in SENSITIVE_PATTERNS:
            masked = pattern.sub(replacement, masked)
        return masked
    
    elif isinstance(data, dict):
        return {k: mask_sensitive_data(v) for k, v in data.items()}
    
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    
    return data


class StructuredLogger(ILogger):
    """
    Structured logger with JSON formatting and context support.
    """
    
    def __init__(self, name: str, mask_sensitive: bool = True):
        self.logger = logging.getLogger(name)
        self.mask_sensitive = mask_sensitive
        self.context: Dict[str, Any] = {}
    
    def _format_message(self, level: str, message: str, **kwargs) -> str:
        """Format log message as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "logger": self.logger.name,
            "message": message,
            **self.context,
            **kwargs
        }
        
        if self.mask_sensitive:
            log_data = mask_sensitive_data(log_data)
        
        return json.dumps(log_data)
    
    def set_context(self, **kwargs):
        """Set logging context (e.g., request_id, user_id)."""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear logging context."""
        self.context.clear()
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(self._format_message("DEBUG", message, **kwargs))
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(self._format_message("INFO", message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(self._format_message("WARNING", message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(self._format_message("ERROR", message, **kwargs))
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(self._format_message("CRITICAL", message, **kwargs))


class LoggerFactory:
    """Factory for creating loggers."""
    
    _loggers: Dict[str, StructuredLogger] = {}
    
    @classmethod
    def get_logger(cls, name: str, mask_sensitive: bool = True) -> StructuredLogger:
        """Get or create a logger."""
        if name not in cls._loggers:
            cls._loggers[name] = StructuredLogger(name, mask_sensitive)
        return cls._loggers[name]
    
    @classmethod
    def configure_logging(
        cls,
        level: str = "INFO",
        format_type: str = "json",
        log_file: Optional[str] = None
    ):
        """Configure global logging settings."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(message)s' if format_type == "json" else '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                *([] if log_file is None else [logging.FileHandler(log_file)])
            ]
        )


# Convenience function
def get_logger(name: str) -> StructuredLogger:
    """Get a logger instance."""
    return LoggerFactory.get_logger(name)
