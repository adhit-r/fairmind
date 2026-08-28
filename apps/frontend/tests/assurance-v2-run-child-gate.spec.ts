import { expect, test, type Route } from '@playwright/test'

async function fulfillJson(route: Route, body: unknown) {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

test('disabled run child gate renders no preview data and makes no v2 request', async ({ page }) => {
  test.skip(
    process.env.NEXT_PUBLIC_ASSURANCE_V2_UI_ENABLED !== 'true'
      || process.env.NEXT_PUBLIC_ASSURANCE_V2_RUN_UI_ENABLED === 'true',
    'requires the dev server with the assurance master enabled and run child disabled',
  )

  const v2Requests: string[] = []
  let resolveSystemResponse: (() => void) | undefined
  const systemResponseCompleted = new Promise<void>((resolve) => {
    resolveSystemResponse = resolve
  })

  await page.addInitScript(() => {
    window.localStorage.setItem('access_token', 'playwright-token')
    window.localStorage.setItem('selected_org_id', 'org-1')
    window.localStorage.setItem('fairmind:selected-ai-system', 'system-1')
  })
  await page.route('**/api/proxy/**', async (route) => {
    const path = new URL(route.request().url()).pathname.replace('/api/proxy', '')
    if (path.includes('/evaluation-v2/')) v2Requests.push(path)
    if (path === '/api/v1/auth/me') {
      return fulfillJson(route, {
        id: 'user-1',
        username: 'reviewer',
        email: 'reviewer@acme.test',
      })
    }
    if (path === '/api/v1/organizations') {
      return fulfillJson(route, {
        organizations: [{
          id: 'org-1',
          name: 'Acme Assurance',
          slug: 'acme-assurance',
          owner_id: 'user-1',
          created_at: '2026-08-28T08:00:00Z',
          role: 'admin',
          permissions: [],
        }],
      })
    }
    if (path === '/api/v1/ai-governance/systems') {
      await fulfillJson(route, [{
        id: 'system-1',
        workspaceId: 'workspace-1',
        name: 'Decisioning Agent',
        owner: 'agent-team@acme.test',
        riskTier: 'high',
        lifecycleStage: 'assess',
        readiness: 42,
        metadata: { source: 'registry' },
      }])
      resolveSystemResponse?.()
      return
    }
    return fulfillJson(route, [])
  })

  await page.goto('/assurance/evaluations/run-1')

  await expect(page.getByRole('heading', { name: 'Assurance run preview disabled' })).toBeVisible()
  await systemResponseCompleted
  await expect(page.getByRole('region', { name: 'Selected AI system context' })).toContainText('Decisioning Agent')
  await page.waitForTimeout(250)
  expect(v2Requests).toEqual([])
})
