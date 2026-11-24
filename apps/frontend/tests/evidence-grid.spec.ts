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
    await page.route('**/api/v1/**', async (route) => {
      const path = new URL(route.request().url()).pathname.replace('/api/proxy', '')
      if (path === `${GOV}/evidence-v2/sys-a`) return json(route, evidence)
      if (path === `${GOV}/evidence/sys-a/summary`) return json(route, summary)
      if (path === `${GOV}/systems/sys-a/seals`) return json(route, [seal])
      if (path === `${GOV}/evidence-v2/sys-b`) return json(route, [
        item('ev-b', 'Fairness report', { systemId: 'sys-b' }),
        item('ev-b-latest', 'Later passing report', { systemId: 'sys-b' }),
      ])
      if (path === `${GOV}/evidence/sys-b/summary`) return json(route, { ...summary, systemId: 'sys-b' })
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
    const record = page.getByRole('dialog', { name: 'Fairness report' })
    await expect(record).toBeVisible()
    await expect(page).toHaveURL(/\/evidence\?system=sys-a&evidence=ev-1$/)
    await expect(record.getByText('ev-1', { exact: true })).toBeVisible()
    await page.goBack()
    await expect(record).toHaveCount(0)
    await page.goForward()
    await expect(record.getByText('ev-1', { exact: true })).toBeVisible()
  })

  test('a copied link opens its exact system and record across reloads', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('fairmind:selected-ai-system', 'sys-a'))
    const reads: URL[] = []
    page.on('request', (request) => {
      const url = new URL(request.url())
      if (url.pathname.includes('/evidence-v2/')) reads.push(url)
    })
    await page.goto('/evidence?system=sys-b&evidence=ev-b')
    const record = page.getByRole('dialog', { name: 'Fairness report' })
    for (const reload of [false, true]) {
      if (reload) await page.reload()
      await expect(record.getByText('ev-b', { exact: true })).toBeVisible()
      await expect(record.getByRole('link', { name: 'Grid system B' })).toHaveAttribute('href', '/systems/sys-b')
    }
    expect(reads.length).toBeGreaterThanOrEqual(2)
    expect(reads.every((url) => url.pathname.endsWith('/evidence-v2/sys-b') && url.searchParams.get('org_id') === 'org-1')).toBe(true)
  })

  test('a record from a different system stays unavailable', async ({ page }) => {
    await page.goto('/evidence?system=sys-b&evidence=ev-1')
    await expect(page.getByText('Evidence record unavailable', { exact: true })).toBeVisible()
    await expect(page.getByText('No accessible record ev-1 was found for Grid system B.', { exact: true })).toBeVisible()
    await expect(page.getByRole('dialog')).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Fairness report' })).toHaveCount(0)
    await page.getByRole('link', { name: 'Browse evidence for Grid system B' }).click()
    await expect(page).toHaveURL(/\/evidence\?system=sys-b$/)
    await expect(page.getByRole('button', { name: 'Later passing report' })).toBeVisible()
  })

  test('Back from a system change restores the library originally opened without a scope', async ({ page }) => {
    await page.goto('/evidence')
    await expect(page).toHaveURL(/\/evidence\?system=sys-a$/)
    await page.getByRole('combobox', { name: 'AI system' }).click()
    await page.getByRole('option', { name: 'Grid system B' }).click()
    await expect(page.getByRole('button', { name: 'Later passing report' })).toBeVisible()
    await page.goBack()
    await expect(page).toHaveURL(/\/evidence\?system=sys-a$/)
    await expect(page.getByRole('button', { name: 'Old monitoring snapshot' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Later passing report' })).toHaveCount(0)
  })

  test('unscoped, unknown or ambiguous links never fetch evidence', async ({ page }) => {
    const reads: string[] = []
    page.on('request', (request) => {
      if (request.url().includes('/evidence-v2/')) reads.push(request.url())
    })
    for (const query of ['evidence=ev-1', 'system=unknown&evidence=ev-1', 'system=sys-a&system=sys-b&evidence=ev-1', 'system=sys-a&evidence=']) {
      await page.goto(`/evidence?${query}`)
      await expect(page.getByText('Evidence link unavailable', { exact: true })).toBeVisible()
      await expect(page.getByRole('dialog')).toHaveCount(0)
    }
    expect(reads).toEqual([])
  })

  test('a denied read shows the failure and retries the original record', async ({ page }) => {
    let denied = true
    await page.route('**/evidence-v2/sys-b?**', async (route) => denied
      ? route.fulfill({ status: 403, json: { detail: 'Access denied' } }) : route.fallback())
    await page.goto('/evidence?system=sys-b&evidence=ev-b')
    await expect(page.getByText('The evidence could not load', { exact: true })).toBeVisible()
    await expect(page.getByRole('dialog')).toHaveCount(0)
    await expect(page.getByText('No evidence collected yet')).toHaveCount(0)
    denied = false
    await page.getByRole('button', { name: 'Try again' }).click()
    await expect(page.getByRole('dialog').getByText('ev-b', { exact: true })).toBeVisible()
  })

  test('failure of a secondary summary leaves the exact record usable and the missing coverage visible', async ({ page }) => {
    await page.route('**/evidence/sys-b/summary?**', (route) => route.fulfill({ status: 403, json: { detail: 'Access denied' } }))
    await page.goto('/evidence?system=sys-b&evidence=ev-b')
    await expect(page.getByRole('dialog').getByText('ev-b', { exact: true })).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(page.getByText('Evidence gap summary unavailable')).toBeVisible()
  })

  test('the search narrows the table', async ({ page }) => {
    await page.goto('/evidence')
    await expect(page.getByRole('button', { name: 'Fairness report' })).toBeVisible({ timeout: 30_000 })
    await page.getByLabel('Search evidence').fill('monitoring')
    await expect(page.getByRole('button', { name: 'Fairness report' })).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Old monitoring snapshot' })).toBeVisible()
  })

  test('the evidence matrix keeps one keyboard stop and restores focus after inspection', async ({ page }) => {
    await page.route((url) => url.pathname.endsWith('/api/v1/packs/controls'), (route) => json(route, {
      controls: [
        { id: 'FMC-FAI-01', name: 'Fairness', objective: '', workflows: [] },
        { id: 'FMC-OVS-01', name: 'Human oversight', objective: '', workflows: [] },
      ],
      crosswalk: [
        { commonControl: 'FMC-FAI-01', key: 'ISO42001|4.1', relation: 'Satisfies' },
        { commonControl: 'FMC-OVS-01', key: 'ISO42001|4.2', relation: 'Satisfies' },
      ],
    }))
    await page.goto('/evidence')
    await page.getByRole('link', { name: 'Evidence grid' }).click({ timeout: 30_000 })
    await expect(page).toHaveURL(/\/evidence\?view=grid$/)

    const evidence = page.getByRole('region', { name: 'Evidence' })
    const matrix = evidence.getByRole('table', { name: 'Evidence matrix' })
    const framework = matrix.getByRole('columnheader').getByRole('link', { name: /42001/ })
    const cells = matrix.getByRole('button')
    const tabStops = cells.and(matrix.locator(':not([tabindex="-1"])'))
    const fairnessProof = matrix.getByRole('button', { name: /^Fairness.*Proof/ }).first()
    const fairnessReach = matrix.getByRole('button', { name: /^Fairness.*42001/ })
    const oversightReach = matrix.getByRole('button', { name: /^Human oversight.*42001/ })

    await expect(framework).toHaveAttribute('href', '/frameworks/ISO42001', { timeout: 30_000 })
    await expect(tabStops).toHaveCount(1)
    await framework.focus()
    await page.keyboard.press('Tab')
    await expect(fairnessProof).toBeFocused()
    await page.keyboard.press('ArrowRight')
    await expect(fairnessReach).toBeFocused()
    await page.keyboard.press('ArrowRight')
    await expect(fairnessReach).toBeFocused()

    // Data governance has proof but no ISO 42001 mapping between these two cells.
    await page.keyboard.press('ArrowDown')
    await expect(oversightReach).toBeFocused()
    await page.keyboard.press('ArrowUp')
    await expect(fairnessReach).toBeFocused()
    await page.keyboard.press('ArrowLeft')
    await expect(fairnessProof).toBeFocused()
    await page.keyboard.press('ArrowRight')
    await page.keyboard.press('ArrowDown')
    await expect(oversightReach).toBeFocused()
    await expect(tabStops).toHaveCount(1)

    await page.keyboard.press('Enter')
    const drawer = page.getByRole('dialog', { name: 'Human oversight' })
    await expect(drawer.getByRole('link', { name: 'Open framework' })).toHaveAttribute('href', '/frameworks/ISO42001')
    await page.keyboard.press('Escape')
    await expect(drawer).toBeHidden()
    await expect(oversightReach).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(cells.and(page.locator(':focus'))).toHaveCount(0)
    await page.keyboard.press('Shift+Tab')
    await expect(oversightReach).toBeFocused()
    await page.keyboard.press('Shift+Tab')
    await expect(framework).toBeFocused()
    await page.keyboard.press('Enter')
    await expect(page).toHaveURL(/\/frameworks\/ISO42001$/)
  })

  test('no page horizontal scroll at 375px', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/evidence')
    await expect(page.getByRole('heading', { level: 1, name: 'Evidence' })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByRole('button', { name: 'Fairness report' })).toBeVisible()
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
  })
})
