# FairMind Permission System Guide

**Version:** 1.0
**Last Updated:** March 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Built-in Roles](#built-in-roles)
3. [Custom Roles](#custom-roles)
4. [Permission Matrix](#permission-matrix)
5. [Decorator Usage](#decorator-usage)
6. [Testing Permissions](#testing-permissions)
7. [Permission Errors](#permission-errors)
8. [Best Practices](#best-practices)

---

## Overview

FairMind's permission system allows fine-grained access control through roles and permissions.

### How It Works

1. **User joins organization** — Gets assigned a role (admin, member, analyst, or custom)
2. **Role defines permissions** — Each role has a list of actions it can perform
3. **Permission format** — `resource:action` (e.g., `members:invite`)
4. **Decorators enforce** — `@require_org_admin` or `@require_permission()` check before endpoint executes
5. **Audit logs track** — All permission checks logged for compliance

### Two-Level System

**Global Level (System-wide):**
- User has global role: `admin`, `analyst`, or `viewer`
- Assigned by Authentik at login
- Controls platform access

**Organization Level (Per-organization):**
- User has org-specific role in each organization they join
- Can be different in different organizations
- Admins can create custom roles

### Permission Flow

```
Request comes in with JWT
    ↓
JWT validated, user_id extracted
    ↓
@require_org_admin decorator runs
    ↓
Checks: Is user member of org? Does user have admin role?
    ↓
If yes → Endpoint executes
If no → 403 Forbidden returned, logged to audit
    ↓
Action logged to org_audit_logs with user, org, action, status
```

---

## Built-in Roles

### Organization Roles (Per-Organization)

Organizations have four built-in roles, plus custom roles.

#### `owner` — Organization Owner

**Description:** Full control over organization

**When assigned:** When creating an organization (creator becomes owner)

**Capabilities:**
- Manage all members (invite, remove, change roles)
- Cannot remove themselves
- Create and edit custom roles
- View all audit logs
- Delete the organization (destructive!)
- Cannot be removed from organization

**Permissions:**
```
members:view        -- See member list
members:invite      -- Send invitations
members:edit        -- Change member roles
members:remove      -- Remove members from org
roles:create        -- Create custom roles
roles:edit          -- Modify role permissions
roles:delete        -- Delete custom roles
audit:view          -- View audit logs
organization:delete -- Delete entire organization
```

**Safeguards:**
- Cannot promote to non-owner and demote themselves
- Cannot be removed from organization
- Cannot remove last owner

**Use case:** Organization founder/administrator

---

#### `admin` — Organization Administrator

**Description:** Manage members and settings, cannot delete organization

**When assigned:** By owner or another admin

**Capabilities:**
- Manage most members (invite, remove, change roles)
- Create and edit custom roles
- View audit logs
- Cannot delete the organization
- Cannot remove last admin (org needs ≥1 admin)

**Permissions:**
```
members:view        -- See member list
members:invite      -- Send invitations
members:edit        -- Change member roles
members:remove      -- Remove members from org
roles:create        -- Create custom roles
roles:edit          -- Modify role permissions
audit:view          -- View audit logs
```

**Safeguards:**
- Cannot demote themselves if it would leave no admins
- Cannot remove last admin

**Use case:** Day-to-day organization management

---

#### `member` — Standard Member

**Description:** Standard access, contribute to work

**When assigned:** By invitation

**Capabilities:**
- View member list
- Upload and view datasets
- Generate reports
- Contribute to projects
- Cannot manage members or roles

**Permissions:**
```
members:view        -- See member list
datasets:view       -- View datasets
datasets:upload     -- Add new datasets
reports:view        -- See compliance reports
reports:generate    -- Create new reports
```

**Use case:** Regular organization users

---

#### `analyst` — Data Analyst

**Description:** Read data and perform analysis

**When assigned:** By admin/owner

**Capabilities:**
- View member list
- View datasets
- Run analysis and generate reports
- View audit logs (optional)
- Cannot modify any data

**Permissions:**
```
members:view        -- See member list
datasets:view       -- View datasets
reports:view        -- See reports
reports:generate    -- Create new reports
models:evaluate     -- Analyze ML models
audit:view          -- View audit logs
```

**Use case:** Data scientists, compliance analysts

---

### Global Roles (From Authentik)

These roles are assigned by Authentik and apply system-wide.

#### `admin` — Global Admin

- Create and delete organizations
- Access all organization data
- Can never be removed from their own organizations

#### `analyst` — Data Analyst

- Join organizations via invitation
- Perform analysis on datasets
- Generate reports

#### `viewer` — Read-Only Viewer

- View dashboards and reports
- Cannot perform any actions
- Read-only access for stakeholders

---

## Custom Roles

Organizations can define custom roles for specific needs.

### Creating Custom Roles

**API Endpoint:**
```bash
POST /api/v1/organizations/{org_id}/roles
```

**Request:**
```json
{
  "name": "Compliance Officer",
  "description": "Manages compliance reporting and audits",
  "permissions": [
    "members:view",
    "reports:view",
    "reports:export",
    "audit:view"
  ]
}
```

### Role Definition

```python
{
    "id": "role-uuid",
    "name": "Compliance Officer",          # Unique name in org
    "description": "...",                  # What it does
    "permissions": [                       # Array of permission strings
        "members:view",
        "reports:view",
        "reports:export",
        "audit:view"
    ],
    "is_system_role": false,               # Custom roles = false
    "created_at": "2026-03-22T10:00:00Z"
}
```

### Examples

**Data Analyst Role:**
```json
{
  "name": "Data Analyst",
  "description": "Can analyze datasets and create reports",
  "permissions": [
    "datasets:view",
    "datasets:analyze",
    "reports:generate",
    "reports:view"
  ]
}
```

**Finance Auditor Role:**
```json
{
  "name": "Finance Auditor",
  "description": "Views financial data and generates compliance reports",
  "permissions": [
    "reports:view",
    "reports:export",
    "audit:view",
    "datasets:view"
  ]
}
```

**Manager Role:**
```json
{
  "name": "Manager",
  "description": "Manages team members and reports",
  "permissions": [
    "members:view",
    "members:invite",
    "members:edit",
    "reports:view",
    "reports:generate",
    "datasets:view"
  ]
}
```

### Assigning Custom Roles

**API:**
```bash
PUT /api/v1/organizations/{org_id}/members/{member_id}

{
  "role": "Data Analyst"  # Use role name
}
```

**Dropdown in UI shows:**
- All system roles (admin, member, analyst)
- All custom roles defined in org

### Permission Strings

Permissions use format: `resource:action`

**Common permissions:**

| Permission | Resource | Action | Allows |
|-----------|----------|--------|--------|
| `members:view` | members | view | See member list |
| `members:invite` | members | invite | Send invitations |
| `members:edit` | members | edit | Change member roles |
| `members:remove` | members | remove | Remove members |
| `datasets:view` | datasets | view | See datasets |
| `datasets:upload` | datasets | upload | Add new datasets |
| `datasets:delete` | datasets | delete | Delete datasets |
| `datasets:analyze` | datasets | analyze | Run analysis |
| `reports:view` | reports | view | See reports |
| `reports:generate` | reports | generate | Create reports |
| `reports:export` | reports | export | Export to PDF/CSV |
| `audit:view` | audit | view | See audit logs |
| `roles:create` | roles | create | Create custom roles |
| `roles:edit` | roles | edit | Edit custom roles |
| `organization:delete` | organization | delete | Delete organization |

You can define any permission string your org needs.

---

## Permission Matrix

| Permission | Owner | Admin | Member | Analyst | Custom* |
|-----------|-------|-------|--------|---------|---------|
| **Members** | | | | | |
| members:view | ✓ | ✓ | ✓ | ✓ | ⚙ |
| members:invite | ✓ | ✓ | ✗ | ✗ | ⚙ |
| members:edit | ✓ | ✓ | ✗ | ✗ | ⚙ |
| members:remove | ✓ | ✓ | ✗ | ✗ | ⚙ |
| **Datasets** | | | | | |
| datasets:view | ✓ | ✓ | ✓ | ✓ | ⚙ |
| datasets:upload | ✓ | ✓ | ✓ | ✗ | ⚙ |
| datasets:delete | ✓ | ✓ | ✗ | ✗ | ⚙ |
| datasets:analyze | ✓ | ✓ | ✓ | ✓ | ⚙ |
| **Reports** | | | | | |
| reports:view | ✓ | ✓ | ✓ | ✓ | ⚙ |
| reports:generate | ✓ | ✓ | ✓ | ✓ | ⚙ |
| reports:export | ✓ | ✓ | ✗ | ✗ | ⚙ |
| **Audit** | | | | | |
| audit:view | ✓ | ✓ | ✗ | ✓ | ⚙ |
| **Roles** | | | | | |
| roles:create | ✓ | ✓ | ✗ | ✗ | ⚙ |
| roles:edit | ✓ | ✓ | ✗ | ✗ | ⚙ |
| **Organization** | | | | | |
| organization:delete | ✓ | ✗ | ✗ | ✗ | ✗ |

*Custom roles: Org admins define permissions marked ⚙

**Legend:**
- ✓ — Role has this permission
- ✗ — Role doesn't have this permission
- ⚙ — Customizable per organization

---

## Decorator Usage

### Authorization Decorators

Decorators are applied to endpoints to enforce permission checks.

#### `@require_org_owner`

Only organization owner can access:

```python
@router.delete("/{org_id}")
@require_org_owner
async def delete_organization(org_id: str, request: Request, db):
    # Only owner can delete org
    await db.execute("DELETE FROM organizations WHERE id = :id", {"id": org_id})
```

**When to use:**
- Sensitive org-level operations
- Account closure/deletion
- Critical configuration changes

---

#### `@require_org_admin`

Organization admin or owner can access:

```python
@router.post("/{org_id}/members/invite")
@require_org_admin
async def invite_member(org_id: str, payload: InviteMemberRequest, request: Request, db):
    # Only admin/owner can invite
    ...
```

**When to use:**
- Member management (invite, remove, change role)
- Role management
- Audit log access
- Organization settings

---

#### `@require_org_member`

Any organization member can access:

```python
@router.get("/{org_id}/members")
@require_org_member
async def list_members(org_id: str, request: Request, db):
    # Any member can see member list
    ...
```

**When to use:**
- View-only endpoints
- Member can see other members
- Data that all members should access

---

#### `@require_permission("resource:action")`

User must have specific permission:

```python
@router.post("/{org_id}/reports/export")
@require_permission("reports:export")
async def export_report(org_id: str, report_id: str, request: Request, db):
    # Only users with reports:export permission
    ...
```

**When to use:**
- Fine-grained access control
- Restrict sensitive operations
- Support for custom roles

**Example:**
```python
@router.delete("/{org_id}/datasets/{dataset_id}")
@require_permission("datasets:delete")
async def delete_dataset(org_id: str, dataset_id: str, request: Request, db):
    # Only users with datasets:delete permission
    await db.execute("DELETE FROM datasets WHERE id = :id", {"id": dataset_id})
```

---

#### `@require_permissions(["perm1", "perm2"], require_all=False)`

User must have multiple permissions:

```python
# Must have ALL permissions (AND logic)
@router.post("/{org_id}/reports/export-secure")
@require_permissions(["reports:view", "reports:export"])
async def export_secure_report(org_id: str, request: Request, db):
    ...

# Must have AT LEAST ONE permission (OR logic)
@router.get("/{org_id}/reports")
@require_permissions(["reports:admin", "reports:view"], require_all=False)
async def list_reports(org_id: str, request: Request, db):
    ...
```

**Default:** `require_all=True` (all permissions required)

---

### Full Example

```python
from fastapi import APIRouter, Request, Depends
from config.auth import get_current_active_user, TokenData
from config.database import get_db_connection
from core.decorators.org_permissions import (
    require_org_admin,
    require_permission,
    audit_org_action
)

router = APIRouter(prefix="/api/v1/organizations", tags=["members"])

@router.post("/{org_id}/members/invite")
@require_org_admin  # Verify admin role
@audit_org_action("invite_member", "member")  # Log the action
async def invite_member(
    org_id: str,
    payload: InviteMemberRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Invite a new member to the organization.

    Requires: admin role
    """
    # Authorization already checked by decorator
    # Endpoint can safely assume user is authorized
    ...
```

---

## Testing Permissions

### Manual Testing

**Test with cURL:**

```bash
#!/bin/bash

API_URL="https://api.fairmind.io"
ORG_ID="org-123"

# Get admin token
ADMIN_TOKEN="jwt-token-admin-role"

# Get member token
MEMBER_TOKEN="jwt-token-member-role"

# Test 1: Admin can invite members (200 OK)
curl -X POST \
  "${API_URL}/api/v1/organizations/${ORG_ID}/members/invite" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -d '{"email": "new@example.com", "role": "analyst"}'
# Expected: 201 Created

# Test 2: Member cannot invite (403 Forbidden)
curl -X POST \
  "${API_URL}/api/v1/organizations/${ORG_ID}/members/invite" \
  -H "Authorization: Bearer ${MEMBER_TOKEN}" \
  -d '{"email": "new@example.com", "role": "analyst"}'
# Expected: 403 Forbidden

# Test 3: Member can view members (200 OK)
curl -X GET \
  "${API_URL}/api/v1/organizations/${ORG_ID}/members" \
  -H "Authorization: Bearer ${MEMBER_TOKEN}"
# Expected: 200 OK with members list
```

### Unit Testing

```python
import pytest
from fastapi.testclient import TestClient
from api.main import app
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_invite_member_requires_admin():
    """Member role cannot invite others."""
    client = TestClient(app)

    # Get member token (from Authentik)
    member_token = "jwt-token-member-role"

    response = client.post(
        "/api/v1/organizations/org-123/members/invite",
        headers={"Authorization": f"Bearer {member_token}"},
        json={"email": "new@example.com", "role": "analyst"}
    )

    assert response.status_code == 403
    assert "Admin access required" in response.json()["detail"]

@pytest.mark.asyncio
async def test_invite_member_admin_succeeds():
    """Admin role can invite members."""
    client = TestClient(app)

    # Get admin token
    admin_token = "jwt-token-admin-role"

    response = client.post(
        "/api/v1/organizations/org-123/members/invite",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": "new@example.com", "role": "analyst"}
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
```

### Integration Testing

```python
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.mark.integration
async def test_member_invitation_flow():
    """Test complete invitation and acceptance flow."""
    client = TestClient(app)

    # Step 1: Admin invites member
    admin_token = "jwt-token-admin"
    response = client.post(
        "/api/v1/organizations/org-123/members/invite",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": "newuser@example.com", "role": "analyst"}
    )
    assert response.status_code == 201
    invitation_token = response.json()["invitation_id"]

    # Step 2: Unauthenticated user views invitation
    response = client.get(f"/api/v1/invitations/{invitation_token}")
    assert response.status_code == 200
    assert response.json()["email"] == "newuser@example.com"

    # Step 3: User accepts invitation
    user_token = "jwt-token-newuser"
    response = client.post(
        f"/api/v1/invitations/{invitation_token}/accept",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 201
    assert response.json()["role"] == "analyst"

    # Step 4: Member can now access org endpoints
    response = client.get(
        "/api/v1/organizations/org-123/members",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
```

---

## Permission Errors

### 403 Forbidden

User lacks required permission:

```json
{
  "detail": "Admin access required"
}
```

**Common causes:**
- Not an admin (need admin/owner role)
- Not a member of organization
- Missing specific permission

**Solution:**
- Contact organization admin
- Request appropriate role assignment

---

### 401 Unauthorized

Missing or invalid JWT:

```json
{
  "detail": "Missing or invalid authentication token"
}
```

**Common causes:**
- JWT missing from Authorization header
- JWT expired (valid for 1 hour)
- JWT tampered with (signature invalid)

**Solution:**
- Log in again via Authentik
- Request new access token
- Check JWT expiration (`exp` claim)

---

### 409 Conflict

Resource already exists:

```json
{
  "detail": "User is already a member of this organization"
}
```

**Common causes:**
- Inviting existing member
- Accepting invitation already accepted
- Creating role with duplicate name

**Solution:**
- Check if member already exists
- Use different role name for custom roles

---

## Best Practices

### 1. Use Least Privilege

Don't assign more permissions than needed:

```python
# ❌ Wrong: Give everyone admin role
role = "admin"

# ✓ Correct: Use appropriate role for job
role = "analyst" if job == "data_science" else "member"
```

### 2. Use Specific Permissions

When possible, use `@require_permission()` instead of `@require_org_admin`:

```python
# ❌ Less specific: Any admin can do this
@require_org_admin
async def export_report(...):
    ...

# ✓ Better: Only users with export permission
@require_permission("reports:export")
async def export_report(...):
    ...
```

### 3. Audit Sensitive Operations

Always log sensitive actions:

```python
# ✓ Good: Audit all member changes
@audit_org_action("remove_member", "member")
async def remove_member(...):
    ...
```

### 4. Handle Permission Errors Gracefully

Show helpful error messages:

```python
try:
    # Attempt admin action
    result = await admin_function()
except PermissionDenied:
    return {
        "error": "You don't have permission to perform this action",
        "required_role": "admin",
        "your_role": user.role
    }
```

### 5. Test Permission Boundaries

Always test that permissions are enforced:

```python
def test_member_cannot_invite():
    """Ensure member role cannot invite others."""
    # This MUST fail with 403
    response = invite_as_member()
    assert response.status_code == 403
```

### 6. Document Custom Roles

When creating custom roles, document purpose:

```json
{
  "name": "Compliance Officer",
  "description": "Manages compliance reporting and audit logs. Can view and export reports, view audit trail, but cannot manage members.",
  "permissions": [
    "members:view",
    "reports:view",
    "reports:export",
    "audit:view"
  ]
}
```

### 7. Regular Audit Review

Periodically review:
- Who has admin access
- What custom roles exist
- Permission usage patterns
- Failed authorization attempts

```bash
# Check who are admins
SELECT user_id, org_id, role FROM org_members WHERE role IN ('admin', 'owner');

# Check failed permission attempts
SELECT user_id, action, COUNT(*) FROM org_audit_logs
WHERE status = 'failure'
GROUP BY user_id, action
ORDER BY COUNT(*) DESC;
```

---

**Document Version:** 1.0
**Last Updated:** March 2026
