import { expect, test, type Page, type Route } from '@playwright/test'
import { GRID_FW, installGridFixtures, layoutFacts } from './grid-fixtures'

// Journey stays mounted while hidden, so only the cards on screen count.
const visibleCards = (page: Page) => page.evaluate(() => [...document.querySelectorAll<HTMLElement>('main .fm-card')].filter((el) => el.offsetParent !== null).length)

// The system file for sys-a, answered here on top of the grid fixtures; nothing reaches a database.
const GOV = '/api/v1/ai-governance'
const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
const checks = [
  { key: 'fairness', label: 'Fairness', state: 'proven', confidence: 0.9, evidenceId: 'ev-f', evidenceClass: 'measured', detail: null },
  { key: 'monitoring', label: 'Monitoring', state: 'open', confidence: 0, evidenceId: null, evidenceClass: null, detail: null },
]
const gate = { verdict: 'conditional_go', confidence: 0.72, band: 'measured', checks, reasons: ['Monitoring is open.'], proven: 1, attested: 0, open: 1 }
const clauseMap = {
  verdict: 'conditional_go', confidence: 0.72, scoped: true, confirmed: [{ key: GRID_FW, name: 'ISO/IEC 42001:2023' }],
  frameworks: [{ key: GRID_FW, name: 'ISO/IEC 42001:2023', counts: { proven: 1, attested: 0, open: 0, total: 1 }, clauses: [{ key: `${GRID_FW}|4.1`, control: '4.1', title: 'Organisation and its context', group: 'Clause 4 Context', state: 'proven', cell: 'proven', checks: [] }] }],
}
const seal = { id: 'seal-1', requestId: 'req-1', decision: 'approved', chainHead: 'abcdef0123456789', evidenceCount: 3, gate: {}, sealedBy: 'approver', createdAt: '2026-11-02T00:00:00Z', verification: { status: 'intact', changed: [], missing: [], addedSince: 0 } }

test.describe('System page tabs', () => {
  test.beforeEach(async ({ page }) => {
    await installGridFixtures(page)
    await page.route('**/api/proxy/**', async (route) => {
      const path = new URL(route.request().url()).pathname.replace('/api/proxy', '')
      if (path === `${GOV}/systems/sys-a`) return json(route, { id: 'sys-a', workspaceId: 'ws-1', name: 'Grid system A', owner: 'owner-a', riskTier: 'high', lifecycleStage: 'govern', metadata: {}, createdAt: '2026-10-01T00:00:00Z', updatedAt: '2026-10-01T00:00:00Z' })
      if (path === `${GOV}/systems/sys-a/gate`) return json(route, gate)
      if (path === `${GOV}/systems/sys-a/clause-map`) return json(route, clauseMap)
      if (path === `${GOV}/systems/sys-a/seals`) return json(route, [seal])
      if (path === `${GOV}/approval/system/sys-a`) return json(route, { systemId: 'sys-a', request: { id: 'req-1', status: 'approved' }, decisions: [{ id: 'd-1', decision: 'approved', decided_by: 'approver', createdAt: '2026-11-02T00:00:00Z' }] })
      // The rest of the system file is absent, as it is for a system with nothing recorded.
      if (path.startsWith(`${GOV}/systems/sys-a/`) || [`${GOV}/evidence/`, `${GOV}/remediation`, `${GOV}/dashboard/risk`, `${GOV}/reports`].some((p) => path.startsWith(p))) return route.fulfill({ status: 404, contentType: 'application/json', body: '{"detail":"Not found"}' })
      return route.fallback()
    })
  })

  test('the hero, Journey by default, Requirements grid and Record', async ({ page }) => {
    await page.goto('/systems/sys-a')
    await expect(page.getByRole('heading', { level: 1, name: 'Grid system A' })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByText('0.72', { exact: true })).toBeVisible()
    await expect(page.getByRole('region', { name: 'Decision' })).toBeVisible()
    await expect(page.getByRole('navigation', { name: 'Lifecycle' }).getByRole('link', { name: /Govern/ })).toHaveAttribute('aria-current', 'step')

    // Journey is one card: the current stage (Govern) open, every other stage a row that expands on click.
    expect(await visibleCards(page)).toBeLessThanOrEqual(3)
    const govern = page.getByRole('region', { name: 'Govern' })
    await expect(govern.getByRole('button', { name: /Govern/ })).toHaveAttribute('aria-expanded', 'true')
    await expect(govern.getByRole('button', { name: 'Open plan' })).toBeVisible()
    const operate = page.getByRole('region', { name: 'Operate' })
    const operateRow = operate.getByRole('button', { name: /Operate/ })
    await expect(operateRow).toHaveAttribute('aria-expanded', 'false')
    expect((await operate.boundingBox())?.height).toBeLessThanOrEqual(45)
    await expect(operate.getByRole('button', { name: 'Generate audit report' })).toBeVisible()
    await expect(operate.getByText('Audit reports')).toBeHidden()
    await operateRow.click()
    await expect(operateRow).toHaveAttribute('aria-expanded', 'true')
    await expect(operate.getByText('Audit reports')).toBeVisible()
    await expect(operate.getByRole('button', { name: 'Monitoring', exact: true })).toBeVisible()
    expect(await visibleCards(page)).toBeLessThanOrEqual(3)

    await page.getByRole('tab', { name: 'Requirements' }).click()
    const grid = page.locator('[data-mx="sysreq"]')
    await expect(grid).toBeVisible()
    await expect(grid.locator('tbody .fm-cel.proven')).toHaveCount(1)
    await expect(page.getByRole('region', { name: 'Decision' })).toBeHidden()
    expect(await visibleCards(page)).toBeLessThanOrEqual(3)
    expect((await layoutFacts(page)).legends).toBe(1)

    await page.getByRole('tab', { name: 'Record' }).click()
    await expect(page.getByRole('region', { name: 'Sealed decisions' }).getByText('abcdef012345')).toBeVisible()
    await expect(page.getByRole('region', { name: 'Approval decisions' }).getByText('Approved')).toBeVisible()
    await expect(page.getByRole('region', { name: 'Approval decisions' }).getByText('· approver')).toBeVisible()
    expect(await visibleCards(page)).toBeLessThanOrEqual(3)
  })

  test('no horizontal scroll at 375px on the Requirements tab', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/systems/sys-a')
    await expect(page.getByRole('region', { name: 'Operate' })).toBeVisible({ timeout: 30_000 })
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
    await page.getByRole('tab', { name: 'Requirements' }).click()
    await expect(page.locator('[data-mx="sysreq"]')).toBeVisible()
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
  })
})
