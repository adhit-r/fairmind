import { expect, test } from '@playwright/test'

const APP_URL = process.env.FAIRMIND_E2E_BASE_URL || 'http://localhost:1111'

test('protected evidence route settles after authentication', async ({ context, page }) => {
  await context.addInitScript(() => {
    window.localStorage.setItem('access_token', 'fairmind-auth-guard-test')
    window.localStorage.setItem('selected_org_id', 'org-auth-guard-test')
  })

  let currentUserRequests = 0

  // Matched on path, not host: the client resolves its base URL from
  // NEXT_PUBLIC_API_URL and falls back to the same-origin /api/proxy route, so
  // a host-specific pattern stops intercepting whenever that variable is absent
  // from the dev server's environment.
  await context.route('**/api/v1/**', async (route) => {
    const url = route.request().url()
    let body: unknown = {}

    if (url.includes('/api/v1/auth/me')) {
      currentUserRequests += 1
      body = {
        id: 'user-auth-guard-test',
        email: 'reviewer@fairmind.local',
        full_name: 'Evidence Reviewer',
        role: 'admin',
        is_active: true,
      }
    } else if (url.includes('/api/v1/organizations')) {
      body = {
        organizations: [
          {
            id: 'org-auth-guard-test',
            name: 'FairMind Recovery Lab',
            slug: 'fairmind-recovery',
            owner_id: 'user-auth-guard-test',
            created_at: '2026-07-18T00:00:00Z',
            role: 'admin',
          },
        ],
      }
    } else if (url.includes('/api/v1/ai-governance/systems')) {
      body = [
        {
          id: 'system-auth-guard-test',
          workspaceId: 'workspace-auth-guard-test',
          name: 'Payments Assistant',
          owner: 'assurance@fairmind.local',
          riskTier: 'high',
          lifecycleStage: 'assess',
          readiness: 31,
          metadata: {},
        },
      ]
    } else if (url.includes('/evidence-v2/')) {
      body = []
    } else if (url.includes('/api/v1/ai-governance/evidence/') && url.includes('/summary')) {
      body = {
        systemId: url.includes('system-auth-guard-test')
          ? 'system-auth-guard-test'
          : 'acme-pricing-lab',
        totalEvidence: 0,
        linkedEvidence: 0,
        averageConfidence: 0,
        highConfidenceEvidence: 0,
        evidenceTypes: [],
        metadataSources: [],
        workflowState: 'empty',
        decisionReadiness: 'needs_evidence',
        missingSignals: ['reviewed mappings', 'artifact hashes', 'retest evidence'],
        recommendedNextStep: 'Run or import one validated evaluation.',
      }
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(body),
    })
  })

  await page.goto(`${APP_URL}/evidence`, { waitUntil: 'domcontentloaded' })

  await expect(page.getByRole('heading', { name: 'Evidence Workbench' })).toBeVisible()
  await expect(page.getByText('Evidence Generator Workbench', { exact: true })).toBeVisible()
  expect(currentUserRequests).toBeLessThanOrEqual(2)
})
