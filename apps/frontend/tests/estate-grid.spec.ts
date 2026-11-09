import { expect, test } from '@playwright/test'
import { installGridFixtures, layoutFacts } from './grid-fixtures'

test.describe('Estate grid', () => {
  test.beforeEach(async ({ page }) => installGridFixtures(page))

  test('renders one decluttered grid with derived cell states', async ({ page }) => {
    await page.goto('/dashboard')
    const grid = page.locator('[data-mx="estate"]')
    await expect(grid).toBeVisible({ timeout: 30_000 })
    await expect(grid.getByRole('link', { name: 'Grid system A' })).toBeVisible()
    await expect(grid.locator('.fm-cel.fails').first()).toBeVisible()
    await expect(grid.locator('.fm-cel.stale').first()).toBeVisible()
    await expect(grid.locator('.fm-cel.attested').first()).toBeVisible()
    await expect(grid.locator('.fm-cel.estimated').first()).toBeVisible()
    await expect(page.getByPlaceholder('Ask about any system or finding')).toHaveCount(0)
    const facts = await layoutFacts(page)
    expect(facts.cards).toBeLessThanOrEqual(3)
    expect(facts.legends).toBe(1)
  })

  test('a cell is focusable and Enter opens its drawer', async ({ page }) => {
    await page.goto('/dashboard')
    const cell = page.locator('[data-mx="estate"] button.fm-cel').first()
    await expect(cell).toBeVisible({ timeout: 30_000 })
    await cell.focus()
    await page.keyboard.press('Enter')
    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByRole('dialog').getByRole('link', { name: 'Open system' })).toBeVisible()
  })

  test('no page horizontal scroll at 375px', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/dashboard')
    await expect(page.locator('[data-mx="estate"]')).toBeVisible({ timeout: 30_000 })
    expect((await layoutFacts(page)).overflow).toBeLessThanOrEqual(0)
  })
})
