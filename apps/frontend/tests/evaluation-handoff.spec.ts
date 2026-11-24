import { expect, test } from '@playwright/test'
import { installGridFixtures } from './grid-fixtures'

const check = 'EV-OVS-04'
const path = `/compliance/evaluations/${check}`
const definition = {
  id: check, name: 'Explanation quality', measures: 'Compare explanations with recorded behaviour.',
  runnable: true, tests: [], pack: { id: 'PK-OVERSIGHT', name: 'Oversight' }, results: null,
}
const record = {
  id: 'run-reviewed', systemId: 'sys-b', evaluationId: check, systemName: 'Grid system B',
  status: 'passed', source: 'traces', partialRead: true, summary: 'Only part of the week was read.',
  createdAt: '2026-10-01T08:00:00Z', files: {}, metrics: {}, detail: [],
}

test('a legacy named-check bookmark preserves its requested system through the catalogue redirect', async ({ page }) => {
  await installGridFixtures(page)
  await page.route(`**/packs/evaluations/${check}?**`, (route) => route.fulfill({ json: definition }))
  await page.goto(`/compliance/evaluations?system=sys-b#${check}`)
  await expect(page).toHaveURL(path + '?system=sys-b')
  await expect(page.getByRole('heading', { name: definition.name })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Grid system B', exact: true })).toHaveAttribute('href', '/systems/sys-b')
  await page.reload()
  await expect(page.getByRole('heading', { name: definition.name })).toBeVisible()
})

test('invalid system and ambiguous run links never load another record', async ({ page }) => {
  await installGridFixtures(page)
  const reads: string[] = []
  page.on('request', (request) => { if (request.url().includes('/packs/evaluation-runs/')) reads.push(request.url()) })
  for (const query of ['run=abc', 'system=sys-b&run=x&run=y', 'system=sys-a&system=sys-b&run=x', 'system=%20&run=x']) {
    await page.goto(path + '?' + query)
    await expect(page.getByText(/Evaluation link unavailable/).first()).toBeVisible()
  }
  await page.goto(path + '?system=unknown&run=x')
  await expect(page.getByText('This AI system is unavailable in this organisation.')).toBeVisible()
  expect(reads).toEqual([])
})

test('denied, wrong and incomplete results stay unavailable until the exact run can be read', async ({ page }) => {
  await installGridFixtures(page)
  await page.route(`**/packs/evaluations/${check}?**`, (route) => route.fulfill({ json: definition }))
  let response: 'denied' | 'other' | 'partial' | 'ok' = 'denied'
  await page.route('**/packs/evaluation-runs/run-reviewed?**', (route) => {
    const query = new URL(route.request().url()).searchParams
    expect([query.get('system_id'), query.get('evaluation_id'), query.get('org_id')]).toEqual(['sys-b', check, 'org-1'])
    if (response === 'denied') return route.fulfill({ status: 403, json: { detail: 'Read denied' } })
    if (response === 'other') return route.fulfill({ json: { ...record, systemId: 'sys-a', summary: 'Another system result' } })
    if (response === 'partial') return route.fulfill({ json: { id: record.id, evaluationId: check, systemId: 'sys-b' } })
    return route.fulfill({ json: record })
  })
  await page.goto(path + '?system=sys-b&run=run-reviewed')
  const unavailable = page.getByText(/Recorded result unavailable/).first()
  await expect(unavailable).toBeVisible()
  for (const variant of ['other', 'partial'] as const) {
    response = variant
    await page.reload()
    await expect(unavailable).toBeVisible()
    await expect(page.getByRole('region', { name: 'Recorded result' })).toHaveCount(0)
    await expect(page.getByText('Another system result')).toHaveCount(0)
  }
  response = 'ok'
  await page.getByRole('button', { name: /retry|try again/i }).click()
  const result = page.getByRole('region', { name: 'Recorded result' })
  await expect(result.getByText(record.id, { exact: true })).toBeVisible()
  await expect(result.getByText(/Partial live-run coverage/)).toBeVisible()
})
