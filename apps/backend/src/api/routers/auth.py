"""
Authentication routes for JWT-based security and Authentik OAuth2 integration.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta, timezone
import asyncio
import logging
import httpx
import secrets
import time
import uuid

from config.auth import (
    auth_manager,
    revoke_user_sessions,
    get_current_user, 
    get_current_active_user,
    User, 
    UserRole, 
    TokenData,
    require_admin,
    api_key_hash,
    E2E_ADMIN_ID,
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
    # Browsers send the fm_refresh cookie instead; the CLI, SDK and MCP send it here.
    refresh_token: Optional[str] = None


# The browser's refresh token lives in this HttpOnly cookie, out of reach of page
# scripts, so an XSS cannot read and replay a 30-day credential (audit S2, S3).
# Path /api covers the backend's own /api/v1/auth/* and the frontend proxy's
# /api/proxy/api/v1/auth/*; SameSite=Strict keeps other sites from sending it.
REFRESH_COOKIE = "fm_refresh"


def _set_refresh_cookie(response: Optional[Response], token: str) -> None:
    if response is None:
        return
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        max_age=auth_manager.refresh_token_expire_days * 86400,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        path="/api",
    )


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


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
async def login(login_data: LoginRequest, response: Response = None):
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
        user = await auth_manager.authenticate(login_data.email, login_data.password)
        if not user:
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
                "org_id": user.org_id,
            }
        }
        _set_refresh_cookie(response, response_data["refresh_token"])
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


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    # Signup is by invitation only; a new organisation comes from an approved
    # access request (POST /api/v1/register), never from this endpoint.
    invitation_token: str


def _check_password_length(password: str) -> None:
    """Signup and password reset share one rule; bcrypt reads at most 72 bytes."""
    if not 12 <= len(password.encode("utf-8")) <= 72:
        raise HTTPException(status_code=422, detail="Password must be 12 to 72 bytes long")


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, response: Response):
    """Create an account for someone holding an invitation, then sign them in.

    The account is created without an organization; the invitee then accepts the
    invitation (POST /organizations/invitations/{token}/accept). Holding the
    token, which only went to that address, is what verifies the email.
    """
    from config.database import get_db_transaction

    _check_password_length(payload.password)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name is required")

    user_id = str(uuid.uuid4())
    try:
        async with get_db_transaction() as db:
            invitation = await db.fetch_one(
                "SELECT id FROM org_invitations WHERE token = :token AND status = 'pending' "
                "AND expires_at > now() AND lower(email) = lower(:email)",
                {"token": payload.invitation_token, "email": payload.email},
            )
            if not invitation:
                raise HTTPException(
                    status_code=400,
                    detail="This invitation is invalid, expired, or for a different email address",
                )
            if await db.fetch_one("SELECT id FROM users WHERE lower(email) = lower(:e)", {"e": payload.email}):
                raise HTTPException(status_code=409, detail="An account with this email already exists")
            # The global role stays analyst, since admin is the platform operator;
            # org rights come from org_members when the invitation is accepted.
            await db.execute(
                "INSERT INTO users (id, email, username, name, password_hash, role, roles, is_active) "
                "VALUES (:id, :email, :username, :name, :pw, 'analyst', CAST(:roles AS jsonb), TRUE)",
                {
                    "id": user_id,
                    "email": payload.email,
                    "username": f"{payload.email.split('@')[0]}-{secrets.token_hex(3)}",
                    "name": name,
                    "pw": auth_manager.get_password_hash(payload.password),
                    "roles": '["analyst"]',
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Signup failed")

    logger.info(f"Signup by invitation: user={user_id}")
    return await login(LoginRequest(email=payload.email, password=payload.password), response)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: Request, refresh_data: RefreshRequest = RefreshRequest()):
    """A new access token for a refresh token from the body or the fm_refresh cookie."""
    try:
        token = refresh_data.refresh_token or request.cookies.get(REFRESH_COOKIE)
        if not token:
            raise TokenMissingException("No refresh token")
        access_token = await auth_manager.refresh_access_token(token)
        
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
    response: Response,
    current_user: TokenData = Depends(get_current_active_user),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """Logout user and revoke tokens using new JWT infrastructure."""
    response.delete_cookie(REFRESH_COOKIE, path="/api")
    try:
        # Revoke the current token, and end every session of this user: their refresh
        # tokens stop working (the blacklist alone needs Redis, which production lacks).
        if credentials and credentials.credentials:
            await auth_manager.revoke_token(credentials.credentials)
        await revoke_user_sessions(current_user.user_id)
        
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


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    password: str


_RESET_ANSWER = {"message": (
    "If that email belongs to an active account that signs in with a password, a link to reset it is on its way. "
    "Accounts that use single sign-on change their password with their identity provider."
)}
_RESET_WINDOW_SECONDS = 15 * 60
_RESET_MAX_PER_WINDOW = 5
_reset_requests: dict[str, list[float]] = {}


def _reset_rate_limited(*keys: str) -> bool:
    """True when any key already made _RESET_MAX_PER_WINDOW requests in the window."""
    # ponytail: per-process memory, so N workers allow N times the limit; move it to Redis when that matters.
    now = time.monotonic()
    if len(_reset_requests) > 10_000:
        for key in [k for k, times in _reset_requests.items() if now - times[-1] > _RESET_WINDOW_SECONDS]:
            del _reset_requests[key]
    recent = {k: [t for t in _reset_requests.get(k, []) if now - t < _RESET_WINDOW_SECONDS] for k in keys}
    if any(len(times) >= _RESET_MAX_PER_WINDOW for times in recent.values()):
        return True
    for key, times in recent.items():
        _reset_requests[key] = [*times, now]
    return False


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(payload: PasswordResetRequest, request: Request):
    """Email a single-use reset link. The answer is the same whether or not the account exists."""
    from config.database import get_db_connection
    from middleware.security import client_ip
    from src.application.services.api_boundary_dependencies import email_service

    if _reset_rate_limited(f"email:{payload.email.lower()}", f"ip:{client_ip(request)}"):
        raise HTTPException(status_code=429, detail="Too many reset requests. Try again in a few minutes.")

    # Only accounts that already sign in with a password: an SSO-only row (no
    # password_hash) must not gain a password that skips the identity provider.
    async with get_db_connection() as db:
        user = await db.fetch_one(
            "SELECT id, email, password_hash FROM users "
            "WHERE lower(email) = lower(:email) AND is_active AND COALESCE(password_hash, '') <> ''",
            {"email": payload.email},
        )
    if user:
        token = auth_manager.create_password_reset_token(str(user["id"]), user["password_hash"])
        # The token rides in the fragment, which browsers never send to a server.
        reset_url = f"{settings.frontend_url}/reset-password#token={token}"
        if email_service.api_key:
            asyncio.create_task(email_service.send_password_reset_email(
                user["email"], reset_url, auth_manager.password_reset_expire_minutes
            ))
        else:
            logger.warning("Password reset requested for an existing account but RESEND_API_KEY is not set; no email was sent")
    return _RESET_ANSWER


@router.post("/password-reset")
async def reset_password(payload: PasswordResetConfirm):
    """Set a new password with a token from /password-reset/request; the token then stops working."""
    from config.database import get_db_connection

    _check_password_length(payload.password)
    invalid = HTTPException(status_code=400, detail="This reset link is invalid or has expired. Request a new one.")
    claims = auth_manager.read_password_reset_token(payload.token)
    if not claims:
        raise invalid
    async with get_db_connection() as db:
        user = await db.fetch_one(
            "SELECT password_hash FROM users WHERE id = :id AND is_active AND COALESCE(password_hash, '') <> ''",
            {"id": claims["sub"]},
        )
        if not user or not secrets.compare_digest(
            claims["pwd"], auth_manager.password_fingerprint(user["password_hash"])
        ):
            raise invalid
        # Compare-and-set on the old hash: of two concurrent uses of one token, only one lands.
        changed = await db.fetch_one(
            # Bumping token_version signs out every existing session along with the old password.
            "UPDATE users SET password_hash = :new, token_version = COALESCE(token_version, 0) + 1 "
            "WHERE id = :id AND password_hash = :old RETURNING id",
            {
                "new": auth_manager.get_password_hash(payload.password),
                "id": claims["sub"],
                "old": user["password_hash"],
            },
        )
    if not changed:
        raise invalid
    logger.info(f"Password reset for user {claims['sub']}")
    return {"message": "Your password has been changed. Sign in with the new password."}


@router.post("/callback", response_model=AuthentikCallbackResponse)
async def authentik_oauth_callback(
    code: str = Query(..., description="Authorization code from Authentik"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    response: Response = None,
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

    if not (settings.authentik_server_url and settings.authentik_oauth_client_id
            and settings.authentik_oauth_client_secret and settings.authentik_oauth_redirect_uri):
        logger.error(
            "Authentik callback refused: set AUTHENTIK_SERVER_URL, AUTHENTIK_OAUTH_CLIENT_ID, "
            "AUTHENTIK_OAUTH_CLIENT_SECRET and AUTHENTIK_OAUTH_REDIRECT_URI"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentik sign-in is not configured on this server"
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

        async with httpx.AsyncClient(timeout=10) as client:
            token_response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.authentik_oauth_redirect_uri,
                    "client_id": settings.authentik_oauth_client_id,
                    "client_secret": settings.authentik_oauth_client_secret,
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

        # The IdP proves who the person is; FairMind decides what they may do.
        # Sign them in as their existing account (made by an invitation or an
        # approved access request), with the platform role and org memberships
        # stored here. IdP groups grant nothing: a group could otherwise make
        # anyone added to it an admin of every tenant.
        email = (payload.get("email") or "").strip()
        user = await auth_manager.get_user_by_email(email) if email else None
        if not user or not user.is_active:
            logger.warning("Authentik sign-in refused: no active FairMind account for this email")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No FairMind account uses this email. Ask your organisation admin for an invitation, or request access.",
            )

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
                "last_login": datetime.utcnow().isoformat()
            },
            ttl=86400  # 24 hours
        )

        logger.info(f"User authenticated via Authentik: {user.email}")

        _set_refresh_cookie(response, refresh_token)
        return AuthentikCallbackResponse(
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
    """Create an API key for programmatic access. Only its hash is stored."""
    from config.database import get_db_transaction

    try:
        # Get full user data
        user_data = await auth_manager.get_user_by_id(current_user.user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if user_data.id == E2E_ADMIN_ID:
            # Keys are rows tied to a users row, and the E2E admin is never stored.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The E2E admin has no stored account, so it cannot hold API keys. Sign in as a registered user."
            )
        
        api_key = auth_manager.create_api_key(user_data, api_key_data.name)
        created_at = datetime.now(timezone.utc)  # api_keys timestamps are timestamptz
        expires_at = created_at + timedelta(days=auth_manager.api_key_expire_days)
        async with get_db_transaction() as db:
            if await db.fetch_one(
                "SELECT id FROM api_keys WHERE user_id = :user AND name = :name",
                {"user": current_user.user_id, "name": api_key_data.name},
            ):
                raise HTTPException(status_code=409, detail="You already have an API key with this name")
            await db.execute(
                "INSERT INTO api_keys (id, user_id, name, description, key_hash, is_active, created_at, expires_at) "
                "VALUES (:id, :user, :name, :description, :hash, TRUE, :created, :expires)",
                {
                    "id": str(uuid.uuid4()),
                    "user": current_user.user_id,
                    "name": api_key_data.name,
                    "description": api_key_data.description,
                    "hash": api_key_hash(api_key),
                    "created": created_at,
                    "expires": expires_at,
                },
            )
        
        logger.info("API key created for user %s", current_user.user_id)
        
        return APIKeyResponse(
            api_key=api_key,
            name=api_key_data.name,
            created_at=created_at,
            expires_at=expires_at
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
    """List the caller's API keys (never the keys themselves)."""
    from config.database import get_db_connection

    try:
        async with get_db_connection() as db:
            rows = await db.fetch_all(
                "SELECT name, description, created_at, expires_at FROM api_keys "
                "WHERE user_id = :user ORDER BY created_at DESC",
                {"user": current_user.user_id},
            )
        return {
            "api_keys": [
                {
                    "name": r["name"],
                    "description": r["description"],
                    "created_at": r["created_at"],
                    "expires_at": r["expires_at"],
                }
                for r in rows
            ]
        }
        
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
    """Revoke an API key. Deleting its row makes the key fail on its next request."""
    from config.database import get_db_connection

    try:
        async with get_db_connection() as db:
            revoked = await db.fetch_one(
                "DELETE FROM api_keys WHERE user_id = :user AND name = :name RETURNING id",
                {"user": current_user.user_id, "name": key_name},
            )
        if not revoked:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
        
        logger.info(f"API key revoked for user {current_user.email}: {key_name}")
        
        return {"message": f"API key '{key_name}' revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke API key error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )


@router.post("/users", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def create_user():
    """Not implemented. Accounts come from signup (POST /api/v1/auth/register), approved
    access requests (POST /api/v1/registrations/{id}/approve) and organisation
    invitations (POST /api/v1/organizations/{org_id}/members/invite)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Users are not created here. Invite them with POST /api/v1/organizations/{org_id}/members/invite.",
    )


@router.get("/users")
async def list_users(
    current_user: TokenData = Depends(require_admin)
):
    """List the users of the caller's organisation (admin only). Returns users from DB or cache."""
    try:
        if not current_user.org_id:
            return {"users": []}
        # Query users from DB if available
        try:
            from api.routes.org_scope import ORG_MEMBER_USER_IDS, plain_id
            from config.database import get_db
            from sqlalchemy import text
            async with get_db() as db:
                result = await db.execute(
                    text(
                        "SELECT id, email, username, name, roles, is_active, last_login, created_at FROM users "
                        f"WHERE {plain_id('id')} IN ({ORG_MEMBER_USER_IDS}) "
                        "ORDER BY created_at DESC LIMIT 100"
                    ),
                    {"org_id": str(current_user.org_id)},
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
            "error": "Health check failed; see the server log",
            "timestamp": datetime.utcnow().isoformat()
        }
