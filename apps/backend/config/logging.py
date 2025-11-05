"""
Production-ready logging configuration for FairMind backend.
"""

import logging
import logging.config
import sys
from typing import Dict, Any
from pathlib import Path

from .settings import settings


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration based on environment."""
    
    # Base configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "json" if settings.log_format == "json" else "default",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "fairmind": {
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }
    
    # Add file handler if log file is specified
    if settings.log_file:
        log_file_path = Path(settings.log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.log_level,
            "formatter": "json" if settings.log_format == "json" else "detailed",
            "filename": str(log_file_path),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
        }
        
        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            logger_config["handlers"].append("file")
    
    # Production-specific configuration
    if settings.is_production:
        # Reduce log levels for third-party libraries
        config["loggers"].update({
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "httpx": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "urllib3": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
        })
    
    return config


def setup_logging():
    """Setup logging configuration."""
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Create logger for the application
    logger = logging.getLogger("fairmind")
    logger.info(f"Logging configured for {settings.environment} environment")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f"fairmind.{name}")


# Setup logging on import
setup_logging()