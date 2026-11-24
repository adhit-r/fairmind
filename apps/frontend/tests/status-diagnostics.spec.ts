import { expect, test } from '@playwright/test'
import { installGridFixtures } from './grid-fixtures'

test('governance diagnostics show only reported observations and recover from a denied read', async ({ page }) => {
  await installGridFixtures(page)
  const timestamp = '2026-11-23T01:02:03Z'
  let result: 'endpoint' | 'denied' | 'probes' = 'endpoint'
  await page.route('**/ai-governance/status?**', (route) => {
    expect(new URL(route.request().url()).searchParams.get('org_id')).toBe('org-1')
    if (result === 'denied') return route.fulfill({ status: 403, json: { detail: 'Status access denied' } })
    const services = result === 'probes' ? { job_queue: { status: 'degraded' }, database: 'up' } : undefined
    return route.fulfill({ json: { status: 'operational', timestamp, capabilities: ['policies'], services } })
  })

  await page.goto('/status')
  await expect(page.getByText('/api/v1/ai-governance/status', { exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Governance API response' })).toBeVisible()
  await expect(page.getByText('operational', { exact: true })).toBeVisible()
  await expect(page.locator('time')).toHaveAttribute('datetime', timestamp)
  await expect(page.getByText('Individual service probes were not reported.')).toBeVisible()
  await expect(page.getByText('0/0', { exact: true })).toHaveCount(0)

  result = 'denied'
  await page.getByRole('button', { name: 'Refresh', exact: true }).click()
  await expect(page.getByText('Governance API status unavailable')).toBeVisible()
  await expect(page.getByText('Status access denied')).toBeVisible()
  await expect(page.getByText('operational', { exact: true })).toHaveCount(0)

  result = 'probes'
  await page.getByRole('button', { name: 'Retry', exact: true }).click()
  await expect(page.getByRole('listitem').filter({ hasText: 'job queue' })).toContainText('degraded')
  await expect(page.getByRole('listitem').filter({ hasText: 'database' })).toContainText('up')
  await expect(page.getByText('Individual service probes were not reported.')).toHaveCount(0)
})
