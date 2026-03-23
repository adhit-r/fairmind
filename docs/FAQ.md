# FairMind RBAC FAQ

**Frequently Asked Questions about Role-Based Access Control**

---

## User Questions

### How do I invite a user to my organization?

**Answer:**

1. Log in to FairMind as organization admin
2. Go to **Settings → Members**
3. Click **Invite Member**
4. Enter email address and select role
5. Click **Send Invitation**

The user will receive an email with:
- Organization name
- Invited role
- Link to accept invitation (valid for 7 days)

**Via API:**
```bash
curl -X POST https://api.fairmind.io/api/v1/organizations/{org_id}/members/invite \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"email":"user@example.com","role":"analyst"}'
```

---

### Can users belong to multiple organizations?

**Answer:** Yes! Users can:
- Join multiple organizations via separate invitations
- Have different roles in different organizations
- Switch between organizations in the UI
- Have different permissions in each organization

**Example:**
- Alice is **admin** in Organization A
- Alice is **analyst** in Organization B
- Alice is **member** in Organization C

When Alice logs in, she sees all three organizations and can switch contexts.

**How to manage:**
- Each org has separate member list
- Roles are per-organization
- Permissions don't transfer between orgs

---

### How do I create custom roles?

**Answer:** Only organization admins can create custom roles.

1. Log in as organization admin
2. Go to **Settings → Roles**
3. Click **Create Role**
4. Enter:
   - **Name:** Unique role name (e.g., "Compliance Officer")
   - **Description:** What the role does
   - **Permissions:** Select permissions this role has
5. Click **Create**

**Example custom roles:**
- Compliance Officer: Can view reports and audit logs
- Data Analyst: Can view datasets and generate reports
- Finance Auditor: Can view reports and export data

**Via API:**
```bash
curl -X POST https://api.fairmind.io/api/v1/organizations/{org_id}/roles \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name":"Compliance Officer",
    "description":"Manages compliance reports",
    "permissions":["reports:view","reports:export","audit:view"]
  }'
```

---

### What happens if an invitation expires?

**Answer:** If a user doesn't accept within 7 days:

1. The invitation **expires automatically**
2. Email link no longer works
3. User needs a new invitation sent
4. Admin must invite again with new link

**Note:** Expired invitations remain in system for audit trail.

---

### Can I accept an invitation without logging in?

**Answer:** No, you must be logged into FairMind to accept an invitation.

**Flow:**
1. User clicks email link (no login required to view)
2. Can see organization name and role
3. Redirected to login if not authenticated
4. After login, can accept invitation

This protects against email forwarding/delegation.

---

### Can users delete their own account?

**Answer:** Users can:
- Leave an organization (remove themselves as member)
- Deactivate their FairMind account (contact support)
- Cannot delete their account without company policy approval

**Organization admins can:**
- Remove users from organization
- Deactivate user accounts
- Cannot delete user's global FairMind account

**Note:** Audit logs show all user actions - deleting users doesn't erase history.

---

### How long are audit logs kept?

**Answer:** FairMind keeps **all audit logs indefinitely** by default.

**Policy:**
- Logs are append-only (cannot be modified)
- Never deleted unless organization requests
- Stored in database + backups
- Compliant with NITI Aayog, DPDP Act, GDPR requirements

**Organizations can:**
- Request data export (CSV, JSON, PDF)
- Request log deletion per compliance policy
- Set retention policies (e.g., keep 7 years)

---

### Can I export compliance reports?

**Answer:** Yes! Organization admins can export audit reports:

1. Go to **Audit → Export**
2. Select date range
3. Choose format (CSV, JSON, PDF)
4. Download report

**Report includes:**
- Who performed each action
- When action occurred
- What was changed
- Success/failure status
- IP address of user

**Via API:**
```bash
curl -X GET https://api.fairmind.io/api/v1/organizations/{org_id}/compliance/audit-report \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/pdf"
```

---

## Admin Questions

### How do I change a user's role?

**Answer:**

1. Go to **Settings → Members**
2. Find the member
3. Click **Edit**
4. Select new role
5. Click **Update**

**Restrictions:**
- Cannot promote/demote yourself
- Cannot remove last admin (org needs ≥1 admin)
- Cannot change owner role

**Via API:**
```bash
curl -X PUT https://api.fairmind.io/api/v1/organizations/{org_id}/members/{member_id} \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"role":"admin"}'
```

---

### How do I remove a user from my organization?

**Answer:**

1. Go to **Settings → Members**
2. Find the member
3. Click **Remove**
4. Confirm removal

**What happens:**
- Member removed from organization
- Member loses access to org data
- Member can be re-invited later
- Audit log shows removal

**Restrictions:**
- Cannot remove organization owner
- Cannot remove last admin
- Cannot remove yourself

**Note:** Member's global FairMind account still exists - they can join other organizations.

---

### What's the difference between owner and admin?

**Answer:**

| Action | Owner | Admin |
|--------|-------|-------|
| Manage members (invite/remove) | ✓ | ✓ |
| Change member roles | ✓ | ✓ |
| Create custom roles | ✓ | ✓ |
| View audit logs | ✓ | ✓ |
| Delete organization | ✓ | ✗ |
| Transfer ownership | ✓ | ✗ |

**Owner is for:**
- Organization founder
- Business decision maker
- Sensitive operations (deletion)

**Admin is for:**
- Day-to-day member management
- Team lead level access

---

### Can I have multiple owners?

**Answer:** Currently, each organization has **one owner**.

If owner leaves company:
1. Owner can transfer ownership to another member
2. Contact support for transfer

**Future feature:** Multiple owners may be supported in later versions.

---

### How do I see what actions a user took?

**Answer:** Check the audit log:

1. Go to **Audit Logs**
2. Filter by user name
3. See all actions they performed with timestamps

**Information shown:**
- Action (invite_member, remove_member, etc.)
- What was changed
- When it occurred
- If it succeeded or failed

---

### How do I deactivate a user without removing them?

**Answer:** Use **Deactivate** instead of **Remove**:

1. Go to **Settings → Members**
2. Click **Actions → Deactivate**
3. User's access suspended, but not removed

**Difference:**
- **Deactivate:** User still in member list, cannot access
- **Remove:** User removed from organization entirely

---

## Permission Questions

### What permissions do different roles have?

**Answer:** See [PERMISSION_SYSTEM.md](PERMISSION_SYSTEM.md) for complete permission matrix.

**Quick summary:**
- **Owner:** All permissions
- **Admin:** All except delete organization
- **Member:** View and contribute
- **Analyst:** View and analyze (read-only mostly)
- **Viewer:** View dashboards only

---

### Can I create a role with specific permissions?

**Answer:** Yes! Custom roles let you choose any permissions:

```json
{
  "name": "Report Manager",
  "permissions": [
    "reports:view",
    "reports:generate",
    "reports:export"
  ]
}
```

You can assign any combination of permissions to match your needs.

---

### What's the difference between "report:view" and "report:generate"?

**Answer:**
- **reports:view** - Can see existing reports
- **reports:generate** - Can create new reports
- **reports:export** - Can download/export reports

A user with only "reports:view" is read-only. With "reports:generate" they can create new reports.

---

## Technical Questions

### How does FairMind prevent unauthorized access to other organizations' data?

**Answer:** FairMind uses 5 layers of protection:

1. **Middleware** - Verifies JWT and extracts org_id
2. **Decorators** - Checks user is member of org before endpoint executes
3. **Query Filtering** - All queries include `WHERE org_id = :org_id`
4. **Row Level Security** - Database enforces org isolation
5. **Audit Logging** - Failed access attempts logged

Even if code has a bug, RLS policies prevent data leakage.

---

### How are authentication tokens stored and sent?

**Answer:**
1. **Generated by:** Authentik OAuth2 server
2. **Format:** JWT (RS256 signed)
3. **Stored:** HttpOnly cookie (frontend only)
4. **Sent:** Authorization header on each request
5. **Verified:** Backend checks RS256 signature
6. **Expires:** After 1 hour (configurable)

**Security:**
- HttpOnly: Prevents JavaScript theft (XSS protection)
- RS256: Cannot be forged by backend
- Expiration: Limits window of compromise

---

### What happens if someone steals a JWT token?

**Answer:** Token is valid until expiration (1 hour by default).

**Attacker can:**
- Perform actions as that user
- Access same organizations as user
- View user's data

**FairMind protects:**
- Logs all actions with IP address
- You'll see actions from wrong IP in audit logs
- Can immediately revoke token by logging out
- Admin can deactivate account

**Prevention:**
- Keep tokens in HttpOnly cookies
- Use HTTPS (token in transit)
- Rotate tokens regularly
- Monitor audit logs for suspicious activity

---

### How is email verified when accepting invitations?

**Answer:** Email is verified by matching:

1. **Invitation email:** From invitation record in database
2. **User email:** From JWT after they log in
3. **Match required:** Must be identical to proceed

This prevents "invitation hijacking" where someone forwards the email link to a different person.

**Example:**
- Admin invites: alice@example.com
- Alice logs in with: alice@example.com ✓ (accepted)
- Email forwarded to: bob@example.com ✗ (rejected - email mismatch)

---

### Where are audit logs stored?

**Answer:** Audit logs are stored in PostgreSQL database table `org_audit_logs`:

```sql
org_audit_logs
├── id (UUID) - unique log entry
├── org_id - which organization
├── user_id - who performed action
├── action - what action (invite_member, etc)
├── resource_type - what was affected
├── resource_id - ID of affected resource
├── changes - what changed
├── status - success/failure
├── error_message - reason if failed
├── ip_address - source IP (forensics)
├── user_agent - browser info
└── created_at - immutable timestamp
```

**Properties:**
- Append-only (cannot modify existing logs)
- Immutable timestamps
- Indexed for fast queries
- Backed up daily
- Never deleted (compliance requirement)

---

## Compliance Questions

### Is FairMind compliant with DPDP Act?

**Answer:** Yes, FairMind supports DPDP Act compliance:

**FairMind features:**
- User consent tracking (via invitations)
- Audit logs show all data access
- Data access control (RBAC)
- User data export (right to data)
- User removal (right to be forgotten)
- Transparent permissions

**Organization must:**
- Define data handling policy
- Use FairMind audit logs for proof
- Document consent for each user
- Export data when requested
- Delete user data when requested

---

### Is FairMind GDPR compliant?

**Answer:** FairMind provides tools for GDPR compliance:

**FairMind features:**
- Access control (only authorized users see data)
- Audit logs (proof of data access)
- User data deletion (right to be forgotten)
- Data export (data portability)
- Consent tracking

**Organization must:**
- Use FairMind with GDPR-compliant practices
- Maintain Data Processing Agreement
- Document data processing
- Conduct impact assessments
- Report data breaches

---

### How do I prove access control for audits?

**Answer:** Use FairMind audit logs:

1. Go to **Audit Logs**
2. Export to PDF/CSV
3. Shows:
   - Who accessed what
   - When they accessed it
   - What they did with it
   - Failure attempts

**Report includes:**
- User identification
- Action timestamps
- Resource accessed
- Status (success/failure)
- Source IP (forensics)

This proves to regulators that access is controlled.

---

## Integration Questions

### Can I integrate FairMind with my existing identity provider?

**Answer:** FairMind uses Authentik for identity management. Authentik supports:

- SAML (for corporate SSO)
- OIDC (for Google, Microsoft, GitHub)
- LDAP (for Active Directory)
- Database (email/password)

**Integration steps:**
1. Set up Authentik with your IdP
2. Configure OAuth2 application
3. Users log in via your corporate identity
4. FairMind permissions still apply per-organization

---

### How do I sync users from my directory?

**Answer:** Currently, users must:
1. Accept invitation email
2. Log in via Authentik OAuth2
3. Automatically added to FairMind on first login

**Future:** Automated user sync from LDAP/AD planned for Q3 2026.

---

### Can I use FairMind with my existing permission system?

**Answer:** Not directly, but you can:

1. **Map existing roles** to FairMind roles
2. **Create custom roles** matching your structure
3. **Assign permissions** to match your policies
4. **Use FairMind audit logs** alongside your system

Example: Your system has "DataOwner" role → Create custom FairMind role with equivalent permissions.

---

## Support & Troubleshooting

### I can't log in - what should I do?

**Answer:**
1. Verify you created FairMind account (OAuth2 signup)
2. Check email for typos
3. Try password reset
4. Clear browser cookies and try again
5. Check that Authentik is running
6. Contact support with error message

---

### I was invited but don't see the invitation email

**Answer:**
1. Check spam/junk folder
2. Ask admin to resend invitation
3. Verify email address is correct
4. Check email with exact address used in invitation

---

### I get "403 Forbidden" when trying to do something

**Answer:** You lack permission for that action.

**Check:**
1. Are you an **admin** or **owner**? Only they can invite/remove members
2. Do you have the required **permission** for custom roles?
3. Check your **role** in organization (**Settings → Members**)

**Solution:**
- Ask organization admin to upgrade your role
- Or ask admin to grant specific permissions

---

### An invitation has been pending for weeks - what happened?

**Answer:** Invitations expire after **7 days**. If not accepted:
1. Invitation is expired and invalid
2. Admin must send new invitation
3. User can use new link

---

### I want to delete my organization - how do I do that?

**Answer:** Only **organization owner** can delete organization:

1. Go to **Settings → Organization**
2. Click **Delete Organization**
3. Confirm by typing organization name
4. Organization and all data deleted (cannot undo!)

**Warning:** This is permanent and affects all members.

---

## Contact & Support

**For questions not answered here:**

**Email:** support@fairmind.io
**Documentation:** https://docs.fairmind.io
**Status Page:** https://status.fairmind.io
**GitHub Issues:** https://github.com/fairmind/fairmind/issues

---

**Last Updated:** March 2026
**Document Version:** 1.0
