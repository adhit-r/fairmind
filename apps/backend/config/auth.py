"""
JWT Authentication configuration for production security.
Updated to use the new secure JWT infrastructure.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
import logging
import secrets
import uuid
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
class _Bcrypt:
    """bcrypt hashing without passlib, whose 1.7.4 release breaks on bcrypt>=4.1."""

    @staticmethod
    def hash(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        # bcrypt reads at most 72 bytes; refuse longer input instead of truncating it.
        secret = password.encode("utf-8")
        if len(secret) > 72:
            return False
        return bcrypt.checkpw(secret, hashed.encode("ascii"))


pwd_context = _Bcrypt()

# JWT Security: disable auto-error so we normalize auth failures to 401 via our JWT exceptions.
security = HTTPBearer(auto_error=False)


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


class PrincipalKind(str, Enum):
    """Security boundary between interactive users and service identities."""

    HUMAN = "human"
    SERVICE = "service"


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
    org_id: Optional[str] = None


class TokenData(BaseModel):
    """Token payload data."""
    user_id: str
    email: str
    role: UserRole
    token_type: TokenType
    principal_kind: PrincipalKind = PrincipalKind.HUMAN
    organization_id: Optional[str] = None
    exp: datetime
    iat: datetime
    permissions: List[str] = []
    org_id: Optional[str] = None


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
            "sub": user.id,
            "user_id": user.id,
            "org_id": user.org_id,
            "email": user.email,
            "roles": [user.role.value],
            "permissions": user.permissions,
            "token_type": TokenType.ACCESS.value,
            "principal_kind": PrincipalKind.HUMAN.value,
        }
        
        return self.jwt_manager.create_token(payload, expires_delta)
    
    def create_refresh_token(self, user: User) -> str:
        """Create a refresh token using new JWT infrastructure."""
        expires_delta = timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user.id,
            "user_id": user.id,
            "org_id": user.org_id,
            "email": user.email,
            "roles": [user.role.value],
            "token_type": TokenType.REFRESH.value,
            "principal_kind": PrincipalKind.HUMAN.value,
        }
        
        return self.jwt_manager.create_token(payload, expires_delta)
    
    def create_api_key(self, user: User, name: str) -> str:
        """Create an API key using new JWT infrastructure."""
        expires_delta = timedelta(days=self.api_key_expire_days)
        
        payload = {
            "sub": user.id,
            "user_id": user.id,
            "org_id": user.org_id,
            "email": user.email,
            "roles": [user.role.value],
            "permissions": user.permissions,
            "token_type": TokenType.API_KEY.value,
            "principal_kind": PrincipalKind.HUMAN.value,
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
            subject = payload.get("sub")
            email = payload.get("email")
            roles = payload.get("roles", [])
            token_type = payload.get("token_type", TokenType.ACCESS.value)
            principal_kind = payload.get("principal_kind", PrincipalKind.HUMAN.value)
            organization_id = payload.get("organization_id")
            exp = payload.get("exp")
            iat = payload.get("iat")
            permissions = payload.get("permissions", [])
            org_id = payload.get("org_id")
            
            if user_id is None or subject is None or email is None:
                raise InvalidTokenException("Invalid token payload")
            if not str(user_id).strip() or str(subject) != str(user_id):
                raise InvalidTokenException("Token subject does not match user identity")
            try:
                parsed_principal_kind = PrincipalKind(principal_kind)
            except (TypeError, ValueError) as error:
                raise InvalidTokenException("Invalid principal kind") from error
            if parsed_principal_kind is PrincipalKind.SERVICE and (
                not isinstance(organization_id, str)
                or not organization_id.strip()
                or organization_id != organization_id.strip()
            ):
                raise InvalidTokenException("Service principal organization is invalid")
            
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
                principal_kind=parsed_principal_kind,
                organization_id=organization_id,
                exp=exp_dt,
                iat=iat_dt,
                permissions=permissions,
                org_id=str(org_id) if org_id else None,
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
            if token_data.principal_kind is not PrincipalKind.HUMAN:
                raise InvalidTokenException("Human refresh token required")
            
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
        """Load a user from the users table by id."""
        if not user_id:
            return None
        if user_id == E2E_ADMIN_ID:
            return _e2e_admin()
        row = await _fetch_user_row("u.id = :key", str(user_id))
        return _user_from_row(row) if row else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Load a user from the users table by email (case-insensitive)."""
        if not email:
            return None
        e2e = _e2e_admin()
        if e2e and email.lower() == e2e.email.lower():
            return e2e
        row = await _fetch_user_row("lower(u.email) = lower(:key)", email)
        return _user_from_row(row) if row else None

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Verify email and password against the users table."""
        e2e = _e2e_admin()
        if e2e and email.lower() == e2e.email.lower():
            return e2e if secrets.compare_digest(password, settings.e2e_admin_password or "") else None
        row = await _fetch_user_row("lower(u.email) = lower(:key)", email)
        if not row or not row["is_active"] or not row["password_hash"]:
            return None
        try:
            if not pwd_context.verify(password, row["password_hash"]):
                return None
        except (ValueError, TypeError):
            # Malformed or unknown hash scheme: never a match.
            return None
        return _user_from_row(row)

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


_USER_COLUMNS = (
    "u.id, u.email, u.username, u.role, u.is_active, u.created_at, u.last_login, "
    "u.permissions, u.password_hash, "
    "COALESCE(u.org_id, u.primary_org_id, "
    "(SELECT m.org_id FROM org_members m WHERE m.user_id = u.id AND m.status = 'active' "
    "ORDER BY m.joined_at LIMIT 1)) AS resolved_org_id, "
    "(SELECT m.role FROM org_members m WHERE m.user_id = u.id AND m.status = 'active' "
    "ORDER BY m.joined_at LIMIT 1) AS resolved_org_role"
)


async def _fetch_user_row(where: str, key: str):
    from .database import get_db_connection
    async with get_db_connection() as db:
        return await db.fetch_one(f"SELECT {_USER_COLUMNS} FROM users u WHERE {where}", {"key": key})


E2E_ADMIN_ID = "e2e-admin"


def _e2e_admin() -> Optional[User]:
    """The CI end-to-end admin: development only, enabled by E2E_ADMIN_EMAIL and
    E2E_ADMIN_PASSWORD, never written to any table. Replaces the hard-coded
    admin login that used to live in the login route."""
    email, password = settings.e2e_admin_email, settings.e2e_admin_password
    if not (settings.is_development and email and password):
        return None
    return User(
        id=E2E_ADMIN_ID,
        email=email,
        username="e2e-admin",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        permissions=["*"],
        org_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"fairmind-e2e:{email.lower()}")),
    )


def _user_from_row(row) -> User:
    try:
        role = UserRole(row["role"])
    except ValueError:
        role = UserRole.VIEWER
    permissions = row["permissions"] or []
    if isinstance(permissions, str):
        import json
        permissions = json.loads(permissions)
    if role == UserRole.ADMIN and "*" not in permissions:
        permissions = [*permissions, "*"]
    try:
        org_role = row["resolved_org_role"]
    except (KeyError, IndexError):
        org_role = None
    if org_role in ("owner", "admin") and "model:write" not in permissions:
        # Org owners and admins may change governance records
        # (GovernanceAssuranceService.may_mutate); every token they mint carries it.
        permissions = [*permissions, "model:write"]
    return User(
        id=str(row["id"]),
        email=row["email"],
        username=row["username"],
        role=role,
        is_active=bool(row["is_active"]),
        created_at=row["created_at"] or datetime.now(timezone.utc),
        last_login=row["last_login"],
        permissions=permissions,
        org_id=str(row["resolved_org_id"]) if row["resolved_org_id"] else None,
    )


# Global auth manager instance
auth_manager = AuthManager()


# FastAPI Dependencies
async def get_verified_principal(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> TokenData:
    """Project one signature-verified bearer without assuming its purpose."""
    # JWTAuthenticationMiddleware already verified this request (or signed it in
    # for local development); reuse its result instead of verifying twice.
    state_user = getattr(request.state, "user", None)
    if isinstance(state_user, TokenData) and getattr(request.state, "authenticated", False):
        return state_user
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


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> TokenData:
    """Return a verified human principal for legacy user-facing dependencies."""

    current_principal = await get_verified_principal(request, credentials)
    if current_principal.principal_kind is not PrincipalKind.HUMAN:
        raise InvalidTokenException("Human principal required")
    return current_principal


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """Return a human session authenticated with an access token."""
    # API keys (POST /api/v1/auth/api-keys) authorise requests like access tokens;
    # only refresh tokens and service principals are turned away here.
    if (
        current_user.token_type not in (TokenType.ACCESS, TokenType.API_KEY)
        or current_user.principal_kind is not PrincipalKind.HUMAN
    ):
        raise InvalidTokenException("Human access token required")
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
