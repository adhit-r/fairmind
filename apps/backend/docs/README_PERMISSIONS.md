# Permission Decorator System

## Overview

FairMind's fine-grained permission checking system for organization-scoped endpoints.

**Quick Links**:
- [Reference Documentation](./PERMISSION_DECORATORS.md) — Complete technical reference
- [Quick Start Guide](./USING_PERMISSION_DECORATORS.md) — Practical examples
- [Implementation Summary](../PERMISSION_SYSTEM_IMPLEMENTATION.md) — Architecture & design

## What It Does

Provides composable decorators for protecting endpoints with role-based and permission-based access control:

```python
@router.post("/{org_id}/members")
@isolate_by_org                                # Ensure user is in an org
@require_org_admin                             # Only admins can access
@audit_org_action("invite_member", "org_member")  # Log the action
async def invite_member(org_id: str, request: Request, db):
    # At this point: user is verified, has admin role, action will be audited
    ...
```

## Decorators Available

| Decorator | Purpose | Use Case |
|-----------|---------|----------|
| `@require_org_owner` | Only owner | Delete org |
| `@require_org_admin` | Admin or owner | Manage members |
| `@require_org_member` | Any member | View org data |
| `@require_permission(perm)` | Specific permission | Fine-grained control |
| `@require_permissions(perms)` | Multiple permissions | Complex rules |
| `@audit_org_action(action, resource)` | Log actions | Compliance audit trail |

## Installation

No installation needed! Already included in the codebase.

```python
from core.decorators import (
    require_org_owner,
    require_org_admin,
    require_org_member,
    require_permission,
    require_permissions,
    audit_org_action,
    PermissionDenied,
)
```

## Basic Usage

### Admin-Only Endpoint

```python
@router.post("/{org_id}/members")
@isolate_by_org
@require_org_admin
@audit_org_action("invite_member", "org_member")
async def invite_member(org_id: str, request: Request, db):
    user_id = request.state.user_id
    # Invite logic...
    return {"status": "sent"}
```

### Permission-Based Endpoint

```python
@router.post("/{org_id}/reports/export")
@isolate_by_org
@require_permission("reports:export")
@audit_org_action("export_report", "report")
async def export_report(org_id: str, request: Request, db):
    # Export logic...
    return {"status": "exported"}
```

## Database Tables

Must exist in your database:

| Table | Purpose | Key Columns |
|-------|---------|------------|
| `org_members` | Member→role mapping | org_id, user_id, role |
| `org_roles` | Role→permissions mapping | org_id, name, permissions (JSON) |
| `org_audit_logs` | Action audit trail | org_id, user_id, action, status |
| `organizations` | Org info | id, owner_id |

See [PERMISSION_DECORATORS.md](./PERMISSION_DECORATORS.md) for full schema.

## Common Scenarios

### Scenario 1: Invite Members (Admin Only)
```python
@router.post("/{org_id}/members/invite")
@isolate_by_org
@require_org_admin
@audit_org_action("invite_member", "org_member")
async def invite_member(org_id: str, payload, request: Request, db):
    ...
```

### Scenario 2: Export Reports (Permission-Based)
```python
@router.post("/{org_id}/reports/export")
@isolate_by_org
@require_permissions(["reports:view", "reports:export"])
@audit_org_action("export_report", "report")
async def export_report(org_id: str, request: Request, db):
    ...
```

### Scenario 3: Delete Organization (Owner Only)
```python
@router.delete("/{org_id}")
@isolate_by_org
@require_org_owner
@audit_org_action("delete_organization", "organization")
async def delete_organization(org_id: str, request: Request, db):
    ...
```

## Error Handling

All decorators return HTTP 403 Forbidden on permission denial:

```json
{
    "detail": "Admin access required" | "Missing permission: members:invite" | etc.
}
```

Specific error messages help debugging:

```
"Only organization owner can perform this action"
"Admin access required"
"Not a member of this organization"
"Missing permission: members:invite"
"Missing permissions: reports:view, reports:export"
"Must have one of: reports:view, reports:admin"
```

## Testing

Run tests:

```bash
cd apps/backend
uv run pytest tests/test_org_permissions.py -v
```

21 comprehensive tests cover:
- All decorators
- Success and failure cases
- Error handling
- Decorator stacking

## Troubleshooting

**"Missing user or organization context"**
→ Check that middleware is configured in `api/main.py`

**"Permission denied" with valid role**
→ Check `org_roles` table has correct permissions for the role

**Audit logs not appearing**
→ Check `org_audit_logs` table exists and is accessible

**Slowdowns**
→ Add database indexes on `org_members(org_id, user_id)` and `org_roles(org_id, name)`

See [PERMISSION_DECORATORS.md](./PERMISSION_DECORATORS.md) for detailed troubleshooting.

## Files

| File | Purpose | Size |
|------|---------|------|
| `core/decorators/org_permissions.py` | Implementation | 646 lines |
| `tests/test_org_permissions.py` | Tests | 641 lines |
| `docs/PERMISSION_DECORATORS.md` | Reference | Complete |
| `docs/USING_PERMISSION_DECORATORS.md` | Quick start | Complete |
| `PERMISSION_SYSTEM_IMPLEMENTATION.md` | Architecture | Complete |

## Next Steps

1. **Read**: [USING_PERMISSION_DECORATORS.md](./USING_PERMISSION_DECORATORS.md) for examples
2. **Implement**: Add decorators to your endpoints
3. **Test**: Run `uv run pytest tests/test_org_permissions.py`
4. **Reference**: Use [PERMISSION_DECORATORS.md](./PERMISSION_DECORATORS.md) as needed

---

**Status**: ✅ Ready for Production  
**Implementation**: Complete and tested  
**Support**: See documentation files
