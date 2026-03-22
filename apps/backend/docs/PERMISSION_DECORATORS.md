# Permission Decorator System

Fine-grained permission checking for organization-scoped endpoints in FairMind.

## Overview

The permission decorator system enforces role-based access control (RBAC) at the endpoint level using composable decorators that stack left-to-right.

**File**: `/apps/backend/core/decorators/org_permissions.py`

## Architecture

### Decorator Stack Order

Decorators are applied in this order (top-to-bottom on the function):

```python
@router.delete("/{org_id}/members/{member_id}")
@isolate_by_org                                    # 1. Establish org context
@require_org_admin                                 # 2. Permission check
@audit_org_action("remove_member", "org_member")  # 3. Audit logging
async def remove_member(org_id: str, request: Request, db):
    ...
```

### Data Flow

```
Request → Auth Middleware → OrgIsolationMiddleware → Endpoint
           ↓                    ↓                        ↓
         user payload      org_id + user_id        Permission check
                                                    (decorators)
                                                         ↓
                                                    Audit log
```

## Decorators

### 1. `@require_org_owner`

**Purpose**: Only organization owner can access.

**Database Query**:
```sql
SELECT owner_id FROM organizations WHERE id = :org_id
```

**Usage**:
```python
@router.delete("/{org_id}")
@isolate_by_org
@require_org_owner
async def delete_org(org_id: str, request: Request, db):
    """Delete organization. Only owner can perform this."""
    ...
```

**Error**: `403 Forbidden` - "Only organization owner can perform this action"

---

### 2. `@require_org_admin`

**Purpose**: Admin or owner of the organization can access.

**Database Query**:
```sql
SELECT role FROM org_members WHERE org_id = :org_id AND user_id = :user_id
```

**Allowed Roles**: `admin`, `owner`

**Usage**:
```python
@router.post("/{org_id}/members")
@isolate_by_org
@require_org_admin
async def invite_member(org_id: str, payload: InvitePayload, request: Request, db):
    """Invite new member to org. Admin only."""
    ...
```

**Error**: `403 Forbidden` - "Admin access required"

---

### 3. `@require_org_member`

**Purpose**: Any member of the organization can access.

**Database Query**:
```sql
SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id
```

**Usage**:
```python
@router.get("/{org_id}/dashboard")
@isolate_by_org
@require_org_member
async def get_dashboard(org_id: str, request: Request, db):
    """Get org dashboard. Members only."""
    ...
```

**Error**: `403 Forbidden` - "Not a member of this organization"

---

### 4. `@require_permission(permission_string)`

**Purpose**: User must have a specific permission in their role.

**Permission Format**: `"resource:action"` (e.g., `"members:invite"`, `"reports:export"`)

**Database Queries**:
```sql
-- 1. Get user's role
SELECT role FROM org_members
WHERE org_id = :org_id AND user_id = :user_id

-- 2. Get role's permissions
SELECT permissions FROM org_roles
WHERE org_id = :org_id AND name = :role_name
-- permissions is a JSON array: ["members:invite", "members:remove", ...]
```

**Usage**:
```python
@router.post("/{org_id}/members/invite")
@isolate_by_org
@require_permission("members:invite")
async def invite_member(org_id: str, payload: InvitePayload, request: Request, db):
    """Invite member. Requires members:invite permission."""
    ...
```

**Error**: `403 Forbidden` - "Missing permission: members:invite"

---

### 5. `@require_permissions(permissions_list, require_all=True)`

**Purpose**: User must have multiple permissions (AND/OR logic).

**Parameters**:
- `permissions_list`: List of permission strings
- `require_all=True`: User must have ALL permissions (AND)
- `require_all=False`: User must have AT LEAST ONE permission (OR)

**Usage - AND Logic (All Required)**:
```python
@router.post("/{org_id}/reports/export")
@isolate_by_org
@require_permissions(["reports:view", "reports:export"])
async def export_report(org_id: str, request: Request, db):
    """Export report. User must have both view AND export permissions."""
    ...
```

**Usage - OR Logic (Any One Required)**:
```python
@router.get("/{org_id}/reports")
@isolate_by_org
@require_permissions(["reports:view", "reports:admin"], require_all=False)
async def list_reports(org_id: str, request: Request, db):
    """List reports. User must have either view OR admin permission."""
    ...
```

**Error (AND)**: `403 Forbidden` - "Missing permissions: reports:export, ..."
**Error (OR)**: `403 Forbidden` - "Must have one of: reports:view, reports:admin"

---

### 6. `@audit_org_action(action, resource_type=None)`

**Purpose**: Log organization actions to audit trail for compliance.

**Parameters**:
- `action`: Action name (e.g., `"invite_member"`, `"export_report"`)
- `resource_type`: Optional resource type (e.g., `"org_member"`, `"compliance_report"`)

**Database Query** (on success):
```sql
INSERT INTO org_audit_logs
(org_id, user_id, action, resource_type, status, ip_address, created_at)
VALUES (:org_id, :user_id, :action, :resource_type, 'success', :ip_address, NOW())
```

**Database Query** (on failure):
```sql
INSERT INTO org_audit_logs
(org_id, user_id, action, resource_type, status, error_message, ip_address, created_at)
VALUES (:org_id, :user_id, :action, :resource_type, 'failure', :error, :ip_address, NOW())
```

**Usage**:
```python
@router.delete("/{org_id}/members/{member_id}")
@isolate_by_org
@require_org_admin
@audit_org_action("remove_member", "org_member")
async def remove_member(org_id: str, member_id: str, request: Request, db):
    """Remove member from org. Action is audited."""
    ...
```

**Logged Data**:
- `org_id`: Organization UUID
- `user_id`: Acting user UUID
- `action`: "remove_member"
- `resource_type`: "org_member"
- `status`: "success" or "failure"
- `ip_address`: Client IP (from X-Forwarded-For, X-Real-IP, or request.client.host)
- `error_message`: Exception message (if failed, truncated to 500 chars)
- `created_at`: Timestamp

**Notes**:
- Logs both successful and failed action attempts
- Audit logging failures do NOT break the request (graceful degradation)
- IP extraction hierarchy: `X-Forwarded-For` → `X-Real-IP` → `request.client.host`
- Permission denied errors from other decorators are NOT logged (exception before execution)

---

## Database Schema Requirements

### org_members Table

```sql
CREATE TABLE org_members (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(50) NOT NULL DEFAULT 'member',  -- admin, owner, member, etc.
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    joined_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_org_members_org_user ON org_members(org_id, user_id);
```

### org_roles Table

```sql
CREATE TABLE org_roles (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(id),
    name VARCHAR(100) NOT NULL,                     -- role name (admin, member, etc.)
    description TEXT,
    permissions JSON NOT NULL DEFAULT '[]',        -- ["members:invite", "reports:view", ...]
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_org_roles_org_name ON org_roles(org_id, name);
```

### org_audit_logs Table

```sql
CREATE TABLE org_audit_logs (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,                  -- invite_member, remove_member, etc.
    resource_type VARCHAR(50),                     -- org_member, report, etc.
    resource_id UUID,
    status VARCHAR(20) NOT NULL DEFAULT 'success', -- success, failure
    error_message TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW() INDEX
);

CREATE INDEX idx_org_audit_logs_org_id ON org_audit_logs(org_id);
CREATE INDEX idx_org_audit_logs_user_id ON org_audit_logs(user_id);
CREATE INDEX idx_org_audit_logs_created_at ON org_audit_logs(created_at);
```

### organizations Table

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    owner_id UUID NOT NULL REFERENCES users(id),  -- @require_org_owner checks this
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## Error Handling

### PermissionDenied Exception

All decorators raise `PermissionDenied` (HTTP 403 Forbidden) with descriptive messages:

```python
from core.decorators import PermissionDenied

try:
    # Endpoint call
    ...
except PermissionDenied as e:
    # e.status_code == 403
    # e.detail == "Detailed message"
```

### Database Errors

If database queries fail:
- Permission check decorators: raise `PermissionDenied("Permission check failed")`
- Audit action decorator: log error but don't raise (graceful degradation)

### Missing Context

If user_id or org_id are missing from request:
- Raise `PermissionDenied("Missing user or organization context")`
- This should not happen if middleware is configured correctly

---

## Permission Constants

Define permission strings as constants for consistency:

```python
# src/domain/organization/constants.py

class OrgPermissions:
    """Organization permission strings."""

    # Member management
    MEMBERS_INVITE = "members:invite"
    MEMBERS_REMOVE = "members:remove"
    MEMBERS_UPDATE = "members:update"

    # Reports
    REPORTS_VIEW = "reports:view"
    REPORTS_EXPORT = "reports:export"
    REPORTS_SCHEDULE = "reports:schedule"

    # Compliance
    COMPLIANCE_VIEW = "compliance:view"
    COMPLIANCE_AUDIT = "compliance:audit"

    # Settings
    SETTINGS_EDIT = "settings:edit"
    SETTINGS_DELETE = "settings:delete"
```

Then use in decorators:

```python
from src.domain.organization.constants import OrgPermissions

@router.post("/{org_id}/members/invite")
@isolate_by_org
@require_permission(OrgPermissions.MEMBERS_INVITE)
async def invite_member(...):
    ...
```

---

## Middleware Integration

### Required Middleware Stack

The decorators require these middleware to be configured first:

```python
# api/main.py

from fastapi import FastAPI
from core.middleware.auth import NeonAuthMiddleware
from core.middleware.org_isolation import OrgIsolationMiddleware
from core.middleware.request_logging import RequestLoggingMiddleware

app = FastAPI()

# Middleware order matters - auth must run before org isolation
app.add_middleware(RequestLoggingMiddleware)      # Last (processed first)
app.add_middleware(OrgIsolationMiddleware)        # Middle
app.add_middleware(NeonAuthMiddleware)            # First (processed last)
```

### Request Context

After middleware, `request.state` contains:

```python
request.state.user_id      # str(UUID) - authenticated user ID
request.state.org_id       # str(UUID) - user's primary org ID
request.state.ip_address   # str - client IP (if set by middleware)
```

---

## Logging

All decorators log to the standard logger:

```python
import logging

logger = logging.getLogger(__name__)

# Logs will appear as:
# DEBUG - "Owner check passed" org_id=... user_id=...
# WARNING - "Owner check denied" org_id=... user_id=...
# ERROR - "Database error checking org owner" org_id=... error=...
```

Configure log levels in your settings:

```python
# config/settings.py

LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
        }
    },
    "loggers": {
        "core.decorators": {
            "handlers": ["default"],
            "level": "DEBUG",  # See all decorator logs
        }
    }
}
```

---

## Complete Example

### Setup: Organization with Roles

```python
# Database: Create admin role
await db.execute("""
    INSERT INTO org_roles (org_id, name, description, permissions, is_system_role)
    VALUES (:org_id, :name, :desc, :perms, TRUE)
""", {
    "org_id": org_id,
    "name": "admin",
    "desc": "Organization administrator",
    "perms": json.dumps([
        "members:invite",
        "members:remove",
        "reports:view",
        "reports:export",
        "settings:edit",
    ]),
})

# Add user as admin
await db.execute("""
    INSERT INTO org_members (org_id, user_id, role, status, joined_at)
    VALUES (:org_id, :user_id, 'admin', 'active', NOW())
""", {
    "org_id": org_id,
    "user_id": user_id,
})
```

### Endpoint: Protected by Decorators

```python
from fastapi import APIRouter, Request
from core.decorators import (
    isolate_by_org,
    require_org_admin,
    require_permission,
    audit_org_action,
    PermissionDenied,
)

router = APIRouter(prefix="/api/v1/orgs", tags=["organizations"])

@router.post("/{org_id}/members/invite")
@isolate_by_org                                    # 1. Check org context
@require_permission("members:invite")              # 2. Check permission
@audit_org_action("invite_member", "org_member")   # 3. Audit log
async def invite_member(
    org_id: str,
    payload: InvitePayload,
    request: Request,
    db,
):
    """
    Invite new member to organization.

    Requires:
    - User is authenticated
    - User is member of org
    - User has 'members:invite' permission
    - Action is audited to org_audit_logs
    """
    # At this point, all checks have passed
    # user_id is in request.state.user_id
    # org_id is verified and in request.state.org_id

    # Invite user
    token = generate_invitation_token()
    await db.execute("""
        INSERT INTO org_invitations (org_id, email, role, token, expires_at, invited_by)
        VALUES (:org_id, :email, :role, :token, NOW() + INTERVAL 7 DAY, :user_id)
    """, {
        "org_id": org_id,
        "email": payload.email,
        "role": payload.role,
        "token": token,
        "user_id": request.state.user_id,
    })

    # Send email (audit will log this success)
    await send_invitation_email(payload.email, token)

    return {"status": "invitation_sent", "email": payload.email}


@router.delete("/{org_id}/members/{member_id}")
@isolate_by_org
@require_org_admin                                 # Admin only (tighter than permission)
@audit_org_action("remove_member", "org_member")
async def remove_member(
    org_id: str,
    member_id: str,
    request: Request,
    db,
):
    """
    Remove member from organization.

    Requires:
    - User is authenticated
    - User is admin of org
    - Action is audited
    """
    # Verify member exists and belongs to org
    member = await db.fetch_one("""
        SELECT user_id FROM org_members WHERE org_id = :org_id AND user_id = :member_id
    """, {"org_id": org_id, "member_id": member_id})

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Remove the member
    await db.execute("""
        DELETE FROM org_members WHERE org_id = :org_id AND user_id = :member_id
    """, {"org_id": org_id, "member_id": member_id})

    return {"status": "member_removed"}
```

---

## Testing

See `tests/test_org_permissions.py` for comprehensive test coverage:

```bash
# Run permission decorator tests
uv run pytest tests/test_org_permissions.py -v

# Test specific decorator
uv run pytest tests/test_org_permissions.py::test_require_org_admin_success -v

# Test with coverage
uv run pytest tests/test_org_permissions.py --cov=core.decorators
```

---

## Troubleshooting

### "Missing user or organization context"

**Cause**: Middleware not configured or not running.

**Solution**: Verify middleware stack in `api/main.py`:
```python
app.add_middleware(OrgIsolationMiddleware)
app.add_middleware(NeonAuthMiddleware)
```

### "Permission denied" with valid role

**Cause**: Role doesn't have the required permission in org_roles.

**Solution**: Check org_roles table:
```sql
SELECT permissions FROM org_roles
WHERE org_id = :org_id AND name = :role_name;
```

Update permissions if needed:
```sql
UPDATE org_roles
SET permissions = jsonb_set(permissions, '{0}', '"members:invite"')
WHERE org_id = :org_id AND name = 'admin';
```

### Audit logs not appearing

**Cause**: Database error or wrong table name.

**Solution**: Verify table exists and is accessible:
```sql
SELECT * FROM org_audit_logs LIMIT 1;
```

Check logs for error messages:
```
ERROR - Failed to log audit entry: permission denied for schema public
```

### Slowdowns from permission checks

**Cause**: No database indexes on org_members or org_roles.

**Solution**: Add indexes:
```sql
CREATE INDEX idx_org_members_org_id_user_id ON org_members(org_id, user_id);
CREATE INDEX idx_org_roles_org_id_name ON org_roles(org_id, name);
```

---

## Implementation Checklist

- [x] `@require_org_owner` checks owner_id matches
- [x] `@require_org_admin` checks role in [admin, owner]
- [x] `@require_org_member` checks any membership
- [x] `@require_permission(perm)` checks org_roles permissions
- [x] `@require_permissions(perms)` supports AND/OR logic
- [x] `@audit_org_action()` logs to org_audit_logs
- [x] Decorators stack (apply multiple to one endpoint)
- [x] Error messages are informative
- [x] Logging tracks failed attempts
- [x] Database queries properly parameterized
- [x] IP address extraction with fallback chain
- [x] Audit logging doesn't break on DB errors
- [x] All decorators export from core/decorators/__init__.py
- [x] Comprehensive test coverage

---

## See Also

- [Organization Management Routes](../src/api/routers/org_management.py)
- [Audit Middleware](../core/middleware/audit.py)
- [Organization Models](../src/infrastructure/db/database/models.py)
