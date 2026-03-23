# FairMind RBAC Implementation Guide

**Version:** 1.0
**Last Updated:** March 2026
**Status:** Production Documentation

---

## Table of Contents

1. [Overview](#overview)
2. [Key Concepts](#key-concepts)
3. [User Roles & Permissions](#user-roles--permissions)
4. [API Endpoints Reference](#api-endpoints-reference)
5. [Permission Decorators](#permission-decorators)
6. [Multi-Tenancy Architecture](#multi-tenancy-architecture)
7. [Invitation Flow](#invitation-flow)
8. [Security Model](#security-model)
9. [Compliance & Audit](#compliance--audit)
10. [Deployment Checklist](#deployment-checklist)

---

## Overview

### What is RBAC?

Role-Based Access Control (RBAC) in FairMind is a comprehensive system that controls who can perform which actions within an organization. It operates at two levels:

**Global Level (System-wide):**
- Controls access to FairMind platform features
- Manages user types: admin, analyst, viewer
- Applied at authentication time via Authentik

**Organizational Level (Per Organization):**
- Controls access within multi-tenant organizations
- Each organization has its own members, roles, and permissions
- Admins can create custom roles specific to their needs

### Why RBAC?

**Compliance Requirements:**
- NITI Aayog, RBI, DPDP Act, and GDPR all mandate access control auditing
- Organizations must prove who accessed what, when, and why
- RBAC provides audit-ready permission trails

**Multi-Tenancy Isolation:**
- Organizations cannot access other organizations' data
- Member data is segregated at database and application layers
- Complete isolation: Members see only their organization's data

**Security:**
- Principle of least privilege: Users get minimum permissions needed
- Fine-grained control down to individual actions
- Immutable audit logs prevent unauthorized access denial

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend Application (Next.js)                                  │
│ - OAuth2 login with Authentik                                   │
│ - JWT token obtained on successful authentication               │
│ - Token stored in HttpOnly cookie                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP Request + Bearer Token
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Authentik OAuth2 Provider                                       │
│ - Validates credentials                                         │
│ - Issues RS256-signed JWT with claims: user_id, email, role     │
│ - Token includes global permissions (admin/analyst/viewer)      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ JWT with user_id, email, global_role
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Middleware Layer (auth.py → rbac.py)                            │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ 1. Extract JWT from Authorization header                  │  │
│ │ 2. Validate JWT signature (RS256) using Authentik public  │  │
│ │ 3. Extract user_id, email, global_role from JWT claims    │  │
│ │ 4. Extract org_id from path parameter (/{org_id}/...)     │  │
│ │ 5. Store in request.state: user_id, org_id, email, role   │  │
│ └────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ request.state populated with user context
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Permission Decorators (@require_org_admin, etc.)                │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ 1. Check user is member of organization (org_members)     │  │
│ │ 2. Verify user's role (admin/member/analyst/custom)       │  │
│ │ 3. Check permission if @require_permission decorator      │  │
│ │ 4. Return 403 Forbidden if authorization fails            │  │
│ │ 5. Log failed authorization attempt to audit logs          │  │
│ └────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Authorization verified
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Endpoint Handler (org_management.py routes)                     │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ Query Filtering:                                           │  │
│ │ - All SELECT queries include: WHERE org_id = :org_id       │  │
│ │ - Prevents cross-organization data leakage                 │  │
│ │ - Database parameterized queries prevent SQL injection     │  │
│ └────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Execute business logic
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Audit Logging (@audit_org_action decorator)                     │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ Insert into org_audit_logs:                                │  │
│ │ - org_id, user_id, action, resource_type, changes          │  │
│ │ - status (success/failure), error_message if failed        │  │
│ │ - ip_address, user_agent for forensics                     │  │
│ │ - timestamp (immutable, append-only)                       │  │
│ └────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Immutable audit trail created
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Database (Neon PostgreSQL)                                      │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ organizations - org records with owner_id                  │  │
│ │ org_members - membership with org_id, user_id, role        │  │
│ │ org_roles - role definitions with permissions              │  │
│ │ org_invitations - pending invites with tokens              │  │
│ │ org_audit_logs - immutable action history                  │  │
│ │ users - global user data from Authentik sync               │  │
│ └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Concepts

### Organizations

Organizations are multi-tenant boundaries in FairMind. Each organization:

- Has a unique ID (UUID)
- Has one owner (who can delete the organization)
- Contains members with assigned roles
- Has custom roles defined by the organization admin
- Maintains isolated audit logs
- Cannot access other organizations' data

**Database Table: `organizations`**
```sql
id (UUID)              -- Unique organization ID
name (VARCHAR)         -- Organization display name
owner_id (UUID)        -- User ID of the owner
created_at (TIMESTAMP) -- When org was created
```

### Users

Users are global accounts in FairMind, typically created via Authentik OAuth2. Each user:

- Has a global role (admin/analyst/viewer) from Authentik
- Can belong to multiple organizations
- Has a `primary_org_id` (first organization they joined)
- Has a current `org_id` (organization they're working in)
- May have different roles in different organizations

**Database Table: `users`**
```sql
id (UUID)              -- Unique user ID
email (VARCHAR)        -- Email address
full_name (VARCHAR)    -- Display name
authentik_id (VARCHAR) -- Linked Authentik ID
primary_org_id (UUID)  -- First organization joined
org_id (UUID)          -- Current organization context
is_active (BOOLEAN)    -- Account active status
created_at (TIMESTAMP) -- When user registered
last_login (TIMESTAMP) -- Last authentication time
```

### Roles

FairMind has two types of roles:

**System Roles (Global - from Authentik):**
- `admin` — Full FairMind platform access, can create organizations
- `analyst` — Data analysis + report access
- `viewer` — Read-only access to dashboards

**Organization Roles (Per-organization):**
- `owner` — Full organization control (can delete org, manage all members)
- `admin` — Manage members, customize roles, view settings
- `member` — Standard access (view data, contribute)
- `analyst` — Read + analysis (view data, run reports)
- Custom roles — Organizations can define their own

**Database Table: `org_roles`**
```sql
id (UUID)          -- Unique role ID
org_id (UUID)      -- Organization this role belongs to
name (VARCHAR)     -- Role name (e.g., "Data Analyst")
description (TEXT) -- What this role can do
permissions (JSON) -- Array of permission strings
is_system_role (BOOLEAN) -- FALSE for custom roles
created_at (TIMESTAMP)
```

### Permissions

Permissions are granular actions that a role can perform. Format: `resource:action`

Examples:
```
members:view           -- View member list
members:invite         -- Send invitations
members:edit           -- Update member roles
members:remove         -- Delete members from org
reports:view           -- View compliance reports
reports:export         -- Export reports to PDF/CSV
datasets:upload        -- Add datasets
datasets:delete        -- Remove datasets
roles:create           -- Create custom roles
roles:edit             -- Modify role permissions
audit:view             -- View audit logs
```

Permissions are stored as JSON arrays in `org_roles.permissions`:
```json
["members:view", "members:invite", "reports:view", "datasets:upload"]
```

### Audit Logs

All organization actions are logged immutably for compliance. Logs include:

- **Who** (user_id) performed the action
- **What** (action name: invite_member, remove_member, etc.)
- **When** (timestamp, never modified)
- **Where** (resource_type and resource_id affected)
- **How** (ip_address and user_agent for forensics)
- **Changes** (before/after values for updates)
- **Status** (success or failure, with error message if failed)

**Database Table: `org_audit_logs`**
```sql
id (UUID)              -- Unique audit log ID
org_id (UUID)          -- Organization where action occurred
user_id (UUID)         -- User who performed action
action (VARCHAR)       -- Action name (invite_member, etc.)
resource_type (VARCHAR) -- What was affected (member, role, etc.)
resource_id (VARCHAR)  -- ID of the resource
changes (JSON)         -- What changed {field: new_value, ...}
status (VARCHAR)       -- "success" or "failure"
error_message (TEXT)   -- Reason if failed
ip_address (VARCHAR)   -- Source IP (for forensics)
user_agent (TEXT)      -- Browser/client info
created_at (TIMESTAMP) -- When action occurred (immutable)
```

### Invitations

Email-based membership onboarding. When an admin invites a user:

1. Creates a pending invitation with a unique token
2. Sends email with link containing the token
3. User clicks link, optionally logs in
4. User accepts invitation
5. User is added to organization as a member

**Database Table: `org_invitations`**
```sql
id (UUID)          -- Unique invitation ID
org_id (UUID)      -- Organization they're being invited to
email (VARCHAR)    -- Email address invited
role (VARCHAR)     -- Role they'll have if accepted
token (UUID)       -- Unique acceptance token (sent via email)
expires_at (TIMESTAMP) -- Invitation expires after 7 days
status (VARCHAR)   -- "pending", "accepted", or "expired"
invited_by (UUID)  -- User who sent the invitation
created_at (TIMESTAMP) -- When invitation was created
accepted_at (TIMESTAMP) -- When invitation was accepted
```

---

## User Roles & Permissions

### Global Roles (from Authentik)

These roles are assigned by Authentik during OAuth2 login and apply system-wide.

#### `admin` - Full System Access
- Create and delete organizations
- Access all organization data they join
- Create custom roles in their organizations
- View all compliance reports
- Access to all datasets
- Can never be removed from their own organizations

**Global Permissions:**
```
organizations:create
organizations:delete
organizations:manage
teams:manage
reports:export
datasets:manage
```

#### `analyst` - Data Analysis Access
- Join organizations (via invitation)
- Run bias detection on datasets
- Generate analysis reports
- View compliance reports
- Cannot invite members or manage organization

**Global Permissions:**
```
datasets:analyze
reports:view
reports:generate
models:evaluate
```

#### `viewer` - Read-Only Access
- View dashboards and reports
- Cannot perform any actions
- Cannot modify any data
- Useful for stakeholder visibility

**Global Permissions:**
```
dashboard:view
reports:view
```

### Organization Roles (Per-organization)

These roles are created per organization and control access within that organization.

#### `owner` - Organization Owner
- Full control over the organization
- Can delete the organization (careful!)
- Manage all members (invite, remove, change roles)
- Create and edit custom roles
- View all audit logs
- Cannot be removed from organization

**Requirements:**
- Each organization must have at least one owner
- Prevents removing the last owner

**Organization Permissions:**
```
members:view
members:invite
members:edit
members:remove
roles:create
roles:edit
roles:delete
audit:view
organization:delete
```

#### `admin` - Organization Admin
- Manage members (invite, remove, change roles)
- Create and edit custom roles
- View audit logs
- Cannot delete organization
- Cannot remove the last admin

**Requirements:**
- Each organization must have at least one admin (or owner)
- Prevents removing the last admin

**Organization Permissions:**
```
members:view
members:invite
members:edit
members:remove
roles:create
roles:edit
audit:view
```

#### `member` - Standard Member
- View members and organization data
- Contribute to datasets
- Generate reports
- Cannot manage members or roles
- Standard "employee" role

**Organization Permissions:**
```
members:view
datasets:view
datasets:upload
reports:generate
reports:view
```

#### `analyst` - Read + Analysis
- View data and reports
- Run analysis
- Cannot modify data or members
- "Analyst" role for data scientists

**Organization Permissions:**
```
datasets:view
reports:view
reports:generate
models:evaluate
audit:view
```

#### Custom Roles
Organizations can define custom roles. For example:

```json
{
  "name": "Compliance Officer",
  "description": "Manages compliance reporting and audit logs",
  "permissions": [
    "members:view",
    "audit:view",
    "reports:view",
    "reports:export"
  ]
}
```

### Permission Matrix

| Permission | Owner | Admin | Member | Analyst | Viewer |
|-----------|-------|-------|--------|---------|--------|
| members:view | ✓ | ✓ | ✓ | ✓ | ✗ |
| members:invite | ✓ | ✓ | ✗ | ✗ | ✗ |
| members:edit | ✓ | ✓ | ✗ | ✗ | ✗ |
| members:remove | ✓ | ✓ | ✗ | ✗ | ✗ |
| roles:create | ✓ | ✓ | ✗ | ✗ | ✗ |
| roles:edit | ✓ | ✓ | ✗ | ✗ | ✗ |
| datasets:view | ✓ | ✓ | ✓ | ✓ | ✗ |
| datasets:upload | ✓ | ✓ | ✓ | ✗ | ✗ |
| datasets:delete | ✓ | ✓ | ✗ | ✗ | ✗ |
| reports:generate | ✓ | ✓ | ✓ | ✓ | ✗ |
| reports:view | ✓ | ✓ | ✓ | ✓ | ✓ |
| reports:export | ✓ | ✓ | ✗ | ✗ | ✗ |
| audit:view | ✓ | ✓ | ✗ | ✓ | ✗ |
| organization:delete | ✓ | ✗ | ✗ | ✗ | ✗ |

---

## API Endpoints Reference

### Organization Member Management (7 Endpoints)

#### 1. List Organization Members

```
GET /api/v1/organizations/{org_id}/members
```

**Authorization:** Any organization member

**Parameters:**
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| org_id | UUID | path | Yes | Organization ID |
| limit | integer | query | No | Page size (default: 50, max: 100) |
| skip | integer | query | No | Pagination offset (default: 0) |

**Response (200 OK):**
```json
{
  "members": [
    {
      "id": "member-uuid-1",
      "user_id": "user-uuid-1",
      "email": "alice@example.com",
      "name": "Alice Cooper",
      "role": "admin",
      "status": "active",
      "joined_at": "2026-03-20T12:00:00Z"
    },
    {
      "id": "member-uuid-2",
      "user_id": "user-uuid-2",
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
| Status | Detail |
|--------|--------|
| 401 | Missing or invalid authentication token |
| 403 | Not a member of this organization |
| 404 | Organization doesn't exist |
| 500 | Database error |

**Example Request:**
```bash
curl -X GET \
  "https://api.fairmind.io/api/v1/organizations/org-123/members?limit=25&skip=0" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

---

#### 2. Invite Member to Organization

```
POST /api/v1/organizations/{org_id}/members/invite
```

**Authorization:** Organization admin or owner

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "role": "analyst"
}
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| email | EmailStr | Yes | Email to invite (must be valid email) |
| role | string | No | Role to assign (default: "analyst") |

**Response (201 Created):**
```json
{
  "invitation_id": "invite-uuid-123",
  "email": "newuser@example.com",
  "role": "analyst",
  "expires_at": "2026-03-30T12:00:00Z",
  "status": "pending"
}
```

**Error Responses:**
| Status | Detail |
|--------|--------|
| 400 | Invalid email format |
| 401 | Missing or invalid token |
| 403 | Admin access required |
| 404 | Organization doesn't exist |
| 409 | User already a member or pending invitation exists |
| 500 | Failed to invite member |

**Important Notes:**
- Invitation tokens expire after **7 days**
- Cannot invite existing members
- Cannot send duplicate pending invitations
- Email is sent asynchronously (doesn't block response)
- If email send fails, invitation is still created

**Example Request:**
```bash
curl -X POST \
  "https://api.fairmind.io/api/v1/organizations/org-123/members/invite" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "analyst@company.com",
    "role": "analyst"
  }'
```

---

#### 3. Update Member Role or Status

```
PUT /api/v1/organizations/{org_id}/members/{member_id}
```

**Authorization:** Organization admin or owner

**Request Body:**
```json
{
  "role": "admin",
  "status": "active"
}
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | UUID | Yes | Organization ID |
| member_id | UUID | Yes | Member ID to update |
| role | string | No | New role to assign |
| status | string | No | New status ("active" or "inactive") |

**Response (200 OK):**
```json
{
  "status": "updated",
  "member_id": "member-uuid"
}
```

**Error Responses:**
| Status | Detail |
|--------|--------|
| 400 | Cannot remove last organization admin |
| 401 | Missing or invalid token |
| 403 | Admin access required |
| 404 | Member not found |
| 500 | Failed to update member |

**Important Safeguards:**
- Cannot demote the last admin to non-admin role
- Audit log records the change
- Status can be "active" or "inactive" (soft delete)

**Example Request:**
```bash
curl -X PUT \
  "https://api.fairmind.io/api/v1/organizations/org-123/members/member-456" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "admin"
  }'
```

---

#### 4. Remove Member from Organization

```
DELETE /api/v1/organizations/{org_id}/members/{member_id}
```

**Authorization:** Organization admin or owner

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | UUID | Yes | Organization ID |
| member_id | UUID | Yes | Member ID to remove |

**Response (204 No Content):**
```
(empty body)
```

**Error Responses:**
| Status | Detail |
|--------|--------|
| 400 | Cannot remove the last organization admin |
| 401 | Missing or invalid token |
| 403 | Admin access required |
| 404 | Member not found |
| 500 | Failed to remove member |

**Important Notes:**
- **Permanent removal** (deleted from org_members table)
- Prevents removing the last admin (organization must have ≥1 admin)
- Audit log records the removal
- User can be re-invited later

**Example Request:**
```bash
curl -X DELETE \
  "https://api.fairmind.io/api/v1/organizations/org-123/members/member-456" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

#### 5. List Organization Roles

```
GET /api/v1/organizations/{org_id}/roles
```

**Authorization:** Any organization member

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | UUID | Yes | Organization ID |

**Response (200 OK):**
```json
{
  "roles": [
    {
      "id": "role-uuid-1",
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
      "id": "role-uuid-2",
      "name": "Compliance Officer",
      "description": "Manages compliance reporting",
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
| Status | Detail |
|--------|--------|
| 401 | Missing or invalid token |
| 403 | Not a member of this organization |
| 404 | Organization doesn't exist |
| 500 | Failed to list roles |

**Example Request:**
```bash
curl -X GET \
  "https://api.fairmind.io/api/v1/organizations/org-123/roles" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

#### 6. Create Custom Organization Role

```
POST /api/v1/organizations/{org_id}/roles
```

**Authorization:** Organization admin or owner

**Request Body:**
```json
{
  "name": "Data Analyst",
  "description": "Can view and analyze datasets",
  "permissions": [
    "datasets:view",
    "reports:view",
    "reports:generate"
  ]
}
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | UUID | Yes | Organization ID |
| name | string | Yes | Role name (must be unique in org) |
| description | string | No | What this role does |
| permissions | array | No | List of permission strings |

**Response (201 Created):**
```json
{
  "role_id": "role-uuid-new",
  "name": "Data Analyst",
  "status": "created"
}
```

**Error Responses:**
| Status | Detail |
|--------|--------|
| 401 | Missing or invalid token |
| 403 | Admin access required |
| 404 | Organization doesn't exist |
| 409 | Role name already exists in this organization |
| 500 | Failed to create role |

**Important Notes:**
- Role names must be unique within the organization
- Cannot create system roles (admin, member, analyst)
- Permissions can be any string (e.g., "resource:action")
- Custom roles can be assigned to new members

**Example Request:**
```bash
curl -X POST \
  "https://api.fairmind.io/api/v1/organizations/org-123/roles" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Compliance Officer",
    "description": "Manages compliance reporting and audits",
    "permissions": [
      "members:view",
      "reports:view",
      "reports:export",
      "audit:view"
    ]
  }'
```

---

#### 7. List Organization Audit Logs

```
GET /api/v1/organizations/{org_id}/audit-logs
```

**Authorization:** Organization admin or owner

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | UUID | Yes | Organization ID |
| limit | integer | No | Page size (default: 50, max: 100) |
| skip | integer | No | Pagination offset (default: 0) |
| action | string | No | Filter by action (e.g., "invite_member") |

**Response (200 OK):**
```json
{
  "logs": [
    {
      "id": "log-uuid-1",
      "user_id": "user-uuid-admin",
      "action": "invite_member",
      "resource_type": "member",
      "resource_id": "member-uuid-new",
      "changes": {
        "email": "newuser@example.com",
        "role": "analyst"
      },
      "status": "success",
      "error_message": null,
      "created_at": "2026-03-22T10:30:00Z"
    },
    {
      "id": "log-uuid-2",
      "user_id": "user-uuid-admin",
      "action": "update_member",
      "resource_type": "member",
      "resource_id": "member-uuid-old",
      "changes": {
        "role": "admin"
      },
      "status": "success",
      "error_message": null,
      "created_at": "2026-03-22T11:00:00Z"
    },
    {
      "id": "log-uuid-3",
      "user_id": "user-uuid-member",
      "action": "remove_member_attempt",
      "resource_type": "member",
      "resource_id": "member-uuid-admin",
      "changes": {},
      "status": "failure",
      "error_message": "Admin access required",
      "created_at": "2026-03-22T11:15:00Z"
    }
  ],
  "total": 127
}
```

**Error Responses:**
| Status | Detail |
|--------|--------|
| 401 | Missing or invalid token |
| 403 | Admin access required (audit logs are sensitive) |
| 404 | Organization doesn't exist |
| 500 | Failed to list audit logs |

**Audit Log Actions:**
Common actions tracked: `invite_member`, `accept_invitation`, `update_member`, `remove_member`, `create_role`, `create_organization`, `delete_organization`

**Example Request:**
```bash
curl -X GET \
  "https://api.fairmind.io/api/v1/organizations/org-123/audit-logs?limit=25&action=invite_member" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

### Authentication Endpoints (3 Endpoints)

#### Register / Create Account

```
POST /api/v1/auth/register
```

Creates a new user account. Integration with Authentik OAuth2 is preferred for production.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "secure-password"
}
```

**Response (201 Created):**
```json
{
  "user_id": "user-uuid",
  "email": "user@example.com",
  "status": "registered"
}
```

---

#### Login / Get Access Token

```
POST /api/v1/auth/login
```

**Production:** Uses Authentik OAuth2 redirect, not this endpoint.

**Development:** Direct login with credentials.

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

#### Accept Invitation

```
POST /api/v1/invitations/{token}/accept
```

**Authorization:** Required (user must be authenticated)

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| token | UUID | Yes | Invitation token from email link |

**Response (201 Created):**
```json
{
  "success": true,
  "org_id": "org-uuid",
  "org_name": "Acme Corp",
  "user_id": "user-uuid",
  "role": "analyst",
  "message": "You have been added to Acme Corp"
}
```

**Error Responses:**
| Status | Detail |
|--------|--------|
| 400 | Invalid or expired invitation token |
| 401 | Missing or invalid authentication |
| 403 | Invitation email doesn't match your account email |
| 404 | Organization doesn't exist |
| 409 | Already a member of this organization |
| 500 | Failed to accept invitation |

**Important Notes:**
- Requires valid JWT (user must be logged in)
- Email in invitation must match authenticated user's email
- Creates `org_member` record
- Sets `user.org_id` to the organization
- Sets `user.primary_org_id` if null (first org they join)
- Logs audit event "member_accepted_invitation"

**Example Request:**
```bash
curl -X POST \
  "https://api.fairmind.io/api/v1/invitations/token-uuid-123/accept" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

---

### Compliance Endpoints

#### Generate Compliance Audit Report

```
GET /api/v1/organizations/{org_id}/compliance/audit-report
```

**Authorization:** Organization admin or owner

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | UUID | Yes | Organization ID |
| start_date | ISO-8601 | No | Report start date |
| end_date | ISO-8601 | No | Report end date |
| format | string | No | Output format (json, csv, pdf) |

**Response (200 OK - JSON format):**
```json
{
  "report_id": "report-uuid",
  "org_id": "org-uuid",
  "org_name": "Acme Corp",
  "period": {
    "start": "2026-01-01T00:00:00Z",
    "end": "2026-03-22T23:59:59Z"
  },
  "summary": {
    "total_actions": 427,
    "total_members": 12,
    "total_failed_attempts": 3,
    "total_permission_denials": 1
  },
  "actions": [
    {
      "timestamp": "2026-03-22T10:30:00Z",
      "user_id": "user-uuid",
      "user_email": "alice@example.com",
      "action": "invite_member",
      "resource": "member",
      "status": "success",
      "details": {
        "invited_email": "bob@example.com",
        "role": "analyst"
      }
    }
  ],
  "generated_at": "2026-03-22T15:00:00Z"
}
```

**Compliance Use Cases:**
- NITI Aayog: Show access control audit trail
- RBI: Demonstrate user action accountability
- DPDP Act: Prove data access is logged and tracked
- GDPR: Show who accessed personal data and when

---

## Permission Decorators

Permission decorators are Python decorators that enforce authorization at the endpoint level. They work with the middleware to control access.

### Decorator Stack

Decorators should be applied in this order (top to bottom):

```python
@router.post("/{org_id}/members/invite")
@isolate_by_org                          # 1. Extract org context (if needed)
@require_org_admin                       # 2. Check authorization
@audit_org_action("invite_member", "member")  # 3. Log the action
async def invite_member(org_id: str, request: Request, db):
    ...
```

**Why this order?**
1. `@isolate_by_org` ensures org context is available
2. Permission decorators validate before executing
3. `@audit_org_action` logs the execution attempt

### Decorator Reference

#### `@require_org_owner`

Verifies user is the organization owner.

```python
@router.delete("/{org_id}")
@require_org_owner
async def delete_organization(org_id: str, request: Request, db):
    # Only the owner can delete the org
    await db.execute(f"DELETE FROM organizations WHERE id = :id", {"id": org_id})
```

**Behavior:**
- Checks `organizations.owner_id` against authenticated user
- Raises 403 if user is not the owner
- Logs failed attempts to audit logs

**Use cases:**
- Delete organization
- Change organization owner
- Dissolve organization

---

#### `@require_org_admin`

Verifies user has admin or owner role in the organization.

```python
@router.post("/{org_id}/members/invite")
@require_org_admin
async def invite_member(org_id: str, payload: InviteMemberRequest, request: Request, db):
    # Admin or owner can invite members
    ...
```

**Behavior:**
- Checks `org_members.role` where role IN ('admin', 'owner')
- Raises 403 if user is not admin or owner
- Logs failed attempts

**Use cases:**
- Manage members (invite, remove, update role)
- Create and edit custom roles
- View and export audit logs
- Configure organization settings

---

#### `@require_org_member`

Verifies user is any member of the organization.

```python
@router.get("/{org_id}/members")
@require_org_member
async def list_members(org_id: str, request: Request, db):
    # Any member can view the member list
    ...
```

**Behavior:**
- Checks if user exists in `org_members` table
- Allows any role (member, analyst, admin, owner, custom)
- Raises 403 if user is not a member
- Does NOT check specific permissions

**Use cases:**
- View members
- View reports
- View organizational data
- View audit logs (for compliance officers)

---

#### `@require_permission("resource:action")`

Checks if user's role has a specific permission.

```python
@router.post("/{org_id}/reports/export")
@require_permission("reports:export")
async def export_report(org_id: str, request: Request, db):
    # Only users with "reports:export" permission can export
    ...
```

**Behavior:**
1. Get user's role from `org_members`
2. Get role's permissions from `org_roles`
3. Check if permission is in permissions array
4. Raise 403 if missing

**Permission format:** `resource:action` (e.g., "members:invite")

**Use cases:**
- Fine-grained access control
- Enforce custom role permissions
- Restrict sensitive actions (e.g., data export, deletion)

**Example:**
```python
@router.delete("/{org_id}/datasets/{dataset_id}")
@require_permission("datasets:delete")
async def delete_dataset(org_id: str, dataset_id: str, request: Request, db):
    # Only users with "datasets:delete" permission
    ...
```

---

#### `@require_permissions(["perm1", "perm2"], require_all=True)`

Checks if user has multiple permissions. Use `require_all=False` for OR logic.

```python
# User must have BOTH permissions
@router.post("/{org_id}/reports/export-secure")
@require_permissions(["reports:view", "reports:export"])
async def export_secure_report(org_id: str, request: Request, db):
    ...

# User must have AT LEAST ONE permission
@router.get("/{org_id}/reports")
@require_permissions(["reports:admin", "reports:view"], require_all=False)
async def list_reports(org_id: str, request: Request, db):
    ...
```

**Behavior:**
- `require_all=True` (default): User must have ALL permissions (AND logic)
- `require_all=False`: User must have AT LEAST ONE permission (OR logic)
- Raises 403 if requirement not met

**Use cases:**
- Complex authorization (e.g., admin OR analyst who created the resource)
- Restrict sensitive operations requiring multiple permissions
- Role composition

---

#### `@audit_org_action("action_name", "resource_type")`

Logs organization actions to `org_audit_logs` table.

```python
@router.post("/{org_id}/members/invite")
@require_org_admin
@audit_org_action("invite_member", "member")
async def invite_member(org_id: str, payload: InviteMemberRequest, request: Request, db):
    ...
```

**Logged Information:**
- `org_id` — Organization where action occurred
- `user_id` — User who performed action
- `action` — Action name ("invite_member")
- `resource_type` — What was affected ("member")
- `resource_id` — ID of the resource
- `changes` — What changed (passed from endpoint)
- `status` — "success" or "failure"
- `error_message` — If failed
- `ip_address` — Source IP (from X-Forwarded-For or client address)
- `user_agent` — Browser/client info
- `created_at` — When action occurred (immutable)

**Behavior:**
- Logs both successful and failed action attempts
- Does NOT log failed permission checks (those happen before decorator)
- Does NOT break request if logging fails
- Timestamps are immutable (append-only audit trail)

**Use cases:**
- Compliance auditing (who did what, when)
- Security forensics (trace actions by user)
- Investigate unauthorized attempts
- Generate audit reports for regulators

---

### Complete Example: Invite Member Endpoint

```python
from fastapi import APIRouter, Request, Depends
from config.auth import get_current_active_user, TokenData
from config.database import get_db_connection
from core.decorators.org_permissions import require_org_admin, audit_org_action

router = APIRouter(prefix="/api/v1/organizations", tags=["members"])

@router.post("/{org_id}/members/invite", status_code=201)
@require_org_admin  # 1. Check user is admin/owner
@audit_org_action("invite_member", "member")  # 2. Log the action
async def invite_member(
    org_id: str,
    payload: InviteMemberRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Invite a new member to organization via email.

    Authorization: Requires admin role in organization
    Logging: All invitations logged to org_audit_logs
    """
    async with get_db_connection() as db:
        # Authorization checks already done by decorators

        # Create invitation in database
        invitation_id = str(uuid.uuid4())
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=7)

        await db.execute(
            """
            INSERT INTO org_invitations
            (id, org_id, email, role, token, expires_at, status, invited_by, created_at)
            VALUES (:id, :org_id, :email, :role, :token, :expires_at, 'pending', :invited_by, :created_at)
            """,
            {
                "id": invitation_id,
                "org_id": org_id,
                "email": payload.email,
                "role": payload.role,
                "token": token,
                "expires_at": expires_at,
                "invited_by": current_user.user_id,
                "created_at": datetime.utcnow()
            }
        )

        # Send email asynchronously
        await email_service.send_org_invitation(
            email=payload.email,
            token=token,
            role=payload.role,
            expires_at=expires_at.isoformat()
        )

        return {
            "invitation_id": invitation_id,
            "email": payload.email,
            "role": payload.role,
            "expires_at": expires_at.isoformat(),
            "status": "pending"
        }
```

---

## Multi-Tenancy Architecture

FairMind uses 5 layers of multi-tenancy enforcement to prevent cross-organization data leakage.

### Layer 1: Middleware - Organization Context Extraction

The `rbac.py` middleware extracts organization ID from the request and validates JWT:

```python
# In middleware/rbac.py
@app.middleware("http")
async def org_isolation_middleware(request: Request, call_next):
    # 1. Extract JWT and validate
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = jwt.decode(token, key=settings.jwt_public_key, algorithms=["RS256"])

    # 2. Extract user context from JWT claims
    request.state.user_id = payload.get("sub")  # User ID from Authentik
    request.state.email = payload.get("email")
    request.state.role = payload.get("role")

    # 3. Extract org_id from path (/{org_id}/...)
    path_parts = request.url.path.split("/")
    if "organizations" in path_parts:
        idx = path_parts.index("organizations")
        if idx + 1 < len(path_parts):
            request.state.org_id = path_parts[idx + 1]

    # 4. Continue to endpoint
    response = await call_next(request)
    return response
```

**Result:** `request.state` now contains: `user_id`, `email`, `role`, `org_id`

### Layer 2: Permission Decorators - Authorization Check

Decorators verify user is authorized before endpoint executes:

```python
@require_org_admin  # Checks org_members table
async def invite_member(org_id: str, request: Request, db):
    # Only executed if user is admin/owner of org_id
    ...
```

**Enforcement:** Queries `org_members` where `org_id = :org_id AND user_id = :user_id`

### Layer 3: Query Filtering - WHERE org_id Clause

All queries in endpoints filter by organization:

```python
# Every SELECT query includes org_id filter
members = await db.fetch_all(
    """
    SELECT * FROM org_members
    WHERE org_id = :org_id
    ORDER BY created_at DESC
    """,
    {"org_id": org_id}
)
```

**Result:** Cannot accidentally return data from other organizations

### Layer 4: Row Level Security (RLS) - Database Policies

PostgreSQL Row Level Security enforces isolation at database level:

```sql
-- Enable RLS on all organization tables
ALTER TABLE org_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_audit_logs ENABLE ROW LEVEL SECURITY;

-- Policies (example for org_members)
CREATE POLICY org_members_isolation ON org_members
    USING (org_id = current_setting('app.current_org_id'));

-- Set org context when user connects
SET app.current_org_id = 'org-uuid-123';

-- Now even if a query forgets WHERE org_id = ...,
-- PostgreSQL will filter by org_id automatically
SELECT * FROM org_members;  -- Automatically filtered!
```

**Result:** Defense-in-depth: Even if code has a bug, RLS policies protect data

### Layer 5: Audit Logging - Trail for Forensics

Every action is logged with org context:

```python
@audit_org_action("delete_member", "member")
async def remove_member(org_id: str, member_id: str, request: Request, db):
    # Action logged to org_audit_logs with org_id
    # Later: Can prove who accessed what in which org
    ...
```

**Logged:** `org_id`, `user_id`, `action`, `resource_id`, `status`, `ip_address`, `timestamp`

**Result:** Complete audit trail for compliance investigations

### Multi-Tenancy Security Checklist

- ✓ **No hardcoded org IDs** in code
- ✓ **All SELECT queries** include `WHERE org_id = :org_id`
- ✓ **All INSERT queries** include `org_id` parameter
- ✓ **All UPDATE/DELETE queries** check `org_id` match
- ✓ **Permission decorators** validate organization membership
- ✓ **Database RLS** enforces isolation at SQL level
- ✓ **Audit logs** include org_id for forensics
- ✓ **JWT validation** confirms user identity
- ✓ **Email verification** on invitation acceptance
- ✓ **IP logging** for fraud detection

---

## Invitation Flow

Email-based membership invitation in 7 steps:

### Step 1: Admin Sends Invitation

```bash
POST /api/v1/organizations/org-123/members/invite

{
  "email": "newuser@example.com",
  "role": "analyst"
}
```

**Backend:**
- Checks user is admin/owner (403 if not)
- Creates `org_invitations` record with 7-day expiration
- Generates unique token (UUID)
- Logs to `org_audit_logs`: action="invite_member"
- Sends email asynchronously (doesn't block response)
- Returns invitation_id

**Database:**
```sql
INSERT INTO org_invitations
(id, org_id, email, role, token, expires_at, status, invited_by, created_at)
VALUES
('invite-uuid', 'org-123', 'newuser@example.com', 'analyst',
 'token-uuid', '2026-03-30T12:00:00Z', 'pending', 'admin-uuid', NOW());
```

### Step 2: Email Sent to User

Email service (Resend) sends HTML email with:

```
Subject: You're invited to FairMind - Acme Corp

You've been invited to join Acme Corp on FairMind.

Organization: Acme Corp
Role: Analyst
Invited by: alice@example.com

Accept Invitation: https://app.fairmind.io/invitations/token-uuid?email=newuser@example.com

This invitation expires on: 2026-03-30

---

If you don't have a FairMind account yet, you'll be asked to create one.
```

**Link format:**
```
https://app.fairmind.io/invitations/{token}?email={email}
```

### Step 3: Unauthenticated User Clicks Link

User clicks the email link. Frontend calls:

```bash
GET /api/v1/invitations/token-uuid
```

**Backend Response (200 OK):**
```json
{
  "org_id": "org-123",
  "org_name": "Acme Corp",
  "email": "newuser@example.com",
  "role": "analyst",
  "created_at": "2026-03-22T12:00:00Z",
  "expires_at": "2026-03-30T12:00:00Z"
}
```

**Frontend displays:**
```
Acme Corp is inviting you to join

Role: Analyst

[Create Account] or [Log In]
```

### Step 4: User Authenticates (OAuth2)

Frontend redirects to Authentik OAuth2 login:

```
https://auth.fairmind.io/application/o/authorize/?
  client_id=fairmind-frontend
  redirect_uri=https://app.fairmind.io/invitations/token-uuid/callback
  response_type=code
  scope=openid+profile+email
```

**User:**
- Creates account OR logs in
- Authentik validates credentials
- Authenticates and redirects back with auth code

**Frontend:**
- Exchanges auth code for JWT
- Stores JWT in HttpOnly cookie
- Redirects to `/invitations/token-uuid`

### Step 5: Authenticated User Accepts Invitation

Frontend calls with authenticated JWT:

```bash
POST /api/v1/invitations/token-uuid/accept

Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
```

**Backend:**
1. Validate JWT (extract user_id, email)
2. Fetch invitation by token
3. Verify invitation exists, not expired, status="pending"
4. Verify invitation email matches JWT email
5. Create `org_members` record
6. Update `users.org_id` = org-123
7. Update `users.primary_org_id` = org-123 (if null)
8. Update invitation: status="accepted", accepted_at=NOW()
9. Log to `org_audit_logs`: action="member_accepted_invitation"

**Database:**
```sql
-- Insert org member
INSERT INTO org_members
(id, org_id, user_id, role, status, invited_by, joined_at, created_at)
VALUES
('member-uuid', 'org-123', 'user-uuid', 'analyst', 'active',
 'admin-uuid', NOW(), NOW());

-- Update user
UPDATE users SET org_id = 'org-123', primary_org_id = 'org-123'
WHERE id = 'user-uuid';

-- Update invitation
UPDATE org_invitations SET status = 'accepted', accepted_at = NOW()
WHERE token = 'token-uuid';

-- Audit log
INSERT INTO org_audit_logs
(org_id, user_id, action, resource_type, resource_id, status, created_at)
VALUES
('org-123', 'user-uuid', 'member_accepted_invitation',
 'organization_member', 'member-uuid', 'success', NOW());
```

### Step 6: Backend Response (201 Created)

```json
{
  "success": true,
  "org_id": "org-123",
  "org_name": "Acme Corp",
  "user_id": "user-uuid",
  "role": "analyst",
  "message": "You have been added to Acme Corp"
}
```

### Step 7: Frontend Redirects to Dashboard

Frontend redirects to dashboard with organization context:

```javascript
// Frontend gets response
const response = await acceptInvitation(token);

// Store org context
localStorage.setItem("org_id", response.org_id);
localStorage.setItem("org_name", response.org_name);

// Redirect to dashboard
router.push(`/organizations/${response.org_id}/dashboard`);
```

---

## Security Model

### JWT Tokens

FairMind uses RS256 JWT tokens issued by Authentik:

```
Header:
{
  "alg": "RS256",
  "kid": "key-id-from-authentik",
  "typ": "JWT"
}

Payload:
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "email_verified": true,
  "name": "User Name",
  "given_name": "User",
  "family_name": "Name",
  "iat": 1710978000,
  "exp": 1710981600,
  "iss": "https://auth.fairmind.io",
  "aud": "fairmind-frontend",
  "azp": "fairmind-frontend",
  "auth_time": 1710978000,
  "scope": "openid profile email",
  "roles": ["analyst"],
  "groups": []
}

Signature:
RSASHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  private_key_from_authentik
)
```

**Token Lifecycle:**
- **Issued:** At Authentik OAuth2 callback
- **Stored:** HttpOnly cookie (frontend)
- **Sent:** Authorization header on every API request
- **Verified:** Backend validates RS256 signature using Authentik's public key
- **Expires:** After 1 hour (configurable via settings.jwt_expire_minutes)
- **Refreshed:** Using refresh token (30-day validity)

**Security Properties:**
- **Signature verification:** Ensures token wasn't tampered with
- **Expiration:** Limits token lifetime, reduces impact of token theft
- **RS256:** Asymmetric signing, backend can't forge tokens
- **HttpOnly cookie:** Protects against XSS theft

### Authentik Integration

Authentik is the OAuth2 identity provider. It:

- Stores user credentials securely
- Validates email and password
- Issues signed JWT tokens
- Manages user attributes (name, email, roles)
- Provides OIDC endpoints for token exchange
- Maintains single sign-on session

**Connection Flow:**
```
FairMind Backend ←→ Authentik OAuth2 Server
   (validates token)      (issues token, manages identity)
```

### Email Verification

On invitation acceptance:

1. Backend verifies JWT email matches invitation email
2. Only allows acceptance if emails match
3. Prevents "token hijacking" (stealing someone's invitation)

```python
if invitation["email"] != current_user.email:
    raise HTTPException(403, "Invitation email doesn't match your account")
```

### Audit Trail for Compliance

All sensitive actions logged immutably:

```sql
-- Example audit log entry
INSERT INTO org_audit_logs VALUES (
  id: 'log-uuid',
  org_id: 'org-123',
  user_id: 'user-uuid',
  action: 'remove_member',
  resource_type: 'member',
  resource_id: 'member-uuid-removed',
  changes: {"removed_user_id": "user-uuid-old"},
  status: 'success',
  error_message: null,
  ip_address: '192.168.1.1',
  user_agent: 'Mozilla/5.0...',
  created_at: '2026-03-22T10:30:00Z'
);
```

**Immutability:** Timestamps are set by database, cannot be modified later

### Rate Limiting (Optional Per Endpoint)

Prevent brute force attacks:

```python
@router.post("/auth/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
async def login(email: str, password: str):
    ...
```

### No Hardcoded Credentials

**FORBIDDEN:**
```python
# ❌ WRONG - Never do this!
db_password = "production-password-123"
api_key = "sk_live_abc123xyz"
org_id = "org-12345"
```

**CORRECT:**
```python
# ✓ Correct - Use environment variables
from config.settings import settings
db_password = settings.database_password  # From .env
api_key = settings.resend_api_key  # From .env
org_id = org_id  # From request parameter
```

---

## Compliance & Audit

### Audit Log Requirements

NITI Aayog, RBI, DPDP Act, and GDPR all require auditability:

**Logged Actions:**
- User registration
- User login
- Organization creation/deletion
- Member invitation
- Member acceptance
- Member role change
- Member removal
- Role creation/modification
- Report generation/export
- Dataset upload/deletion
- All permission denials

**Logged Details:**
- **Who:** user_id, email
- **What:** action name
- **When:** timestamp (immutable)
- **Where:** org_id, resource_id
- **How:** ip_address, user_agent
- **Status:** success or failure
- **Error:** error_message if failed

### Audit Log Schema

```sql
CREATE TABLE org_audit_logs (
  id UUID PRIMARY KEY,
  org_id UUID NOT NULL,         -- Which organization
  user_id UUID,                 -- Who did it
  action VARCHAR(255),          -- What action
  resource_type VARCHAR(255),   -- What was affected
  resource_id VARCHAR(255),     -- ID of resource
  changes JSONB,                -- What changed
  status VARCHAR(50),           -- success/failure
  error_message TEXT,           -- Why it failed
  ip_address VARCHAR(45),       -- Source IP
  user_agent TEXT,              -- Client info
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Immutable
);

-- Indexes for fast audit queries
CREATE INDEX idx_audit_org_id ON org_audit_logs(org_id);
CREATE INDEX idx_audit_user_id ON org_audit_logs(user_id);
CREATE INDEX idx_audit_action ON org_audit_logs(action);
CREATE INDEX idx_audit_timestamp ON org_audit_logs(created_at DESC);
```

### Data Retention

**Default Policy:**
- Keep all audit logs indefinitely (append-only)
- No deletion of audit logs
- Regular backups (external storage)
- Quarterly compliance reviews

**Optional:** Organizations can define retention policies:
- Keep 7 years (DPDP Act, EU AI Act)
- Export on demand (CSV, JSON, PDF)
- Anonymization of old logs (optional)

### Privacy Considerations

**Users CANNOT:**
- See other organizations' audit logs
- Delete or modify their own audit entries
- Export logs without admin approval

**Only org admins can:**
- View audit logs
- Export logs for compliance review
- Generate audit reports

---

## Deployment Checklist

Use this checklist when deploying FairMind RBAC to production.

### Prerequisites

- [ ] Authentik instance running and configured
  - [ ] OAuth2 application created (`fairmind-frontend`)
  - [ ] OAuth2 application created (`fairmind-backend`)
  - [ ] Public key accessible at `/.well-known/openid-configuration`

- [ ] Neon PostgreSQL database created
  - [ ] Network access configured (allow app IPs)
  - [ ] Connection string available

- [ ] Resend email API account created
  - [ ] API key generated and stored securely
  - [ ] Sender domain verified

### Environment Variables

Set these in `.env` or deployment configuration:

```bash
# Authentik
AUTHENTIK_URL=https://auth.fairmind.io
AUTHENTIK_CLIENT_ID=fairmind-backend
AUTHENTIK_CLIENT_SECRET=...from authentik...
JWT_PUBLIC_KEY=...RSA public key...
JWT_ALGORITHM=RS256
JWT_EXPIRE_MINUTES=60

# Database
DATABASE_URL=postgresql://user:password@host:5432/fairmind
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Email
RESEND_API_KEY=...from resend...
RESEND_SENDER_EMAIL=noreply@fairmind.io

# Application
API_BASE_URL=https://api.fairmind.io
FRONTEND_URL=https://app.fairmind.io
LOG_LEVEL=INFO
```

### Database Migration

Run the RBAC schema migration:

```bash
# From project root
cd apps/backend

# Using uv (FairMind's package manager)
uv run python -m alembic upgrade head

# OR: Direct SQL execution
psql postgresql://user:password@host:5432/fairmind < migrations/007_rbac_schema.sql
```

**Schema created:**
- `organizations` table
- `org_members` table
- `org_roles` table
- `org_invitations` table
- `org_audit_logs` table
- `users` table (updated)
- All required indexes

### Backend Service Startup

```bash
cd apps/backend

# Development
uv run fastapi dev api/main.py

# Production (with Gunicorn)
uv run gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  api.main:app
```

**Verify startup:**
```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status": "ok"}
```

### Frontend Service Startup

```bash
cd apps/frontend

# Development
npm run dev

# Production build
npm run build
npm run start

# Docker
docker build -t fairmind-frontend .
docker run -p 3000:3000 fairmind-frontend
```

### Verification Checklist

Run these tests to verify deployment:

- [ ] **Health Check:**
  ```bash
  curl https://api.fairmind.io/api/v1/health
  # Response: {"status": "ok"}
  ```

- [ ] **JWT Validation:**
  ```bash
  # Get token from Authentik OAuth2 login
  # Verify token is valid and contains correct claims
  ```

- [ ] **Organization Creation:**
  ```bash
  curl -X POST https://api.fairmind.io/api/v1/organizations \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"name": "Test Org"}'
  # Response: 201 Created with org_id
  ```

- [ ] **Member Invitation:**
  ```bash
  curl -X POST https://api.fairmind.io/api/v1/organizations/{org_id}/members/invite \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"email": "test@example.com", "role": "analyst"}'
  # Response: 201 Created with invitation_id
  ```

- [ ] **Audit Logging:**
  ```bash
  curl https://api.fairmind.io/api/v1/organizations/{org_id}/audit-logs \
    -H "Authorization: Bearer $TOKEN"
  # Response: 200 OK with audit log entries
  ```

- [ ] **Email Sending:**
  - Check email arrives in invitee's inbox
  - Verify link contains correct token
  - Verify expiration is 7 days

### Monitoring & Logging

**Metrics to monitor:**
- API response times (target: <200ms p99)
- Database connection pool utilization
- Email delivery success rate
- 403 Forbidden responses (failed authorizations)
- 401 Unauthorized responses (invalid tokens)
- Audit log volume (should grow steadily)

**Log files to watch:**
```bash
# Application logs
tail -f logs/fairmind-api.log | grep -E "ERROR|WARNING"

# Audit trail (check for security issues)
tail -f logs/audit.log

# Database queries (slow query logs)
# Set log_min_duration_statement = 1000ms in PostgreSQL
```

### Troubleshooting

**Problem:** 401 Unauthorized on every request

**Solution:**
- Verify JWT_PUBLIC_KEY is correct (from Authentik)
- Check token expiration (default: 1 hour)
- Verify Authentik is running and accessible
- Check database connectivity

**Problem:** 403 Forbidden on organization endpoints

**Solution:**
- Verify user is member of organization
- Check org_members table has user_id + org_id + role
- Verify role is admin/owner if calling admin endpoints
- Check audit logs for failed authorization attempts

**Problem:** Invitations not being sent

**Solution:**
- Verify RESEND_API_KEY is set correctly
- Check Resend API status page
- Review invitation creation (should be in org_invitations)
- Check application logs for email service errors
- Verify sender email is verified in Resend

**Problem:** Database connection timeouts

**Solution:**
- Increase DATABASE_POOL_SIZE
- Check database host accessibility
- Verify database credentials
- Monitor database load (CPU, connections)
- Consider adding read replicas if needed

---

## Additional Resources

- [API Reference](API_REFERENCE.md) — Detailed endpoint documentation
- [Permission System](PERMISSION_SYSTEM.md) — How permissions work
- [Deployment Guide](DEPLOYMENT_GUIDE.md) — Production deployment steps
- [Operations Guide](OPERATIONS_GUIDE.md) — Monitoring and maintenance
- [FAQ](FAQ.md) — Common questions and answers

---

**Document Version:** 1.0
**Last Updated:** March 2026
**Maintained By:** FairMind Engineering
