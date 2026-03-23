# FairMind RBAC Documentation Index

**Version:** 1.0
**Last Updated:** March 2026
**Total Documentation:** 7,500+ words

---

## Quick Links

### For Developers
- **[RBAC Implementation Guide](RBAC_IMPLEMENTATION_GUIDE.md)** — Complete RBAC architecture, concepts, and implementation
- **[API Reference](API_REFERENCE.md)** — Detailed endpoint documentation with examples
- **[Permission System](PERMISSION_SYSTEM.md)** — Roles, permissions, and decorators

### For DevOps/Operations
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** — Production deployment, setup, verification
- **[Operations Guide](OPERATIONS_GUIDE.md)** — Monitoring, maintenance, incident response

### For Everyone
- **[FAQ](FAQ.md)** — Common questions and answers

---

## Documentation by Use Case

### "I'm implementing RBAC in the backend"
1. Read: [RBAC Implementation Guide](RBAC_IMPLEMENTATION_GUIDE.md)
2. Reference: [API Reference](API_REFERENCE.md)
3. Learn: [Permission System](PERMISSION_SYSTEM.md)

### "I need to deploy FairMind to production"
1. Read: [Deployment Guide](DEPLOYMENT_GUIDE.md)
2. Reference: [Operations Guide](OPERATIONS_GUIDE.md)
3. Check: Deployment Checklist in Deployment Guide

### "I'm building the frontend integration"
1. Read: [API Reference](API_REFERENCE.md) (endpoints section)
2. Learn: [Invitation Flow](RBAC_IMPLEMENTATION_GUIDE.md#invitation-flow)
3. Reference: [Permission System](PERMISSION_SYSTEM.md) (for UI logic)

### "I need to monitor FairMind in production"
1. Read: [Operations Guide](OPERATIONS_GUIDE.md) (monitoring section)
2. Reference: [Troubleshooting](DEPLOYMENT_GUIDE.md#troubleshooting)
3. Check: [Incident Response](OPERATIONS_GUIDE.md#incident-response)

### "I'm managing an organization in FairMind"
1. Read: [FAQ](FAQ.md)
2. Reference: [Permission System](PERMISSION_SYSTEM.md) (roles and permissions)
3. Learn: [Invitation Flow](RBAC_IMPLEMENTATION_GUIDE.md#invitation-flow)

### "I need compliance documentation"
1. Read: [Compliance & Audit](RBAC_IMPLEMENTATION_GUIDE.md#compliance--audit)
2. Reference: [FAQ - Compliance](FAQ.md#compliance-questions)
3. Check: Audit log export in API Reference

---

## Documentation by Document

### RBAC Implementation Guide (2,500+ words)
**Purpose:** Complete architectural overview and implementation reference

**Sections:**
1. Overview — What is RBAC, why needed
2. Key Concepts — Organizations, users, roles, permissions, audit logs
3. User Roles & Permissions — Global and organization roles
4. API Endpoints Reference — 7 org management + 3 auth + 1 compliance endpoint
5. Permission Decorators — @require_org_admin, @require_permission, etc.
6. Multi-Tenancy Architecture — 5 enforcement layers
7. Invitation Flow — 7-step email-based onboarding
8. Security Model — JWT, Authentik, audit trails
9. Compliance & Audit — Requirements and implementation
10. Deployment Checklist — Pre-deployment verification

**Best for:** Understanding complete system, implementation decisions, architecture

**Key Content:**
- ASCII architecture diagram
- Permission matrix
- Database schema descriptions
- Complete endpoint specifications
- Decorator usage patterns

---

### API Reference (1,500+ words)
**Purpose:** Complete REST API documentation

**Sections:**
1. Authentication — JWT token usage
2. Organization Management (7 endpoints)
   - List members
   - Invite member
   - Update member
   - Remove member
   - List roles
   - Create custom role
   - List audit logs
3. Authentication (3 endpoints)
   - Register
   - Login
   - Accept invitation
4. Compliance Endpoint — Audit report generation
5. Invitation Management — Public access to invitation details
6. Response Formats — Success/error response structures
7. Pagination — Limit/skip parameters
8. Rate Limiting — Default limits and handling
9. Code Examples — Python, JavaScript, cURL

**Best for:** API integration, endpoint reference, examples

**Key Content:**
- Detailed endpoint specifications
- Request/response examples
- Error responses with HTTP status codes
- Parameter descriptions and types
- Example code in 3 languages
- cURL examples for all endpoints

---

### Permission System Guide (1,000+ words)
**Purpose:** Roles, permissions, and fine-grained access control

**Sections:**
1. Overview — Two-level permission system
2. Built-in Roles — owner, admin, member, analyst, viewer
3. Custom Roles — Creating and managing
4. Permission Matrix — Role → Action reference
5. Decorator Usage — Code examples for each decorator
6. Testing Permissions — Manual, unit, and integration tests
7. Permission Errors — Common 403/401 issues and solutions
8. Best Practices — Security and design patterns

**Best for:** Understanding permissions, creating custom roles, testing

**Key Content:**
- Complete role definitions
- Permission string format
- Decorator examples
- Test code examples
- Python/pytest patterns

---

### Deployment Guide (1,500+ words)
**Purpose:** Production deployment, setup, and verification

**Sections:**
1. Prerequisites — Authentik, PostgreSQL, Resend, tools
2. Environment Setup — Backend and frontend env vars
3. Database Migration — Schema creation and verification
4. Service Startup — Development and production
5. Verification — Health checks, tests, complete checklist
6. Troubleshooting — Common issues and solutions
7. Post-Deployment — Monitoring, logging, backups

**Best for:** Setting up production, troubleshooting, verification

**Key Content:**
- Environment variable templates
- Database setup commands
- Service startup scripts
- Complete verification test suite
- Troubleshooting guide for common issues
- Post-deployment checklist

---

### Operations Guide (1,000+ words)
**Purpose:** Production monitoring, maintenance, and incident response

**Sections:**
1. Monitoring — Key metrics, Prometheus config, dashboards
2. Maintenance — Daily, weekly, monthly tasks
3. Backup Strategy — Daily backups, disaster recovery
4. Incident Response — Common incidents and solutions
5. Performance Tuning — Database and application optimization
6. Scaling — Horizontal and vertical scaling strategies

**Best for:** Production operations, incident response, monitoring

**Key Content:**
- Monitoring metrics and alerts
- SQL maintenance queries
- Backup scripts
- Incident runbooks
- Performance tuning examples
- Auto-scaling configuration

---

### FAQ (500+ words)
**Purpose:** Common questions and quick answers

**Categories:**
1. User Questions — How to use RBAC features
2. Admin Questions — How to manage organizations
3. Permission Questions — Understanding permissions
4. Technical Questions — How RBAC works
5. Compliance Questions — Regulatory requirements
6. Integration Questions — Connecting with other systems
7. Support & Troubleshooting — Getting help

**Best for:** Quick answers, troubleshooting, getting started

**Key Content:**
- Question → Answer format
- Links to detailed documentation
- Step-by-step instructions
- Technical explanations
- Compliance information

---

## How to Read This Documentation

### If you have 15 minutes
Read: [FAQ](FAQ.md) — Get answers to common questions

### If you have 30 minutes
Read: [API Reference](API_REFERENCE.md) — Understand available endpoints

### If you have 1 hour
Read: [RBAC Implementation Guide](RBAC_IMPLEMENTATION_GUIDE.md) — Complete overview

### If you have 2+ hours
Read all documents in order:
1. RBAC Implementation Guide
2. API Reference
3. Permission System
4. Deployment Guide
5. Operations Guide
6. FAQ

---

## Key Concepts Summary

### Organizations
Multi-tenant boundaries. Each org has:
- Members with assigned roles
- Custom roles
- Audit logs
- Settings

### Users
Global accounts that:
- Belong to multiple organizations
- Have different roles in different orgs
- Have primary organization context

### Roles
Two types:
- **System roles** (global): admin, analyst, viewer
- **Organization roles**: owner, admin, member, analyst, custom

### Permissions
Format: `resource:action` (e.g., `members:invite`)

Controlled by:
- Decorators (@require_org_admin, @require_permission)
- Permission matrix (role → permissions)
- Custom role definitions

### Audit Logs
Immutable history of all actions:
- Who performed action
- What action (invite, remove, etc.)
- When it occurred
- What changed
- If it succeeded or failed

### Invitations
Email-based onboarding:
- 7-day expiration
- Unique token per invite
- Email verification on acceptance
- Audit logged

---

## Cross-References

### Topics mentioned across documents

**JWT / Authentication:**
- Overview: [Implementation Guide - Security Model](RBAC_IMPLEMENTATION_GUIDE.md#security-model)
- API: [API Reference - Authentication](API_REFERENCE.md#authentication)
- Troubleshooting: [Deployment Guide - JWT Validation Fails](DEPLOYMENT_GUIDE.md#jwt-validation-fails)

**Multi-Tenancy:**
- Architecture: [Implementation Guide - Multi-Tenancy](RBAC_IMPLEMENTATION_GUIDE.md#multi-tenancy-architecture)
- Security: [Implementation Guide - 5 Enforcement Layers](RBAC_IMPLEMENTATION_GUIDE.md#layer-1-middleware---organization-context-extraction)

**Audit Logs:**
- Overview: [Implementation Guide - Audit Logs](RBAC_IMPLEMENTATION_GUIDE.md#audit-logs)
- Compliance: [Implementation Guide - Compliance](RBAC_IMPLEMENTATION_GUIDE.md#compliance--audit)
- API: [API Reference - List Audit Logs](API_REFERENCE.md#list-organization-audit-logs)
- Operations: [Operations Guide - Maintenance](OPERATIONS_GUIDE.md#maintenance)

**Invitations:**
- Overview: [Implementation Guide - Invitations](RBAC_IMPLEMENTATION_GUIDE.md#invitations)
- Flow: [Implementation Guide - Invitation Flow](RBAC_IMPLEMENTATION_GUIDE.md#invitation-flow)
- API: [API Reference - Invitation Endpoints](API_REFERENCE.md#invitation-management)
- FAQ: [FAQ - Invitations](FAQ.md#how-do-i-invite-a-user-to-my-organization)

**Roles & Permissions:**
- Overview: [Implementation Guide - User Roles](RBAC_IMPLEMENTATION_GUIDE.md#user-roles--permissions)
- System: [Permission System Guide](PERMISSION_SYSTEM.md)
- API: [API Reference - Role Endpoints](API_REFERENCE.md)
- FAQ: [FAQ - Permissions](FAQ.md#permission-questions)

---

## Document Maintenance

### When to Update Documentation

**Update RBAC Implementation Guide when:**
- Architecture changes
- New decorators added
- Database schema changes
- New concepts introduced

**Update API Reference when:**
- Endpoints added/changed
- Response format changes
- Error codes change
- New parameters added

**Update Permission System when:**
- New roles created
- Permissions change
- Decorator behavior changes

**Update Deployment Guide when:**
- Prerequisites change
- Environment variables change
- New services needed
- Setup procedures change

**Update Operations Guide when:**
- Monitoring metrics change
- Maintenance procedures change
- Incident patterns identified
- Performance optimization found

**Update FAQ when:**
- New questions from users
- Clarifications needed
- Links need updating

---

## Contributing to Documentation

When making changes to RBAC:

1. **Update relevant documentation**
   - Code changes → Update API Reference and/or Implementation Guide
   - New features → Add to FAQ
   - Procedures → Update Deployment or Operations Guide

2. **Test with examples**
   - Include working code examples
   - Include cURL examples
   - Test all examples before committing

3. **Update version dates**
   - Change "Last Updated" date
   - Update version number if major change

4. **Cross-reference**
   - Link related sections
   - Update this index if needed

---

## Document Statistics

| Document | Words | Sections | Examples |
|----------|-------|----------|----------|
| RBAC Implementation Guide | 2,500+ | 10 | 15+ |
| API Reference | 1,500+ | 9 | 20+ |
| Permission System | 1,000+ | 8 | 10+ |
| Deployment Guide | 1,500+ | 7 | 25+ |
| Operations Guide | 1,000+ | 6 | 15+ |
| FAQ | 500+ | 7 | 30+ |
| **Total** | **7,500+** | **47** | **115+** |

---

## Related Resources

- **Codebase:** `/apps/backend/src/api/routers/org_management.py`
- **Database:** `migrations/007_rbac_schema.sql`
- **Decorators:** `/apps/backend/core/decorators/org_permissions.py`
- **Tests:** `/apps/backend/tests/test_org_management.py`
- **Frontend:** `/apps/frontend/src/lib/api/endpoints.ts`

---

## Quick Reference

### API Endpoints (Quick)
```
GET    /api/v1/organizations/{org_id}/members
POST   /api/v1/organizations/{org_id}/members/invite
PUT    /api/v1/organizations/{org_id}/members/{member_id}
DELETE /api/v1/organizations/{org_id}/members/{member_id}
GET    /api/v1/organizations/{org_id}/roles
POST   /api/v1/organizations/{org_id}/roles
GET    /api/v1/organizations/{org_id}/audit-logs

POST   /api/v1/auth/register
POST   /api/v1/auth/login
GET    /api/v1/invitations/{token}
POST   /api/v1/invitations/{token}/accept
```

### Permission Decorators (Quick)
```python
@require_org_owner              # Only owner
@require_org_admin              # Admin or owner
@require_org_member             # Any member
@require_permission("res:act")  # Specific permission
@require_permissions([...])     # Multiple permissions
@audit_org_action("act", "res") # Log action
```

### Environment Variables (Quick)
```bash
# Authentik
AUTHENTIK_URL
JWT_PUBLIC_KEY
JWT_ALGORITHM=RS256

# Database
DATABASE_URL
DATABASE_POOL_SIZE=20

# Email
RESEND_API_KEY
RESEND_SENDER_EMAIL

# Application
API_BASE_URL
FRONTEND_URL
```

---

**Documentation Version:** 1.0
**Last Updated:** March 2026
**Maintained By:** FairMind Engineering Team
