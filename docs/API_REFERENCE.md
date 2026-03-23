# FairMind RBAC API Reference

**Version:** 1.0
**Base URL:** `https://api.fairmind.io`
**Authentication:** Bearer JWT tokens (from Authentik OAuth2)
**Content-Type:** `application/json`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Organization Management Endpoints](#organization-management-endpoints)
3. [Response Formats](#response-formats)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)

---

## Authentication

All endpoints (except `/invitations/{token}` for preview) require a valid JWT Bearer token:

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6I...
```

**Token acquisition:**
1. User logs in via Authentik OAuth2
2. Receives JWT in response
3. Frontend stores in HttpOnly cookie
4. Sent on every API request

**Token format:**
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLXV1aWQiLCJlbWFpbCI6InVzZXJAZXhhbXBsZS5jb20iLCJleHAiOjE3MTA5ODE2MDB9.signature...
```

**Token expiration:** 1 hour (configurable)

**Refresh tokens:** Use to get new access token (30-day validity)

---

## Organization Management Endpoints

### List Organization Members

```http
GET /api/v1/organizations/{org_id}/members
```

**Authorization:** Any organization member

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| org_id | UUID | Organization ID |

**Query Parameters:**
| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| limit | integer | 50 | 100 | Number of members per page |
| skip | integer | 0 | - | Pagination offset |

**Request Example:**
```bash
curl -X GET \
  "https://api.fairmind.io/api/v1/organizations/org-123e4567-e89b-12d3-a456-426614174000/members?limit=25&skip=0" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..." \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "members": [
    {
      "id": "member-550e8400-e29b-41d4-a716-446655440000",
      "user_id": "user-550e8400-e29b-41d4-a716-446655440001",
      "email": "alice@example.com",
      "name": "Alice Cooper",
      "role": "admin",
      "status": "active",
      "joined_at": "2026-03-20T12:00:00Z"
    },
    {
      "id": "member-550e8400-e29b-41d4-a716-446655440002",
      "user_id": "user-550e8400-e29b-41d4-a716-446655440003",
      "email": "bob@example.com",
      "name": "Bob Smith",
      "role": "analyst",
      "status": "active",
      "joined_at": "2026-03-21T14:30:00Z"
    }
  ],
  "total": 42
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Bad Request | Invalid query parameters |
| 401 | Unauthorized | Missing or invalid JWT |
| 403 | Forbidden | Not a member of this organization |
| 404 | Not Found | Organization doesn't exist |
| 500 | Server Error | Database or server error |

**Example Error:**
```json
{
  "detail": "You are not a member of this organization"
}
```

---

### Invite Member to Organization

```http
POST /api/v1/organizations/{org_id}/members/invite
```

**Authorization:** Organization admin or owner

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| org_id | UUID | Organization ID |

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "role": "analyst"
}
```

**Body Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | EmailStr | Yes | Valid email address |
| role | string | No | Role ("admin", "member", "analyst", or custom) |

**Request Example:**
```bash
curl -X POST \
  "https://api.fairmind.io/api/v1/organizations/org-123e4567-e89b-12d3-a456-426614174000/members/invite" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "email": "analyst@company.com",
    "role": "analyst"
  }'
```

**Response (201 Created):**
```json
{
  "invitation_id": "invite-550e8400-e29b-41d4-a716-446655440000",
  "email": "analyst@company.com",
  "role": "analyst",
  "expires_at": "2026-03-29T12:00:00Z",
  "status": "pending"
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Bad Request | Invalid email format |
| 401 | Unauthorized | Missing or invalid JWT |
| 403 | Forbidden | Admin access required |
| 404 | Not Found | Organization doesn't exist |
| 409 | Conflict | User already member or pending invitation exists |
| 500 | Server Error | Email service error (invitation still created) |

**Important Notes:**
- Invitations expire after 7 days
- Email sent asynchronously (doesn't block response)
- Cannot invite existing members
- Cannot create duplicate pending invitations

---

### Update Member Role or Status

```http
PUT /api/v1/organizations/{org_id}/members/{member_id}
```

**Authorization:** Organization admin or owner

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| org_id | UUID | Organization ID |
| member_id | UUID | Member ID to update |

**Request Body (all optional, at least one required):**
```json
{
  "role": "admin",
  "status": "active"
}
```

**Body Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| role | string | New role ("admin", "member", "analyst", custom roles) |
| status | string | New status ("active", "inactive") |

**Request Example:**
```bash
curl -X PUT \
  "https://api.fairmind.io/api/v1/organizations/org-123e4567-e89b-12d3-a456-426614174000/members/member-550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "role": "admin"
  }'
```

**Response (200 OK):**
```json
{
  "status": "updated",
  "member_id": "member-550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Bad Request | Cannot remove last admin from org |
| 401 | Unauthorized | Missing or invalid JWT |
| 403 | Forbidden | Admin access required |
| 404 | Not Found | Member not found in organization |
| 500 | Server Error | Database error |

---

### Remove Member from Organization

```http
DELETE /api/v1/organizations/{org_id}/members/{member_id}
```

**Authorization:** Organization admin or owner

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| org_id | UUID | Organization ID |
| member_id | UUID | Member ID to remove |

**Request Example:**
```bash
curl -X DELETE \
  "https://api.fairmind.io/api/v1/organizations/org-123e4567-e89b-12d3-a456-426614174000/members/member-550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..."
```

**Response (204 No Content):**
```
(empty body)
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Bad Request | Cannot remove last organization admin |
| 401 | Unauthorized | Missing or invalid JWT |
| 403 | Forbidden | Admin access required |
| 404 | Not Found | Member not found |
| 500 | Server Error | Database error |

**Important Notes:**
- **Permanent removal** from organization
- Cannot remove the last admin (organizations need ≥1 admin)
- User can be re-invited later
- Audit log recorded

---

### List Organization Roles

```http
GET /api/v1/organizations/{org_id}/roles
```

**Authorization:** Any organization member

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| org_id | UUID | Organization ID |

**Request Example:**
```bash
curl -X GET \
  "https://api.fairmind.io/api/v1/organizations/org-123e4567-e89b-12d3-a456-426614174000/roles" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..." \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "roles": [
    {
      "id": "role-550e8400-e29b-41d4-a716-446655440000",
      "name": "admin",
      "description": "Full organization control",
      "permissions": [
        "members:view",
        "members:invite",
        "members:edit",
        "members:remove",
        "roles:create",
        "roles:edit",
        "audit:view"
      ],
      "is_system_role": true,
      "created_at": "2026-03-20T10:00:00Z"
    },
    {
      "id": "role-550e8400-e29b-41d4-a716-446655440001",
      "name": "Compliance Officer",
      "description": "Manages compliance and audits",
      "permissions": [
        "members:view",
        "reports:view",
        "reports:export",
        "audit:view"
      ],
      "is_system_role": false,
      "created_at": "2026-03-22T14:00:00Z"
    }
  ]
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Unauthorized | Missing or invalid JWT |
| 403 | Forbidden | Not a member of this organization |
| 404 | Not Found | Organization doesn't exist |
| 500 | Server Error | Database error |

---

### Create Custom Organization Role

```http
POST /api/v1/organizations/{org_id}/roles
```

**Authorization:** Organization admin or owner

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| org_id | UUID | Organization ID |

**Request Body:**
```json
{
  "name": "Data Analyst",
  "description": "Can analyze datasets and generate reports",
  "permissions": [
    "datasets:view",
    "reports:view",
    "reports:generate"
  ]
}
```

**Body Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | Yes | Role name (unique in org) |
| description | string | No | What the role does |
| permissions | array | No | List of permission strings |

**Request Example:**
```bash
curl -X POST \
  "https://api.fairmind.io/api/v1/organizations/org-123e4567-e89b-12d3-a456-426614174000/roles" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Analyst",
    "description": "Can analyze datasets and generate reports",
    "permissions": [
      "datasets:view",
      "reports:view",
      "reports:generate"
    ]
  }'
```

**Response (201 Created):**
```json
{
  "role_id": "role-550e8400-e29b-41d4-a716-446655440002",
  "name": "Data Analyst",
  "status": "created"
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Unauthorized | Missing or invalid JWT |
| 403 | Forbidden | Admin access required |
| 404 | Not Found | Organization doesn't exist |
| 409 | Conflict | Role name already exists in organization |
| 500 | Server Error | Database error |

---

### List Organization Audit Logs

```http
GET /api/v1/organizations/{org_id}/audit-logs
```

**Authorization:** Organization admin or owner (sensitive data)

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| org_id | UUID | Organization ID |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 50 | Number of logs per page |
| skip | integer | 0 | Pagination offset |
| action | string | - | Filter by action (e.g., "invite_member") |

**Request Example:**
```bash
curl -X GET \
  "https://api.fairmind.io/api/v1/organizations/org-123e4567-e89b-12d3-a456-426614174000/audit-logs?limit=25&action=invite_member" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..." \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "logs": [
    {
      "id": "log-550e8400-e29b-41d4-a716-446655440000",
      "user_id": "user-550e8400-e29b-41d4-a716-446655440001",
      "action": "invite_member",
      "resource_type": "member",
      "resource_id": "member-550e8400-e29b-41d4-a716-446655440002",
      "changes": {
        "email": "newuser@example.com",
        "role": "analyst"
      },
      "status": "success",
      "error_message": null,
      "created_at": "2026-03-22T10:30:00Z"
    },
    {
      "id": "log-550e8400-e29b-41d4-a716-446655440003",
      "user_id": "user-550e8400-e29b-41d4-a716-446655440004",
      "action": "remove_member",
      "resource_type": "member",
      "resource_id": "member-550e8400-e29b-41d4-a716-446655440005",
      "changes": {
        "removed_user_id": "user-550e8400-e29b-41d4-a716-446655440006"
      },
      "status": "success",
      "error_message": null,
      "created_at": "2026-03-22T11:00:00Z"
    },
    {
      "id": "log-550e8400-e29b-41d4-a716-446655440007",
      "user_id": "user-550e8400-e29b-41d4-a716-446655440008",
      "action": "invite_member_attempt",
      "resource_type": "member",
      "resource_id": null,
      "changes": {},
      "status": "failed",
      "error_message": "Insufficient permissions (not admin)",
      "created_at": "2026-03-22T11:15:00Z"
    }
  ],
  "total": 127
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Unauthorized | Missing or invalid JWT |
| 403 | Forbidden | Admin access required |
| 404 | Not Found | Organization doesn't exist |
| 500 | Server Error | Database error |

**Common Actions:**
- `invite_member` — Sent member invitation
- `member_accepted_invitation` — Member accepted invitation
- `update_member` — Changed member role/status
- `remove_member` — Removed member from org
- `create_role` — Created custom role
- `create_organization` — Created organization
- `delete_organization` — Deleted organization

---

## Invitation Management

### Get Invitation Details (Unauthenticated)

```http
GET /api/v1/invitations/{token}
```

**Authorization:** None (unauthenticated users can preview)

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| token | UUID | Invitation token from email |

**Request Example:**
```bash
curl -X GET \
  "https://api.fairmind.io/api/v1/invitations/token-550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "org_id": "org-123e4567-e89b-12d3-a456-426614174000",
  "org_name": "Acme Corp",
  "email": "newuser@example.com",
  "role": "analyst",
  "created_at": "2026-03-22T12:00:00Z",
  "expires_at": "2026-03-29T12:00:00Z"
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Bad Request | Invalid or expired token |
| 404 | Not Found | Invitation doesn't exist |
| 500 | Server Error | Database error |

---

### Accept Invitation (Authenticated)

```http
POST /api/v1/invitations/{token}/accept
```

**Authorization:** Valid JWT (user must be logged in)

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| token | UUID | Invitation token from email |

**Request Example:**
```bash
curl -X POST \
  "https://api.fairmind.io/api/v1/invitations/token-550e8400-e29b-41d4-a716-446655440000/accept" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..." \
  -H "Content-Type: application/json"
```

**Response (201 Created):**
```json
{
  "success": true,
  "org_id": "org-123e4567-e89b-12d3-a456-426614174000",
  "org_name": "Acme Corp",
  "user_id": "user-550e8400-e29b-41d4-a716-446655440001",
  "role": "analyst",
  "message": "You have been added to Acme Corp"
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Bad Request | Invalid, expired, or already accepted invitation |
| 401 | Unauthorized | Missing or invalid JWT |
| 403 | Forbidden | Invitation email doesn't match your account |
| 404 | Not Found | Organization doesn't exist |
| 409 | Conflict | Already a member of this organization |
| 500 | Server Error | Database error |

**Post-Acceptance:**
- User added to organization with specified role
- User's `org_id` updated to this organization
- User's `primary_org_id` set (if first organization)
- Audit log: "member_accepted_invitation"
- User can now access organization endpoints

---

## Response Formats

### Success Response

All successful responses include:

```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2026-03-22T12:00:00Z",
    "request_id": "req-550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Common structures:**

**Single Resource:**
```json
{
  "id": "resource-uuid",
  "name": "Resource Name",
  "created_at": "2026-03-22T12:00:00Z"
}
```

**Resource List:**
```json
{
  "items": [ { ... }, { ... } ],
  "total": 42,
  "limit": 25,
  "skip": 0
}
```

### Error Response

All errors follow standard format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2026-03-22T12:00:00Z",
  "request_id": "req-550e8400-e29b-41d4-a716-446655440000"
}
```

**Error status codes:**

| Status | Meaning | Example |
|--------|---------|---------|
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing/invalid JWT |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable | Invalid data type |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Database/server error |

---

## Pagination

Paginated endpoints support limit/skip parameters:

```bash
GET /api/v1/organizations/{org_id}/members?limit=25&skip=0
```

**Response:**
```json
{
  "items": [ ... ],
  "total": 1234,
  "limit": 25,
  "skip": 0
}
```

**Pagination parameters:**
- `limit` — Items per page (default: 50, max: 100)
- `skip` — How many items to skip (for offset pagination)

**Example: Get page 2 with 25 items per page**
```bash
GET /api/v1/organizations/{org_id}/members?limit=25&skip=25
```

---

## Rate Limiting

Rate limits prevent abuse:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1710981600
```

**Default limits:**
- 100 requests per minute per API key
- 1000 requests per hour per API key

**When rate limited (429 Too Many Requests):**
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

**Wait `retry_after` seconds before retrying.**

---

## Webhooks (Future)

Currently not implemented. Coming in Q2 2026:
- Organization events (member added/removed)
- Invitation events (sent/accepted/expired)
- Audit log events (real-time streaming)

---

## API Versioning

Current API version: **v1**

**URL pattern:** `/api/v1/...`

**Backwards compatibility:** v1 maintained for 12 months after v2 release

---

## Examples by Language

### Python

```python
import requests
from datetime import datetime

API_URL = "https://api.fairmind.io"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# List members
response = requests.get(
    f"{API_URL}/api/v1/organizations/org-123/members",
    headers=headers
)
members = response.json()
print(f"Organization has {members['total']} members")

# Invite member
response = requests.post(
    f"{API_URL}/api/v1/organizations/org-123/members/invite",
    headers=headers,
    json={
        "email": "newuser@example.com",
        "role": "analyst"
    }
)
invitation = response.json()
print(f"Invitation sent to {invitation['email']}")
```

### JavaScript/TypeScript

```typescript
const API_URL = "https://api.fairmind.io";
const TOKEN = "your-jwt-token";

async function listMembers(orgId: string) {
  const response = await fetch(
    `${API_URL}/api/v1/organizations/${orgId}/members`,
    {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${TOKEN}`,
        "Content-Type": "application/json"
      }
    }
  );
  const data = await response.json();
  console.log(`Organization has ${data.total} members`);
  return data;
}

async function inviteMember(orgId: string, email: string, role: string) {
  const response = await fetch(
    `${API_URL}/api/v1/organizations/${orgId}/members/invite`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${TOKEN}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        email,
        role
      })
    }
  );
  const invitation = await response.json();
  console.log(`Invitation sent to ${invitation.email}`);
  return invitation;
}
```

### cURL

```bash
#!/bin/bash

API_URL="https://api.fairmind.io"
ORG_ID="org-123e4567-e89b-12d3-a456-426614174000"
TOKEN="your-jwt-token"

# List members
curl -X GET \
  "${API_URL}/api/v1/organizations/${ORG_ID}/members" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq .

# Invite member
curl -X POST \
  "${API_URL}/api/v1/organizations/${ORG_ID}/members/invite" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "role": "analyst"
  }' | jq .

# Accept invitation
TOKEN_TO_ACCEPT="token-550e8400-e29b-41d4-a716-446655440000"
curl -X POST \
  "${API_URL}/api/v1/invitations/${TOKEN_TO_ACCEPT}/accept" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq .
```

---

## Common Response Examples

### Success - 200 OK

```
HTTP/1.1 200 OK
Content-Type: application/json
X-RateLimit-Remaining: 95

{
  "members": [
    {
      "id": "member-uuid",
      "email": "user@example.com",
      "role": "analyst",
      "status": "active",
      "joined_at": "2026-03-20T12:00:00Z"
    }
  ],
  "total": 5
}
```

### Success - 201 Created

```
HTTP/1.1 201 Created
Content-Type: application/json
Location: /api/v1/organizations/org-123/members/member-uuid

{
  "invitation_id": "invite-uuid",
  "email": "newuser@example.com",
  "role": "analyst",
  "expires_at": "2026-03-29T12:00:00Z",
  "status": "pending"
}
```

### Success - 204 No Content

```
HTTP/1.1 204 No Content
(empty body)
```

### Error - 401 Unauthorized

```
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "detail": "Missing or invalid authentication token"
}
```

### Error - 403 Forbidden

```
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "Admin access required"
}
```

### Error - 409 Conflict

```
HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "detail": "User is already a member of this organization"
}
```

---

## Best Practices

1. **Always include Authorization header** — All endpoints except `/invitations/{token}` require JWT
2. **Handle rate limiting** — Check X-RateLimit-Remaining and respect 429 responses
3. **Use pagination** — Don't fetch all records at once, use limit/skip
4. **Validate input** — Email addresses, UUIDs, role names
5. **Retry on 5xx errors** — Use exponential backoff (e.g., 1s, 2s, 4s, 8s)
6. **Check error details** — Error messages provide context for debugging
7. **Store request IDs** — Useful for support tickets and debugging
8. **Use HTTPS only** — Always use https://api.fairmind.io, never http://

---

**Document Version:** 1.0
**Last Updated:** March 2026
