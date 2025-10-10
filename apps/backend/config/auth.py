"""
JWT Authentication configuration for production security.
Updated to use the new secure JWT infrastructure.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import logging
from enum import Enum
from pydantic import BaseModel

from .settings import settings
from .cache import cache_manager
from .jwt_config import get_jwt_manager, init_jwt_manager
from .jwt_exceptions import (
    TokenExpiredException, 
    InvalidTokenException, 
    TokenMissingException,
    handle_jwt_exception
)
from .jwt_models import (
    JWTPayload, 
    TokenRequest, 
    TokenResponse, 
    UserRole, 
    TokenType
)

logger = logging.getLogger("fairmind.auth")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer()


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_USER = "api_user"


class TokenType(str, Enum):
    """Token types."""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


class User(BaseModel):
    """User model."""
    id: str
    email: str
    username: str
    role: UserRole
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    permissions: List[str] = []


class TokenData(BaseModel):
    """Token payload data."""
    user_id: str
    email: str
    role: UserRole
    token_type: TokenType
    exp: datetime
    iat: datetime
    permissions: List[str] = []


class AuthManager:
    """JWT Authentication manager using new secure JWT infrastructure."""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_expire_minutes
        self.refresh_token_expire_days = 30
        self.api_key_expire_days = 365
        
        # Initialize the JWT manager
        self.jwt_manager = init_jwt_manager(self.secret_key, self.algorithm)
        logger.info("AuthManager initialized with new JWT infrastructure")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def create_access_token(
        self, 
        user: User, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create an access token using new JWT infrastructure."""
        if not expires_delta:
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user.email,  # Standard JWT subject claim
            "user_id": int(user.id) if user.id.isdigit() else hash(user.id) % 2147483647,
            "email": user.email,
            "roles": [user.role.value],
            "permissions": user.permissions,
            "token_type": TokenType.ACCESS.value,
        }
        
        return self.jwt_manager.create_token(payload, expires_delta)
    
    def create_refresh_token(self, user: User) -> str:
        """Create a refresh token using new JWT infrastructure."""
        expires_delta = timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user.email,
            "user_id": int(user.id) if user.id.isdigit() else hash(user.id) % 2147483647,
            "email": user.email,
            "roles": [user.role.value],
            "token_type": TokenType.REFRESH.value,
        }
        
        return self.jwt_manager.create_token(payload, expires_delta)
    
    def create_api_key(self, user: User, name: str) -> str:
        """Create an API key using new JWT infrastructure."""
        expires_delta = timedelta(days=self.api_key_expire_days)
        
        payload = {
            "sub": user.email,
            "user_id": int(user.id) if user.id.isdigit() else hash(user.id) % 2147483647,
            "email": user.email,
            "roles": [user.role.value],
            "permissions": user.permissions,
            "token_type": TokenType.API_KEY.value,
            "key_name": name,
        }
        
        return self.jwt_manager.create_token(payload, expires_delta)
    
    async def verify_token(self, token: str) -> TokenData:
        """Verify and decode a JWT token using new JWT infrastructure."""
        try:
            # Check if token is blacklisted
            blacklist_key = f"blacklist:{token}"
            if await cache_manager.exists(blacklist_key):
                raise TokenExpiredException("Token has been revoked")
            
            # Use new JWT manager for verification
            payload = self.jwt_manager.verify_token(token)
            
            if payload is None:
                raise InvalidTokenException("Token verification failed")
            
            # Extract data from payload
            user_id = payload.get("user_id")
            email = payload.get("email") or payload.get("sub")
            roles = payload.get("roles", [])
            token_type = payload.get("token_type", TokenType.ACCESS.value)
            exp = payload.get("exp")
            iat = payload.get("iat")
            permissions = payload.get("permissions", [])
            
            if user_id is None or email is None:
                raise InvalidTokenException("Invalid token payload")
            
            # Convert timestamps if they're datetime objects
            if isinstance(exp, datetime):
                exp_dt = exp
            else:
                exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
            
            if isinstance(iat, datetime):
                iat_dt = iat
            else:
                iat_dt = datetime.fromtimestamp(iat, tz=timezone.utc)
            
            # Get primary role
            primary_role = roles[0] if roles else UserRole.VIEWER.value
            
            return TokenData(
                user_id=str(user_id),
                email=email,
                role=UserRole(primary_role),
                token_type=TokenType(token_type),
                exp=exp_dt,
                iat=iat_dt,
                permissions=permissions,
            )
            
        except (TokenExpiredException, InvalidTokenException):
            raise
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise InvalidTokenException("Could not validate credentials")
    
    async def refresh_access_token(self, refresh_token: str) -> str:
        """Create a new access token from a refresh token using new JWT infrastructure."""
        try:
            token_data = await self.verify_token(refresh_token)
            
            if token_data.token_type != TokenType.REFRESH:
                raise InvalidTokenException("Invalid token type for refresh")
            
            # Get user data (in production, this would come from database)
            user = await self.get_user_by_id(token_data.user_id)
            if not user or not user.is_active:
                raise InvalidTokenException("User not found or inactive")
            
            return self.create_access_token(user)
            
        except (TokenExpiredException, InvalidTokenException):
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise InvalidTokenException("Token refresh failed")
    
    async def revoke_token(self, token: str):
        """Revoke a token by adding it to blacklist using new JWT infrastructure."""
        try:
            # Use JWT manager to get token expiry without full verification
            expiry = self.jwt_manager.get_token_expiry(token)
            if expiry:
                blacklist_key = f"blacklist:{token}"
                
                # Calculate TTL based on token expiration
                ttl = int((expiry - datetime.utcnow()).total_seconds())
                if ttl > 0:
                    await cache_manager.set(blacklist_key, True, ttl=ttl)
                    logger.info("Token revoked and added to blacklist")
            
        except Exception as e:
            logger.warning(f"Token revocation warning: {str(e)}")
            # Token is already invalid, no need to blacklist
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID (placeholder - implement with your user storage)."""
        # This is a placeholder - in production, fetch from database
        # For now, return a mock user for demonstration
        if user_id == "admin":
            return User(
                id="admin",
                email="admin@fairmind.ai",
                username="admin",
                role=UserRole.ADMIN,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                permissions=["*"],  # Admin has all permissions
            )
        
        return None
    
    def check_permission(self, user: TokenData, required_permission: str) -> bool:
        """Check if user has required permission."""
        # Admin has all permissions
        if user.role == UserRole.ADMIN or "*" in user.permissions:
            return True
        
        # Check specific permission
        return required_permission in user.permissions
    
    def check_role(self, user: TokenData, required_roles: List[UserRole]) -> bool:
        """Check if user has one of the required roles."""
        return user.role in required_roles


# Global auth manager instance
auth_manager = AuthManager()


# FastAPI Dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Get current authenticated user using new JWT infrastructure."""
    if not credentials:
        raise TokenMissingException("Authentication credentials required")
    
    token = credentials.credentials
    if not token:
        raise TokenMissingException("Token missing from credentials")
    
    try:
        return await auth_manager.verify_token(token)
    except (TokenExpiredException, InvalidTokenException, TokenMissingException):
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise InvalidTokenException("Authentication failed")


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """Get current active user."""
    # In production, you might want to check if user is still active in database
    return current_user


def require_role(allowed_roles: List[UserRole]):
    """Dependency to require specific roles with new JWT infrastructure."""
    def role_checker(current_user: TokenData = Depends(get_current_active_user)):
        try:
            if not auth_manager.check_role(current_user, allowed_roles):
                from .jwt_exceptions import InsufficientPermissionsException
                raise InsufficientPermissionsException("Insufficient role permissions")
            return current_user
        except Exception as e:
            logger.error(f"Role check error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return role_checker


def require_permission(required_permission: str):
    """Dependency to require specific permission with new JWT infrastructure."""
    def permission_checker(current_user: TokenData = Depends(get_current_active_user)):
        try:
            if not auth_manager.check_permission(current_user, required_permission):
                from .jwt_exceptions import InsufficientPermissionsException
                raise InsufficientPermissionsException(f"Permission required: {required_permission}")
            return current_user
        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return permission_checker


# Common role dependencies
require_admin = require_role([UserRole.ADMIN])
require_analyst = require_role([UserRole.ADMIN, UserRole.ANALYST])
require_viewer = require_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER])


# Permission constants
class Permissions:
    """Permission constants."""
    # Model permissions
    MODEL_READ = "model:read"
    MODEL_WRITE = "model:write"
    MODEL_DELETE = "model:delete"
    
    # Dataset permissions
    DATASET_READ = "dataset:read"
    DATASET_WRITE = "dataset:write"
    DATASET_DELETE = "dataset:delete"
    
    # Analysis permissions
    ANALYSIS_RUN = "analysis:run"
    ANALYSIS_READ = "analysis:read"
    ANALYSIS_DELETE = "analysis:delete"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_MONITOR = "system:monitor"
    
    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"


# Default permissions by role
ROLE_PERMISSIONS = {
    UserRole.ADMIN: ["*"],  # All permissions
    UserRole.ANALYST: [
        Permissions.MODEL_READ,
        Permissions.MODEL_WRITE,
        Permissions.DATASET_READ,
        Permissions.DATASET_WRITE,
        Permissions.ANALYSIS_RUN,
        Permissions.ANALYSIS_READ,
        Permissions.SYSTEM_MONITOR,
    ],
    UserRole.VIEWER: [
        Permissions.MODEL_READ,
        Permissions.DATASET_READ,
        Permissions.ANALYSIS_READ,
    ],
    UserRole.API_USER: [
        Permissions.MODEL_READ,
        Permissions.DATASET_READ,
        Permissions.ANALYSIS_RUN,
        Permissions.ANALYSIS_READ,
    ],
}