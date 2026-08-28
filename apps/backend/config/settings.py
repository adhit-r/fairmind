"""
Production-ready configuration management for FairMind backend.
"""

import os
import secrets
from typing import List, Optional
try:
    from pydantic_settings import BaseSettings
    from pydantic import field_validator
    validator = field_validator  # Alias for compatibility
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
    api_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    
    # Security
    secret_key: str = secrets.token_urlsafe(32)
    jwt_secret: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:1111"
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: List[str] = ["*"]
    allow_credentials: bool = True
    
    # Database
    database_url: str = "sqlite:///./fairmind.db"
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 30
    database_timeout: int = 30
    assurance_v2_enabled: bool = False
    # Core assurance surfaces stay separately hidden until their exact
    # release gate is deliberately enabled with the master switch.
    assurance_v2_target_versions_enabled: bool = False
    assurance_v2_suite_versions_enabled: bool = False
    assurance_v2_plans_enabled: bool = False
    assurance_v2_runs_enabled: bool = False
    # Verified Evidence Passport admission remains independently disabled until
    # the route, trust catalog, and reviewer workflow pass their release gate.
    assurance_v2_evidence_submit_enabled: bool = False
    # Unsigned reports are separately disabled by default. When enabled, they
    # remain explicitly unverified, human-review-only material.
    assurance_v2_evidence_import_enabled: bool = False
    # Four-eyes evidence review remains separately disabled until its
    # persistence, authorization, and release-gate controls are validated.
    assurance_v2_evidence_review_enabled: bool = False
    # Normal governance decisions remain independently disabled until their
    # PostgreSQL CAS path and authorization gate are deliberately released.
    assurance_v2_governance_decision_enabled: bool = False
    # Owner decision overrides remain separately disabled until their
    # PostgreSQL owner-authority proof and audited exception path are released.
    assurance_v2_separation_override_enabled: bool = False
    # Evaluator registration administration is inert until the dedicated
    # release gate, narrow organization permission, and audited ceremony are
    # deliberately enabled together.
    assurance_v2_evaluator_catalog_enabled: bool = False
    # Issuer, public-key, and trust-policy administration remains independently
    # hidden until PostgreSQL 013f and the literal trust-admin permission release.
    assurance_v2_trust_administration_enabled: bool = False
    assurance_migration_schema: Optional[str] = None
    
    # Neon Auth + Data API
    neon_auth_enabled: bool = False
    neon_jwks_url: Optional[str] = None
    neon_jwt_issuer: Optional[str] = None
    neon_jwt_audience: Optional[str] = None
    neon_data_api_url: Optional[str] = None
    neon_data_api_key: Optional[str] = None

    # Authentik Configuration
    authentik_enabled: bool = False
    authentik_server_url: Optional[str] = None
    authentik_jwks_url: Optional[str] = None
    authentik_issuer: Optional[str] = None
    authentik_audience: Optional[str] = None
    authentik_jwt_algorithm: str = "RS256"
    authentik_jwks_cache_ttl: int = 3600
    jwt_validation_mode: str = "internal"  # "internal" (HS256) or "authentik" (RS256)
    authentik_oauth_client_id: Optional[str] = "fairmind-frontend"
    authentik_oauth_client_secret: Optional[str] = None
    authentik_oauth_redirect_uri: Optional[str] = "http://localhost:3000/auth/callback"
    authentik_token_endpoint: Optional[str] = None  # Will default to {authentik_server_url}/application/o/token/
    authentik_refresh_token_ttl: int = 604800  # 7 days in seconds
    
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
    
    # Email Configuration
    email_backend: str = "console"  # "console", "smtp", "sendgrid", "ses", "resend"
    email_from_address: str = "noreply@fairmind.ai"
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_tls: bool = True
    sendgrid_api_key: Optional[str] = None
    resend_api_key: Optional[str] = None
    resend_from_email: str = "noreply@fairmind.ai"
    admin_email: str = "admin@fairmind.ai"
    
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
    
    # LLM Configuration
    google_api_key: Optional[str] = None
    llm_model: str = "gemini-1.5-flash"
    
    # Encryption Configuration
    compliance_encryption_key: Optional[str] = None
    encryption_algorithm: str = "AES-256"
    
    # RBAC Configuration
    enable_rbac: bool = True
    default_role: str = "compliance_viewer"
    
    # Audit Logging Configuration
    enable_audit_logging: bool = True
    audit_log_retention_days: int = 90
    audit_log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    def get_allowed_origins(self) -> List[str]:
        """Get allowed origins as a list."""
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
