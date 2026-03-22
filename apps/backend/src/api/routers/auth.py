"""
Authentication routes for JWT-based security and Authentik OAuth2 integration.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import logging
import httpx
import secrets

from config.auth import (
    auth_manager, 
    get_current_user, 
    get_current_active_user,
    User, 
    UserRole, 
    TokenData,
    require_admin
)
from config.cache import cache_manager
from config.jwt_exceptions import (
    TokenExpiredException,
    InvalidTokenException,
    TokenMissingException,
    handle_jwt_exception
)
from config.jwt_models import (
    LoginRequest as JWTLoginRequest,
    LoginResponse as JWTLoginResponse,
    TokenResponse as JWTTokenResponse
)
from config.settings import settings
from config.authentik_config import get_authentik_config

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


class AuthentikCallbackRequest(BaseModel):
    code: str
    state: str


class AuthentikCallbackResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict



@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    logger.info(f"Login attempt for: {login_data.email}")
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
        access_token = str(auth_manager.create_access_token(user))
        refresh_token = str(auth_manager.create_refresh_token(user))
        
        # Ensure they are not byte string representations like "b'...'"
        if access_token.startswith("b'") and access_token.endswith("'"):
             access_token = access_token[2:-1]
        if refresh_token.startswith("b'") and refresh_token.endswith("'"):
             refresh_token = refresh_token[2:-1]
        
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
        
        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": auth_manager.access_token_expire_minutes * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role.value,
            }
        }
        logger.info(f"Login Response Data Types: access_token={type(access_token)}, refresh_token={type(refresh_token)}")
        import json
        try:
            json.dumps(response_data)
            logger.info("Login Response is JSON serializable")
        except Exception as e:
            logger.error(f"Login Response JSON serialization failed: {e}")

        return LoginResponse(**response_data)
        
    except HTTPException:
        raise
    except (TokenExpiredException, InvalidTokenException, TokenMissingException) as e:
        logger.warning(f"JWT error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
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


@router.post("/callback", response_model=AuthentikCallbackResponse)
async def authentik_oauth_callback(
    code: str = Query(..., description="Authorization code from Authentik"),
    state: str = Query(..., description="State parameter for CSRF protection")
):
    """
    Handle Authentik OAuth2 callback.

    This endpoint exchanges an authorization code for an access token.
    Called by the frontend after user authenticates with Authentik.

    Args:
        code: Authorization code from Authentik
        state: State parameter for CSRF protection

    Returns:
        Access token, refresh token, and user information

    Raises:
        400: Invalid or missing authorization code
        401: Invalid state parameter or code exchange failed
        500: Server error during token exchange
    """
    if not settings.authentik_enabled:
        logger.warning("Authentik callback received but Authentik is not enabled")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentik is not enabled"
        )

    if not code or not state:
        logger.warning("Authentik callback missing code or state")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code or state"
        )

    try:
        # Exchange authorization code for access token
        token_url = f"{settings.authentik_server_url}/application/o/token/"

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.authentik_oauth_redirect_uri or "http://localhost:3000/auth/callback",
                    "client_id": settings.authentik_oauth_client_id or "fairmind-frontend",
                    "client_secret": settings.authentik_oauth_client_secret or "fairmind-frontend-secret",
                },
                timeout=10.0
            )

            if token_response.status_code != 200:
                logger.error(f"Token exchange failed: {token_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to exchange authorization code"
                )

            token_data = token_response.json()
            authentik_token = token_data.get("access_token")

            if not authentik_token:
                logger.error("No access token in Authentik response")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No access token received from Authentik"
                )

        # Validate token with Authentik JWKS
        authentik_config = get_authentik_config()
        if not authentik_config:
            logger.warning("Authentik config not initialized")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentik configuration not available"
            )

        # Validate Authentik token
        payload = await authentik_config.validate_token(authentik_token)
        if not payload:
            logger.error("Authentik token validation failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authentik token"
            )

        # Extract user info from token
        role_info = authentik_config.extract_role_info(payload)

        # Create or update user in database
        # For now, we'll use the existing user creation flow
        # In production, this would sync with the User model
        user = User(
            id=payload.get("sub", payload.get("user_id", "authentik-" + secrets.token_hex(8))),
            email=payload.get("email", ""),
            username=payload.get("preferred_username", payload.get("email", "").split("@")[0]),
            role=UserRole.VIEWER,  # Default role, should be mapped from Authentik groups
            is_active=True,
            created_at=datetime.utcnow(),
            permissions=[]  # Will be computed from roles
        )

        # Map Authentik roles to FairMind roles
        if "admin" in role_info.get("roles", []):
            user.role = UserRole.ADMIN
            user.permissions = ["*"]
        elif "analyst" in role_info.get("roles", []):
            user.role = UserRole.ANALYST
            user.permissions = [
                "model:read", "model:write",
                "dataset:read", "dataset:write",
                "analysis:run", "analysis:read"
            ]
        else:
            user.role = UserRole.VIEWER
            user.permissions = ["model:read", "dataset:read"]

        # Create tokens for FairMind
        access_token = str(auth_manager.create_access_token(user))
        refresh_token = str(auth_manager.create_refresh_token(user))

        # Ensure they are not byte string representations
        if access_token.startswith("b'") and access_token.endswith("'"):
            access_token = access_token[2:-1]
        if refresh_token.startswith("b'") and refresh_token.endswith("'"):
            refresh_token = refresh_token[2:-1]

        # Cache user session
        session_key = f"session:{user.id}"
        await cache_manager.set(
            session_key,
            {
                "user_id": user.id,
                "email": user.email,
                "role": user.role.value,
                "roles": role_info.get("roles", []),
                "groups": role_info.get("groups", []),
                "last_login": datetime.utcnow().isoformat()
            },
            ttl=86400  # 24 hours
        )

        logger.info(f"User authenticated via Authentik: {user.email}")

        return AuthentikCallbackResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=auth_manager.access_token_expire_minutes * 60,
            user={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role.value,
                "roles": role_info.get("roles", []),
                "groups": role_info.get("groups", [])
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentik callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
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


@router.get("/users")
async def list_users(
    current_user: TokenData = Depends(require_admin)
):
    """List all users (admin only). Returns users from DB or cache."""
    try:
        # Query users from DB if available
        try:
            from config.database import get_db
            from sqlalchemy import text
            async with get_db() as db:
                result = await db.execute(
                    text("SELECT id, email, username, name, roles, is_active, last_login, created_at FROM users ORDER BY created_at DESC LIMIT 100")
                )
                rows = result.mappings().all()
                users = [
                    {
                        "id": str(row["id"]),
                        "email": row["email"],
                        "username": row["username"],
                        "name": row.get("name") or row["username"],
                        "roles": row.get("roles") or [],
                        "is_active": row["is_active"],
                        "last_login": row["last_login"].isoformat() if row["last_login"] else None,
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    }
                    for row in rows
                ]
                return {"users": users}
        except Exception as db_err:
            logger.warning(f"Could not query users from DB: {db_err}")
            # Return empty list if DB not available
            return {"users": []}

    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
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


# OAuth2 Organization RBAC Endpoints

class OAuth2ValidateRequest(BaseModel):
    """Request model for OAuth2 token validation endpoint."""
    code: str
    state: str
    code_verifier: Optional[str] = None


class OAuth2ValidateResponse(BaseModel):
    """Response model for OAuth2 token validation."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class OAuth2SyncUserRequest(BaseModel):
    """Request model for OAuth2 user sync endpoint."""
    access_token: str
    org_id: Optional[str] = None


class OAuth2SyncUserResponse(BaseModel):
    """Response model for OAuth2 user sync."""
    user_id: str
    email: str
    username: str
    roles: list
    org_id: Optional[str]


class OAuth2RefreshRequest(BaseModel):
    """Request model for OAuth2 refresh token endpoint."""
    refresh_token: str


@router.post("/oauth2/validate", response_model=OAuth2ValidateResponse)
async def oauth2_validate(
    request: OAuth2ValidateRequest,
    x_client_ip: Optional[str] = None,
):
    """
    Validate OAuth2 authorization code and return JWT tokens.

    This endpoint exchanges an OAuth2 authorization code for JWT tokens
    (access and refresh). Called after user authenticates with Authentik.

    Process:
    1. Validate state parameter against session (CSRF protection)
    2. Exchange code for tokens via Authentik token endpoint
    3. Validate JWT signature with JWKS (RS256)
    4. Extract claims: user ID, email, groups (roles), org assignment
    5. Check if user exists in FairMind users table:
       - If exists: UPDATE roles, last_login, last_ip
       - If new: INSERT new user with authentik_id, roles from Authentik groups
    6. Return { access_token, refresh_token, user: { id, email, roles, org_id } }

    Args:
        code: Authorization code from Authentik
        state: State parameter for CSRF protection
        code_verifier: PKCE code verifier (optional)
        x_client_ip: Client IP address (from header)

    Returns:
        Access token, refresh token, and user information

    Raises:
        400: Invalid authorization code or missing parameters
        403: Invalid or expired state parameter (CSRF check failed)
        502: Failed to connect to Authentik or JWKS validation failed
        500: Server error during validation
    """
    try:
        from src.services.oauth2_service import oauth2_service

        # Validate input
        if not request.code or not request.state:
            logger.warning("OAuth2 validate: missing code or state")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing authorization code or state",
            )

        logger.info(f"OAuth2 validate request: code={request.code[:10]}..., state={request.state[:10]}...")

        # Exchange authorization code for tokens
        try:
            token_data = await oauth2_service.exchange_code_for_tokens(
                code=request.code,
                state=request.state,
                code_verifier=request.code_verifier,
            )
        except ValueError as e:
            if "Invalid or expired state" in str(e):
                logger.warning(f"OAuth2 validate: CSRF validation failed - {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid or expired state parameter (CSRF check failed)",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        # Validate and extract claims from token
        access_token = token_data.get("access_token")
        if not access_token:
            logger.error("OAuth2 validate: no access token in Authentik response")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="No access token received from authentication server",
            )

        # Extract claims from token
        claims = await oauth2_service.extract_claims(access_token)
        if not claims:
            logger.error("OAuth2 validate: token validation failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to validate authentication token",
            )

        # Sync user to database
        user_data = await oauth2_service.sync_user_from_authentik(
            claims=claims,
            ip_address=x_client_ip,
        )
        if not user_data:
            logger.error("OAuth2 validate: user sync failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sync user to database",
            )

        # Create FairMind JWT tokens for the user
        try:
            # Create a temporary User object for token generation
            user = User(
                id=user_data.get("user_id"),
                email=user_data.get("email"),
                username=user_data.get("username"),
                role=UserRole.ADMIN if "admin" in user_data.get("roles", [])
                    else UserRole.ANALYST if "analyst" in user_data.get("roles", [])
                    else UserRole.VIEWER,
                is_active=True,
                created_at=datetime.utcnow(),
                permissions=[]
            )

            # Generate FairMind JWT tokens
            fairmind_access_token = str(auth_manager.create_access_token(user))
            fairmind_refresh_token = str(auth_manager.create_refresh_token(user))

            # Clean up byte string representations
            if fairmind_access_token.startswith("b'") and fairmind_access_token.endswith("'"):
                fairmind_access_token = fairmind_access_token[2:-1]
            if fairmind_refresh_token.startswith("b'") and fairmind_refresh_token.endswith("'"):
                fairmind_refresh_token = fairmind_refresh_token[2:-1]

            # Cache user session
            session_key = f"session:{user_data.get('user_id')}"
            await cache_manager.set(
                session_key,
                {
                    "user_id": user_data.get("user_id"),
                    "email": user_data.get("email"),
                    "roles": user_data.get("roles", []),
                    "last_login": datetime.utcnow().isoformat(),
                },
                ttl=86400,  # 24 hours
            )

            logger.info(f"OAuth2 validate success: user={user_data.get('email')}")

            return OAuth2ValidateResponse(
                access_token=fairmind_access_token,
                refresh_token=fairmind_refresh_token,
                expires_in=auth_manager.access_token_expire_minutes * 60,
                user={
                    "id": user_data.get("user_id"),
                    "email": user_data.get("email"),
                    "username": user_data.get("username"),
                    "roles": user_data.get("roles", []),
                    "org_id": user_data.get("org_id"),
                },
            )

        except Exception as e:
            logger.error(f"OAuth2 validate: failed to create tokens - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create authentication tokens",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth2 validate error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication validation failed",
        )


@router.post("/oauth2/sync-user", response_model=OAuth2SyncUserResponse)
async def oauth2_sync_user(
    request: OAuth2SyncUserRequest,
    x_client_ip: Optional[str] = None,
):
    """
    Sync user from OAuth2 token and create/update in database.

    This endpoint validates an OAuth2 access token from Authentik
    and creates or updates the corresponding user in the FairMind database.

    Process:
    1. Validate JWT with JWKS
    2. Extract claims
    3. UPDATE user in DB with fresh data from Authentik
    4. Return synced user object

    Args:
        access_token: OAuth2 access token from Authentik (JWT)
        org_id: Optional organization ID to assign user to
        x_client_ip: Client IP address (from header)

    Returns:
        User ID, email, username, roles, and organization assignment

    Raises:
        401: Invalid or expired token
        404: Organization not found (if org_id provided)
        500: Server error during sync
    """
    try:
        from src.services.oauth2_service import oauth2_service

        if not request.access_token:
            logger.warning("OAuth2 sync-user: missing access_token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing access token",
            )

        logger.info(f"OAuth2 sync-user request: token={request.access_token[:10]}...")

        # Extract claims from token
        claims = await oauth2_service.extract_claims(request.access_token)
        if not claims:
            logger.warning("OAuth2 sync-user: token validation failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        # Sync user to database
        user_data = await oauth2_service.sync_user_from_authentik(
            claims=claims,
            ip_address=x_client_ip,
        )
        if not user_data:
            logger.error("OAuth2 sync-user: user sync failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sync user to database",
            )

        logger.info(f"OAuth2 sync-user success: user={user_data.get('email')}")

        return OAuth2SyncUserResponse(
            user_id=user_data.get("user_id"),
            email=user_data.get("email"),
            username=user_data.get("username"),
            roles=user_data.get("roles", []),
            org_id=user_data.get("org_id"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth2 sync-user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User sync failed",
        )


@router.post("/oauth2/refresh", response_model=RefreshResponse)
async def oauth2_refresh(request: OAuth2RefreshRequest):
    """
    Refresh access token using OAuth2 refresh token.

    This endpoint calls the Authentik refresh endpoint with a valid refresh token
    to obtain a new access token (and optionally a new refresh token).

    Process:
    1. Call Authentik refresh endpoint: POST ${AUTHENTIK_SERVER_URL}/application/o/token/
    2. Return { access_token, refresh_token }

    Args:
        refresh_token: Valid refresh token

    Returns:
        New access token and expiration

    Raises:
        401: Invalid or expired refresh token
        500: Server error during token refresh
    """
    try:
        from src.services.oauth2_service import oauth2_service

        if not request.refresh_token:
            logger.warning("OAuth2 refresh: missing refresh_token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing refresh token",
            )

        logger.info("OAuth2 refresh request: attempting token refresh")

        # Call Authentik refresh endpoint
        try:
            token_data = await oauth2_service.refresh_token(request.refresh_token)
        except ValueError as e:
            logger.warning(f"OAuth2 refresh: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

        # Extract tokens from response
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token", request.refresh_token)

        if not access_token:
            logger.error("OAuth2 refresh: no access token in response")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to obtain new access token",
            )

        logger.info("OAuth2 refresh success: tokens refreshed")

        return RefreshResponse(
            access_token=access_token,
            expires_in=auth_manager.access_token_expire_minutes * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth2 refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )
