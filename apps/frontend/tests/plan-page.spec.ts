import { expect, test, type Route } from '@playwright/test'
import { GRID_FW, installGridFixtures, layoutFacts } from './grid-fixtures'

// The plan for sys-a, answered here on top of the grid fixtures; nothing reaches a database.
const GOV = '/api/v1/ai-governance'
const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
const applicability = {
  rulesVersion: '1', suggestedTier: 'high', tier: 'high', suggestedFrameworks: [GRID_FW], frameworks: [{ key: GRID_FW, name: 'ISO/IEC 42001:2023' }],
  answers: { use: 'credit_scoring', decidesAboutPeople: true, humanReview: 'each', markets: ['IN'], rbiRegulated: 'yes', personalDataIndia: true, intendedPurpose: null },
  tierRules: [{ id: 'T1', text: 'Decides about credit', cite: null }], added: [], removed: [], reason: null, tierBelowSuggestion: false,
  overrideAcceptedBy: null, overrideAcceptedAt: null, confirmedBy: 'reviewer', confirmedAt: '2026-11-01T00:00:00Z', evidenceId: 'ev-app',
}
const wf = (id: string, pack: string, relation: string) => ({ id, name: `Workflow ${id}`, relation, stage: 'govern', pack, installed: pack === 'p-org', latestRun: null })
const req = (control: string, workflows: unknown[]) => ({ key: `${GRID_FW}|${control}`, control, title: `Requirement ${control}`, status: 'gap', workflows, evaluations: [] })
const journey = {
  key: GRID_FW, name: 'ISO/IEC 42001:2023', pillar: 'governance', version: null, type: null, binding: null, status: null, active: 3, coveredAll: 2, coveredInstalled: 1,
  groups: [{ name: 'Clause 4 Context', requirements: [req('4.1', [wf('w1', 'p-org', 'Supports'), wf('w2', 'p-risk', 'Satisfies')]), req('4.2', [wf('w3', 'p-org', 'Partially satisfies')]), req('9.1', [])] }],
  steps: [
    { pack: 'p-org', name: 'Organisation pack', installed: true, newlyCovered: 2, cumulative: 2 },
    { pack: 'p-risk', name: 'Risk pack', installed: false, newlyCovered: 0, cumulative: 2 },
  ],
}
const packs = [
  { id: 'p-org', name: 'Organisation pack', workflowCount: 2 },
  { id: 'p-risk', name: 'Risk pack', workflowCount: 1 },
]
const detail = { id: 'p-risk', name: 'Risk pack', patterns: [{ id: 'pt', name: 'Pattern', objective: '', agentic: false, workflows: [{ id: 'w2', name: 'Workflow w2', autonomy: 'manual', stage: 'govern', latestRun: null }], evaluations: [] }], frameworks: [] }

test.describe('Plan page', () => {
  test.beforeEach(async ({ page }) => {
    await installGridFixtures(page)
    await page.route('**/api/proxy/**', async (route) => {
      const path = new URL(route.request().url()).pathname.replace('/api/proxy', '')
      if (path === `${GOV}/systems/sys-a`)
        return json(route, { id: 'sys-a', workspaceId: 'ws-1', name: 'Grid system A', owner: 'owner-a', riskTier: 'high', lifecycleStage: 'govern', metadata: { source: 'mlflow' }, applicability, createdAt: '2026-10-01T00:00:00Z', updatedAt: '2026-10-01T00:00:00Z' })
      if (path === `/api/v1/packs/journeys/${GRID_FW}`) return json(route, journey)
      if (path === '/api/v1/packs') return json(route, packs)
      if (path === '/api/v1/packs/library/p-risk') return json(route, detail)
      if (path.startsWith(`${GOV}/systems/sys-a/`) || [`${GOV}/evidence/`, `${GOV}/remediation`, `${GOV}/dashboard/risk`, `${GOV}/reports`, `${GOV}/approval/`].some((p) => path.startsWith(p)))
        return route.fulfill({ status: 404, contentType: 'application/json', body: '{"detail":"Not found"}' })
      return route.fallback()
    })
  })

  test('packs, the AI read, and unticking dims the column and updates Best', async ({ page }) => {
    await page.goto('/systems/sys-a/plan')
    await expect(page.getByRole('heading', { level: 1, name: 'Plan for Grid system A' })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByRole('button', { name: 'Install 1 pack for the organisation' })).toBeEnabled()
    const read = page.getByRole('region', { name: 'What the AI read' })
    await expect(read.getByText('Credit scoring')).toBeVisible()
    await expect(read.getByText('MLflow registry')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Save plan for this system' })).toBeDisabled()

    await page.getByRole('button', { name: '1 workflow', exact: true }).click()
    await expect(page.getByRole('link', { name: 'Workflow w2' })).toBeVisible()

    await page.getByRole('tab', { name: 'Requirements' }).click()
    const grid = page.locator('[data-mx="plancov"]')
    await expect(grid.locator('tbody tr')).toHaveCount(2)
    const best = grid.locator('tbody tr').first().locator('td.mx-cnt .fm-cel')
    await expect(best).toHaveClass(/r3/)
    expect((await layoutFacts(page)).legends).toBe(1)

    await page.getByRole('tab', { name: 'Packs' }).click()
    await page.getByRole('checkbox', { name: 'Include Risk pack' }).uncheck()
    await expect(page.getByRole('button', { name: 'Open system' })).toHaveCount(0)
    await expect(page.getByRole('link', { name: 'Open system' })).toBeVisible()
    await page.getByRole('tab', { name: 'Requirements' }).click()
    await expect(grid.locator('th.mx-ch.mx-off')).toHaveCount(1)
    await expect(best).toHaveClass(/r1/)

    await page.getByRole('button', { name: 'Show all 3' }).click()
    await expect(grid.locator('tbody tr')).toHaveCount(3)
  })

  test('no horizontal scroll at 375px', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/systems/sys-a/plan')
    await expect(page.getByRole('heading', { level: 1, name: 'Plan for Grid system A' })).toBeVisible({ timeout: 30_000 })
    await page.getByRole('tab', { name: 'Requirements' }).click()
    await expect(page.locator('[data-mx="plancov"]')).toBeVisible()
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
  })
})
