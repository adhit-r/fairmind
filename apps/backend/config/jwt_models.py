"""
JWT Data Models

Pydantic models for JWT token payloads, responses, and validation.
Provides type safety and validation for JWT operations.
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum


class TokenType(str, Enum):
    """JWT token types."""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"
    VERIFICATION = "verification"


class UserRole(str, Enum):
    """User roles for authorization."""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    VIEWER = "viewer"


class JWTPayload(BaseModel):
    """
    JWT token payload structure.
    
    Represents the claims contained within a JWT token.
    """
    sub: str = Field(..., description="Subject (user email or ID)")
    user_id: int = Field(..., description="User database ID")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
    nbf: Optional[datetime] = Field(None, description="Not before time")
    token_type: TokenType = Field(TokenType.ACCESS, description="Type of token")
    scope: Optional[str] = Field(None, description="Token scope/permissions")
    roles: List[UserRole] = Field(default_factory=list, description="User roles")
    permissions: List[str] = Field(default_factory=list, description="Specific permissions")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    @validator('exp', 'iat', 'nbf', pre=True)
    def parse_timestamps(cls, v):
        """Convert Unix timestamps to datetime objects."""
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v)
        return v
    
    @validator('roles', pre=True)
    def parse_roles(cls, v):
        """Ensure roles are properly parsed."""
        if isinstance(v, str):
            return [v]
        return v or []
    
    @validator('permissions', pre=True)
    def parse_permissions(cls, v):
        """Ensure permissions are properly parsed."""
        if isinstance(v, str):
            return [v]
        return v or []
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: int(v.timestamp())
        }


class TokenRequest(BaseModel):
    """Request model for token creation."""
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    roles: List[UserRole] = Field(default_factory=list, description="User roles")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    token_type: TokenType = Field(TokenType.ACCESS, description="Type of token to create")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")
    scope: Optional[str] = Field(None, description="Token scope")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class TokenResponse(BaseModel):
    """Response model for token operations."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    scope: Optional[str] = Field(None, description="Token scope")
    refresh_token: Optional[str] = Field(None, description="Refresh token if applicable")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TokenVerification(BaseModel):
    """Response model for token verification."""
    valid: bool = Field(..., description="Whether token is valid")
    payload: Optional[JWTPayload] = Field(None, description="Token payload if valid")
    error: Optional[str] = Field(None, description="Error message if invalid")
    error_type: Optional[str] = Field(None, description="Type of error")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    time_remaining: Optional[int] = Field(None, description="Seconds until expiration")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TokenRefreshRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str = Field(..., description="Refresh token")
    expires_in: Optional[int] = Field(None, description="New token expiration in seconds")


class TokenIntrospection(BaseModel):
    """Token introspection response (RFC 7662 style)."""
    active: bool = Field(..., description="Whether token is active")
    sub: Optional[str] = Field(None, description="Subject")
    user_id: Optional[int] = Field(None, description="User ID")
    exp: Optional[int] = Field(None, description="Expiration timestamp")
    iat: Optional[int] = Field(None, description="Issued at timestamp")
    token_type: Optional[str] = Field(None, description="Token type")
    scope: Optional[str] = Field(None, description="Token scope")
    roles: Optional[List[str]] = Field(None, description="User roles")
    permissions: Optional[List[str]] = Field(None, description="User permissions")


class JWTConfig(BaseModel):
    """JWT configuration model."""
    secret_key: str = Field(..., description="JWT secret key")
    algorithm: str = Field("HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(30, description="Access token expiration in minutes")
    refresh_token_expire_days: int = Field(7, description="Refresh token expiration in days")
    issuer: Optional[str] = Field(None, description="JWT issuer")
    audience: Optional[str] = Field(None, description="JWT audience")
    
    @validator('algorithm')
    def validate_algorithm(cls, v):
        """Validate JWT algorithm."""
        allowed_algorithms = ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
        if v not in allowed_algorithms:
            raise ValueError(f"Algorithm must be one of: {allowed_algorithms}")
        return v
    
    @validator('access_token_expire_minutes')
    def validate_access_token_expiry(cls, v):
        """Validate access token expiration."""
        if v <= 0 or v > 1440:  # Max 24 hours
            raise ValueError("Access token expiration must be between 1 and 1440 minutes")
        return v
    
    @validator('refresh_token_expire_days')
    def validate_refresh_token_expiry(cls, v):
        """Validate refresh token expiration."""
        if v <= 0 or v > 365:  # Max 1 year
            raise ValueError("Refresh token expiration must be between 1 and 365 days")
        return v


class LoginRequest(BaseModel):
    """Login request model."""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(False, description="Whether to extend token expiration")
    
    @validator('email')
    def validate_email(cls, v):
        """Basic email validation."""
        if '@' not in v or '.' not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    user: Dict[str, Any] = Field(..., description="User information")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LogoutRequest(BaseModel):
    """Logout request model."""
    token: str = Field(..., description="JWT token to invalidate")
    all_sessions: bool = Field(False, description="Whether to logout from all sessions")


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: str = Field(..., description="User email")
    
    @validator('email')
    def validate_email(cls, v):
        """Basic email validation."""
        if '@' not in v or '.' not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Basic password validation."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class TokenBlacklist(BaseModel):
    """Token blacklist model for revoked tokens."""
    jti: str = Field(..., description="JWT ID (unique token identifier)")
    token_hash: str = Field(..., description="Hash of the token")
    user_id: int = Field(..., description="User ID")
    revoked_at: datetime = Field(..., description="When token was revoked")
    reason: Optional[str] = Field(None, description="Reason for revocation")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class JWTSecurityEvent(BaseModel):
    """JWT security event model for logging."""
    event_type: str = Field(..., description="Type of security event")
    user_id: Optional[int] = Field(None, description="User ID if applicable")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional event details")
    severity: str = Field("info", description="Event severity level")
    
    @validator('severity')
    def validate_severity(cls, v):
        """Validate severity level."""
        allowed_levels = ['debug', 'info', 'warning', 'error', 'critical']
        if v not in allowed_levels:
            raise ValueError(f"Severity must be one of: {allowed_levels}")
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }