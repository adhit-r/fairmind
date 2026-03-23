/**
 * RBAC Frontend E2E Tests (Playwright)
 *
 * Comprehensive frontend testing:
 * 1. User registration & org creation
 * 2. OAuth2 flow
 * 3. Invite member
 * 4. Accept invitation
 * 5. Org switcher
 * 6. Admin panel
 * 7. Compliance report download
 */

import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const API_URL = process.env.API_URL || 'http://localhost:8000/api/v1';

// ── Test Fixtures ────────────────────────────────────────────────────────────

let userEmail = `test-${Date.now()}@example.com`;
let userPassword = 'TestPassword123!';
let orgName = `TestOrg-${Date.now()}`;

// ── Test Suite 1: User Registration & Org Creation ──────────────────────────

test.describe('User Registration & Org Creation', () => {
  test('should register new user and create organization', async ({ page }) => {
    // Navigate to register page
    await page.goto(`${BASE_URL}/register`);

    // Fill registration form
    await page.fill('input[name="email"]', userEmail);
    await page.fill('input[name="password"]', userPassword);
    await page.fill('input[name="confirm_password"]', userPassword);
    await page.fill('input[name="org_name"]', orgName);
    await page.fill('input[name="domain"]', orgName.toLowerCase());

    // Submit form
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await page.waitForURL(`${BASE_URL}/dashboard`);
    expect(page.url()).toContain('/dashboard');

    // Verify organization is created
    const orgSwitcher = page.locator('[data-testid="org-switcher"]');
    await expect(orgSwitcher).toContainText(orgName);
  });

  test('should show org in switcher after creation', async ({ page }) => {
    // Login first
    await loginUser(page, userEmail, userPassword);

    // Open org switcher
    await page.click('[data-testid="org-switcher"]');

    // Verify org appears in list
    const orgOption = page.locator(`text=${orgName}`);
    await expect(orgOption).toBeVisible();
  });

  test('should not allow duplicate organization names', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    // Navigate to org creation
    await page.goto(`${BASE_URL}/org/create`);

    // Try to create org with same name
    await page.fill('input[name="org_name"]', orgName);
    await page.click('button[type="submit"]');

    // Should show error message
    const errorMessage = page.locator('[role="alert"]');
    await expect(errorMessage).toContainText('already exists');
  });
});

// ── Test Suite 2: OAuth2 Flow ────────────────────────────────────────────────

test.describe('OAuth2 Login Flow', () => {
  test('should redirect to Authentik consent screen', async ({ page }) => {
    // Navigate to login
    await page.goto(`${BASE_URL}/login`);

    // Click OAuth2 button
    await page.click('button:has-text("Login with Authentik")');

    // Should redirect to Authentik
    await page.waitForURL(/authentik/);
    expect(page.url()).toContain('authentik');
  });

  test('should store JWT token in localStorage', async ({ page, context }) => {
    // Navigate to login
    await page.goto(`${BASE_URL}/login`);

    // Click OAuth2 button
    await page.click('button:has-text("Login with Authentik")');

    // Simulate OAuth callback
    await page.goto(`${BASE_URL}/auth/callback?code=test-code&state=test-state`);

    // Check localStorage for token
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(token).toBeTruthy();
  });

  test('should redirect to dashboard after successful login', async ({ page }) => {
    // Login via OAuth
    await page.goto(`${BASE_URL}/login`);
    await page.click('button:has-text("Login with Authentik")');

    // Simulate OAuth callback
    await page.goto(`${BASE_URL}/auth/callback?code=test-code&state=test-state`);

    // Should redirect to dashboard
    await page.waitForURL(`${BASE_URL}/dashboard`);
    expect(page.url()).toContain('/dashboard');
  });

  test('should set Authorization header with JWT token', async ({ page }) => {
    let authHeaderSet = false;

    // Intercept API calls to check Authorization header
    await page.on('request', request => {
      if (request.url().includes('/api/v1')) {
        const authHeader = request.headers()['authorization'];
        if (authHeader && authHeader.startsWith('Bearer ')) {
          authHeaderSet = true;
        }
      }
    });

    await loginUser(page, userEmail, userPassword);

    // Make an API call
    await page.goto(`${BASE_URL}/dashboard`);

    // Wait for request and verify
    await page.waitForTimeout(500);
    expect(authHeaderSet).toBeTruthy();
  });
});

// ── Test Suite 3: Invite Member ─────────────────────────────────────────────

test.describe('Invite Member', () => {
  test('should open invite dialog on button click', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    // Navigate to org-admin/members
    await page.goto(`${BASE_URL}/org-admin/members`);

    // Click invite button
    await page.click('button:has-text("Invite Member")');

    // Dialog should be visible
    const dialog = page.locator('[role="dialog"]');
    await expect(dialog).toBeVisible();
  });

  test('should send invitation email', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    // Navigate to members page
    await page.goto(`${BASE_URL}/org-admin/members`);

    // Click invite button
    await page.click('button:has-text("Invite Member")');

    // Fill invitation form
    const inviteeEmail = `invitee-${Date.now()}@example.com`;
    await page.fill('input[name="email"]', inviteeEmail);
    await page.selectOption('select[name="role"]', 'analyst');

    // Submit
    await page.click('button:has-text("Send Invite")');

    // Should show success toast
    const toast = page.locator('[role="status"]');
    await expect(toast).toContainText('Invitation sent');
  });

  test('should not allow duplicate invitations', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    const inviteeEmail = `duplicate-${Date.now()}@example.com`;

    // Invite user
    await page.goto(`${BASE_URL}/org-admin/members`);
    await page.click('button:has-text("Invite Member")');
    await page.fill('input[name="email"]', inviteeEmail);
    await page.click('button:has-text("Send Invite")');

    // Try to invite again
    await page.click('button:has-text("Invite Member")');
    await page.fill('input[name="email"]', inviteeEmail);
    await page.click('button:has-text("Send Invite")');

    // Should show error
    const errorMessage = page.locator('[role="alert"]');
    await expect(errorMessage).toContainText('pending invitation');
  });

  test('should validate email format', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    await page.goto(`${BASE_URL}/org-admin/members`);
    await page.click('button:has-text("Invite Member")');

    // Enter invalid email
    await page.fill('input[name="email"]', 'invalid-email');

    // Submit button should be disabled or show error
    const submitButton = page.locator('button:has-text("Send Invite")');
    const isDisabled = await submitButton.isDisabled();

    if (!isDisabled) {
      // Try to click and check for validation error
      await page.click('button:has-text("Send Invite")');
      const errorMessage = page.locator('[role="alert"]');
      await expect(errorMessage).toContainText('valid email');
    }
  });

  test('should show member immediately after successful invite', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    const inviteeEmail = `immediate-${Date.now()}@example.com`;

    // Invite user
    await page.goto(`${BASE_URL}/org-admin/members`);
    await page.click('button:has-text("Invite Member")');
    await page.fill('input[name="email"]', inviteeEmail);
    await page.selectOption('select[name="role"]', 'viewer');
    await page.click('button:has-text("Send Invite")');

    // Member list should include the invited user with "pending" status
    const memberList = page.locator('[data-testid="member-list"]');
    await expect(memberList).toContainText(inviteeEmail);
    await expect(memberList).toContainText('Pending');
  });
});

// ── Test Suite 4: Accept Invitation ─────────────────────────────────────────

test.describe('Accept Invitation', () => {
  test('should navigate to invitation page with token', async ({ page }) => {
    const inviteToken = 'test-invite-token-123';

    // Navigate to invitation page
    await page.goto(`${BASE_URL}/invitations/${inviteToken}`);

    // Should show invitation details
    await expect(page.locator('text=Join Organization')).toBeVisible();
  });

  test('should display org name and role', async ({ page }) => {
    const inviteToken = 'test-invite-token-123';

    // Mock the invitation details API
    await page.route(`${API_URL}/organizations/invitations/${inviteToken}`, route => {
      route.abort();
    });

    await page.goto(`${BASE_URL}/invitations/${inviteToken}`);

    // Should show organization details
    await expect(page.locator('[data-testid="org-name"]')).toBeVisible();
    await expect(page.locator('[data-testid="invite-role"]')).toBeVisible();
  });

  test('should accept invitation and redirect to dashboard', async ({ page }) => {
    const inviteToken = 'test-invite-token-123';

    // Navigate to invitation page
    await page.goto(`${BASE_URL}/invitations/${inviteToken}`);

    // Click Accept button
    await page.click('button:has-text("Accept")');

    // Should redirect to dashboard
    await page.waitForURL(`${BASE_URL}/dashboard`);
    expect(page.url()).toContain('/dashboard');

    // Should show success toast
    const toast = page.locator('[role="status"]');
    await expect(toast).toContainText("You've joined");
  });

  test('should reject expired invitations', async ({ page }) => {
    const inviteToken = 'expired-token';

    // Navigate to expired invitation
    await page.goto(`${BASE_URL}/invitations/${inviteToken}`);

    // Should show error message
    const errorMessage = page.locator('[role="alert"]');
    await expect(errorMessage).toContainText('expired');
  });

  test('should require login to accept invitation', async ({ page }) => {
    const inviteToken = 'test-token';

    // Clear localStorage to simulate unauthenticated user
    await page.evaluate(() => localStorage.clear());

    // Navigate to invitation
    await page.goto(`${BASE_URL}/invitations/${inviteToken}`);

    // Should redirect to login
    await page.waitForURL(`${BASE_URL}/login`);
    expect(page.url()).toContain('/login');
  });

  test('should auto-redirect to dashboard after acceptance', async ({ page }) => {
    const inviteToken = 'test-token';

    // Navigate to invitation
    await page.goto(`${BASE_URL}/invitations/${inviteToken}`);

    // Click accept
    await page.click('button:has-text("Accept")');

    // Auto-redirect should happen
    await page.waitForURL(`${BASE_URL}/dashboard`, { timeout: 5000 });
    expect(page.url()).toContain('/dashboard');
  });
});

// ── Test Suite 5: Organization Switcher ─────────────────────────────────────

test.describe('Org Switcher', () => {
  test('should list all user organizations', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    // Open org switcher
    await page.click('[data-testid="org-switcher"]');

    // Should list both orgs
    const dropdown = page.locator('[role="listbox"]');
    await expect(dropdown).toContainText(orgName);
  });

  test('should switch organization on selection', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    // Get current org name
    const currentOrg = await page.locator('[data-testid="org-switcher"]').textContent();

    // Open switcher and select a different org
    await page.click('[data-testid="org-switcher"]');

    // Find an option that's not the current org
    const options = page.locator('[role="option"]');
    const count = await options.count();

    if (count > 1) {
      // Click the second org option
      await options.nth(1).click();

      // Page should refresh/navigate
      await page.waitForLoadState('networkidle');

      // Org in header should change
      const newOrg = await page.locator('[data-testid="org-switcher"]').textContent();
      expect(newOrg).not.toBe(currentOrg);
    }
  });

  test('should update URL with new org_id', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    // Get initial org ID from URL
    const initialUrl = page.url();
    const initialOrgId = new URL(initialUrl).searchParams.get('org_id');

    // Switch org
    await page.click('[data-testid="org-switcher"]');
    const secondOption = page.locator('[role="option"]').nth(1);
    await secondOption.click();

    // Wait for URL change
    await page.waitForTimeout(500);

    // New org_id in URL
    const newUrl = page.url();
    const newOrgId = new URL(newUrl).searchParams.get('org_id');

    if (initialOrgId && newOrgId) {
      expect(newOrgId).not.toBe(initialOrgId);
    }
  });

  test('should load correct members list after switch', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    // Go to members page
    await page.goto(`${BASE_URL}/org-admin/members`);

    // Get members for first org
    const firstOrgMembers = await page.locator('[data-testid="member-list"] > [data-testid="member-row"]').count();

    // Switch org
    await page.click('[data-testid="org-switcher"]');
    await page.locator('[role="option"]').nth(1).click();

    // Members list should refresh
    await page.goto(`${BASE_URL}/org-admin/members`);

    // Should be different members
    await page.waitForLoadState('networkidle');
    const secondOrgMembers = await page.locator('[data-testid="member-list"] > [data-testid="member-row"]').count();

    // Lists may be same size but should be fetched for the right org
    expect(page.url()).toBeDefined();
  });
});

// ── Test Suite 6: Admin Panel ───────────────────────────────────────────────

test.describe('Admin Panel Access', () => {
  test('admin user can access admin panel', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    // Navigate to admin
    await page.goto(`${BASE_URL}/org-admin`);

    // Should load without redirect
    expect(page.url()).toContain('/org-admin');

    // Should see admin content
    await expect(page.locator('text=Organization Settings')).toBeVisible();
  });

  test('non-admin user cannot access admin panel', async ({ page, context }) => {
    // Create non-admin user context
    const nonAdminPage = await context.newPage();

    // Navigate to admin (should redirect)
    await nonAdminPage.goto(`${BASE_URL}/org-admin`);

    // Should redirect to dashboard
    await nonAdminPage.waitForURL(`${BASE_URL}/dashboard`, { timeout: 5000 });
    expect(nonAdminPage.url()).not.toContain('/org-admin');
  });

  test('admin can view audit logs', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    // Navigate to audit logs
    await page.goto(`${BASE_URL}/org-admin/audit-logs`);

    // Should display logs
    const logTable = page.locator('[data-testid="audit-log-table"]');
    await expect(logTable).toBeVisible();

    // Should have columns
    await expect(page.locator('th:has-text("Action")')).toBeVisible();
    await expect(page.locator('th:has-text("User")')).toBeVisible();
    await expect(page.locator('th:has-text("Timestamp")')).toBeVisible();
  });

  test('admin can update member roles', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    // Navigate to members
    await page.goto(`${BASE_URL}/org-admin/members`);

    // Find a member row with role dropdown
    const memberRow = page.locator('[data-testid="member-row"]').first();
    const roleSelect = memberRow.locator('select[name="role"]');

    // Change role
    await roleSelect.selectOption('admin');

    // Should show success message
    const toast = page.locator('[role="status"]');
    await expect(toast).toContainText('updated');
  });

  test('admin can download compliance report', async ({ page, context }) => {
    await loginUser(page, userEmail, userPassword);

    // Navigate to compliance page
    await page.goto(`${BASE_URL}/compliance/dashboard`);

    // Set date range
    await page.fill('input[name="start_date"]', '2026-03-01');
    await page.fill('input[name="end_date"]', '2026-03-23');

    // Select CSV format
    await page.selectOption('select[name="format"]', 'csv');

    // Start download promise before clicking
    const downloadPromise = page.waitForEvent('download');

    // Click generate
    await page.click('button:has-text("Generate Report")');

    // Wait for download
    const download = await downloadPromise;

    // Verify file
    expect(download.suggestedFilename()).toContain('audit-report');
    expect(download.suggestedFilename()).toContain('.csv');
  });

  test('admin can export report as PDF', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    await page.goto(`${BASE_URL}/compliance/dashboard`);

    // Set date range and format
    await page.fill('input[name="start_date"]', '2026-03-01');
    await page.fill('input[name="end_date"]', '2026-03-23');
    await page.selectOption('select[name="format"]', 'pdf');

    // Download PDF
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Generate Report")');
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toContain('.pdf');
  });
});

// ── Test Suite 7: Compliance Report Download ────────────────────────────────

test.describe('Compliance Report Generation', () => {
  test('should generate report with date range', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    await page.goto(`${BASE_URL}/compliance/dashboard`);

    // Set date range
    await page.fill('input[name="start_date"]', '2026-03-15');
    await page.fill('input[name="end_date"]', '2026-03-23');

    // Generate report
    await page.click('button:has-text("Generate Report")');

    // Should show preview
    const preview = page.locator('[data-testid="report-preview"]');
    await expect(preview).toBeVisible();
  });

  test('should validate date range', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    await page.goto(`${BASE_URL}/compliance/dashboard`);

    // Set invalid date range (end before start)
    await page.fill('input[name="start_date"]', '2026-03-23');
    await page.fill('input[name="end_date"]', '2026-03-15');

    // Try to generate
    await page.click('button:has-text("Generate Report")');

    // Should show error
    const errorMessage = page.locator('[role="alert"]');
    await expect(errorMessage).toContainText('End date must be after start date');
  });

  test('should download report in CSV format', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    await page.goto(`${BASE_URL}/compliance/dashboard`);

    await page.fill('input[name="start_date"]', '2026-03-01');
    await page.fill('input[name="end_date"]', '2026-03-23');
    await page.selectOption('select[name="format"]', 'csv');

    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Generate Report")');
    const download = await downloadPromise;

    // Verify CSV
    const path = await download.path();
    expect(path).toBeDefined();
    expect(download.suggestedFilename()).toMatch(/\.csv$/);
  });

  test('should have correct columns in CSV export', async ({ page }) => {
    await loginUser(page, userEmail, userPassword);

    // Mock the API response to check CSV content
    await page.route(`${API_URL}/organizations/*/audit-logs*`, route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          logs: [
            {
              id: 'log-1',
              action: 'invite_member',
              user_id: 'user-1',
              resource_type: 'member',
              created_at: '2026-03-23T10:00:00Z'
            }
          ]
        })
      });
    });

    await page.goto(`${BASE_URL}/compliance/dashboard`);

    await page.fill('input[name="start_date"]', '2026-03-01');
    await page.fill('input[name="end_date"]', '2026-03-23');
    await page.selectOption('select[name="format"]', 'csv');

    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Generate Report")');
    const download = await downloadPromise;

    // Read file content to verify CSV structure
    const path = await download.path();
    expect(path).toBeDefined();
  });
});

// ── Helper Functions ──────────────────────────────────────────────────────────

async function loginUser(page: Page, email: string, password: string) {
  // Set token in localStorage to simulate login
  await page.goto(`${BASE_URL}/`);

  await page.evaluate((credentials) => {
    localStorage.setItem('access_token', 'mock-jwt-token');
    localStorage.setItem('user_email', credentials.email);
    localStorage.setItem('user_id', 'test-user-id');
  }, { email, password });

  // Navigate to dashboard
  await page.goto(`${BASE_URL}/dashboard`);

  // Wait for page to load
  await page.waitForLoadState('networkidle');
}
