# Org Admin Endpoints - Quick Reference

## API Endpoints Summary

### Member Management

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| `GET` | `/api/v1/organizations/{org_id}/members` | Member | List all members |
| `POST` | `/api/v1/organizations/{org_id}/members/invite` | Admin | Invite new member |
| `PUT` | `/api/v1/organizations/{org_id}/members/{member_id}` | Admin | Update role/status |
| `DELETE` | `/api/v1/organizations/{org_id}/members/{member_id}` | Admin | Remove member |

### Role Management

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| `GET` | `/api/v1/organizations/{org_id}/roles` | Member | List roles & permissions |
| `POST` | `/api/v1/organizations/{org_id}/roles` | Admin | Create custom role |

### Audit & Compliance

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| `GET` | `/api/v1/organizations/{org_id}/audit-logs` | Admin | View organization audit trail |

---

## Common Tasks

### List members in organization

```bash
curl -X GET \
  "http://localhost:8000/api/v1/organizations/{org_id}/members?limit=50&skip=0" \
  -H "Authorization: Bearer {token}"
```

### Invite new member

```bash
curl -X POST \
  "http://localhost:8000/api/v1/organizations/{org_id}/members/invite" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@company.com",
    "role": "analyst"
  }'
```

### Change member role

```bash
curl -X PUT \
  "http://localhost:8000/api/v1/organizations/{org_id}/members/{member_id}" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "admin"
  }'
```

### Remove member

```bash
curl -X DELETE \
  "http://localhost:8000/api/v1/organizations/{org_id}/members/{member_id}" \
  -H "Authorization: Bearer {token}"
```

### Create custom role

```bash
curl -X POST \
  "http://localhost:8000/api/v1/organizations/{org_id}/roles" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Analyst",
    "description": "Can analyze bias reports",
    "permissions": ["read:reports", "read:datasets"]
  }'
```

### View audit logs

```bash
curl -X GET \
  "http://localhost:8000/api/v1/organizations/{org_id}/audit-logs?limit=50&action=invite_member" \
  -H "Authorization: Bearer {token}"
```

---

## Default System Roles

| Role | Permissions |
|------|-------------|
| `admin` | All permissions (manage members, roles, view audit logs) |
| `owner` | Organization owner (inherited from org creation) |
| `analyst` | Default member role (read-only access) |
| `member` | Basic member role |

Custom roles can be created with any combination of permissions.

---

## Error Codes Reference

| Code | Meaning | Typical Cause |
|------|---------|---------------|
| `200 OK` | Success | Request completed successfully |
| `201 Created` | Created | Resource created (invitation, role) |
| `204 No Content` | Success (no body) | Deletion succeeded |
| `400 Bad Request` | Invalid input | Cannot remove last admin, invalid email |
| `401 Unauthorized` | No auth | Missing or invalid JWT token |
| `403 Forbidden` | No permission | Not org member or admin |
| `404 Not Found` | Not found | Member/role/org doesn't exist |
| `409 Conflict` | Duplicate | Pending invitation or role exists |
| `500 Server Error` | Internal error | Database or service error |

---

## Key Security Features

✅ **Multi-tenant isolation** - Queries filtered by org_id at all layers
✅ **Admin safeguards** - Cannot remove last admin (prevents lockout)
✅ **Audit logging** - All admin actions logged to org_audit_logs
✅ **Async emails** - Invitations sent without blocking response
✅ **Token expiration** - Invitation tokens expire after 7 days
✅ **Context injection** - IP address and user-agent logged for security

---

## Decorators for New Endpoints

When creating new org-scoped endpoints, use decorators:

```python
from core.decorators.org_permissions import (
    require_org_member,      # User must be in org
    require_org_admin,       # User must be admin/owner
    require_permission,      # User must have specific permission
    require_permissions,     # User must have multiple permissions
    audit_org_action,        # Log the action
)

# Example: endpoint requiring admin
@router.post("/{org_id}/custom-action")
@isolate_by_org           # From OrgIsolationMiddleware
@require_org_admin        # Check admin role
@audit_org_action("custom_action", "custom_resource")
async def custom_endpoint(org_id: str, request: Request, db):
    # Implementation...
    pass
```

---

## Database Tables

**org_members** - User to organization mapping
- Columns: id, org_id, user_id, role, status, joined_at
- Indexes: org_id, user_id, role, status

**org_invitations** - Pending invitations with tokens
- Columns: id, org_id, email, role, token, expires_at, status
- Indexes: org_id, email, token, expires_at

**org_roles** - Custom roles with permissions
- Columns: id, org_id, name, permissions (JSONB), is_system_role
- Indexes: org_id, name

**org_audit_logs** - Immutable audit trail
- Columns: id, org_id, user_id, action, resource_type, changes, status, error_message
- Indexes: org_id, user_id, action

---

## Testing

Run tests:
```bash
cd apps/backend
pytest tests/test_org_management.py -v
```

Test coverage includes:
- Member CRUD operations
- Invitation lifecycle
- Role management
- Audit logging
- Admin safeguards
- Multi-tenant isolation
- Error handling
- Security

---

## Development Notes

### Adding New Admin Permissions

1. Define permission string: `"resource:action"` (e.g., `"reports:export"`)
2. Add to role's permissions array in org_roles table
3. Use decorator in endpoint: `@require_permission("resource:action")`

### Async Email Service

Invitations are sent asynchronously via `email_service.send_org_invitation()`. If the service is unavailable, the invitation is still created successfully (non-blocking).

### Audit Logs

- Automatically logged by endpoints
- Immutable (no delete endpoint)
- Can be exported for compliance reports
- Filter by action, org_id, user_id, status

---

## Files

- **Routers**: `/apps/backend/src/api/routers/org_management.py`
- **Decorators**: `/apps/backend/core/decorators/org_permissions.py`
- **Tests**: `/apps/backend/tests/test_org_management.py`
- **Docs**: `ORG_MEMBER_MANAGEMENT_IMPLEMENTATION.md`

---

Last Updated: 2026-03-22
Status: ✅ Production Ready
