"""
Authentication routes for JWT-based security.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import logging

from ...config.auth import (
    auth_manager, 
    get_current_user, 
    get_current_active_user,
    User, 
    UserRole, 
    TokenData,
    require_admin
)
from ...config.cache import cache_manager
from ...config.jwt_exceptions import (
    TokenExpiredException,
    InvalidTokenException,
    TokenMissingException,
    handle_jwt_exception
)
from ...config.jwt_models import (
    LoginRequest as JWTLoginRequest,
    LoginResponse as JWTLoginResponse,
    TokenResponse as JWTTokenResponse
)

logger = logging.getLogger("fairmind.auth")

router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "user-123",
                    "email": "user@example.com",
                    "username": "johndoe",
                    "role": "admin"
                }
            }
        }


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CreateUserRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: UserRole = UserRole.VIEWER


class CreateAPIKeyRequest(BaseModel):
    name: str
    description: Optional[str] = None


class APIKeyResponse(BaseModel):
    api_key: str
    name: str
    created_at: datetime
    expires_at: datetime


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """
    Authenticate user and return JWT tokens using new JWT infrastructure.
    
    **Example Request:**
    ```json
    {
      "email": "user@example.com",
      "password": "securepassword123"
    }
    ```
    
    **Example Response:**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "expires_in": 1800,
      "user": {
        "id": "user-123",
        "email": "user@example.com",
        "username": "johndoe",
        "role": "admin"
      }
    }
    ```
    
    **Error Responses:**
    - `401 Unauthorized`: Invalid email or password
    - `422 Unprocessable Entity`: Validation error (invalid email format, missing fields)
    - `429 Too Many Requests`: Rate limit exceeded
    - `500 Internal Server Error`: Server error during authentication
    """
    try:
        # In production, verify credentials against database
        # This is a simplified example
        if login_data.email == "admin@fairmind.ai" and login_data.password == "admin123":
            user = User(
                id="admin",
                email=login_data.email,
                username="admin",
                role=UserRole.ADMIN,
                is_active=True,
                created_at=datetime.utcnow(),
                permissions=["*"]
            )
        elif login_data.email == "analyst@fairmind.ai" and login_data.password == "analyst123":
            user = User(
                id="analyst",
                email=login_data.email,
                username="analyst",
                role=UserRole.ANALYST,
                is_active=True,
                created_at=datetime.utcnow(),
                permissions=[
                    "model:read", "model:write",
                    "dataset:read", "dataset:write",
                    "analysis:run", "analysis:read"
                ]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create tokens using new JWT infrastructure
        access_token = auth_manager.create_access_token(user)
        refresh_token = auth_manager.create_refresh_token(user)
        
        # Cache user session
        session_key = f"session:{user.id}"
        await cache_manager.set(
            session_key,
            {
                "user_id": user.id,
                "email": user.email,
                "role": user.role.value,
                "last_login": datetime.utcnow().isoformat()
            },
            ttl=86400  # 24 hours
        )
        
        logger.info(f"User logged in successfully: {user.email}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=auth_manager.access_token_expire_minutes * 60,
            user={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role.value,
            }
        )
        
    except HTTPException:
        raise
    except (TokenExpiredException, InvalidTokenException, TokenMissingException) as e:
        logger.warning(f"JWT error during login: {str(e)}")
        raise handle_jwt_exception(e)
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(refresh_data: RefreshRequest):
    """Refresh access token using refresh token with new JWT infrastructure."""
    try:
        access_token = await auth_manager.refresh_access_token(refresh_data.refresh_token)
        
        return RefreshResponse(
            access_token=access_token,
            expires_in=auth_manager.access_token_expire_minutes * 60
        )
        
    except (TokenExpiredException, InvalidTokenException, TokenMissingException) as e:
        logger.warning(f"JWT error during token refresh: {str(e)}")
        raise handle_jwt_exception(e)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    current_user: TokenData = Depends(get_current_active_user),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """Logout user and revoke tokens using new JWT infrastructure."""
    try:
        # Revoke the current token
        if credentials and credentials.credentials:
            await auth_manager.revoke_token(credentials.credentials)
        
        # Remove user session from cache
        session_key = f"session:{current_user.user_id}"
        await cache_manager.delete(session_key)
        
        logger.info(f"User logged out successfully: {current_user.email}")
        
        return {"message": "Successfully logged out"}
        
    except (TokenExpiredException, InvalidTokenException, TokenMissingException) as e:
        logger.warning(f"JWT error during logout: {str(e)}")
        # Still allow logout even if token is invalid
        return {"message": "Logged out (token was already invalid)"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: TokenData = Depends(get_current_active_user)):
    """Get current user information."""
    try:
        # In production, fetch full user data from database
        user_data = await auth_manager.get_user_by_id(current_user.user_id)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user_data.id,
            email=user_data.email,
            username=user_data.username,
            role=user_data.role,
            is_active=user_data.is_active,
            created_at=user_data.created_at,
            last_login=user_data.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: CreateAPIKeyRequest,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Create an API key for programmatic access."""
    try:
        # Get full user data
        user_data = await auth_manager.get_user_by_id(current_user.user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create API key
        api_key = auth_manager.create_api_key(user_data, api_key_data.name)
        
        # Store API key metadata in cache
        api_key_meta = {
            "name": api_key_data.name,
            "description": api_key_data.description,
            "user_id": current_user.user_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        }
        
        await cache_manager.set(
            f"api_key:{current_user.user_id}:{api_key_data.name}",
            api_key_meta,
            ttl=365 * 24 * 3600  # 1 year
        )
        
        logger.info(f"API key created for user {current_user.email}: {api_key_data.name}")
        
        return APIKeyResponse(
            api_key=api_key,
            name=api_key_data.name,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create API key error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.get("/api-keys")
async def list_api_keys(current_user: TokenData = Depends(get_current_active_user)):
    """List user's API keys."""
    try:
        # In production, fetch from database
        # For now, return cached API key metadata
        pattern = f"api_key:{current_user.user_id}:*"
        # This would need to be implemented with proper key scanning
        
        return {"api_keys": []}  # Placeholder
        
    except Exception as e:
        logger.error(f"List API keys error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete("/api-keys/{key_name}")
async def revoke_api_key(
    key_name: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Revoke an API key."""
    try:
        # Remove API key metadata from cache
        await cache_manager.delete(f"api_key:{current_user.user_id}:{key_name}")
        
        logger.info(f"API key revoked for user {current_user.email}: {key_name}")
        
        return {"message": f"API key '{key_name}' revoked successfully"}
        
    except Exception as e:
        logger.error(f"Revoke API key error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: CreateUserRequest,
    current_user: TokenData = Depends(require_admin)
):
    """Create a new user (admin only)."""
    try:
        # In production, this would create user in database
        # For now, return a mock response
        
        new_user = User(
            id=f"user_{user_data.username}",
            email=user_data.email,
            username=user_data.username,
            role=user_data.role,
            is_active=True,
            created_at=datetime.utcnow(),
            permissions=[]
        )
        
        logger.info(f"User created by {current_user.email}: {user_data.email}")
        
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            username=new_user.username,
            role=new_user.role,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            last_login=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/health")
async def auth_health_check():
    """Health check for authentication service."""
    try:
        # Check if cache is available
        cache_status = await cache_manager.health_check()
        
        return {
            "status": "healthy",
            "cache_available": cache_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Auth health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }