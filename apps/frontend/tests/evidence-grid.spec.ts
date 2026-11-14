import { expect, test, type Route } from '@playwright/test'
import { installGridFixtures, layoutFacts } from './grid-fixtures'

// Evidence and seals for sys-a, answered here on top of the grid fixtures; nothing reaches a database.
const GOV = '/api/v1/ai-governance'
const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
const item = (id: string, title: string, extra: Record<string, unknown> = {}) => ({
  id, systemId: 'sys-a', type: 'fairness_report', title, source: 'test', status: 'collected', uploadedBy: 'reviewer', capturedAt: '2026-11-01T00:00:00Z',
  content: {}, confidence: 0.9, metadata: {}, tags: ['fairness'], folder: 'tests', artifactKind: 'report', fileUrl: '', fileName: '', fileSize: 0,
  timestamp: '2026-11-01T00:00:00Z', stale: false, linkedEntityCount: 1, linkedEntities: [], metadataSummary: {}, workflowState: 'linked', ...extra,
})
const evidence = [item('ev-1', 'Fairness report'), item('ev-2', 'Old monitoring snapshot', { type: 'monitoring', stale: true, tags: [] })]
const summary = { systemId: 'sys-a', totalEvidence: 2, linkedEvidence: 2, averageConfidence: 0.9, highConfidenceEvidence: 2, evidenceTypes: [], metadataSources: [], workflowState: 'linked', decisionReadiness: 'ready', missingSignals: [], recommendedNextStep: '' }
const seal = { id: 'seal-1', requestId: 'req-1', decision: 'approved', chainHead: 'abcdef0123456789', evidenceCount: 2, gate: {}, sealedBy: 'approver', createdAt: '2026-11-02T00:00:00Z', verification: { status: 'intact', changed: [], missing: [], addedSince: 0 } }

test.describe('Evidence page', () => {
  test.beforeEach(async ({ page }) => {
    await installGridFixtures(page)
    await page.route('**/api/proxy/**', async (route) => {
      const path = new URL(route.request().url()).pathname.replace('/api/proxy', '')
      if (path === `${GOV}/evidence-v2/sys-a`) return json(route, evidence)
      if (path === `${GOV}/evidence/sys-a/summary`) return json(route, summary)
      if (path === `${GOV}/systems/sys-a/seals`) return json(route, [seal])
      return route.fallback()
    })
  })

  test('shows the system picker, the evidence table and the sealed chain', async ({ page }) => {
    await page.goto('/evidence')
    await expect(page.getByRole('heading', { level: 1, name: 'Evidence' })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByText('What backs the release decision for Grid system A.')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Fairness report' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Old monitoring snapshot' })).toBeVisible()
    await expect(page.getByText('Stale', { exact: true })).toHaveCount(1)
    const chain = page.getByRole('region', { name: 'Evidence chain' })
    await expect(chain.locator('code')).toHaveText('abcdef0123456789')
    await expect(chain.getByText('Chain intact')).toBeVisible()
  })

  test('a row opens the evidence detail drawer', async ({ page }) => {
    await page.goto('/evidence')
    await page.getByRole('button', { name: 'Fairness report' }).click({ timeout: 30_000 })
    await expect(page.getByRole('dialog')).toBeVisible()
  })

  test('the search narrows the table', async ({ page }) => {
    await page.goto('/evidence')
    await expect(page.getByRole('button', { name: 'Fairness report' })).toBeVisible({ timeout: 30_000 })
    await page.getByLabel('Search evidence').fill('monitoring')
    await expect(page.getByRole('button', { name: 'Fairness report' })).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Old monitoring snapshot' })).toBeVisible()
  })

  test('no page horizontal scroll at 375px', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/evidence')
    await expect(page.getByRole('heading', { level: 1, name: 'Evidence' })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByRole('button', { name: 'Fairness report' })).toBeVisible()
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
  })
})
