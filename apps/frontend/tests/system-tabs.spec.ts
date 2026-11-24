import { expect, test, type Route } from '@playwright/test'
import { GRID_FW, installGridFixtures, layoutFacts } from './grid-fixtures'

// The system file for sys-a, answered here on top of the grid fixtures; nothing reaches a database.
const GOV = '/api/v1/ai-governance'
const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
const systemId = 'sys-a'
const systemName = 'COMPAS recidivism risk score'
const originalEvidence = 'ev-failed-fairness'
const laterEvidence = 'ev-later-fairness'
const evidenceTitle = 'Fairness test on race, sex, age_cat (6172 rows)'
const date = '2026-11-01T00:00:00Z'
const evaluationId = 'EV-FAI-01'
const retestId = 'run-retest'
const system = { id: systemId, workspaceId: 'ws-1', name: systemName, owner: 'owner-a', riskTier: 'high', lifecycleStage: 'govern', metadata: {}, createdAt: date, updatedAt: date }
const otherSystem = { ...system, id: 'sys-b', name: 'Grid system B', owner: 'owner-b' }
const evidence = {
  id: originalEvidence, systemId, type: 'fairness_test', title: evidenceTitle, source: 'test', status: 'collected', uploadedBy: 'reviewer',
  capturedAt: date, timestamp: date, confidence: 0.9, metadata: {}, tags: ['fairness'], folder: 'tests', linkedEntityCount: 0, linkedEntities: [],
  content: { attributes: [{ attribute: 'race', checks: { disparate_impact: false }, disparate_impact: { value: 0.63, threshold: 0.8 } }] },
}
const checks = [
  { key: 'fairness', label: 'Fairness', state: 'proven', confidence: 0.9, evidenceId: laterEvidence, failureEvidenceIds: [originalEvidence], evidenceClass: 'measured', fails: true, detail: null },
  { key: 'monitoring', label: 'Monitoring', state: 'open', confidence: 0, evidenceId: null, evidenceClass: null, detail: null },
]
const passingFairness = { key: 'fairness', label: 'Fairness', state: 'proven', confidence: 0.9, evidenceId: laterEvidence, evidenceClass: 'measured', detail: null }
const gate = { systemId, verdict: 'no_go', confidence: 0.72, band: 'measured', checks, reasons: ['Fairness has a threshold failure.', 'Monitoring is open.'], proven: 0, attested: 0, open: 1, failing: 1 }
const clauseMap = {
  verdict: 'no_go', confidence: 0.72, scoped: true, confirmed: [{ key: GRID_FW, name: 'ISO/IEC 42001:2023' }],
  frameworks: [{ key: GRID_FW, name: 'ISO/IEC 42001:2023', counts: { proven: 1, attested: 0, open: 0, total: 1 }, clauses: [{ key: `${GRID_FW}|4.1`, control: '4.1', title: 'Organisation and its context', group: 'Clause 4 Context', state: 'proven', cell: 'proven', checks: [] }] }],
}
const seal = { id: 'seal-1', requestId: 'req-1', decision: 'approved', chainHead: 'abcdef0123456789', evidenceCount: 3, gate: {}, sealedBy: 'approver', createdAt: '2026-11-02T00:00:00Z', verification: { status: 'intact', changed: [], missing: [], addedSince: 0 } }
const finding = { id: 'finding-fairness', systemId, source: 'fairmind.eval_engines', metadata: { evaluationId, evidenceId: originalEvidence, retestEvidenceId: retestId }, title: 'Disparate impact failure', severity: 'high', status: 'open', description: 'The observed ratio fell below the minimum.', mitigation: '', timestamp: date }
const unrelatedFindings = [
  { ...finding, id: 'wrong-system', systemId: otherSystem.id },
  { ...finding, id: 'wrong-evidence', metadata: { ...finding.metadata, evidenceId: laterEvidence, retestEvidenceId: 'unrelated-retest' } },
]
const riskStatus = (risks: (typeof finding)[]) => ({ risks, suggested: [], summary: { total: risks.length, open: risks.length, automated: risks.length, suggested: 0, bySeverity: { low: 0, medium: 0, high: risks.length, critical: 0 } } })

test.describe('System page tabs', () => {
  test.beforeEach(async ({ page }) => {
    await installGridFixtures(page)
    await page.route('**/api/v1/**', async (route) => {
      const path = new URL(route.request().url()).pathname.replace('/api/proxy', '')
      if (path === `${GOV}/systems`) return json(route, [system, otherSystem])
      if (path === `${GOV}/systems/sys-a`) return json(route, system)
      if (path === `${GOV}/systems/sys-a/gate`) return json(route, gate)
      if (path === `${GOV}/systems/sys-a/clause-map`) return json(route, clauseMap)
      if (path === `${GOV}/systems/sys-a/seals`) return json(route, [seal])
      if (path === `${GOV}/approval/system/sys-a`) return json(route, { systemId: 'sys-a', request: { id: 'req-1', status: 'approved' }, decisions: [{ id: 'd-1', decision: 'approved', decided_by: 'approver', createdAt: '2026-11-02T00:00:00Z' }] })
      if (path === `${GOV}/evidence-item/${originalEvidence}`) return json(route, evidence)
      if (path === `${GOV}/evidence-v2/sys-a`) return json(route, [{ ...evidence, id: laterEvidence, title: 'Later passing fairness test', content: {} }, evidence])
      if (path === `${GOV}/dashboard/risk`) return json(route, riskStatus(unrelatedFindings))
      if (path === `/api/v1/packs/ai-systems/${systemId}/traces/summary`) return json(route, null)
      // The rest of the system file is absent, as it is for a system with nothing recorded.
      if (path.startsWith(`${GOV}/systems/sys-a/`) || [`${GOV}/evidence/`, `${GOV}/remediation`, `${GOV}/reports`].some((p) => path.startsWith(p))) return route.fulfill({ status: 404, contentType: 'application/json', body: '{"detail":"Not found"}' })
      return route.fallback()
    })
  })

  test('the system file, Requirements grid and Record retain their views through browser navigation', async ({ page }) => {
    await page.goto('/systems/sys-a')
    await expect(page.getByRole('heading', { level: 1, name: systemName })).toBeVisible({ timeout: 30_000 })
    const tabs = page.getByRole('navigation', { name: 'Tabs' })
    await expect(tabs.getByRole('button')).toHaveCount(3)
    for (const name of ['System file', 'Requirements', 'Record']) await expect(tabs.getByRole('button', { name })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Journey' })).toHaveCount(0)
    await expect(page.getByRole('heading', { level: 2, name: 'Release checks' })).toBeVisible()
    await expect(page.locator('[data-mx="sysreq"]')).toHaveCount(0)

    await tabs.getByRole('button', { name: 'Requirements' }).click()
    await expect(page).toHaveURL('/systems/sys-a?tab=requirements')
    const grid = page.locator('[data-mx="sysreq"]')
    await expect(grid).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Release checks' })).toBeHidden()
    await expect(grid.locator('tbody .fm-cel.proven')).toHaveCount(1)
    expect((await layoutFacts(page)).legends).toBe(1)

    await tabs.getByRole('button', { name: 'Record' }).click()
    await expect(page).toHaveURL('/systems/sys-a?tab=record')
    await expect(grid).toBeHidden()
    await expect(page.getByRole('region', { name: 'Sealed decisions' }).getByText('abcdef012345')).toBeVisible()
    await expect(page.getByRole('region', { name: 'Approval decisions' }).getByText('Approved')).toBeVisible()
    await page.reload()
    await expect(page.getByRole('region', { name: 'Approval decisions' }).getByText('· approver')).toBeVisible()
    await page.goBack()
    await expect(page).toHaveURL('/systems/sys-a?tab=requirements')
    await expect(grid).toBeVisible()
  })

  test('the release blocker opens its originating evidence and exposes no unrelated finding', async ({ page }) => {
    await page.goto('/systems/sys-a')
    const overview = page.getByRole('region', { name: 'Release overview' })
    const reviewTrail = page.getByRole('region', { name: 'Review trail' })
    const source = `/evidence?system=${systemId}&evidence=${originalEvidence}`
    const openEvidence = overview.getByRole('link', { name: /Open evidence/i })
    await expect(openEvidence).toHaveAttribute('href', source, { timeout: 30_000 })
    await expect(overview.getByText('Observed 0.63, minimum 0.8.')).toBeVisible()
    await expect(page.getByRole('region', { name: 'Release checks' }).getByRole('link', { name: /Open the evidence/ })).toHaveAttribute('href', source)
    await expect(reviewTrail.getByText('No linked finding')).toBeVisible()
    await expect(reviewTrail.getByText('No linked retest')).toBeVisible()

    await openEvidence.click()
    await expect(page).toHaveURL(source)
    const record = page.getByRole('dialog', { name: evidenceTitle })
    await expect(record.getByText(originalEvidence, { exact: true })).toBeVisible()
    await page.reload()
    await expect(record.getByRole('link', { name: systemName })).toHaveAttribute('href', `/systems/${systemId}`)
    await page.goBack()
    await expect(openEvidence).toHaveAttribute('href', source)
  })

  test('the review trail opens the scoped finding and names its exact recorded retest', async ({ page }) => {
    await page.route('**/api/v1/ai-governance/dashboard/risk?**', (route) => json(route, riskStatus([unrelatedFindings[1], finding])))
    await page.route(`**/api/v1/packs/evaluations/${evaluationId}?**`, (route) => json(route, {
      id: evaluationId, name: 'Disparate impact ratio', measures: 'Checks selection rates across groups.', engine: 'Engine exists', runnable: true,
      installed: true, tests: [], pack: { id: 'fairness', name: 'Fairness' }, pattern: {}, results: null,
    }))
    const retestSummary = 'The retest ratio met the minimum.'
    await page.route(`**/api/v1/packs/evaluation-runs/${retestId}?**`, (route) => json(route, {
      id: retestId, evaluationId, systemId, systemName, status: 'passed', summary: retestSummary, createdAt: date, detail: [], files: {}, metrics: {},
    }))
    await page.goto('/systems/sys-a')
    const reviewTrail = page.getByRole('region', { name: 'Review trail' })
    const findingUrl = `/findings?system=${systemId}&finding=${finding.id}`
    const retestUrl = `/compliance/evaluations/${evaluationId}?system=${systemId}&run=${retestId}&finding=${finding.id}`
    const findingLink = reviewTrail.getByRole('link', { name: finding.title })
    await expect(findingLink).toHaveAttribute('href', findingUrl, { timeout: 30_000 })
    await expect(reviewTrail.getByRole('link', { name: 'View recorded retest' })).toHaveAttribute('href', retestUrl)
    await findingLink.click()
    await expect(page).toHaveURL(findingUrl)
    const retestLink = page.getByRole('dialog', { name: `Finding: ${finding.title}` }).getByRole('link', { name: 'View recorded retest' })
    await expect(retestLink).toHaveAttribute('href', retestUrl)
    await retestLink.click()
    await expect(page).toHaveURL(retestUrl)
    await expect(page.getByRole('region', { name: 'Recorded result' }).getByText(retestSummary)).toBeVisible()
  })

  test('a gate with no failed check shows passing and unrecorded checks separately', async ({ page }) => {
    await page.route('**/api/v1/ai-governance/dashboard/risk?**', (route) => json(route, riskStatus([finding])))
    await page.route('**/api/v1/ai-governance/systems/sys-a/gate?**', (route) => json(route, {
      ...gate, verdict: 'conditional_go', checks: [passingFairness, checks[1]], reasons: ['Monitoring is open.'], proven: 1, failing: 0,
    }))
    await page.goto('/systems/sys-a')
    const overview = page.getByRole('region', { name: 'Release overview' })
    await expect(overview.getByRole('heading', { name: 'Check status' })).toBeVisible({ timeout: 30_000 })
    await expect(overview.getByRole('listitem').filter({ hasText: 'Fairness' }).getByText('Passes')).toBeVisible()
    await expect(overview.getByRole('listitem').filter({ hasText: 'Monitoring' }).getByText('Nothing on file')).toBeVisible()
    await expect(overview.getByRole('region', { name: 'Review trail' })).toHaveCount(0)
    await overview.getByRole('button', { name: 'View release checks' }).click()
    await expect(page.getByRole('heading', { name: 'Release checks' })).toBeFocused()

    await page.getByRole('navigation', { name: 'Tabs' }).getByRole('button', { name: 'Record' }).click()
    const history = page.getByRole('region', { name: 'Review history' })
    await expect(history.getByRole('link', { name: 'Original evidence' })).toHaveAttribute('href', `/evidence?system=${systemId}&evidence=${originalEvidence}`)
    await expect(history.getByRole('link', { name: 'View finding' })).toHaveAttribute('href', `/findings?system=${systemId}&finding=${finding.id}`)
    await expect(history.getByRole('link', { name: 'Latest recorded retest' })).toHaveAttribute('href', `/compliance/evaluations/${evaluationId}?system=${systemId}&run=${retestId}&finding=${finding.id}`)
  })

  test('no horizontal scroll at 375px on the Requirements tab', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/systems/sys-a')
    await expect(page.getByRole('heading', { level: 1, name: systemName })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByRole('region', { name: 'Review trail' })).toBeVisible()
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
    await page.getByRole('navigation', { name: 'Tabs' }).getByRole('button', { name: 'Requirements' }).click()
    await expect(page.locator('[data-mx="sysreq"]')).toBeVisible()
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
  })
})
