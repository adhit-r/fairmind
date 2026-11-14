import { expect, test, type Route } from '@playwright/test'
import { GRID_FW, installGridFixtures, layoutFacts } from './grid-fixtures'

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

  test('the system file, Requirements grid and Record', async ({ page }) => {
    await page.goto('/systems/sys-a')
    await expect(page.getByRole('heading', { level: 1, name: 'Grid system A' })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByRole('navigation', { name: 'Tabs' }).getByRole('button')).toHaveCount(3)
    for (const name of ['System file', 'Requirements', 'Record']) await expect(page.getByRole('navigation', { name: 'Tabs' }).getByRole('button', { name })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Journey' })).toHaveCount(0)
    await expect(page.getByRole('heading', { level: 3, name: 'Release gate' })).toBeVisible()
    await expect(page.getByText('0.72', { exact: true }).first()).toBeVisible()
    await expect(page.locator('[data-mx="sysreq"]')).toHaveCount(0)

    await page.getByRole('navigation', { name: 'Tabs' }).getByRole('button', { name: 'Requirements' }).click()
    const grid = page.locator('[data-mx="sysreq"]')
    await expect(grid).toBeVisible()
    await expect(grid.locator('tbody .fm-cel.proven')).toHaveCount(1)
    expect((await layoutFacts(page)).legends).toBe(1)

    await page.getByRole('navigation', { name: 'Tabs' }).getByRole('button', { name: 'Record' }).click()
    await expect(page.getByRole('region', { name: 'Sealed decisions' }).getByText('abcdef012345')).toBeVisible()
    await expect(page.getByRole('region', { name: 'Approval decisions' }).getByText('Approved')).toBeVisible()
    await expect(page.getByRole('region', { name: 'Approval decisions' }).getByText('· approver')).toBeVisible()
  })

  test('no horizontal scroll at 375px on the Requirements tab', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/systems/sys-a')
    await expect(page.getByRole('heading', { level: 1, name: 'Grid system A' })).toBeVisible({ timeout: 30_000 })
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
    await page.getByRole('navigation', { name: 'Tabs' }).getByRole('button', { name: 'Requirements' }).click()
    await expect(page.locator('[data-mx="sysreq"]')).toBeVisible()
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
  })
})
