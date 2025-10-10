"""
JWT Authentication configuration for production security.
"""

import jwt
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
    """JWT Authentication manager."""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_expire_minutes
        self.refresh_token_expire_days = 30
        self.api_key_expire_days = 365
    
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
        """Create an access token."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )
        
        to_encode = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "token_type": TokenType.ACCESS.value,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "permissions": user.permissions,
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, user: User) -> str:
        """Create a refresh token."""
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        
        to_encode = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "token_type": TokenType.REFRESH.value,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_api_key(self, user: User, name: str) -> str:
        """Create an API key."""
        expire = datetime.now(timezone.utc) + timedelta(days=self.api_key_expire_days)
        
        to_encode = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "token_type": TokenType.API_KEY.value,
            "key_name": name,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "permissions": user.permissions,
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    async def verify_token(self, token: str) -> TokenData:
        """Verify and decode a JWT token."""
        try:
            # Check if token is blacklisted
            blacklist_key = f"blacklist:{token}"
            if await cache_manager.exists(blacklist_key):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            user_id: str = payload.get("user_id")
            email: str = payload.get("email")
            role: str = payload.get("role")
            token_type: str = payload.get("token_type")
            exp: int = payload.get("exp")
            iat: int = payload.get("iat")
            permissions: List[str] = payload.get("permissions", [])
            
            if user_id is None or email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check if token is expired
            if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return TokenData(
                user_id=user_id,
                email=email,
                role=UserRole(role),
                token_type=TokenType(token_type),
                exp=datetime.fromtimestamp(exp, tz=timezone.utc),
                iat=datetime.fromtimestamp(iat, tz=timezone.utc),
                permissions=permissions,
            )
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def refresh_access_token(self, refresh_token: str) -> str:
        """Create a new access token from a refresh token."""
        token_data = await self.verify_token(refresh_token)
        
        if token_data.token_type != TokenType.REFRESH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type for refresh",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user data (in production, this would come from database)
        user = await self.get_user_by_id(token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return self.create_access_token(user)
    
    async def revoke_token(self, token: str):
        """Revoke a token by adding it to blacklist."""
        try:
            token_data = await self.verify_token(token)
            blacklist_key = f"blacklist:{token}"
            
            # Calculate TTL based on token expiration
            ttl = int((token_data.exp - datetime.now(timezone.utc)).total_seconds())
            if ttl > 0:
                await cache_manager.set(blacklist_key, True, ttl=ttl)
            
        except HTTPException:
            # Token is already invalid, no need to blacklist
            pass
    
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
    """Get current authenticated user."""
    token = credentials.credentials
    return await auth_manager.verify_token(token)


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """Get current active user."""
    # In production, you might want to check if user is still active in database
    return current_user


def require_role(allowed_roles: List[UserRole]):
    """Dependency to require specific roles."""
    def role_checker(current_user: TokenData = Depends(get_current_active_user)):
        if not auth_manager.check_role(current_user, allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker


def require_permission(required_permission: str):
    """Dependency to require specific permission."""
    def permission_checker(current_user: TokenData = Depends(get_current_active_user)):
        if not auth_manager.check_permission(current_user, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {required_permission}"
            )
        return current_user
    
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