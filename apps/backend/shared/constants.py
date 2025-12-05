"""Application constants."""

from enum import Enum


# API Configuration
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"


# Authentication
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


# Rate Limiting
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds


# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000


# File Upload
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = [".csv", ".json", ".xlsx", ".parquet", ".txt"]


# Cache
DEFAULT_CACHE_TTL = 3600  # 1 hour
HEALTH_CHECK_CACHE_TTL = 60  # 1 minute


# Timeouts
DATABASE_TIMEOUT = 30
EXTERNAL_SERVICE_TIMEOUT = 60
MODEL_INFERENCE_TIMEOUT = 300  # 5 minutes


# HTTP Status Codes
class StatusCode:
    """HTTP status codes."""
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# Service Names
class ServiceName(str, Enum):
    """Service identifiers."""
    DATABASE = "database"
    CACHE = "cache"
    SUPABASE = "supabase"
    MLFLOW = "mlflow"
    WANDB = "wandb"
    STORAGE = "storage"


# Health Status
class HealthStatus(str, Enum):
    """Health check statuses."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
