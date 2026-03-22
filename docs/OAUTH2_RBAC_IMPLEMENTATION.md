# OAuth2 RBAC Integration — Week 1 Day 3-4 Implementation

## Overview

This document describes the implementation of three critical OAuth2 endpoints for RBAC integration with Authentik.

## Implemented Endpoints

### 1. POST `/api/v1/auth/oauth2/validate`

**Purpose**: Exchange Authentik OAuth2 code for JWT tokens and synchronize user to database.

**Request**:
```json
{
  "code": "string (authorization code from Authentik)",
  "state": "string (CSRF protection)",
  "code_verifier": "string (PKCE code verifier, optional)"
}
```

**Response** (200 OK):
```json
{
  "access_token": "string (FairMind JWT)",
  "refresh_token": "string (FairMind JWT)",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "john.doe",
    "roles": ["admin", "analyst"],
    "org_id": "uuid (optional)"
  }
}
```

**Process Flow**:
1. Validate state parameter for CSRF protection (5-minute TTL)
2. Exchange code for tokens via Authentik token endpoint
3. Validate JWT signature with JWKS (RS256)
4. Extract claims: user ID, email, groups (roles), org assignment
5. Check if user exists in FairMind users table:
   - If exists: UPDATE roles, last_login, last_ip
   - If new: INSERT new user with authentik_id, roles from Authentik groups
6. Create FairMind JWT tokens (access + refresh)
7. Return tokens and user info

**Error Responses**:
- `400 Bad Request`: Missing code or state, invalid input
- `403 Forbidden`: Invalid or expired state (CSRF check failed)
- `502 Bad Gateway`: Failed to connect to Authentik, JWKS validation failed
- `500 Internal Server Error`: Database sync failed, token creation failed

**Key Features**:
- CSRF protection via state validation
- PKCE support for enhanced security
- Automatic user creation/update
- Role mapping from Authentik groups to FairMind roles
- IP address tracking for audit trail

---

### 2. POST `/api/v1/auth/oauth2/sync-user`

**Purpose**: Sync Authentik user data (roles, email, name) to FairMind database.

**Request**:
```json
{
  "access_token": "string (Authentik JWT)",
  "org_id": "uuid (optional, to assign user to org)"
}
```

**Response** (200 OK):
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "username": "john.doe",
  "roles": ["admin", "analyst"],
  "org_id": "uuid (optional)"
}
```

**Process Flow**:
1. Validate JWT with JWKS
2. Extract claims from token
3. UPDATE user in DB with fresh data from Authentik
4. Return synced user object

**Error Responses**:
- `400 Bad Request`: Missing access_token
- `401 Unauthorized`: Invalid or expired token
- `500 Internal Server Error`: User sync failed

**Key Features**:
- Keeps FairMind database in sync with Authentik
- Updates roles, groups, email, and other user data
- Can optionally assign user to organization
- Useful for periodic sync or after Authentik changes

---

### 3. POST `/api/v1/auth/oauth2/refresh`

**Purpose**: Refresh expired access token using refresh token.

**Request**:
```json
{
  "refresh_token": "string (refresh token)"
}
```

**Response** (200 OK):
```json
{
  "access_token": "string (new FairMind JWT)",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Process Flow**:
1. Call Authentik refresh endpoint: `POST ${AUTHENTIK_SERVER_URL}/application/o/token/`
2. Return new access token

**Error Responses**:
- `400 Bad Request`: Missing refresh_token
- `401 Unauthorized`: Invalid or expired refresh token
- `502 Bad Gateway`: Failed to connect to Authentik
- `500 Internal Server Error`: Token refresh failed

**Key Features**:
- Seamless token refresh without re-authentication
- Maintains user sessions
- Supports optional refresh token rotation

---

## Implementation Details

### Service Layer: OAuth2Service

Located at: `src/services/oauth2_service.py`

**Methods**:
- `generate_state()` - Generate CSRF state parameter
- `validate_state(state)` - Validate state (CSRF protection)
- `exchange_code_for_tokens(code, state, code_verifier)` - Exchange code for tokens
- `validate_token_with_jwks(token)` - Validate JWT with JWKS
- `extract_claims(token)` - Extract claims from token
- `sync_user_from_authentik(claims, ip_address)` - Sync user to DB
- `refresh_token(refresh_token)` - Refresh expired token

**Key Features**:
- JWKS caching (1 hour TTL)
- CSRF state validation with 5-minute expiration
- Async HTTP client (httpx) for Authentik communication
- Integration with UserSyncService for database operations
- Role mapping from Authentik groups to FairMind roles

### Database Models

**User Table** (existing, enhanced with Authentik fields):
```python
class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True)
    authentik_id = Column(String, unique=True, index=True)  # Authentik user UUID
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    name = Column(String)

    # Roles and permissions from Authentik
    roles = Column(JSON, default=list)  # ["admin", "analyst", "viewer"]
    groups = Column(JSON, default=list)  # Authentik groups
    permissions = Column(JSON, default=list)  # Computed permissions

    # Organization relationships
    primary_org_id = Column(UUID, ForeignKey('organizations.id'))
    org_id = Column(UUID, ForeignKey('organizations.id'))

    # Audit trail
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)
    last_ip = Column(String)
    last_sync = Column(DateTime)
    authentik_data = Column(JSON)  # Store full Authentik user object
```

### Configuration

**Settings** (config/settings.py):
```python
# Authentik Configuration
authentik_enabled: bool = False
authentik_server_url: Optional[str] = None
authentik_jwks_url: Optional[str] = None
authentik_issuer: Optional[str] = None
authentik_audience: Optional[str] = None
authentik_jwt_algorithm: str = "RS256"
authentik_jwks_cache_ttl: int = 3600  # 1 hour
authentik_oauth_client_id: Optional[str] = "fairmind-frontend"
authentik_oauth_client_secret: Optional[str] = None
authentik_oauth_redirect_uri: Optional[str] = "http://localhost:3000/auth/callback"
authentik_token_endpoint: Optional[str] = None
authentik_refresh_token_ttl: int = 604800  # 7 days
```

**JWKS Cache** (config/authentik_config.py):
- 1 hour TTL with automatic refresh
- Fallback to Authentik if cache miss
- Error handling if Authentik unreachable

---

## Testing

### Prerequisites

1. **Authentik Setup**:
   - Authentik server running (e.g., `https://authentik.example.com`)
   - OAuth2 application configured in Authentik with:
     - Client ID: `fairmind-frontend`
     - Client Secret: (set in env var `AUTHENTIK_OAUTH_CLIENT_SECRET`)
     - Redirect URI: `http://localhost:3000/auth/callback`
   - JWKS endpoint available: `${AUTHENTIK_SERVER_URL}/application/o/connect/jwks/`

2. **Environment Variables**:
```bash
AUTHENTIK_ENABLED=true
AUTHENTIK_SERVER_URL=https://authentik.example.com
AUTHENTIK_JWKS_URL=https://authentik.example.com/application/o/connect/jwks/
AUTHENTIK_ISSUER=https://authentik.example.com
AUTHENTIK_AUDIENCE=fairmind-frontend
AUTHENTIK_OAUTH_CLIENT_ID=fairmind-frontend
AUTHENTIK_OAUTH_CLIENT_SECRET=your-secret-here
AUTHENTIK_OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback
```

3. **Database**:
   - PostgreSQL or SQLite for development
   - Users table created with Authentik integration fields

### Manual Testing with cURL

#### 1. Test OAuth2 Validate Endpoint

First, generate a state:
```bash
STATE=$(openssl rand -hex 16)
echo "State: $STATE"
```

Get authorization code from Authentik (in browser):
```
https://authentik.example.com/application/o/authorize/?client_id=fairmind-frontend&response_type=code&scope=openid&state=$STATE&redirect_uri=http://localhost:3000/auth/callback
```

Then validate the code:
```bash
curl -X POST http://localhost:8000/api/v1/auth/oauth2/validate \
  -H "Content-Type: application/json" \
  -d '{
    "code": "your-auth-code-here",
    "state": "your-state-here",
    "code_verifier": "optional-pkce-verifier"
  }'
```

**Expected Response**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "john.doe",
    "roles": ["admin"],
    "org_id": null
  }
}
```

#### 2. Test OAuth2 Sync User Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/auth/oauth2/sync-user \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "your-access-token-here",
    "org_id": "optional-org-uuid"
  }'
```

**Expected Response**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "john.doe",
  "roles": ["admin"],
  "org_id": null
}
```

#### 3. Test OAuth2 Refresh Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/auth/oauth2/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your-refresh-token-here"
  }'
```

**Expected Response**:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Test Users in Authentik

Create test users in Authentik with these group memberships:

1. **admin_test**
   - Email: admin_test@example.com
   - Groups: `fairmind-admin`
   - Expected roles in FairMind: `["admin"]`

2. **analyst_test**
   - Email: analyst_test@example.com
   - Groups: `fairmind-analyst`
   - Expected roles in FairMind: `["analyst"]`

3. **viewer_test**
   - Email: viewer_test@example.com
   - Groups: `fairmind-viewer`
   - Expected roles in FairMind: `["viewer"]`

### Logging

All operations are logged with DEBUG level in `fairmind.oauth2`:
```bash
# View logs during testing
tail -f logs/fairmind.log | grep "oauth2"
```

Key log messages:
- `OAuth2 validate request: code=...`
- `State validated successfully`
- `Token validated successfully for user: ...`
- `Claims extracted for user: ...`
- `User synced successfully: ...`
- `OAuth2 validate success: user=...`

---

## Security Considerations

### CSRF Protection
- State parameter generated with `secrets.token_urlsafe(32)`
- State expires after 5 minutes
- One-time use per state (replay attack prevention)
- Stored in in-memory cache (thread-safe)

### JWT Validation
- Signature validation with JWKS (RS256)
- Issuer validation (`iss` claim)
- Audience validation (`aud` claim)
- Expiration validation (`exp` claim)

### User Synchronization
- Authentik ID used as primary key for user lookup
- Email uniqueness enforced at database level
- IP address captured for audit trail
- Last login timestamp updated on each auth

### Refresh Token Handling
- Refresh tokens managed by Authentik
- FairMind respects refresh token TTL (7 days default)
- No token rotation (can be added in future)

---

## Error Handling

### HTTP Status Codes
- `200`: Success
- `400`: Bad request (validation errors)
- `401`: Unauthorized (invalid/expired token)
- `403`: Forbidden (CSRF check failed)
- `500`: Internal server error (database, config issues)
- `502`: Bad gateway (Authentik unavailable, JWKS unreachable)

### Exception Handling
- All HTTP exceptions are logged with context
- ValueError raised for validation failures
- DatabaseError exceptions handled gracefully
- Authentik connection errors return 502

---

## Future Enhancements

1. **Refresh Token Rotation**: Implement automatic rotation on refresh
2. **User Deprovisioning**: Handle user deletion from Authentik
3. **Group Sync**: Periodic background sync of Authentik groups
4. **Multi-Org Support**: Enhanced org assignment from Authentik groups
5. **Audit Logging**: Detailed audit trail of OAuth2 operations
6. **Rate Limiting**: API rate limits for auth endpoints
7. **Token Revocation**: Explicit token revocation endpoint
8. **Social Login**: Additional OAuth2 providers (Google, GitHub)

---

## Troubleshooting

### State Validation Failed
- **Issue**: "Invalid or expired state parameter"
- **Cause**: State expired (>5 minutes) or not found
- **Fix**: Regenerate new state and retry

### JWKS Fetch Failed
- **Issue**: "Failed to fetch JWKS" in logs
- **Cause**: Authentik unreachable or misconfigured JWKS URL
- **Fix**: Verify `AUTHENTIK_JWKS_URL` and network connectivity

### User Sync Failed
- **Issue**: "Failed to sync user to database"
- **Cause**: Database issues, missing fields, or constraint violation
- **Fix**: Check database logs, verify required fields in token claims

### Token Validation Failed
- **Issue**: "Invalid or expired token"
- **Cause**: Token expired, signature invalid, or claims mismatch
- **Fix**: Get fresh token via code exchange, check Authentik config

---

## Files Modified/Created

### New Files
- `src/services/oauth2_service.py` — OAuth2 service implementation

### Modified Files
- `src/api/routers/auth.py` — Added three OAuth2 endpoints
- `config/settings.py` — Added Authentik token endpoint config
- `api/main.py` — Added Authentik initialization in lifespan

### No Changes Required
- `src/infrastructure/db/database/models.py` — User model already supports Authentik
- `config/authentik_config.py` — Already has JWKS validation
- `src/services/user_sync_service.py` — Already handles user sync
