"""
Production-ready configuration management for FairMind backend.
"""

import os
import secrets
from typing import List, Optional
try:
    from pydantic_settings import BaseSettings
    from pydantic import validator
except ImportError:
    from pydantic import BaseSettings, validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation and environment-specific configurations."""
    
    # Environment
    environment: str = "development"
    debug: bool = False
    
    # API Configuration
    api_title: str = "FairMind AI Governance Platform"
    api_description: str = "Production-ready AI governance and bias detection platform"
    api_version: str = "1.0.0"
    api_port: int = 8000
    
    # Security
    secret_key: str = secrets.token_urlsafe(32)
    jwt_secret: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # CORS
    allowed_origins: str = "http://localhost:3000"
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: List[str] = ["*"]
    allow_credentials: bool = True
    
    # Database
    database_url: str = "sqlite:///./fairmind.db"
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 30
    database_timeout: int = 30
    
    # Supabase
    supabase_url: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    
    # File Storage
    upload_dir: str = "uploads"
    database_dir: str = "datasets"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: List[str] = [".csv", ".json", ".xlsx", ".parquet"]
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Health Checks
    health_check_timeout: int = 30
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    # Redis (for caching and rate limiting)
    redis_url: Optional[str] = None
    redis_ttl: int = 3600
    
    # Email
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_tls: bool = True
    
    # Error Tracking
    sentry_dsn: Optional[str] = None
    
    # AWS S3
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    aws_s3_bucket: Optional[str] = None
    
    # ML Model Configuration
    model_cache_dir: str = "models"
    model_timeout: int = 300
    max_concurrent_models: int = 5
    
    # Bias Detection Configuration
    bias_detection_timeout: int = 600
    max_dataset_size: int = 1000000  # 1M rows
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    def get_allowed_origins(self) -> List[str]:
        """Parse allowed origins from string."""
        if isinstance(self.allowed_origins, str):
            return [origin.strip() for origin in self.allowed_origins.split(",")]
        return self.allowed_origins
    
    @validator("environment")
    def validate_environment(cls, v):
        if v not in ["development", "staging", "production"]:
            raise ValueError("Environment must be development, staging, or production")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        if v.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Invalid log level")
        return v.upper()
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def database_config(self) -> dict:
        """Database configuration for SQLAlchemy."""
        config = {
            "url": self.database_url,
            "echo": self.database_echo and not self.is_production,
        }
        
        if self.database_url.startswith("postgresql"):
            config.update({
                "pool_size": self.database_pool_size,
                "max_overflow": self.database_max_overflow,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
            })
        
        return config
    
    @property
    def cors_config(self) -> dict:
        """CORS configuration."""
        return {
            "allow_origins": self.get_allowed_origins(),
            "allow_methods": self.allowed_methods,
            "allow_headers": self.allowed_headers,
            "allow_credentials": self.allow_credentials,
        }


class DevelopmentSettings(Settings):
    """Development environment settings."""
    environment: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"
    database_echo: bool = True


class ProductionSettings(Settings):
    """Production environment settings."""
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"
    database_echo: bool = False
    
    # Production security requirements
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if v == "development-secret-key-change-in-production":
            raise ValueError("Must set a secure SECRET_KEY in production")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("jwt_secret")
    def validate_jwt_secret(cls, v):
        if v == "development-jwt-secret-change-in-production":
            raise ValueError("Must set a secure JWT_SECRET in production")
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get application settings based on environment."""
    env = os.getenv("NODE_ENV", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    else:
        return DevelopmentSettings()


# Global settings instance
settings = get_settings()