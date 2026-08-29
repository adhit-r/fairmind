import { expect, test, type Route } from '@playwright/test'

const unsupportedRequestPattern = /\/api\/v1\/(?:bias\/llm-judge|bias-detection(?:-v2)?|modern-bias(?:-detection)?|multimodal-bias(?:-detection)?)/

async function fulfillJson(route: Route, body: unknown) {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

for (const [path, pageHeading] of [
  ['/explainability-studio', 'Explainability Studio'],
  ['/llm-judge', 'LLM Judge'],
  ['/llm-testing', 'LLM Testing'],
  ['/modern-bias', 'Modern Bias Evaluation'],
  ['/multimodal-bias', 'Multimodal Bias Detection'],
] as const) {
  test(`${pageHeading} is an inert unsupported-pack boundary`, async ({ page }) => {
    const unsupportedRequests: string[] = []

    page.on('request', (request) => {
      const requestPath = new URL(request.url()).pathname.replace('/api/proxy', '')
      if (unsupportedRequestPattern.test(requestPath)) unsupportedRequests.push(requestPath)
    })

    await page.addInitScript(() => {
      window.localStorage.setItem('access_token', 'playwright-token')
      window.localStorage.setItem('selected_org_id', 'org-1')
    })
    await page.route('**/api/proxy/**', async (route) => {
      const requestPath = new URL(route.request().url()).pathname.replace('/api/proxy', '')

      if (requestPath === '/api/v1/auth/me') {
        return fulfillJson(route, {
          id: 'user-1',
          username: 'reviewer',
          email: 'reviewer@acme.test',
        })
      }
      if (requestPath === '/api/v1/organizations') {
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
      return fulfillJson(route, [])
    })

    await page.goto(path)

    const surface = page.locator('section[aria-labelledby="unsupported-pack-page-title"]')
    await expect(surface.getByRole('heading', { name: pageHeading, exact: true })).toBeVisible()
    await expect(surface.getByRole('heading', { name: 'Evaluation pack unavailable', exact: true })).toBeVisible()
    await expect(surface.getByText('No score, result, evidence, or compliance conclusion is generated here.')).toBeVisible()
    await expect(surface.locator('form, input, textarea, select, [role="tab"], [role="combobox"]')).toHaveCount(0)
    await expect(surface.getByRole('button', { name: /evaluate|detect|run|export|download/i })).toHaveCount(0)
    await page.waitForTimeout(250)
    expect(unsupportedRequests).toEqual([])
  })
}
