import { expect, test, type Page } from '@playwright/test'
import { installGridFixtures } from './grid-fixtures'

const pack = { id: 'PK-THIRD-PARTY', name: 'Third parties, IP and liability', pillar: 'GOVERN', installed: true, description: 'Vendors, licensing and liability.', workflowCount: 1, evaluationCount: 2, requirementsTouched: 1 }
const workflow = { id: 'ip_copyright_review', name: 'IP and copyright review', autonomy: 'A2', stage: 'Govern', latestRun: null }
const checks = [
  { id: 'EV-LEG-01', name: 'Verbatim reproduction', engine: 'Engine exists' },
  { id: 'EV-DAT-10', name: 'Training data licence compliance', engine: 'Engine exists' },
]
const pattern = { id: 'FP-GOV-11', name: pack.name, objective: pack.description, workflows: [workflow], evaluations: checks }
const second = checks[1]
const packUrl = `/compliance/packs/${pack.id}`
const workflowUrl = `/compliance/workflows/${workflow.id}`
const checkUrl = `/compliance/evaluations/${second.id}`
const scope = '?system=sys-b'
const journeyUrl = '/compliance/journeys/ISO42001'

async function fixtures(page: Page) {
  await installGridFixtures(page, {
    framework: { key: 'ISO42001', name: 'ISO 42001' },
    systems: [{ id: 'sys-a', name: 'Grid system A', riskTier: 'low' }, { id: 'sys-b', name: 'Grid system B', riskTier: 'high' }],
    requirements: [{ key: 'ISO42001|4.1', cells: [{ state: 'open', checks: [] }, { state: 'fails', checks: [] }] }],
    unconfirmed: 0, notInScope: 0,
  })
  await page.route(/\/api\/v1\/packs(?:[/?]|$)/, async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname.split('/api/v1/packs')[1]
    const system = url.searchParams.get('system')
    const json = (data: unknown) => route.fulfill({ json: data })
    if (path === '/catalogue') return json({ pillars: [{ id: pack.pillar, name: 'Govern' }] })
    if (!path) return json([{ ...pack, patterns: [pattern] }])
    if (path === `/library/${pack.id}`) return json({ ...pack, patterns: [pattern], frameworks: [{ key: 'ISO42001', name: 'ISO 42001', touched: 1, covered: 0 }] })
    if (path === `/workflows/${workflow.id}`) return json({
      ...workflow, pack, installed: true, pattern, version: '2.3', mappings: [], triggers: [], steps: [], evaluations: checks,
      latestRun: system === 'sys-b' ? null : { id: 'other-system-run', status: 'waiting' },
    })
    if (path === '/journeys/ISO42001') return json({
      key: 'ISO42001', name: 'ISO 42001', active: 1, coveredAll: 1, coveredInstalled: 0,
      steps: [{ pack: pack.id, name: pack.name, installed: true, newlyCovered: 1, cumulative: 1 }],
      groups: [{ name: 'Controls', requirements: [{
        key: 'ISO42001|4.1', control: '4.1', title: 'Context', status: 'available', workflows: [],
        evaluations: [
          ...Array.from({ length: 5 }, (_, i) => ({ id: `EV-OTHER-${i}`, name: `Other check ${i}`, engine: 'Not found' })),
          second,
        ].map((c) => ({ ...c, installed: true, pack: pack.id, relation: 'Tests' })),
      }] }],
    })
    if (path === `/evaluations/${second.id}`) return json({
      ...second, runnable: true, pack, pattern, tests: [], installed: true, results: null,
      measures: system === 'sys-b' ? 'Licence evidence for system B.' : 'Catalogue description.',
    })
    if (path === `/evaluations/${second.id}/engine`) return json({
      id: second.id, slots: [], params: [], ways: [], platform: false, judge: false, live: '', method: 'Read licence records.',
    })
    return route.fallback()
  })
}

test('a pack and its workflow open the named check on the originating system across Back and reload', async ({ page }) => {
  test.slow()
  await fixtures(page)
  await page.goto(`/compliance${scope}`)
  await page.getByRole('tab', { name: 'Packs', exact: true }).click()
  await page.getByLabel('Pillar').selectOption('GOVERN')
  await page.getByRole('link', { name: `Open ${pack.name}` }).click()
  await expect(page).toHaveURL(packUrl + scope)

  for (const source of [packUrl, workflowUrl, journeyUrl]) {
    if (source === workflowUrl) await page.getByRole('link', { name: workflow.name, exact: true }).click()
    if (source === journeyUrl) await page.getByRole('link', { name: 'ISO 42001', exact: true }).click()
    await expect(page).toHaveURL(source + scope)
    if (source === workflowUrl) await expect(page.getByRole('link', { name: 'Open latest run' })).toHaveCount(0)
    if (source === journeyUrl) {
      await page.getByText('1 more evaluation', { exact: true }).click()
      await expect(page).toHaveURL(/expanded=ISO42001%7C4.1/)
    }
    const sourceBeforeCheck = page.url()
    const link = page.getByRole('link', { name: second.name, exact: true })
    await expect(link).toHaveAttribute('href', checkUrl + scope)
    await link.click()
    await expect(page).toHaveURL(checkUrl + scope)
    await expect(page.getByRole('heading', { name: second.name, exact: true })).toBeVisible()
    await expect(page.getByText('Licence evidence for system B.', { exact: true })).toBeVisible()
    await expect(page.getByRole('link', { name: /Back to Grid system B$/ })).toHaveAttribute('href', '/systems/sys-b')
    await page.reload()
    await expect(page.getByRole('heading', { name: second.name, exact: true })).toBeVisible()
    await expect(page.getByText('Licence evidence for system B.', { exact: true })).toBeVisible()
    await expect(page.getByRole('link', { name: /Back to Grid system B$/ })).toHaveAttribute('href', '/systems/sys-b')

    await page.goBack()
    await expect(page).toHaveURL(sourceBeforeCheck)
    await page.reload()
    await expect(link).toBeVisible()
    await expect(link).toHaveAttribute('href', checkUrl + scope)
    if (source !== packUrl) {
      await page.goBack()
      await expect(page).toHaveURL(packUrl + scope)
    }
  }

  await page.goBack()
  await page.reload()
  await expect(page.getByRole('tab', { name: 'Packs', exact: true })).toHaveAttribute('aria-selected', 'true')
  await expect(page.getByLabel('Pillar')).toHaveValue('GOVERN')
})

test('an organisation pack keeps the named check without choosing the first system', async ({ page }) => {
  await fixtures(page)
  await page.goto(packUrl)
  await page.getByRole('link', { name: second.name, exact: true }).click()
  await expect(page).toHaveURL(checkUrl)
  await expect(page.getByRole('heading', { name: second.name, exact: true })).toBeVisible()
  await expect(page.getByText('Choose a system', { exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Grid system A', exact: true })).toHaveCount(0)
  await page.reload()
  await expect(page).toHaveURL(checkUrl)
  await expect(page.getByText('Choose a system', { exact: true })).toBeVisible()
  await page.goBack()
  await expect(page).toHaveURL(packUrl)
})


test('a system cell opens its packs and the selected check for that system', async ({ page }) => {
  await fixtures(page)
  await page.goto('/frameworks/ISO42001?view=matrix')
  await page.locator('[data-mx="fwsys"] button.fm-cel.fails').click()
  const drawer = page.getByRole('dialog')
  await expect(drawer).toBeVisible()
  const cellUrl = page.url()
  await drawer.getByRole('link', { name: /^Packs for / }).click()
  await expect(page).toHaveURL(journeyUrl + scope)
  await page.getByRole('link', { name: pack.name, exact: true }).click()
  await expect(page).toHaveURL(packUrl + scope)
  await page.getByRole('link', { name: second.name, exact: true }).click()
  await expect(page).toHaveURL(checkUrl + scope)
  await expect(page.getByText('Licence evidence for system B.', { exact: true })).toBeVisible()
  await page.goBack()
  await expect(page).toHaveURL(packUrl + scope)
  await page.goBack()
  await expect(page).toHaveURL(journeyUrl + scope)
  await page.goBack()
  await expect(page).toHaveURL(cellUrl)
  await page.reload()
  await expect(drawer.getByRole('link', { name: /^Packs for / })).toHaveAttribute('href', journeyUrl + scope)
})


test('pack and workflow sources reject malformed scope and substituted records', async ({ page }) => {
  await fixtures(page)
  for (const [kind, source] of [['pack', packUrl], ['workflow', workflowUrl]]) {
    for (const query of ['?system=', '?system=sys-a&system=sys-b']) {
      await page.goto(source + query)
      await expect(page.getByText('This link needs one valid system identifier.')).toBeVisible()
      await expect(page.getByRole('link', { name: second.name, exact: true })).toHaveCount(0)
    }
    const api = kind === 'pack' ? `library/${pack.id}` : `workflows/${workflow.id}`
    await page.route(`**/api/v1/packs/${api}?**`, (route) => route.fulfill({ json: { id: 'different-record' } }))
    await page.goto(source + scope)
    await expect(page.getByText(new RegExp(`The requested ${kind} was not returned`))).toBeVisible()
    await expect(page.getByRole('link', { name: second.name, exact: true })).toHaveCount(0)
  }
})
