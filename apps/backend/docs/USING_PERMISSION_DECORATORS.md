# Using Permission Decorators — Quick Start Guide

A practical guide for adding permission checks to FairMind endpoints.

## Quick Reference

### Import Decorators

```python
from core.decorators import (
    isolate_by_org,
    require_org_admin,
    require_org_member,
    require_permission,
    require_permissions,
    audit_org_action,
    PermissionDenied,
)
```

### Decorator Patterns

#### Pattern 1: Anyone in the org can access

```python
@router.get("/{org_id}/dashboard")
@isolate_by_org
@require_org_member
async def get_dashboard(org_id: str, request: Request, db):
    pass
```

#### Pattern 2: Only admins can access

```python
@router.post("/{org_id}/settings")
@isolate_by_org
@require_org_admin
@audit_org_action("update_settings", "org_settings")
async def update_settings(org_id: str, payload, request: Request, db):
    pass
```

#### Pattern 3: Only owner can access

```python
@router.delete("/{org_id}")
@isolate_by_org
@require_org_owner
@audit_org_action("delete_organization")
async def delete_org(org_id: str, request: Request, db):
    pass
```

#### Pattern 4: Permission-based fine-grained control

```python
@router.post("/{org_id}/members/invite")
@isolate_by_org
@require_permission("members:invite")
@audit_org_action("invite_member", "org_member")
async def invite_member(org_id: str, payload, request: Request, db):
    pass
```

#### Pattern 5: Multiple permissions (AND logic — all required)

```python
@router.post("/{org_id}/reports/export")
@isolate_by_org
@require_permissions(["reports:view", "reports:export"])
@audit_org_action("export_report", "report")
async def export_report(org_id: str, request: Request, db):
    pass
```

#### Pattern 6: Multiple permissions (OR logic — any one required)

```python
@router.get("/{org_id}/reports")
@isolate_by_org
@require_permissions(["reports:view", "reports:admin"], require_all=False)
async def list_reports(org_id: str, request: Request, db):
    pass
```

---

## Step-by-Step: Adding Permissions to an Endpoint

### Step 1: Identify the Access Level

Decide what level of access is needed:

| Need | Decorator | Checks |
|------|-----------|--------|
| Owner only | `@require_org_owner` | Matches `organization.owner_id` |
| Admin or owner | `@require_org_admin` | Role in [admin, owner] |
| Any member | `@require_org_member` | Has membership record |
| Specific permission | `@require_permission("x:y")` | Role has permission |
| Multiple permissions | `@require_permissions([...])` | Role has all/any permissions |

### Step 2: Add the Decorator(s)

Stack decorators from inside-out:

```python
@router.post("/{org_id}/reports")
@isolate_by_org                                    # Always first
@require_org_admin                                 # Permission check
@audit_org_action("create_report", "report")       # Always last
async def create_report(org_id: str, request: Request, db):
    # org_id and user_id are automatically injected
    # If any decorator fails, the endpoint never executes
    ...
```

### Step 3: Use Context in Endpoint

Access authenticated user and org info:

```python
async def create_report(org_id: str, request: Request, db):
    # Provided by middleware:
    user_id = request.state.user_id        # Current user UUID
    org_id = request.state.org_id          # Current org UUID (also parameter)

    # Your endpoint logic:
    report = await db.fetch_one("""
        INSERT INTO reports (org_id, created_by, ...)
        VALUES (:org_id, :user_id, ...)
        RETURNING id
    """, {"org_id": org_id, "user_id": user_id, ...})

    return {"id": report["id"]}
```

---

## Common Scenarios

### Scenario 1: Invite Members (Admin Only)

```python
@router.post("/{org_id}/members/invite")
@isolate_by_org
@require_org_admin
@audit_org_action("invite_member", "org_member")
async def invite_member(
    org_id: str,
    payload: InviteMemberRequest,
    request: Request,
    db,
):
    """
    Invite a new member to the organization.

    Permission: Requires admin role.
    """
    user_id = request.state.user_id

    # Create invitation
    token = generate_token()
    await db.execute("""
        INSERT INTO org_invitations (org_id, email, token, invited_by)
        VALUES (:org_id, :email, :token, :user_id)
    """, {
        "org_id": org_id,
        "email": payload.email,
        "token": token,
        "user_id": user_id,
    })

    # Send email
    await send_invitation_email(payload.email, token)

    return {"status": "sent"}
```

### Scenario 2: Export Reports (Permission-Based)

First, define permissions:

```python
# src/domain/organization/constants.py

class OrgPermissions:
    REPORTS_VIEW = "reports:view"
    REPORTS_EXPORT = "reports:export"
    REPORTS_SCHEDULE = "reports:schedule"
```

Then use in endpoint:

```python
@router.post("/{org_id}/reports/{report_id}/export")
@isolate_by_org
@require_permissions([
    OrgPermissions.REPORTS_VIEW,
    OrgPermissions.REPORTS_EXPORT,
])  # User must have both
@audit_org_action("export_report", "report")
async def export_report(
    org_id: str,
    report_id: str,
    payload: ExportRequest,
    request: Request,
    db,
):
    """
    Export a compliance report.

    Permissions: Requires reports:view AND reports:export.
    """
    # User has necessary permissions
    # Fetch and export the report...
    report_data = await db.fetch_one("""
        SELECT * FROM reports WHERE id = :report_id AND org_id = :org_id
    """, {"report_id": report_id, "org_id": org_id})

    # Generate PDF/Excel...
    return send_file(...)
```

### Scenario 3: Delete Organization (Owner Only)

```python
@router.delete("/{org_id}")
@isolate_by_org
@require_org_owner
@audit_org_action("delete_organization", "organization")
async def delete_organization(
    org_id: str,
    request: Request,
    db,
):
    """
    Delete organization permanently.

    Permission: Owner only.
    """
    # Only the owner reaches here
    user_id = request.state.user_id

    # Verify ownership one more time (belt-and-suspenders)
    org = await db.fetch_one(
        "SELECT owner_id FROM organizations WHERE id = :org_id",
        {"org_id": org_id},
    )
    assert str(org["owner_id"]) == str(user_id)

    # Delete org and cascade delete members, roles, settings...
    await db.execute(
        "DELETE FROM organizations WHERE id = :org_id",
        {"org_id": org_id},
    )

    return {"status": "deleted"}
```

### Scenario 4: View Team Members (Member Access)

```python
@router.get("/{org_id}/members")
@isolate_by_org
@require_org_member
async def list_members(org_id: str, request: Request, db):
    """
    List members of the organization.

    Permission: Any organization member can view.
    """
    members = await db.fetch("""
        SELECT om.id, om.user_id, om.role, u.email, u.name
        FROM org_members om
        JOIN users u ON u.id = om.user_id
        WHERE om.org_id = :org_id
        ORDER BY om.joined_at
    """, {"org_id": org_id})

    return {"members": members}
```

---

## Error Handling

### Expected Exceptions

```python
from core.decorators import PermissionDenied
from fastapi import HTTPException, status

# Decorator raises PermissionDenied (HTTP 403)
# FastAPI automatically converts to HTTP response:
# {
#     "detail": "Permission denied" or "Specific message"
# }
```

### Custom Error Messages

Decorators provide context-specific messages:

```
401 Unauthorized    - Missing authentication (auth middleware)
403 Forbidden       - PermissionDenied from decorator:
                      - "Not a member of this organization"
                      - "Admin access required"
                      - "Missing permission: members:invite"
                      - "Only organization owner can perform this action"
500 Internal Error  - Database error, audit logging error
```

### Handling in Endpoints

```python
@router.post("/{org_id}/settings")
@isolate_by_org
@require_org_admin
@audit_org_action("update_settings")
async def update_settings(org_id: str, payload, request: Request, db):
    try:
        # Decorator permission checks happen BEFORE this code
        # If we reach here, user is admin

        # Additional business logic validation
        if not payload.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Value cannot be empty",
            )

        # Update settings
        await db.execute(...)

    except ValueError as e:
        # Business logic error
        logger.warning(f"Settings validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
```

---

## Audit Logging

The `@audit_org_action()` decorator automatically logs:

```python
@audit_org_action("invite_member", "org_member")
async def invite_member(...):
    ...

# Logs to org_audit_logs:
# {
#     "org_id": "...",
#     "user_id": "...",
#     "action": "invite_member",
#     "resource_type": "org_member",
#     "status": "success",
#     "ip_address": "192.168.1.100",
#     "created_at": "2026-03-22T10:30:00Z"
# }
```

### Querying Audit Logs

```python
# Get all actions for an org
SELECT * FROM org_audit_logs
WHERE org_id = :org_id
ORDER BY created_at DESC;

# Get failed actions
SELECT * FROM org_audit_logs
WHERE org_id = :org_id AND status = 'failure'
ORDER BY created_at DESC;

# Get actions by user
SELECT * FROM org_audit_logs
WHERE org_id = :org_id AND user_id = :user_id
ORDER BY created_at DESC;

# Get specific action type
SELECT * FROM org_audit_logs
WHERE org_id = :org_id AND action = 'invite_member'
ORDER BY created_at DESC;
```

---

## Testing Endpoints with Decorators

### Test Success Case

```python
@pytest.mark.asyncio
async def test_invite_member_as_admin(client, org_id, admin_user_token):
    """Admin can invite members."""
    response = await client.post(
        f"/api/v1/orgs/{org_id}/members/invite",
        json={"email": "new@example.com"},
        headers={"Authorization": f"Bearer {admin_user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "sent"
```

### Test Permission Denied

```python
@pytest.mark.asyncio
async def test_invite_member_as_member_denied(client, org_id, member_user_token):
    """Member cannot invite others."""
    response = await client.post(
        f"/api/v1/orgs/{org_id}/members/invite",
        json={"email": "new@example.com"},
        headers={"Authorization": f"Bearer {member_user_token}"},
    )
    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()
```

### Test Different Org

```python
@pytest.mark.asyncio
async def test_cross_org_access_denied(client, org_id_1, org_id_2, user_token):
    """User cannot access different org."""
    # User is admin of org_id_1
    response = await client.get(
        f"/api/v1/orgs/{org_id_2}/members",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403
```

---

## Permission Configuration

### Define Role Permissions

At application startup, set up roles:

```python
# src/api/startup.py

async def setup_org_roles(db, org_id):
    """Configure default roles for new organization."""

    roles = {
        "owner": [
            "members:invite",
            "members:remove",
            "settings:edit",
            "settings:delete",
            "roles:manage",
        ],
        "admin": [
            "members:invite",
            "members:remove",
            "settings:edit",
            "reports:view",
            "reports:export",
        ],
        "member": [
            "reports:view",
        ],
        "viewer": [
            "reports:view",
        ],
    }

    for role_name, permissions in roles.items():
        await db.execute("""
            INSERT INTO org_roles (org_id, name, permissions, is_system_role)
            VALUES (:org_id, :name, :perms, TRUE)
        """, {
            "org_id": org_id,
            "name": role_name,
            "perms": json.dumps(permissions),
        })
```

### Update Permissions

```python
# Add a permission to existing role
await db.execute("""
    UPDATE org_roles
    SET permissions = jsonb_set(
        permissions,
        '{5}',
        '"compliance:audit"'
    )
    WHERE org_id = :org_id AND name = 'admin'
""", {"org_id": org_id})

# Remove a permission
await db.execute("""
    UPDATE org_roles
    SET permissions = permissions - 'reports:export'
    WHERE org_id = :org_id AND name = 'member'
""", {"org_id": org_id})
```

---

## Debugging

### Check Request State

Add logging to see what's in request.state:

```python
import logging

logger = logging.getLogger(__name__)

@router.get("/{org_id}/debug")
@isolate_by_org
async def debug_state(org_id: str, request: Request):
    """Debug endpoint to inspect request state."""
    logger.info(f"user_id: {request.state.user_id}")
    logger.info(f"org_id: {request.state.org_id}")

    return {
        "user_id": str(request.state.user_id),
        "org_id": str(request.state.org_id),
    }
```

### Check User's Role

```python
@router.get("/{org_id}/debug/role")
@isolate_by_org
async def debug_role(org_id: str, request: Request, db):
    """Check what role user has in this org."""
    user_id = request.state.user_id

    member = await db.fetch_one("""
        SELECT role FROM org_members
        WHERE org_id = :org_id AND user_id = :user_id
    """, {"org_id": org_id, "user_id": user_id})

    return {"role": member["role"] if member else None}
```

### Check Role Permissions

```python
@router.get("/{org_id}/debug/permissions")
@isolate_by_org
async def debug_permissions(org_id: str, request: Request, db):
    """Check what permissions user's role has."""
    user_id = request.state.user_id

    member = await db.fetch_one("""
        SELECT role FROM org_members
        WHERE org_id = :org_id AND user_id = :user_id
    """, {"org_id": org_id, "user_id": user_id})

    if not member:
        return {"error": "Not a member"}

    role = await db.fetch_one("""
        SELECT permissions FROM org_roles
        WHERE org_id = :org_id AND name = :role
    """, {"org_id": org_id, "role": member["role"]})

    return {"permissions": role["permissions"] if role else []}
```

### View Audit Logs

```python
@router.get("/{org_id}/debug/audit")
@isolate_by_org
@require_org_admin  # Only admins see audit logs
async def debug_audit(org_id: str, limit: int = 10, request: Request, db):
    """View recent audit logs for this org."""
    logs = await db.fetch("""
        SELECT action, resource_type, status, user_id, ip_address, created_at
        FROM org_audit_logs
        WHERE org_id = :org_id
        ORDER BY created_at DESC
        LIMIT :limit
    """, {"org_id": org_id, "limit": limit})

    return {"logs": logs}
```

---

## Production Checklist

- [ ] All org-scoped endpoints use `@isolate_by_org`
- [ ] Sensitive operations use `@require_org_admin` or `@require_org_owner`
- [ ] Fine-grained operations use `@require_permission()`
- [ ] All mutation operations use `@audit_org_action()`
- [ ] Org roles and permissions are configured
- [ ] Audit logs are being written
- [ ] Database indexes exist on org_members, org_roles
- [ ] Error handling is in place
- [ ] Logging is configured
- [ ] Tests cover permission denied cases

---

## See Also

- [Permission Decorators Reference](./PERMISSION_DECORATORS.md)
- [Organization Models](../src/infrastructure/db/database/models.py)
- [Audit Middleware](../core/middleware/audit.py)
