import { expect, test } from '@playwright/test'
import { GRID_FW, installGridFixtures, layoutFacts } from './grid-fixtures'

// The shared fixtures' crosswalk only reaches the monitoring control, which has no evidence record; add the fairness one.
const controls = {
  controls: [{ id: 'FMC-FAI-01', name: 'Fairness', objective: null, workflows: [] }],
  crosswalk: [
    { commonControl: 'FMC-FAI-01', key: `${GRID_FW}|4.1`, relation: 'Satisfies' },
    { commonControl: 'FMC-FAI-01', key: `${GRID_FW}|9.1`, relation: 'Supports' },
  ],
}

test.describe('Evidence grid', () => {
  test.beforeEach(async ({ page }) => {
    await installGridFixtures(page)
    await page.route('**/api/proxy/api/v1/packs/controls**', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(controls) }),
    )
  })

  test('opens on the grid: one row per evidence item, its proof and framework reach', async ({ page }) => {
    await page.goto('/evidence')
    const grid = page.locator('[data-mx="evidence"]')
    await expect(grid).toBeVisible({ timeout: 30_000 })
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('6 evidence items across 2 systems')
    await expect(grid.locator('tbody .fm-cel.r3')).toHaveCount(1)
    await expect(grid.locator('tbody .fm-cel.fails')).toHaveCount(2)
    const facts = await layoutFacts(page)
    expect(facts.cards).toBeLessThanOrEqual(3)
    expect(facts.legends).toBe(1)
  })

  test('a framework cell opens the requirements it touches', async ({ page }) => {
    await page.goto('/evidence')
    await page.locator('[data-mx="evidence"] button.fm-cel.r3').click({ timeout: 30_000 })
    const dialog = page.getByRole('dialog')
    await expect(dialog.getByText('Organisation and its context')).toBeVisible()
    await expect(dialog.getByText('2 requirements')).toBeVisible()
    await expect(dialog.getByRole('link', { name: 'Open framework' })).toHaveAttribute('href', `/frameworks/${GRID_FW}`)
  })

  test('Grid | Library switches the view', async ({ page }) => {
    await page.goto('/evidence')
    await expect(page.locator('[data-mx="evidence"]')).toBeVisible({ timeout: 30_000 })
    const seg = page.getByRole('navigation', { name: 'Evidence layout' })
    await seg.getByRole('link', { name: 'Library' }).click()
    await expect(page).toHaveURL(/\/evidence\?view=artifacts$/)
    await expect(page.locator('[data-mx="evidence"]')).toHaveCount(0)
    await expect(seg.getByRole('link', { name: 'Library' })).toHaveAttribute('aria-current', 'page')
    await seg.getByRole('link', { name: 'Grid' }).click()
    await expect(page.locator('[data-mx="evidence"]')).toBeVisible()
  })

  test('no page horizontal scroll at 375px', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/evidence')
    await expect(page.locator('[data-mx="evidence"]')).toBeVisible({ timeout: 30_000 })
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
  })
})
