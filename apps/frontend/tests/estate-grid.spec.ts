import { expect, test, type Page } from '@playwright/test'
import { gridGates, installGridFixtures, layoutFacts } from './grid-fixtures'

const cellsOf = (page: Page) => page.getByRole('table').getByRole('button')
const failedEvidence = {
  id: 'ev-standing-failure', systemId: 'sys-a', title: 'Original fairness assessment',
  type: 'fairness_test', source: 'test', status: 'collected', confidence: 0.9, metadata: {}, tags: [],
  content: {
    rows: 245, thresholds: { disparate_impact_ratio: 0.8 }, all_checks_pass: false,
    attributes: [
      { attribute: 'age', checks: { disparate_impact: true }, disparate_impact_ratio: 0.62,
        selection_rates: { Younger: 0.31, Older: 0.5 },
        disparate_impact: { value: 0.62, threshold: 0.8, crosses_threshold: true, is_fair: true } },
      { attribute: 'region', checks: { disparate_impact: false }, disparate_impact_ratio: 0.57,
        selection_rates: { North: 0.8, East: 0.6, South: 0.456 }, groups: { North: 100, East: 20, South: 125 },
        disparate_impact: { value: 0.57, threshold: 0.8, crosses_threshold: true, is_fair: false } },
    ],
  },
  linkedEntities: [], linkedEntityCount: 0, stale: false, artifactKind: 'report', metadataSummary: {}, workflowState: 'linked',
  timestamp: '2026-10-01T00:00:00Z', capturedAt: '2026-10-01T00:00:00Z',
}
const passingEvidence = {
  ...failedEvidence, id: 'ev-fairness', title: 'Later passing assessment',
  content: { all_checks_pass: true, attributes: [] },
  timestamp: '2026-10-02T00:00:00Z', capturedAt: '2026-10-02T00:00:00Z',
}

async function installPriorityEstate(page: Page) {
  const unassessed = Array.from({ length: 9 }, (_, i) => ({ id: `untested-${i + 1}`, name: `Untested system ${i + 1}` }))
  const systems = [{ id: 'sys-a', name: 'Grid system A' }, ...unassessed].map(system => ({
    ...system, workspaceId: 'ws-1', owner: 'reviewer', riskTier: 'high', lifecycleStage: 'govern', metadata: {},
  }))
  const unassessedGates = unassessed.map(system => ({
    ...gridGates[1], systemId: system.id,
    checks: gridGates[1].checks.map(({ key, label }) => ({ key, label, state: 'open', confidence: 0, evidenceId: null, evidenceClass: null })),
  }))
  const failing = {
    ...gridGates[0],
    checks: gridGates[0].checks.map(check => check.key === 'fairness'
      ? { ...check, label: 'Fairness measured', failureEvidenceIds: ['ev-standing-failure', '', 'ev-standing-failure'] }
      : check),
  }
  await page.route('**/api/v1/ai-governance/systems?**', route => route.fulfill({ json: systems }))
  await page.route('**/api/v1/ai-governance/estate/gates?**', route => route.fulfill({ json: [failing, ...unassessedGates] }))
  return unassessed
}

test.describe('Home board', () => {
  test.beforeEach(async ({ page }) => installGridFixtures(page))

  test('leads with the failed check and matrix, keeps unassessed systems accessible, and restores the evidence link', async ({ page }) => {
    const unassessed = await installPriorityEstate(page)
    const requestedItems: URL[] = []
    await page.route('**/api/v1/ai-governance/evidence-item/**', route => {
      const url = new URL(route.request().url())
      requestedItems.push(url)
      return route.fulfill({ json: url.pathname.endsWith(`/${failedEvidence.id}`) ? failedEvidence : passingEvidence })
    })
    await page.route('**/api/v1/ai-governance/evidence-v2/sys-a?**', route => route.fulfill({ json: [passingEvidence, failedEvidence] }))
    await page.route('**/api/v1/ai-governance/evidence/sys-a/summary?**', route => route.fulfill({ json: {
      systemId: 'sys-a', totalEvidence: 2, linkedEvidence: 0, averageConfidence: 0.9, highConfidenceEvidence: 2,
      evidenceTypes: [], metadataSources: [], workflowState: 'linked', decisionReadiness: 'ready', missingSignals: [], recommendedNextStep: '',
    } }))
    await page.goto('/dashboard')
    const failures = page.getByRole('region', { name: '1 failed release check', exact: true })
    await expect(page.getByRole('navigation', { name: 'Sections', exact: true })).toBeVisible()
    const review = failures.getByRole('link', { name: 'Review Fairness on Grid system A' })
    await expect(review).toBeInViewport({ ratio: 1 })
    await expect(failures).toContainText('Grid system A')
    await expect(failures).toContainText('Fairness')
    await expect(failures.getByText(failedEvidence.title, { exact: false })).toBeVisible()
    await expect(failures).toContainText(/0\.57\b/)
    await expect(failures).toContainText(/0\.80?\b/)
    await expect(failures).not.toContainText(/0\.62\b/)
    await expect(failures).not.toContainText(passingEvidence.title)
    expect(requestedItems.length).toBeGreaterThan(0)
    expect(requestedItems.every(url => url.pathname.endsWith(`/${failedEvidence.id}`) &&
      url.searchParams.get('system_id') === 'sys-a' && url.searchParams.get('org_id') === 'org-1')).toBe(true)
    const directProof = failures.locator('a[href="/evidence?system=sys-a&evidence=ev-standing-failure"]')
    await expect(directProof).toBeInViewport({ ratio: 1 })
    await expect(directProof).toHaveAccessibleName(new RegExp(failedEvidence.title))
    const board = page.getByRole('region', { name: 'Every system against every release check' })
    const failedCell = board.getByRole('button', { name: 'Fairness on Grid system A: Fails' })
    await expect(failedCell).toBeInViewport({ ratio: 1 })
    if (page.viewportSize()!.width < 600) {
      expect((await directProof.boundingBox())!.y).toBeLessThan((await failedCell.boundingBox())!.y)
    }
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)

    const breakdown = page.getByRole('figure', { name: 'Selection rate by region' })
    await expect(breakdown).toBeVisible()
    const compare = failures.getByRole('button', { name: 'Compare groups' })
    await compare.focus()
    await page.keyboard.press('Enter')
    await expect(breakdown).toBeFocused()
    await expect(breakdown).toBeInViewport()
    await expect(breakdown).toContainText(/Grid system A.*245 records/)
    await expect(breakdown.getByRole('listitem')).toHaveText([
      /South.*125 records.*45\.6%/, /East.*20 records.*60\.0%/, /North.*100 records.*80\.0%/,
    ])
    await expect(page.getByRole('figure', { name: /selection rate by age/i })).toHaveCount(0)

    const summary = page.locator('summary').filter({ hasText: /9 systems.*(?:no|without) evidence/i })
    await expect(summary).toBeVisible()
    const inventory = page.locator('details').filter({ has: summary })
    await expect(inventory).toHaveJSProperty('open', false)
    await expect(inventory.getByRole('link')).toHaveCount(0)
    await summary.focus()
    await page.keyboard.press('Enter')
    for (const { id, name } of unassessed) {
      await expect(inventory.getByRole('link', { name, exact: true })).toHaveAttribute('href', `/systems/${id}`)
    }
    await expect(inventory.locator('a[href="/evaluations"]')).toBeVisible()
    await summary.press('Space')
    await expect(inventory).toHaveJSProperty('open', false)

    await directProof.click()
    await expect(page).toHaveURL(/\/evidence\?system=sys-a&evidence=ev-standing-failure$/)
    await expect(page.getByRole('dialog', { name: failedEvidence.title }).getByText(failedEvidence.id, { exact: true })).toBeVisible()
    await page.goBack()
    await expect(review).toBeVisible()
    await expect(review).toHaveAttribute('href', '/dashboard?system=sys-a&check=fairness')
    await review.focus()
    await page.keyboard.press('Enter')
    const dialog = page.getByRole('dialog', { name: 'Fairness on Grid system A' })
    const source = dialog.getByRole('link', { name: 'Open the evidence ev-standing-failure' })
    await expect(source).toHaveAttribute('href', '/evidence?system=sys-a&evidence=ev-standing-failure')
    await source.click()
    await expect(page).toHaveURL(/\/evidence\?system=sys-a&evidence=ev-standing-failure$/)
    await page.goBack()
    await expect(source).toBeVisible()
    await page.reload()
    await expect(source).toBeVisible()
  })

  test('keeps the original record link when its title is unavailable', async ({ page }) => {
    await page.route('**/api/v1/ai-governance/estate/gates?**', route => route.fulfill({ json: [gridGates[0]] }))
    for (const status of [200, 403]) {
      const read = page.waitForResponse(response => response.url().includes(`/evidence-item/${failedEvidence.id}?`))
      await page.route('**/api/v1/ai-governance/evidence-item/ev-standing-failure?**', route =>
        route.fulfill({ status, json: status === 403 ? { detail: 'Access denied' } :
          { ...failedEvidence, systemId: 'sys-b', title: 'Another system assessment' } }), { times: 1 })
      await page.goto('/dashboard')
      expect((await read).status()).toBe(status)
      const failures = page.getByRole('region', { name: /failed release checks?/ })
      await expect(failures.getByText(/record details unavailable/i)).toBeVisible()
      await expect(failures.locator('a[href="/evidence?system=sys-a&evidence=ev-standing-failure"]')).toBeVisible()
      await expect(failures).not.toContainText('Another system assessment')
      await expect(failures).not.toContainText(passingEvidence.title)
      await expect(page.getByRole('figure', { name: /selection rate/i })).toHaveCount(0)
      await expect(failures.getByRole('button', { name: 'Compare groups' })).toHaveCount(0)
    }
  })

  test('counts registered lifecycle stages and opens the register filtered to a legacy stage', async ({ page }) => {
    const systems = [
      { id: 'sys-a', name: 'Grid system A', lifecycleStage: 'govern' },
      { id: 'sys-b', name: 'Design assistant', lifecycleStage: 'design' },
      { id: 'sys-c', name: 'Design classifier', lifecycleStage: 'design' },
      { id: 'sys-old', name: 'Retired system', lifecycleStage: 'retired' },
    ].map(system => ({ ...system, workspaceId: 'ws-1', owner: 'reviewer', riskTier: 'high', metadata: {} }))
    await page.route('**/api/v1/ai-governance/systems?**', route => route.fulfill({ json: systems }))
    await page.goto('/dashboard')
    const chart = page.getByRole('region', { name: 'Systems by lifecycle stage' })
    await expect(chart).toContainText('3 active registered systems')
    await expect(chart.getByRole('link', { name: 'Govern, 1 of 3 active systems' })).toHaveAttribute('href', '/systems?stage=govern')
    await expect(chart.getByRole('link', { name: /^Operate,/ })).toHaveCount(0)
    await expect(chart.getByRole('link', { name: /retired/i })).toHaveCount(0)
    const design = chart.getByRole('link', { name: 'Design, 2 of 3 active systems' })
    await expect(design).toHaveAttribute('href', '/systems?stage=design')
    await design.click()
    await expect(page).toHaveURL(/\/systems\?stage=design$/)
    const register = page.getByRole('main')
    await expect(register.getByRole('button', { name: /Design assistant/ })).toBeVisible()
    await expect(register.getByRole('button', { name: /Design classifier/ })).toBeVisible()
    await expect(register.getByRole('button', { name: /Grid system A|Retired system/ })).toHaveCount(0)
  })

  test('keeps stale checks and rejected decisions separate from failed check results', async ({ page }) => {
    const gates = gridGates.map(gate => ({
      ...gate, approvalStatus: 'rejected', checks: gate.checks.map(check => ({ ...check, fails: false })),
    }))
    await page.route('**/api/v1/ai-governance/estate/gates?**', route => route.fulfill({ json: gates }))
    await page.goto('/dashboard')
    await expect(page.getByRole('button', { name: 'Decision on Grid system A: Rejected' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Monitoring on Grid system A: Out of date' })).toBeVisible()
    await expect(page.getByRole('region', { name: /failed release check/ })).toHaveCount(0)
    await expect(page.getByText('0 failing checks')).toBeVisible()
  })

  test('exposes additional failed checks on demand with their own system scope', async ({ page }) => {
    const gates = gridGates.map(gate => ({
      ...gate,
      checks: gate.checks.map(check => ({
        ...check, state: 'proven', evidenceClass: 'measured', fails: true,
        failureEvidenceIds: [`failure-${gate.systemId}-${check.key}`],
      })),
    }))
    await page.route('**/api/v1/ai-governance/estate/gates?**', route => route.fulfill({ json: gates }))
    await page.goto('/dashboard')
    const failures = page.getByRole('region', { name: '10 failed release checks' })
    const checkLinks = failures.getByRole('link', { name: /^Review .* on Grid system/ })
    await expect(checkLinks).toHaveCount(3)
    await failures.getByText('7 more failed checks').click()
    await expect(checkLinks).toHaveCount(10)
    await failures.getByRole('link', { name: 'Review Fairness on Grid system B' }).click()
    await expect(page.getByRole('dialog').getByRole('link', { name: 'Open the evidence failure-sys-b-fairness' }))
      .toHaveAttribute('href', '/evidence?system=sys-b&evidence=failure-sys-b-fairness')
  })

  test('keeps registration available in an empty estate', async ({ page }) => {
    await page.route('**/api/v1/ai-governance/systems?**', route => route.fulfill({ json: [] }))
    await page.goto('/dashboard')
    await expect(page.getByRole('heading', { name: 'No registered AI systems yet' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Register systems' })).toHaveAttribute('href', '/onboard')
    await expect(page.getByRole('region', { name: /failed release check/ })).toHaveCount(0)
  })

  test('both pending release actions open the decision for the named system', async ({ page }) => {
    const gates = gridGates.map(gate => ({ ...gate, approvalStatus: 'pending' }))
    await page.route('**/api/v1/ai-governance/estate/gates?**', route => route.fulfill({ json: gates }))
    await page.goto('/dashboard')
    const pending = page.getByRole('region', { name: '2 systems are waiting for a release decision' })
    for (const [name, id] of [['Grid system A', 'sys-a'], ['Grid system B', 'sys-b']]) {
      const target = `/systems/${id}?decide`
      await expect(pending.getByRole('link', { name: `Review release for ${name}` })).toHaveAttribute('href', target)
      await page.getByRole('button', { name: `Decision on ${name}: Waiting for a reviewer` }).click()
      const decision = page.getByRole('dialog', { name: `Decision on ${name}` })
      await expect(decision.getByRole('link', { name: 'Decide now' })).toHaveAttribute('href', target)
      await page.keyboard.press('Escape')
      await expect(decision).toBeHidden()
    }
  })

  test('shows the recorded states for every system and release check', async ({ page }) => {
    await page.goto('/dashboard')
    const board = page.getByRole('region', { name: 'Every system against every release check' })
    await expect(board).toBeVisible({ timeout: 30_000 })
    await expect(board.getByRole('link', { name: /Grid system A/ })).toBeVisible()
    await expect(board.getByRole('link', { name: /Grid system B/ })).toBeVisible()
    await expect(board.getByRole('button', { name: 'Fairness on Grid system A: Fails' })).toBeVisible()
    await expect(board.getByRole('button', { name: 'Monitoring on Grid system A: Out of date' })).toBeVisible()
    await expect(board.getByRole('button', { name: 'Data governance on Grid system A: Attested' })).toBeVisible()
    await expect(board.getByRole('button', { name: 'Human oversight on Grid system A: Estimated' })).toBeVisible()
    await expect(board.getByRole('button', { name: 'Environment on Grid system A: Nothing on file' })).toBeVisible()
    // Five checks and the decision for each of the two systems.
    await expect(cellsOf(page)).toHaveCount(12)
  })

  test('a cell is focusable and Enter opens its drawer', async ({ page }) => {
    await page.goto('/dashboard')
    const cell = page.getByRole('button', { name: 'Fairness on Grid system A: Fails' })
    await expect(cell).toBeVisible({ timeout: 30_000 })
    await cell.focus()
    await page.keyboard.press('Enter')
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    await expect(dialog.getByRole('link', { name: 'Open the system file' })).toHaveAttribute('href', '/systems/sys-a')
    const evidence = dialog.getByRole('link', { name: 'Open the evidence ev-standing-failure' })
    await expect(evidence).toHaveAttribute('href', '/evidence?system=sys-a&evidence=ev-standing-failure')
    await evidence.click()
    await expect(page).toHaveURL(/\/evidence\?system=sys-a&evidence=ev-standing-failure$/)
    await page.goBack()
    await expect(evidence).toBeVisible()
    await page.reload()
    await expect(evidence).toBeVisible()
  })

  test('the phone menu, failing check and compact matrix fit at 375px', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await installPriorityEstate(page)
    await page.goto('/dashboard')
    await expect(page.getByRole('navigation', { name: 'Sections', exact: true })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Review Fairness on Grid system A' })).toBeInViewport({ ratio: 1 })
    await expect(page.getByRole('button', { name: 'Fairness on Grid system A: Fails' })).toBeInViewport({ ratio: 1 })
    const disclosure = page.locator('details').filter({ has: page.locator('summary', { hasText: /9 systems without evidence/i }) })
    await expect(disclosure).toHaveJSProperty('open', false)
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
  })

  test('a denied system register shows a retry instead of an empty estate', async ({ page }) => {
    await page.route('**/api/v1/ai-governance/systems?**', route => route.fulfill({ status: 403, json: { detail: 'Access denied' } }))
    await page.goto('/dashboard')
    await expect(page.getByRole('heading', { name: 'The system register could not load' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Try again' })).toBeVisible()
    await expect(page.getByText('No registered AI systems yet')).toHaveCount(0)
  })

  test('an omitted gate identifies the missing system beside the known failing check', async ({ page }) => {
    await page.route('**/api/v1/ai-governance/estate/gates?**', route => route.fulfill({ json: [gridGates[0]] }))
    await page.goto('/dashboard')
    const unknown = page.getByRole('region', { name: 'Unavailable release checks' })
    await expect(unknown.getByRole('link', { name: 'Grid system B' })).toBeVisible()
    await expect(page.getByRole('region', { name: '1 failed release check' }).getByText('Some release checks could not be read.')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Fairness on Grid system A: Fails' })).toBeVisible()
    await expect(page.getByText('Partial coverage')).toBeVisible()
    await expect(page.getByText('1 failing check in available results')).toBeVisible()
  })
})
