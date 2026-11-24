import { expect, test, type Locator } from '@playwright/test'
import { GRID_FW, installGridFixtures, ONE_PER_TIER } from './grid-fixtures'

const framework = `/frameworks/${GRID_FW}`
const trace = `${framework}/4.1`
const selected = `${trace}?system=sys-c`

test.beforeEach(async ({ page }) => {
  const failure = {
    check: 'fairness', label: 'Fairness', relation: 'Supports', cell: 'fails', fails: true, confidence: 1,
    evidenceId: 'later-passing-record', failureEvidenceIds: ['failure-one', 'failure-two'], evidenceClass: 'measured',
  }
  await installGridFixtures(page, {
    ...ONE_PER_TIER,
    requirements: ONE_PER_TIER.requirements.map((r) => r.key.endsWith('|4.1')
      ? { ...r, cells: [r.cells[0], { state: 'fails', checks: [failure] }, r.cells[2]] }
      : r),
  })
})

test('an unscoped requirement waits for a choice and opens only that system’s deciding records', async ({ page }) => {
  const journeyScopes: Array<string | null> = []
  page.on('request', (request) => {
    const url = new URL(request.url())
    if (url.pathname.endsWith(`/packs/journeys/${GRID_FW}`)) journeyScopes.push(url.searchParams.get('system'))
  })
  await page.goto(trace)
  await expect(page.getByRole('heading', { name: 'Choose a system' })).toBeVisible()
  await expect(page.getByRole('region', { name: /^Trace for/ })).toHaveCount(0)
  await page.getByRole('navigation', { name: 'AI system' }).getByRole('link', { name: 'Grid system C' }).click()
  await expect(page).toHaveURL(selected)
  for (const load of ['click', 'reload']) {
    if (load === 'reload') await page.reload()
    await expect(page.getByRole('region', { name: 'Trace for Grid system C' })).toBeVisible()
    const checks = page.getByRole('region', { name: 'Release checks behind it' })
    await expect(checks.getByRole('link')).toHaveCount(2)
    for (const id of ['failure-one', 'failure-two']) {
      await expect(checks.getByRole('link', { name: new RegExp(id) })).toHaveAttribute('href', `/evidence?system=sys-c&evidence=${id}`)
    }
    await expect(page.getByRole('link', { name: 'Open system evidence library' })).toHaveAttribute('href', '/evidence?system=sys-c')
    await expect(page.getByRole('link', { name: /^Next:/ })).toHaveAttribute('href', `${framework}/4.2?system=sys-c`)
  }
  expect(journeyScopes.length).toBeGreaterThan(0)
  expect(new Set(journeyScopes)).toEqual(new Set(['sys-c']))
  await page.goBack()
  await expect(page).toHaveURL(trace)
  await expect(page.getByRole('heading', { name: 'Choose a system' })).toBeVisible()
})

test('missing, blank and ambiguous systems show an unavailable record with an explicit recovery', async ({ page }) => {
  for (const query of ['system=retired-or-foreign', 'system=', 'system=sys-a&system=sys-c']) {
    await page.goto(`${trace}?${query}`)
    await expect(page.getByRole('heading', { name: 'Requested system unavailable' })).toBeVisible()
    await expect(page.getByRole('region', { name: /^Trace for/ })).toHaveCount(0)
    await expect(page.locator('main a[href^="/evidence"]')).toHaveCount(0)
  }
  await page.getByRole('navigation', { name: 'AI system' }).getByRole('link', { name: 'Grid system C' }).click()
  await expect(page).toHaveURL(selected)
})

test('the requirement list preserves the selected system after a detail visit and Back', async ({ page }) => {
  await page.goto(`${framework}?tab=all&system=sys-c`)
  const title = page.getByRole('region', { name: 'All requirements' }).getByRole('link', { name: 'Organisation and its context' })
  await expect(title).toHaveAttribute('href', selected)
  await title.click()
  await expect(page.getByRole('region', { name: 'Trace for Grid system C' })).toBeVisible()
  await page.goBack()
  await expect(title).toHaveAttribute('href', selected)
  await expect(page.getByText('Showing requirement status for Grid system C')).toBeVisible()
})

test('matrix and trace proof links each open the deciding record and restore the source on Back', async ({ page }) => {
  const records = [
    { id: 'later-passing-record', title: 'Later passing evaluation', timestamp: '2026-11-03T12:00:00Z' },
    { id: 'failure-two', title: 'Disparity by age', timestamp: '2026-11-02T12:00:00Z' },
    { id: 'failure-one', title: 'Disparity by region', timestamp: '2026-11-01T12:00:00Z' },
  ].map((record) => ({
    ...record, systemId: 'sys-c', type: 'evaluation_run', source: 'test', status: 'collected',
    uploadedBy: 'reviewer', capturedAt: record.timestamp, confidence: 1,
    content: { status: record.id === 'later-passing-record' ? 'passed' : 'failed' },
    tags: [], metadata: {}, linkedEntities: [], metadataSummary: {}, linkedEntityCount: 0, stale: false,
  }))
  const register = ONE_PER_TIER.systems.map((system) => ({
    ...system, workspaceId: 'ws-1', owner: 'reviewer', lifecycleStage: 'govern', metadata: {},
  }))
  await page.route('**/api/v1/ai-governance/**', async (route) => {
    const url = new URL(route.request().url())
    if (url.pathname.endsWith('/ai-governance/systems') && url.searchParams.get('org_id') === 'org-1') {
      return route.fulfill({ json: register })
    }
    if (url.pathname.endsWith('/evidence-v2/sys-c') && url.searchParams.get('org_id') === 'org-1') {
      return route.fulfill({ json: records })
    }
    if (url.pathname.endsWith('/evidence/sys-c/summary') && url.searchParams.get('org_id') === 'org-1') {
      return route.fulfill({ json: { systemId: 'sys-c', totalEvidence: records.length, missingSignals: [] } })
    }
    return route.fallback()
  })
  await page.goto(`${framework}?view=matrix`)
  await page.locator('[data-mx="fwsys"] button.fm-cel.fails').click()
  const drawer = page.getByRole('dialog')
  const selectedCell = `${framework}?${new URLSearchParams({ view: 'matrix', row: `${GRID_FW}|4.1`, col: 'sys-c' })}`
  await expect(page).toHaveURL(selectedCell)
  await page.reload()
  const checkProofLinks = async (source: Locator, sourceUrl: string) => {
    for (const { id, title } of records.filter((record) => record.content.status === 'failed')) {
      const link = source.getByRole('link', { name: new RegExp(id) })
      await link.click()
      await expect(page).toHaveURL(`/evidence?system=sys-c&evidence=${id}`)
      const record = page.getByRole('dialog', { name: title })
      await expect(record.getByText(id, { exact: true })).toBeVisible()
      await expect(record.getByRole('link', { name: 'Grid system C' })).toHaveAttribute('href', '/systems/sys-c')
      await page.goBack()
      await expect(page).toHaveURL(sourceUrl)
      await expect(link).toBeVisible()
    }
  }
  await checkProofLinks(drawer, selectedCell)
  await drawer.getByRole('link', { name: 'Review 4.1 for Grid system C' }).click()
  await expect(page).toHaveURL(selected)
  const scopedTrace = page.getByRole('region', { name: 'Trace for Grid system C' })
  const sources = page.getByRole('region', { name: 'Release checks behind it' })
  await expect(scopedTrace).toBeVisible()
  await expect(sources.getByRole('link')).toHaveCount(2)
  await checkProofLinks(sources, selected)
  await page.getByRole('link', { name: 'Open system evidence library' }).click()
  await expect(page).toHaveURL('/evidence?system=sys-c')
  await expect(page.getByText('What backs the release decision for Grid system C.')).toBeVisible()
  for (const record of records) {
    await expect(page.getByRole('button', { name: record.title })).toBeVisible()
  }
  await expect(page.getByRole('dialog')).toHaveCount(0)
  await page.goBack()
  await expect(page).toHaveURL(selected)
  await expect(scopedTrace).toBeVisible()
})

test('invalid matrix cell links stay unavailable until the selection is cleared', async ({ page }) => {
  const matrix = `${framework}?view=matrix`
  for (const params of ['row=unknown&col=sys-c', 'row=ISO42001%7C4.1&col=unknown', 'row=ISO42001%7C4.1&col=sys-a&col=sys-c']) {
    await page.goto(`${matrix}&${params}`)
    await expect(page.getByText('This matrix cell is unavailable.')).toBeVisible()
    await expect(page.getByRole('dialog')).toHaveCount(0)
    await page.getByRole('button', { name: 'Clear selection' }).click()
    await expect(page).toHaveURL(matrix)
  }
})
