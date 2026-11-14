"""
Production-ready configuration management for FairMind backend.
"""

import os
import secrets
from typing import List, Optional
try:
    from pydantic_settings import BaseSettings
    from pydantic import field_validator, model_validator
    validator = field_validator  # Alias for compatibility
except ImportError:
    from pydantic import BaseSettings, validator
from pydantic import Field, SecretStr
from dotenv import dotenv_values
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation and environment-specific configurations."""
    
    # Environment. Production unless told otherwise, so a deploy that forgets to
    # set it never runs development behaviour.
    environment: str = "production"
    # Local development only: JWTAuthenticationMiddleware signs loopback
    # requests without a token in as this existing user. Ignored outside development.
    fairmind_dev_login_email: Optional[str] = None
    # CI end-to-end runs only: a sign-in that needs no users table. Honoured only
    # when both values are set and the environment is development; never stored.
    e2e_admin_email: Optional[str] = None
    e2e_admin_password: Optional[str] = None
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
    # PostgreSQL only, e.g. postgresql://user:pass@host/db
    database_url: str = Field(default="", validate_default=True)
    database_echo: bool = False
    # Per pool, per process; a process has the async pool, the sync engine and the
    # ORM engine. Small by default so replicas stay under Neon's connection limit.
    database_pool_size: int = 5
    # Seconds to wait for a pooled connection at startup. Serverless Postgres
    # (Neon) can take 10 to 30 seconds to wake a suspended compute.
    database_connect_timeout: int = 60
    database_max_overflow: int = 5
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
    # Linking a verified admission is a separate mutation and remains hidden
    # until its PostgreSQL authority and separation controls pass release gates.
    assurance_v2_evidence_link_enabled: bool = False
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
    # Human upload of evaluation input artifacts to the write-once S3 store.
    # Hidden until enabled with the master switch and the store settings below.
    assurance_v2_artifact_upload_enabled: bool = False
    # A dedicated least-privilege IAM user (s3:PutObject and s3:GetObject on the
    # prefix only), separate from aws_access_key_id. No defaults: the store
    # refuses to build until every value is set.
    evaluation_artifact_s3_bucket: Optional[str] = None
    evaluation_artifact_s3_prefix: Optional[str] = None
    evaluation_artifact_s3_region: Optional[str] = None
    evaluation_artifact_s3_endpoint_url: Optional[str] = None
    evaluation_artifact_aws_access_key_id: Optional[str] = None
    evaluation_artifact_aws_secret_access_key: Optional[SecretStr] = None
    evaluation_artifact_max_bytes: int = Field(default=10 * 1024 * 1024, ge=1, le=1073741824)
    # Generic Evidence Hub URLs and direct entity links are untrusted until a
    # reviewed deployment explicitly enables this compatibility capability.
    untrusted_external_evidence_linking_enabled: bool = False
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
    authentik_oauth_client_id: Optional[str] = None
    authentik_oauth_client_secret: Optional[str] = None
    authentik_oauth_redirect_uri: Optional[str] = None
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
    # How often published policy rules are re-checked for newly failing systems; 0 turns alerts off.
    policy_alert_interval_seconds: int = 900
    # How often the release autopilot runs systems set to run; 0 turns the schedule off (Run now still works).
    autopilot_interval_seconds: int = 3600
    # How often discovery connectors are checked for a due schedule; 0 turns scheduled discovery off.
    discovery_check_interval_seconds: int = 300
    admin_email: str = "admin@fairmind.ai"
    
    # Error Tracking
    sentry_dsn: Optional[str] = None
    # Cloudflare Turnstile secret; when set, the public forms require a token (config/turnstile.py).
    turnstile_secret_key: Optional[str] = None
    # The public demo: POST /api/v1/auth/demo signs a visitor in as this existing
    # user, and DemoReadOnlyMiddleware refuses every change made as them. Off when unset.
    demo_user_email: Optional[str] = None
    
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
    openai_api_key: Optional[str] = None
    llm_model: str = "gemini-3.8-flash"
    # Local development: LLM features may call the developer's signed-in grok CLI. Ignored unless environment is development.
    grok_cli_enabled: bool = False

    # Evaluation sandbox launcher (src/infrastructure/sandbox). Worker host only, off by default;
    # setup and the memory budget are in docs/operations/rootless-docker-sandbox.md.
    sandbox_launcher_enabled: bool = False
    sandbox_docker_cli: str = "/usr/bin/docker"
    sandbox_docker_host: str = ""  # the rootless daemon, e.g. unix:///run/user/<uid>/docker.sock
    sandbox_require_rootless: bool = True
    sandbox_runner_repository: str = ""  # registry path of apps/eval-runner, without tag or digest
    sandbox_runner_digests: str = ""  # comma-separated sha256:<hex> allowlist
    sandbox_seccomp_profile: str = ""  # absolute path to apps/eval-runner/seccomp/sandbox.json
    sandbox_cpus: float = 1.0
    sandbox_max_memory_mib: int = 512
    sandbox_max_processes: int = 64
    sandbox_max_duration_seconds: int = 300
    sandbox_max_disk_mib: int = 64
    sandbox_max_input_bytes: int = 32 * 1024 * 1024
    sandbox_max_output_bytes: int = 16 * 1024

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
    
    @validator("database_url")
    def validate_database_url(cls, v):
        if not v.startswith("postgresql"):
            raise ValueError(
                "DATABASE_URL must be a PostgreSQL URL; see apps/backend/config/env.example"
            )
        return v

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
    def database_is_local(self) -> bool:
        """True when DATABASE_URL points at this machine."""
        from urllib.parse import urlsplit
        return urlsplit(self.database_url).hostname in ("localhost", "127.0.0.1", "::1")
    
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
    @model_validator(mode="after")
    def require_explicit_secrets(self):
        # The base defaults are random per process, so an unset secret passes every check below
        # yet signs tokens no other worker or restart can verify. Production must supply both.
        missing = [n.upper() for n in ("secret_key", "jwt_secret") if n not in self.model_fields_set]
        if missing:
            raise ValueError(f"{' and '.join(missing)} must be set when ENVIRONMENT is production")
        return self

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


# Same file Settings reads (Config.env_file), relative to the working directory.
_ENV_FILE: Optional[str] = ".env"


def resolve_environment() -> str:
    """The environment name both the settings class and the environment field use.

    ENVIRONMENT wins because pydantic fills Settings.environment from it, and an
    env var beats a subclass default. Picking the class from NODE_ENV alone let
    the two disagree: NODE_ENV=production with ENVIRONMENT=development built a
    ProductionSettings whose is_development was True, which skipped the Neon auth
    middleware despite NEON_AUTH_ENABLED=true and switched on the dev auto-login.
    NODE_ENV stays supported for start.sh, which already sets it. The .env file
    is read too, as Settings reads it. With nothing set the answer is production.
    """
    file_values = dotenv_values(_ENV_FILE) if _ENV_FILE and os.path.exists(_ENV_FILE) else {}

    def pick(name):
        return os.getenv(name) or file_values.get(name)

    return (pick("ENVIRONMENT") or pick("NODE_ENV") or "production").lower()


@lru_cache()
def get_settings() -> Settings:
    """Get application settings based on environment."""
    env = resolve_environment()

    node_env = os.getenv("NODE_ENV")
    if node_env and node_env.lower() != env:
        # Loud, because the two disagreeing is how a deployment ends up running
        # development behaviour while believing it is production.
        print(
            f"WARNING: NODE_ENV={node_env!r} but ENVIRONMENT resolves to {env!r}; "
            f"using {env!r}. Set them to the same value.",
            flush=True,
        )

    if env == "production":
        return ProductionSettings()
    else:
        return DevelopmentSettings()


# Global settings instance
settings = get_settings()
