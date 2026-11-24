import { expect, test } from '@playwright/test'
import { installGridFixtures } from './grid-fixtures'

test.beforeEach(async ({ page }) => installGridFixtures(page))

test('violations require a scoped, successful, complete read before showing an empty register', async ({ page }) => {
  let result: 'denied' | 'incomplete' | 'empty' = 'denied'
  await page.route('**/compliance/violations?**', async (route) => {
    expect(new URL(route.request().url()).searchParams.get('org_id')).toBe('org-1')
    if (result === 'denied') return route.fulfill({ status: 403, json: { detail: 'Read denied' } })
    if (result === 'incomplete') return route.fulfill({ json: { violations: [], total: 3 } })
    return route.fulfill({ json: { violations: [], total: 0 } })
  })
  await page.goto('/compliance-automation')
  await page.getByRole('button', { name: 'Violations', exact: true }).click()
  const error = page.getByRole('alert').filter({ hasText: 'Violations unavailable' })
  await expect(error).toContainText('Read denied')
  await expect(page.getByText('No recorded violations')).toHaveCount(0)
  result = 'incomplete'
  await error.getByRole('button', { name: 'Try again' }).click()
  await expect(error).toContainText('incomplete')
  result = 'empty'
  await error.getByRole('button', { name: 'Try again' }).click()
  await expect(page.getByRole('heading', { name: 'No recorded violations' })).toBeVisible()
  await expect(page.getByText(/Grid org contains no records across all dates/)).toBeVisible()
})

test('automation summary drops earlier counts on refresh and unavailable lists offer retry', async ({ page }) => {
  let denied = false
  await page.route('**/compliance/status?**', (route) => denied
    ? route.fulfill({ status: 403, json: { detail: 'Summary denied' } })
    : route.fulfill({ json: { scheduler_running: true, active_schedules: 1, pending_jobs: 3, total_violations: 2, critical_violations: 1, reports_generated_today: 1 } }))
  await page.route('**/compliance/schedules?**', (route) => route.fulfill({ status: 403, json: { detail: 'Schedules denied' } }))
  await page.route('**/compliance/reports?**', (route) => route.fulfill({ status: 501, json: { detail: 'Report history is not stored yet.' } }))
  await page.goto('/compliance-automation')
  await expect(page.getByText('Scheduler Running', { exact: true })).toBeVisible()
  await expect(page.getByRole('alert').filter({ hasText: 'Schedules unavailable' })).toContainText('Schedules denied')
  await expect(page.getByText(/No schedules configured/)).toHaveCount(0)
  denied = true
  await page.getByRole('button', { name: 'Refresh', exact: true }).click()
  await expect(page.getByText('Summary denied', { exact: true })).toBeVisible()
  await expect(page.getByText('Scheduler Running', { exact: true })).toHaveCount(0)
  await page.getByRole('button', { name: 'Reports', exact: true }).click()
  await expect(page.getByRole('alert').filter({ hasText: 'Report history unavailable' })).toContainText('not stored yet', { timeout: 15000 })
  await expect(page.getByText('No reports recorded.')).toHaveCount(0)
})

for (const path of ['/monitoring', '/environment?system=sys-b']) {
  test(`${path} retains an active registered system when its gate is missing or denied`, async ({ page }) => {
    let denied = false
    await page.route('**/estate/gates?**', (route) => denied
      ? route.fulfill({ status: 403, json: { detail: 'Gate access denied' } })
      : route.fulfill({ json: [{ systemId: 'sys-a', checks: [] }] }))
    await page.goto(path)
    const row = page.getByRole('listitem').filter({ has: page.getByRole('link', { name: 'Grid system B', exact: true }) })
    await expect(row).toContainText('Gate status unknown')
    await expect(row.getByRole('link', { name: 'Grid system B' })).toBeVisible()
    if (path.startsWith('/environment')) {
      await expect(row.getByRole('button', { name: 'Start an assessment' })).toBeVisible()
      await expect(page.getByText('Not counted in release decisions', { exact: true })).toHaveCount(0)
    }
    denied = true
    await page.reload()
    await expect(page.getByText('Gate access denied').first()).toBeVisible()
    await expect(row).toContainText('Gate status unknown')
    const counts = page.getByRole('list', { name: path.startsWith('/environment') ? /Environmental checks/ : /Monitoring across/ })
    await expect(counts.getByRole('listitem').filter({ hasText: path.startsWith('/environment') ? 'Fails' : 'Drifting' })).toContainText('—')
  })
}

test('policy alerts only show a scoped empty result after retry succeeds', async ({ page }) => {
  let denied = true
  await page.route('**/policies/alerts', (route) => denied
    ? route.fulfill({ status: 403, json: { detail: 'Alerts denied' } })
    : route.fulfill({ json: [] }))
  await page.goto('/alerts')
  await expect(page.getByText('Alerts Unavailable', { exact: true })).toBeVisible()
  await expect(page.getByText(/No open policy alerts/)).toHaveCount(0)
  denied = false
  await page.getByRole('button', { name: 'Refresh', exact: true }).click()
  await expect(page.getByText('No open policy alerts recorded for this organisation.')).toBeVisible()
})

test('review queue keeps available items, identifies missing feeds and distinguishes a filtered empty list', async ({ page }) => {
  let denied = true
  await page.route('**/plan?**', (route) => route.fulfill({ json: { exists: false, status: 'discovery' } }))
  await page.route('**/internal-audits/mine?**', (route) => route.fulfill({ json: { items: [] } }))
  await page.route('**/policies/alerts', (route) => denied
    ? route.fulfill({ status: 403, json: { detail: 'Alerts denied' } })
    : route.fulfill({ json: [] }))
  await page.route('**/runs?status=waiting**', (route) => route.fulfill({ json: [{ id: 'waiting-1', workflowName: 'Review rollout', waitingFor: 'input' }] }))
  await page.goto('/needs-you')
  await expect(page.getByText('Review rollout', { exact: true })).toBeVisible()
  await expect(page.getByText(/Policy alerts: Alerts denied/)).toBeVisible()
  await page.getByText('Policy alert', { exact: true }).click()
  await expect(page.getByText('Review queue incomplete', { exact: true })).toBeVisible()
  await expect(page.getByText('Nothing waits on you')).toHaveCount(0)
  denied = false
  await page.getByRole('button', { name: 'Try again' }).click()
  await expect(page.getByRole('heading', { name: 'No items match this filter' })).toBeVisible()
  await page.getByRole('button', { name: 'Show all types' }).click()
  await expect(page.getByText('Review rollout', { exact: true })).toBeVisible()
})
